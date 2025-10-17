from rest_framework.response import Response


class UnifiedResponseMiddleware:
    """
    对所有 DRF Response 进行统一格式封装：
    {
        code: 状态码,
        message: 成功/失败,
        detail: 数据
    }
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return self.process_response(request, response)

    def process_response(self, request, response):
        if isinstance(response, Response):
            response.data = {
                "code": response.status_code,
                "message": "失败" if response.status_code >= 400 else "成功",
                # 保留原来的 detail data
                "detail": getattr(response, "data", None),
            }
            # JsonResponse 必须重置 content
            response._is_rendered = False
        return response
