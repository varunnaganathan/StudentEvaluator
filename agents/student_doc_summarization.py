from llama_index.core.schema import Document
import os
from typing import List, Union
from settings import student_data_dir, student_output_docs_dir
from prompting.templates import STUDENT_CERTIFICATE_SUMMARIZATION_PROMPT
from agents.utils import get_llm_response_multithreaded
from storage.constants import DOC_FILE_NAME, DOC_SUMMARY


def get_student_docs(student_id: Union[int, str, List]):
    if isinstance(student_id, int):
        student_id = str(student_id)
        
    def get_doc_data(sid):
        docs = list()
        for f in os.listdir(os.path.join(student_data_dir, str(sid), student_output_docs_dir)):
            content = open(os.path.join(student_data_dir, str(sid), student_output_docs_dir, f)).read()
            doc = Document(text=content, metadata={DOC_FILE_NAME: f})
            docs.append(doc)
        return docs
    
    if isinstance(student_id, str):
        return get_doc_data(student_id)
    elif isinstance(student_id, List):
        return [get_doc_data(sid) for sid in student_id]


def add_student_doc_prompts(docs: Union[List, List[List]]):
    def add_single_student_doc_prompts(student_docs):
        for i in range(len(student_docs)):
            sd = student_docs[i]
            prompt = STUDENT_CERTIFICATE_SUMMARIZATION_PROMPT.format(student_doc_content=sd.text)
            sd.metadata['prompt'] = prompt

    if isinstance(docs[0], str):
        add_single_student_doc_prompts(docs)
    
    elif isinstance(docs[0], List):
        for d in docs:
            add_single_student_doc_prompts(d)


def add_student_summarized_docs(student_docs: Union[List[Document], List[List[Document]]]):
    def add_summaries(docs: List[Document]):
        summaries = get_llm_response_multithreaded([d.text for d in docs])
        for i in range(len(docs)):
            docs[i].metadata[DOC_SUMMARY] = summaries[i]
        
        for d in docs:
            assert DOC_SUMMARY in d.metadata

    if isinstance(student_docs[0], Document):
        add_summaries(student_docs)

    elif isinstance(student_docs[0], List):
        for s_docs in student_docs:
            add_summaries(s_docs)

