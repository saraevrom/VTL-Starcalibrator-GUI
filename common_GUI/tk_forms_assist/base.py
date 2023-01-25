

PERSISTENT_CONFIGS = dict()

class Node(object):
    FIELD_TYPE = "FIXME"
    DEFAULT_VALUE = None
    DISPLAY_NAME = "Generic"

    def parse_formdata(self, formdata):
        raise NotImplementedError()

    def get_data(self):
        raise NotImplementedError()

    @classmethod
    def generate_configuration(cls):
        conf =  {
            "display_name": cls.DISPLAY_NAME,
            "type": cls.FIELD_TYPE
        }
        if cls.DEFAULT_VALUE is not None:
            conf["default"] = cls.DEFAULT_VALUE
        return conf


    @classmethod
    def get_config_persistent(cls):
        key = cls
        if key not in PERSISTENT_CONFIGS:
            PERSISTENT_CONFIGS[key] = dict()
        return PERSISTENT_CONFIGS[key]


    @classmethod
    def fill_configuration(cls):
        cls.get_config_persistent()
        key = cls
        if not PERSISTENT_CONFIGS[key]:
            PERSISTENT_CONFIGS[key].update(cls.generate_configuration())
            return True
        return False

    @classmethod
    def get_configuration(cls):
        cls.fill_configuration()
        key = cls
        return PERSISTENT_CONFIGS[key]

