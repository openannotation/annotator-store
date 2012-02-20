from nose.tools import *
import pyes

from annotator.annotation import make_model

conn = None
Annotation = None

def setup():
    global conn, Annotation
    conn = pyes.ES('127.0.0.1:9200')
    Annotation = make_model(conn)
    conn.delete_index_if_exists(Annotation.index)

class TestAnnotation(object):
    def setup(self):
        Annotation.create_all()

    def teardown(self):
        Annotation.drop_all()

    def test_new(self):
        a = Annotation()
        assert_equal('{}', repr(a))

    def test_save(self):
        a = Annotation(name='bob')
        a.save()
        assert_in('id', a)

    def test_fetch(self):
        a = Annotation(foo='bar')
        a.save()
        b = Annotation.fetch(a.id)
        assert_equal(b['foo'], 'bar')

    def test_delete(self):
        ann = Annotation(id=1)
        ann.save()

        newann = Annotation.fetch(1)
        newann.delete()

        noann = Annotation.fetch(1)
        assert noann == None

    def test_basics(self):
        user = "alice"
        ann = Annotation(text="Hello there", user=user)
        ann['ranges'] = []
        ann['ranges'].append({})
        ann['ranges'].append({})
        ann.save()

        ann = Annotation.fetch(ann.id)
        assert_equal(ann['text'], "Hello there")
        assert_equal(ann['user'], "alice")
        assert_equal(len(ann['ranges']), 2)

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

        conn.refresh(timesleep=0.01)

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

        res = Annotation.search(uri=uri1)
        assert_equal(len(res), 2)
        assert_equal(res[0]['uri'], uri1)
        assert_equal(res[0]['id'], anno2.id)

        res = Annotation.search(user=user1)
        assert_equal(len(res), 2)
        assert_equal(res[0]['user'], user1)
        assert_equal(res[0]['id'], anno3.id)

        res = Annotation.search(user=user1, uri=uri2)
        assert_equal(len(res), 1)
        assert_equal(res[0]['user'], user1)
        assert_equal(res[0]['id'], anno3.id)

        res = Annotation.count(user=user1, uri=uri2)
        assert_equal(res, 1)

    def test_search_permissions_null(self):
        anno = Annotation(text='Foobar')
        anno.save()

        conn.refresh(timesleep=0.01)

        res = Annotation.search()
        assert_equal(len(res), 0)

        res = Annotation.search(_user_id='bob')
        assert_equal(len(res), 0)

    def test_search_permissions_simple(self):
        anno = Annotation(text='Foobar',
                          consumer='testconsumer',
                          permissions={'read': ['bob']})
        anno.save()

        conn.refresh(timesleep=0.01)

        res = Annotation.search()
        assert_equal(len(res), 0)

        res = Annotation.search(_user_id='alice', _consumer_key='testconsumer')
        assert_equal(len(res), 0)

        res = Annotation.search(_user_id='bob')
        assert_equal(len(res), 0)

        res = Annotation.search(_user_id='bob', _consumer_key='testconsumer')
        assert_equal(len(res), 1)

    def test_search_permissions_world(self):
        anno = Annotation(text='Foobar',
                          consumer='testconsumer',
                          permissions={'read': ['group:__world__']})
        anno.save()

        conn.refresh(timesleep=0.01)

        res = Annotation.search()
        assert_equal(len(res), 1)

        res = Annotation.search(_user_id='alice', _consumer_key='testconsumer')
        assert_equal(len(res), 1)

        res = Annotation.search(_user_id='bob')
        assert_equal(len(res), 1)

        res = Annotation.search(_user_id='bob', _consumer_key='testconsumer')
        assert_equal(len(res), 1)

    def test_search_permissions_authenticated(self):
        anno = Annotation(text='Foobar',
                          consumer='testconsumer',
                          permissions={'read': ['group:__authenticated__']})
        anno.save()

        conn.refresh(timesleep=0.01)

        res = Annotation.search()
        assert_equal(len(res), 0)

        res = Annotation.search(_user_id='alice', _consumer_key='testconsumer')
        assert_equal(len(res), 1)

        res = Annotation.search(_user_id='bob', _consumer_key='anotherconsumer')
        assert_equal(len(res), 1)


    def test_search_permissions_consumer(self):
        anno = Annotation(text='Foobar',
                          user='alice',
                          consumer='testconsumer',
                          permissions={'read': ['group:__consumer__']})
        anno.save()

        conn.refresh(timesleep=0.01)

        res = Annotation.search()
        assert_equal(len(res), 0)

        res = Annotation.search(_user_id='bob', _consumer_key='testconsumer')
        assert_equal(len(res), 1)

        res = Annotation.search(_user_id='bob', _consumer_key='anotherconsumer')
        assert_equal(len(res), 0)

    def test_search_permissions_owner(self):
        anno = Annotation(text='Foobar',
                          user='alice',
                          consumer='testconsumer')
        anno.save()

        conn.refresh(timesleep=0.01)

        res = Annotation.search()
        assert_equal(len(res), 0)

        res = Annotation.search(_user_id='alice', _consumer_key='testconsumer')
        assert_equal(len(res), 1)
