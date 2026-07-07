from PyQt5.QtCore import QSettings

class SettingsManager:
    def __init__(self, app_name="BooruTagEditorPro", org_name="BossGame"):
        self.settings = QSettings(org_name, app_name)

    def get(self, key, default=None):
        return self.settings.value(key, default)

    def set(self, key, value):
        self.settings.setValue(key, value)

    @property
    def danbooru_username(self):
        return self.get("danbooru_username", "")

    @danbooru_username.setter
    def danbooru_username(self, value):
        self.set("danbooru_username", value)

    @property
    def danbooru_api_key(self):
        return self.get("danbooru_api_key", "")

    @danbooru_api_key.setter
    def danbooru_api_key(self, value):
        self.set("danbooru_api_key", value)

    @property
    def danbooru_cookies(self):
        return self.get("danbooru_cookies", "")

    @danbooru_cookies.setter
    def danbooru_cookies(self, value):
        self.set("danbooru_cookies", value)

    def save_window_geometry(self, window):
        self.set("window_geometry", window.saveGeometry())
        self.set("window_state", window.saveState())

    def restore_window_geometry(self, window):
        geom = self.get("window_geometry")
        if geom:
            window.restoreGeometry(geom)
        state = self.get("window_state")
        if state:
            window.restoreState(state)