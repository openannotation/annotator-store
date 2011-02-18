from flask import json, url_for

from annotator.app import app, setup_app
from annotator.model import Annotation, Range
from annotator.model import create_all, drop_all, session

def setup():
    setup_app()

class TestStore():
    def setup(self):
        app.config['AUTH_ON'] = False
        self.app = app.test_client()
        create_all()

    def teardown(self):
        session.remove()
        drop_all()

    def _create_annotation(self, **kwargs):
        ann = Annotation(**kwargs)
        session.commit()
        return ann

    def _get_annotation(self, id_):
        return Annotation.get(id_)

    def test_index(self):
        assert self.app.get('/annotations').data == "[]", "response should be empty list"

    def test_create(self):
        import re
        payload = json.dumps({'name': 'Foo'})
        response = self.app.post('/annotations', data=payload, content_type='application/json')

        # See http://bit.ly/gxJBHo for details of this change.
        # assert response.status_code == 303, "response should be 303 SEE OTHER"
        # assert re.match(r"http://localhost/store/\d+", response.headers['Location']), "response should redirect to read_annotation url"

        assert response.status_code == 200, "response should be 200 OK"
        data = json.loads(response.data)
        assert 'id' in data, "annotation id should be returned in response"

    def test_read(self):
        kwargs = dict(text=u"Foo", id=123)
        self._create_annotation(**kwargs)
        response = self.app.get('/annotations/123')
        data = json.loads(response.data)
        assert data['id'] == 123, "annotation id should be returned in response"
        assert data['text'] == "Foo", "annotation text should be returned in response"

    def test_read_notfound(self):
        response = self.app.get('/annotations/123')
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_update(self):
        kwargs = dict(text=u"Foo", id=123)
        self._create_annotation(**kwargs)

        payload = json.dumps({'id': 123, 'text': 'Bar'})
        response = self.app.put('/annotations/123', data=payload, content_type='application/json')

        ann = self._get_annotation(123)
        assert ann.text == "Bar", "annotation wasn't updated in db"

        data = json.loads(response.data)
        assert data['text'] == "Bar", "update annotation should be returned in response"

    def test_update_notfound(self):
        response = self.app.put('/annotations/123')
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_delete(self):
        kwargs = dict(text=u"Bar", id=456)
        ann = self._create_annotation(**kwargs)

        response = self.app.delete('/annotations/456')
        assert response.status_code == 204, "response should be 204 NO CONTENT"

        assert self._get_annotation(456) == None, "annotation wasn't deleted in db"

    def test_delete_notfound(self):
        response = self.app.delete('/annotations/123')
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_search(self):
        uri1 = u'http://xyz.com'
        uri2 = u'urn:uuid:xxxxx'
        user = u'levin'
        user2 = u'anna'
        anno = self._create_annotation(**dict(
                uri=uri1,
                text=uri1,
                user=user,
                ))
        anno2 = self._create_annotation(**dict(
                uri=uri1,
                text=uri1 + uri1,
                user=user2,
                ))
        anno3 = self._create_annotation(**dict(
                uri=uri2,
                text=uri2,
                user=user
                ))
        annoid = anno.id
        anno2id = anno2.id

        url = '/search'
        res = self.app.get(url)
        body = json.loads(res.data)
        assert body['total'] == 3, body

        url = '/search?limit=1'
        res = self.app.get(url)
        body = json.loads(res.data)
        assert body['total'] == 3, body
        assert len(body['rows']) == 1

        url = '/search?uri=' + uri1 + '&all_fields=1'
        res = self.app.get(url)
        body = json.loads(res.data)
        assert body['total'] == 2, body
        out = body['rows']
        assert len(out) == 2
        assert out[0]['uri'] == uri1
        assert out[0]['id'] in [ annoid, anno2id ]

        url = '/search?uri=' + uri1
        res = self.app.get(url)
        body = json.loads(res.data)
        assert body['rows'][0].keys() == ['id'], body['rows']

        url = '/search?limit=-1'
        res = self.app.get(url)
        body = json.loads(res.data)
        assert len(body['rows']) == 3, body

    def test_cors_preflight(self):
        response = self.app.open('/annotations', method="OPTIONS")

        headers = dict(response.headers)

        assert headers['Access-Control-Allow-Methods'] == 'GET, POST, PUT, DELETE', \
            "Did not send the right Access-Control-Allow-Methods header."

        assert headers['Access-Control-Allow-Origin'] == '*', \
            "Did not send the right Access-Control-Allow-Origin header."

        assert headers['Access-Control-Expose-Headers'] == 'Location', \
                "Did not send the right Access-Control-Expose-Headers header."

class TestStoreAuth():
    def setup(self):
        app.config['AUTH_ON'] = True
        self.app = app.test_client()
        create_all()

    def teardown(self):
        session.remove()
        drop_all()

    def test_reject_bare_request(self):
        response = self.app.get('/annotations')
        assert response.status_code == 401, "response should be 401 NOT AUTHORIZED"
