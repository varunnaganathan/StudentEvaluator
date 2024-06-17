from typing import List

from tqdm.auto import tqdm
from settings import db_file
from storage.manager import DatabaseManager
from handlers.uni_handlers.base import get_uni_handler
from prompting.generator import student_evaluation_prompt
from parsing.pdf_parser import parse_pdf
from agents.utils import get_llm_response, get_llm_response_multithreaded


class DatabaseAgent:
    def __init__(
            self, 
            uni_name,
            db_file = db_file,
            db_overwrite=False,
        ):
        self.university_data_store = get_uni_handler(uni_name)()
        self.db_manager = DatabaseManager(file=db_file, overwrite=db_overwrite)
    
    
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
    

    def get_course_requirements(self, student_email, course_name):
        assert course_name in self.university_data_store.courses, f"Course {course_name} not found"
        _, _, country = self.db_manager.retrieve_student(student_email)

        assert country in self.university_data_store.countries, f"Country {country} not supported by University"

        university_id = self.university_data_store.website
        course_entry_requirements = f"Course: {course_name}" + self.db_manager.retrieve_course_details(
            university_id, course_name
        )
        country_entry_requirements = f"Country: {country}\n" + self.db_manager.retrieve_country_details(
            university_id,
            country
        )

        return course_entry_requirements, country_entry_requirements

        
    def generate_evaluation_prompt(self, student_email, course_name):
        course_entry_requirements, country_entry_requirements = self.get_course_requirements(
            student_email, course_name
        )

        student_doc = self.db_manager.retrieve_student_doc(student_email)
        prompt = student_evaluation_prompt(
            student_doc,
            course_entry_requirements,
            country_entry_requirements
        )

        return prompt


    def generate_evaluation_prompts(self, student_email, course_name):
        course_entry_requirements, country_entry_requirements = self.get_course_requirements(
            student_email, course_name
        )

        student_docs = self.db_manager.retrieve_student_docs(student_email)
        
        prompts = [student_evaluation_prompt(
            student_doc,
            course_entry_requirements,
            country_entry_requirements
        ) for student_doc in student_docs]

        return prompts


    def add_student_document(self, student_email, document_path: str):
        doc_contents = parse_pdf(document_path)
        self.db_manager.add_student_doc(student_email, doc_contents)
        print("Student document added successfully")
    

    def add_student_documents(self, student_email, document_paths: List):
        for document_path in tqdm(document_paths, desc="Adding student documents"):
            self.add_student_document(student_email, document_path)
    

    def evaluate_student_doc(self, student_email, course_name):
        student_data_prompt = self.generate_evaluation_prompt(student_email, course_name)
        
        student_eval_response = get_llm_response(student_data_prompt)
        return student_eval_response

    def evaluate_student_docs(self, student_email, course_name):
        student_data_prompts = self.generate_evaluation_prompts(student_email, course_name)
        
        student_eval_responses = get_llm_response_multithreaded(
            student_data_prompts, get_llm_response
        )
        return student_eval_responses