import os
from sys import platform
import subprocess


TESTCMD = "import tensorflow as tf; print(len(tf.config.list_physical_devices('GPU')))"


def test_tf_need():
    res = subprocess.run(["python", "-c", TESTCMD], capture_output=True)
    output = res.stdout.decode("utf-8").strip()
    if not output:
        print("NO TENSORFLOW")
        return False   # No tensorflow
    return int(output) == 0 # If zero cores available

def add_to_ldpath(pkg):
    pkg_file = pkg.__file__
    pkg_dir = os.path.join(os.path.dirname(pkg_file), "lib")
    print("ADDING TO LD_LIBRARY_PATH", pkg_dir)
    old = os.environ.get("LD_LIBRARY_PATH")
    if old:
        if pkg_dir in os.environ["LD_LIBRARY_PATH"].split(":"):
            print("NO NEED")
        else:
            print("DONE")
            os.environ["LD_LIBRARY_PATH"] = old + ":" + pkg_dir
    else:
        os.environ["LD_LIBRARY_PATH"] = pkg_dir

if platform == "linux" or platform == "linux2":
    if test_tf_need():
        try:
            import nvidia.cudnn
            import tensorrt
            add_to_ldpath(nvidia.cudnn)
            add_to_ldpath(tensorrt)

        except ImportError:
            print("Skipped CUDNN init")
    else:
        print("No need for CUDNN")
else:
    print("Skipped CUDNN init (platform mismatch)")