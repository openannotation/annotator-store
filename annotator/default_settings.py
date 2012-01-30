from flask import Flask

DEBUG = False

SQLALCHEMY_DATABASE_URI = 'sqlite:///%s/annotator.db'

ELASTICSEARCH_HOST = '127.0.0.1:9200'
ELASTICSEARCH_INDEX = 'annotator'
