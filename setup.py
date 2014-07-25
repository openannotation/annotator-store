from setuptools import setup, find_packages
import os

requires = [
    'Flask==0.9',
    'elasticsearch',
    'PyJWT==0.1.4',
    'iso8601==0.1.4',
]

def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), 'r') as f:
        return f.read()

setup(
    name = 'annotator',
    version = '0.11.2',
    packages = find_packages(exclude=['test*']),

    install_requires = requires,
    extras_require = {
        'docs': ['Sphinx'],
        'testing': ['nose', 'coverage'],
    },

    # metadata for upload to PyPI
    author = 'Rufus Pollock and Nick Stenning (Open Knowledge Foundation)',
    author_email = 'annotator@okfn.org',
    description = 'Database backend for Annotator (http://annotatorjs.org)',
    long_description = (read('README.rst') + '\n\n' +
                        read('CHANGES.rst')),
    license = 'MIT',
    keywords = 'annotation web javascript',

    url = 'http://annotatorjs.org/',
    download_url = 'https://github.com/openannotation/annotator-store',

    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'
    ],
)
