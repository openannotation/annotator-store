from setuptools import setup, find_packages

setup(
    name = 'annotator',
    version = '0.7.9',
    packages = find_packages(),

    install_requires = [
        'Flask==0.8',
        'pyes==0.19.1',
        'PyJWT==0.1.4',
        'iso8601==0.1.4',
        'nose==1.1.2',
        'mock==0.8.0'
    ],

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
