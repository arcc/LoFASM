#!/usr/bin/python
#setup.py

from distutils.core import setup

setup(
    name='lofasm',
    version='1.0',
    author='Louis P. Dartez',
    author_email='louis.dartez@gmail.com',
    packages=['lofasm'],
    scripts=['bin/initialize.py','bin/ten_gbe_recorder.py','bin/poco_plot.py'],
    description='LoFASM Tools',
    long_description=open('README').read(),
    install_requires=[
        "matplotlib >= 1.1.1",
        "numpy >= 1.6.2",
        ],
)


