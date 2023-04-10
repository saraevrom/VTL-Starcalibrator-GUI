class Cutter(object):
    def cut(self, length):
        raise NotImplementedError("No idea how to cut")

class CutoffCutter(Cutter):
    def __init__(self, at_start, at_end):
        self.at_start = at_start
        self.at_end = at_end

    def cut(self, length):
        assert self.at_start<length
        assert self.at_end<length
        return self.at_start, self.at_end

class SliceCutter(Cutter):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def cut(self, length):
        if self.end<0:
            end = length-self.end
        else:
            end = self.end
        assert self.start<length
        assert end<length
        return self.start, length - end

class IntervalCutter(Cutter):
    def __init__(self, start, length):
        self.start = start
        self.cut_length = length

    def cut(self, length):
        end = self.start+self.cut_length
        assert self.start<length
        assert end<length
        return self.start, length - end
