import os
import sys
import traceback
from progressbar import Percentage, Bar
from mdb.progress import ProgressBar, Fraction
from mdb import Database

class Slurp:
    def __init__(self, server, name, paths):
        self.paths = paths
        self.current_files = 0
        self.current_dir = ''
        self.db = Database(server, name)

        self._count_files(paths)
        widgets = [Fraction(), ", ", Percentage(), " ", Bar()]
        self.bar = ProgressBar(self.total_files, widgets=widgets)

    def _count_files(self, paths):
        self.total_files = 0
        for files in self._walk(paths):
            self.total_files += len(files)
            sys.stderr.write("Counting files... %d\r" % self.total_files)
        sys.stderr.write("\n")

    def run(self):
        self.bar.start()
        for paths in self._walk(self.paths):
            self.current_dir = os.path.dirname(paths[0])
            self._update()
            try: self.db.add_many(paths)
            except Exception:
                print "Error when importing %s:" % self.current_dir
                traceback.print_exc()
            self._update(paths)
        self.bar.finish()

    def _update(self, paths = []):
        self.bar.fd.write("\033[1A\033[KSlurping %r...\r\033[1B" % self.current_dir)
        self.current_files += len(paths)
        self.bar.update(self.current_files)

    def _walk(self, paths):
        for path in paths:
            if os.path.isfile(path): yield [os.path.abspath(path)]
            else:
                for (dirname, _, files) in os.walk(path):
                    if files:
                        yield [os.path.abspath(os.path.join(dirname, f)) for f in files]
        
