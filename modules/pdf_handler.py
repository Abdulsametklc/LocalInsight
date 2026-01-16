from PyPDF2 import PdfReader

def get_pdf_text(pdf_docs):
    """Yüklenen PDF dosyalarından metin çıkarır."""
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            t = page.extract_text()
            if t: text += t
    return text