"""
Unit Test of the check records functions for the base class, CheckIfExtract
"""

import unittest
import utils
import json
from settings import PROJ_HOME, config, CONSTANTS, META_CONTENT
from lib import CheckIfExtract as check
from lib import StandardFileExtract as std_extract
test_file = 'tests/test_integration/stub_data/fulltext.links'
test_file_stub = 'tests/test_integration/stub_data/fulltext_stub.links'
test_file_wrong = 'tests/test_integration/stub_data/fulltext_wrong.links'
test_file_exists = 'tests/test_integration/stub_data/fulltext_exists.links'

test_stub_xml = 'tests/test_unit/stub_data/test.xml'

class TestCheckIfExtracted(unittest.TestCase):

    def test_file_not_extracted_before(self):

        FileInputStream = utils.FileInputStream(test_file_stub)
        FileInputStream.extract()

        payload = FileInputStream.raw[0]

        exists = check.meta_output_exists(payload, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

        self.assertEqual(exists, False)

    def test_file_extracted_before(self):

        FileInputStream = utils.FileInputStream(test_file_exists)
        FileInputStream.extract()

        payload = FileInputStream.raw[0]

        exists = check.meta_output_exists(payload, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

        self.assertEqual(exists, True, "Could not establish that this file has been extracted before")

    def test_file_extract_meta(self):

        FileInputStream = utils.FileInputStream(test_file_exists)
        FileInputStream.extract()

        payload = FileInputStream.raw[0]

        content = check.load_meta_file(payload, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")


        self.assertTrue(len(content)>0, "Did not extract the meta data correctly")

    def test_file_should_be_updated_if_missing_fulltext(self):

        FileInputStream = utils.FileInputStream(test_file_exists)
        FileInputStream.extract()

        meta_content = check.load_meta_file(FileInputStream.raw[0], extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")
        new_meta_content = {}

        for key in meta_content.keys():
            if key != 'ft_source':	new_meta_content[key] = meta_content[key]

        updated = check.meta_needs_update(FileInputStream, new_meta_content, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

        self.assertEqual(updated, 'MISSING_FULL_TEXT', "The ft_source should need updating, not %s" % updated)

    def test_file_should_be_updated_if_content_differs_to_input(self):

        FileInputStream = utils.FileInputStream(test_file_exists)
        FileInputStream.extract()
        payload = FileInputStream.raw[0]

        meta_content = check.load_meta_file(payload, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

        meta_content['ft_source'] = ''
        updated = check.meta_needs_update(payload, meta_content, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

        self.assertEqual(updated, 'DIFFERING_FULL_TEXT', "The ft_source should need updating, not %s" % updated)

    def test_file_should_be_updated_if_content_is_stale(self):

        FileInputStream = utils.FileInputStream(test_file_exists)
        FileInputStream.extract()

        payload = FileInputStream.raw[0]

        meta_content = check.load_meta_file(payload, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

        updated = check.meta_needs_update(payload, meta_content, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

        self.assertEqual(updated, 'STALE_CONTENT', "The file content should be stale, not %s" % updated)

    def test_file_should_be_extracted(self):

        FileInputStream = utils.FileInputStream(test_file)
        FileInputStream.extract()

        payload = check.check_if_extract(FileInputStream.raw, extract_key="FULLTEXT_EXTRACT_PATH_UNITTEST")

        pdf_compare = [content for content in json.loads(payload["PDF"]) if content["UPDATE"] in
         [u"STALE_CONTENT", u"DIFFERING_FULL_TEXT", u"MISSING_FULL_TEXT", u"NOT_EXTRACTED_BEFORE"]]

        standard_compare = [content for content in json.loads(payload["Standard"]) if content["UPDATE"] in
         [u"STALE_CONTENT", u"DIFFERING_FULL_TEXT", u"MISSING_FULL_TEXT", u"NOT_EXTRACTED_BEFORE"]]

        self.assertTrue(len(pdf_compare) == 3, json.loads(payload["PDF"]))
        self.assertTrue(len(standard_compare) == 1)


class TestFileStreamInput(unittest.TestCase):

    def test_file_stream_input_extract_file(self):

        FileInputStream = utils.FileInputStream(test_file)
        ext = FileInputStream.extract()

        self.assertEqual(len(FileInputStream.bibcode), 5, "Did not extract the correct number of records from the input file")

    def test_file_stream_input_extract_list(self):

        FileInputStream = utils.FileInputStream(test_file_stub)
        ext = FileInputStream.extract()

        self.assertIn("2015MNRAS.446.4239E", FileInputStream.bibcode)
        self.assertIn("/vagrant/test/data/test.pdf", FileInputStream.full_text_path)
        self.assertIn("MNRAS", FileInputStream.provider)


class TestStandardFileExtract(unittest.TestCase):

    def setUp(self):
        self.dict_item = {CONSTANTS["FILE_SOURCE"]: "%s/%s" % (config["FULLTEXT_EXTRACT_PATH"], test_stub_xml)}
        self.extractor = std_extract.StandardExtractorXML(self.dict_item)

    def test_that_we_can_open_an_xml_file(self):
        full_text_content = self.extractor.open_xml()

        self.assertIn("<journal-title>Review of Scientific Instruments</journal-title>", full_text_content)

    def test_that_we_can_parse_the_xml_content(self):
        full_text_content = self.extractor.open_xml()
        content = self.extractor.parse_xml()
        journal_title = content.xpath('//journal-title')[0].text_content()

        self.assertEqual(journal_title, "Review of Scientific Instruments")

    def test_that_we_can_extract_using_settings_template(self):

        full_text_content = self.extractor.open_xml()
        parsed_xml = self.extractor.parse_xml()
        content = self.extractor.extract_multi_content()

        self.assertEqual(META_CONTENT["XML"].keys(), content.keys())

    def test_that_we_can_extract_all_content_from_payload_input(self):

        file_path = "%s/%s" % (config["FULLTEXT_EXTRACT_PATH"], test_stub_xml)
        pay_load = [self.dict_item]

        content = json.loads(std_extract.extract_content(pay_load))

        self.assertEqual(len(content[0].keys()), 3)
        self.assertItemsEqual(content[0].keys(), META_CONTENT["XML"].keys())


if __name__ == '__main__':
    unittest.main()