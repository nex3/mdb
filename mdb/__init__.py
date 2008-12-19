import os
import urllib
import glob
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

QUOTED_TAGS = ["~filename", "~dirname", "~mountpoint"]

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
            self._load_views()
        self.view = self.db.view('_view/update/mtime')

    def add(self, path):
        song = self._song_for(os.path.realpath(path))
        if song is None: return

        song = self._dict_for(song)
        doc = self._doc_for(song)
        if doc: song["_rev"] = doc.value["_rev"]
        self.db[song["_id"]] = song

    def add_many(self, paths):
        paths = map(os.path.realpath, paths)
        def updated_file(path):
            doc = self._doc_for(path)
            if not doc: return True
            return util.mtime(path) > doc.value["mtime"]

        songs = filter(None, map(self._song_for, filter(updated_file, paths)))
        if not songs: return
        songs = map(self._dict_for, songs)
        for song in songs:
            doc = self._doc_for(song)
            if not doc: continue
            song["_rev"] = doc.value["_rev"]
        self.db.update(songs)

    def remove(self, path):
        del self.db[_id(path)]

    def remove_docs(self, songs):
        for song in songs:
            song["_deleted"] = True
        self.db.update(songs)

    def update(self, doc, path):
        song = self._song_for(path)
        if song is None: return

        song = self._dict_for(song)
        song["_rev"] = doc["_rev"]
        self.db[song["_id"]] = song

    def docs_beneath(self, path):
        path = util.qdecode(path).split(os.path.sep)
        return [row.value for row in self.db.view('_view/tree/by-path', startkey=path, endkey=path + [{}])]

    def _song_for(self, path):
        try: return MusicFile(path)
        except IOError: return None

    def _dict_for(self, song):
        d = {}
        for tag in SAVED_METATAGS + song.realkeys():
            val = song(tag)
            if val:
                if isinstance(val, basestring):
                    if tag in QUOTED_TAGS:
                        val = util.qdecode(val)
                    else:
                        val = util.fsdecode(val)
                    if not tag in SINGLETON_TAGS:
                        val = val.split("\n")
                d[tag] = val
        for tag, default in DEFAULTS.items():
            if not tag in song: song[tag] = default
        d["~path"] = d["~filename"].split(os.path.sep)
        # CouchDB doesn't like apostrophes in keys for some reason...
        d["_id"] = _id(song.key)
        return d

    def _doc_for(self, song):
        docs = list(self.view[_id(song) if isinstance(song, basestring) else song["_id"]])
        if not docs: return None
        return docs[0]

    def _load_views(self):
        for view in glob.glob(util.data_path('views', '*.json')):
            name = os.path.basename(view)[0:-5]
            f = open(view)
            # Can't use __setitem__ 'cause it assumes content is a hash
            self.db.resource.put('_design/' + name, content=f.read())
            f.close()
