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

    def test_new(self):
        d = Document()
        assert_equal('{}', repr(d))

    def test_basics(self):
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

    def test_deficient_links(self):
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
        assert_equal(len(d['link']), 2)
        assert_equal(d['link'][0]['href'], "http://cuckoo.baboon/")
        assert_equal(d['link'][1]['href'], "http://cuckoo.baboon/")
        assert_equal(d['link'][1]['type'], "text/html")

    def test_delete(self):
        # Test deleting a document
        ann = Document(id=1)
        ann.save()

        newdoc = Document.fetch(1)
        newdoc.delete()

        nodoc = Document.fetch(1)
        assert nodoc is None

    def test_search(self):
        # Test search retrieve
        d = Document({
            "id": "1",
            "title": "document",
            "link": [peerj["html"], peerj["pdf"]]
        })
        d.save()
        res = Document.search(query={'title': 'document'})
        assert_equal(len(res), 1)

    def test_get_by_uri(self):
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

    def test_get_by_uri_not_found(self):
        assert Document.get_by_uri("bogus") is None

    def test_uris(self):
        d = Document({
            "id": "1",
            "title": "document",
            "link": [peerj["html"], peerj["pdf"]]
        })
        assert_equal(d.uris(), [
            "https://peerj.com/articles/53/",
            "https://peerj.com/articles/53.pdf"
        ])

    def test_merge_links(self):
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

    def test_save(self):
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
        assert d1 is None
        assert d2 is None
        assert d3 is None
        assert d4

    def test_save_merge_documents(self):
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

        # They are not merged yet
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

        # d2 is merged into d3
        d2 = Document.fetch(2)
        d3 = Document.fetch(3)
        assert d2 is None
        assert d3

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
        d4 = Document.fetch(4)
        assert d4

        d5 = Document({
            "id": "5",
            "title": "document5",
            "link": [peerj["pdf"], peerj["doc"]]
        })

        d5.save()

        # The documents have been merged into d5
        d1 = Document.fetch(1)
        d2 = Document.fetch(2)
        d3 = Document.fetch(3)
        d4 = Document.fetch(4)
        d5 = Document.fetch(5)

        assert d1 is None
        assert d2 is None
        assert d3 is None
        assert d4
        assert d5
