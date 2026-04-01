"""
Message Service
消息和积分赠送业务逻辑
"""

from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
import logging
import time

from core.models import Message, AppUser, PointsLog, TeamInvitation
from team_messaging.mapper.team_message_mapper import MessageMapper, PointsMapper


class MessageServiceError(Exception):
    """消息业务异常"""

    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)


class MessageService:
    """消息管理业务逻辑"""

    def __init__(self):
        self.message_mapper = MessageMapper()
        self.logger = logging.getLogger(__name__)
        # Redis 不可用时短暂熔断，直接降级到数据库，避免每次请求都阻塞重试。
        self._cache_disabled_until = 0.0
        self._cache_cooldown_seconds = 30

    def _cache_enabled(self):
        return time.time() >= self._cache_disabled_until

    def _trip_cache_circuit(self, operation, key, error):
        was_enabled = self._cache_enabled()
        self._cache_disabled_until = time.time() + self._cache_cooldown_seconds
        if was_enabled:
            self.logger.warning(
                "cache backend unavailable, fallback to DB for %ss. op=%s key=%s err=%s",
                self._cache_cooldown_seconds,
                operation,
                key,
                error,
            )

    def _safe_cache_get(self, key):
        if not self._cache_enabled():
            return None
        try:
            return cache.get(key)
        except Exception as e:
            self._trip_cache_circuit("get", key, e)
            return None

    def _safe_cache_set(self, key, value, timeout):
        if not self._cache_enabled():
            return
        try:
            cache.set(key, value, timeout)
        except Exception as e:
            self._trip_cache_circuit("set", key, e)

    def _safe_cache_delete(self, key):
        if not self._cache_enabled():
            return
        try:
            cache.delete(key)
        except Exception as e:
            self._trip_cache_circuit("delete", key, e)

    def get_messages(self, user, page=1, page_size=20, message_type=None, status=None):
        """获取用户消息列表（分页、筛选）"""
        version_key = f"user:{user.id}:messages_cache_version"
        cache_version = self._safe_cache_get(version_key)
        if cache_version is None:
            cache_version = 0

        cache_key = (
            f"user:{user.id}:messages:v{cache_version}:"
            f"p{page}:s{page_size}:t{message_type or 'all'}:st{status or 'all'}"
        )
        cached_result = self._safe_cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        messages = self.message_mapper.get_user_messages(
            user.id,
            page=page,
            page_size=page_size,
            message_type=message_type,
            status=status,
        )
        total_count = self.message_mapper.get_user_messages_count(
            user.id, message_type=message_type, status=status
        )

        invite_ids = [
            msg.ref_id
            for msg in messages
            if msg.message_type == "team_invite" and msg.ref_id
        ]
        invite_status_map = {
            row["id"]: row["status"]
            for row in TeamInvitation.objects.filter(
                id__in=invite_ids,
                invitee_id=user.id,
            ).values("id", "status")
        }

        result = {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "messages": [
                {
                    "id": msg.id,
                    "title": msg.title,
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "sender_id": msg.sender_id,
                    "sender_nickname": msg.sender.nickname if msg.sender else "System",
                    "status": msg.status,
                    "created_at": msg.created_at.isoformat(),
                    "read_at": msg.read_at.isoformat() if msg.read_at else None,
                    "ref_type": msg.ref_type,
                    "ref_id": msg.ref_id,
                    "points_amount": msg.points_amount,
                    "is_accepted": (
                        msg.is_accepted
                        or invite_status_map.get(msg.ref_id) == "accepted"
                    ),
                    "invitation_status": (
                        invite_status_map.get(msg.ref_id)
                        if msg.message_type == "team_invite"
                        else None
                    ),
                    "can_accept_invite": (
                        msg.message_type == "team_invite"
                        and invite_status_map.get(msg.ref_id) == "pending"
                    ),
                }
                for msg in messages
            ],
        }
        self._safe_cache_set(cache_key, result, 30)
        return result

    def get_unread_count(self, user):
        """获取用户未读消息数（使用Redis缓存）"""
        cache_key = f"user:{user.id}:unread_msg_count"

        # 尝试从 Redis 读取
        unread_count = self._safe_cache_get(cache_key)

        if unread_count is None:
            # 缓存 miss，从 DB 查询
            unread_count = self.message_mapper.get_unread_message_count(user.id)
            # 写入缓存（TTL 1小时）
            self._safe_cache_set(cache_key, unread_count, 3600)

        return {"unread_count": unread_count}

    def mark_as_read(self, user, message_id):
        """标记消息已读"""
        message = self.message_mapper.get_message(message_id)

        if not message:
            raise MessageServiceError(404, "Message not found")

        if message.user_id != user.id:
            raise MessageServiceError(403, "Cannot read others' messages")

        self.message_mapper.mark_as_read(message_id)

        # 清除未读数缓存
        cache_key = f"user:{user.id}:unread_msg_count"
        self._safe_cache_delete(cache_key)

        return {"id": message_id, "status": "read"}

    def delete_message(self, user, message_id):
        """删除消息"""
        message = self.message_mapper.get_message(message_id)

        if not message:
            raise MessageServiceError(404, "Message not found")

        if message.user_id != user.id:
            raise MessageServiceError(403, "Cannot delete others' messages")

        self.message_mapper.delete_message(message_id)

        # 清除未读数缓存
        cache_key = f"user:{user.id}:unread_msg_count"
        self._safe_cache_delete(cache_key)

        return {"id": message_id, "status": "deleted"}


