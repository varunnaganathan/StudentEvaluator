import ast
from typing import List
from agents.utils import run_multithreaded_handler
from handlers.uni_handlers.base import get_uni_handler
import json
import os
from config import (
    university_data_dir, 
    student_output_docs_dir, 
    student_data_dir,
    summary_folder
)
from agents.utils import get_llm_response

from student_eval.models import *
from student_eval.db_utils import *



def get_requirements_countries(university_name="northumbria") -> List[UniversityCountry]:
    path = os.path.join(university_data_dir, university_name, "countries.json")
    if os.path.exists(path):
        return UniversityCountry.objects.filter(university__name=university_name)
    university = add_or_get_university(university_name)
    uni_handler = get_uni_handler(university_name)()
    countries: dict = uni_handler.get_countries()
    return [
        add_or_get_university_country(university, country_name, requirements)
        for country_name, requirements in countries.items()
    ]


def get_requirements_courses(university_name="northumbria") -> List[UniversityCourse]:
    path = os.path.join(university_data_dir, university_name, "courses.json")
    if os.path.exists(path):
        return UniversityCourse.objects.filter(university__name=university_name)
    university = add_or_get_university(university_name)
    uni_handler = get_uni_handler(university_name)()
    courses: dict = uni_handler.get_courses()
    return [
        add_or_get_university_course(university, course_name, requirements)
        for course_name, requirements in courses.items()
    ]


def load_university_data_from_fs(uni_name):    
    courses_fname = os.path.join(
        university_data_dir, uni_name, "courses.json"
    )
    courses: dict = json.load(open(courses_fname))

    countries_fname = os.path.join(
        university_data_dir, uni_name, "countries.json"
    )
    countries: dict = json.load(open(countries_fname))

    course_x_countries_fname = os.path.join(
        university_data_dir, uni_name, "course_x_country_requirements.json"
    )

    countriesxcourses = json.load(open(course_x_countries_fname))

    university = add_or_get_university(uni_name)


    for course, requirements in courses.items():
        add_or_get_university_course(
            university=university, 
            course_name=course, 
            requirements=requirements
        )
    for country, requirements in countries.items():
        add_or_get_university_country(
            university=university, 
            country_name=country, 
            requirements=requirements
        )

    for country_name in countriesxcourses:
        for course_name, requirements in countriesxcourses[country_name].items():
            course = add_or_get_university_course(university, course_name)
            country = add_or_get_university_country(university, country_name)
            add_or_get_countryxcourse(
                university=university, 
                country=country, 
                course=course, 
                requirements=requirements[1]
            )


def extract_country_x_course_requirements(uni_name="northumbria"):
    # parse uni req
    # get all courses and countries
    university = add_or_get_university(uni_name)

    f_name = os.path.join(
        university_data_dir, 
        uni_name, 
        "course_x_country_requirements.json"
    )
    if os.path.exists(f_name):
        load_university_data_from_fs(uni_name)
        print("University requirements already extracted. Skipping...")
        return 
    
    
    requirements_courses = get_requirements_courses(uni_name)
    requirements_countries = get_requirements_countries(uni_name)
    course_map = {course.name: course for course in requirements_courses}
    country_map = {country.name: country for country in requirements_countries}
    courses = [course.name for course in requirements_courses]
    countries = [country.name for country in requirements_countries]

    prompt_get_course_req = """
    given the requirements for entry into university below, 
    extract and summarize in very short  the fields structurally in json isolating - academic, english, work experience, documents needed and other requirements separately . 
    if there are multiple levels or types of sub courses, isolate them as well. Dont output anything else but the json and dont make up any requirement that isnt mentioned. 
    Provide any notes you have in a separate column in the json.
    here is the requirements - {course_requirement}
    """

    prompt_get_country_req = """
    You are given the requirements for entry into university below for a student from UK, 
    and rules below for a student applying from a different country - {country}, recreate above json for university requirements for same course 
    if student is from {country} by correctly mapping and altering requirements given based on the rules given . 
    Dont output anything else but the json and dont make up any requirement that is not mentioned. 
    Provide any notes you have in a separate column in the json about the replacements in entry requirements you made.
    here are the rules for a student applying from {country} - {country_requirement}
    """

    system_prompt = "You are an expert in extracting summarized information in structured json format from unstructured text"

    course_prompts = {
        course: prompt_get_course_req.format(course_requirement=requirements_courses[course])
        for course in courses
    }
    course_responses = run_multithreaded_handler(
        course_prompts, ordered=True, system_prompt=system_prompt
    )

    for course, course_response in course_responses.items():
        country_prompts = {
            country:
            prompt_get_country_req.format(
                country=country, country_requirement=requirements_countries[country]
            ) + course_response
            for country in countries if country in ["India", "Bangladesh"]
        }

        country_responses = run_multithreaded_handler(
            country_prompts, ordered=True, system_prompt=system_prompt
        )

        for country, country_response in country_responses.items():
            course, country = course_map[course], country_map[country]
            add_or_get_countryxcourse(
                university=university,
                course=course,
                country=country,
                requirements=country_response
            )
            

    # json.dump(
    #     course_x_country_requirements, 
    #     open(f_name, 'w'), 
    #     indent=4
    # )


