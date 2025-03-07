import configparser
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import List, Tuple

from albert import *

md_iid = "3.0"
md_version = "1.0"
md_name = "Firefox Bookmarks and History"
md_description = "Access Firefox bookmarks and history"
md_license = "MIT"
md_url = "https://github.com/tomsquest/albert_plugin_firefox_bookmarks"
md_authors = "@tomsquest"
md_lib_dependencies = ["sqlite3"]
md_credits = ["@stevenxxiu", "@sagebind"]


firefox_bookmark_icon = Path(__file__).parent / "firefox_bookmark.svg"
firefox_history_icon = Path(__file__).parent / "firefox_history.svg"


def get_firefox_root() -> Path:
    """Get the Firefox root directory"""
    return Path.home() / ".mozilla" / "firefox"


def get_available_profiles() -> List[str]:
    """Get list of available Firefox profiles from profiles.ini"""
    profiles = []
    firefox_root = get_firefox_root()

    if not firefox_root.exists():
        return profiles

    try:
        config = configparser.ConfigParser()
        config.read(firefox_root / "profiles.ini")

        for section in config.sections():
            if section.startswith("Profile") and "Path" in config[section]:
                profile_path = firefox_root / config[section]["Path"]
                if (profile_path / "places.sqlite").exists() and (
                    profile_path / "favicons.sqlite"
                ).exists():
                    profiles.append(config[section]["Path"])

    except Exception as e:
        warning(f"Failed to read Firefox profiles: {str(e)}")

    return profiles


@contextmanager
def get_connection(db_path: Path):
    """Create a connection to the places database with read-only access"""
    if not db_path.exists():
        raise FileNotFoundError(f"Places database not found at {db_path}")

    conn = sqlite3.connect(f"file:{db_path}?immutable=1", uri=True)
    try:
        yield conn
    finally:
        conn.close()


def get_bookmarks(places_db: Path) -> List[Tuple[str, str, str, str]]:
    """Get all bookmarks from the places database"""
    try:
        with get_connection(places_db) as conn:
            cursor = conn.cursor()

            # Query bookmarks
            cursor.execute("""
                SELECT bookmark.guid, bookmark.title, place.url, place.url_hash
                FROM moz_bookmarks bookmark
                  JOIN moz_places place ON place.id = bookmark.fk
                WHERE bookmark.type = 1 -- 1 = bookmark
                  AND place.hidden = 0
                  AND place.url IS NOT NULL
            """)

            return cursor.fetchall()

    except sqlite3.Error as e:
        critical(f"Failed to read Firefox bookmarks: {str(e)}")
        return []


def get_history(places_db: Path) -> List[Tuple[str, str, str]]:
    """Get all history items from the places database"""
    try:
        with get_connection(places_db) as conn:
            cursor = conn.cursor()

            # Query history excluding bookmarks
            cursor.execute("""
                SELECT place.guid, place.title, place.url
                FROM moz_places place
                  LEFT JOIN moz_bookmarks bookmark ON place.id = bookmark.fk
                WHERE place.hidden = 0
                  AND place.url IS NOT NULL
                  AND bookmark.id IS NULL
            """)

            return cursor.fetchall()

    except sqlite3.Error as e:
        critical(f"Failed to read Firefox history: {str(e)}")
        return []


def get_favicons_data(favicons_db: Path) -> dict[str, bytes]:
    """Get all favicon data from the favicons database"""
    try:
        with get_connection(favicons_db) as conn:
            cursor = conn.cursor()

            # Query favicons
            cursor.execute("""
                SELECT moz_pages_w_icons.page_url_hash, moz_icons.data
                FROM moz_icons
                  INNER JOIN moz_icons_to_pages ON moz_icons.id = moz_icons_to_pages.icon_id
                  INNER JOIN moz_pages_w_icons ON moz_icons_to_pages.page_id = moz_pages_w_icons.id
            """)

            return {row[0]: row[1] for row in cursor.fetchall()}

    except sqlite3.Error as e:
        warning(f"Failed to read favicon data: {str(e)}")
        return {}


