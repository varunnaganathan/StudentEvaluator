from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from typing import List, Union
from storage.data import (
    Student, 
    StudentDocument, 
    University, 
    UniversityCountry, 
    UniversityCourse
)
from tqdm.auto import tqdm
from prompting.templates import (
    REQUIREMENTS_STRUCTURING_SYSTEM_PROMPT, 
    STUDENT_CONTENT_EXTRACTION_SYSTEM_PROMPT, 
    STUDENT_QUALIFICATION_EVALUATION_SYSTEM_PROMPT
)
from settings import db_file
from storage.manager import DatabaseManager
from storage.data import Student
from handlers.uni_handlers.base import get_uni_handler
from prompting.generator import (
    get_doc_content_ext_prompt, 
    get_requirements_structuring_prompt, 
    student_evaluation_prompt
)
from agents.utils import get_llm_response, run_multithreaded_handler

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


    def add_student(self, student: dict):
        student = Student(**student)
        self.db_manager.add_student(student)

    def retrieve_student(self, student_id: str):
        return self.db_manager.retrieve_student(student_id)
    

    def add_university_courses(self):
        courses = self.university_data_store.courses
        for course_name, requirements in courses.items():
            self.add_univerisity_course(course_name, requirements)
    

    def retrieve_course(self, course_name):
        university_id = self.university_data_store.website
        return self.db_manager.retrieve_course(university_id, course_name)
    

    def update_course(self, course: UniversityCourse):
        self.db_manager.update_course(course)


    def add_univerisity_course(self, course_name, entry_requirements):
        university_id = self.university_data_store.website
        university_course = UniversityCourse(
            name=course_name,
            entry_req=entry_requirements,
            uni_id=university_id
        )
        self.db_manager.add_univerisity_course(university_course)
            

    def add_university_countries(self):
        countries = self.university_data_store.countries
        for country_name, requirements in countries.items():
            self.add_university_country(country_name, requirements)


    def add_university_country(self, country_name, entry_requirements):
        university_id = self.university_data_store.website
        university_country = UniversityCountry(
            uni_id=university_id,
            country_name=country_name,
            entry_req=entry_requirements
        )
        self.db_manager.add_university_country(university_country)


    def retrieve_country(self, country_name):
        university_id = self.university_data_store.website
        return self.db_manager.retrieve_country(university_id, country_name)


    def update_country(self, country):
        self.db_manager.update_country(country)


    def add_uni_courses_str_handler(self, uni_course: UniversityCourse):
        _ = self.get_course_requirements_str(uni_course)
        assert uni_course.entry_req_json is not None, f"Course {uni_course.name} requirements not found"
        self.db_manager.update_course(
            uni_course
        )


    def add_university_courses_structure(self, parallel=True, overwrite=False):
        uni_courses = self.db_manager.retrieve_university_courses(self.university_data_store.website)
        if parallel:
            courses = [
                uni_course for uni_course in uni_courses 
                if uni_course.entry_req_json is None or overwrite
            ]
            run_multithreaded_handler(
                courses,
                handler=self.add_uni_courses_str_handler
            )

        else:
            for uni_course in tqdm(uni_courses, desc='Adding courses structure'):
                if uni_course.entry_req_json is None or overwrite:
                    self.add_uni_courses_str_handler(uni_course)


    def add_uni_countries_str_handler(self, uni_country: UniversityCountry):
        _ = self.get_country_requirements_str(uni_country)
        assert uni_country.entry_req_json is not None, f"Country {uni_country.country_name} requirements not found"
        self.db_manager.update_country(
            uni_country
        )

    def add_university_countries_structure(self, parallel=True, overwrite=False):
        uni_countries = self.db_manager.retrieve_university_countries(self.university_data_store.website)
        if parallel:
            countries = [
                uni_country for uni_country in uni_countries 
                if uni_country.entry_req_json is None or overwrite
            ]
            run_multithreaded_handler(
                countries,
                handler=self.add_uni_countries_str_handler
            )
        else:
            for uni_country in tqdm(uni_countries, desc='Adding countries structure'):
                if uni_country.entry_req_json is None or overwrite:
                    self.add_uni_countries_str_handler(uni_country)


    def add_university(self, university_name):
        university_id = self.university_data_store.website
        university = University(
            website=university_id,
            name=university_name
        )
        
        self.db_manager.add_university(university)
    

    def get_course_requirements_str(self, uni_course: UniversityCourse):
        assert uni_course.name in self.university_data_store.courses, f"Course {uni_course.name} not found"
        req_json: str = uni_course.entry_req_json if uni_course.entry_req_json else self.get_course_requirements(uni_course)
        course_entry_requirements = f"\nCourse {uni_course.name} Requirements: {req_json}"
        return course_entry_requirements
    

    def get_country_requirements_str(self, uni_country: UniversityCountry):
        assert uni_country.country_name in self.university_data_store.countries, f"Country {uni_country.country_name} not supported by University"
        req_json: str = uni_country.entry_req_json if uni_country.entry_req_json else self.get_country_requirements(uni_country)
        country_entry_requirements = f"\nCountry {uni_country.country_name} Requirements: {req_json}"
        return country_entry_requirements
    
        
    def generate_evaluation_prompt(
            self, 
            student: Student, 
            mode = EvalMode.COURSE.value
        ):
        requirements = ""
        if mode in [EvalMode.COURSE.value, EvalMode.HYBRID.value]:
            course = self.retrieve_course(student.course)
            requirements += self.get_course_requirements_str(course)

        elif mode in [EvalMode.COUNTRY.value, EvalMode.HYBRID.value]:
            country = self.retrieve_country(student.country)
            requirements += self.get_country_requirements_str(country)


        student_docs = self.get_student_application(student.student_id, requirements)

        prompt = student_evaluation_prompt(
            student,
            student_docs,
            requirements,
        )

        return prompt


    def add_student_document(self, doc: dict):
        doc = StudentDocument(**doc)
        self.db_manager.add_student_doc(doc)
    

    def add_student_documents(self, docs: List[dict]):
        for doc in tqdm(docs, desc="Adding student documents"):
            self.add_student_document(doc)
    
    def get_student(self, student_id):
        return self.db_manager.retrieve_student(student_id)

    def get_student_application(self, student_id: Union[str, List], requirements):
        def get_docs_content(sid):
            docs = self.db_manager.retrieve_student_docs(sid)
            if not docs:
                print(f"No documents found for student {sid}")
                return None
            docs_to_structure = [d.content for d in docs if d.summary is None]
            doc_content_ext_prompts = [
                get_doc_content_ext_prompt(d.content, requirements) 
                for d in docs_to_structure
            ]
            doc_responses = run_multithreaded_handler(
                doc_content_ext_prompts,
                system_prompt = STUDENT_CONTENT_EXTRACTION_SYSTEM_PROMPT
            )
            for r, d in zip(doc_responses, docs_to_structure):
                d.summary = r
                self.db_manager.update_student_doc(sid, d)
            
            return "\n\n".join([d.summary for d in docs])
        
        if isinstance(student_id, str):
            return get_docs_content(student_id)
        
        elif isinstance(student_id, List):
            return [get_docs_content(_id) for _id in student_id]


    # def get_docs_with_summaries(self, student_id: Union[str, List]):
    #     student_documents = get_student_docs(student_id)
    #     add_student_doc_prompts(student_documents)
    #     add_student_summarized_docs(student_documents)

    #     return student_documents


    # def summarize_and_add_docs(self, student_id: str):
    #     student_documents = get_student_docs(student_id)
    #     add_student_doc_prompts(student_documents)
    #     docs_to_summarize = [d for d in student_documents\
    #         if not self.db_manager.check_document_exists(student_id, d)]
    #     if len(docs_to_summarize):
            # add_student_summarized_docs(docs_to_summarize)
    #         self.add_student_documents(student_id, docs_to_summarize)
    
    
    # def summarize_and_add_student_docs(self, student_id: Union[str, List]):
    #     if isinstance(student_id, str):
    #         self.summarize_and_add_docs(student_id)
        
    #     elif isinstance(student_id, List):
    #         for sid in student_id:
    #             self.summarize_and_add_docs(sid)


    def evaluate_student(self, student: Student, mode = EvalMode.COUNTRY.value):
        student_data_prompt = self.generate_evaluation_prompt(student, mode)
        
        print(student_data_prompt)
        student_eval_response = get_llm_response(
            student_data_prompt, 
            system_prompt=STUDENT_QUALIFICATION_EVALUATION_SYSTEM_PROMPT
        )
        print(student_eval_response)
        return student_eval_response


    def get_country_requirements(self, country: UniversityCountry):        
        requirements_structuring_prompt = get_requirements_structuring_prompt(
            country.entry_req, country_name=country.country_name
        )
        structured_requirements = get_llm_response(
            requirements_structuring_prompt,
            system_prompt=REQUIREMENTS_STRUCTURING_SYSTEM_PROMPT
        )
        country.entry_req_json = structured_requirements
        self.update_country(country)
        structured_requirements = json.dumps(json.loads(structured_requirements), indent=4)
        return structured_requirements


    def get_course_requirements(self, uni_course: UniversityCourse):
        requirements_structuring_prompt = get_requirements_structuring_prompt(
            uni_course.entry_req, course_name=uni_course.name
        )
        structured_requirements = get_llm_response(
            requirements_structuring_prompt,
            system_prompt=REQUIREMENTS_STRUCTURING_SYSTEM_PROMPT
        )
        uni_course.entry_req_json = structured_requirements
        self.update_course(uni_course)
        structured_requirements = json.dumps(json.loads(structured_requirements), indent=4)
        return structured_requirements