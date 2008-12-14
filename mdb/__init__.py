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

    def record(self, path):
        try: song = MusicFile(path)
        except IOError: return
        if song is None: return

        self.db.create(self.dict_for(song))

    def dict_for(self, song):
        d = {}
        for tag in SAVED_METATAGS + song.realkeys():
            d[tag] = song(tag)
            if isinstance(d[tag], str) or isinstance(d[tag], unicode):
                d[tag] = d[tag].split("\n")
        return d
