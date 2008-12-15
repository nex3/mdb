import os
import urllib
from datetime import datetime

from couchdb.client import Server

import mdb.util
from mdb.formats import MusicFile

SAVED_METATAGS = [
    "~filename", "~dirname", "~format", "~mountpoint", "~performers",
    "~people", "~#added", "~#bitrate", "~#length", "~#year", "~#mtime",
    "~#disc", "~#discs", "~#track", "~#tracks"
    ]

SINGLETON_TAGS = ["~filename", "~dirname", "~format", "~mountpoint"]

DEFAULTS = {"~#disc": 1, "~#discs": 1}

def _id(path):
    if isinstance(path, unicode):
        path = path.encode("utf-8")
    return urllib.quote(path, '')

class Database:
    def __init__(self, server, name):
        self.server = Server(server)
        if name in self.server: self.db = self.server[name]
        else: self.db = self.server.create(name)

    def add(self, path):
        song = self.song_for(os.path.realpath(path))
        if song is None: return
        self.db[song.key] = self.dict_for(song)

    def add_many(self, paths):
        paths = map(os.path.realpath, paths)
        view = self.db.view('_view/update/all')
        def updated_file(path):
            docs = list(view[_id(path)])
            if not docs: return True
            return util.mtime(path) > docs[0].value["mtime"]

        songs = filter(None, map(self.song_for, filter(updated_file, paths)))
        if not songs: return
        songs = map(self.dict_for, songs)
        for song in songs:
            docs = list(view[song["_id"]])
            if not docs: break
            song["_rev"] = docs[0].value["_rev"]
        self.db.update(songs)

    def song_for(self, path):
        try: return MusicFile(path)
        except IOError: return None

    def dict_for(self, song):
        d = {}
        for tag in SAVED_METATAGS + song.realkeys():
            val = song(tag)
            if val:
                if isinstance(val, basestring):
                    val = util.fsdecode(val)
                    if not tag in SINGLETON_TAGS:
                        val = val.split("\n")
                d[tag] = val
        for tag, default in DEFAULTS.items():
            if not tag in song: song[tag] = default
        # CouchDB doesn't like apostrophes in keys for some reason...
        d["_id"] = _id(song.key)
        return d