def add_university_requirements(application: Application) -> List[UniversityCourseXCountry]:
    extract_country_x_course_requirements(uni_name=application.university.name)
    print("University requirements extracted")

    print(application.university.name, application.course.name, application.country.name)
    course_country_req = UniversityCourseXCountry.objects.get(
        university=application.university,
        course=application.course,
        country=application.country
    )
    
    if '```' in course_country_req.requirements:
        course_country_req.requirements = course_country_req.requirements.split('```')[1]

    application.university_requirements = course_country_req.requirements
    application.save()

    return course_country_req.requirements



def summary_exists_in_dir(student_doc: StudentDocument):
    student_docs_folder = os.path.join(
        student_data_dir, 
        str(student_doc.student.student_id), 
        student_output_docs_dir
    )
    out_dir = os.path.join(student_docs_folder, summary_folder)
    os.makedirs(out_dir, exist_ok=True)

    summary_file = os.path.join(out_dir, student_doc.file_name)
    if os.path.exists(summary_file):
        student_doc.summary = open(summary_file).read()
        student_doc.save()
        return True
    
    return False


def get_unsummarised_student_docs_from_dir(student: Student) -> List[StudentDocument]:

    unsummarized_docs = list()
    student_docs_folder = os.path.join(student_data_dir, str(student.student_id), student_output_docs_dir)
    for f in os.listdir(student_docs_folder):
        if os.path.isfile(os.path.join(student_docs_folder, f)) and f.endswith(".txt"):
            try:
                student_doc = StudentDocument.objects.get(student=student, file_name=f)
            except StudentDocument.DoesNotExist:
                student_doc = StudentDocument(
                    student=student,
                    file_name=f,
                    text=open(os.path.join(student_docs_folder, f), encoding='utf-8').read()
                )
                student_doc.save()

            if not summary_exists_in_dir(student_doc):
                unsummarized_docs.append(student_doc)

    return unsummarized_docs


