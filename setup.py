#!/usr/bin/env python
import kaknas
from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

def install():

    setup(
        name='kaknas',
        version=kaknas.__version__,
        description='kaknas website project',
        long_description=readme,
        author=kaknas.__author__,
        license='MIT',
        platforms=['POSIX'],
        classifiers=[
            'Development Status :: 1 - Planning',
            'License :: OSI Approved :: MIT License',
            'Environment :: Console',
            'Operating System :: POSIX',
            'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
            'Framework :: Flask',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',],
        packages=find_packages(exclude=('tests', )),
        install_requires=[
            'Flask==0.12.3',
            'Flask-Migrate==2.0.0',
            'Flask-Script==2.0.5',
            'Flask-SQLAlchemy==2.1',
            'mysqlclient==1.3.9',
            'requests==2.19.1',
            'Flask-Caching=1.4.0',
            'apscheduler==3.5.3',
            'Flask-APScheduler==1.6.0',
            'dulwich --global-option=--pure',
        ],
    )

if __name__ == "__main__":
    install()
