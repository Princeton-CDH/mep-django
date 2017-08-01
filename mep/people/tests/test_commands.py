from io import StringIO

from django.test import TestCase
from django.core.management.base import CommandError
import pytest

from mep.people.management.commands import import_personography
from mep.people.tests.test_xmlmodels import XML_FIXTURE


class TestImportPersonography(TestCase):

    def setUp(self):
        self.cmd = import_personography.Command()
        self.cmd.stdout = StringIO()

    def test_command(self):
        # bad path
        with pytest.raises(CommandError):
            self.cmd.handle(path='/tmp/not/here')

        # valid path
        self.cmd.handle(path=XML_FIXTURE)
        output = self.cmd.stdout.getvalue()
        # inspect output
        expected_text = [
            'Found 4 people in XML personography',
            '4 people added',
            '3 addresses added',
            '3 countries added',
            '3 urls added'
        ]

        for txt in expected_text:
            assert txt in output

        # run again, should not re-add
        self.cmd.handle(path=XML_FIXTURE)
        output = self.cmd.stdout.getvalue()
        assert '0 people added' in output

