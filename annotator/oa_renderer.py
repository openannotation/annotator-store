import logging
log = logging.getLogger(__name__)

try:
    from collections import OrderedDict
except ImportError:
    try:
        from ordereddict import OrderedDict
    except ImportError:
        log.warn("No OrderedDict available, JSON-LD content will be unordered. "
                 "Use Python>=2.7 or install ordereddict module to fix.")
        OrderedDict = dict


class OARenderer(object):
    def __init__(self, jsonld_baserurl=None):
        self.jsonld_baseurl = jsonld_baserurl

    def render(self, annotation):
        """The JSON-LD formatted RDF representation of the annotation."""

        context = [
            "http://www.w3.org/ns/oa-context-20130208.json",
            {'annotator': 'http://annotatorjs.org/ns/'}
        ]

        if self.jsonld_baseurl is not None:
            context.append({'@base': self.jsonld_baseurl})

        # Extract textual_bodies and tags
        textual_bodies = get_textual_bodies(annotation)
        tags = get_tags(annotation)

        # The JSON-LD spec recommends to put @context at the top of the
        # document, so we'll be nice and use and ordered dictionary.
        out = OrderedDict()
        out['@context'] = context
        out['@id'] = annotation['id']
        out['@type'] = 'oa:Annotation'
        out['hasBody'] = has_body(textual_bodies, tags)
        out['hasTarget'] = has_target(annotation)
        out['annotatedBy'] = annotated_by(annotation)
        out['annotatedAt'] = annotated_at(annotation)
        out['serializedBy'] = serialized_by()
        out['serializedAt'] = serialized_at(annotation)
        out['motivatedBy'] = motivated_by(textual_bodies, tags)
        return out


def has_body(textual_bodies, tags):
    """Return all annotation bodies: the text comment and each tag"""
    bodies = []
    bodies += textual_bodies
    bodies += tags
    return bodies


def get_textual_bodies(annotation):
    """A list with a single text body or an empty list"""
    if not annotation.get('text'):
        # Note that we treat an empty text as not having text at all.
        return []
    body = {
        '@type': ['dctypes:Text', 'cnt:ContentAsText'],
        'dc:format': 'text/plain',
        'cnt:chars': annotation['text'],
    }
    return [body]


def get_tags(annotation):
    """A list of oa:Tag items"""
    if 'tags' not in annotation:
        return []
    return [
        {
            '@type': ['oa:Tag', 'cnt:ContentAsText'],
            'dc:format': 'text/plain',
            'cnt:chars': tag,
        }
        for tag in annotation['tags']
    ]


def motivated_by(textual_bodies, tags):
    """Motivations for the annotation.

       Currently any combination of commenting and/or tagging.
    """
    motivations = []
    if textual_bodies:
        motivations.append('oa:commenting')
    if tags:
        motivations.append('oa:tagging')
    return motivations


def has_target(annotation):
    """The targets of the annotation.

       Returns a selector for each range of the page content that was
       selected, or if a range is absent the url of the page itself.
    """
    targets = []
    if 'uri' not in annotation:
        return targets
    if annotation.get('ranges'):
        # Build the selector for each quote
        for rangeSelector in annotation['ranges']:
            selector = {
                '@type': 'annotator:TextRangeSelector',
                'annotator:startContainer': rangeSelector['start'],
                'annotator:endContainer': rangeSelector['end'],
                'annotator:startOffset': rangeSelector['startOffset'],
                'annotator:endOffset': rangeSelector['endOffset'],
            }
            target = {
                '@type': 'oa:SpecificResource',
                'hasSource': annotation['uri'],
                'hasSelector': selector,
            }
            targets.append(target)
    else:
        # The annotation targets the page as a whole
        targets.append(annotation['uri'])
    return targets


def annotated_by(annotation):
    """The user that created the annotation."""
    if not annotation.get('user'):
        return {}
    return {
        '@type': 'foaf:Agent',  # It could be either a person or a bot
        'foaf:name': annotation['user'],
    }


def annotated_at(annotation):
    """The annotation's creation date"""
    if annotation.get('created'):
        return annotation['created']


def serialized_by():
    """The software used for serializing."""
    return {
        '@id': 'annotator:annotator-store',
        '@type': 'prov:Software-agent',
        'foaf:name': 'annotator-store',
        'foaf:homepage': {'@id': 'http://annotatorjs.org'},
    }  # todo: add version number


def serialized_at(annotation):
    """The last time the serialization changed."""
    # Following the spec[1], we do not use the current time, but the last
    # time the annotation graph has been updated.
    # [1]: https://hypothes.is/a/R6uHQyVTQYqBc4-1V9X56Q
    if annotation.get('updated'):
        return annotation['updated']
