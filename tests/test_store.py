from . import TestCase
from .helpers import MockUser, MockConsumer
from nose.tools import *

from flask import json, url_for

from annotator import auth, es
from annotator.annotation import Annotation

class TestStore(TestCase):
    def setup(self):
        super(TestStore, self).setup()

        self.consumer = MockConsumer()
        self.user = MockUser()

        token = auth.generate_token(self.consumer, self.user.username)
        self.headers = auth.headers_for_token(token)

        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def teardown(self):
        self.ctx.pop()
        super(TestStore, self).teardown()

    def _create_annotation(self, **kwargs):
        opts = {
            'user': self.user.username,
            'consumer': self.consumer.key
        }
        opts.update(kwargs)
        ann = Annotation(**opts)
        ann.save()
        return ann

    def _get_annotation(self, id_):
        return Annotation.fetch(id_)

    def test_cors_preflight(self):
        response = self.cli.open('/api/annotations', method="OPTIONS")

        headers = dict(response.headers)

        assert headers['Access-Control-Allow-Methods'] == 'GET, POST, PUT, DELETE, OPTIONS', \
            "Did not send the right Access-Control-Allow-Methods header."

        assert headers['Access-Control-Allow-Origin'] == '*', \
            "Did not send the right Access-Control-Allow-Origin header."

        assert headers['Access-Control-Expose-Headers'] == 'Location', \
            "Did not send the right Access-Control-Expose-Headers header."

    def test_index(self):
        response = self.cli.get('/api/annotations', headers=self.headers)
        assert response.data == "[]", "response should be empty list"

    def test_create(self):
        payload = json.dumps({'name': 'Foo'})
        response = self.cli.post('/api/annotations',
                                 data=payload,
                                 content_type='application/json',
                                 headers=self.headers)

        # import re
        # See http://bit.ly/gxJBHo for details of this change.
        # assert response.status_code == 303, "response should be 303 SEE OTHER"
        # assert re.match(r"http://localhost/store/\d+", response.headers['Location']), "response should redirect to read_annotation url"

        assert response.status_code == 200, "response should be 200 OK"
        data = json.loads(response.data)
        assert 'id' in data, "annotation id should be returned in response"
        assert data['user'] == self.user.username
        assert data['consumer'] == self.consumer.key

    def test_create_ignore_created(self):
        payload = json.dumps({'created': 'abc'})

        response = self.cli.post('/api/annotations',
                                 data=payload,
                                 content_type='application/json',
                                 headers=self.headers)

        data = json.loads(response.data)
        ann = self._get_annotation(data['id'])

        assert ann['created'] != 'abc', "annotation 'created' field should not be used by API"

    def test_create_ignore_updated(self):
        payload = json.dumps({'updated': 'abc'})

        response = self.cli.post('/api/annotations',
                                 data=payload,
                                 content_type='application/json',
                                 headers=self.headers)

        data = json.loads(response.data)
        ann = self._get_annotation(data['id'])

        assert ann['updated'] != 'abc', "annotation 'updated' field should not be used by API"

    def test_create_ignore_auth_in_payload(self):
        payload = json.dumps({'user': 'jenny', 'consumer': 'myconsumer'})

        response = self.cli.post('/api/annotations',
                                 data=payload,
                                 content_type='application/json',
                                 headers=self.headers)

        data = json.loads(response.data)
        ann = self._get_annotation(data['id'])

        assert ann['user'] == self.user.username, "annotation 'user' field should not be futzable by API"
        assert ann['consumer'] == self.consumer.key, "annotation 'consumer' field should not be used by API"

    def test_read(self):
        kwargs = dict(text=u"Foo", id='123')
        self._create_annotation(**kwargs)
        response = self.cli.get('/api/annotations/123', headers=self.headers)
        data = json.loads(response.data)
        assert data['id'] == '123', "annotation id should be returned in response"
        assert data['text'] == "Foo", "annotation text should be returned in response"

    def test_read_notfound(self):
        response = self.cli.get('/api/annotations/123', headers=self.headers)
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_update(self):
        self._create_annotation(text=u"Foo", id='123', created='2010-12-10')

        payload = json.dumps({'id': '123', 'text': 'Bar'})
        response = self.cli.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.headers)

        ann = self._get_annotation('123')
        assert ann['text'] == "Bar", "annotation wasn't updated in db"

        data = json.loads(response.data)
        assert data['text'] == "Bar", "update annotation should be returned in response"

    def test_update_without_payload_id(self):
        self._create_annotation(text=u"Foo", id='123')

        payload = json.dumps({'text': 'Bar'})
        response = self.cli.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.headers)

        ann = self._get_annotation('123')
        assert ann['text'] == "Bar", "annotation wasn't updated in db"

    def test_update_with_wrong_payload_id(self):
        self._create_annotation(text=u"Foo", id='123')

        payload = json.dumps({'text': 'Bar', 'id': 'abc'})
        response = self.cli.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.headers)

        ann = self._get_annotation('123')
        assert ann['text'] == "Bar", "annotation wasn't updated in db"

    def test_update_notfound(self):
        response = self.cli.put('/api/annotations/123', headers=self.headers)
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_update_ignore_created(self):
        ann = self._create_annotation(text=u"Foo", id='123')

        payload = json.dumps({'created': 'abc'})

        response = self.cli.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.headers)

        upd = self._get_annotation('123')

        assert upd['created'] == ann['created'], "annotation 'created' field should not be updated by API"

    def test_update_ignore_updated(self):
        ann = self._create_annotation(text=u"Foo", id='123')

        payload = json.dumps({'updated': 'abc'})

        response = self.cli.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.headers)

        upd = self._get_annotation('123')

        assert upd['created'] != 'abc', "annotation 'updated' field should not be updated by API"

    def test_update_ignore_auth_in_payload(self):
        ann = self._create_annotation(text=u"Foo", id='123')

        payload = json.dumps({'user': 'jenny', 'consumer': 'myconsumer'})

        response = self.cli.put('/api/annotations/123',
                                 data=payload,
                                 content_type='application/json',
                                 headers=self.headers)

        upd = self._get_annotation('123')

        assert_equal(upd['user'], self.user.username, "annotation 'user' field should not be futzable by API")
        assert_equal(upd['consumer'], self.consumer.key, "annotation 'consumer' field should not be futzable by API")


    def test_delete(self):
        kwargs = dict(text=u"Bar", id='456')
        ann = self._create_annotation(**kwargs)

        response = self.cli.delete('/api/annotations/456', headers=self.headers)
        assert response.status_code == 204, "response should be 204 NO CONTENT"

        assert self._get_annotation('456') == None, "annotation wasn't deleted in db"

    def test_delete_notfound(self):
        response = self.cli.delete('/api/annotations/123', headers=self.headers)
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_search(self):
        uri1 = u'http://xyz.com'
        uri2 = u'urn:uuid:xxxxx'
        user = u'levin'
        user2 = u'anna'
        anno = self._create_annotation(uri=uri1, text=uri1, user=user)
        anno2 = self._create_annotation(uri=uri1, text=uri1 + uri1, user=user2)
        anno3 = self._create_annotation(uri=uri2, text=uri2, user=user)

        es.conn.refresh(timesleep=0.01)

        res = self._get_search_results()
        assert_equal(res['total'], 3)

        res = self._get_search_results('limit=1')
        assert_equal(res['total'], 3)
        assert_equal(len(res['rows']), 1)

        res = self._get_search_results('uri=' + uri1)
        assert_equal(res['total'], 2)
        assert_equal(len(res['rows']), 2)
        assert_equal(res['rows'][0]['uri'], uri1)
        assert_in(res['rows'][0]['id'], [anno.id, anno2.id])

    def test_search_limit(self):
        for i in xrange(250):
            self._create_annotation()

        es.conn.refresh(timesleep=0.01)

        # by default return 20
        res = self._get_search_results()
        assert_equal(len(res['rows']), 20)

        # return maximum 200
        res = self._get_search_results('limit=250')
        assert_equal(len(res['rows']), 200)

        # return minimum 0
        res = self._get_search_results('limit=-10')
        assert_equal(len(res['rows']), 0)

        # ignore bogus values
        res = self._get_search_results('limit=foobar')
        assert_equal(len(res['rows']), 20)

    def test_search_offset(self):
        for i in xrange(250):
            self._create_annotation()

        es.conn.refresh(timesleep=0.01)

        res = self._get_search_results()
        assert_equal(len(res['rows']), 20)
        first = res['rows'][0]

        res = self._get_search_results('offset=240')
        assert_equal(len(res['rows']), 10)

        # ignore negative values
        res = self._get_search_results('offset=-10')
        assert_equal(len(res['rows']), 20)
        assert_equal(res['rows'][0], first)

        # ignore bogus values
        res = self._get_search_results('offset=foobar')
        assert_equal(len(res['rows']), 20)
        assert_equal(res['rows'][0], first)

    def _get_search_results(self, qs=''):
        res = self.cli.get('/api/search?{qs}'.format(qs=qs), headers=self.headers)
        return json.loads(res.data)


