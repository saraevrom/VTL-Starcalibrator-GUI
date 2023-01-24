class BaseNode(object):
    def set_data(self, obj):
        raise NotImplementedError()

    def get_data(self):
        raise NotImplementedError()

class ValueNode(BaseNode):
    def __init__(self):
        self.value = None

    def set_data(self, obj):
        self.value = obj

    def get_data(self):
        return self.value

class ArrayNode(BaseNode):
    def __init__(self, used_class):
        self.buffer = []
