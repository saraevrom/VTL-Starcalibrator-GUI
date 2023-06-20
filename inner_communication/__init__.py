import builtins

SHARED_ACTIONS = dict()
def register_action(key, callable):
    def wrapper(*args,**kwargs):
        print(f"ACTION {key}")
        return callable(*args,**kwargs)

    SHARED_ACTIONS[key] = callable

def invoke(key,*args, **kwargs):
    return SHARED_ACTIONS[key](*args, **kwargs)

class ManualStopException(Exception):
    def __init__(self):
        super().__init__("Stopped")

def die():
    raise ManualStopException()

def run_script(source):
    globals = SHARED_ACTIONS.copy()
    globals["__builtins__"] = builtins
    globals["die"] = die
    try:
        exec (source, globals, dict())
    except ManualStopException:
        pass