def add_student_qualifications_data(application: Application):
    student_id = application.student.student_id
    unsummarized_docs = get_unsummarised_student_docs_from_dir(application.student)   ### Change this to use the database instead of the file system
    student_docs_folder = os.path.join(student_data_dir, str(student_id), student_output_docs_dir)
    
    out_dir = os.path.join(student_docs_folder, summary_folder)
    os.makedirs(out_dir, exist_ok=True)

    summarization_prompt = \
    """
    Below is a text generated by an OCR model from parsing a PDF document. 

    The PDF is of the official documents of a student like certificates, passport and qualifications while applying to a university for masters or undergraduate programs. 
    Infer the name of the document and summarize the key details like qualifications, personal information for each of these that would be crucial in applying to international universities. 
    Clearly call out any ambiguous info and info that is not clearly mentioned. Do not make assumptions. Here is the text - 
    {student_doc_content}
    """


    file_summarization_prompts_dict = {
        doc.id: f"{summarization_prompt} {doc.text}"
        for doc in unsummarized_docs
    }
    
    doc_id_map = {doc.id: doc for doc in unsummarized_docs}

    if not len(file_summarization_prompts_dict):
        print("Student documents already summarized. Skipping...")
    else:
        system_prompt = "You are an expert in summarizing broken text extracted from an ocr model on documents"
        file_contents_responses = run_multithreaded_handler(
            file_summarization_prompts_dict, ordered=True, system_prompt=system_prompt
        )

        for doc_id, response in file_contents_responses.items():
            doc = doc_id_map[doc_id]
            doc.summary = response
            doc.save()

    student_docs = StudentDocument.objects.filter(student=application.student)

    student_data = f"\n{'-'*20}\n{'-'*20}\n".join([
        f"Doc ID: {doc.id}\n\n{doc.summary}"
        for doc in student_docs
    ])

    application.student_qualifications = student_data
    return student_data


def process_student_qualifications(application: Application, re_eval=False):
    def get_response():
        output_example = """
        {
            "requirement": "IELTS 6.5 (or above) with no single element below 5.5 or equivalent",
            "qualification": "No IELTS score mentioned",
            "qualification_result": "Does not meet the requirement",
            "doc_id": "1",
            "qualification_text": "No IELTS score mentioned",
        }
        """
        STUDENT_GET_KEYS_DATA_PROMPT = f"""
        Below are qualifications of a student given across all the documents he has submitted. Given these qualifications and some university requirements in key, value json format.
        Create a new JSON keeping the university key, value pairs intact, and add the following information.
        1. requirement: The requirement for the given key
        2. qualification: Student qualifications for the given key along with it to the same json.
        3. qualification_result: Clearly mention if the student qualifications does not have the qualifications corresponding to a key present in the updated json you provide. Make sure to provide only factual details of the student qualifications from the documents provided. 
        4. doc_id: Provide the document ID for the student document
        5. qualification_text: Provide the text extracted from the student document responsible for the qualification.

        
        Here are the student qualifications - \n {application.student_qualifications}. \n
        Here are the key, value json for university requirements for the country and course student has applied to - {application.university_requirements}.\n
        If the requirements have more than one course or levels of course, add student qualifications for each.
        Do not output any other information but the updated JSON and do not output any key, value pairs that is not about a university requirement criteria.

        Output Example:
        {output_example}
        """

        student_value_pairs = get_llm_response(
            STUDENT_GET_KEYS_DATA_PROMPT, 
            system_prompt="You are an expert in extracting information from texts in a given key, value pair format for a given set of keys"
        )
        print("Student Value Pairs Extracted")

        return student_value_pairs

    if application.processed_qualifications and not re_eval:
        print("Student qualifications already processed. Skipping...")
        return 

    processed_data = None
    while not processed_data or '```' not in processed_data:
        processed_data = get_response()
    
    processed_data = ast.literal_eval(processed_data.split("```")[1])       

    application.processed_qualifications = processed_data
    application.save()


def create_student_application(
        student_id,
        university_name,
        course_name,
        country_name,
    ):
    print(f"Creating application for student {student_id} at {university_name} for course {course_name} in {country_name}")
    university = add_or_get_university(university_name)
    course = add_or_get_university_course(university, course_name)
    country = add_or_get_university_country(university, country_name)
    student = get_student(student_id)
    application = add_or_get_student_application(
        student=student,
        university=university,
        course=course,
        country=country
    )

    print("Application Created")

    return application


def get_processed_student_data(application: Application, re_eval=False):
    add_university_requirements(application)
    add_student_qualifications_data(application)
    process_student_qualifications(application, re_eval)
    
    return application.processed_qualifications


