
class SortedQueue(object):
    def __init__(self):
        self.queue = []

    def push(self, common_data, index):
        i = 0
        while i < len(self.queue) and index > self.queue[i][1]:
            i += 1
        self.queue.insert(i, (common_data, index))

    def pop(self):
        return self.queue.pop(0)