# Open Firefox Bookmarks and History in AlbertLauncher

This plugin/extension helps you open your **Firefox bookmarks and history** in [AlbertLauncher](https://albertlauncher.github.io/).

Albert will present the entries in frequency order: the more you use a bookmark, the higher it will be in the list.

## Features

- Open bookmarks and history from Firefox
- Select the Profile to use in the Preferences
- Enable or not the history search

## TODO

- [x] Index bookmarks
- [x] Index history (with preferences)
- [x] Select the profile to use
- [ ] (maybe) Select many profiles to index
- [ ] (complex) Favicon in the results (those are in another DB, need to extracted on disk...)

## Setup

1. Make the plugin directory

```
mkdir -p ~/.local/share/albert/python/plugins/firefox/
```

2. Clone the repository

```
git clone https://github.com/tomsquest/albert_plugin_firefox_bookmarks.git ~/.local/share/albert/python/plugins
```

## Alternatives

- [Stevenxxiu plugin](https://github.com/stevenxxiu/albert_firefox)
- [Sagebind plugin](https://github.com/sagebind/dotfiles/blob/master/home.linux/.local/share/albert/python/plugins/firefoxbookmarks/__init__.py)
- [Official but archived C++ plugin](https://github.com/albertlauncher/plugins)
