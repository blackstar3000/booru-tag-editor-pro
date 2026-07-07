from PyQt5.QtGui import QPixmap
from pathlib import Path
from PIL import Image, ImageQt
from .thumbnail_cache import ThumbnailCache
import logging

logger = logging.getLogger(__name__)

class ImageLoader:
    def __init__(self, cache_size=500):
        self.cache = ThumbnailCache(cache_size)

    def get_pixmap(self, path: Path):
        cached = self.cache.get(path)
        if cached is not None:
            return cached

        try:
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                # Fallback to Pillow
                pil_img = Image.open(path)
                qt_img = ImageQt.ImageQt(pil_img)
                pixmap = QPixmap.fromImage(qt_img)
            self.cache.put(path, pixmap)
            return pixmap
        except Exception as e:
            logger.error(f"Failed to load image {path}: {e}")
            return None