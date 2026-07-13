# core/advanced_bulk.py
"""
Advanced Bulk Operations – regex, merge, prefix, suffix, rename, split, etc.
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class AdvancedBulkOperations:
    @staticmethod
    def apply_regex_find_replace(tags: List[str], find_pattern: str, replace_pattern: str) -> List[str]:
        try:
            return [re.sub(find_pattern, replace_pattern, t) for t in tags]
        except re.error as e:
            logger.warning(f"Invalid regex pattern '{find_pattern}': {e}")
            return tags

    @staticmethod
    def apply_merge_tags(tags: List[str], merge_map: Dict[str, str]) -> List[str]:
        # merge_map: { "old_tag": "new_tag" } or list of tags to merge into one
        # For simplicity, we'll accept a list of tags to merge into the first one.
        result = []
        for tag in tags:
            if tag in merge_map:
                result.append(merge_map[tag])
            else:
                result.append(tag)
        return result

    @staticmethod
    def apply_split_tags(tags: List[str], delimiter: str) -> List[str]:
        new_tags = []
        for tag in tags:
            if delimiter in tag:
                new_tags.extend([t.strip() for t in tag.split(delimiter) if t.strip()])
            else:
                new_tags.append(tag)
        return new_tags

    @staticmethod
    def apply_prefix(tags: List[str], prefix: str) -> List[str]:
        return [f"{prefix}{t}" for t in tags]

    @staticmethod
    def apply_suffix(tags: List[str], suffix: str) -> List[str]:
        return [f"{t}{suffix}" for t in tags]

    @staticmethod
    def apply_rename_tags(tags: List[str], rename_map: Dict[str, str]) -> List[str]:
        return [rename_map.get(t, t) for t in tags]

    @staticmethod
    def apply_remove_by_pattern(tags: List[str], pattern: str) -> List[str]:
        try:
            return [t for t in tags if not re.search(pattern, t)]
        except re.error as e:
            logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            return tags

    @staticmethod
    def apply_sort_tags(tags: List[str], sort_type: str = "alphabetical") -> List[str]:
        if sort_type == "alphabetical":
            return sorted(tags)
        elif sort_type == "reverse":
            return sorted(tags, reverse=True)
        elif sort_type == "by_length":
            return sorted(tags, key=len)
        elif sort_type == "by_category":
            # Placeholder: we don't have category info, so just return sorted
            return sorted(tags)
        return tags

    @staticmethod
    def apply_normalize(tags: List[str]) -> List[str]:
        return sorted(set(tags))

    @staticmethod
    def apply_add_tag(tags: List[str], tag: str) -> List[str]:
        if tag not in tags:
            tags.append(tag)
        return tags

    @staticmethod
    def apply_remove_tag(tags: List[str], tag: str) -> List[str]:
        return [t for t in tags if t != tag]

    @staticmethod
    def apply_replace_tag(tags: List[str], old_tag: str, new_tag: str) -> List[str]:
        return [new_tag if t == old_tag else t for t in tags]