# Copyright 2004-2005 Joe Wreschnig, Michael Urman
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation
#
# $Id$

import sys
import traceback

from warnings import warn
from glob import glob
from os.path import dirname, basename, join

base = dirname(__file__)
self = basename(base)
parent = basename(dirname(base))
modules = [f[:-3] for f in glob(join(base, "[!_]*.py"))]
modules = ["%s.%s.%s" % (parent, self, basename(m)) for m in modules]

_infos = {}
for i, name in enumerate(modules):
    try: format = __import__(name, {}, {}, self)
    except Exception, err:
        traceback.print_exc()
        continue
    format = __import__(name, {}, {}, self)
    for ext in format.extensions:
        _infos[ext] = format.info
    # Migrate pre-0.16 library, which was using an undocumented "feature".
    sys.modules[name.replace(".", "/")] = format
    if name and name.startswith("mdb."):
        sys.modules[name.split(".", 1)[1]] = sys.modules[name]
    modules[i] = (format.extensions and name.split(".")[-1])

try: sys.modules["formats.flac"] = sys.modules["formats.xiph"]
except KeyError: pass
try: sys.modules["formats.oggvorbis"] = sys.modules["formats.xiph"]
except KeyError: pass

modules = filter(None, modules)
modules.sort()

def MusicFile(filename):
    for ext in _infos.keys():
        if filename.lower().endswith(ext):
            return _infos[ext](filename)
    else: return None

def supported(song):
    for ext in _infos.keys():
        if song.key.lower().endswith(ext):
            return True
    return False

def filter(filename):
    for ext in _infos.keys():
        if filename.lower().endswith(ext): return True
    return False