def add_student_qualifications_decisions(application: Application, re_eval=False):
    def get_response():
        output_example = """
        {
            "requirement": "IELTS 6.5 (or above) with no single element below 5.5 or equivalent",
            "qualification": "No IELTS score mentioned",
            "qualification_result": "Does not meet the requirement",
            "doc_id": "1",
            "qualification_text": "No IELTS score mentioned",
            "decision": "fail",
            "reasoning": "The student does not have an IELTS score, which does not meet the requirement of 6.5 or above.",
            "support_doc_id": "1",
            "supporting_text": "No IELTS score mentioned"
        }
        """

        GET_KEYS_DECISION_PROMPT = f"""
        Given a JSON showing university requirements for a given course, student qualifications for each student file, append a two new fields for each key.
        1. decision: The decision of if the student meets criteria or not. The decision can be pass, fail or ambiguous. Decision is to be ambiguous only if student qualifications for that university requirement arent clear.
        2. reasoning: The reasoning for the decision. The reasoning should be a short summary of why the student meets or fails to meet the criteria. If the decision is ambiguous, the reasoning should be a short summary of why the student qualifications are not clear.
        3. support_doc_id: Support the decision by giving the doc ID responsible for the qualification
        4. supporting_text: Support the decision by providing the text extracted from the student document responsible for the qualification. If the decision is ambiguous, mention the text that is missing or unclear.
        Do not output anything but the JSON. Here is the json with requirement, qualifications - {application.processed_qualifications}

        Output Example:
        {output_example}
        """

        student_decision_pairs = get_llm_response(
            GET_KEYS_DECISION_PROMPT, 
            system_prompt="You are an expert in evaluating if a students qualifications meets a given university requirements both in terms of academics, english and subjective requirements by the university"
        )

        return student_decision_pairs
    

    if application.decision_data and not re_eval:
        print("Student decision pairs already extracted. Skipping...")
        return

    decision_pairs = None
    while not decision_pairs or '```' not in decision_pairs:
        decision_pairs = get_response()
        if decision_pairs and '```' not in decision_pairs:
            print("Response not retreived in correct format. Trying again...")
    print("Student Decision Pairs Extracted")

    decision_pairs = ast.literal_eval(decision_pairs.split("```")[1])
    application.decision_data = decision_pairs
    application.save()



def get_student_qualifications_decisions(
        student_id,
        university_name, 
        course, 
        country, 
        re_eval=False
    ):
    application = create_student_application(
        student_id, 
        university_name, 
        course, 
        country
    )
    get_processed_student_data(application, re_eval)
    add_student_qualifications_decisions(application, re_eval)
    



# if __name__ == "__main__":
#     university_name = "northumbria"
#     student_id = "10445379"
#     country = "Bangladesh"
#     course = "MSc Digital Marketing (with Advanced Practice)"

#     student_data = {
#         'student_id': student_id,
#         'first_name': "John",
#         'last_name': "Doe",
#         'email': "",
#         'course': course,
#         'country': country
#     }

#     decision_result = get_student_qualifications_decisions(
#         university_name=university_name, 
#         student_data=student_data
#     )

#     with open("student_decision.json", 'w') as f:
#         json.dump(decision_result, f, indent=4)

    # import pandas as pd
    # students = pd.read_excel(os.path.join(student_data_dir, "Students.xlsx"))
    # students['student_id'] = students['student_id'].astype(str)
    # for i, r in students.iterrows():
    #     student_id = r['student_id']
    #     country = r['country']
    #     course = r['course']
    #     first_name = r['first_name']
    #     last_name = r['last_name']
    #     email = r['email']
    #     if country not in ["India", "Bangladesh"]:
    #         continue
    #     university_requirements = get_university_requirements(university_name, country, course)
    #     student_qualifications = get_student_data(student_id)
    #     decision = get_student_decision(student_qualifications, university_requirements)

