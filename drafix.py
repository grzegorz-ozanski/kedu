import lxml.etree as et
import argparse
from pathlib import Path


KEDU_5_5_NAMESPACE = 'http://www.zus.pl/2022/KEDU_5_5'


def load_dra_file(path: Path) -> et.ElementTree:
    print(f'Opening {path}')
    with open(path, encoding='utf-8') as file:
        return et.parse(file)


def find_user_info(document: et.ElementTree, expected_namespace: str) -> et.ElementTree:
    actual_namespace = document.xpath('namespace-uri(.)')
    assert actual_namespace == expected_namespace, (f'Actual namespace "{actual_namespace}" differs than expected one '
                                                    f'"{expected_namespace}", document cannot be processed')
    return document.xpath('/zus:KEDU/zus:ZUSDRA/zus:II', namespaces={'zus': expected_namespace})[0]


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


def main() -> None:
    parser = argparse.ArgumentParser(description='Fix DRA file generated by inFakt')
    parser.add_argument('dra_file', help='DRA file name')
    parser.add_argument('-i', '--id', help='Add provided Polish ID card')
    parser.add_argument('-p', '--passport', help='Add provided Polish passport')
    parser.add_argument('-n', '--no-backup', help='Does not create backup file', action='store_true')
    parser.add_argument('-d', '--debug', help='Debug mode', action='store_true')
    args = parser.parse_args()

    if (args.id and args.passport) or not (args.id or args.passport):
        print("Needs exactly one argument '--id' or '--passport'")
        parser.print_help()
        exit(2)

    dra_file = Path(args.dra_file)
    document = load_dra_file(dra_file)

    document_type = '1' if args.id else '2'
    document_id = args.id if args.id else args.passport

    user_id_entry = find_user_info(document, KEDU_5_5_NAMESPACE)
    add_user_id_data(user_id_entry, document_type, document_id)

    if args.debug:
        print(et.tostring(user_id_entry, pretty_print=True).decode('utf-8'))

    fixed_dra_file = dra_file if args.no_backup else Path(dra_file.parent, f'{dra_file.stem}_new{dra_file.suffix}')

    save_dra_file(document, fixed_dra_file)
    print('Done')


if __name__ == '__main__':
    main()
