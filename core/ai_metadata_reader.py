# core/ai_metadata_reader.py
"""
AI Metadata Reader – extract prompts, parameters, and workflows from images.

Uses the same parsing logic as the Metadata Extractor Pro ComfyUI node:
- ComfyUI embedded workflow (walks node graph, follows text references)
- A1111/Forge/Civitai 'parameters' text block
- NovelAI, SwarmUI, Fooocus, etc. (basic support)
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# ── Constants from Metadata Extractor ──────────────────────────────────────

_SAMPLER_NODE_TYPES = {
    "KSampler", "KSamplerAdvanced", "SamplerCustom", "SamplerCustomAdvanced",
}
_CLIP_ENCODE_TYPES = {"CLIPTextEncode", "CLIPTextEncodeSDXL"}
_MODEL_LOADER_TYPES = {
    "CheckpointLoaderSimple": "ckpt_name",
    "CheckpointLoader": "ckpt_name",
    "unCLIPCheckpointLoader": "ckpt_name",
    "UNETLoader": "unet_name",
    "UnetLoaderGGUF": "unet_name",
    "UnetLoaderGGUFAdvanced": "unet_name",
    "CheckpointLoaderGGUF": "ckpt_name",
}
_LATENT_SIZE_TYPES = {"EmptyLatentImage", "EmptySD3LatentImage"}
_TEXT_CANDIDATE_KEYS = (
    "text", "positive", "negative", "string", "prompt", "value", "conditioning",
)


def _to_int(v):
    try:
        return int(float(str(v).strip()))
    except (TypeError, ValueError):
        return None


def _to_float(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def _blank_result():
    return {
        "found": False,
        "format": "none",
        "positive_prompt": "",
        "negative_prompt": "",
        "steps": None,
        "sampler_name": "",
        "cfg": None,
        "scheduler": "",
        "seed": None,
        "model_name": "",
        "width": None,
        "height": None,
        "raw": "",
    }


# ── A1111 / Civitai "parameters" text block parser ─────────────────────────

def _parse_a1111_parameters(text: str) -> dict:
    result = _blank_result()
    result["raw"] = text
    if not text:
        return result

    neg_idx = text.find("Negative prompt:")
    steps_idx = text.find("Steps:")

    if neg_idx != -1:
        result["positive_prompt"] = text[:neg_idx].strip()
        neg_end = steps_idx if steps_idx != -1 else len(text)
        result["negative_prompt"] = text[neg_idx + len("Negative prompt:"):neg_end].strip()
    elif steps_idx != -1:
        result["positive_prompt"] = text[:steps_idx].strip()
    else:
        result["positive_prompt"] = text.strip()

    if steps_idx != -1:
        tail = text[steps_idx:]
        for m in re.finditer(r'([A-Za-z ]+):\s*("(?:[^"\\]|\\.)*"|[^,]+)', tail):
            key = m.group(1).strip().lower()
            val = m.group(2).strip().strip('"')
            if key == "steps":
                result["steps"] = _to_int(val)
            elif key == "sampler":
                result["sampler_name"] = val
            elif key == "cfg scale":
                result["cfg"] = _to_float(val)
            elif key == "seed":
                result["seed"] = _to_int(val)
            elif key == "size":
                wh = val.lower().split("x")
                if len(wh) == 2:
                    result["width"] = _to_int(wh[0])
                    result["height"] = _to_int(wh[1])
            elif key == "model":
                result["model_name"] = val
            elif key == "schedule type":
                result["scheduler"] = val
    return result


# ── ComfyUI native "prompt" graph parser ────────────────────────────────────

def _parse_comfy_prompt_graph(prompt_json: str) -> dict:
    """
    Best-effort extraction from a ComfyUI API-format prompt graph.
    Walks known node types and follows text references through concatenation
    and utility nodes to extract the actual prompt text.
    """
    result = _blank_result()
    result["raw"] = prompt_json
    try:
        graph = json.loads(prompt_json)
    except (TypeError, ValueError):
        return result
    if not isinstance(graph, dict):
        return result

    def node_input(node, key, default=None):
        val = (node.get("inputs") or {}).get(key, default)
        return default if isinstance(val, list) else val

    def resolve_text(ref, depth=0, visited=None):
        """
        Follow a wired reference (or literal) to find the text it actually
        resolves to, walking through common text-utility custom nodes.
        """
        if depth > 10:
            return ""
        if isinstance(ref, str):
            return ref
        if not isinstance(ref, list) or not ref:
            return ""
        node_id = str(ref[0])
        if visited is None:
            visited = set()
        if node_id in visited:
            return ""
        visited = visited | {node_id}

        node = graph.get(node_id)
        if not isinstance(node, dict):
            return ""
        class_type = node.get("class_type", "")
        inputs = node.get("inputs") or {}

        if class_type == "Text Concatenate":
            delim = inputs.get("delimiter", ", ")
            if not isinstance(delim, str):
                delim = ", "
            parts = []
            for key in ("text_a", "text_b", "text_c", "text_d"):
                if key in inputs:
                    t = resolve_text(inputs[key], depth + 1, visited)
                    if t:
                        parts.append(t)
            return delim.join(parts)

        if class_type == "ShowText|pysssss":
            for key, val in inputs.items():
                if key != "text" and isinstance(val, str) and val:
                    return val
            return resolve_text(inputs.get("text"), depth + 1, visited)

        for key in _TEXT_CANDIDATE_KEYS:
            if key in inputs:
                return resolve_text(inputs[key], depth + 1, visited)

        for val in inputs.values():
            if isinstance(val, list):
                t = resolve_text(val, depth + 1, visited)
                if t:
                    return t
        for val in inputs.values():
            if isinstance(val, str) and val:
                return val
        return ""

    sampler_node = None
    for node in graph.values():
        if not isinstance(node, dict):
            continue
        if node.get("class_type") in _SAMPLER_NODE_TYPES:
            sampler_node = node
            break

    if sampler_node:
        result["seed"] = _to_int(
            node_input(sampler_node, "seed", node_input(sampler_node, "noise_seed"))
        )
        result["steps"] = _to_int(node_input(sampler_node, "steps"))
        result["cfg"] = _to_float(node_input(sampler_node, "cfg"))
        result["sampler_name"] = node_input(sampler_node, "sampler_name", "") or ""
        result["scheduler"] = node_input(sampler_node, "scheduler", "") or ""

        pos_ref = (sampler_node.get("inputs") or {}).get("positive")
        neg_ref = (sampler_node.get("inputs") or {}).get("negative")
        if pos_ref is not None:
            result["positive_prompt"] = resolve_text(pos_ref)
        if neg_ref is not None:
            result["negative_prompt"] = resolve_text(neg_ref)

    if not result["positive_prompt"] and not result["negative_prompt"]:
        # Fallback: grab the two longest CLIPTextEncode texts we can find.
        texts = []
        for node in graph.values():
            if not isinstance(node, dict):
                continue
            if node.get("class_type") in _CLIP_ENCODE_TYPES:
                t = node_input(node, "text", "")
                if t:
                    texts.append(t)
        texts.sort(key=len, reverse=True)
        if len(texts) >= 1:
            result["positive_prompt"] = texts[0]
        if len(texts) >= 2:
            result["negative_prompt"] = texts[1]

    for node in graph.values():
        if not isinstance(node, dict):
            continue
        loader_key = _MODEL_LOADER_TYPES.get(node.get("class_type"))
        if loader_key:
            result["model_name"] = node_input(node, loader_key, "") or ""
            break

    for node in graph.values():
        if not isinstance(node, dict):
            continue
        if node.get("class_type") in _LATENT_SIZE_TYPES:
            result["width"] = _to_int(node_input(node, "width"))
            result["height"] = _to_int(node_input(node, "height"))
            break

    return result


# ── Main Extraction Entrypoint ──────────────────────────────────────────────

class AIMetadataReader:
    @staticmethod
    def extract_metadata(image_path: Path) -> Dict[str, Any]:
        """
        Main entry point. Extracts all known AI metadata from the image.
        Returns a dict with keys: 'source', 'prompt', 'negative_prompt', 'settings', 'workflow', 'tags', etc.
        """
        result = {
            'source': 'unknown',
            'prompt': '',
            'negative_prompt': '',
            'settings': {},
            'workflow': None,
            'tags': [],
            'raw': {},
        }

        try:
            with Image.open(image_path) as img:
                info = dict(img.info or {})
        except Exception as e:
            logger.warning(f"Failed to open image {image_path}: {e}")
            return result

        # Check for ComfyUI embedded prompt JSON
        if "prompt" in info:
            parsed = _parse_comfy_prompt_graph(info["prompt"])
            parsed["found"] = True
            parsed["format"] = "comfyui"
            if "workflow" in info:
                result["workflow"] = info["workflow"]
            result["source"] = "ComfyUI"
            result["prompt"] = parsed.get("positive_prompt", "")
            result["negative_prompt"] = parsed.get("negative_prompt", "")
            settings = {}
            if parsed.get("seed") is not None:
                settings["seed"] = parsed["seed"]
            if parsed.get("steps") is not None:
                settings["steps"] = parsed["steps"]
            if parsed.get("cfg") is not None:
                settings["cfg"] = parsed["cfg"]
            if parsed.get("sampler_name"):
                settings["sampler_name"] = parsed["sampler_name"]
            if parsed.get("scheduler"):
                settings["scheduler"] = parsed["scheduler"]
            if parsed.get("model_name"):
                settings["model_name"] = parsed["model_name"]
            if parsed.get("width") is not None:
                settings["width"] = parsed["width"]
            if parsed.get("height") is not None:
                settings["height"] = parsed["height"]
            result["settings"] = settings
            result["raw"] = parsed
            return result

        # Check for A1111/Forge parameters
        if "parameters" in info:
            parsed = _parse_a1111_parameters(info["parameters"])
            parsed["found"] = True
            parsed["format"] = "a1111"
            result["source"] = "AUTOMATIC1111/Forge"
            result["prompt"] = parsed.get("positive_prompt", "")
            result["negative_prompt"] = parsed.get("negative_prompt", "")
            settings = {}
            if parsed.get("seed") is not None:
                settings["seed"] = parsed["seed"]
            if parsed.get("steps") is not None:
                settings["steps"] = parsed["steps"]
            if parsed.get("cfg") is not None:
                settings["cfg"] = parsed["cfg"]
            if parsed.get("sampler_name"):
                settings["sampler_name"] = parsed["sampler_name"]
            if parsed.get("scheduler"):
                settings["scheduler"] = parsed["scheduler"]
            if parsed.get("model_name"):
                settings["model_name"] = parsed["model_name"]
            if parsed.get("width") is not None:
                settings["width"] = parsed["width"]
            if parsed.get("height") is not None:
                settings["height"] = parsed["height"]
            result["settings"] = settings
            result["raw"] = parsed
            return result

        # Fallback: try to extract from other known keys
        for key in ["Description", "UserComment", "Comment"]:
            if key in info:
                val = info[key]
                if isinstance(val, str) and val.strip():
                    result["raw"][key] = val
                    if "prompt" in val.lower():
                        result["prompt"] = val
                    if "negative" in val.lower():
                        result["negative_prompt"] = val
                    result["source"] = "unknown (metadata found)"
                    break

        return result