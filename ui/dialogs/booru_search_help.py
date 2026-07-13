# ui/dialogs/booru_search_help.py
"""
Help window for the Booru Search dialog.
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

<h1>Search Booru Posts</h1>

<p>Search across multiple booru sites by tag keywords. Browse results as a thumbnail gallery,
then import tags from any post directly into your current image.</p>

<h2>Quick Start</h2>
<ol>
    <li>Type search tags into the search bar (e.g. <code>1girl solo landscape</code>)</li>
    <li>Optionally select a specific source from the dropdown, or leave on "All Sources"</li>
    <li>Click <b>Search</b> (or press Enter)</li>
    <li>Click a thumbnail to see its tags in the detail panel</li>
    <li>Click <b>Import Tags to Current Image</b> to add them</li>
</ol>

<h2>Search Syntax</h2>

<p>Enter space-separated tags. Most boorus support these operators:</p>

<table>
    <tr><th>Syntax</th><th>Meaning</th><th>Example</th></tr>
    <tr><td><code>tag1 tag2</code></td><td>AND — both tags must match</td><td><code>1girl solo</code></td></tr>
    <tr><td><code>tag1 tag2 -tag3</code></td><td>Exclude tag3</td><td><code>1girl -solo</code></td></tr>
    <tr><td><code>rating:general</code></td><td>Filter by rating</td><td><code>rating:safe 1girl</code></td></tr>
    <tr><td><code>score:>100</code></td><td>Filter by score (Danbooru)</td><td><code>score:>500 landscape</code></td></tr>
    <tr><td><code>sort:score</code></td><td>Sort results (Danbooru)</td><td><code>1girl sort:score</code></td></tr>
</table>

<div class="info"><b>Note:</b> Search syntax varies by source. Danbooru supports the most advanced operators.
yande.re and Konachan use a simpler tag-based system.</div>

<h2>Source Selection</h2>

<table>
    <tr><th>Option</th><th>Behavior</th></tr>
    <tr><td><b>All Sources</b></td><td>Searches every enabled source and merges results. Posts show their source label.</td></tr>
    <tr><td><b>Danbooru</b></td><td>Largest tag database. Best for character/artist lookups.</td></tr>
    <tr><td><b>Gelbooru</b></td><td>Good for anime-style. Requires API credentials.</td></tr>
    <tr><td><b>Rule34</b></td><td>NSFW content. Requires API credentials.</td></tr>
    <tr><td><b>yande.re</b></td><td>High-quality anime art. No auth needed.</td></tr>
    <tr><td><b>Konachan</b></td><td>Similar to yande.re. No auth needed.</td></tr>
</table>

<div class="tip"><b>Tip:</b> If a source isn't appearing, check that it's enabled in Settings → Sources.</div>

<h2>Browsing Results</h2>

<h3>Thumbnail Grid</h3>
<ul>
    <li><b>Left-click</b> a thumbnail to view its tags in the detail panel</li>
    <li><b>Right-click</b> for a context menu with more options</li>
    <li>Each card shows the post ID, source, and rating</li>
    <li>Thumbnails are cached — revisiting a search loads instantly</li>
</ul>

<h3>Detail Panel (right side)</h3>
<ul>
    <li>Shows post ID, source, rating, score, and tag count</li>
    <li>Lists all tags as comma-separated text</li>
    <li><b>Import Tags</b> button adds them to the current image</li>
</ul>

<h2>Right-Click Context Menu</h2>

<p>Right-click any thumbnail for these options:</p>

<table>
    <tr><th>Action</th><th>Description</th></tr>
    <tr><td><b>Download Image</b></td><td>Save the full-resolution image to disk</td></tr>
    <tr><td><b>View Image</b></td><td>Open a full-size preview in a new window</td></tr>
    <tr><td><b>View Post</b></td><td>Open the original post page in your browser</td></tr>
</table>

<h2>Import Options</h2>

<h3>Import Tags to Current Image</h3>
<p>Appends all tags from the selected post to the current image's tag list.
Use this to build up tags from multiple reference posts.</p>

<div class="tip"><b>Workflow:</b> Search for a style reference → Import → Search for a character → Import again.
The tags from both posts combine on your image.</div>

<h2>Examples</h2>

<h3>Example 1: Find anime landscape references</h3>
<ol>
    <li>Search: <code>1girl landscape scenery</code></li>
    <li>Set source to <b>yande.re</b> (no auth needed)</li>
    <li>Browse thumbnails, click promising ones</li>
    <li>Import tags from the best match</li>
</ol>

<h3>Example 2: Find a specific character</h3>
<ol>
    <li>Search: <code>ganyu_(genshin_impact)</code></li>
    <li>Set source to <b>Danbooru</b> (best character tags)</li>
    <li>Right-click → View Post to see the full post</li>
    <li>Import tags from the detail panel</li>
</ol>

<h3>Example 3: Multi-source search</h3>
<ol>
    <li>Search: <code>wlop masterpiece</code></li>
    <li>Keep source on <b>All Sources</b></li>
    <li>Results from Danbooru, Gelbooru, yande.re, and more appear together</li>
    <li>Each card shows which source it came from</li>
</ol>

<h2>Troubleshooting</h2>

<table>
    <tr><th>Problem</th><th>Solution</th></tr>
    <tr><td>No results found</td><td>Try different tags, or switch sources. Some tags only exist on specific boorus.</td></tr>
    <tr><td>Thumbnails not loading</td><td>Check your internet connection. Some sources may block requests — try another source.</td></tr>
    <tr><td>"Cloudflare blocked"</td><td>Set browser cookies in Settings → Sources for the relevant source.</td></tr>
    <tr><td>Import button is grayed out</td><td>Click a thumbnail first to load its tags.</td></tr>
    <tr><td>Source not in dropdown</td><td>Enable it in Settings → Sources and restart this dialog.</td></tr>
</table>
"""


class BooruSearchHelpDialog(QDialog):
    """Help window for the Booru Search dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help — Search Booru Posts")
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
