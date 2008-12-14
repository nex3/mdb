from datetime import datetime

from mdb.formats import MusicFile
from couchdb.client import Server

SAVED_METATAGS = [
    "~filename", "~format", "~mountpoint", "~performers", "~people",
    "~#added", "~#bitrate", "~#length", "~#year", "~#mtime",
    "~#disc", "~#discs", "~#track", "~#tracks"
    ]

class Database:
    def __init__(self, server, name):
        self.server = Server(server)
        if name in self.server: self.db = self.server[name]
        else: self.db = self.server.create(name)

    def add(self, path):
        song = self.song_for(path)
        if song is None: return
        self.db[song.key] = self.dict_for(song)

    def add_many(self, paths):
        self.db.update(map(self.dict_for,
                           filter(None,
                                  map(self.song_for, paths))))

    def song_for(self, path):
        try: return MusicFile(path)
        except IOError: return None

    def dict_for(self, song):
        d = {}
        for tag in SAVED_METATAGS + song.realkeys():
            d[tag] = song(tag)
            if isinstance(d[tag], str) or isinstance(d[tag], unicode):
                d[tag] = d[tag].split("\n")
        d["_id"] = song.key
        return d
