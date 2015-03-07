import copy
from nose.tools import *

from . import TestCase
from annotator.oa_renderer import OARenderer

annotation = {
    'created': '2015-03-07T09:48:34.891753+00:00',
    'id': 'test-annotation-id-1',
    'ranges': [{
        'type': 'RangeSelector',
        'startOffset': 0,
        'endOffset': 30,
        'end': '/div[1]/div[5]/div[1]/div[5]/div[1]/div[2]',
        'start': '/div[1]/div[5]/div[1]/div[5]/div[1]/div[1]'
    }],
    'text': 'From childhood\'s hour I have not been'
            'As others were-I have not seen',
    'tags': ['Edgar Allan Poe', 'Alone', 'Poem'],
    'updated': '2015-03-07T09:49:34.891769+00:00',
    'uri': 'http://www.poetryfoundation.org/poem/175776',
    'user': 'nameless.raven'
}

oa_rendered_annotation = {
    '@context': [
        "http://www.w3.org/ns/oa-context-20130208.json",
        {'annotator': 'http://annotatorjs.org/ns/'}
    ],
    '@id': annotation['id'],
    '@type': 'oa:Annotation',
    'hasBody': [
        {
            '@type': ['dctypes:Text', 'cnt:ContentAsText'],
            'dc:format': 'text/plain',
            'cnt:chars': annotation['text']
        },
        {
            '@type': ['oa:Tag', 'cnt:ContentAsText'],
            'dc:format': 'text/plain',
            'cnt:chars': annotation['tags'][0]
        },
        {
            '@type': ['oa:Tag', 'cnt:ContentAsText'],
            'dc:format': 'text/plain',
            'cnt:chars': annotation['tags'][1]
        },
        {
            '@type': ['oa:Tag', 'cnt:ContentAsText'],
            'dc:format': 'text/plain',
            'cnt:chars': annotation['tags'][2]
        }
    ],
    'hasTarget': [
        {
            '@type': 'oa:SpecificResource',
            'hasSource': annotation['uri'],
            'hasSelector': {
                '@type': 'annotator:TextRangeSelector',
                'annotator:startContainer': annotation['ranges'][0]['start'],
                'annotator:endContainer': annotation['ranges'][0]['end'],
                'annotator:startOffset': annotation['ranges'][0]['startOffset'],
                'annotator:endOffset': annotation['ranges'][0]['endOffset']
            }
        }
    ],
    'annotatedBy': {
        '@type': 'foaf:Agent',
        'foaf:name': annotation['user']
    },
    'annotatedAt': annotation['created'],
    'serializedBy': {
        '@id': 'annotator:annotator-store',
        '@type': 'prov:Software-agent',
        'foaf:name': 'annotator-store',
        'foaf:homepage': {'@id': 'http://annotatorjs.org'},
    },
    'serializedAt': annotation['updated'],
    'motivatedBy': ['oa:commenting', 'oa:tagging']
}


