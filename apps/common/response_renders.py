from rest_framework.renderers import JSONRenderer

class UnifiedJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response")
        unified_data = {
            "code": response.status_code if response else 200,
            "message": "失败" if response and response.status_code >= 400 else "成功",
            "detail": data,
        }
        return super().render(unified_data, accepted_media_type, renderer_context)
