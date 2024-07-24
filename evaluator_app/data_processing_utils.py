from config import (
    student_output_docs_dir,
    student_data_dir
)
from agents.utils import run_multithreaded_handler
import os



def ocr_doc(doc_path):
    print(f"OCR-ing {doc_path}")

    assert os.path.isfile(doc_path), f"File {doc_path} not found"
    # OCR Logic

    ocr_doc_path = os.path.join(
        os.path.dirname(doc_path), 
        student_output_docs_dir, 
        os.path.basename(doc_path).replace('.pdf', '.txt')
    )
    if os.path.exists(ocr_doc_path):
        print(f"OCR already done for {doc_path}")
        return
    
    ocr_contents = "This is the OCR content of the document"
    with open(ocr_doc_path, 'w') as f:
        f.write(ocr_contents)
    print(f"OCR Completed for {doc_path}")



def ocr_student_documents(student_id):
    student_docs_dir = os.path.join(student_data_dir, student_id)
    ocr_docs_dir = os.path.join(student_docs_dir, student_output_docs_dir)
    os.makedirs(ocr_docs_dir, exist_ok=True)

    docs_to_ocr = [
        os.path.join(student_docs_dir, doc)
        for doc in os.listdir(student_docs_dir)
        if doc.endswith('.pdf')
            and os.path.isfile(os.path.join(student_docs_dir, doc))
            # and os.path.exists(os.path.join(ocr_docs_dir, doc.split('.')[0] + '.txt'))
    ]   

    print(docs_to_ocr)

    run_multithreaded_handler(docs_to_ocr, ocr_doc, num_workers=4)