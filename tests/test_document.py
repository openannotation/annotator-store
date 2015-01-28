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

    @staticmethod
    def test_new():
        d = Document()
        assert_equal('{}', repr(d))

    @staticmethod
    def test_basics():
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

    @staticmethod
    def test_delete():
        ann = Document(id=1)
        ann.save()

        newdoc = Document.fetch(1)
        newdoc.delete()

        nodoc = Document.fetch(1)
        assert nodoc is None

    @staticmethod
    def test_search():
        d = Document({
            "id": "1",
            "title": "document",
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
        res = Document.search(query={'title': 'document'})
        assert_equal(len(res), 1)

    @staticmethod
    def test_get_by_uri():

        # create 3 documents and make sure get_by_uri works properly

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

        doc = Document.get_by_uri("https://peerj.com/articles/53/")
        assert doc
        assert_equal(doc['title'], "document1") 

    @staticmethod
    def test_get_all_by_uri():
        # add two documents and make sure we can search for both

        d = Document({
            "id": "1",
            "title": "document1",
            "link": [
                {
                    "href": "https://peerj.com/articles/53/",
                    "type": "text/html"
                },
            ]
        })
        d.save()

        d = Document({
            "id": "2",
            "title": "document2",
            "link": [
                {
                    "href": "https://peerj.com/articles/53.pdf",
                    "type": "application/pdf"
                }
            ]
        })
        d.save()

        docs = Document.get_all_by_uris(["https://peerj.com/articles/53/", "https://peerj.com/articles/53.pdf"])
        assert_equal(len(docs), 2)

    @staticmethod
    def test_uris():
        d = Document({
            "id": "1",
            "title": "document",
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
        assert_equal(d.uris(), [
            "https://peerj.com/articles/53/",
            "https://peerj.com/articles/53.pdf"
        ])

    @staticmethod
    def test_merge_links():
        d = Document({
            "id": "1",
            "title": "document",
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

        d = Document.fetch(1)
        assert d
        assert_equal(len(d['link']), 2)

        d.merge_links([
            {
                "href": "https://peerj.com/articles/53/",
                "type": "text/html"
            },
            {
                "href": "http://peerj.com/articles/53.doc",
                "type": "application/vnd.ms-word.document"
            }
        ])
        d.save()

        assert_equal(len(d['link']), 3)
        d = Document.fetch(1)
        assert d
        assert_equal(len(d['link']), 3)

        doc = Document.get_by_uri("https://peerj.com/articles/53/")
        assert doc
        assert_equal(len(doc['link']), 3)


