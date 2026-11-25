from rest_framework.renderers import JSONRenderer

class EnvelopeJSONRenderer(JSONRenderer):
    """Keep successful API payloads in a uniform {success, data} envelope."""
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, dict) and "success" in data:
            wrapped = data
        else:
            wrapped = {"success": True, "data": data}
        return super().render(wrapped, accepted_media_type, renderer_context)
