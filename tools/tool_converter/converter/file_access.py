import fsspec
import os.path
from compatibility.h5py_aliased_fields import SafeMatHDF5
from compatibility.alt_ftp import FTPFileSystem

class FileAccess(object):
    def get_file_read(self):
        raise NotImplementedError()

    def get_repr(self):
        raise NotImplementedError()

    def __eq__(self, other):
        return self.get_repr() == other.get_repr()

    def get_h5(self):
        handle = self.get_file_read()
        return SafeMatHDF5(handle,"r")

class LocalFileAccess(FileAccess):
    def __init__(self, filename):
        self.filename = filename

    def get_file_read(self):
        return open(self.filename, "rb")

    def get_repr(self):
        return os.path.basename(self.filename)


class RemoteFileAccess(FileAccess):
    def __init__(self, addr, login, password, filename):
        self.addr = addr
        self.login = login
        self.password = password
        self.filename = filename

    def get_file_read(self):
        fs = FTPFileSystem(host=self.addr, username=self.login, password=self.password)
        return fs.open(self.filename, "rb")

    def get_repr(self):
        fn = self.filename
        addr = self.addr
        return f"ftp://{addr}/{fn}"
