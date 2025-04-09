"""
    Converts identity document (ID card or passport) to the form required by ZUS KEDU
"""
import re

ID_CARD_REGEX = r'[A-Z]{3}\d{6}'
PASSPORT_REGEX = r'[A-Z]{2}\d{7}'


class IdentityDocument:
    """
        Polish identity document
    """
    _number: str | None = None
    _type: str | None = None

    def __init__(self, document_number: str):
        self._document_number = document_number

    @property
    def number(self) -> str:
        """
        :return: Document number in the form required by ZUS KEDU
        """
        if self._number is None:
            self._number = self._document_number.strip().upper()
        return self._number

    @property
    def type(self) -> str:
        """
        :return: Document type ('1' for ID card, '2' for passport) in the form required by ZUS KEDU
        """
        if self._type is None:
            if re.match(ID_CARD_REGEX, self.number):
                self._type = '1'
            elif re.match(PASSPORT_REGEX, self.number):
                self._type = '2'
            else:
                raise RuntimeError(f'Unknown document format for document id "{self._document_number}"!')
        return self._type
