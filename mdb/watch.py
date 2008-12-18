import traceback
import time
import os

import pyinotify as pyi

from mdb import Database

class Process(pyi.ProcessEvent):
    def __init__(self, server, name):
        self.db = Database(server=server, name=name)

    def process_IN_CREATE(self, event):
        path = os.path.join(event.path, event.name)
        print "Adding %s..." % path
        time.sleep(0.1) # Make sure the file is actually written
        self.db.add(path)

mask = pyi.EventsCodes.IN_CREATE
class Watcher:
    def __init__(self, *args, **kwargs):
        self.wm = pyi.WatchManager()
        self.notifier = pyi.Notifier(self.wm, Process(*args, **kwargs))

    def start(self):
        while True:
            try:
                self.notifier.process_events()
                if self.notifier.check_events():
                    self.notifier.read_events()
            except Exception:
                traceback.print_exc()
            except KeyboardInterrupt:
                self.notifier.stop()
                break

    def watch(self, path):
        self.wm.add_watch(path, mask, rec=True)
