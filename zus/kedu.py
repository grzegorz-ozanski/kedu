"""
    ZUS KEDU handler
"""
from pathlib import Path
from typing import Optional

import lxml.etree as et

from .identity_document import IdentityDocument


class KEDU:
    """
        ZUS KEDU document
    """
    path: Path | None
    xml: et.ElementTree
    patched: bool = False

    def __init__(self):
        self.path: Path | None = None
        self.xml: Optional[et.ElementTree] = None

    def _parse_user_data(self):
        namespace = self.xml.xpath('namespace-uri(.)')
        users = self.xml.xpath('/zus:KEDU/zus:*/zus:II', namespaces={'zus': namespace})
        assert len(users) > 0, 'Malformed ZUS KEDU document, expected at least one user id data entry, found 0!'
        return users

    def load(self, path: Path | str):
        """
        Load ZUS DRA file as XML
        """
        self.path = Path(path)
        print(f'Opening {self.path}')
        with open(self.path, encoding='utf-8') as file:
            self.xml = et.parse(file)
        self._parse_user_data()

    def add_id_document(self, id_document: IdentityDocument, debug: bool = False) -> None:
        """
        Adds user ID document to ZUS KEDU
        :param id_document: ID document
        :param debug: produce debug output
        """
        self.patched = False
        for user_data in self._parse_user_data():
            if (any(child.tag.endswith('p4') for child in user_data) and
                any(child.tag.endswith('p5') for child in user_data)):
                print(
                    f'WARNING: element {et.QName(user_data).localname} of {et.QName(user_data.getparent()).localname} '
                    f'already contains valid user ID data, patching skipped')
                continue

            print('Patching')
            for idx, data in enumerate((id_document.type, id_document.number), start=3):
                item = et.Element(f'p{idx + 1}')
                item.text = data
                user_data.insert(idx, item)
                self.patched = True

            if debug:
                print(et.tostring(user_data, pretty_print=True).decode('utf-8'))

    def save(self, path: Path | str | None = None, backup: bool = True) -> bool:
        """

        :param path:
        :param backup:
        """
        if not self.patched:
            print(f'Nothing was changed, not writing')
            return False
        if path:
            file_name = Path(path)
        else:
            file_name = Path(self.path.parent, f'{self.path.stem}_new{self.path.suffix}') if backup else self.path
        print(f'Writing to {file_name}')
        with open(file_name, mode='wb') as file:
            self.xml.write(file)
        return True
