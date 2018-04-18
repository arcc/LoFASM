#__init__.py

__all__ = ['lofasm_dat_lib', 'parse_data', 'parse_data_H',
           'animate_lofasm', 'simulate', 'write', 'config',
           'fs']
from config import getConfig
import platform
import matplotlib

# matplotlib backend patch
if platform.system() == "Darwin":
    matplotlib.use("TkAgg")
elif platform.system() == "Linux":
    matplotlib.use("Agg")
version = '1.0.080917'