class TestStoreAuthz(TestCase):

    def setup(self):
        super(TestStoreAuthz, self).setup()

        self.consumer = MockConsumer()
        self.user = MockUser() # alice

        self.anno_id = '123'
        self.permissions = {
            'read': [self.user.username, 'bob'],
            'update': [self.user.username, 'charlie'],
            'admin': [self.user.username]
        }

        self.ctx = self.app.test_request_context()
        self.ctx.push()

        ann = Annotation(id=self.anno_id,
                         user=self.user.username,
                         consumer=self.consumer.key,
                         text='Foobar',
                         permissions=self.permissions)
        ann.save()

        for u in ['alice', 'bob', 'charlie']:
            token = auth.generate_token(self.consumer, u)
            setattr(self, '%s_headers' % u, auth.headers_for_token(token))

    def teardown(self):
        self.ctx.pop()
        super(TestStoreAuthz, self).teardown()

    def test_read(self):
        response = self.cli.get('/api/annotations/123')
        assert response.status_code == 401, "response should be 401 NOT AUTHORIZED"

        response = self.cli.get('/api/annotations/123', headers=self.charlie_headers)
        assert response.status_code == 401, "response should be 401 NOT AUTHORIZED"

        response = self.cli.get('/api/annotations/123', headers=self.alice_headers)
        assert response.status_code == 200, "response should be 200 OK"
        data = json.loads(response.data)
        assert data['text'] == 'Foobar'

    def test_update(self):
        payload = json.dumps({'id': self.anno_id, 'text': 'Bar'})

        response = self.cli.put('/api/annotations/123', data=payload, content_type='application/json')
        assert response.status_code == 401, "response should be 401 NOT AUTHORIZED"

        response = self.cli.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.bob_headers)
        assert response.status_code == 401, "response should be 401 NOT AUTHORIZED"

        response = self.cli.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.charlie_headers)
        assert response.status_code == 200, "response should be 200 OK"

    def test_update_change_permissions_not_allowed(self):
        self.permissions['read'] = ['alice', 'charlie']
        payload = json.dumps({
            'id': self.anno_id,
            'text': 'Bar',
            'permissions': self.permissions
        })

        response = self.cli.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json')
        assert response.status_code == 401, "response should be 401 NOT AUTHORIZED"

        response = self.cli.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.charlie_headers)
        assert response.status_code == 401, "response should be 401 NOT AUTHORIZED"
        assert 'permissions update' in response.data

        response = self.cli.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.alice_headers)
        assert response.status_code == 200, "response should be 200 OK"

    def test_update_other_users_annotation(self):
        ann = Annotation(id=123,
                         user='foo',
                         consumer=self.consumer.key,
                         permissions={'update': ['group:__consumer__']})
        ann.save()

        payload = json.dumps({
            'id': 123,
            'text': 'Foo'
        })

        response = self.cli.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.bob_headers)
        assert response.status_code == 200, "response should be 200 OK"

