import uuid
import json
import pprint
from nose.tools import assert_raises

from annotator.model.couch import Annotation
from annotator.model.couch import rebuild_db, init_model, Metadata


class TestAnnotation():
    testdb = 'annotator-test'

    def setup(self):
        config = {
            'COUCHDB_HOST': 'http://localhost:5984',
            'COUCHDB_DATABASE': self.testdb
            }
        init_model(config)

    def teardown(self):
        del Metadata.SERVER[self.testdb]

    def test_01_text(self):
        ann = Annotation(text="Hello there", user="Alice")
        ann.save()
        ann = Annotation.get(ann.id)
        assert ann.text == "Hello there", "annotation text wasn't set"
        assert ann.user == "Alice", "annotation user wasn't set"

    def test_ranges(self):
        ann = Annotation()
        ann.ranges.append({})
        ann.ranges.append({})
        assert len(ann.ranges) == 2, "ranges weren't added to annotation"

    def test_to_dict(self):
        ann = Annotation(text="Foo")
        data = {'ranges': [], 'text': 'Foo', 'user': None}
        outdict = ann.to_dict()
        for k,v in data.items():
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

        # alldocs = [x.doc for x in Metadata.DB.view('_all_docs', include_docs=True)]
        # pprint.pprint(alldocs)

        res = list(Annotation.search())
        assert len(res) == 3, res

        res = list(Annotation.search(limit=1))
        assert len(res) == 1

        res = list(Annotation.search(uri=uri1))
        assert len(res) == 2, [ x.doc for x in res ]
        assert res[0].doc['uri'] == uri1
        assert res[0].doc.id in [ annoid, anno2id ]

