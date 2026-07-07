# workers/metadata_worker.py
from PyQt5.QtCore import QRunnable, pyqtSignal, QObject
from core.ai_metadata_reader import AIMetadataReader
import logging

logger = logging.getLogger(__name__)

class MetadataWorkerSignals(QObject):
    finished = pyqtSignal(dict)  # metadata dict

class MetadataWorker(QRunnable):
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.signals = MetadataWorkerSignals()

    def run(self):
        try:
            metadata = AIMetadataReader.extract_metadata(self.image_path)
            self.signals.finished.emit(metadata)
        except Exception as e:
            logger.error(f"Metadata worker failed: {e}")
            self.signals.finished.emit({})