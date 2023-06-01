#from distutils.core import setup
from setuptools import setup, find_packages

setup(
    name='canfix-utility',
    version='0.1.0',
    long_description=open('README.rst').read(),
    description="CAN-FIX Network Utility",
    author="Phil Birkelbach",
    author_email="phil@petrasoft.net",
    license='GNU General Public License Version 2',
    url='https://github.com/birkelbach/CAN-FIX-Utility',
    packages=find_packages(),
    package_data = {'config':['main.ini']},
    install_requires = ['python-can', 'tk', 'intelhex', 'python-canfix', 'appdirs' ],
    #test_suite = 'tests',
)
