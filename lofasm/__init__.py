#__init__.py

__all__ = ['lofasm_dat_lib', 'parse_data', 'parse_data_H',
           'animate_lofasm', 'simulate', 'write', 'config',
           'fs']
from config import getConfig
import platform
import matplotlib

# matplotlib backend patch for Mac OS X
if platform.system() == "Darwin":
    matplotlib.use("TkAgg")
version = '1.0.080917'
