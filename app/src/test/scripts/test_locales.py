#!/usr/bin/env python3
"""Check locale coverage and Android formatting before compiling resources."""
import collections
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

RES = Path(__file__).resolve().parents[2] / 'main/res'
PRINTF = re.compile(r'%(?:\d+\$)?[-#+ 0,(]*\d*(?:\.\d+)?[a-zA-Z%]')


def resources(folder):
    strings = {}
    for file in (RES / folder).glob('*.xml'):
        for node in ET.parse(file).getroot():
            if node.tag == 'string':
                name = node.attrib['name']
                if name in strings:
                    raise AssertionError(f'duplicate {folder}/{name}')
                strings[name] = node
    return strings


class LocaleResourcesTest(unittest.TestCase):
    def assert_covers_all_translatable_strings(self, folder):
        base, translated = resources('values'), resources(folder)
        for name, node in base.items():
            if node.attrib.get('translatable') != 'false':
                self.assertIn(name, translated, f'{folder}/{name}')
                self.assertEqual(
                    collections.Counter(PRINTF.findall(''.join(node.itertext()))),
                    collections.Counter(PRINTF.findall(''.join(translated[name].itertext()))),
                    f'{folder}/{name}')

    def test_portuguese_covers_all_translatable_strings(self):
        self.assert_covers_all_translatable_strings('values-pt-rBR')

    def test_indonesian_covers_all_translatable_strings(self):
        self.assert_covers_all_translatable_strings('values-in')

    def test_indonesian_does_not_translate_untranslatable_strings(self):
        base, indonesian = resources('values'), resources('values-in')
        for name, node in base.items():
            if node.attrib.get('translatable') == 'false':
                self.assertNotIn(name, indonesian)

    def test_explicit_english_overrides_a_secondary_portuguese_locale(self):
        base, english = resources('values'), resources('values-en')
        for name, node in base.items():
            if node.attrib.get('translatable') != 'false':
                self.assertIn(name, english)
                self.assertEqual(''.join(node.itertext()), ''.join(english[name].itertext()), name)

    def test_only_display_arrays_are_translated(self):
        base = {x.attrib['name']: x for x in ET.parse(RES / 'values/arrays.xml').getroot()}
        for folder in ('values-pt-rBR', 'values-in'):
            for node in ET.parse(RES / folder / 'arrays.xml').getroot():
                self.assertIn(node.attrib['name'], {
                    'binding_type_entries', 'button_options', 'touchscreenInputModesEntries',
                    'transformCapturedPointerEntries'}, folder)
                self.assertEqual(len(base[node.attrib['name']]), len(node), f'{folder}/{node.attrib["name"]}')

    def test_declared_locales(self):
        ns = '{http://schemas.android.com/apk/res/android}'
        config = ET.parse(RES / 'xml/locales_config.xml').getroot()
        self.assertEqual(['en', 'pt-BR', 'id'], [node.attrib[ns + 'name'] for node in config])


if __name__ == '__main__':
    unittest.main()
        
