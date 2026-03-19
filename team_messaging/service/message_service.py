"""
Message Service
消息和积分赠送业务逻辑
"""

from django.db import transaction
from django.utils import timezone
from django.core.cache import cache

from core.models import Message, AppUser, PointsLog
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

    def get_messages(self, user, page=1, page_size=20, message_type=None, status=None):
        """获取用户消息列表（分页、筛选）"""
        messages = self.message_mapper.get_user_messages(
            user.id, page=page, page_size=page_size, status=status
        )
        total_count = self.message_mapper.get_user_messages_count(
            user.id, status=status
        )

        return {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "messages": [
                {
                    "id": msg.id,
                    "title": msg.title,
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "sender_nickname": msg.sender.nickname if msg.sender else "System",
                    "status": msg.status,
                    "created_at": msg.created_at.isoformat(),
                    "read_at": msg.read_at.isoformat() if msg.read_at else None,
                }
                for msg in messages
            ],
        }

    def get_unread_count(self, user):
        """获取用户未读消息数（使用Redis缓存）"""
        cache_key = f"user:{user.id}:unread_msg_count"

        # 尝试从 Redis 读取
        unread_count = cache.get(cache_key)

        if unread_count is None:
            # 缓存 miss，从 DB 查询
            unread_count = self.message_mapper.get_unread_message_count(user.id)
            # 写入缓存（TTL 1小时）
            cache.set(cache_key, unread_count, 3600)

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
        cache.delete(cache_key)

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
        cache.delete(cache_key)

        return {"id": message_id, "status": "deleted"}


class PointsGiftService:
    """积分赠送业务逻辑"""

    # 日赠送上限（200点）
    DAILY_GIFT_LIMIT = 200

    def __init__(self):
        self.message_mapper = MessageMapper()
        self.points_mapper = PointsMapper()

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
            raise MessageServiceError(400, "Points must be positive")

        if points_amount > 5000:
            raise MessageServiceError(400, "Cannot gift more than 5000 points at once")

        # 检查接收者
        try:
            receiver = AppUser.objects.get(id=receiver_id)
        except AppUser.DoesNotExist:
            raise MessageServiceError(404, "Receiver not found")

        if receiver_id == sender.id:
            raise MessageServiceError(400, "Cannot gift to yourself")

        # 检查发送者积分充足
        if sender.points < points_amount:
            raise MessageServiceError(
                400, f"Insufficient points (have {sender.points}, need {points_amount})"
            )

        # 检查日赠送额度
        daily_total = self.points_mapper.get_daily_gift_total(sender.id)
        if daily_total + points_amount > self.DAILY_GIFT_LIMIT:
            remaining = self.DAILY_GIFT_LIMIT - daily_total
            raise MessageServiceError(
                429,
                f"Daily gift limit exceeded (limit {self.DAILY_GIFT_LIMIT}, already sent {daily_total}, remaining {remaining})",
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
            reason=f"Gift {points_amount} points to {receiver.nickname}",
            ref_type="user",
            ref_id=receiver_id,
        )

        # 创建积分日志（接收者入款）
        self.points_mapper.create_points_log(
            user_id=receiver_id,
            points_type="points_gift_receive",
            delta=points_amount,
            reason=f"Received {points_amount} points from {sender.nickname}",
            ref_type="user",
            ref_id=sender.id,
        )

        # 创建消息通知
        msg = self.message_mapper.create_message(
            user_id=receiver_id,
            sender_id=sender.id,
            message_type="points_gift",
            title=f"{sender.nickname} sent you {points_amount} points",
            content=message or f"You received {points_amount} points!",
            points_amount=points_amount,
            ref_type="user",
            ref_id=sender.id,
        )

        # 清除接收者的未读数缓存
        cache_key = f"user:{receiver_id}:unread_msg_count"
        from django.core.cache import cache

        cache.delete(cache_key)

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
