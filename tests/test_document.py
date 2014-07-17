from flask import g
from nose.tools import *

from . import TestCase, es
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
        d.save(es)
        d = Document.fetch(es, "1")
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
        ann.save(es)

        newdoc = Document.fetch(es, 1)
        newdoc.delete(es)

        nodoc = Document.fetch(es, 1)
        assert nodoc == None

    def test_search(self):
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
        d.save(es)
        res = Document.search(es, title='document')
        assert_equal(len(res), 1)

    def test_get_by_uri(self):

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
        d.save(es)

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
        d.save(es)

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
        d.save(es)

        doc = Document.get_by_uri(es, "https://peerj.com/articles/53/")
        assert doc
        assert_equal(doc['title'], "document1") 

    def test_get_all_by_uri(self):
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
        d.save(es)

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
        d.save(es)

        docs = Document.get_all_by_uris(es, ["https://peerj.com/articles/53/", "https://peerj.com/articles/53.pdf"])
        assert_equal(len(docs), 2)

    def test_uris(self):
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

    def test_merge_links(self):
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
        d.save(es)

        d = Document.fetch(es, 1)
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
        d.save(es)

        assert_equal(len(d['link']), 3)
        d = Document.fetch(es, 1)
        assert d
        assert_equal(len(d['link']), 3)

        doc = Document.get_by_uri(es, "https://peerj.com/articles/53/")
        assert doc
        assert_equal(len(doc['link']), 3)


