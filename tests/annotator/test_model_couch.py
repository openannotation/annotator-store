import uuid
import json
import pprint
from nose.tools import assert_raises

from annotator.model.couch import Annotation, Account
from annotator.model.couch import rebuild_db, init_model, Metadata

testdb = 'annotator-test'

class TestAnnotation():
    def setup(self):
        config = {
            'COUCHDB_HOST': 'http://localhost:5984',
            'COUCHDB_DATABASE': testdb
            }
        init_model(config)

    def teardown(self):
        del Metadata.SERVER[testdb]

    def test_01_text(self):
        user = {"id": "Alice", "name": "Alice Wonderland"}
        ann = Annotation(text="Hello there", user=user)
        ann.ranges.append({})
        ann.ranges.append({})
        ann.save()
        ann = Annotation.get(ann.id)
        assert ann.text == "Hello there", "annotation text wasn't set"
        assert ann.user['id'] == "Alice", "annotation user wasn't set"
        assert ann.user['name'] == "Alice Wonderland", "annotation user wasn't set"
        assert len(ann.ranges) == 2, "ranges weren't added to annotation"

    def test_to_dict(self):
        ann = Annotation(text="Foo")
        data = {'ranges': [], 'text': 'Foo', 'user': {}}
        outdict = ann.to_dict()
        for k,v in data.items():
            print k,v,outdict[k]
            assert outdict[k] == v, "annotation wasn't converted to dict correctly"

    def test_to_dict_with_range(self):
        ann = Annotation(text="Bar")
        ann.ranges.append({})
        assert len(ann.to_dict()['ranges']) == 1, "annotation ranges weren't in dict"

    def test_from_dict(self):
        ann = Annotation.from_dict({'text': 'Baz'})
        assert ann.text == "Baz", "annotation wasn't updated from dict"

    def test_from_dict_with_range(self):
        ann = Annotation.from_dict({'ranges': [{}]})
        assert len(ann.ranges) == 1, "annotation ranges weren't updated from dict"

    def test_extras_in(self):
        ann = Annotation.from_dict({'foo':1, 'bar':2})
        ann.save()
        ann = Annotation.get(ann.id)
        extras = dict(ann.items())
        print extras
        assert 'foo' in extras.keys(), "extras weren't serialized properly"
        assert 'bar' in extras.keys(), "extras weren't serialized properly"
        assert ann['foo'] == 1, "extras weren't serialized properly"
        assert ann['bar'] == 2, "extras weren't serialized properly"

    def test_extras_out(self):
        ann = Annotation.from_dict({"bar": 3, "baz": 4})
        print ann
        data = ann.to_dict()
        print data
        assert data['bar'] == 3, "extras weren't deserialized properly"
        assert data['baz'] == 4, "extras weren't deserialized properly"
    
    def test_delete(self):
        id_ = str(uuid.uuid4())
        ann = Annotation(id=id_)
        ann.save()

        newann = Annotation.get(id_)
        newann.delete()

        noann = Annotation.get(id_)
        assert noann == None

    def test_search(self):
        uri1 = u'http://xyz.com'
        uri2 = u'urn:uuid:xxxxx'
        user = u'levin'
        user2 = u'anna'
        anno = Annotation(**dict(
                uri=uri1,
                text=uri1,
                user=user,
                ))
        anno2 = Annotation(**dict(
                uri=uri1,
                text=uri1 + uri1,
                user=user2,
                ))
        anno3 = Annotation(**dict(
                uri=uri2,
                text=uri2,
                user=user
                ))
        anno.save()
        anno2.save()
        anno3.save()
        annoid = anno.id
        anno2id = anno2.id
        anno3id = anno3.id

        # alldocs = [x.doc for x in Metadata.DB.view('_all_docs', include_docs=True)]
        # pprint.pprint(alldocs)

        res = list(Annotation.search())
        assert len(res) == 3, res

        res = list(Annotation.search(limit=1))
        assert len(res) == 1, len(res)

        res = list(Annotation.search(uri=uri1))
        assert len(res) == 2, [ x for x in res ]
        assert res[0].uri == uri1
        assert res[0].id in [ annoid, anno2id ]

        res = list(Annotation.search(**{'user.id':user}))
        assert len(res) == 2, [ x for x in res ]
        assert res[0].user['id'] == user
        assert res[0].id in [ annoid, anno3id ]

        res = list(Annotation.search(**{'user.id':user, 'uri': uri2}))
        assert len(res) == 1, [ x for x in res ]
        assert res[0].user['id'] == user
        assert res[0].id == anno3id


class TestAccount():
    def setup(self):
        config = {
            'COUCHDB_HOST': 'http://localhost:5984',
            'COUCHDB_DATABASE': testdb
            }
        init_model(config)

    def teardown(self):
        del Metadata.SERVER[testdb]

    def test_key(self):
        c = Account(id='foo')
        c.save()
        c = Account.get('foo')
        assert c.id == 'foo', 'Account key not set by constructor'
        assert len(c.secret) == 36, c

    def test_account_by_email(self):
        email = 'me@me.com'     
        acc = Account(email=email, username='abc')
        acc.save()

        out = Account.get_by_email('madeupemail')
        assert len(out) == 0, out

        out = Account.get_by_email(email)
        assert len(out) == 1, out
        assert out[0].email == email
        assert out[0].username == 'abc'

