import progressbar
from progressbar import ProgressBarWidget

class Fraction(ProgressBarWidget):
    def update(self, pbar):
        return "%d/%d" % (pbar.currval, pbar.maxval)

class ProgressBar(progressbar.ProgressBar):
    def _need_update(self): return True
