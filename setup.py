import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

# create shapely pickle if shapely is installed

import os, sys
from distutils.core import setup
from distutils.command.install import install as _install


def _post_install(dir):
    from subprocess import call
    call([sys.executable, 'tzwhere/tzwhere.py'],
         cwd=os.path.join(dir, 'packagename'))


class install(_install):
    def run(self):
        _install.run(self)
        self.execute(_post_install, (self.install_lib,),
                     msg="Creating timezone map")

setup(
    name='tzwhere',
    version='3.0a',
    packages=['tzwhere'],
    package_data={
        'tzwhere': ['tz_world.json']
        },
    include_package_data=True,
    install_requires=[
        'numpy',
        'shapely'
    ],
    license='MIT License',
    description='Python library to look up timezone from lat / long offline',
    long_description=README,
    url='https://github.com/pegler/pytzwhere',
    author='Matt Pegler',
    author_email='matt@pegler.co',
    maintainer='Christoph Stich',
    maintainer_email='christoph@stich.xyz',
    cmdclass={'install': install},
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
	'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Localization',
    ],
)
