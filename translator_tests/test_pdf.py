# test_pdf.py
import PyPDF2

pdf_path = "contracts/Simple Rental Agreement v1.pdf"

with open(pdf_path, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    print(f"✓ PDF has {len(pdf_reader.pages)} pages")
    
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    
    print(f"✓ Extracted {len(text)} characters")
    print(f"\nFirst 200 characters:\n{text[:200]}")