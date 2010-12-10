from flask import json, url_for

from annotator import app
from annotator.model import Annotation, Range
from annotator.model import create_all, drop_all, session

app.mountpoint = '/store'

class TestStore():
    def setup(self):
        self.app = app.test_client()
        create_all()

    def teardown(self):
        session.remove()
        drop_all()

    def test_index(self):
        assert self.app.get('/store').data == "[]", "response should be empty list"

    def test_create(self):
        import re
        payload = json.dumps({'name': 'Foo'})
        response = self.app.post('/store', data={'json': payload})
        assert response.status_code == 303, "response should be 303 SEE OTHER"
        assert re.match(r"http://localhost/store/\d+", response.headers['Location']), "response should redirect to read_annotation url"

    def test_read(self):
        Annotation(text=u"Foo", id=123)
        session.commit()
        response = self.app.get('/store/123')
        data = json.loads(response.data)
        assert data['id'] == 123, "annotation id should be returned in response"
        assert data['text'] == "Foo", "annotation text should be returned in response"

    def test_read_notfound(self):
        response = self.app.get('/store/123')
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_update(self):
        ann = Annotation(text=u"Foo", id=123)
        session.commit() # commits expire all properties of `ann'

        payload = json.dumps({'id': 123, 'text': 'Bar'})
        response = self.app.put('/store/123', data={'json': payload})

        assert ann.text == "Bar", "annotation wasn't updated in db"

        data = json.loads(response.data)
        assert data['text'] == "Bar", "update annotation should be returned in response"

    def test_update_notfound(self):
        response = self.app.put('/store/123')
        assert response.status_code == 404, "response should be 404 NOT FOUND"

    def test_delete(self):
        ann = Annotation(text=u"Bar", id=456)
        session.commit()

        response = self.app.delete('/store/456')
        assert response.status_code == 204, "response should be 204 NO CONTENT"

        assert Annotation.get(456) == None, "annotation wasn't deleted in db"

    def test_delete_notfound(self):
        response = self.app.delete('/store/123')
        assert response.status_code == 404, "response should be 404 NOT FOUND"
