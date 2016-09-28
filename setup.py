#!/usr/bin/python


from distutils.core import setup

setup(
    name='lofasm',
    version='0.1',
    author='Louis P. Dartez',
    author_email='louis.dartez@gmail.com',

    packages=['lofasm', 'lofasm.simulate'],

    scripts=['bin/initialize.py','bin/ten_gbe_recorder.py','bin/lofasm_plot.py',
    'bin/rec_snap.sh', 'bin/init_roach.sh', 'bin/simulate_signal_as_AA.py',
    'bin/simulate_zeros_as_AA.py', 'bin/lofasm-chop.py','bin/LoFASM_GUI.py',
    'bin/sched_parser.py','bin/schedule_obs.py', 'bin/lofasm2fil.py',
     'bin/fbplot.py', 'bin/applyDelay.py', 'bin/lofasm2d.py', 'bin/lightcurve.py',
     'bin/skymap.py', 'bin/readfile.py', 'bin/waterfall.py', 'bin/stethoscope.py',
     'bin/record.py'],
    description='LoFASM Tools',
    long_description=open('README.md').read(),
    install_requires=[
        "matplotlib >= 1.1.1",
        "numpy >= 1.6.2",
        "scipy",
        "astropy"],
)
