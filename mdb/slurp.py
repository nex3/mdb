import os
import traceback
from progressbar import ProgressBar
from mdb import Database

class Slurp:
    def __init__(self, server, name, paths):
        self.paths = paths
        self.current_files = 0
        self.db = Database(server, name)
        print "Calculating number of files..."
        self.total_files = sum(map(len, self.walk(paths)))
        self.bar = ProgressBar(self.total_files)

    def run(self):
        self.bar.start()
        for paths in self.walk(self.paths):
            try: self.db.add_many(paths)
            except Exception:
                print "Error when importing %s:" % os.path.dirname(paths[0])
                traceback.print_exc()
            self.update(paths)
        self.bar.finish()

    def update(self, paths):
        self.current_files += len(paths)
        self.bar.update(self.current_files)

    def walk(self, paths):
        for path in paths:
            if os.path.isfile(path): yield [os.path.abspath(path)]
            else:
                for (dirname, _, files) in os.walk(path):
                    yield [os.path.abspath(os.path.join(dirname, f)) for f in files]
        
