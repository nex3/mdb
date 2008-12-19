import os
import sys
import traceback
from progressbar import Percentage, Bar
from mdb.progress import ProgressBar, Fraction
from mdb import Database

class Slurp:
    def __init__(self, paths, server, name, progress=True):
        self.paths = paths
        self.current_files = 0
        self.current_dir = ''
        self.db = Database(server, name)
        self.progress = progress

        if progress:
            self._count_files(paths)
            widgets = [Fraction(), ", ", Percentage(), " ", Bar()] if progress else []
            self.bar = ProgressBar(self.total_files, widgets=widgets)

    def _count_files(self, paths):
        self.total_files = 0
        for files in self._walk(paths):
            self.total_files += len(files)
            if self.progress:
                sys.stderr.write("Counting files... %d\r" % self.total_files)
        if self.progress:
            sys.stderr.write("\n")

    def run(self):
        if self.progress: self.bar.start()
        for paths in self._walk(self.paths):
            self.current_dir = os.path.dirname(paths[0])
            self._update()
            try: self.db.add_many(paths)
            except Exception:
                sys.stderr.write("Error when importing %s:\n" % self.current_dir)
                traceback.print_exc()
                if self.progress: sys.stderr.write("\n\n")
            self._update(paths)
        if self.progress: self.bar.finish()

    def _update(self, paths = []):
        if not self.progress: return
        self.bar.fd.write("\033[1A\033[KSlurping %s...\r\033[1B" % self.current_dir)
        self.current_files += len(paths)
        self.bar.update(self.current_files)

    def _walk(self, paths):
        for path in paths:
            if os.path.isfile(path): yield [os.path.abspath(path)]
            else:
                for (dirname, _, files) in os.walk(path):
                    if files:
                        yield [os.path.abspath(os.path.join(dirname, f)) for f in files]
