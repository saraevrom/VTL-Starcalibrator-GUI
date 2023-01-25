from .base import Node

class ValueNode(Node):
    def __init__(self):
        self.value = None

    def parse_formdata(self, formdata):
        self.value = formdata

    def get_data(self):
        return self.value


class IntNode(ValueNode):
    FIELD_TYPE = "int"
    DEFAULT_VALUE = 0


class FloatNode(ValueNode):
    FIELD_TYPE = "float"
    DEFAULT_VALUE = 0.0


class StringNode(ValueNode):
    FIELD_TYPE = "str"
    DEFAULT_VALUE = ""


class BoolNode(ValueNode):
    FIELD_TYPE = "bool"
    DEFAULT_VALUE = False


class RadioNode(ValueNode):
    FIELD_TYPE = "radio"
    VALUES = []

    @classmethod
    def generate_configuration(cls):
        conf = super(RadioNode, cls).generate_configuration()
        conf["values"] = cls.VALUES
        return conf


class ComboNode(RadioNode):
    FIELD_TYPE = "combo"
    SELECTION_READONLY = False

    @classmethod
    def generate_configuration(cls):
        conf = super(ComboNode, cls).generate_configuration()
        conf["readonly"] = cls.SELECTION_READONLY
        return conf


class FileNode(ValueNode):
    FIELD_TYPE = "file"
