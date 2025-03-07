# Open Firefox Bookmarks and History in AlbertLauncher

This plugin/extension helps you open your **Firefox bookmarks and history** in [AlbertLauncher](https://albertlauncher.github.io/).

Albert will present the entries in frequency order: the more you use a bookmark, the higher it will be in the list.

## Features

- 📚 Open bookmarks and history from Firefox
- ✨ Display favicons for bookmarks
- 🧑‍🤝‍🧑 Select the Profile to use in the Preferences
- 🛗 Enable or not the history search

## TODO

- [x] Index bookmarks
- [x] Index history (with preferences)
- [x] Select the profile to use
- [x] Display Bookmark favicons

## Setup

1. Make the plugin directory

```
mkdir -p ~/.local/share/albert/python/plugins
```

2. Clone the repository

```
git clone https://github.com/tomsquest/albert_plugin_firefox_bookmarks.git ~/.local/share/albert/python/plugins/firefox_bookmarks
```

3. Enable the plugin in `Settings > Plugins` and tick `Firefox Bookmarks`

![plugin_enable.png](plugin_enable.png)

4. Configure the plugin by picking the Firefox profile to use and if you want to search in history

![plugin_settings.png](plugin_settings.png)

5. The default trigger is `f` (for Firefox), so start typing `f` in Albert to see your bookmarks and history

## Alternatives

- [Stevenxxiu plugin](https://github.com/stevenxxiu/albert_firefox)
- [Sagebind plugin](https://github.com/sagebind/dotfiles/blob/master/home.linux/.local/share/albert/python/plugins/firefoxbookmarks/__init__.py)
- [Official but archived C++ plugin](https://github.com/albertlauncher/plugins/tree/main/.archive/firefoxbookmarks)
