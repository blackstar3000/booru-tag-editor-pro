# core/booru_source_manager.py
# Manages multiple booru API clients, merges results, routes requests.

import logging
from typing import Dict, List, Optional

from PyQt5.QtCore import QObject, pyqtSignal

from core.booru_client_base import BooruClientBase, _normalize_tag
from core.settings_manager import SettingsManager

logger = logging.getLogger(__name__)


class BooruSourceManager(QObject):
    """Central manager for multiple booru sources.

    Owns all booru clients, provides unified signals for consumers,
    and merges autocomplete results from all active sources.
    """

    # Unified signals (consumers connect to these)
    autocomplete_results = pyqtSignal(str, list)         # (query, merged_tags)
    autocomplete_error = pyqtSignal(str, str)             # (query, error)
    tag_info_fetched = pyqtSignal(str, dict)              # (tag, info)
    tag_info_error = pyqtSignal(str, str)                 # (tag, error)
    wiki_fetched = pyqtSignal(str, str)                   # (tag, body)
    wiki_error = pyqtSignal(str, str)                     # (tag, error)
    example_posts_fetched = pyqtSignal(str, list)         # (tag, posts)
    example_posts_error = pyqtSignal(str, str)            # (tag, error)
    preview_loaded = pyqtSignal(str, int, object)         # (tag, index, pixmap)
    post_fetched = pyqtSignal(str, dict)                   # (source_name, post_data)
    post_fetch_error = pyqtSignal(str, str)                # (source_name, error)
    search_posts_results = pyqtSignal(str, str, list)    # (source_name, query, posts)
    search_posts_error = pyqtSignal(str, str, str)       # (source_name, query, error)
    credentials_missing = pyqtSignal()

    def __init__(self, settings: SettingsManager):
        super().__init__()
        self.settings = settings
        self._clients: Dict[str, BooruClientBase] = {}
        self._source_order: List[str] = []
        self._autocomplete_buffers: Dict[str, dict] = {}  # query -> {source_name: tags}
        self._pending_autocomplete: Dict[str, int] = {}   # query -> remaining sources
        self._search_posts_buffers: Dict[str, dict] = {}  # query -> {source_name: posts}
        self._pending_search_posts: Dict[str, int] = {}   # query -> remaining sources

    def register_client(self, client: BooruClientBase):
        """Register a booru client as an available source."""
        self._clients[client.source_name] = client
        if client.source_name not in self._source_order:
            self._source_order.append(client.source_name)

        # Connect client signals to our handlers
        client.autocomplete_results.connect(self._on_client_autocomplete)
        client.autocomplete_error.connect(self._on_client_autocomplete_error)
        client.tag_info_fetched.connect(self._on_client_tag_info)
        client.tag_info_error.connect(self._on_client_tag_info_error)
        client.wiki_fetched.connect(self._on_client_wiki)
        client.wiki_error.connect(self._on_client_wiki_error)
        client.example_posts_fetched.connect(self._on_client_example_posts)
        client.example_posts_error.connect(self._on_client_example_posts_error)
        client.preview_loaded.connect(self._on_client_preview)
        client.post_fetched.connect(self._on_client_post_fetched)
        client.post_fetch_error.connect(self._on_client_post_fetch_error)
        client.search_posts_results.connect(self._on_client_search_posts)
        client.search_posts_error.connect(self._on_client_search_posts_error)
        client.credentials_missing.connect(self._on_client_credentials_missing)

        logger.info(f"Registered booru source: {client.source_name}")

    def get_client(self, source_name: str) -> Optional[BooruClientBase]:
        return self._clients.get(source_name)

    def get_enabled_clients(self) -> List[BooruClientBase]:
        return [self._clients[name] for name in self._source_order if self._clients[name].enabled]

    def get_source_names(self) -> List[str]:
        return [name for name in self._source_order if name in self._clients]

    def get_enabled_source_names(self) -> List[str]:
        return [name for name in self._source_order if name in self._clients and self._clients[name].enabled]

    def set_source_enabled(self, source_name: str, enabled: bool):
        if source_name in self._clients:
            self._clients[source_name].enabled = enabled
            self.settings.set(f"source_{source_name}_enabled", enabled)
            logger.info(f"Source {source_name} {'enabled' if enabled else 'disabled'}")

    def load_source_states(self):
        """Load enabled/disabled states from settings."""
        for name in self._source_names():
            enabled = self.settings.get(f"source_{name}_enabled", True)
            if name in self._clients:
                self._clients[name].enabled = enabled

    def _source_names(self):
        return list(self._clients.keys())

    def reload_all_settings(self):
        """Reload credentials for all sources."""
        for client in self._clients.values():
            client.reload_settings()
        self.load_source_states()

    def autocomplete(self, query: str):
        """Request autocomplete from all enabled sources, merge results."""
        enabled = self.get_enabled_clients()
        if not enabled:
            self.autocomplete_results.emit(query, [])
            return

        self._autocomplete_buffers[query] = {}
        self._pending_autocomplete[query] = len(enabled)

        for client in enabled:
            client.autocomplete(query)

    def fetch_tag_info(self, tag: str):
        """Fetch tag info from the first enabled source."""
        tag = _normalize_tag(tag)
        for client in self.get_enabled_clients():
            client.fetch_tag_info(tag)
            return
        self.tag_info_error.emit(tag, "No enabled sources")

    def fetch_wiki(self, tag: str):
        """Fetch wiki from all enabled sources (first to respond wins)."""
        tag = _normalize_tag(tag)
        for client in self.get_enabled_clients():
            client.fetch_wiki(tag)
            return
        self.wiki_error.emit(tag, "No enabled sources")

    def fetch_example_posts(self, tag: str):
        """Fetch example posts from the first enabled source."""
        tag = _normalize_tag(tag)
        for client in self.get_enabled_clients():
            client.fetch_example_posts(tag)
            return
        self.example_posts_error.emit(tag, "No enabled sources")

    def fetch_preview_image(self, tag: str, index: int, url: str):
        """Fetch preview image using the first enabled source."""
        tag = _normalize_tag(tag)
        for client in self.get_enabled_clients():
            client.fetch_preview_image(tag, index, url)
            return

    def fetch_post_by_id(self, post_id: str, source_name: str = None):
        """Fetch a single post by ID from a specific source (or first enabled)."""
        if source_name:
            client = self.get_client(source_name)
            if client and client.enabled:
                client.fetch_post_by_id(post_id)
                return
            self.post_fetch_error.emit(source_name, f"Source '{source_name}' not available")
            return
        for client in self.get_enabled_clients():
            client.fetch_post_by_id(post_id)
            return
        self.post_fetch_error.emit("", "No enabled sources")

    def search_posts(self, query: str, source_name: str = None, limit: int = 20):
        """Search for posts by tag from a specific source, or all enabled sources."""
        if source_name:
            client = self.get_client(source_name)
            if client and client.enabled:
                client.search_posts(query, limit)
                return
            self.search_posts_error.emit(source_name, query, f"Source '{source_name}' not available")
            return
        enabled = self.get_enabled_clients()
        if not enabled:
            self.search_posts_error.emit("", query, "No enabled sources")
            return
        self._search_posts_buffers[query] = {}
        self._pending_search_posts[query] = len(enabled)
        for client in enabled:
            client.search_posts(query, limit)

    # --- Signal handlers ---

    def _on_client_autocomplete(self, source_name, query, tags):
        if query not in self._autocomplete_buffers:
            return
        self._autocomplete_buffers[query][source_name] = tags
        self._pending_autocomplete[query] -= 1

        if self._pending_autocomplete[query] <= 0:
            merged = self._merge_autocomplete(query)
            del self._autocomplete_buffers[query]
            del self._pending_autocomplete[query]
            self.autocomplete_results.emit(query, merged)

    def _merge_autocomplete(self, query: str) -> list:
        """Merge autocomplete results from all sources, prioritizing by source order."""
        buffers = self._autocomplete_buffers.get(query, {})
        seen = set()
        merged = []

        for source_name in self._source_order:
            if source_name not in buffers:
                continue
            for tag in buffers[source_name]:
                name = tag.get('name', '') if isinstance(tag, dict) else str(tag)
                if name and name not in seen:
                    seen.add(name)
                    if isinstance(tag, dict):
                        tag['source'] = source_name
                    merged.append(tag)
        return merged

    def _on_client_autocomplete_error(self, source_name, query, error):
        # Auth failures are expected when credentials aren't configured - log at debug level
        if '401' in str(error) or '403' in str(error):
            logger.debug(f"Auth error from {source_name} for '{query}': {error}")
        else:
            logger.warning(f"Autocomplete error from {source_name} for '{query}': {error}")
        if query in self._pending_autocomplete:
            self._pending_autocomplete[query] -= 1
            if self._pending_autocomplete[query] <= 0:
                merged = self._merge_autocomplete(query)
                del self._autocomplete_buffers[query]
                del self._pending_autocomplete[query]
                if merged:
                    self.autocomplete_results.emit(query, merged)
                else:
                    self.autocomplete_error.emit(query, error)

    def _on_client_tag_info(self, source_name, tag, info):
        info['source'] = source_name
        self.tag_info_fetched.emit(tag, info)

    def _on_client_tag_info_error(self, source_name, tag, error):
        if '401' in str(error) or '403' in str(error):
            logger.debug(f"Auth error from {source_name} for tag '{tag}': {error}")
        else:
            logger.warning(f"Tag info error from {source_name} for '{tag}': {error}")
        self.tag_info_error.emit(tag, error)

    def _on_client_wiki(self, source_name, tag, body):
        self.wiki_fetched.emit(tag, body)

    def _on_client_wiki_error(self, source_name, tag, error):
        logger.warning(f"Wiki error from {source_name} for '{tag}': {error}")
        self.wiki_error.emit(tag, error)

    def _on_client_example_posts(self, source_name, tag, posts):
        self.example_posts_fetched.emit(tag, posts)

    def _on_client_example_posts_error(self, source_name, tag, error):
        logger.warning(f"Example posts error from {source_name} for '{tag}': {error}")
        self.example_posts_error.emit(tag, error)

    def _on_client_preview(self, source_name, tag, index, pixmap):
        self.preview_loaded.emit(tag, index, pixmap)

    def _on_client_post_fetched(self, source_name, post_data):
        self.post_fetched.emit(source_name, post_data)

    def _on_client_post_fetch_error(self, source_name, error):
        self.post_fetch_error.emit(source_name, error)

    def _on_client_search_posts(self, source_name, query, posts):
        if query in self._search_posts_buffers:
            self._search_posts_buffers[query][source_name] = posts
            self._pending_search_posts[query] -= 1

            if self._pending_search_posts[query] <= 0:
                merged = self._merge_search_posts(query)
                del self._search_posts_buffers[query]
                del self._pending_search_posts[query]
                self.search_posts_results.emit("All Sources", query, merged)
        else:
            for post in posts:
                post.setdefault('source', source_name)
            self.search_posts_results.emit(source_name, query, posts)

    def _merge_search_posts(self, query: str) -> list:
        """Merge search results from all sources."""
        buffers = self._search_posts_buffers.get(query, {})
        seen = set()
        merged = []
        for source_name in self._source_order:
            if source_name not in buffers:
                continue
            for post in buffers[source_name]:
                post_id = post.get('id')
                if not post_id:
                    continue
                key = f"{source_name}:{post_id}"
                if key not in seen:
                    seen.add(key)
                    post['source'] = source_name
                    merged.append(post)
        return merged

    def _on_client_search_posts_error(self, source_name, query, error):
        logger.warning(f"Search posts error from {source_name} for '{query}': {error}")
        if query in self._pending_search_posts:
            self._pending_search_posts[query] -= 1
            if self._pending_search_posts[query] <= 0:
                merged = self._merge_search_posts(query) if query in self._search_posts_buffers else []
                if query in self._search_posts_buffers:
                    del self._search_posts_buffers[query]
                if query in self._pending_search_posts:
                    del self._pending_search_posts[query]
                if merged:
                    self.search_posts_results.emit("All Sources", query, merged)
                else:
                    self.search_posts_error.emit("All Sources", query, error)
        else:
            self.search_posts_error.emit(source_name, query, error)

    def _on_client_credentials_missing(self, source_name):
        logger.info(f"Credentials missing for {source_name}")
        self.credentials_missing.emit()
