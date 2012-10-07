# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from provy import __version__

setup(
    name='provy',
    version=__version__,
    description="provy is an easy-to-use server provisioning tool.",
    long_description="provy is an easy-to-use server provisioning tool.",
    keywords='provisioning devops infrastructure server',
    author='Bernardo Heynemann',
    author_email='heynemann@gmail.com',
    url='http://heynemann.github.com/provy',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6',
        'Topic :: System :: Installation/Setup'
    ],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['*.template'],
    },

    install_requires=[
        "fabric",
        "jinja2",
        "M2Crypto",
        "configobj",
    ],

    entry_points={
        'console_scripts': [
            'provy = provy.console:main',
        ],
    },

)
