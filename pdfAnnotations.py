#!/usr/bin/env python3

import argparse
from typing import Final

from PyPDF2 import PdfFileReader, PdfFileWriter
from PyPDF2.generic import (ArrayObject, FloatObject, createStringObject)
# local lib
from colorfulPrint import print_in_green

# set command-line argument parser
arg_parser = argparse.ArgumentParser(description='Show and update PDF Annotations',
                                     epilog="""\
Examples:
- Print all the annotations
    python3 <this script> input.pdf
- Update the border of all the annotations of subtype '/Link' from red to blue.
  (See PDF Reference v1.7, Sec. 8.4 "Annotations" for more info.)
    python3 <this script> --update Link C '[1,0,0]' '[0,0,1]' --write input.pdf""",
                                     formatter_class=argparse.RawDescriptionHelpFormatter, )
arg_parser.add_argument('input',
                        help='pdf file name')
arg_parser.add_argument('--pages',
                        help='page ranges (page number is 0 based). default: every page')
# arg_parser.add_argument('--entry',
#                         default=['/A', '/C', '/CA'],
#                         dest='entries',
#                         metavar='/ENTRY',
#                         help='add printed entry, accumulated. default [\'/A\', \'/C\', \'/CA\']',
#                         action='append')
arg_parser.add_argument('--update', nargs=4, action='append',
                        dest='update_rules',
                        metavar=('/Subtype', '/ENTRY', 'old', 'new'),
                        help='update annotations by subtype and entry filters, accumulated')
arg_parser.add_argument('--dry', action='store_const', const=True, default=False,
                        help='do not write updated pdf to new file. default: False')


def parse_page_ranges(pages, max_page):
    if pages is None:
        rst = range(max_page)
    else:
        rst = []
        for p_range in pages.split(','):
            if '-' not in p_range:
                p_range = int(p_range)
                if p_range >= max_page:
                    raise ValueError(f'Page number {p_range} out of range [0, {max_page})')
                else:
                    rst.append(int(p_range))
            else:
                beg, end = p_range.split('-')
                beg, end = int(beg), int(end)
                if beg < end:
                    beg, end = end, beg
                if end >= max_page:
                    raise ValueError(f'Page range {p_range} out of range [0, {max_page})')
                else:
                    rst.extend(range(beg, end + 1))
    return rst


# get value by possible key from a dictionary
def get_xkey(d, key, default=None, wrapper=lambda x: x):
    value = d.get(key, default)
    return wrapper(value)


def get_annotations(pdf, pages_list):
    for p_num in pages_list:
        page = pdf.getPage(p_num)

        annots = page.get('/Annots', None)
        if annots is None:
            continue

        for annot in annots.getObject():
            yield p_num, annot.getObject()


def print_annotations(annotations):
    for p_num, annot in annotations:
        # print "header"
        print(f"Page: {print_in_green(p_num)} Type: {get_xkey(annot, '/Subtype', wrapper=print_in_green)}")

        # print selective entries
        entries = {'/C': 'color', '/CA': 'opacity', '/A': 'action'}
        for key, note in entries.items():
            if key in annot:
                print(f"  {key} \t({note}):\t {get_xkey(annot, key)}")

        # print all entries
        # for i in annot:
        #     if i != '/Subtype':
        #         print(f"  {i}: {annot[i]}")


ENTRY_HANDLERS: Final = {
    '/C': lambda c: ArrayObject(map(lambda x: FloatObject(x), eval(c))),
    '/CA': lambda c: ArrayObject(map(lambda x: FloatObject(x), eval(c))),
}


def update_annotations(annotations, subtype, entry, old_value, new_value):
    # normalize
    if not subtype.startswith('/'):
        subtype = '/' + subtype
    if not entry.startswith('/'):
        entry = '/' + entry
    handler = ENTRY_HANDLERS.get(entry, lambda x: x)
    old_value = handler(old_value)
    new_value = handler(new_value)

    print(f'Update {print_in_green(subtype)} annotation: {entry} = {old_value} -> {entry} = {new_value}')

    for p_num, annot in annotations:
        if annot['/Subtype'] == subtype and entry in annot and annot[entry] == old_value:
            print(f"  Page: {print_in_green(p_num)}, /A (action): {get_xkey(annot, '/A')}")

            # to update, both the key and value must be a subclass of PdfObject
            annot[createStringObject(entry)] = new_value


if __name__ == '__main__':
    # args, args_unknown = arg_parser.parse_known_args()
    args = arg_parser.parse_args()

    pdf_reader = PdfFileReader(args.input)

    MAX_PAGE: Final = pdf_reader.getNumPages()
    pages_list = parse_page_ranges(args.pages, MAX_PAGE)

    # print
    annotations = get_annotations(pdf_reader, pages_list)
    print_annotations(annotations)

    # update
    if args.update_rules:
        print()
        # print(args.update_rules)

        for subtype, entry, old_value, new_value in args.update_rules:
            annotations = get_annotations(pdf_reader, pages_list)
            update_annotations(annotations, subtype, entry, old_value, new_value)

        # data for manual test (hyperref creates '/C: [1, 0, 0]' by default
        #     RED_BORDER: Final = ArrayObject([FloatObject(i) for i in (1, 0, 0)])
        #     BLUE_BORDER: Final = ArrayObject([FloatObject(i) for i in (0, 0, 1)])

        # write
        if not args.dry:
            print()
            pdf_writer = PdfFileWriter()
            pdf_writer.cloneReaderDocumentRoot(pdf_reader)

            output = args.input.replace('.pdf', '-updated.pdf')
            with open(output, 'wb') as pdf_out:
                print(f'Write to file {output}')
                pdf_writer.write(pdf_out)
