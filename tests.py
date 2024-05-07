import unittest
import unittest.mock
from pathlib import Path

from drafix import add_user_id_data, find_user_info, load_dra_file, save_dra_file, KEDU_5_5_NAMESPACE
from lxml.etree import ElementTree, XML, tostring as xml_to_string, fromstring as xml_from_string
from functools import partial
from dataclasses import dataclass


@dataclass
class NamespaceTestData:
    namespace: str
    message: str


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.xml = '''\
    <KEDU xmlns="{namespace}" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" wersja_schematu="1"
    xsi:schemaLocation="http://www.zus.pl/2022/KEDU_5_5_kedu 5_5.xsd">
    <ZUSDRA>{user_id}</ZUSDRA></KEDU>'''

    def test_namespace(self):
        invalid_namespace = 'http://www.zus.pl/2023/KEDU_5_6'

        test_data = [NamespaceTestData(KEDU_5_5_NAMESPACE, 'Malformed ZUS DRA document, '
                                                           'expected single user id data entry, found: 0!'),
                     NamespaceTestData(invalid_namespace, f'Actual namespace "{invalid_namespace}" '
                                                          f'differs than expected one "{KEDU_5_5_NAMESPACE}", '
                                                          f'document cannot be processed')]

        for test_item in test_data:
            namespace = test_item.namespace
            document = XML(self.xml.format(namespace=namespace, user_id=''))
            try:
                self.assertRaisesRegex(AssertionError, test_item.message, find_user_info, document, KEDU_5_5_NAMESPACE)
            except Exception:
                print(f'{test_item = }')
                raise

    def test_malformed_document(self):
        user_id = '<II><p1></p1><p2></p2><p3></p3><p6></p6><p7></p7><p8></p8><p9></p9></II>'
        for i in range(0, 2):
            document = XML(self.xml.format(namespace=KEDU_5_5_NAMESPACE, user_id=(user_id * i)))
            if i == 1:
                _ = find_user_info(document, KEDU_5_5_NAMESPACE)
            else:
                self.assertRaisesRegex(AssertionError, 'Malformed ZUS DRA document, '
                                                       f'expected single user id data entry, found: {i}!',
                                       find_user_info,
                                       document,
                                       KEDU_5_5_NAMESPACE)

    def test_add_id(self):
        user_id = '<II><p1></p1><p2></p2><p3></p3><p6></p6><p7></p7><p8></p8><p9></p9></II>'
        expected = b'<II xmlns="http://www.zus.pl/2022/KEDU_5_5" ' \
                   b'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' \
                   b'<p1/><p2/><p3/><p4>aaa</p4><p5>bbb</p5><p6/><p7/><p8/><p9/></II>'
        document = XML(self.xml.format(namespace=KEDU_5_5_NAMESPACE, user_id=user_id))
        user_info_entry = find_user_info(document, KEDU_5_5_NAMESPACE)
        user_info_entry = add_user_id_data(user_info_entry, 'aaa', 'bbb')
        self.assertEqual(xml_to_string(user_info_entry), expected)

    def test_load_xml(self):
        content = self.xml.format(namespace=KEDU_5_5_NAMESPACE, user_id='')
        document = XML(content)
        with unittest.mock.patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=content):
            dra = load_dra_file(Path('dra.xml'))
            self.assertEqual(xml_to_string(dra), xml_to_string(document))

    def test_save_xml(self):
        content = self.xml.format(namespace=KEDU_5_5_NAMESPACE, user_id='')
        document = xml_from_string(content).getroottree()
        write_mock = unittest.mock.mock_open()
        with unittest.mock.patch('builtins.open', write_mock):
            output = Path('dra.xml')
            save_dra_file(document, output)
            write_mock.assert_called_once_with(output, mode='wb')
            write_mock().write.assert_called_once_with(xml_to_string(document))


if __name__ == '__main__':
    unittest.main()
