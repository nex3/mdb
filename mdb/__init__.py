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
        if name in self.server:
            self.db = self.server[name]
        else:
            self.db = self.server.create(name)
            self.db["_design/update"] = {
                "language": "javascript",
                "views": {
                    "all": {
                        "map": """
function(doc) {
  emit(doc._id, {mtime: doc["~#mtime"], _rev: doc._rev});
}
"""
                        }
                    }
                }
        self.view = self.db.view('_view/update/all')

    def add(self, path):
        song = self.song_for(os.path.realpath(path))
        if song is None: return

        song = self.dict_for(song)
        doc = self.doc_for(song)
        if doc: song["_rev"] = doc.value["_rev"]
        self.db[song["_id"]] = song

    def add_many(self, paths):
        paths = map(os.path.realpath, paths)
        def updated_file(path):
            doc = self.doc_for(path)
            if not doc: return True
            return util.mtime(path) > doc.value["mtime"]

        songs = filter(None, map(self.song_for, filter(updated_file, paths)))
        if not songs: return
        songs = map(self.dict_for, songs)
        for song in songs:
            doc = self.doc_for(song)
            if not doc: break
            song["_rev"] = doc.value["_rev"]
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

    def doc_for(self, song):
        docs = list(self.view[_id(song) if isinstance(song, basestring) else song["_id"]])
        if not docs: return None
        return docs[0]
