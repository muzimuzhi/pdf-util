# pdf-util

Script
  - `pdfAnnotations.py` Show and update PDF Annotations, require [`PyPDF2`](https://pypi.org/project/PyPDF2/) and helper `colorfulPrint.py`

Helper
  - `colorfulPrint.py` A simple wrapper of [`colorama`](https://pypi.org/project/colorama/)

------

Useful links of used PDF libraries
  - `PyPDF2`
    - doc: https://pythonhosted.org/PyPDF2/ (insufficient)
    - repo: https://github.com/mstamy2/PyPDF2
    - known problem(s):
      - `PdfFileWriter.cloneDocumentFromReader()` is buggy ([`PyPDF#219`][pypdf#219])

[pypdf#219]: https://github.com/mstamy2/PyPDF2/issues/219

Alternative libraries
  - `PyMuPDF`
    - repo: https://github.com/pymupdf/PyMuPDF
    - doc: https://readthedocs.org/projects/pymupdf/
  - `PyPDF4` https://github.com/claird/PyPDF4 (haven't used, not active maintained)
