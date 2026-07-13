# core/llm_client.py
"""
LLM client for natural language to booru tag generation.
Supports any OpenAI-compatible server: LM Studio, Ollama, llama.cpp, vLLM.
Uses stdlib urllib — no extra dependencies.
"""

import json
import logging
import re
import urllib.request
import urllib.error
from PyQt5.QtCore import QObject, pyqtSignal, QThread

logger = logging.getLogger(__name__)

_OLLAMA_CACHE = {}


def _is_ollama(base_url):
    cached = _OLLAMA_CACHE.get(base_url)
    if cached is not None:
        return cached
    try:
        urllib.request.urlopen(base_url + "/api/version", timeout=5)
        found = True
    except Exception:
        found = False
    _OLLAMA_CACHE[base_url] = found
    return found


def clear_ollama_cache():
    """Clear the cached Ollama detection results."""
    _OLLAMA_CACHE.clear()


def _post_json(url, payload, headers, timeout):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_error_detail(e):
    try:
        return e.read().decode("utf-8", "replace")[:300]
    except Exception:
        return ""


def _strip_think(text):
    if "<think>" in text:
        text = re.sub(r"<think>.*?(?:</think>|$)", "", text, flags=re.DOTALL).strip()
    return text


class LLMClient(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None

    def generate(self, user_prompt, system_prompt, server_url,
                 model="qwen/qwen3-1.7b", temperature=0.4, max_tokens=500,
                 enable_thinking=False, api_key="", timeout=120):
        if self._thread and self._thread.isRunning():
            self.error.emit("Already generating")
            return

        self._thread = _GenerateThread(
            user_prompt, system_prompt, server_url, model,
            temperature, max_tokens, enable_thinking, api_key, timeout
        )
        self._thread.finished.connect(self.finished)
        self._thread.error.connect(self.error)
        self._thread.start()

    def cancel(self):
        if self._thread and self._thread.isRunning():
            self._thread._cancelled = True
            self._thread.wait(3000)
            if self._thread.isRunning():
                self._thread.terminate()
                self._thread.wait(1000)
            self._thread = None


class _GenerateThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, user_prompt, system_prompt, server_url, model,
                 temperature, max_tokens, enable_thinking, api_key, timeout):
        super().__init__()
        self._user_prompt = user_prompt
        self._system_prompt = system_prompt
        self._server_url = server_url.rstrip("/")
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._enable_thinking = enable_thinking
        self._api_key = api_key
        self._timeout = timeout
        self._cancelled = False

    def run(self):
        try:
            if self._cancelled:
                return
            base = self._server_url
            system_prompt = self._system_prompt
            if self._enable_thinking:
                system_prompt = re.sub(r"\s*/no_think\s*$", "", system_prompt)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": self._user_prompt},
            ]

            headers = {"Content-Type": "application/json"}
            if self._api_key.strip():
                headers["Authorization"] = "Bearer " + self._api_key.strip()

            if self._cancelled:
                return

            if _is_ollama(base):
                url = base + "/api/chat"
                payload = {
                    "model": self._model,
                    "messages": messages,
                    "think": bool(self._enable_thinking),
                    "stream": False,
                    "options": {
                        "temperature": self._temperature,
                        "num_predict": self._max_tokens,
                    },
                }
            else:
                url = base + "/v1/chat/completions"
                payload = {
                    "model": self._model,
                    "messages": messages,
                    "temperature": self._temperature,
                    "max_tokens": self._max_tokens,
                    "stream": False,
                }
                if not self._enable_thinking:
                    payload["enable_thinking"] = False

            try:
                result = _post_json(url, payload, headers, self._timeout)
            except urllib.error.HTTPError as e:
                if ("think" in payload and e.code == 400
                        and "think" in _http_error_detail(e).lower()):
                    payload.pop("think")
                    result = _post_json(url, payload, headers, self._timeout)
                else:
                    raise

            msg = (result["message"] if "message" in result
                   else result["choices"][0]["message"])
            text = (msg.get("content") or "").strip()
            if not text:
                text = (msg.get("thinking") or msg.get("reasoning") or
                        msg.get("reasoning_content") or "").strip()

            text = _strip_think(text)
            logger.info(f"LLM response: {text[:160]}...")
            self.finished.emit(text)

        except urllib.error.HTTPError as e:
            detail = _http_error_detail(e)
            self.error.emit(f"HTTP {e.code}: {detail}")
        except urllib.error.URLError as e:
            self.error.emit(
                f"Cannot reach LLM server at {self._server_url} ({e.reason}). "
                "Is it running?"
            )
        except Exception as e:
            self.error.emit(f"Error: {e}")
