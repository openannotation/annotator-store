from nose.tools import *

from annotator.document import Document

from . import TestCase

class TestDocument(TestCase):

    def test_new(self):
        d = Document() 
        assert_equal('{}', repr(d))