class Plugin(PluginInstance, IndexQueryHandler):
    def __init__(self):
        PluginInstance.__init__(self)
        IndexQueryHandler.__init__(self)
        self.thread = None

        # Get available profiles
        self.profiles = get_available_profiles()
        if not self.profiles:
            critical("No Firefox profiles found")
            return

        # Initialize profile selection
        self._current_profile_path = self.readConfig("current_profile_path", str)
        if self._current_profile_path not in self.profiles:
            # Use first profile as default if current profile is not valid
            self._current_profile_path = self.profiles[0]
            self.writeConfig("current_profile_path", self._current_profile_path)

        # Initialize history indexing preference
        self._index_history = self.readConfig("index_history", bool)
        if self._index_history is None:
            self._index_history = False
            self.writeConfig("index_history", self._index_history)

    def __del__(self):
        if self.thread and self.thread.is_alive():
            self.thread.join()

    def extensions(self):
        return [self]

    def defaultTrigger(self):
        return "f "

    @property
    def current_profile_path(self):
        return self._current_profile_path

    @current_profile_path.setter
    def current_profile_path(self, value):
        self._current_profile_path = value
        self.writeConfig("current_profile_path", value)
        self.updateIndexItems()

    @property
    def index_history(self):
        return self._index_history

    @index_history.setter
    def index_history(self, value):
        self._index_history = value
        self.writeConfig("index_history", value)
        self.updateIndexItems()

    def configWidget(self):
        return [
            {
                "type": "combobox",
                "property": "current_profile_path",
                "label": "Firefox Profile",
                "items": self.profiles,
                "widget_properties": {
                    "toolTip": "Select Firefox profile to search bookmarks from"
                },
            },
            {
                "type": "checkbox",
                "property": "index_history",
                "label": "Index Firefox History",
                "widget_properties": {
                    "toolTip": "Enable or disable indexing of Firefox history"
                },
            },
        ]

    def updateIndexItems(self):
        if self.thread and self.thread.is_alive():
            self.thread.join()
        self.thread = threading.Thread(target=self.update_index_items_task)
        self.thread.start()

    def update_index_items_task(self):
        firefox_root = get_firefox_root()
        places_db = firefox_root / self.current_profile_path / "places.sqlite"
        favicons_db = firefox_root / self.current_profile_path / "favicons.sqlite"

        bookmarks = get_bookmarks(places_db)
        info(f"Found {len(bookmarks)} bookmarks")

        # Create favicons directory if it doesn't exist
        favicons_location = Path(self.dataLocation()) / "favicons"
        favicons_location.mkdir(exist_ok=True, parents=True)

        # Drop existing favicons
        for f in favicons_location.glob("*"):
            f.unlink()

        favicons = get_favicons_data(favicons_db)

        index_items = []
        seen_urls = set()

        for guid, title, url, url_hash in bookmarks:
            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Search and store favicons
            favicon_data = favicons.get(url_hash)
            if favicon_data:
                favicon_path = favicons_location / f"favicon_{guid}.png"
                with open(favicon_path, "wb") as f:
                    f.write(favicon_data)
                icon_urls = [f"file:{favicon_path}", "xdg:firefox"]
            else:
                icon_urls = [
                    f"file:{firefox_bookmark_icon}",
                    "xdg:firefox",
                ]

            item = StandardItem(
                id=guid,
                text=title if title else url,
                subtext=url,
                iconUrls=icon_urls,
                actions=[
                    Action("open", "Open in Firefox", lambda u=url: openUrl(u)),
                    Action("copy", "Copy URL", lambda u=url: setClipboardText(u)),
                ],
            )

            # Create searchable string for the bookmark
            index_items.append(IndexItem(item=item, string=f"{title} {url}".lower()))

        if self._index_history:
            history = get_history(places_db)
            info(f"Found {len(history)} history items")
            for guid, title, url in history:
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                item = StandardItem(
                    id=guid,
                    text=title if title else url,
                    subtext=url,
                    iconUrls=[
                        f"file:{firefox_history_icon}",
                        "xdg:firefox",
                    ],
                    actions=[
                        Action("open", "Open in Firefox", lambda u=url: openUrl(u)),
                        Action("copy", "Copy URL", lambda u=url: setClipboardText(u)),
                    ],
                )

                # Create searchable string for the history item
                index_items.append(
                    IndexItem(item=item, string=f"{title} {url}".lower())
                )

        self.setIndexItems(index_items)
