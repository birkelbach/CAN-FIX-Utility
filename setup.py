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
    package_data = {'cfutil.data':['*.ini']},
    install_requires = ['python-can', 'intelhex', 'python-canfix', 'appdirs'],
    entry_points = {
        'console_scripts': ['cfutil=cfutil.main:main'],
    },

    #test_suite = 'tests',
)
