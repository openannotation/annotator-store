from setuptools import setup, find_packages
from annotator import __version__, __license__, __author__

setup(
    name = 'annotator',
    version = __version__,
    packages = find_packages(),

    install_requires = [
        'Flask==0.8',
        'Flask-WTF==0.5.2',
        'Flask-SQLAlchemy==0.15',
        'SQLAlchemy==0.7.4',
        'pyes==0.16.0',
        'nose==1.0.0',
        'mock==0.7.4',
        'iso8601==0.1.4'
    ],

    # metadata for upload to PyPI
    author = __author__,
    author_email = 'annotator@okfn.org',
    description = 'Inline web annotation application and middleware using javascript and WSGI',
    long_description = """Inline javascript-based web annotation library. \
Package includeds a database-backed annotation store \
with RESTFul (WSGI-powered) web-interface.""",
    license = __license__,
    keywords = 'annotation web javascript',

    url = 'http://okfnlabs.org/annotator/',
    download_url = 'https://github.com/okfn/annotator-store',

    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'
    ],
)
