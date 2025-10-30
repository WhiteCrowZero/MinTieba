# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync
# import json
#
#
# class NotificationService:
#
#     @staticmethod
#     def send_notification(user_id, message):
#         """
#         向指定用户发送通知
#         :param user_id: 用户ID
#         :param message: 消息内容
#         """
#         channel_layer = get_channel_layer()
#         group_name = f"user_{user_id}"
#
#         async_to_sync(channel_layer.group_send)(
#             group_name,
#             {
#                 "type": "send_notification",
#                 "message": message,
#             },
#         )
#
#     @staticmethod
#     def send_system_notification(message):
#         """
#         发送全体用户通知
#         :param message: 通知内容
#         """
#         channel_layer = get_channel_layer()
#
#         # 这里可以发送给所有用户的组，也可以指定特定用户组
#         async_to_sync(channel_layer.group_send)(
#             "system_notifications",  # 系统通知组
#             {
#                 "type": "send_system_notification",
#                 "message": message,
#             },
#         )
