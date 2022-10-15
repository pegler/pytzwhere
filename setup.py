import os
from setuptools import setup, find_packages

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='geodjango-tzwhere',
    version='0.1',
    packages=find_packages(),
    package_data={
        'geodjango-tzwhere': [
            'tz_world.json.gz',
        ]
    },
    include_package_data=True,
    install_requires=[
        'django>=1.11'
    ],
    license='MIT License',
    description='Python library to look up timezone from lat / long offline',
    long_description=README,
    url='https://github.com/cjh79/geodjango-tzwhere',
    author='Chris Hawes',
    author_email='chrishawes@gmail.com',
    maintainer='Christopher Hawes',
    maintainer_email='chrishawes@gmail.com',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Localization',
    ],
)
