# ui/dialogs/tag_validator_help.py
"""
Help window for the Tag Validator dialog.
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

<h1>Tag Validator</h1>

<p>Validates, fixes, and explores booru tags against the real Danbooru vocabulary
with <b>~140,782</b> tags. Automatically fixes common mistakes, expands abbreviations,
and sorts tags in proper Danbooru convention.</p>

<h2>Quick Start</h2>
<ol>
    <li>Paste your tag string in the input box (top)</li>
    <li>Click <b>Validate</b></li>
    <li>Review the results table (kept tags, categories, post counts)</li>
    <li>Optionally apply template quality tags (bottom dropdown)</li>
    <li>Click <b>Apply to editor</b> or <b>Copy</b></li>
</ol>

<h2>Validation Features</h2>

<h3>Alias Remapping</h3>
<p>Tags are automatically corrected to their canonical form:</p>
<ul>
    <li><code>blond_hair</code> → <code>blonde_hair</code></li>
    <li><code>blue_eyes</code> → <code>blue_eyes</code> (kept if exists)</li>
    <li><code>black_hair</code> → <code>black_hair</code></li>
</ul>

<h3>Morphological Fixes</h3>
<p>Common spelling and format corrections:</p>
<ul>
    <li>Whitespace handling: <code>blue eyes</code> → <code>blue_eyes</code></li>
    <li>Case normalization: <code>Blue_Eyes</code> → <code>blue_eyes</code></li>
    <li>Backslash removal: <code>\\(</code> → <code>(</code></li>
</ul>

<h3>Sub-phrase Extraction</h3>
<p>If a complex phrase is not a valid tag, it's broken into valid sub-tags:</p>
<ul>
    <li><code>beautiful detailed eyes</code> → <code>detailed_eyes</code> (if valid)</li>
    <li><code>wearing red dress</code> → <code>red_dress</code> (if valid)</li>
</ul>

<h3>Fuzzy Matching</h3>
<p>If exact match fails, the closest tag is suggested using Levenshtein distance.
The fuzzy match must have a similarity score above 0.6 to be accepted.</p>

<h3>Danbooru-Conventional Sorting</h3>
<p>Tags are automatically sorted in the order Danbooru uses:</p>
<ol>
    <li>Rating (general, sensitive, questionable, explicit)</li>
    <li>Meta tags (meta)</li>
    <li>Copyright tags (series, franchise)</li>
    <li>Character tags (character names)</li>
    <li>Artist tags (creator names)</li>
    <li>General tags (hair, eyes, clothing, pose, etc.)</li>
</ol>

<h2>Strict Mode</h2>
<p>When <b>Strict</b> is checked (default):</p>
<ul>
    <li>Tags not found in Danbooru are <b>dropped</b></li>
    <li>Only valid tags appear in the output</li>
    <li>Best for prompt generation (avoids garbage tags)</li>
</ul>

<p>When <b>Strict</b> is unchecked:</p>
<ul>
    <li>Unknown tags are <b>preserved</b> in the output</li>
    <li>They appear at the end of the tag string</li>
    <li>Good for discovering new tags or checking your own tags</li>
</ul>

<h2>Tag Info Table</h2>
<p>The bottom table shows detailed information for each validated tag:</p>
<ul>
    <li><b>Tag</b> — The canonical tag name</li>
    <li><b>Category</b> — Color-coded: General (green), Artist (red), Copyright (purple), Character (blue), Meta (yellow)</li>
    <li><b>Posts</b> — Number of posts using this tag on Danbooru</li>
    <li><b>Aliases</b> — Alternative names that map to this tag</li>
</ul>

<div class="tip"><b>Tip:</b> Higher post counts generally mean the tag is more commonly used and better recognized by AI models.</div>

<h2>Template Presets</h2>
<p>The dropdown at the bottom lets you wrap validated tags with quality tags:</p>

<table>
    <tr><th>Template</th><th>Purpose</th><th>Example Tags Added</th></tr>
    <tr><td><b>nov_anime_xl</b></td><td>Nova Anime XL models</td><td><code>masterpiece, best quality</code></td></tr>
    <tr><td><b>illustrious</b></td><td>Illustrious XL</td><td><code>score_9, score_8_up</code></td></tr>
    <tr><td><b>animagine_xl</b></td><td>Animagine XL</td><td><code>masterpiece, absurdres</code></td></tr>
    <tr><td><b>tags_only</b></td><td>No quality tags</td><td>Raw validated tags only</td></tr>
</table>

<h2>Examples</h2>

<h3>Example 1: Fix messy tags</h3>
<p>Input: <code>blue eyes, blond hair, school uniform, 1 girl, solo</code></p>
<p>Output: <code>1girl, solo, blonde_hair, blue_eyes, school_uniform</code></p>
<p>The validator fixes: <code>1 girl</code> → <code>1girl</code>, <code>blond</code> → <code>blonde</code>, adds underscores</p>

<h3>Example 2: Expand sub-phrases</h3>
<p>Input: <code>wearing a white dress with ribbons</code></p>
<p>Output: <code>white_dress, ribbon</code></p>
<p>The validator extracts valid tags from the phrase</p>

<h3>Example 3: Check unknown tags</h3>
<p>Input: <code>custom_fanart_tag, 1girl, solo</code> (strict OFF)</p>
<p>Output: <code>1girl, solo, custom_fanart_tag</code></p>
<p>Unknown tag is preserved at the end for review</p>

<h2>Troubleshooting</h2>

<table>
    <tr><th>Problem</th><th>Solution</th></tr>
    <tr><td>All tags dropped</td><td>Tags may not exist on Danbooru. Check spelling, try fewer tags at once.</td></tr>
    <tr><td>Tag not recognized</td><td>It may not be in the Danbooru vocabulary. Try variations or check Danbooru directly.</td></tr>
    <tr><td>Wrong category shown</td><td>Some tags have multiple meanings. The most common one is shown.</td></tr>
    <tr><td>Sort order looks wrong</td><td>Tags follow Danbooru's conventional ordering, not alphabetical.</td></tr>
</table>
"""


class TagValidatorHelpDialog(QDialog):
    """Help window for the Tag Validator dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help — Tag Validator")
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
