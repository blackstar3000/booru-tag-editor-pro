"""
WorkspaceManager – save, load, rename, delete, duplicate, import, export
complete UI layout states as JSON files under settings/workspaces/.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

import logging

logger = logging.getLogger(__name__)

WORKSPACE_VERSION = 1
WORKSPACE_DIR = "settings/workspaces"


class WorkspaceManager:
    """Manages workspace JSON files on disk and exposes CRUD + import/export."""

    def __init__(self, base_dir: str | Path | None = None):
        if base_dir is None:
            base_dir = Path.cwd() / WORKSPACE_DIR
        self.workspaces_dir = Path(base_dir)
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)

    # ── public helpers ───────────────────────────────────────────────

    def list_workspaces(self) -> list[str]:
        """Return sorted list of workspace names (no extension)."""
        names = []
        for f in self.workspaces_dir.glob("*.json"):
            names.append(f.stem)
        return sorted(names)

    def exists(self, name: str) -> bool:
        return self._path_for(name).exists()

    # ── CRUD ────────────────────────────────────────────────────────

    def save(self, name: str, data: dict, overwrite: bool = True) -> Path:
        """Persist a workspace. Returns the file path."""
        path = self._path_for(name)
        if path.exists() and not overwrite:
            raise FileExistsError(f"Workspace '{name}' already exists.")
        data["name"] = name
        data["modified_date"] = datetime.now().isoformat()
        if "creation_date" not in data:
            data["creation_date"] = data["modified_date"]
        data["version"] = WORKSPACE_VERSION
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Workspace saved: {path}")
        return path

    def load(self, name: str) -> dict | None:
        """Load a workspace dict. Returns None if missing/corrupt."""
        path = self._path_for(name)
        if not path.exists():
            logger.warning(f"Workspace not found: {name}")
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return self._validate(data)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error(f"Failed to load workspace '{name}': {exc}")
            return None

    def delete(self, name: str) -> bool:
        path = self._path_for(name)
        if path.exists():
            path.unlink()
            logger.info(f"Workspace deleted: {name}")
            return True
        return False

    def rename(self, old_name: str, new_name: str) -> bool:
        old_path = self._path_for(old_name)
        new_path = self._path_for(new_name)
        if not old_path.exists() or new_path.exists():
            return False
        data = json.loads(old_path.read_text(encoding="utf-8"))
        data["name"] = new_name
        data["modified_date"] = datetime.now().isoformat()
        new_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        old_path.unlink()
        logger.info(f"Workspace renamed: {old_name} -> {new_name}")
        return True

    def duplicate(self, source_name: str, dest_name: str) -> bool:
        data = self.load(source_name)
        if data is None:
            return False
        data.pop("creation_date", None)
        try:
            self.save(dest_name, data, overwrite=False)
            return True
        except FileExistsError:
            return False

    # ── import / export ─────────────────────────────────────────────

    def export_workspace(self, name: str, dest_path: str | Path) -> Path:
        """Copy workspace file to an arbitrary location."""
        src = self._path_for(name)
        if not src.exists():
            raise FileNotFoundError(f"Workspace '{name}' not found.")
        dest = Path(dest_path)
        if dest.suffix != ".json":
            dest = dest / f"{name}.workspace.json"
        shutil.copy2(src, dest)
        logger.info(f"Workspace exported: {name} -> {dest}")
        return dest

    def import_workspace(self, file_path: str | Path, new_name: str | None = None) -> str | None:
        """Import a workspace JSON file. Returns the stored name or None."""
        src = Path(file_path)
        if not src.exists():
            logger.error(f"Import file not found: {src}")
            return None
        try:
            data = json.loads(src.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.error(f"Failed to read import file: {exc}")
            return None
        data = self._validate(data)
        if data is None:
            return None
        name = new_name or data.get("name") or src.stem.replace(".workspace", "")
        data["name"] = name
        data["creation_date"] = datetime.now().isoformat()
        self.save(name, data, overwrite=True)
        return name

    # ── internal ────────────────────────────────────────────────────

    def _path_for(self, name: str) -> Path:
        safe = name.replace("/", "_").replace("\\", "_")
        return self.workspaces_dir / f"{safe}.json"

    def _validate(self, data: dict) -> dict | None:
        """Basic schema validation; returns data or None if unrecoverable."""
        if not isinstance(data, dict):
            return None
        ver = data.get("version", 0)
        if ver > WORKSPACE_VERSION:
            logger.warning(
                f"Workspace version {ver} > supported {WORKSPACE_VERSION}; "
                "some fields may be ignored."
            )
        return data
