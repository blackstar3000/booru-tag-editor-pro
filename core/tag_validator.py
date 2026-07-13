import csv
import logging
import re
import difflib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "danbooru_full.csv"

EXTRA_ALIASES = {
    "silver_hair": "grey_hair",
    "silver_eyes": "grey_eyes",
    "golden_hair": "blonde_hair",
}

CATEGORY_NAMES = {
    0: "general",
    1: "artist",
    3: "copyright",
    4: "character",
    5: "meta",
}

NOVA_ANIME_XL_TEMPLATE = (
    "masterpiece, best quality, amazing quality, 4k, very aesthetic, "
    "high resolution, ultra-detailed, absurdres, newest, scenery, "
    "{prompt}, BREAK, depth of field, volumetric lighting"
)

TEMPLATE_PRESETS = {
    "nova_anime_xl": NOVA_ANIME_XL_TEMPLATE,
    "illustrious": ("masterpiece, best quality, very aesthetic, absurdres, "
                    "{prompt}"),
    "pony": "score_9, score_8_up, score_7_up, source_anime, {prompt}",
    "animagine_xl": ("{prompt}, masterpiece, best quality, very aesthetic, "
                     "absurdres"),
    "tags_only": "{prompt}",
    "custom": "{prompt}",
}

DEFAULT_SYSTEM_PROMPT = (
    "You convert a scene description into Danbooru tags for an anime image model. "
    "Output ONLY lowercase tags separated by commas. "
    "No sentences, no explanations, no numbering, no category words. "
    "Write attributes in real Danbooru tag style: 'blue eyes' not 'eye color blue', "
    "'black hair' not 'hair color black'. Use spaces, not underscores. "
    "Use 1girl, 1boy, 2girls, etc. for people. "
    "Do NOT add quality tags like masterpiece, best quality, absurdres, score_9 - "
    "those are added separately.\n"
    "Example input: a cheerful blonde girl in a red dress on a beach at sunset\n"
    "Example output: 1girl, blonde hair, long hair, smile, red dress, beach, sunset, "
    "ocean, sky, cloud, standing\n"
    "Example input: a lone samurai in the rain at night\n"
    "Example output: 1boy, solo, samurai, japanese clothes, katana, rain, night, wet, "
    "serious, outdoors\n"
    "Now output tags only for the next description. /no_think"
)

_WS = re.compile(r"\s+")
_HAS_LETTER = re.compile(r"[a-z]")

_COUNT_TAG = re.compile(
    r"^(?:\d+(?:girls?|boys?|others?)|solo|multiple_girls|multiple_boys"
    r"|multiple_others)$")
_CATEGORY_ORDER = {4: 1, 3: 2, 1: 3, 0: 4, 5: 5}


def _sort_group(norm, category):
    if category == 0 and _COUNT_TAG.match(norm):
        return 0
    return _CATEGORY_ORDER.get(category, 4)


def normalize(tag):
    t = tag.strip().lower()
    t = t.replace("\\(", "(").replace("\\)", ")")
    t = _WS.sub(" ", t).strip()
    t = t.replace(" ", "_")
    return t


def _morph_variants(norm):
    out = []
    if "_" in norm:
        head, _, tail = norm.rpartition("_")
        prefix = head + "_"
    else:
        prefix, tail = "", norm
    for suf, repl in (("ing", ""), ("ing", "e"), ("ed", ""), ("ed", "e"),
                      ("es", ""), ("s", "")):
        if tail.endswith(suf) and len(tail) - len(suf) >= 3:
            out.append(prefix + tail[:-len(suf)] + repl)
    if not tail.endswith("s") and len(tail) >= 3:
        out.append(prefix + tail + "s")
    return out


def to_prompt(tag):
    if _HAS_LETTER.search(tag):
        t = tag.replace("_", " ")
    else:
        t = tag
    return t.replace("(", "\\(").replace(")", "\\)")


def apply_template(template, prompt):
    if "{prompt}" in template:
        return template.replace("{prompt}", prompt)
    if not template.strip():
        return prompt
    return template.rstrip().rstrip(",") + ", " + prompt


def get_template_names():
    return list(TEMPLATE_PRESETS.keys())


