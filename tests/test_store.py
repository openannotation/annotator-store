from . import TestCase

from flask import json, url_for

import annotator
from annotator import auth, db
from annotator.model import Annotation, Consumer

def save(x):
    annotator.db.session.add(x)
    annotator.db.session.commit()

class TestStore(TestCase):
    def setup(self):
        super(TestStore, self).setup()

        self.app = annotator.app.test_client()
        self.consumer = Consumer('test-consumer-key')
        save(self.consumer)

        self.user = 'test-user'

        token = auth.generate_token(self.consumer.key, self.user)
        self.headers = auth.headers_for_token(token)


    def _create_annotation(self, **kwargs):
        ann = Annotation(**kwargs)
        ann.save()
        return ann

    def _get_annotation(self, id_):
        return Annotation.fetch(id_)

    def test_index(self):
        response = self.app.get('/api/annotations', headers=self.headers)
        assert response.data == "[]", "response should be empty list"

    def test_create(self):
        payload = json.dumps({'name': 'Foo'})
        response = self.app.post('/api/annotations',
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
        assert data['user'] == self.user
        assert data['consumer'] == self.consumer.key

    def test_create_ignore_created(self):
        payload = json.dumps({'created': 'abc'})

        response = self.app.post('/api/annotations',
                                 data=payload,
                                 content_type='application/json',
                                 headers=self.headers)

        data = json.loads(response.data)
        ann = self._get_annotation(data['id'])

        assert ann['created'] != 'abc', "annotation 'created' field should not be used by API"

    def test_create_ignore_updated(self):
        payload = json.dumps({'updated': 'abc'})

        response = self.app.post('/api/annotations',
                                 data=payload,
                                 content_type='application/json',
                                 headers=self.headers)

        data = json.loads(response.data)
        ann = self._get_annotation(data['id'])

        assert ann['updated'] != 'abc', "annotation 'updated' field should not be used by API"

    def test_read(self):
        kwargs = dict(text=u"Foo", id='123')
        self._create_annotation(**kwargs)
        response = self.app.get('/api/annotations/123', headers=self.headers)
        data = json.loads(response.data)
        assert data['id'] == '123', "annotation id should be returned in response"
        assert data['text'] == "Foo", "annotation text should be returned in response"

    def test_read_notfound(self):
        response = self.app.get('/api/annotations/123', headers=self.headers)
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_update(self):
        self._create_annotation(text=u"Foo", id='123', created='2010-12-10')

        payload = json.dumps({'id': '123', 'text': 'Bar'})
        response = self.app.put('/api/annotations/123',
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
        response = self.app.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.headers)

        ann = self._get_annotation('123')
        assert ann['text'] == "Bar", "annotation wasn't updated in db"

    def test_update_with_wrong_payload_id(self):
        self._create_annotation(text=u"Foo", id='123')

        payload = json.dumps({'text': 'Bar', 'id': 'abc'})
        response = self.app.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.headers)

        ann = self._get_annotation('123')
        assert ann['text'] == "Bar", "annotation wasn't updated in db"

    def test_update_notfound(self):
        response = self.app.put('/api/annotations/123', headers=self.headers)
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_update_ignore_created(self):
        ann = self._create_annotation(text=u"Foo", id='123')

        payload = json.dumps({'created': 'abc'})

        response = self.app.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.headers)

        upd = self._get_annotation('123')

        assert upd['created'] == ann['created'], "annotation 'created' field should not be updated by API"

    def test_update_ignore_updated(self):
        ann = self._create_annotation(text=u"Foo", id='123')

        payload = json.dumps({'updated': 'abc'})

        response = self.app.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.headers)

        upd = self._get_annotation('123')

        assert upd['created'] != 'abc', "annotation 'updated' field should not be updated by API"


    def test_delete(self):
        kwargs = dict(text=u"Bar", id='456')
        ann = self._create_annotation(**kwargs)

        response = self.app.delete('/api/annotations/456', headers=self.headers)
        assert response.status_code == 204, "response should be 204 NO CONTENT"

        assert self._get_annotation('456') == None, "annotation wasn't deleted in db"

    def test_delete_notfound(self):
        response = self.app.delete('/api/annotations/123', headers=self.headers)
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_search(self):
        uri1 = u'http://xyz.com'
        uri2 = u'urn:uuid:xxxxx'
        user = u'levin'
        user2 = u'anna'
        anno = self._create_annotation(uri=uri1, text=uri1, user=user)
        anno2 = self._create_annotation(uri=uri1, text=uri1 + uri1, user=user2)
        anno3 = self._create_annotation(uri=uri2, text=uri2, user=user)
        annoid = anno.id
        anno2id = anno2.id

        annotator.es.refresh()

        url = '/api/search'
        res = self.app.get(url, headers=self.headers)
        body = json.loads(res.data)
        assert body['total'] == 3, body

        url = '/api/search?limit=1'
        res = self.app.get(url, headers=self.headers)
        body = json.loads(res.data)
        assert body['total'] == 3, body
        assert len(body['rows']) == 1

        url = '/api/search?uri=' + uri1
        res = self.app.get(url, headers=self.headers)
        body = json.loads(res.data)
        assert body['total'] == 2, body
        out = body['rows']
        assert len(out) == 2
        assert out[0]['uri'] == uri1
        assert out[0]['id'] in [ annoid, anno2id ]

        url = '/api/search'
        res = self.app.get(url, headers=self.headers)
        body = json.loads(res.data)
        assert len(body['rows']) == 3, body

    def test_cors_preflight(self):
        response = self.app.open('/api/annotations', method="OPTIONS")

        headers = dict(response.headers)

        assert headers['Access-Control-Allow-Methods'] == 'GET, POST, PUT, DELETE, OPTIONS', \
            "Did not send the right Access-Control-Allow-Methods header."

        assert headers['Access-Control-Allow-Origin'] == '*', \
            "Did not send the right Access-Control-Allow-Origin header."

        assert headers['Access-Control-Expose-Headers'] == 'Location', \
            "Did not send the right Access-Control-Expose-Headers header."

