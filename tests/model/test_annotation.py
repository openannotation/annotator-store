from .. import TestCase, helpers as h

import annotator
from annotator.model import Annotation

class TestAnnotation(TestCase):

    def test_new(self):
        a = Annotation()
        h.assert_equal('{}', repr(a))

    def test_save(self):
        a = Annotation(name='bob')
        a.save()
        h.assert_in('id', a)

    def test_fetch(self):
        a = Annotation(foo='bar')
        a.save()
        b = Annotation.fetch(a.id)
        h.assert_equal(b['foo'], 'bar')

    def test_delete(self):
        id_ = 1
        ann = Annotation(id=id_)
        ann.save()

        newann = Annotation.fetch(id_)
        newann.delete()

        noann = Annotation.fetch(id_)
        assert noann == None

    def test_basics(self):
        user = "alice"
        ann = Annotation(text="Hello there", user=user)
        ann['ranges'] = []
        ann['ranges'].append({})
        ann['ranges'].append({})
        ann.save()

        ann = Annotation.fetch(ann.id)
        h.assert_equal(ann['text'], "Hello there")
        h.assert_equal(ann['user'], "alice")
        h.assert_equal(len(ann['ranges']), 2)

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

        self.es.refresh(timesleep=0.01)

        res = Annotation.search()
        h.assert_equal(len(res), 3)

        # ordering (most recent first)
        h.assert_equal(res[0]['text'], uri2)

        res = Annotation.count()
        h.assert_equal(res, 3)

        res = Annotation.search(limit=1)
        h.assert_equal(len(res), 1)
        res = Annotation.count(limit=1)
        h.assert_equal(res, 3)

        res = Annotation.search(uri=uri1)
        h.assert_equal(len(res), 2)
        h.assert_equal(res[0]['uri'], uri1)
        h.assert_equal(res[0]['id'], anno2.id)

        res = Annotation.search(user=user1)
        h.assert_equal(len(res), 2)
        h.assert_equal(res[0]['user'], user1)
        h.assert_equal(res[0]['id'], anno3.id)

        res = Annotation.search(user=user1, uri=uri2)
        h.assert_equal(len(res), 1)
        h.assert_equal(res[0]['user'], user1)
        h.assert_equal(res[0]['id'], anno3.id)

        res = Annotation.count(user=user1, uri=uri2)
        h.assert_equal(res, 1)

    def test_search_permissions_null(self):
        anno = Annotation(text='Foobar')
        anno.save()

        self.es.refresh(timesleep=0.01)

        res = Annotation.search()
        h.assert_equal(len(res), 0)

        res = Annotation.search(_user_id='bob')
        h.assert_equal(len(res), 0)

    def test_search_permissions_simple(self):
        anno = Annotation(text='Foobar',
                          consumer='testconsumer',
                          permissions={'read': ['bob']})
        anno.save()

        self.es.refresh(timesleep=0.01)

        res = Annotation.search()
        h.assert_equal(len(res), 0)

        res = Annotation.search(_user_id='alice', _consumer_key='testconsumer')
        h.assert_equal(len(res), 0)

        res = Annotation.search(_user_id='bob')
        h.assert_equal(len(res), 0)

        res = Annotation.search(_user_id='bob', _consumer_key='testconsumer')
        h.assert_equal(len(res), 1)

    def test_search_permissions_world(self):
        anno = Annotation(text='Foobar',
                          consumer='testconsumer',
                          permissions={'read': ['group:__world__']})
        anno.save()

        self.es.refresh(timesleep=0.01)

        res = Annotation.search()
        h.assert_equal(len(res), 1)

        res = Annotation.search(_user_id='alice', _consumer_key='testconsumer')
        h.assert_equal(len(res), 1)

        res = Annotation.search(_user_id='bob')
        h.assert_equal(len(res), 1)

        res = Annotation.search(_user_id='bob', _consumer_key='testconsumer')
        h.assert_equal(len(res), 1)

    def test_search_permissions_authenticated(self):
        anno = Annotation(text='Foobar',
                          consumer='testconsumer',
                          permissions={'read': ['group:__authenticated__']})
        anno.save()

        self.es.refresh(timesleep=0.01)

        res = Annotation.search()
        h.assert_equal(len(res), 0)

        res = Annotation.search(_user_id='alice', _consumer_key='testconsumer')
        h.assert_equal(len(res), 1)

        res = Annotation.search(_user_id='bob', _consumer_key='anotherconsumer')
        h.assert_equal(len(res), 1)


    def test_search_permissions_consumer(self):
        anno = Annotation(text='Foobar',
                          user='alice',
                          consumer='testconsumer',
                          permissions={'read': ['group:__consumer__']})
        anno.save()

        self.es.refresh(timesleep=0.01)

        res = Annotation.search()
        h.assert_equal(len(res), 0)

        res = Annotation.search(_user_id='bob', _consumer_key='testconsumer')
        h.assert_equal(len(res), 1)

        res = Annotation.search(_user_id='bob', _consumer_key='anotherconsumer')
        h.assert_equal(len(res), 0)

    def test_search_permissions_owner(self):
        anno = Annotation(text='Foobar',
                          user='alice',
                          consumer='testconsumer')
        anno.save()

        self.es.refresh(timesleep=0.01)

        res = Annotation.search()
        h.assert_equal(len(res), 0)

        res = Annotation.search(_user_id='alice', _consumer_key='testconsumer')
        h.assert_equal(len(res), 1)
