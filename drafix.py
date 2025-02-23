import re

import lxml.etree as et
import argparse
from pathlib import Path


KEDU_5_5_NAMESPACE = 'http://www.zus.pl/2022/KEDU_5_5'
ID_CARD = r'[A-Z]{3}\d{6}'
PASSPORT = r'[A-Z]{2}\d{7}'


def load_dra_file(path: Path) -> et.ElementTree:
    print(f'Opening {path}')
    with open(path, encoding='utf-8') as file:
        return et.parse(file)


def find_user_info(document: et.ElementTree, namespace: str) -> et.ElementTree:
    actual_namespace = document.xpath('namespace-uri(.)')
    assert actual_namespace == namespace, (f'Actual namespace "{actual_namespace}" differs than expected one '
                                           f'"{namespace}", document cannot be processed')
    user_id_data = document.xpath('/zus:KEDU/zus:ZUSDRA/zus:II', namespaces={'zus': namespace})
    assert len(user_id_data) == 1, (f'Malformed ZUS DRA document, expected single user id data entry, '
                                    f'found: {len(user_id_data)}!')
    return user_id_data[0]


def add_user_id_data(element: et.ElementTree, document_type: str, document_id: str) -> et.ElementTree:
    print('Patching')

    for idx, data in enumerate((document_type, document_id), start=3):
        item = et.Element(f'p{idx + 1}')
        item.text = data
        element.insert(idx, item)
    return element


def save_dra_file(document: et.ElementTree, name: Path) -> None:
    print(f'Writing to {name}')
    with open(name, mode='wb') as file:
        document.write(file)

def get_document_type(document_id: str) -> str:
    if re.match(ID_CARD, document_id):
        return '1'
    if re.match(PASSPORT, document_id):
        return '2'
    raise Exception(f'Unknown document format for document id "{document_id}"!')


def main() -> None:
    parser = argparse.ArgumentParser(description='Fix DRA file generated by inFakt')
    parser.add_argument('document_id', help='ID card or passport number')
    parser.add_argument('dra_file', help='DRA file name')
    parser.add_argument('-n', '--no-backup', help='Does not create backup file', action='store_true')
    parser.add_argument('-d', '--debug', help='Debug mode', action='store_true')
    args = parser.parse_args()

    dra_file = Path(args.dra_file)
    document = load_dra_file(dra_file)

    document_id = args.document_id.strip().upper()
    document_type = get_document_type(document_id)

    user_id_entry = find_user_info(document, KEDU_5_5_NAMESPACE)
    add_user_id_data(user_id_entry, document_type, document_id)

    if args.debug:
        print(et.tostring(user_id_entry, pretty_print=True).decode('utf-8'))

    fixed_dra_file = dra_file if args.no_backup else Path(dra_file.parent, f'{dra_file.stem}_new{dra_file.suffix}')

    save_dra_file(document, fixed_dra_file)
    print('Done')


if __name__ == '__main__':
    main()
