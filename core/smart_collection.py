# core/smart_collection.py
"""
Smart Collections – dynamic image filtering based on rules.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from PIL import Image

logger = logging.getLogger(__name__)

class Condition:
    """A single condition for a smart collection rule."""
    def __init__(self, type: str, value: Any, operator: str = "contains"):
        self.type = type
        self.value = value
        self.operator = operator

    def evaluate(self, metadata: Dict[str, Any]) -> bool:
        """Evaluate this condition against image metadata."""
        if self.type == "tag_contains":
            tags = metadata.get('tags', [])
            return self.value in tags
        elif self.type == "tag_not_contains":
            tags = metadata.get('tags', [])
            return self.value not in tags
        elif self.type == "tag_count":
            count = len(metadata.get('tags', []))
            if self.operator == ">=":
                return count >= self.value
            elif self.operator == "<=":
                return count <= self.value
            elif self.operator == "==":
                return count == self.value
            elif self.operator == "!=":
                return count != self.value
            elif self.operator == ">":
                return count > self.value
            elif self.operator == "<":
                return count < self.value
        elif self.type == "width":
            width = metadata.get('width', 0)
            if self.operator == ">=":
                return width >= self.value
            elif self.operator == "<=":
                return width <= self.value
            elif self.operator == "==":
                return width == self.value
            elif self.operator == "!=":
                return width != self.value
            elif self.operator == ">":
                return width > self.value
            elif self.operator == "<":
                return width < self.value
        elif self.type == "height":
            height = metadata.get('height', 0)
            if self.operator == ">=":
                return height >= self.value
            elif self.operator == "<=":
                return height <= self.value
            elif self.operator == "==":
                return height == self.value
            elif self.operator == "!=":
                return height != self.value
            elif self.operator == ">":
                return height > self.value
            elif self.operator == "<":
                return height < self.value
        elif self.type == "file_type":
            file_type = metadata.get('file_type', '')
            if self.operator == "==":
                return file_type == self.value
            elif self.operator == "!=":
                return file_type != self.value
            elif self.operator == "in":
                return file_type in self.value
        elif self.type == "file_date":
            file_date = metadata.get('file_date', datetime.min)
            if self.operator == ">":
                return file_date > self.value
            elif self.operator == "<":
                return file_date < self.value
            elif self.operator == ">=":
                return file_date >= self.value
            elif self.operator == "<=":
                return file_date <= self.value
        elif self.type == "tag_has_any":
            tags = metadata.get('tags', [])
            return any(t in tags for t in self.value)
        elif self.type == "tag_has_all":
            tags = metadata.get('tags', [])
            return all(t in tags for t in self.value)
        return False


class SmartCollection:
    def __init__(self, name: str, conditions: List[Dict], logic: str = "AND"):
        self.name = name
        self.conditions = [Condition(**c) for c in conditions]
        self.logic = logic  # "AND" or "OR"

    def matches(self, metadata: Dict[str, Any]) -> bool:
        if not self.conditions:
            return True
        if self.logic == "AND":
            return all(c.evaluate(metadata) for c in self.conditions)
        else:  # OR
            return any(c.evaluate(metadata) for c in self.conditions)

    def to_dict(self):
        return {
            "name": self.name,
            "conditions": [
                {"type": c.type, "value": c.value, "operator": c.operator}
                for c in self.conditions
            ],
            "logic": self.logic
        }


class CollectionManager:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.collections: List[SmartCollection] = []
        self.load()

    def load(self):
        if not self.storage_path.exists():
            self.collections = []
            return
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.collections = [
                SmartCollection(
                    name=item['name'],
                    conditions=item['conditions'],
                    logic=item.get('logic', 'AND')
                )
                for item in data
            ]
        except Exception as e:
            logger.warning(f"Failed to load collections: {e}")
            self.collections = []

    def save(self):
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump([c.to_dict() for c in self.collections], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save collections: {e}")

    def add(self, collection: SmartCollection):
        self.collections.append(collection)
        self.save()

    def delete(self, name: str):
        self.collections = [c for c in self.collections if c.name != name]
        self.save()

    def get(self, name: str) -> Optional[SmartCollection]:
        for c in self.collections:
            if c.name == name:
                return c
        return None