from PyQt5.QtCore import QRunnable, pyqtSignal, QObject, QThreadPool
from pathlib import Path
import logging

class FolderScanSignals(QObject):
    started = pyqtSignal()
    finished = pyqtSignal(list)  # list of paths
    progress = pyqtSignal(int, int)
    error = pyqtSignal(str)

class FolderScanWorker(QRunnable):
    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.signals = FolderScanSignals()
        self.image_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif')

    def run(self):
        self.signals.started.emit()
        try:
            folder = Path(self.folder_path)
            images = []
            # iterating over directory (non-recursive)
            for item in folder.iterdir():
                if item.is_file() and item.suffix.lower() in self.image_extensions:
                    images.append(item)
            images.sort()
            # could emit progress
            self.signals.finished.emit(images)
        except Exception as e:
            logging.getLogger(__name__).exception("Folder scan error")
            self.signals.error.emit(str(e))