# ui/dialogs/source_manager_help.py
"""
Help window for the Source Manager dialog.
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

<h1>Source Manager</h1>

<p>Manage all your booru data sources from one place. Enable or disable sources,
configure authentication, and check connection status.</p>

<h2>Supported Sources</h2>

<table>
    <tr><th>Source</th><th>Auth Required</th><th>Features</th></tr>
    <tr><td><b>Danbooru</b></td><td>Username + API Key (recommended)</td><td>Full API, post search, tag search</td></tr>
    <tr><td><b>Gelbooru</b></td><td>User ID + API Key (recommended)</td><td>Post search, tag search</td></tr>
    <tr><td><b>Rule34</b></td><td>User ID + API Key</td><td>Post search, tag search</td></tr>
    <tr><td><b>yande.re</b></td><td>Optional (API key + cookies)</td><td>Post search, tag search</td></tr>
    <tr><td><b>Konachan</b></td><td>Optional (API key + cookies)</td><td>Post search, tag search</td></tr>
</table>

<h2>Authentication Setup</h2>

<h3>Danbooru</h3>
<ol>
    <li>Create an account at <a href="https://danbooru.donmai.us">danbooru.donmai.us</a></li>
    <li>Go to <b>My Account → Edit</b></li>
    <li>Find your <b>API Key</b> (or generate one)</li>
    <li>Enter your username and API key in the fields above</li>
</ol>

<div class="tip"><b>Tip:</b> Without authentication, Danbooru's post search API returns 403 Cloudflare errors.
Tag search works without auth. Always use an API key for reliable access.</div>

<h3>Gelbooru</h3>
<ol>
    <li>Create an account at <a href="https://gelbooru.com">gelbooru.com</a></li>
    <li>Go to <b>My Account → Options</b></li>
    <li>Find your <b>User ID</b> (numeric, e.g. <code>2013147</code>)</li>
    <li>Generate an <b>API Key</b></li>
    <li>Enter both in the fields above</li>
</ol>

<h3>Rule34</h3>
<ol>
    <li>Create an account at <a href="https://rule34.xxx">rule34.xxx</a></li>
    <li>Go to <b>Options</b></li>
    <li>Find your <b>User ID</b> and <b>API Key</b></li>
    <li>Enter both in the fields above</li>
</ol>

<h3>yande.re / Konachan</h3>
<p>Authentication is optional for these sources. If you have an API key, you can enter it
to increase rate limits. Cookies can be used for accessing restricted content.</p>

<h2>Enable / Disable Sources</h2>
<p>Use the <b>Enable</b> checkbox at the top of each tab, or use the <b>Enable All</b>
/ <b>Disable All</b> buttons at the bottom.</p>

<div class="warning"><b>Warning:</b> Disabled sources won't appear in autocomplete or search results.</div>

<h2>Status Indicators</h2>
<ul>
    <li><b>Enabled</b> — Source is active and will be used for tag lookups</li>
    <li><b>Disabled</b> — Source is inactive and won't be queried</li>
</ul>

<h2>Troubleshooting</h2>

<table>
    <tr><th>Problem</th><th>Solution</th></tr>
    <tr><td>Danbooru returns 403</td><td>Add your API key. Cloudflare blocks unauthenticated requests.</td></tr>
    <tr><td>Gelbooru returns empty results</td><td>Check your User ID is numeric (not username).</td></tr>
    <tr><td>Rule34 autocomplete not working</td><td>Rule34 API has limitations. TagDB provides local autocomplete as fallback.</td></tr>
    <tr><td>Source won't connect</td><td>Check your internet connection and firewall settings.</td></tr>
    <tr><td>Tags not appearing in autocomplete</td><td>Make sure the source is enabled and has credentials configured.</td></tr>
</table>

<h2>Data Flow</h2>

<p>When you search for tags or fetch posts:</p>
<ol>
    <li>The app queries all <b>enabled</b> sources in parallel</li>
    <li>Results are merged and deduplicated</li>
    <li>Tags are validated against the Danbooru vocabulary (if Tag Validator is enabled)</li>
    <li>Valid tags are added to your autocomplete and tag editor</li>
</ol>

<div class="info"><b>Note:</b> Each source has its own rate limits. Disabling unused sources
reduces the number of API calls and prevents rate limiting.</div>
"""


class SourceManagerHelpDialog(QDialog):
    """Help window for the Source Manager dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help — Source Manager")
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
