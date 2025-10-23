from tencentcloud.common import credential
from tencentcloud.sms.v20210111 import sms_client, models
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from django.conf import settings

from common.utils.cache_utils import CacheService


class TencentSMSService:
    """腾讯云短信发送工具类"""

    @staticmethod
    def get_client(region="ap-guangzhou"):
        cred = credential.Credential(
            getattr(settings, "TENCENTCLOUD_SECRET_ID"),
            getattr(settings, "TENCENTCLOUD_SECRET_KEY"),
        )
        http_profile = HttpProfile(endpoint="sms.tencentcloudapi.com")
        client_profile = ClientProfile(httpProfile=http_profile)
        return sms_client.SmsClient(cred, region, client_profile)

    @staticmethod
    def send_sms(
        phone_number, code, app_id, sign_name, template_id, region="ap-guangzhou"
    ):
        """发送验证码短信"""
        client = TencentSMSService.get_client(region)
        req = models.SendSmsRequest()
        req.SmsSdkAppId = app_id
        req.SignName = sign_name
        req.TemplateId = template_id
        req.TemplateParamSet = [str(code), "5"]  # 模板参数，5分钟有效期
        req.PhoneNumberSet = [f"+86{phone_number}"]

        try:
            resp = client.SendSms(req)
            print(f"短信发送成功: {resp.to_json_string()}")
            return True
        except Exception as e:
            print(f"短信发送失败: {e}")
            return False


class SMSService:
    """短信验证码验证服务"""

    @staticmethod
    def send_code(phone_number, code):
        """发送验证码"""
        # 调用腾讯云短信服务
        sent = TencentSMSService.send_sms(
            phone_number=phone_number,
            code=code,
            app_id=getattr(settings, "TENCENT_SMS_APP_ID"),
            sign_name=getattr(settings, "TENCENT_SMS_SIGN"),
            template_id=getattr(settings, "TENCENT_SMS_TEMPLATE_ID"),
        )

        if sent:
            CacheService.set_value(
                key=f"sms:{phone_number}",
                val=code,
                exp=getattr(settings, "SMS_CODE_EXPIRE_SECONDS", 300),
            )
            return True
        return False

    @staticmethod
    def verify_code(phone_number, input_code):
        """验证验证码是否正确"""
        key = f"sms:{phone_number}"
        is_valid = CacheService.validate_value(key, input_code)
        if is_valid:
            CacheService.del_value(key)
        return is_valid


if __name__ == "__main__":
    SMSService.send_code("13820826029", 1244)
