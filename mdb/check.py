import os
import sys
import traceback

from progressbar import ProgressBar, Percentage, Bar

import mdb.util as util
from mdb import Database

class Check:
    def __init__(self, server, name, progress=True):
        self.current_files = 0
        self.db = Database(server, name)
        self.progress = progress
        self.view = self.db.db.view('_view/update/check')

        if self.progress:
            sys.stderr.write("Counting files...\r")
            self.total_files = len(self.view)
            self.bar = ProgressBar(self.total_files)
        else:
            self.total_files = sys.maxint

    def run(self):
        if self.progress: self.bar.start()

        mount_errors = set()
        for i, doc in enumerate(row.value for row in self.view):
            if "mountpoint" in doc:
                mountpoint = util.qencode(doc["mountpoint"])
                if not os.path.ismount(mountpoint):
                    if not mountpoint in mount_errors:
                        sys.stderr.write("Error: %s isn't mounted\n" % mountpoint)
                        if self.progress: sys.stderr.write("\n\n")
                        mount_errors.add(mountpoint)
                    continue
            filename = util.qencode(doc["filename"])
            try:
                if not os.path.isfile(filename):
                    self.db.remove(filename)
                elif util.mtime(filename) > doc["mtime"]:
                    self.db.update(doc, filename)
            except Exception:
                print "Error when updating %s:" % filename
                traceback.print_exc()
                if self.progress: sys.stderr.write("\n\n")
            if self.progress: self.bar.update(i)
        if self.progress: self.bar.finish()
