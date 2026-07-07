from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List

@dataclass
class ImageModel:
    path: Path
    metadata: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    thumbnail: Optional[bytes] = None  # not used yet; for future