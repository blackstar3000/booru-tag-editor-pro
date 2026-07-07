from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class ImageModel:
    path: Path
    metadata: dict = None
    tags: list = None
    thumbnail: Optional[bytes] = None  # we might not store in model, but in cache