class PointsGiftService:
    """积分赠送业务逻辑"""

    # 日赠送上限（200点）
    DAILY_GIFT_LIMIT = 200

    def __init__(self):
        self.message_mapper = MessageMapper()
        self.points_mapper = PointsMapper()
        self.logger = logging.getLogger(__name__)

    def _safe_cache_delete(self, key):
        try:
            cache.delete(key)
        except Exception as e:
            self.logger.warning("cache.delete failed for %s: %s", key, e)

    @transaction.atomic
    def send_points_gift(self, sender, receiver_id, points_amount, message=""):
        """
        赠送积分

        业务规则：
        - 发送者积分必须充足
        - 接收者必须存在
        - 日赠送不超过200点
        - 事务保护：扣减发送者、增加接收者、创建2条PointsLog、创建Message
        """

        # 参数验证
        if points_amount <= 0:
            raise MessageServiceError(400, "赠送积分必须大于0")

        if points_amount > 5000:
            raise MessageServiceError(400, "单次赠送积分不能超过5000")

        # 检查接收者
        try:
            receiver = AppUser.objects.get(id=receiver_id)
        except AppUser.DoesNotExist:
            raise MessageServiceError(404, "接收用户不存在")

        if receiver_id == sender.id:
            raise MessageServiceError(400, "不能给自己赠送积分")

        # 检查发送者积分充足
        if sender.points < points_amount:
            raise MessageServiceError(
                400, f"积分不足（当前{sender.points}，需要{points_amount}）"
            )

        # 检查日赠送额度
        daily_total = self.points_mapper.get_daily_gift_total(sender.id)
        if daily_total + points_amount > self.DAILY_GIFT_LIMIT:
            remaining = self.DAILY_GIFT_LIMIT - daily_total
            raise MessageServiceError(
                429,
                f"今日赠送积分已超上限（上限{self.DAILY_GIFT_LIMIT}，已赠送{daily_total}，剩余{remaining}）",
            )

        # 事务处理：扣减发送者、增加接收者、创建日志、创建消息
        sender.points -= points_amount
        sender.save()

        receiver.points += points_amount
        receiver.save()

        # 创建积分日志（发送者扣款）
        self.points_mapper.create_points_log(
            user_id=sender.id,
            points_type="points_gift",
            delta=-points_amount,
            reason=f"向 {receiver.nickname} 赠送 {points_amount} 积分",
            ref_type="user",
            ref_id=receiver_id,
        )

        # 创建积分日志（接收者入款）
        self.points_mapper.create_points_log(
            user_id=receiver_id,
            points_type="points_gift_receive",
            delta=points_amount,
            reason=f"收到 {sender.nickname} 赠送的 {points_amount} 积分",
            ref_type="user",
            ref_id=sender.id,
        )

        # 创建消息通知
        msg = self.message_mapper.create_message(
            user_id=receiver_id,
            sender_id=sender.id,
            message_type="points_gift",
            title=f"{sender.nickname} 向你赠送了 {points_amount} 积分",
            content=message or f"你收到了 {points_amount} 积分",
            points_amount=points_amount,
            ref_type="user",
            ref_id=sender.id,
        )

        # 给赠送方在与伙伴会话中保留一条记录，便于追溯互动历史。
        self.message_mapper.create_message(
            user_id=sender.id,
            sender_id=receiver_id,
            message_type="system",
            title="积分赠送记录",
            content=f"你已向 {receiver.nickname} 赠送 {points_amount} 积分。",
            points_amount=points_amount,
            ref_type="user",
            ref_id=receiver_id,
        )

        # 清除接收者的未读数缓存（Redis 异常时不影响主流程）
        cache_key = f"user:{receiver_id}:unread_msg_count"
        self._safe_cache_delete(cache_key)

        sender_cache_key = f"user:{sender.id}:unread_msg_count"
        self._safe_cache_delete(sender_cache_key)

        return {
            "message_id": msg.id,
            "sender_id": sender.id,
            "receiver_id": receiver_id,
            "points_amount": points_amount,
            "status": "success",
            "created_at": msg.created_at.isoformat(),
        }

    def get_daily_gift_limit_info(self, sender):
        """获取用户日赠送额度信息"""
        daily_total = self.points_mapper.get_daily_gift_total(sender.id)
        remaining = max(0, self.DAILY_GIFT_LIMIT - daily_total)

        return {
            "limit": self.DAILY_GIFT_LIMIT,
            "sent_today": daily_total,
            "remaining": remaining,
        }
