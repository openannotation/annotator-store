from flask import Flask

DEBUG = False

ROOT_URL = 'http://annotateit.org'

SQLALCHEMY_DATABASE_URI = 'sqlite:///%s/annotator.db'

ELASTICSEARCH_HOST = '127.0.0.1:9200'
ELASTICSEARCH_INDEX = 'annotator'

MOUNT_STORE = '/api'
MOUNT_USER = '/user'
MOUNT_HOME = '/'
