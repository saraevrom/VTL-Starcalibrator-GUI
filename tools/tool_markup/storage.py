from searching import comparing_binsearch

class ConservativeStorage(object):
    def __init__(self):
        self.on_store = None
        self.on_take = None

    def get_available(self):
        raise NotImplementedError("Cannot determine what is here")

    def store(self, item):
        raise NotImplementedError("Cannot store item here")

    def take(self, *args):
        raise NotImplementedError("Cannot take item from here")

    def take_external(self):
        item = self.take()
        if item is not None and self.on_take:
            self.on_take()
        return item

    def store_external(self, item):
        success = self.store(item)
        if success and self.on_store:
            self.on_store()
        return success

    def try_move_to(self, target, *args):
        item = self.take(*args)
        if item is not None:
            if target.store(item):
                if target.on_store:
                    target.on_store()
                if self.on_take:
                    self.on_take()
                return True
            else:
                self.store(item)
                return False
        return False



class ArrayStorage(ConservativeStorage):
    def __init__(self):
        super().__init__()
        self.storage = []

    def store(self, item):
        self.storage.append(item)
        return True

    def get_available(self):
        return self.storage


    def take(self, index):
        if 0 <= index < len(self.storage):
            return self.storage.pop(index)
        else:
            return None

    def clear(self):
        self.storage.clear()

class SingleStorage(ConservativeStorage):
    def __init__(self):
        super().__init__()
        self.item = None

    def store(self, item):
        if self.item is None:
            self.item = item
            return True
        else:
            return False

    def take(self):
        item = self.item
        self.item = None
        return item

    def drop(self):
        self.item = None

    def has_item(self):
        return self.item is not None

class Interval(object):
    def __init__(self,start,end):
        assert start<end
        self.start = start
        self.end = end
        assert isinstance(start,int)
        assert isinstance(end,int)

    def length(self):
        return self.end - self.start

    def inside_of(self,outer):
        return outer.start <= self.start and self.end <= outer.end

    def intersects(self,other):
        return self.start<other.end and other.start<self.end

    def subdivide(self):
        middle = (self.start+self.end)//2
        if middle == self.start:
            return None
        return Interval(self.start, middle), Interval(middle, self.end)

    def __repr__(self):
        return f"[{self.start}, {self.end})"

    def __str__(self):
        return f"[{self.start}, {self.end})"

    def __lt__(self, other):
        return self.start<other.start

    def __gt__(self, other):
        return self.start>other.start

    def is_same_as(self, other):
        return self.start == other.start and self.end == other.end


class IntervalStorage(ConservativeStorage):
    def __init__(self, start, end, empty=False):
        super().__init__()
        self.outer = Interval(start,end)
        self.taken_intervals = []
        if empty:
            self.taken_intervals.append(Interval(start,end))

    def has_interval(self,interval):
        return interval.inside_of(self.outer)

    def get_available_index_to_take(self, interval:Interval):
        if not self.has_interval(interval):
            return None
        if self.taken_intervals:
            closest_i = comparing_binsearch(self.taken_intervals, interval)
            if self.taken_intervals[closest_i].intersects(interval):
                return None
            if closest_i>0 and self.taken_intervals[closest_i-1].intersects(interval):
                return None
            if closest_i<len(self.taken_intervals)-1 and self.taken_intervals[closest_i+1].intersects(interval):
                return None
            closest = self.taken_intervals[closest_i]
            if closest<interval:
                return closest_i+1
            elif closest>interval:
                return closest_i
            else:
                raise RuntimeError(f"Somehow got equal non-intersecting intervals {closest} and {interval}")

        else:
            return 0


    def get_available_index_to_store(self, interval:Interval):
        if not self.has_interval(interval):
            return None
        if self.taken_intervals:
            assert isinstance(interval, Interval)
            closest_i = comparing_binsearch(self.taken_intervals, interval)
            source_i = None
            if interval.inside_of(self.taken_intervals[closest_i]):
                source_i = closest_i
            if source_i is None \
                    and closest_i>0 \
                    and interval.inside_of(self.taken_intervals[closest_i-1]):
                source_i = closest_i-1
            if source_i is None \
                    and closest_i < len(self.taken_intervals) - 1 \
                    and self.taken_intervals[closest_i + 1].intersects(interval):
                source_i = closest_i+1

            return source_i

        else:
            return None

    def simplify_from(self,index):
        simplifying = True
        while simplifying and index<len(self.taken_intervals)-1:
            e1 = self.taken_intervals[index].end
            s1 = self.taken_intervals[index+1].start
            if e1<s1:
                return
            else:
                assert e1==s1
                nextint = self.taken_intervals.pop(index+1)
                s = self.taken_intervals[index].start
                e = nextint.end
                self.taken_intervals[index] = Interval(s,e)

    def take(self, interval:Interval):
        index_to_take = self.get_available_index_to_take(interval)
        if index_to_take is None:
            return None
        else:
            self.taken_intervals.insert(index_to_take,interval)
            self.simplify_from(max(index_to_take-1,0))
            return interval

    def store(self, item:Interval):
        index = self.get_available_index_to_store(item)
        if index is None:
            return False
        target_interval = self.taken_intervals.pop(index)
        e2 = target_interval.end
        s2 = item.end
        if e2>s2:
            self.taken_intervals.insert(index,Interval(s2,e2))
        s1 = target_interval.start
        e1 = item.start
        if s1<e1:
            self.taken_intervals.insert(index,Interval(s1, e1))
        return True

    def get_available(self):
        last = self.outer.start
        r = []
        for item in self.taken_intervals:
            if last<item.start:
                r.append(Interval(last, item.start))
            last = item.end
        if last<self.outer.end:
            r.append(Interval(last,self.outer.end))
        return r

    def get_first_accessible(self):
        if self.taken_intervals:
            first_taken_interval = self.taken_intervals[0]
            if first_taken_interval.start > self.outer.start:
                return Interval(self.outer.start, first_taken_interval.start)
            elif len(self.taken_intervals)==1:
                if first_taken_interval.is_same_as(self.outer):
                    return None
                return Interval(first_taken_interval.end,self.outer.end)
            else:
                second_taken_interval = self.taken_intervals[1]
                return Interval(first_taken_interval.end, second_taken_interval.start)
        else:
            return self.outer

    def __repr__(self):
        return str(self)

    def __str__(self):
        free = self.get_available()
        rs = [str(item) for item in free]
        return f"U({', '.join(rs)})"