import uuid
import json
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



