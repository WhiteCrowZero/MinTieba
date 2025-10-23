import io
from django.conf import settings
from PIL import Image, ExifTags


# ---------- 图片处理组件 ----------
class ImageProcessor:
    """图片处理器：压缩、EXIF旋转、格式转换"""

    @staticmethod
    def normalize_exif_orientation(img: Image.Image) -> Image.Image:
        try:
            for k, v in ExifTags.TAGS.items():
                if v == "Orientation":
                    orientation_key = k
                    break
            exif = img._getexif()
            if not exif:
                return img
            orientation = exif.get(orientation_key)
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
            return img
        except Exception:
            return img

    @staticmethod
    def compress_image(file_obj, max_width=None, quality=None):
        """压缩图片并返回 bytes 与 content_type"""
        max_width = max_width or getattr(settings, "OSS_MAX_IMAGE_WIDTH", 2000)
        quality = quality or getattr(settings, "OSS_DEFAULT_IMAGE_QUALITY", 85)

        file_obj.seek(0)
        buf = io.BytesIO(file_obj.read())
        img = Image.open(buf)
        img = ImageProcessor.normalize_exif_orientation(img)
        w, h = img.size
        if max(w, h) > max_width:
            scale = max_width / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        out_buf = io.BytesIO()
        fmt = (img.format or "JPEG").upper()
        fmt = fmt if fmt in ("JPEG", "PNG", "WEBP") else "JPEG"

        if fmt == "PNG":
            img.save(out_buf, format="PNG", optimize=True)
            ct = "image/png"
        elif fmt == "WEBP":
            img.save(out_buf, format="WEBP", quality=quality)
            ct = "image/webp"
        else:
            img.save(out_buf, format="JPEG", quality=quality, optimize=True)
            ct = "image/jpeg"

        return out_buf.getvalue(), ct
