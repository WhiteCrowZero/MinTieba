import io
import hashlib
import logging
from datetime import timedelta
from typing import Optional

from django.conf import settings
from minio import Minio

from common.exceptions import MinioOperationError, UploadImageError
from common.utils.image_utils import ImageProcessor

logger = logging.getLogger("feat")


# ---------- MinIO 客户端封装 ----------
class MinioClientWrapper:
    """MinIO 客户端操作封装"""

    @staticmethod
    def get_client():
        return Minio(
            endpoint=getattr(settings, "MINIO_ENDPOINT"),
            access_key=getattr(settings, "MINIO_ACCESS_KEY"),
            secret_key=getattr(settings, "MINIO_SECRET_KEY"),
            secure=getattr(settings, "MINIO_USE_SSL", False),
        )

    @staticmethod
    def ensure_bucket(client=None, bucket=None):
        client = client or MinioClientWrapper.get_client()
        bucket = bucket or getattr(settings, "MINIO_BUCKET_NAME")
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
        return client, bucket

    @staticmethod
    def upload_bytes(
        data: bytes, object_name: str, content_type: str, bucket=None, client=None
    ):
        """上传数据"""
        try:
            client, bucket = MinioClientWrapper.ensure_bucket(client, bucket)
            client.put_object(
                bucket,
                object_name,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            logger.info(f"上传文件成功: {object_name}")
            return object_name
        except Exception as e:
            raise MinioOperationError(f"MinIO 上传失败: {object_name}") from e

    @staticmethod
    def get_presigned_url(
        object_name: str, bucket=None, client=None, expires_time=timedelta(hours=3)
    ):
        """获取对象URL，可设置临时链接或者公开永久链接"""
        if not object_name:
            raise MinioOperationError("获取URL失败: object_name 不能为空")
        client, bucket = MinioClientWrapper.ensure_bucket(client, bucket)
        return client.presigned_get_object(bucket, object_name, expires=expires_time)

    @staticmethod
    def get_public_url(object_name: str, bucket=None, client=None):
        """获取公开URL"""
        if not object_name:
            raise MinioOperationError("获取URL失败: object_name 不能为空")
        client, bucket = MinioClientWrapper.ensure_bucket(client, bucket)
        # return f"https://{getattr(settings, 'MINIO_ENDPOINT')}/{bucket}/{object_name}"
        return f"http://{getattr(settings, 'MINIO_ENDPOINT')}/{bucket}/{object_name}"


# ---------- OSS 服务工具封装 ----------


class OssService:
    """文件上传服务（组合模式 + 静态方法）"""

    @staticmethod
    def calc_checksum(data: bytes) -> str:
        """计算文件内容的 SHA256 哈希值"""
        h = hashlib.sha256()
        h.update(data)
        return h.hexdigest()

    @staticmethod
    def upload_image(
        uploaded_file,
        folder_name=None,
        compress=True,
        processor=None,
        client_wrapper=None,
        expires_time:Optional[timedelta]=None,
    ):
        """
        上传图片并返回 URL
        processor: 可传入自定义 ImageProcessor
        client_wrapper: 可传入自定义 MinioClientWrapper 或者其他封装的第三方方API
                        只需要实现 upload_bytes 和 get_presigned_url 方法
        """
        processor = processor or ImageProcessor
        if not client_wrapper:
            raise UploadImageError("client_wrapper 不能为空")
        if not folder_name:
            folder_name = getattr(settings, "DEFAULT_IMAGE_FOLDER_NAME")

        uploaded_file.seek(0)
        raw_data = uploaded_file.read()

        # 压缩图片
        if compress:
            data, content_type = processor.compress_image(io.BytesIO(raw_data))
        else:
            data = raw_data
            content_type = uploaded_file.content_type

        # 计算 checksum 做对象名
        checksum = OssService.calc_checksum(data)
        ext = uploaded_file.name.split(".")[-1].lower()
        object_name = f"{folder_name}/{checksum}.{ext}"

        try:
            # 上传
            client_wrapper.upload_bytes(data, object_name, content_type)
            # 生成 URL
            if not expires_time:
                url = client_wrapper.get_public_url(object_name)
            else:
                url = client_wrapper.get_presigned_url(
                    object_name, expires_time=expires_time
                )
        except Exception as e:
            raise UploadImageError(f"OSS处理上传图片失败: {object_name}") from e
        return {
            "object_name": object_name,
            "url": url,
            "checksum": checksum,
            "size": len(data),
            "content_type": content_type,
        }
