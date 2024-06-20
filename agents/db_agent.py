import os
from typing import List, Union

from tqdm.auto import tqdm
from settings import db_file
from storage.constants import DOC_SUMMARY
from storage.manager import DatabaseManager
from handlers.uni_handlers.base import get_uni_handler
from prompting.generator import student_evaluation_prompt
from agents.utils import get_llm_response
from llama_index.core.schema import Document
from agents.student_doc_summarization import add_student_doc_prompts, add_student_summarized_docs, get_student_docs

from enum import Enum

class EvalMode(Enum):
    COURSE = "course"
    COUNTRY = "country"
    HYBRID = "hybrid"


class DatabaseAgent:
    def __init__(
            self, 
            uni_name,
            db_file = db_file,
            db_overwrite=False,
        ):
        self.set_university_data_store(uni_name)
        self.db_manager = DatabaseManager(file=db_file, overwrite=db_overwrite)
    

    def set_university_data_store(self, uni_name):
        self.university_data_store = get_uni_handler(uni_name)()

    def add_student(self, s_id, student_email, first_name, last_name, student_country):
        self.db_manager.add_student(s_id, student_email, first_name, last_name, student_country)
    
    def add_university_courses(self):
        university_id = self.university_data_store.website
        courses = self.university_data_store.courses
        self.db_manager.add_university_courses(university_id, courses)
    

    def retrieve_course_details(self, course_name):
        university_id = self.university_data_store.website
        return self.db_manager.retrieve_course_details(university_id, course_name)


    def add_univerisity_course(self, course_name, entry_requirements):
        university_id = self.university_data_store.website
        self.db_manager.add_univerisity_course(university_id, course_name, entry_requirements)
        

    def retrieve_country_details(self, country_name):
        university_id = self.university_data_store.website
        return self.db_manager.retrieve_country_details(university_id, country_name)
    

    def add_university_countries(self):
        university_id = self.university_data_store.website
        countries = self.university_data_store.countries
        self.db_manager.add_university_countries(university_id, countries)


    def add_university_country(self, country_name, entry_requirements):
        university_id = self.university_data_store.website
        self.db_manager.add_university_country(university_id, country_name, entry_requirements)


    def add_university(self, university_name):
        university_id = self.university_data_store.website
        self.db_manager.add_university(university_id, university_name)
    

    def get_course_requirements(self, course_name):
        assert course_name in self.university_data_store.courses, f"Course {course_name} not found"
        
        university_id = self.university_data_store.website
        course_entry_requirements = f"\nCourse {course_name} Requirements: " + self.db_manager.retrieve_course_details(
            university_id, course_name
        )

        return course_entry_requirements
    

    def get_country_requirements(self, student_id):
        _, _, country = self.db_manager.retrieve_student(student_id)
        assert country in self.university_data_store.countries, f"Country {country} not supported by University"
        
        university_id = self.university_data_store.website
        country_entry_requirements = f"\nCountry {country} Requirements: " + self.db_manager.retrieve_country_details(
            university_id, country
        )

        return country_entry_requirements
    
        
    def generate_evaluation_prompt(self, student_id, course_name, mode = EvalMode.COURSE.value):
        entry_requirements = ""
        if mode in [EvalMode.COURSE.value, EvalMode.HYBRID.value]:
            entry_requirements += self.get_course_requirements(course_name)

        elif mode in [EvalMode.COUNTRY.value, EvalMode.HYBRID.value]:
            entry_requirements += self.get_country_requirements(student_id)


        student_doc = self.get_student_application(student_id)

        prompt = student_evaluation_prompt(
            student_doc,
            entry_requirements,
        )

        return prompt


    def add_student_document(self, student_id, doc: Document):
        self.db_manager.add_student_doc(student_id, doc)
    

    def add_student_documents(self, student_id, docs: List[Document]):
        for doc in tqdm(docs, desc="Adding student documents"):
            self.add_student_document(student_id, doc)
    

    def get_student_application(self, student_id: Union[str, List]):
        def get_student_docs(sid):
            docs = self.db_manager.retrieve_student_docs(sid)
            return "\n\n".join(docs)
        
        if isinstance(student_id, str):
            return get_student_docs(student_id)
        
        elif isinstance(student_id, List):
            return [get_student_docs(_id) for _id in student_id]


    def get_docs_with_summaries(self, student_id: Union[str, List]):
        student_documents = get_student_docs(student_id)
        add_student_doc_prompts(student_documents)
        add_student_summarized_docs(student_documents)

        return student_documents

    def summarize_and_add_docs(self, student_id: str):
        student_documents = get_student_docs(student_id)
        add_student_doc_prompts(student_documents)
        docs_to_summarize = [d for d in student_documents\
            if not self.db_manager.check_document_exists(student_id, d)]
        if len(docs_to_summarize):
            add_student_summarized_docs(docs_to_summarize)
            self.add_student_documents(student_id, docs_to_summarize)
    
    
    def summarize_and_add_student_docs(self, student_id: Union[str, List]):
        if isinstance(student_id, str):
            self.summarize_and_add_docs(student_id)
        
        elif isinstance(student_id, List):
            for sid in student_id:
                self.summarize_and_add_docs(sid)


    def evaluate_student_doc(self, student_id, course_name):
        student_data_prompt = self.generate_evaluation_prompt(student_id, course_name)
        
        student_eval_response = get_llm_response(student_data_prompt)
        return student_eval_response