class TestStoreAuthz(TestCase):

    def setup(self):
        super(TestStoreAuthz, self).setup()
        self.app = annotator.app.test_client()

        self.anno_id = '123'
        self.permissions = {
            'read': ['alice', 'bob'],
            'update': ['alice', 'charlie'],
            'admin': ['alice']
        }

        ann = Annotation(id=self.anno_id,
                         user='alice',
                         text='Foobar',
                         permissions=self.permissions)
        ann.save()

        self.consumer = Consumer('test-consumer-key')
        save(self.consumer)

        self.user = 'test-user'

        for u in ['alice', 'bob', 'charlie']:
            token = auth.generate_token(self.consumer.key, u)
            setattr(self, '%s_headers' % u, auth.headers_for_token(token))

    def test_read(self):
        response = self.app.get('/api/annotations/123')
        assert response.status_code == 401, "response should be 401 NOT AUTHORIZED"

        response = self.app.get('/api/annotations/123', headers=self.charlie_headers)
        assert response.status_code == 401, "response should be 401 NOT AUTHORIZED"

        response = self.app.get('/api/annotations/123', headers=self.alice_headers)
        assert response.status_code == 200, "response should be 200 OK"
        data = json.loads(response.data)
        assert data['text'] == 'Foobar'

    def test_update(self):
        payload = json.dumps({'id': self.anno_id, 'text': 'Bar'})

        response = self.app.put('/api/annotations/123', data=payload, content_type='application/json')
        assert response.status_code == 401, "response should be 401 NOT AUTHORIZED"

        response = self.app.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.bob_headers)
        assert response.status_code == 401, "response should be 401 NOT AUTHORIZED"

        response = self.app.put('/api/annotations/123',
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

        response = self.app.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json')
        assert response.status_code == 401, "response should be 401 NOT AUTHORIZED"

        response = self.app.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.charlie_headers)
        assert response.status_code == 401, "response should be 401 NOT AUTHORIZED"
        assert '(permissions change)' in response.data

        response = self.app.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.alice_headers)
        assert response.status_code == 200, "response should be 200 OK"

    def test_update_other_users_annotation(self):
        ann = Annotation(id=123,
                         user='foo',
                         permissions={'update': []})
        ann.save()

        payload = json.dumps({
            'id': 123,
            'text': 'Foo'
        })

        response = self.app.put('/api/annotations/123',
                                data=payload,
                                content_type='application/json',
                                headers=self.bob_headers)
        assert response.status_code == 200, "response should be 200 OK"

