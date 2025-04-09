"""
    Unittests
"""
import io
import re
import unittest
import unittest.mock
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, List

from lxml.etree import tostring as xml_to_string, fromstring as xml_from_string

import zus


@dataclass
class TestDocument:
    """
    User ID document test class
    """
    number: str = ''
    type: str = '0'


@dataclass
class TestXml:
    """
    ZUS KEDU XML test class
    """
    _tmpl_xml = '<KEDU xmlns="http://www.zus.pl/2022/KEDU_5_5" ' \
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" wersja_schematu="1" ' \
                'xsi:schemaLocation="http://www.zus.pl/2022/KEDU_5_5_kedu 5_5.xsd">' \
                '<ZUSDRA>{user_id}</ZUSDRA></KEDU>'
    _original_user_id = '<II><p1></p1><p2></p2><p3></p3><p6></p6><p7></p7><p8></p8><p9></p9></II>'
    _tmpl_patched_user_id = '<II><p1/><p2/><p3/><p4>{type}</p4><p5>{number}</p5><p6/><p7/><p8/><p9/></II>'

    user_id_count: int

    def to_xml(self) -> bytes:
        """
        :return: ZUS KEDU original document XML
        """
        return self._tmpl_xml.format(user_id=(self._original_user_id * self.user_id_count)).encode()

    def to_patched_xml(self, user_id_document: TestDocument) -> bytes:
        """
        :param user_id_document: user ID document
        :return: ZUS KEDU XML with user data added
        """
        return self._tmpl_xml.format(user_id=(self._patched_user_id(user_id_document) * self.user_id_count)).encode()

    def to_canonical(self) -> bytes:
        """
        :return: Canonical form of ZUS KEDU original document (e.g. with no empty tags)
        """
        return xml_to_string(xml_from_string(self.to_xml()))

    def _patched_user_id(self, user_id_document: TestDocument):
        return self._tmpl_patched_user_id.format(number=user_id_document.number.strip().upper(),
                                                 type=user_id_document.type)


def prepare_test_data(user_id_count: int = 1) -> Tuple[TestXml, zus.kedu.KEDU]:
    """
    Prepare test data
    :param user_id_count: number of user id entries
    :return: ZUS KEDU test XML object, ZUS KEDU object
    """
    content = TestXml(user_id_count)
    kedu = zus.kedu.KEDU()
    return content, kedu


