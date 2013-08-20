from nose.tools import istest

from provy.core.errors import ConfigurationError
from provy.core.runner import get_items, recurse_items
from tests.unit.tools.helpers import ProvyTestCase


class RunnerTest(ProvyTestCase):
    @istest
    def cannot_get_items_if_prov_doesnt_have_required_attribute(self):
        self.assertRaises(ConfigurationError, get_items, 'some prov variable', 'inexistant_item_name', 'inexistant_item_key', 'some test func')

    @istest
    def builds_items_list_after_recursing_over_a_dict(self):

        def foo_macher(item):
            return 'foo' in item

        found_items = []

        collection = {
            'my name': 'foo name',
            'personal stuff': {
                'car': 'some foo truck',
                'books': ['foo', 'bar'],
                'bar': 'something with iron, just ignore',
                'others': {
                    'foo': 'something undescribable',
                },
            },
        }

        recurse_items(collection, foo_macher, found_items)

        expected_items = [
            'foo name',
            'some foo truck',
            ['foo', 'bar'],
            {
                'foo': 'something undescribable',
            },
        ]
        self.assertListEqual(sorted(found_items), sorted(expected_items), found_items)