class TestOARenderer(TestCase):
    def setup(self):
        super(TestOARenderer, self).setup()
        self.renderer = OARenderer()

    def teardown(self):
        super(TestOARenderer, self).teardown()

    def test_context_without_jsonld_baseurl(self):
        rendered = self.renderer.render(annotation)

        assert '@context' in rendered
        context = rendered['@context']
        exp_context = oa_rendered_annotation['@context']
        assert len(context) is 2
        assert context[0] == exp_context[0]
        assert context[1] == exp_context[1]

    def test_context_with_jsonld_baseurl(self):
        jsonld_baseurl = 'http://jsonld_baseurl.com'
        renderer = OARenderer(jsonld_baseurl)
        rendered = renderer.render(annotation)

        assert '@context' in rendered
        context = rendered['@context']
        assert len(context) is 3
        assert '@base' in context[2]
        assert context[2]['@base'] == jsonld_baseurl

    def test_id(self):
        rendered = self.renderer.render(annotation)
        assert '@id' in rendered
        assert rendered['@id'] == oa_rendered_annotation['@id']

    def test_type(self):
        rendered = self.renderer.render(annotation)
        assert '@type' in rendered
        assert rendered['@type'] == oa_rendered_annotation['@type']

    def test_has_body(self):
        rendered = self.renderer.render(annotation)

        assert 'hasBody' in rendered
        hasBody = rendered['hasBody']
        assert len(hasBody) is 4

        assert hasBody[0] == oa_rendered_annotation['hasBody'][0]
        assert hasBody[1] == oa_rendered_annotation['hasBody'][1]
        assert hasBody[2] == oa_rendered_annotation['hasBody'][2]
        assert hasBody[3] == oa_rendered_annotation['hasBody'][3]

        assert 'motivatedBy' in rendered
        assert len(rendered['motivatedBy']) is 2
        assert rendered['motivatedBy'][0] == 'oa:commenting'
        assert rendered['motivatedBy'][1] == 'oa:tagging'

    def test_has_body_without_tags(self):
        copied_annotation = copy.deepcopy(annotation)
        del copied_annotation['tags']
        rendered = self.renderer.render(copied_annotation)

        assert 'hasBody' in rendered
        hasBody = rendered['hasBody']
        assert len(hasBody) is 1
        assert hasBody[0] == oa_rendered_annotation['hasBody'][0]

        assert 'motivatedBy' in rendered
        assert len(rendered['motivatedBy']) is 1
        assert rendered['motivatedBy'][0] == 'oa:commenting'

    def test_has_body_without_text(self):
        copied_annotation = copy.deepcopy(annotation)
        del copied_annotation['text']
        rendered = self.renderer.render(copied_annotation)

        assert 'hasBody' in rendered
        hasBody = rendered['hasBody']
        assert len(hasBody) is 3
        assert hasBody[0] == oa_rendered_annotation['hasBody'][1]
        assert hasBody[1] == oa_rendered_annotation['hasBody'][2]
        assert hasBody[2] == oa_rendered_annotation['hasBody'][3]

        assert 'motivatedBy' in rendered
        assert len(rendered['motivatedBy']) is 1
        assert rendered['motivatedBy'][0] == 'oa:tagging'

    def test_has_body_empty(self):
        copied_annotation = copy.deepcopy(annotation)
        del copied_annotation['text']
        del copied_annotation['tags']
        rendered = self.renderer.render(copied_annotation)

        assert 'hasBody' in rendered
        hasBody = rendered['hasBody']
        assert len(hasBody) is 0

        assert 'motivatedBy' in rendered
        assert len(rendered['motivatedBy']) is 0

    def test_has_target(self):
        rendered = self.renderer.render(annotation)

        assert 'hasTarget' in rendered
        hasTarget = rendered['hasTarget']
        assert len(hasTarget) is 1
        assert hasTarget[0] == oa_rendered_annotation['hasTarget'][0]

        assert 'hasSelector' in hasTarget[0]
        hasSelector = hasTarget[0]['hasSelector']
        oa_selector = oa_rendered_annotation['hasTarget'][0]['hasSelector']
        assert hasSelector == oa_selector

    def test_has_target_without_ranges(self):
        copied_annotation = copy.deepcopy(annotation)
        del copied_annotation['ranges']
        rendered = self.renderer.render(copied_annotation)

        assert 'hasTarget' in rendered
        hasTarget = rendered['hasTarget']
        assert len(hasTarget) is 1
        assert hasTarget[0] == annotation['uri']

    def test_has_target_without_uri(self):
        copied_annotation = copy.deepcopy(annotation)
        del copied_annotation['uri']
        rendered = self.renderer.render(copied_annotation)

        assert 'hasTarget' in rendered
        hasTarget = rendered['hasTarget']
        assert len(hasTarget) is 0

    def test_annotated_by(self):
        rendered = self.renderer.render(annotation)

        assert 'annotatedBy' in rendered
        assert rendered['annotatedBy'] == oa_rendered_annotation['annotatedBy']

    def test_annotated_by_without_user(self):
        copied_annotation = copy.deepcopy(annotation)
        del copied_annotation['user']
        rendered = self.renderer.render(copied_annotation)

        assert 'annotatedBy' in rendered
        assert rendered['annotatedBy'] == {}

    def test_annotated_at(self):
        rendered = self.renderer.render(annotation)

        assert 'annotatedAt' in rendered
        assert rendered['annotatedAt'] == oa_rendered_annotation['annotatedAt']

    def test_serialized_at(self):
        rendered = self.renderer.render(annotation)

        assert 'serializedAt' in rendered
        assert rendered['serializedAt'] == oa_rendered_annotation['serializedAt']