class MyTestCase(unittest.TestCase):
    def setUp(self):
        """
        Test setup
        """
        self.stdout_patcher = unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
        self.stdout = self.stdout_patcher.start()

        self.stderr_patcher = unittest.mock.patch('sys.stderr', new_callable=io.StringIO)
        self.stderr = self.stderr_patcher.start()

    def tearDown(self):
        """
        Test teardown
        """
        self.stdout_patcher.stop()
        self.stderr_patcher.stop()

    def add_id(self, users: int, test_documents: List[TestDocument]):
        """
        Tests adding user ID document
        :param users: number of user entries to generate in ZUS KEDU
        :param test_documents: list of ID documents to be used in tests
        """
        content, kedu = prepare_test_data(users)
        for test_document in test_documents:
            with unittest.mock.patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=content.to_xml()):
                kedu.load('kedu.xml')
            kedu.add_id_document(zus.identity_document.IdentityDocument(test_document.number))
            self.assertEqual(xml_to_string(kedu.xml), content.to_patched_xml(test_document))

    def test_malformed_document(self):
        for i in range(0, 2):
            content, kedu = prepare_test_data(i)
            with unittest.mock.patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=content.to_xml()):
                if i > 0:
                    kedu.load('kedu.xml')
                else:
                    with self.assertRaisesRegex(AssertionError,
                                                'Malformed ZUS KEDU document, expected at least one user id data entry, found 0!'):
                        kedu.load('kedu.xml')
        self.assertEqual(len(re.findall(r'Opening kedu\.xml', self.stdout.getvalue())), 2)

    def test_add_id(self):
        test_documents = [
            TestDocument('aaa000000', '1'),
            TestDocument('aa0000000', '2'),
            TestDocument('BBB000000', '1'),
            TestDocument('BB0000000', '2'),
            TestDocument('CcC000000', '1'),
            TestDocument('Ca0000000', '2')
        ]
        self.add_id(1, test_documents)
        output = self.stdout.getvalue()
        self.assertEqual(len(re.findall(r'Opening kedu\.xml', output)), 6)
        self.assertEqual(len(re.findall('Patching', output)), 6)

    def test_add_id_two_users(self):
        test_documents = [
            TestDocument('aaa000000', '1'),
            TestDocument('aa0000000', '2'),
            TestDocument('BBB000000', '1'),
            TestDocument('BB0000000', '2'),
            TestDocument('CcC000000', '1'),
            TestDocument('Ca0000000', '2')
        ]
        self.add_id(2, test_documents)
        output = self.stdout.getvalue()
        self.assertEqual(len(re.findall(r'Opening kedu\.xml', output)), 6)
        self.assertEqual(len(re.findall('Patching', output)), 12)

    def test_load_xml(self):
        content, kedu = prepare_test_data()
        with unittest.mock.patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=content.to_xml()):
            kedu.load(Path('kedu.xml'))
            self.assertEqual(xml_to_string(kedu.xml), content.to_canonical())
        self.assertIn('Opening kedu.xml', self.stdout.getvalue())

    def test_dont_save_not_patched_xml(self):
        content, kedu = prepare_test_data()
        with unittest.mock.patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=content.to_xml()):
            kedu.load(Path('kedu.xml'))

        write_mock = unittest.mock.mock_open()
        with unittest.mock.patch('builtins.open', write_mock):
            output_file = Path('kedu.xml')
            kedu.save(output_file)
            write_mock.assert_not_called()

        output = self.stdout.getvalue()
        self.assertIn('Opening kedu.xml', output)
        self.assertIn('Nothing was changed, not writing', output)

    def test_save_patched_xml(self):
        content, kedu = prepare_test_data()
        test_document = TestDocument('aaa000000', '1')
        with unittest.mock.patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=content.to_xml()):
            kedu.load(Path('kedu.xml'))
        write_mock = unittest.mock.mock_open()

        id_document = zus.identity_document.IdentityDocument(test_document.number)
        kedu.add_id_document(id_document)
        with unittest.mock.patch('builtins.open', write_mock):
            output = Path('kedu.xml')
            kedu.save(output)
            write_mock.assert_called_once_with(output, mode='wb')
            write_mock().write.assert_called_once_with(content.to_patched_xml(test_document))

        output = self.stdout.getvalue()
        self.assertIn('Opening kedu.xml', output)
        self.assertIn('Patching', output)
        self.assertIn('Writing to kedu.xml', output)

    def test_skip_patching_if_already_patched(self):
        content, kedu = prepare_test_data()
        test_document = TestDocument('aaa000000', '1')
        with unittest.mock.patch('builtins.open', new_callable=unittest.mock.mock_open,
                                 read_data=content.to_patched_xml(test_document)):
            kedu.load(Path('kedu.xml'))
        write_mock = unittest.mock.mock_open()

        id_document = zus.identity_document.IdentityDocument(test_document.number)
        kedu.add_id_document(id_document)
        with unittest.mock.patch('builtins.open', write_mock):
            output = Path('kedu.xml')
            kedu.save(output)
            write_mock.assert_not_called()

        output = self.stdout.getvalue()
        self.assertIn('Opening kedu.xml', output)
        self.assertRegex(output,
                         r'WARNING: element .* of .* already contains valid user ID data, patching skipped')
        self.assertIn('Nothing was changed, not writing', output)

if __name__ == '__main__':
    unittest.main()
