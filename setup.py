#!/usr/bin/env python

# Copyright (c) 2017, The Linux Foundation. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#     * Neither the name of The Linux Foundation nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import sys
import yaml

from setuptools import setup
from setuptools.command.install import install

from license_identifier.util import show_licenses_from_directory

CUSTOM_DIR = 'license_identifier/data/license_dir/custom/'


def check_custom_yml_up_to_date():
    with open('license_identifier/data/custom_license.yml') as file:
        mappings = yaml.safe_load(file)

    files_in_mappings = mappings.keys()
    custom_licenses = show_licenses_from_directory(CUSTOM_DIR)
    assert set(files_in_mappings) == set(custom_licenses)


if sys.argv[-1] == 'sdist':
    try:
        check_custom_yml_up_to_date()
    except AssertionError:
        print("Please update custom_license.yml file.")
        sys.exit(1)


class CustomInstall(install):

    def run(self):
        # Perform original install steps
        install.run(self)

        # Perform custom install steps
        from license_identifier.license_identifier import LicenseIdentifier

        license_dir = os.path.join(
            self.install_lib, 'license_identifier/data/license_dir'
        )
        pickle_file_path = os.path.join(
            self.install_lib,
            'license_identifier/data/license_n_gram_lib.pickle'
        )

        LicenseIdentifier(license_dir=license_dir,
                          pickle_file_path=pickle_file_path)


setup(
    name='lid',
    version='1.2.4',
    description='Scans a file or folder for predefined licenses',
    author='Peter Shin',
    author_email='phshin@codeaurora.org',
    url='https://www.python.org/sigs/distutils-sig/',
    packages=['license_identifier'],
    entry_points={
        'console_scripts': [
            'license-identifier = license_identifier.cli:main',
        ],
    },
    install_requires=[
        "chardet",
        "future",
        "nltk==3.2.1",
        "pyyaml",
        "rdflib",
        "six",
    ],
    package_data={
        'license_identifier': [
            'data/license_n_gram_lib.pickle',
            'data/license_dir/*.txt',
            'data/license_dir/custom/*.txt',
            'data/license_dir/headers/*.txt',
            'data/license_dir/exceptions/*.txt',
        ]
    },
    cmdclass={'install': CustomInstall},
)
