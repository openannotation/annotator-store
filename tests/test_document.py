from flask import g
from nose.tools import *

from . import TestCase
from annotator.document import Document

class TestDocument(TestCase):

    def setup(self):
        super(TestDocument, self).setup()
        self.ctx = self.app.test_request_context(path='/api')
        self.ctx.push()
        g.user = None

    def teardown(self):
        self.ctx.pop()
        super(TestDocument, self).teardown()

    def test_new(self):
        d = Document() 
        assert_equal('{}', repr(d))

    def test_basics(self):
        d = Document({
            "id": "1", 
            "title": "Annotations: The Missing Manual",
            "link": [
                {
                    "href": "https://peerj.com/articles/53/",
                    "type": "text/html"
                },
                { 
                    "href": "https://peerj.com/articles/53.pdf",
                    "type": "application/pdf"
                }
            ],
        })
        d.save()
        d = Document.fetch("1")
        assert_equal(d["title"], "Annotations: The Missing Manual")
        assert_equal(len(d['link']), 2)
        assert_equal(d['link'][0]['href'], "https://peerj.com/articles/53/")
        assert_equal(d['link'][0]['type'], "text/html")
        assert_equal(d['link'][1]['href'], "https://peerj.com/articles/53.pdf")
        assert_equal(d['link'][1]['type'], "application/pdf")
        assert d['created']
        assert d['updated']

    def test_delete(self):
        ann = Document(id=1)
        ann.save()

        newdoc = Document.fetch(1)
        newdoc.delete()

        nodoc = Document.fetch(1)
        assert nodoc == None


    def test_search(self):
        d = Document({
            "id": "1", 
            "title": "annotation",
            "link": [
                {
                    "href": "https://peerj.com/articles/53/",
                    "type": "text/html"
                },
                { 
                    "href": "https://peerj.com/articles/53.pdf",
                    "type": "application/pdf"
                }
            ],
        })
        d.save()
        res = Document.search(title='annotation')
        assert_equal(len(res), 1)

    def test_get_by_url(self):
        d = Document({
            "id": "1", 
            "title": "document1",
            "link": [
                {
                    "href": "https://peerj.com/articles/53/",
                    "type": "text/html"
                },
                { 
                    "href": "https://peerj.com/articles/53.pdf",
                    "type": "application/pdf"
                },
            ],
        })
        d.save()

        d = Document({
            "id": "2", 
            "title": "document2",
            "link": [
                {
                    "href": "https://peerj.com/articles/53/",
                    "type": "text/html"
                },
                { 
                    "href": "https://peerj.com/articles/53.pdf",
                    "type": "application/pdf"
                },
            ],
        })
        d.save()

        d = Document({
            "id": "3", 
            "title": "document3",
            "link": [
                {
                    "href": "http://nature.com/123/",
                    "type": "text/html"
                }
            ],
        })
        d.save()

        doc = Document.get_by_url("https://peerj.com/articles/53/")
        assert doc
        assert_equal(doc['title'], "document1") 

        docs = Document.get_all_by_url("https://peerj.com/articles/53/")
        assert_equal(len(docs), 2)
