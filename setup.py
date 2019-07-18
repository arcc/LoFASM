#!/usr/bin/python


from distutils.core import setup
from glob import glob
import os

galaxy_model_files = [os.path.basename(f) for f in glob('lofasm/galaxy_model/*.dat')]


setup(
    name='lofasm',
    version='0.1',
    author=['Louis P. Dartez', 'Jing Luo', 'LoFASM Data Analysis Team'],
    author_email='louis.dartez@gmail.com',

    packages=['lofasm',
              'lofasm.simulate',
              'lofasm.bbx',
              'lofasm.formats',
              'lofasm.data_file_info',
              'lofasm.calibrate',
              'lofasm.handler',
              'lofasm.galaxy_model'
              ],
    package_dir={'lofasm.simulate': 'lofasm/simulate',
                'lofasm.galaxy_model': 'lofasm/galaxy_model'
                 },
    package_data={'lofasm.simulate': ['lambda_haslam408_dsds.fits.txt'],
                'lofasm.galaxy_model': galaxy_model_files
                  },
    scripts=['bin/lofasm_plot.py',
             'bin/loco2bx.py',
             'bin/lofasm2csv.py',
             'bin/simulate_dispered_filterbank.py',
             'bin/cleanfile.py',
             'bin/normalize_data.py',
             'bin/clean_data.py',
             'bin/calibrate_plot.py',
             'bin/explorebbx2d'],

    description='LoFASM Tools',
    long_description=open('README.md').read(),
)
