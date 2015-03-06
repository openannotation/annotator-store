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

from annotator.annotation import Annotation


class OAAnnotation(Annotation):
    jsonld_baseurl = None

    @property
    def jsonld(self):
        """The JSON-LD formatted RDF representation of the annotation."""

        context = [
            "http://www.w3.org/ns/oa-context-20130208.json",
            {'annotator': 'http://annotatorjs.org/ns/'}
        ]

        if self.jsonld_baseurl is not None:
            context.append({'@base': self.jsonld_baseurl})

        # The JSON-LD spec recommends to put @context at the top of the
        # document, so we'll be nice and use and ordered dictionary.
        annotation = OrderedDict()
        annotation['@context'] = context
        annotation['@id'] = self['id']
        annotation['@type'] = 'oa:Annotation'
        annotation['hasBody'] = self.has_body
        annotation['hasTarget'] = self.has_target
        annotation['annotatedBy'] = self.annotated_by
        annotation['annotatedAt'] = self.annotated_at
        annotation['serializedBy'] = self.serialized_by
        annotation['serializedAt'] = self.serialized_at
        annotation['motivatedBy'] = self.motivated_by
        return annotation

    @property
    def has_body(self):
        """Return all annotation bodies: the text comment and each tag"""
        bodies = []
        bodies += self.textual_bodies
        bodies += self.tags
        return bodies

    @property
    def textual_bodies(self):
        """A list with a single text body or an empty list"""
        if not self.get('text'):
            # Note that we treat an empty text as not having text at all.
            return []
        body = {
            '@type': ['dctypes:Text', 'cnt:ContentAsText'],
            'dc:format': 'text/plain',
            'cnt:chars': self['text'],
        }
        return [body]

    @property
    def tags(self):
        """A list of oa:Tag items"""
        if 'tags' not in self:
            return []
        return [
            {
                '@type': ['oa:Tag', 'cnt:ContentAsText'],
                'dc:format': 'text/plain',
                'cnt:chars': tag,
            }
            for tag in self['tags']
        ]

    @property
    def motivated_by(self):
        """Motivations for the annotation.

           Currently any combination of commenting and/or tagging.
        """
        motivations = []
        if self.textual_bodies:
            motivations.append('oa:commenting')
        if self.tags:
            motivations.append('oa:tagging')
        return motivations

    @property
    def has_target(self):
        """The targets of the annotation.

           Returns a selector for each range of the page content that was
           selected, or if a range is absent the url of the page itself.
        """
        targets = []
        if not 'uri' in self:
            return targets
        if self.get('ranges'):
            # Build the selector for each quote
            for rangeSelector in self['ranges']:
                selector = {
                    '@type': 'annotator:TextRangeSelector',
                    'annotator:startContainer': rangeSelector['start'],
                    'annotator:endContainer': rangeSelector['end'],
                    'annotator:startOffset': rangeSelector['startOffset'],
                    'annotator:endOffset': rangeSelector['endOffset'],
                }
                target = {
                    '@type': 'oa:SpecificResource',
                    'hasSource': self['uri'],
                    'hasSelector': selector,
                }
                targets.append(target)
        else:
            # The annotation targets the page as a whole
            targets.append(self['uri'])
        return targets

    @property
    def annotated_by(self):
        """The user that created the annotation."""
        if not self.get('user'):
            return []
        return {
            '@type': 'foaf:Agent', # It could be either a person or a bot
            'foaf:name': self['user'],
        }

    @property
    def annotated_at(self):
        """The annotation's creation date"""
        if self.get('created'):
            return self['created']

    @property
    def serialized_by(self):
        """The software used for serializing."""
        return {
            '@id': 'annotator:annotator-store',
            '@type': 'prov:Software-agent',
            'foaf:name': 'annotator-store',
            'foaf:homepage': {'@id': 'http://annotatorjs.org'},
        }  # todo: add version number

    @property
    def serialized_at(self):
        """The last time the serialization changed."""
        # Following the spec[1], we do not use the current time, but the last
        # time the annotation graph has been updated.
        # [1]: https://hypothes.is/a/R6uHQyVTQYqBc4-1V9X56Q
        if self.get('updated'):
            return self['updated']
