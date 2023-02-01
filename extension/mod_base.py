class AppModifier(object):
    EXT_NAME = "FIXME"

    @staticmethod
    def modify_apply():
        raise NotImplementedError()

    @staticmethod
    def modify_needed():
        raise NotImplementedError()