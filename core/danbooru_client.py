# core/danbooru_client.py
# Production-ready Danbooru API client with custom User-Agent, caching, rate limiting, retries, and background workers.

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import cloudscraper
import requests
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool, QTimer
from PyQt5.QtCore import QMetaObject, Qt

from core.settings_manager import SettingsManager

logger = logging.getLogger(__name__)

# --- Configuration ---
CACHE_TTL = 3600  # 1 hour
MAX_RETRIES = 3
BASE_RETRY_DELAY = 1.0  # seconds
REQUESTS_PER_SECOND = 1  # Danbooru free tier
RATE_LIMIT_BURST = 1

# Custom User-Agent that identifies the app (as recommended by Danbooru forum)
APP_USER_AGENT = "BooruTagEditorPro/1.0 (user: bossgame; contact: bossgame@example.com)"

# --- Helper Classes ---

class _CacheManager:
    """LRU cache with TTL."""
    def __init__(self, ttl=CACHE_TTL, maxsize=1000):
        self._ttl = ttl
        self._cache = {}
        self._access_order = []

    def get(self, key):
        if key not in self._cache:
            return None
        entry = self._cache[key]
        if datetime.now() > entry['expires']:
            del self._cache[key]
            return None
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        return entry['value']

    def put(self, key, value):
        if len(self._cache) >= 1000:
            old_key = self._access_order.pop(0)
            del self._cache[old_key]
        self._cache[key] = {
            'value': value,
            'expires': datetime.now() + timedelta(seconds=self._ttl)
        }
        self._access_order.append(key)

    def clear(self):
        self._cache.clear()
        self._access_order.clear()


class _RateLimiter:
    def __init__(self, requests_per_sec=1, burst=1):
        self._interval = 1.0 / requests_per_sec
        self._last_request_time = 0
        self._lock = threading.Lock()

    def wait_if_needed(self):
        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._interval:
                sleep_time = self._interval - elapsed
                time.sleep(sleep_time)
            self._last_request_time = time.time()


class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)


class _RequestWorker(QRunnable):
    def __init__(self, method, url, params, headers, cookies, retry_count):
        super().__init__()
        self.method = method
        self.url = url
        self.params = params
        self.headers = headers
        self.cookies = cookies
        self.retry_count = retry_count
        self.signals = WorkerSignals()

    def run(self):
        try:
            # Use cloudscraper to mimic a real browser
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False,
                }
            )
            # Set headers including custom User-Agent
            scraper.headers.update(self.headers)
            if self.cookies:
                for item in self.cookies.split(';'):
                    if '=' in item:
                        key, val = item.strip().split('=', 1)
                        scraper.cookies.set(key.strip(), val.strip())
            response = scraper.request(self.method, self.url, params=self.params, timeout=15)
            self.signals.finished.emit(response)
        except Exception as e:
            self.signals.error.emit(str(e))


