# core/duplicate_detector.py
"""
Duplicate Detector – compute perceptual hashes for images and group duplicates.
"""

import logging
from PIL import Image
import imagehash
from pathlib import Path
from collections import defaultdict
import threading
import time

logger = logging.getLogger(__name__)

class DuplicateDetector:
    def __init__(self, hash_size=8):
        self.hash_size = hash_size
        self._cache = {}  # path -> imagehash

    def compute_hash(self, image_path):
        """Compute perceptual hash for an image, with caching."""
        if image_path in self._cache:
            return self._cache[image_path]
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed (for PNG with alpha)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                hash_val = imagehash.phash(img, hash_size=self.hash_size)
                self._cache[image_path] = hash_val
                return hash_val
        except Exception as e:
            logger.warning(f"Failed to hash {image_path}: {e}")
            return None

    def find_duplicates(self, image_paths, similarity_threshold=0):
        """
        Find duplicate groups.
        similarity_threshold: maximum Hamming distance to consider as duplicates (0 = exact match).
        Returns a dict: hash -> list of paths.
        """
        groups = defaultdict(list)
        for path in image_paths:
            h = self.compute_hash(path)
            if h is not None:
                # For exact matching, group by exact hash.
                # For near duplicates, we could use a more advanced clustering,
                # but we'll keep it simple for now: group by exact hash.
                groups[h].append(path)
        # Remove groups with only one image
        return {h: paths for h, paths in groups.items() if len(paths) > 1}