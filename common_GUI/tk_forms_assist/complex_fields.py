from .base import Node


class ArrayNode(Node):
    '''
    Node corresponding to the "array" entry
    Use ITEM_TYPE for specifying subconf
    '''
    FIELD_TYPE = "array"
    ITEM_TYPE = None

    def __init__(self):
        self.data_list = []

    def parse_formdata(self, formdata):
        self.data_list.clear()
        for item in formdata:
            item_typed = self.ITEM_TYPE()
            item_typed.parse_formdata(item)
            self.data_list.append(item_typed)

    def get_data(self):
        return [item.get_data() for item in self.data_list]

    @classmethod
    def generate_configuration(cls):
        conf = super(ArrayNode, cls).generate_configuration()
        conf["subconf"] = cls.ITEM_TYPE.get_config_persistent()
        return conf

    @classmethod
    def fill_configuration(cls):
        if super().fill_configuration():
            cls.ITEM_TYPE.fill_configuration()
            return True
        return False


class AlternatingNode(Node):
    '''
    Node corresponding to "alter" entry
    Use SEL__<name> for specifying selection types
    '''

    FIELD_TYPE = "alter"

    def __init__(self):
        self.value = None

    @classmethod
    def generate_configuration(cls):
        conf = super(AlternatingNode, cls).generate_configuration()
        values = []
        for k in cls.__dict__.keys():
            if k.startswith("SEL__"):
                name = k[5:]
                subconf = cls.__dict__[k].get_config_persistent()
                values.append({
                    "name": name,
                    "subconf": subconf
                })
        conf["values"] = values
        if cls.DEFAULT_VALUE is None:
            name0 = values[0]["name"]

            default_value = {
                "selection_type": name0
            }
            conf["default"] = default_value
        return conf

    @classmethod
    def fill_configuration(cls):
        if super().fill_configuration():
            for k in cls.__dict__.keys():
                if k.startswith("SEL__"):
                    cls.__dict__[k].fill_configuration()
            return True
        return False

    def parse_formdata(self, formdata):
        selection = formdata["selection_type"]
        obj_value = formdata["value"]
        self.value = type(self).__dict__["SEL__"+selection]()
        self.value.parse_formdata(obj_value)

    def get_data(self):
        return self.value.get_data()

class FormNode(Node):
    '''
    Node corresponding to the form itself and "subform" field
    Use FIELD__<name> for specifying fields
    Call get_configuration_root() for getting root form
    '''
    FIELD_TYPE = "subform"
    USE_SCROLLVIEW = True

    def __init__(self):
        self.fields = dict()
        for k in type(self).__dict__.keys():
            if k.startswith("FIELD__"):
                name = k[7:]
                self.fields[name] = type(self).__dict__[k]()

    def parse_formdata(self, formdata: dict):
        for k in formdata.keys():
            self.fields[k].parse_formdata(formdata[k])

    def get_data(self):
        res_dict = dict()
        for k in self.fields.keys():
            res_dict[k] = self.fields[k].get_data()
        return res_dict

    @classmethod
    def generate_configuration_root(cls):
        res_dict = dict()
        for k in cls.__dict__.keys():
            if k.startswith("FIELD__"):
                name = k[7:]
                res_dict[name] = cls.__dict__[k].get_config_persistent()
        return res_dict

    @classmethod
    def generate_configuration(cls):
        conf = super(FormNode, cls).generate_configuration()
        conf["use_scrollview"] = cls.USE_SCROLLVIEW
        conf["subconf"] = cls.generate_configuration_root()
        return conf

    @classmethod
    def fill_configuration(cls):
        if super().fill_configuration():
            cls.fill_configurations()
            return True
        return False


    @classmethod
    def fill_configurations(cls):
        for k in cls.__dict__.keys():
            if k.startswith("FIELD__"):
                cls.__dict__[k].fill_configuration()

    @classmethod
    def get_configuration_root(cls):
        cls.fill_configurations()
        return cls.generate_configuration_root()