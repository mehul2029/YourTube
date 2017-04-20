#!/usr/bin/env python
from setuptools import setup, find_packages
from distutils.command import build as build_module
import os
import sys
from database.init_db import Videoinfo, Videorel, UserDB

if sys.hexversion < 0x30400f0:
    print('YourTube requires at least Python 3.4')
    sys.exit(1)

# Set up required databases.
def setup_db():
	obj = Videoinfo()
	obj.init_db()
	obj = Videorel()
	obj.init_db()
	obj = UserDB()
	print('Databases set up.')
setup_db()


version = "0.1"

setup(
	name = "YourTube",
	version = version,
	url = "https://github.com/mehul2029/YourTube",
	packages = find_packages(),
	incude_packages_data = True,
	install_requires = [
		'py2neo<=3.1.2',
		'pymongo',
		'sqlalchemy',
		'mysqlclient',
		'pymysql',
		'pandas',
	],
)
