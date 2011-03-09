from flask import json, url_for

from annotator.app import app, setup_app
from annotator.model import Annotation
from annotator.model.couch import rebuild_db, Metadata

def setup():
    setup_app()

class TestStore():
    def setup(self):
        app.config['AUTH_ON'] = False
        assert app.config['MOUNTPOINT'] == '', "MOUNTPOINT config option is incorrect for tests. should be ''"
        self.app = app.test_client()
        self.account_id = 'testing-user'
        self.headers = {'x-annotator-account-id': self.account_id}

    def teardown(self):
        rebuild_db(app.config['COUCHDB_DATABASE'])

    def _create_annotation(self, **kwargs):
        ann = Annotation(**kwargs)
        ann.save()
        return ann

    def _get_annotation(self, id_):
        return Annotation.get(id_)

    def test_index(self):
        assert self.app.get('/annotations').data == "[]", "response should be empty list"

    def test_create(self):
        payload = json.dumps({'name': 'Foo'})
        response = self.app.post(
            '/annotations',
            data=payload,
            content_type='application/json',
            headers=self.headers
            )

        # import re
        # See http://bit.ly/gxJBHo for details of this change.
        # assert response.status_code == 303, "response should be 303 SEE OTHER"
        # assert re.match(r"http://localhost/store/\d+", response.headers['Location']), "response should redirect to read_annotation url"

        assert response.status_code == 200, "response should be 200 OK"
        data = json.loads(response.data)
        assert 'id' in data, "annotation id should be returned in response"
        assert data['account_id'] == self.account_id

    def test_read(self):
        kwargs = dict(text=u"Foo", id='123')
        self._create_annotation(**kwargs)
        response = self.app.get('/annotations/123')
        data = json.loads(response.data)
        assert data['id'] == '123', "annotation id should be returned in response"
        assert data['text'] == "Foo", "annotation text should be returned in response"

    def test_read_notfound(self):
        response = self.app.get('/annotations/123')
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_update(self):
        kwargs = dict(text=u"Foo", id='123')
        self._create_annotation(**kwargs)

        payload = json.dumps({'id': '123', 'text': 'Bar'})
        response = self.app.put('/annotations/123', data=payload, content_type='application/json')

        ann = self._get_annotation('123')
        assert ann.text == "Bar", "annotation wasn't updated in db"

        data = json.loads(response.data)
        assert data['text'] == "Bar", "update annotation should be returned in response"

    def test_update_notfound(self):
        response = self.app.put('/annotations/123')
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_delete(self):
        kwargs = dict(text=u"Bar", id='456')
        ann = self._create_annotation(**kwargs)

        response = self.app.delete('/annotations/456')
        assert response.status_code == 204, "response should be 204 NO CONTENT"

        assert self._get_annotation('456') == None, "annotation wasn't deleted in db"

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
        assert body['total'] == 1, body
        assert len(body['rows']) == 1

        url = '/search?uri=' + uri1
        res = self.app.get(url)
        body = json.loads(res.data)
        assert body['total'] == 2, body
        out = body['rows']
        assert len(out) == 2
        assert out[0]['uri'] == uri1
        assert out[0]['id'] in [ annoid, anno2id ]

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

    def teardown(self):
        app.config['AUTH_ON'] = False

    def test_get_allowed(self):
        response = self.app.get('/annotations')
        assert response.status_code == 200, "GET should be allowed"

    def test_reject_post_request(self):
        payload = json.dumps({'name': 'Foo'})
        response = self.app.post('/annotations', data=payload,
                content_type='application/json')
        assert response.status_code == 401, "response should be 401 NOT AUTHORIZED"


class TestStoreAuthz:
    anno_id = '123'
    gooduser = u'alice'
    baduser = u'bob'
    updateuser = u'charlie'
    headers = { 'x-annotator-user-id': gooduser }
    bad_headers = { 'x-annotator-user-id': baduser }

    def setup(self):
        self.permissions = dict(
            read=[self.gooduser, self.updateuser],
            update=[self.gooduser, self.updateuser],
            admin=[self.gooduser])
        kwargs = dict(
            id=self.anno_id,
            text=u"Foo",
            permissions=self.permissions
            )
        ann = Annotation(**kwargs)
        ann.save()
        self.app = app.test_client()

    def teardown(self):
        rebuild_db(app.config['COUCHDB_DATABASE'])

    def test_read(self):
        response = self.app.get('/annotations/123')
        assert response.status_code == 401, response.status_code

        response = self.app.get('/annotations/123', headers=self.bad_headers)
        assert response.status_code == 401, response.status_code

        response = self.app.get('/annotations/123', headers=self.headers)
        assert response.status_code == 200, response.status_code
        data = json.loads(response.data)
        assert data['text'] == 'Foo'

    def test_update(self):
        payload = json.dumps({'id': self.anno_id, 'text': 'Bar'})

        response = self.app.put('/annotations/123', data=payload, content_type='application/json')
        assert response.status_code == 401, response.status_code

        response = self.app.put('/annotations/123', data=payload,
                content_type='application/json', headers=self.bad_headers)
        assert response.status_code == 401, response.status_code

        response = self.app.put('/annotations/123', data=payload,
                content_type='application/json', headers=self.headers)
        assert response.status_code == 200, response.status_code

    def test_update_change_permissions_not_allowed(self):
        newperms = dict(self.permissions)
        newperms['read'] = [self.gooduser, self.baduser]
        payload = json.dumps({'id': self.anno_id, 'text': 'Bar',
            'permissions': newperms})

        response = self.app.put('/annotations/123', data=payload,
                content_type='application/json', headers=self.bad_headers
                )
        assert response.status_code == 401, response.status_code

        response = self.app.put('/annotations/123', data=payload,
                content_type='application/json',
                headers={'x-annotator-user-id': self.updateuser}
                )
        assert response.status_code == 401, response.status_code
        assert '(permissions change)' in response.data, response.data

        response = self.app.put('/annotations/123', data=payload,
                content_type='application/json', headers=self.headers
                )
        assert response.status_code == 200, response.status_code

