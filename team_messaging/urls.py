from django.urls import path

from team_messaging.controller import team_controller, message_controller

urlpatterns = [
    # ========== 队伍管理 ==========
    path("teams", team_controller.create_team, name="create_team"),
    path(
        "teams/mine", team_controller.get_my_team, name="get_my_team"
    ),  # ★ Phase 2: 单队伍模式
    path(
        "teams/<int:team_id>", team_controller.get_team_detail, name="get_team_detail"
    ),
    path(
        "teams/<int:team_id>/members",
        team_controller.get_team_members,
        name="get_team_members",
    ),
    path("teams/<int:team_id>/update", team_controller.update_team, name="update_team"),
    path("teams/<int:team_id>/delete", team_controller.delete_team, name="delete_team"),
    path(
        "teams/<int:team_id>/members/<int:user_id>/remove",
        team_controller.remove_team_member,
        name="remove_team_member",
    ),
    path(
        "teams/<int:team_id>/members/<int:user_id>/role",
        team_controller.set_member_role,
        name="set_member_role",
    ),
    # ========== 组队邀请 ==========
    path(
        "teams/<int:team_id>/invite",
        team_controller.send_team_invitation,
        name="send_team_invitation",
    ),
    path("invitations", team_controller.get_invitations, name="get_invitations"),
    path(
        "invitations/<int:invitation_id>/accept",
        team_controller.accept_invitation,
        name="accept_invitation",
    ),
    path(
        "invitations/<int:invitation_id>/reject",
        team_controller.reject_invitation,
        name="reject_invitation",
    ),
    # ========== 邀请冷却检查 ==========
    path(
        "teams/<int:team_id>/invite/<int:invitee_id>/cooldown",
        team_controller.check_invitation_cooldown,
        name="check_invitation_cooldown",
    ),
    # ========== 消息中心 ==========
    path("messages", message_controller.get_messages, name="get_messages"),
    path(
        "messages/unread-count",
        message_controller.get_unread_count,
        name="get_unread_count",
    ),
    path(
        "messages/<int:message_id>/read",
        message_controller.mark_message_as_read,
        name="mark_message_as_read",
    ),
    path(
        "messages/<int:message_id>/delete",
        message_controller.delete_message,
        name="delete_message",
    ),
    # ========== 积分赠送 ==========
    path(
        "messages/points-gift",
        message_controller.send_points_gift,
        name="send_points_gift",
    ),
    path(
        "messages/points-gift/limit",
        message_controller.get_points_gift_limit,
        name="get_points_gift_limit",
    ),
]
