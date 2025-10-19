from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


User = get_user_model()


# class RegisterSerializer(CaptchaValidateMixin, serializers.ModelSerializer):

class RegisterSerializer(serializers.ModelSerializer):
    """普通注册序列化器，负责用户名或者邮箱注册"""

    # 密码和二次确认密码
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    # 用户和邮箱保持唯一性，防止重复
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="该用户名已被使用")]
    )
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="该邮箱已被注册")]
    )

    # # 额外添加的校验码字段
    # captcha_id = serializers.CharField(write_only=True)
    # captcha_code = serializers.CharField(write_only=True)

    class Meta:
        model = User
        # fields = ['username', 'email', 'password', 'confirm_password', 'captcha_id', 'captcha_code']
        fields = ['username', 'email', 'password', 'confirm_password']

    def validate(self, attrs):
        # # 单独使用工具类校验 captcha
        # attrs = self.validate_captcha(attrs)  # 直接传 attrs
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "两次输入的密码不一致"})
        return attrs

    def validate_username(self, value):
        if '@' in value:
            raise serializers.ValidationError({"username": "不能含有 @ 符号"})
        return value

    def create(self, validated_data):
        # 保留密码字段
        password = validated_data.pop('password')

        # 其余字段检验完后丢弃
        validated_data.pop('confirm_password')
        # validated_data.pop('captcha_id')
        # validated_data.pop('captcha_code')

        # 其余字段创建模型
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