class DanbooruClient(QObject):
    tag_info_fetched = pyqtSignal(str, dict)
    tag_info_error = pyqtSignal(str, str)
    autocomplete_results = pyqtSignal(str, list)
    autocomplete_error = pyqtSignal(str, str)
    credentials_missing = pyqtSignal()

    def __init__(self, settings: SettingsManager):
        super().__init__()
        self.settings = settings
        self._username = None
        self._api_key = None
        self._cookies = None
        self._rate_limiter = _RateLimiter(REQUESTS_PER_SECOND, RATE_LIMIT_BURST)
        self._tag_cache = _CacheManager(ttl=CACHE_TTL, maxsize=500)
        self._autocomplete_cache = _CacheManager(ttl=CACHE_TTL, maxsize=200)
        self._request_queue = []
        self._pending_requests = 0
        self._queue_timer = QTimer()
        self._queue_timer.setSingleShot(True)
        self._queue_timer.timeout.connect(self._process_queue)
        self._threadpool = QThreadPool()
        self._threadpool.setMaxThreadCount(4)
        self._reload_credentials()

        # Also store the custom User-Agent as a constant for use in requests
        self.user_agent = APP_USER_AGENT

    def _reload_credentials(self):
        self._username = self.settings.danbooru_username or ""
        self._api_key = self.settings.danbooru_api_key or ""
        self._cookies = self.settings.danbooru_cookies or ""
        logger.info(f"Credentials loaded for user: {self._username}")
        if not self._username or not self._api_key:
            self.credentials_missing.emit()

    def _get_auth_params(self):
        if self._username and self._api_key:
            auth = (self._username, self._api_key)
            params = {}
        else:
            auth = None
            params = {'login': self._username, 'api_key': self._api_key} if self._username and self._api_key else {}
        return auth, params

    def _process_queue(self):
        if not self._request_queue:
            return
        if self._pending_requests >= REQUESTS_PER_SECOND:
            self._queue_timer.start(1000)
            return
        item = self._request_queue.pop(0)
        self._pending_requests += 1

        # Build request details
        auth, auth_params = self._get_auth_params()
        req_params = auth_params.copy()
        if item.get('params'):
            req_params.update(item['params'])

        # Headers with custom User-Agent
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://danbooru.donmai.us/',
            'Origin': 'https://danbooru.donmai.us',
        }

        url = f"https://danbooru.donmai.us/{item['endpoint']}"
        worker = _RequestWorker(
            method='GET',
            url=url,
            params=req_params,
            headers=headers,
            cookies=self._cookies,
            retry_count=0
        )

        if item['type'] == 'tag_info':
            tag = item['tag']
            worker.signals.finished.connect(lambda resp, tag=tag: self._handle_tag_response(tag, resp))
            worker.signals.error.connect(lambda err, tag=tag: self.tag_info_error.emit(tag, err))
        elif item['type'] == 'autocomplete':
            query = item['query']
            worker.signals.finished.connect(lambda resp, query=query: self._handle_autocomplete_response(query, resp))
            worker.signals.error.connect(lambda err, query=query: self.autocomplete_error.emit(query, err))

        self._threadpool.start(worker)
        self._queue_timer.start(1000)

    def _enqueue_request(self, request_type, endpoint, params, tag=None, query=None):
        self._request_queue.append({
            'type': request_type,
            'endpoint': endpoint,
            'params': params,
            'tag': tag,
            'query': query,
        })
        self._process_queue()

    def fetch_tag_info(self, tag: str):
        if not tag:
            return
        cached = self._tag_cache.get(tag)
        if cached is not None:
            self.tag_info_fetched.emit(tag, cached)
            return
        if not self._username or not self._api_key:
            self.credentials_missing.emit()
            return
        params = {'search[name]': tag}
        self._enqueue_request('tag_info', 'tags.json', params, tag=tag)

    def _handle_tag_response(self, tag, response):
        self._pending_requests -= 1
        try:
            if response.status_code == 200:
                data = response.json()
                if data:
                    info = data[0]
                    self._tag_cache.put(tag, info)
                    self.tag_info_fetched.emit(tag, info)
                else:
                    self.tag_info_error.emit(tag, "Tag not found")
            else:
                self.tag_info_error.emit(tag, f"HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            self.tag_info_error.emit(tag, f"Error parsing response: {e}")
        self._process_queue()

    def autocomplete(self, query: str):
        if len(query) < 2:
            self.autocomplete_results.emit(query, [])
            return
        cached = self._autocomplete_cache.get(query)
        if cached is not None:
            self.autocomplete_results.emit(query, cached)
            return
        if not self._username or not self._api_key:
            self.credentials_missing.emit()
            return
        params = {'search[name_matches]': f'{query}*', 'limit': 10}
        self._enqueue_request('autocomplete', 'tags.json', params, query=query)

    def _handle_autocomplete_response(self, query, response):
        self._pending_requests -= 1
        try:
            if response.status_code == 200:
                data = response.json()
                tags = [tag['name'] for tag in data]
                self._autocomplete_cache.put(query, tags)
                self.autocomplete_results.emit(query, tags)
            else:
                self.autocomplete_error.emit(query, f"HTTP {response.status_code}")
        except Exception as e:
            self.autocomplete_error.emit(query, f"Error parsing response: {e}")
        self._process_queue()

    def reload_settings(self):
        self._reload_credentials()
        self._tag_cache.clear()
        self._autocomplete_cache.clear()