# ui/dialogs/llm_tag_generator_help.py
"""
Help window for the LLM Tag Generator dialog.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt

from ui.windows_theme import set_dark_title_bar

HELP_HTML = """
<style>
    body { font-family: 'Segoe UI', sans-serif; color: #e2e8f0; background: transparent; line-height: 1.6; }
    h1 { color: #a78bfa; font-size: 18px; border-bottom: 1px solid rgba(139,92,246,0.3); padding-bottom: 6px; }
    h2 { color: #c4b5fd; font-size: 14px; margin-top: 18px; }
    h3 { color: #ddd6fe; font-size: 12px; margin-top: 12px; }
    code { background: rgba(139,92,246,0.15); padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; color: #c4b5fd; }
    .tip { background: rgba(34,197,94,0.1); border-left: 3px solid #22c55e; padding: 8px 12px; margin: 8px 0; border-radius: 0 6px 6px 0; }
    .warning { background: rgba(234,179,8,0.1); border-left: 3px solid #eab308; padding: 8px 12px; margin: 8px 0; border-radius: 0 6px 6px 0; }
    .info { background: rgba(59,130,246,0.1); border-left: 3px solid #3b82f6; padding: 8px 12px; margin: 8px 0; border-radius: 0 6px 6px 0; }
    table { border-collapse: collapse; width: 100%; margin: 8px 0; }
    th { background: rgba(139,92,246,0.15); text-align: left; padding: 6px 10px; color: #c4b5fd; font-size: 11px; }
    td { padding: 6px 10px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 12px; }
    ul { padding-left: 20px; }
    li { margin-bottom: 4px; }
</style>

<h1>LLM Tag Generator</h1>

<p>Describe a scene in plain English, and a local LLM converts it into validated booru tags.
Tags are automatically checked against the real Danbooru vocabulary (~140k tags)
and invalid tags are dropped.</p>

<h2>Quick Start</h2>
<ol>
    <li>Make sure you have a local LLM server running (Ollama or LM Studio)</li>
    <li>Type a scene description in the text box</li>
    <li>Click <b>Generate Tags</b></li>
    <li>Review the generated tags and dropped tags</li>
    <li>Click <b>Apply to editor</b> or <b>Copy</b></li>
</ol>

<h2>Supported LLM Servers</h2>

<table>
    <tr><th>Server</th><th>Default URL</th><th>Auth</th><th>Notes</th></tr>
    <tr><td><b>Ollama</b></td><td><code>http://localhost:11434</code></td><td>None</td><td>Auto-detected. Best for local use.</td></tr>
    <tr><td><b>LM Studio</b></td><td><code>http://localhost:1234</code></td><td>None</td><td>OpenAI-compatible API.</td></tr>
    <tr><td><b>llama.cpp</b></td><td><code>http://localhost:8080</code></td><td>None</td><td>Server mode with OpenAI endpoint.</td></tr>
    <tr><td><b>vLLM</b></td><td><code>http://localhost:8000</code></td><td>API key</td><td>Production-grade. May need API key.</td></tr>
    <tr><td><b>OpenAI API</b></td><td><code>https://api.openai.com</code></td><td>API key</td><td>Cloud-based. Costs money per request.</td></tr>
</table>

<div class="tip"><b>Tip:</b> For Ollama, install a model first: <code>ollama pull qwen3:1.7b</code>
The default settings work well with Qwen3 models.</div>

<h2>Settings Explained</h2>

<h3>Server URL</h3>
<p>The base URL of your LLM server. The dialog auto-detects Ollama by checking
<code>/api/version</code>. For other servers, use the OpenAI-compatible endpoint.</p>

<h3>Model</h3>
<p>The model name to use. For Ollama, this is the model tag (e.g. <code>qwen3:1.7b</code>,
<code>llama3.1:8b</code>). For OpenAI-compatible servers, use the model ID
(e.g. <code>gpt-4o-mini</code>).</p>

<table>
    <tr><th>Recommended Models</th><th>Size</th><th>Quality</th><th>Speed</th></tr>
    <tr><td><code>qwen3:1.7b</code></td><td>1.7B</td><td>Good</td><td>Fast</td></tr>
    <tr><td><code>qwen3:4b</code></td><td>4B</td><td>Better</td><td>Medium</td></tr>
    <tr><td><code>llama3.1:8b</b></td><td>8B</td><td>Great</td><td>Slower</td></tr>
    <tr><td><code>qwen3:14b</code></td><td>14B</td><td>Excellent</td><td>Slow</td></tr>
</table>

<h3>Temperature</h3>
<p>Controls randomness in the output. Lower = more deterministic, higher = more creative.</p>
<ul>
    <li><b>0.2–0.4</b> — Best for tag generation (consistent, accurate tags)</li>
    <li><b>0.5–0.7</b> — More varied outputs</li>
    <li><b>0.8–1.0</b> — Very creative, may produce unusual tags</li>
</ul>

<div class="tip"><b>Best setting:</b> <b>0.4</b> — gives a good balance of accuracy and variety.</div>

<h3>Max Tokens</h3>
<p>Maximum number of tokens the LLM can generate. More tokens = longer tag lists.</p>
<ul>
    <li><b>300–500</b> — Simple scenes (1-2 characters)</li>
    <li><b>500–800</b> — Complex scenes (multiple characters, detailed background)</li>
    <li><b>1000+</b> — Very detailed scenes or when you want extra tags</li>
</ul>

<h3>Template</h3>
<p>Wraps your generated tags with quality tags optimized for different model families:</p>

<table>
    <tr><th>Template</th><th>Best For</th><th>Quality Tags Added</th></tr>
    <tr><td><b>nova_anime_xl</b></td><td>Nova Anime XL, SD anime models</td><td><code>masterpiece, best quality, ...</code></td></tr>
    <tr><td><b>illustrious</b></td><td>Illustrious XL, Pony-based models</td><td><code>score_9, score_8_up, ...</code></td></tr>
    <tr><td><b>pony</b></td><td>Pony Diffusion</td><td><code>score_9, score_8_up, ...</code></td></tr>
    <tr><td><b>animagine_xl</b></td><td>Animagine XL</td><td><code>masterpiece, best quality, ...</code></td></tr>
    <tr><td><b>tags_only</b></td><td>Any model (no quality tags)</td><td>None — raw tags only</td></tr>
    <tr><td><b>custom</b></td><td>Your own template</td><td>Edit the system prompt</td></tr>
</table>

<h3>Thinking Mode</h3>
<p>When enabled, the LLM uses "thinking" (chain-of-thought) before generating tags.
This can improve quality for complex scenes but takes longer.</p>

<div class="info"><b>Note:</b> Not all models support thinking mode. Qwen3 models do.
If you get errors, disable this option.</div>

<h3>API Key</h3>
<p>Optional. Only needed for servers that require authentication (e.g. OpenAI API, vLLM with auth).
Leave empty for Ollama and most local servers.</p>

<h2>System Prompt</h2>

<p>Click <b>▸ System prompt</b> to expand and view/edit the system prompt.
This tells the LLM how to format its output. The default prompt is optimized
for booru tag generation.</p>

<div class="warning"><b>Warning:</b> Only edit the system prompt if you know what you're doing.
A bad system prompt will produce poor results.</div>

<h2>Understanding the Output</h2>

<h3>Generated Tags</h3>
<p>The validated, template-wrapped tag string ready to use. These are comma-separated
and sorted in Danbooru convention (counts, character, copyright, artist, general, meta).</p>

<h3>Dropped Tags</h3>
<p>Tags that the LLM generated but don't exist in the Danbooru database.
These are removed in strict mode. Common reasons:</p>
<ul>
    <li>Misspellings (e.g. <code>blond_hair</code> instead of <code>blonde_hair</code>)</li>
    <li>Non-existent tags (e.g. made-up character names)</li>
    <li>Wrong format (e.g. <code>beautiful detailed eyes</code> instead of <code>detailed_eyes</code>)</li>
</ul>

<h2>Examples</h2>

<h3>Example 1: Simple character</h3>
<p>Input: <code>A blonde girl with blue eyes wearing a school uniform</code></p>
<p>Output: <code>1girl, solo, blonde_hair, blue_eyes, school_uniform, pleated_skirt, white_shirt, blue_bow</code></p>

<h3>Example 2: Complex scene</h3>
<p>Input: <code>Two girls fighting in a cyberpunk city at night, neon lights, rain, dynamic poses</code></p>
<p>Output: <code>2girls, fighting_stance, cyberpunk, city, night, neon_lights, rain, wet, dynamic_pose, ...</code></p>

<h3>Example 3: Landscape</h3>
<p>Input: <code>A peaceful Japanese garden with a wooden bridge over a koi pond, cherry blossoms falling</code></p>
<p>Output: <code>landscape, scenery, japanese_garden, wooden_bridge, koi_pond, cherry_blossoms, petals, ...</code></p>

<h2>Troubleshooting</h2>

<table>
    <tr><th>Problem</th><th>Solution</th></tr>
    <tr><td>"Cannot reach LLM server"</td><td>Make sure your LLM server is running. Check the URL and port.</td></tr>
    <tr><td>"HTTP 400" or "think" error</td><td>Your model doesn't support thinking mode. Disable it.</td></tr>
    <tr><td>Empty or garbage output</td><td>Try a different model, or lower the temperature to 0.3.</td></tr>
    <tr><td>Too many dropped tags</td><td>The model may be too small. Try a larger model (4B+).</td></tr>
    <tr><td>Very slow generation</td><td>Use a smaller model (1.7B) or reduce max tokens.</td></tr>
    <tr><td>Tags are in wrong format</td><td>Check the template setting. Use "tags_only" for raw output.</td></tr>
</table>
"""


class LLMTagGeneratorHelpDialog(QDialog):
    """Help window for the LLM Tag Generator dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help — LLM Tag Generator")
        self.setMinimumSize(680, 600)
        self.resize(720, 650)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(HELP_HTML)
        browser.setStyleSheet("""
            QTextBrowser {
                background: rgba(16, 18, 26, 0.85);
                color: #e2e8f0;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 10px;
                padding: 12px;
                font-size: 12px;
            }
            QScrollBar:vertical {
                background: rgba(30, 32, 40, 0.8);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(139, 92, 246, 0.35);
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        layout.addWidget(browser)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(100, 100, 120, 0.3);
                color: #ccc;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 6px 20px;
            }
            QPushButton:hover { background: rgba(100, 100, 120, 0.5); }
        """)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def showEvent(self, event):
        super().showEvent(event)
        set_dark_title_bar(self)
