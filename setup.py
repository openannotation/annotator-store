from setuptools import setup, find_packages
import sys

requires = [
    'Flask==0.9',
    'pyes==0.19.1',
    'PyJWT==0.1.4',
    'iso8601==0.1.4',
]

if sys.version_info < (2, 7):
    requires.append('ordereddict==1.1')

setup(
    name = 'annotator',
    version = '0.9.1',
    packages = find_packages(),

    install_requires = requires,

    # metadata for upload to PyPI
    author = 'Rufus Pollock and Nick Stenning (Open Knowledge Foundation)',
    author_email = 'annotator@okfn.org',
    description = 'Database backend for the Annotator (http://annotateit.org)',
    license = 'MIT',
    keywords = 'annotation web javascript',

    url = 'http://okfnlabs.org/annotator/',
    download_url = 'https://github.com/okfn/annotator-store',

    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'
    ],
)
