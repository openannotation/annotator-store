from flask import g
from nose.tools import *

from . import TestCase
from annotator.document import Document


peerj = {
    "html": {
        "href": "https://peerj.com/articles/53/",
        "type": "text/html"
    },
    "pdf": {
        "href": "https://peerj.com/articles/53.pdf",
        "type": "application/pdf"
    },
    "doc": {
        "href": "http://peerj.com/articles/53.doc",
        "type": "application/vnd.ms-word.document"
    },
    "docx": {
        "href": "https://peerj.com/articles/53.docx",
        "type": "application/vnd.ms-word.document"
    }
}


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
        # Creating a single document and verifies the saved attributes
        d = Document({
            "id": "1",
            "title": "Annotations: The Missing Manual",
            "link": [peerj["html"], peerj["pdf"]]
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
    def test_deficient_links():
        # Test that bad links are not saved
        d = Document({
            "id": "1",
            "title": "Chaos monkey: The messed up links",
            "link": [{
                "href": "http://cuckoo.baboon/"
            }, {
                # I'm an empty link entry
            }, {
                "type": "text/html"
            }, {
                "href": "http://cuckoo.baboon/",
                "type": "text/html"
            }]
        })
        d.save()
        d = Document.fetch("1")
        assert_equal(len(d['link']), 1)
        assert_equal(d['link'][0]['href'], "http://cuckoo.baboon/")
        assert_equal(d['link'][0]['type'], "text/html")

    @staticmethod
    def test_delete():
        # Test deleting a document
        ann = Document(id=1)
        ann.save()

        newdoc = Document.fetch(1)
        newdoc.delete()

        nodoc = Document.fetch(1)
        assert nodoc is None

    @staticmethod
    def test_search():
        # Test search retrieve
        d = Document({
            "id": "1",
            "title": "document",
            "link": [peerj["html"], peerj["pdf"]]
        })
        d.save()
        res = Document.search(query={'title': 'document'})
        assert_equal(len(res), 1)

    @staticmethod
    def test_get_by_uri():
        # Make sure that only the document with the given uri is retrieved

        d = Document({
            "id": "1",
            "title": "document1",
            "link": [peerj["html"], peerj["pdf"]]
        })
        d.save()

        d = Document({
            "id": "2",
            "title": "document2",
            "link": [
                {
                    "href": "http://nature.com/123/",
                    "type": "text/html"
                }
            ],
        })
        d.save()

        d = Document({
            "id": "3",
            "title": "document3",
            "link": [peerj["doc"]]
        })
        d.save()

        doc = Document.get_by_uri("https://peerj.com/articles/53/")
        assert doc
        assert_equal(doc['title'], "document1") 

    @staticmethod
    def test_uris():
        d = Document({
            "id": "1",
            "title": "document",
            "link": [peerj["html"], peerj["pdf"]]
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
            "link": [peerj["html"], peerj["pdf"]]
        })
        d.save()

        d = Document.fetch(1)
        assert d
        assert_equal(len(d['link']), 2)

        d.merge_links([peerj["html"], peerj["doc"]])
        d.save()

        assert_equal(len(d['link']), 3)
        d = Document.fetch(1)
        assert d
        assert_equal(len(d['link']), 3)

        doc = Document.get_by_uri("https://peerj.com/articles/53/")
        assert doc
        assert_equal(len(doc['link']), 3)

    @staticmethod
    def test_save():
        d1 = Document({
            "id": "1",
            "title": "document1",
            "link": [peerj["html"], peerj["pdf"]]
        })
        d1.save()

        d2 = Document({
            "id": "2",
            "title": "document2",
            "link": [peerj["pdf"], peerj["doc"]]
        })
        d2.save()

        d3 = Document({
            "id": "3",
            "title": "document3",
            "link": [peerj["doc"], peerj["docx"]]
        })
        d3.save()

        d4 = Document({
            "id": "4",
            "title": "document4",
            "link": [peerj["docx"]]
        })
        d4.save()

        d1 = Document.fetch(1)
        d2 = Document.fetch(2)
        d3 = Document.fetch(3)
        d4 = Document.fetch(4)
        assert d1
        assert d2 is None
        assert d3 is None
        assert d4 is None

    @staticmethod
    def test_save_merge_documents():
        d1 = Document({
            "id": "1",
            "title": "document1",
            "link": [peerj["html"], peerj["pdf"]]
        })
        d1.save()

        d2 = Document({
            "id": "2",
            "title": "document2",
            "link": [peerj["doc"], peerj["docx"]]
        })
        d2.save()

        # They are not merged yes
        d1 = Document.fetch(1)
        d2 = Document.fetch(2)
        assert d1
        assert d2

        d3 = Document({
            "id": "3",
            "title": "document3",
            "link": [peerj["doc"], peerj["docx"]]
        })
        d3.save()

        d3 = Document.fetch(3)
        assert d3 is None

        d4 = Document({
            "id": "4",
            "title": "document4",
            "link": [
                {
                    "href": "https://totallydifferenturl.com",
                    "type": "text/html"
                }
            ]
        })

        # A new document is created for d4
        # It is not merged
        d4.save()
        count = Document.count()
        assert count == 3

        d5 = Document({
            "id": "5",
            "title": "document5",
            "link": [peerj["pdf"], peerj["doc"]]
        })

        d5.save()

        # The documents have been merged into d2
        d1 = Document.fetch(1)
        d2 = Document.fetch(2)
        d3 = Document.fetch(3)
        d4 = Document.fetch(4)
        d5 = Document.fetch(5)

        assert d1 is None
        assert d2
        assert d3 is None
        assert d4
        assert d5 is None
