from rest_framework.views import exception_handler
from django.db import DatabaseError, IntegrityError
from rest_framework.response import Response
from rest_framework import status
import logging

# 获取自定义业务日志
logger = logging.getLogger('feat')


def database_exception_handler(exc, context):
    """
    自定义数据库异常处理器：
    - IntegrityError → 400 错误，提示前端检查数据
    - DatabaseError → 500 错误，提示服务器内部错误
    - 其他异常 → 调用 DRF 默认异常处理
    """
    # 调用 DRF 默认异常处理器
    response = exception_handler(exc, context)

    # 如果 DRF 默认处理不了，则处理数据库相关异常
    if response is None:
        if isinstance(exc, IntegrityError):
            # 写业务日志
            logger.error(f"数据完整性错误: {exc}", exc_info=True)
            # 返回前端简洁提示
            return Response(
                {"error": "数据完整性错误", "detail": "请检查输入数据"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif isinstance(exc, DatabaseError):
            # 写业务日志
            logger.error(f"数据库操作失败: {exc}", exc_info=True)
            # 返回前端简洁提示
            return Response(
                {"error": "数据库操作失败", "detail": "服务器内部错误，请稍后重试"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return response
