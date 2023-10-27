# pdf-util

Script
  - `pdfAnnotations.py` Show and update PDF Annotations, require [`pypdf`](https://pypi.org/project/pypdf/) and helper `colorfulPrint.py`

Helper
  - `colorfulPrint.py` A simple wrapper of [`colorama`](https://pypi.org/project/colorama/)

------

Useful links of used PDF libraries
  - `pypdf`
    - doc: https://pypdf.readthedocs.io/en/latest/ (insufficient)
    - repo: https://github.com/py-pdf/pypdf
    - [need recheck] known problem(s):
      - `PdfFileWriter.cloneDocumentFromReader()` is buggy ([`PyPDF#219`][pypdf#219])

[pypdf#219]: https://github.com/mstamy2/PyPDF2/issues/219

Alternative libraries
  - `PyMuPDF`
    - repo: https://github.com/pymupdf/PyMuPDF
    - doc: https://readthedocs.org/projects/pymupdf/
