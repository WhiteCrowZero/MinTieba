from celery import shared_task
from django.utils import timezone
from django.db import transaction
from forums.models import Forum, ForumMember, RoleChoices, ForumActivity


@shared_task(bind=True, max_retries=3)
def toggle_forum_membership_task(self, forum_id, user_id):
    """
    异步处理用户加入或退出贴吧（保证最终一致性）
    """
    try:
        with transaction.atomic():
            forum = Forum.objects.select_for_update().get(pk=forum_id)
            member = ForumMember.all_objects.filter(
                forum=forum, user_id=user_id
            ).first()

            if not member:
                member = ForumMember.objects.create(
                    forum=forum,
                    user_id=user_id,
                    role_type=RoleChoices.MEMBER,
                )
                # ForumActivity.objects.create(
                #     forum=forum,
                #     forum_member=member,
                # )
                action = "joined"
            elif member.is_deleted:
                member.is_deleted = False
                member.deleted_at = None
                member.joined_at = timezone.now()
                member.save(update_fields=["is_deleted", "deleted_at", "joined_at"])
                action = "rejoined"
            else:
                member.delete()
                action = "left"

            # 同步更新成员数
            forum.member_count = ForumMember.objects.filter(forum=forum).count()
            forum.save(update_fields=["member_count"])

        return {"status": "success", "action": action, "forum": forum_id}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)


@shared_task
def refresh_forum_member_counts():
    for forum in Forum.objects.all():
        forum.member_count = ForumMember.objects.filter(
            forum=forum, is_deleted=False
        ).count()
        forum.save(update_fields=["member_count"])
