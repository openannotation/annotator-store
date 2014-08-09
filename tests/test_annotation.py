from nose.tools import *
from mock import MagicMock
from . import TestCase, helpers as h

from annotator import es
from annotator.annotation import Annotation

class TestAnnotation(TestCase):
    def setup(self):
        super(TestAnnotation, self).setup()

    def teardown(self):
        super(TestAnnotation, self).teardown()

    def test_new(self):
        a = Annotation()
        assert_equal('{}', repr(a))

    def test_save_refresh(self):
        a = Annotation(name='bob')
        c = a.es.conn
        a.save(refresh=True)
        assert_true('id' in a)

    def test_save_assert_refresh(self):
        a = Annotation(name='bob')
        a.es = MagicMock()
        a.es.index = 'foo'
        a.save()
        args, kwargs = a.es.conn.index.call_args
        assert_equal(kwargs['refresh'], True)

    def test_save_refresh_disable(self):
        a = Annotation(name='bob')
        a.es = MagicMock()
        a.es.index = 'foo'
        a.save(refresh=False)
        args, kwargs = a.es.conn.index.call_args
        assert_equal(kwargs['refresh'], False)

    def test_fetch(self):
        a = Annotation(foo='bar')
        a.save()
        b = Annotation.fetch(a['id'])
        assert_equal(b['foo'], 'bar')

    def test_delete(self):
        ann = Annotation(id=1)
        ann.save()

        newann = Annotation.fetch(1)
        newann.delete()

        noann = Annotation.fetch(1)
        assert_true(noann == None)

    def test_basics(self):
        user = "alice"
        ann = Annotation(text="Hello there", user=user)
        ann['ranges'] = []
        ann['ranges'].append({'startOffset': 3})
        ann['ranges'].append({'startOffset': 5})
        ann['document'] = {
            'title': 'Annotation for Dummies',
            'link': [
                {'href': 'http://example.com/1234', 'type': 'application/pdf'}
            ]
        }
        ann.save()

        ann = Annotation.fetch(ann['id'])
        assert_equal(ann['text'], "Hello there")
        assert_equal(ann['user'], "alice")
        assert_equal(len(ann['ranges']), 2)
        assert_equal(ann['document']['title'], 'Annotation for Dummies')
        assert_equal(ann['document']['link'][0]['href'], 'http://example.com/1234')
        assert_equal(ann['document']['link'][0]['type'], 'application/pdf')

    def test_search(self):
        perms = {'read': ['group:__world__']}
        uri1 = u'http://xyz.com'
        uri2 = u'urn:uuid:xxxxx'
        user1 = u'levin'
        user2 = u'anna'
        anno1 = Annotation(uri=uri1, text=uri1, user=user1, permissions=perms)
        anno2 = Annotation(uri=uri1, text=uri1 + uri1, user=user2, permissions=perms)
        anno3 = Annotation(uri=uri2, text=uri2, user=user1, permissions=perms)
        anno1.save()
        anno2.save()
        anno3.save()

        res = Annotation.search()
        assert_equal(len(res), 3)

        # ordering (most recent first)
        assert_equal(res[0]['text'], uri2)

        res = Annotation.count()
        assert_equal(res, 3)

        res = Annotation.search(limit=1)
        assert_equal(len(res), 1)
        res = Annotation.count(limit=1)
        assert_equal(res, 3)

        res = Annotation.search(query={'uri':uri1})
        assert_equal(len(res), 2)
        assert_equal(res[0]['uri'], uri1)
        assert_equal(res[0]['id'], anno2['id'])

        res = Annotation.search(query={'user':user1})
        assert_equal(len(res), 2)
        assert_equal(res[0]['user'], user1)
        assert_equal(res[0]['id'], anno3['id'])

        res = Annotation.search(query={'user':user1, 'uri':uri2})
        assert_equal(len(res), 1)
        assert_equal(res[0]['user'], user1)
        assert_equal(res[0]['id'], anno3['id'])

        res = Annotation.count(query={'user':user1, 'uri':uri2})
        assert_equal(res, 1)

    def test_search_permissions_null(self):
        anno = Annotation(text='Foobar')
        anno.save()

        res = Annotation.search()
        assert_equal(len(res), 0)

        user = h.MockUser('bob')
        res = Annotation.search(user=user)
        assert_equal(len(res), 0)

    def test_search_permissions_simple(self):
        anno = Annotation(text='Foobar',
                          consumer='testconsumer',
                          permissions={'read': ['bob']})
        anno.save()

        res = Annotation.search()
        assert_equal(len(res), 0)

        user = h.MockUser('alice', 'testconsumer')
        res = Annotation.search(user=user)
        assert_equal(len(res), 0)

        user = h.MockUser('bob')
        res = Annotation.search(user=user)
        assert_equal(len(res), 0)

        user = h.MockUser('bob', 'testconsumer')
        res = Annotation.search(user=user)
        assert_equal(len(res), 1)

    def test_search_permissions_world(self):
        anno = Annotation(text='Foobar',
                          consumer='testconsumer',
                          permissions={'read': ['group:__world__']})
        anno.save()

        res = Annotation.search()
        assert_equal(len(res), 1)

        user = h.MockUser('alice', 'testconsumer')
        res = Annotation.search(user=user)
        assert_equal(len(res), 1)

        user = h.MockUser('bob')
        res = Annotation.search(user=user)
        assert_equal(len(res), 1)

        user = h.MockUser('bob', 'testconsumer')
        res = Annotation.search(user=user)
        assert_equal(len(res), 1)

    def test_search_permissions_authenticated(self):
        anno = Annotation(text='Foobar',
                          consumer='testconsumer',
                          permissions={'read': ['group:__authenticated__']})
        anno.save()

        res = Annotation.search()
        assert_equal(len(res), 0)

        user = h.MockUser('alice', 'testconsumer')
        res = Annotation.search(user=user)
        assert_equal(len(res), 1)

        user = h.MockUser('bob', 'anotherconsumer')
        res = Annotation.search(user=user)
        assert_equal(len(res), 1)


    def test_search_permissions_consumer(self):
        anno = Annotation(text='Foobar',
                          user='alice',
                          consumer='testconsumer',
                          permissions={'read': ['group:__consumer__']})
        anno.save()

        res = Annotation.search()
        assert_equal(len(res), 0)

        user = h.MockUser('bob', 'testconsumer')
        res = Annotation.search(user=user)
        assert_equal(len(res), 1)

        user = h.MockUser('alice', 'anotherconsumer')
        res = Annotation.search(user=user)
        assert_equal(len(res), 0)

    def test_search_permissions_owner(self):
        anno = Annotation(text='Foobar',
                          user='alice',
                          consumer='testconsumer')
        anno.save()

        res = Annotation.search()
        assert_equal(len(res), 0)

        user = h.MockUser('alice', 'testconsumer')
        res = Annotation.search(user=user)
        assert_equal(len(res), 1)

    def test_search_permissions_malicious(self):
        anno = Annotation(text='Foobar',
                          user='alice',
                          consumer='testconsumer',
                          permissions={'read': ['group:__consumer__']})
        anno.save()

        # Any user whose username starts with "group:" must be refused any results
        user = h.MockUser('group:anyone', 'testconsumer')
        res = Annotation.search(user=user)
        assert_equal(len(res), 0)

    def test_search_permissions_admin(self):
        anno = Annotation(text='Foobar',
                          user='alice',
                          consumer='testconsumer')
        anno.save()

        user = h.MockUser('bob', 'testconsumer')
        user.is_admin = True

        res = Annotation.search(user=user)
        assert_equal(len(res), 1)

    def test_cross_representations(self):

        # create an annotation for an html document which we can
        # scrape some document metadata from, including a link to a pdf

        a1 = Annotation(uri='http://example.com/1234',
                        text='annotation1',
                        user='alice',
                        document = {
                            "link": [
                                {
                                    "href": "http://example.com/1234",
                                    "type": "text/html"
                                },
                                {
                                    "href": "http://example.com/1234.pdf",
                                    "type": "application/pdf"
                                }
                            ]
                        },
                        consumer='testconsumer')
        a1.save()

        # create an annotation for the pdf that lacks document metadata since
        # annotator doesn't currently extract information from pdfs

        a2 = Annotation(uri='http://example.com/1234.pdf',
                        text='annotation2',
                        user='alice',
                        consumer='testconsumer')
        a2.save()

        # now a query for annotations of the pdf should yield both annotations

        user = h.MockUser('alice', 'testconsumer')
        res = Annotation.search(user=user,
                                query={'uri':'http://example.com/1234.pdf'})
        assert_equal(len(res), 2)

        # and likewise for annotations of the html
        res = Annotation.search(user=user,
                                query={'uri':'http://example.com/1234'})
        assert_equal(len(res), 2)
