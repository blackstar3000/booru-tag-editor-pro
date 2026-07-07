from PyQt5.QtCore import QRunnable, pyqtSignal, QObject
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ThumbnailSignals(QObject):
    finished = pyqtSignal(Path, object)  # path, QPixmap
    progress = pyqtSignal(int, int)

class ThumbnailWorker(QRunnable):
    def __init__(self, image_paths, image_loader):
        super().__init__()
        self.image_paths = image_paths
        self.image_loader = image_loader
        self.signals = ThumbnailSignals()

    def run(self):
        total = len(self.image_paths)
        for i, path in enumerate(self.image_paths):
            pixmap = self.image_loader.get_pixmap(path)
            if pixmap:
                self.signals.finished.emit(path, pixmap)
            self.signals.progress.emit(i+1, total)