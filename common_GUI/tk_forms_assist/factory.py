from .simple_fields import LabelNode

def create_value_field(form_t, display_name, default_value=None):
    class FieldClass(form_t):
        DISPLAY_NAME = display_name

    if default_value is not None:
        FieldClass.DEFAULT_VALUE = default_value

    return FieldClass

def create_label(label, fancy=False):
    class LabelClass(LabelNode):
        DISPLAY_NAME = label
        FANCY = fancy

    return LabelClass