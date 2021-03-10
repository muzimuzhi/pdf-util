#!/usr/bin/env python3

import argparse
from decimal import Decimal
from typing import Final

from PyPDF2 import PdfFileReader, PdfFileWriter
from PyPDF2.generic import (ArrayObject, DecodedStreamObject, FloatObject, createStringObject)
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
arg_parser.add_argument('--print-all', action='store_const', const=True, default=False,
                        help='print every entries of an annotation')
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


def floatobject__repr__(self):
    if self == self.to_integral():
        return str(self.quantize(Decimal(1)))
    else:
        # Standard formatting adds useless extraneous zeros.
        o = '%.6f' % self  # <<< CHANGED HERE
        # Remove the zeros.
        while o and o[-1] == '0':
            o = o[:-1]
        return o


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


# get value by possible key from a DictionaryObject
def get_entry(d, key, default=None, wrapper=lambda x: x):
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
        print(f"Page: {print_in_green(p_num)} Type: {get_entry(annot, '/Subtype', wrapper=print_in_green)}")

        if args.print_all:
            for i in annot:
                if i != '/Subtype':
                    print(f"  {i}: {annot[i]}")
        else:
            # print selective entries
            entries = {'/C': 'color', '/CA': 'opacity', '/A': 'action'}
            for key, note in entries.items():
                if key in annot:
                    print(f"  {key} \t({note}):\t {get_entry(annot, key)}")


ENTRY_HANDLERS: Final = {
    '/C': lambda c: ArrayObject(map(lambda x: FloatObject(x), eval(c) if isinstance(c, str) else c)),
    '/CA': lambda c: ArrayObject(map(lambda x: FloatObject(x), eval(c) if isinstance(c, str) else c)),
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

    print(f'Updated {print_in_green(subtype)} annotation: {entry} = {old_value} -> {entry} = {new_value}')

    for p_num, annot in annotations:
        if annot['/Subtype'] == subtype and entry in annot and repr(annot[entry]) == repr(old_value):
            # use repr() to compare FloatObject, a decimal.Decimal wrapper
            print(f'  Page: {print_in_green(p_num)}, /A (action): {get_entry(annot, "/A")}')

            # to update, both the key and value should be instances of PdfObject
            annot[createStringObject(entry)] = new_value

            # replace another color deeply stored in '/AP' of '/Highlight' subtype (created by adobe reader), and
            # this color spec is part of a content stream (in python, bytes object) of graphics objects
            if subtype == annot['/Subtype'] == '/Highlight' and entry == '/C':
                # 1. get stream
                stream: DecodedStreamObject = \
                    annot['/AP']['/N']['/Resources']['/XObject']['/MWFOForm']['/Resources']['/XObject']['/Form']

                # 2. convert stream to str
                str_ = stream.getData().decode()
                # >>> str_
                # 1 0.819611 0 rg                                           % set non-stroking color
                # 0.6227 w                                                  % set line width (in multiples of 1/72 inch)
                # 133.768 556.1424 m                                        % move to
                # 131.4198 558.4906 131.4198 563.7568 133.768 566.105 c     % curve to
                # 161.6074 566.105 l                                        % line to
                # 163.9556 563.7568 163.9556 558.4906 161.6074 556.1424 c
                # f                                                         % fill path

                # 3. replace color
                def color_repr(color: ArrayObject, mode: str):
                    color_spec = [repr(c) for c in color]
                    color_spec.append(mode)
                    return ' '.join(color_spec)

                if len(old_value) == 3:
                    old_repr = color_repr(old_value, 'rg')
                    new_repr = color_repr(new_value, 'rg')
                else:
                    raise ValueError(f'Color length {len(old_value)} not yet supported')

                if old_repr in str_:
                    str_new = str_.replace(old_repr, new_repr)
                    print(f'  Updated /AP (appearance dictionary) also: {old_repr} -> {new_repr}')
                else:
                    raise ValueError(f'Color spec "{old_repr}" not found in stream\n{str_}')

                # 4. convert back to bytes and finally update stream
                stream.setData(str_new.encode())


if __name__ == '__main__':
    # redefine FloatObject.__repr__, use 6 decimals instead of 5
    # because Adobe uses 6 in annotation color arrays.
    FloatObject.__repr__ = floatobject__repr__

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

        for subtype, entry, old_value, new_value in args.update_rules:
            annotations = get_annotations(pdf_reader, pages_list)
            update_annotations(annotations, subtype, entry, old_value, new_value)

        # write
        if not args.dry:
            print()
            pdf_writer = PdfFileWriter()
            pdf_writer.cloneReaderDocumentRoot(pdf_reader)

            output = args.input.replace('.pdf', '-updated.pdf')
            with open(output, 'wb') as pdf_out:
                print(f'Write to file {output}')
                pdf_writer.write(pdf_out)
