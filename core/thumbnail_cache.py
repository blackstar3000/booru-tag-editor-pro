from collections import OrderedDict
from PyQt5.QtGui import QPixmap
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ThumbnailCache:
    def __init__(self, max_size=500):
        self.max_size = max_size
        self._cache = OrderedDict()

    def get(self, path: Path):
        return self._cache.get(path)

    def put(self, path: Path, pixmap: QPixmap):
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
        self._cache[path] = pixmap
        logger.debug(f"Cached thumbnail for {path.name}")
        return pixmap

    def clear(self):
        self._cache.clear()
        logger.info("Thumbnail cache cleared")