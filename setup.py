import os

from setuptools import setup, find_packages

VERSION = '1.0'

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='jira-work-logger',
    version=VERSION,
    classifiers=[
        'Intended Audience :: JIRA users',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
    ],
    packages=find_packages(),
    include_package_data=True,
    author='Pavel Terekhov',
    author_email='pavelterex@gmail.com',
    url='<url>',
    description='Autologger tool for JIRA work logs',
    install_requires=[
        'jira',
        'PyQt5==5.12.1',
        'PyYAML'
    ],
    entry_points={
        'console_scripts': [
            'jira-logger=jira-work-logger.jira_work_logger:runner'
        ],
    }
)
