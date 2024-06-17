student_doc_parent_dir = "./StudentData/"
uni_requirement_parent_dir = "./universityData/"

# To read the PDF
import PyPDF2
import llm_filter_info
# To analyze the PDF layout and extract text
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LTTextContainer, LTChar, LTRect, LTFigure
# To extract text from tables in PDF
import pdfplumber, studentDoc
# To extract the images from the PDFs
from PIL import Image
from pdf2image import convert_from_path
# To perform OCR to extract text from images 
import pytesseract 
# To remove the additional created files
import os


# for google vision
# for vision model
from google.cloud import vision
from typing import Sequence
import pickle


"""
We create the db for student data here. 

student data
1. all docs for a student in a subdir by student id
2. links for all data to their docs and sources
3. A rag bot on student data 

"""


class StudentData():

    docsData = {}
    docsDataLLM = {}
    def __init__(self, id, docs, email):
        self.id = id
        self.docs = docs
        self.email = email
        self.docsData = {}

    def get_Docdata(self, filepath):
        # use doc class and get text for it
        doc = studentDoc(filepath)
        return doc.getDocData()

    def getLLMSummaryDocData(self, docpath, data):
        # make openai call here
        return ""

    # get all docs data in given student dir
    # also get llm summarized version of them
    def get_Docsdata(self, dir_path):
        for path in os.listdir(dir_path):
            # check if current path is a file
            if os.path.isfile(os.path.join(dir_path, path)) and str(os.path.join(dir_path, path)).endswith(".pdf"):
                fname = os.path.join(dir_path, path)
                self.docsData[fname] = self.get_Docdata(fname)
                self.docsDataLLM[fname] = self.getLLMSummaryDocData(fname, self.docsData[fname])

    # when new doc is added later for a student
    async def updateDocsData(self, dir_path, file_path):
        if os.path.isfile(os.path.join(dir_path, file_path)) and str(os.path.join(dir_path, file_path)).endswith(".pdf"):
                fname = os.path.join(dir_path, file_path)
                self.docsData[fname] = self.get_Docdata(fname)
                self.docsDataLLM[fname] = self.getLLMSummaryDocData(fname, self.docsData[fname])


    async def deleteDocsData(self, dir_path, file_path):
        if os.path.isfile(os.path.join(dir_path, file_path)) and str(os.path.join(dir_path, file_path)).endswith(".pdf"):
                fname = os.path.join(dir_path, file_path)
                self.docsData[fname] = []
                self.docsDataLLM[fname] = []
