import logging
from config.celery import app
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags

"""
所有发送的邮件模板集中到一个字典 HTML_MESSAGES 里
其中 
subject 为 邮件标题
html_message 为 HTML邮件内容
"""

HTML_MESSAGES = {
    "activate": {
        "subject": "MiniTieba 激活邮件",
        "html_message": """
                        <p>尊敬的用户，您好！</p>
                        <p>感谢您注册 <strong>MiniTieba</strong>，请点击以下链接完成账户验证：</p>
                        <p style="font-size: 22px; font-weight: bold; color: #FF4C4C;">{}</p>
                        <p>该链接 <strong>{} 分钟</strong> 内有效，请尽快使用。</p>
                        <p>如果您未进行过本网站的注册操作，请忽略此邮件。</p>
                        <hr>
                        <p style="color: gray; font-size: 12px;">此邮件由系统自动发送，请勿直接回复。</p>
                    """,
    },
    "verify": {
        "subject": "MiniTieba 邮箱验证邮件",
        "html_message": """
                        <p>尊敬的用户，您好！</p>
                        <p>请点击以下链接完成 <strong>MiniTieba</strong> 账户邮箱更改的验证：</p>
                        <p style="font-size: 22px; font-weight: bold; color: #FF4C4C;">{}</p>
                        <p>该验证码 <strong>{} 分钟</strong> 内有效，请尽快使用。</p>
                        <p>如果您未进行过本网站的邮箱更改操作，请及时查看您的账户是否被盗。</p>
                        <hr>
                        <p style="color: gray; font-size: 12px;">此邮件由系统自动发送，请勿直接回复。</p>
                    """,
    },
}


@app.task
def send_email(email_recv, verify_code, mode="activate"):
    try:
        # 收件人列表格式化
        if isinstance(email_recv, str):
            email_recv = [email_recv]

        if mode not in HTML_MESSAGES.keys():
            logging.error(f"邮件发送失败: 当前类型 {mode} 错误")
            raise ValueError("Mode is error")

        subject = HTML_MESSAGES[mode]["subject"]
        html_message = HTML_MESSAGES[mode]["html_message"]
        html_message = html_message.format(
            verify_code, int(settings.EMAIL_EXPIRE_SECONDS) // 60
        )

        # 纯文本内容（避免部分邮箱不支持 HTML）
        plain_message = strip_tags(html_message)
        # 发件人（必须和实际的邮箱一致）
        from_email = settings.EMAIL_HOST_USER
        # 发送
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=email_recv,
            html_message=html_message,
        )
        logging.info(f"邮件发送到: {email_recv}")
    except Exception as e:
        logging.error(f"邮件发送失败: {e}")
