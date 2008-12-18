import traceback
import time
import os

import pyinotify as pyi

from mdb import Database
from mdb.slurp import Slurp

class Process(pyi.ProcessEvent):
    def __init__(self, server, name):
        self.server = server
        self.name = name
        self.db = Database(server=server, name=name)

    def process_IN_DELETE(self, event):
        if event.is_dir: return

        path = os.path.join(event.path, event.name)
        print "Removing %s..." % path
        self.db.remove(path)

    def process_IN_MOVED_TO(self, event):
        if not event.is_dir:
            self.process_default(event)
            return

        path = os.path.join(event.path, event.name)
        print "Slurping %s..." % path
        Slurp([path], server=self.server, name=self.name, progress=False).run()

    def process_default(self, event):
        if event.is_dir: return

        path = os.path.join(event.path, event.name)
        print "Updating %s..." % path

        for attempt in range(10):
            try:
                self.db.add(path)
                break
            except EOFError:
                if attempt < 9:
                    print "File not yet written, waiting a second..."
                    time.sleep(1)
                else:
                    print "Giving up."

mask = pyi.EventsCodes.IN_CREATE | pyi.EventsCodes.IN_MODIFY | \
    pyi.EventsCodes.IN_DELETE | pyi.EventsCodes.IN_MOVED_TO
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
        self.wm.add_watch(path, mask, rec=True, auto_add=True)