class TagValidator:
    def __init__(self, path=None):
        self._path = Path(path) if path else _DATA_PATH
        self.canonical = {}
        self.alias = {}
        self._keys = None
        self._loaded = False
        self._total_tags = 0

    def load(self) -> bool:
        if self._loaded:
            return True
        if not self._path.exists():
            logger.warning(f"Tag database not found: {self._path}")
            return False
        try:
            with open(self._path, encoding="utf-8", newline="") as f:
                for row in csv.reader(f):
                    if not row or not row[0].strip():
                        continue
                    tag = row[0].strip()
                    category = int(row[1]) if len(row) > 1 and row[1].strip().isdigit() else 0
                    count = int(row[2]) if len(row) > 2 and row[2].strip().isdigit() else 0
                    norm = normalize(tag)
                    if not norm:
                        continue
                    self.canonical[norm] = (tag, category, count)
                    if len(row) > 3 and row[3]:
                        for a in row[3].split(","):
                            a = normalize(a)
                            if a and a not in self.canonical and a not in self.alias:
                                self.alias[a] = norm
            for a, canon in EXTRA_ALIASES.items():
                if canon in self.canonical and a not in self.canonical:
                    self.alias.setdefault(a, canon)
            self._total_tags = len(self.canonical)
            self._loaded = True
            logger.info(f"Loaded {self._total_tags} tags from {self._path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load tag database: {e}")
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def total_tags(self) -> int:
        return self._total_tags

    def _lookup(self, norm):
        if norm in self.canonical:
            return norm
        if norm in self.alias:
            return self.alias[norm]
        return None

    def resolve(self, candidate, fuzzy_cutoff=0.0):
        norm = normalize(candidate)
        if not norm:
            return None
        direct = self._lookup(norm)
        if direct:
            return direct
        for v in _morph_variants(norm):
            hit = self._lookup(v)
            if hit:
                return hit
        if fuzzy_cutoff and fuzzy_cutoff > 0:
            if self._keys is None:
                self._keys = list(self.canonical.keys())
            hit = difflib.get_close_matches(norm, self._keys, n=1, cutoff=fuzzy_cutoff)
            if hit:
                return hit[0]
        return None

    def extract(self, candidate, fuzzy_cutoff=0.0):
        toks = [w for w in re.split(r"\s+", candidate.strip().lower()) if w]
        if len(toks) < 2:
            return []
        found, i = [], 0
        while i < len(toks):
            matched = False
            for j in range(len(toks), i, -1):
                sub = "_".join(toks[i:j])
                hit = self.resolve(sub, fuzzy_cutoff) if j - i > 1 else self._lookup(sub)
                if hit:
                    found.append(hit)
                    i = j
                    matched = True
                    break
            if not matched:
                i += 1
        return found

    def get_info(self, tag: str) -> Optional[Dict[str, Any]]:
        norm = normalize(tag)
        if not norm:
            return None
        resolved = self._lookup(norm)
        if not resolved:
            for v in _morph_variants(norm):
                resolved = self._lookup(v)
                if resolved:
                    break
        if not resolved:
            return None
        orig, category, count = self.canonical[resolved]
        return {
            'name': orig,
            'normalized': resolved,
            'category': category,
            'category_name': CATEGORY_NAMES.get(category, 'unknown'),
            'post_count': count,
        }

    def get_aliases(self, tag: str) -> List[str]:
        norm = normalize(tag)
        resolved = self._lookup(norm) or norm
        aliases = []
        for alias_norm, canon in self.alias.items():
            if canon == resolved:
                orig = self.canonical.get(resolved, (resolved, 0, 0))[0]
                aliases.append(alias_norm.replace("_", " "))
        return aliases

    def validate(self, text, strict=True, fuzzy_cutoff=0.0,
                 min_post_count=0, max_tags=0, exclude_categories=None,
                 sort_tags=False):
        exclude = set(exclude_categories or ())
        kept, dropped, seen = [], [], set()

        def accept(norm):
            _orig, category, count = self.canonical[norm]
            if category in exclude:
                return False
            if min_post_count and count < min_post_count:
                return False
            if norm in seen:
                return True
            if max_tags and len(kept) >= max_tags:
                return False
            seen.add(norm)
            kept.append((norm, category))
            return True

        for cand in (c.strip() for c in text.split(",")):
            if not cand:
                continue
            if max_tags and len(kept) >= max_tags:
                break

            norm = self.resolve(cand, fuzzy_cutoff)
            if norm is not None:
                if not accept(norm):
                    dropped.append(cand)
                continue

            subs = self.extract(cand, fuzzy_cutoff)
            if subs:
                results = [accept(s) for s in subs]
                if any(results):
                    continue

            if strict:
                dropped.append(cand)
            else:
                key = normalize(cand)
                if key not in seen:
                    seen.add(key)
                    kept.append((key, 0))

        if sort_tags:
            kept.sort(key=lambda e: _sort_group(e[0], e[1]))
        out = [to_prompt(norm) for norm, _cat in kept]
        return ", ".join(out), out, dropped


_validator = None


def get_validator() -> Optional[TagValidator]:
    global _validator
    if _validator is None:
        _validator = TagValidator()
        if not _validator.load():
            _validator = None
    return _validator
