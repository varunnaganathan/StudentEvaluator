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

import utils, llm_filter_info
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
    def __init__(self, id, docs_dir, email):
        self.id = id
        self.docs_dir = docs_dir
        self.email = email
        self.docsData = {}

    def get_Docdata(self, filepath):
        # use doc class and get text for it
        doc = studentDoc.studentDoc(filepath)
        return doc.getDocData()

    def getLLMSummaryDocData(self, docpath, data):
        # make openai call here
        return utils.get_llm_response(
             user_prompt="",
             task_prompt="",
             system_prompt=""
        )

    # get all docs data in given student dir
    # also get llm summarized version of them
    def get_Docsdata(self):
        for path in os.listdir(self.docs_dir):
            # check if current path is a file
            if os.path.isfile(os.path.join(self.docs_dir, path)) and str(os.path.join(self.docs_dir, path)).endswith(".pdf"):
                fname = os.path.join(self.docs_dir, path)
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

    
    def writeDocsData(self):
         outdir = self.docs_dir + "outputDocs/"
         for k in self.docsData:
              outfile = outdir + ((k.split("/")[-1]).rstrip(k.split(".")[-1])) + "txt"
              print(outfile)
              os.makedirs(os.path.dirname(outfile), exist_ok=True)
              f = open(outfile,'w')
              f.write("file name = "+k)
              f.write(self.docsData[k])
              f.close()

    def writeDocsDataLLM(self):
         outdir = self.docs_dir + "outputDocsLLM/"
         for k in self.docsDataLLM:
              outfile = outdir + ((k.split("/")[-1]).rstrip(k.split(".")[-1])).strip('.') + "_llm.txt"
              print(outfile)
              os.makedirs(os.path.dirname(outfile), exist_ok=True)
              f = open(outfile,'w')
              f.write("file name = "+k)
              f.write(self.docsDataLLM[k])
              f.close()
    
if __name__ == "__main__":
     docs_dir = "./sample/10445379/"
     d = StudentData(id="10445379",docs_dir=docs_dir, email="hello")
     d.get_Docsdata()
     print(d.docsData)
     d.writeDocsData()
     d.writeDocsDataLLM()


    

                