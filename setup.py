from setuptools import setup

setup(name="ctdsampler",
      version="0.1",
      packages = ['ctdsampler'],
      py_modules = [],
      entry_points = {'console_scripts':['ctdsampler = ctdsampler.scripts:main'],
                      'gui_scripts':[]
                      },
      install_requires = 'urwid matplotlib pyserial pyserial-asyncio'.split(),
      author="Lucas Merckelbach",
      author_email="lucas.merckelbach@hzg.de",
      description="A simple program with UI to monitor a Seabird GPCTD",
      long_description="""A simple program with UI to monitor a Seabird GPCTD""",
      url='http://dockserver0.hzg.de/software/ctdsampler.html',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Scientific/Engineering',
      ])
