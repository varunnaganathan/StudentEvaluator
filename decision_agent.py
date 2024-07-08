from agents.utils import get_llm_response, run_multithreaded_handler
import json
import os
from prompting.templates import STUDENT_CERTIFICATE_SUMMARIZATION_PROMPT
from settings import university_data_dir, student_output_docs_dir, summary_folder, student_data_dir


"""
This is a base class for the student evaluator.
This takes the two dicts, sanitizes the text within them,
and creates an agent with math, reasoning and doc check tool
Responses for each tool should be true, false and a comment.

Flow
1. get dict
2. sanitize
3. for each key
    3.1 Send to llm agent to evaluate
    3.2 math, reasoning or missing info
    3.2 return true / false with comments and reason
4. display net reason
"""

prompt = """
You need to evaluate a student for a degree and university he is applying to. Youll be given a single university requirement, the students relevant qualification for that requirement
and a set of tools to perform the evaluation. The tools are
1. MathTool - to compare any numeric criteria like grade and marks between university requirement and student qualifications.
2. DocCheck tool - if you feel information isnt present of the student or incomplete info supplied, this tool can be used to check if student has provided needed info and documents.
3. Use your own reasoning if the evaluation is more subjective in nature.

For each set of requirements and qualification, use appropriate tool, evaluate response and reply of form of json like this - {"Verdict":"True/False/Ambiguous","Comments":"Describe why he meets or doenst meet the criteria"}.
Dont give any additional info and follow output format.

"""

output_format = """
"Requirement1, student qualification1 : { "decision":"True / False / math / data incomplete", "Reasoning":"Explain your reasoning for the decision"}

"""

prompt_agentic = f"""
Given the json of universite requirements corresponding student qualificatications for each requirement, 
you need to do the following
evaluate each requirement, qualification pair and decide if it involved mathematical comparison or logical reasoning to decide if the student is eligible,
1. if it involves mathematical requirement , extract only the mathematical / numeric parts to be compared for each requirement, qualification pair and label the pair as "math".
2. If it involves logical or language based comparison, compare and output True, false telling if the student meets the requirement for that requirement, qualification pair or not.
3. if data is incomplete to evaluate , output "data incomplete" as decision.
end output for each (requirement, qualification) pair should be of format {output_format}. dont output anything else but the json in output format and dont make any new facts up.
here are the university requirements for the country and course student has applied to as well as the student's qualifications. 

"""


def extract_country_x_course_requirements(uni_name="northumbria"):
    # parse uni req
    # get all courses and countries

    f_name = os.path.join(university_data_dir, uni_name, "course_x_country_requirements.json")
    if os.path.exists(f_name):
        print("University requirements already extracted. Skipping...")
        return 
    
    course_x_country_requirements = dict()
    requirements_courses: dict = json.load(
        open(os.path.join(university_data_dir, uni_name, "courses.json"))
    )
    courses = requirements_courses.keys()

    requirements_countries: dict = json.load(
        open(os.path.join(university_data_dir, uni_name, "countries.json"))
    )
    countries = requirements_countries.keys()

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
    Dont output anything else but the json and dont make up any requirement that isnt mentioned. 
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
            if country not in course_x_country_requirements:
                course_x_country_requirements[country] = dict()
            course_x_country_requirements[country][course] = (course_response, country_response)

    json.dump(
        course_x_country_requirements, 
        open(f_name, 'w'), 
        indent=4
    )


# provide folder with extarcted data in txt form
# call llm, to summarize cook and create a student profile here from a single folder with all student docs

def get_student_data(student_id):
    student_docs_folder = os.path.join(student_data_dir, student_id, student_output_docs_dir)
    out_dir = os.path.join(student_docs_folder, summary_folder)
    os.makedirs(out_dir, exist_ok=True)
    file_summarization_prompts_dict = {
        os.path.join(out_dir, file_name): 
        f"{STUDENT_CERTIFICATE_SUMMARIZATION_PROMPT} {open(os.path.join('.', student_docs_folder, file_name), encoding='utf8').read()}"
        for file_name in os.listdir(student_docs_folder)
        if not os.path.exists(os.path.join(out_dir, file_name)) \
            and os.path.isfile(os.path.join(student_docs_folder, file_name))\
            and file_name.endswith(".txt")
    }
    
    if not len(file_summarization_prompts_dict):
        print("Student documents already summarized. Skipping...")
    else:
        system_prompt = "You are an expert in summarizing broken text extracted from an ocr model on documents"
        file_contents_responses = run_multithreaded_handler(
            file_summarization_prompts_dict, ordered=True, system_prompt=system_prompt
        )

        for out_file_path, response in file_contents_responses.items():
            with open(f"{out_file_path}", 'w') as f:
                f.write(response)

    student_data = "\n".join([
        open(os.path.join(out_dir, file_name)).read()
        for file_name in os.listdir(out_dir) if os.path.isfile(os.path.join(out_dir, file_name))
    ])
    return student_data


def get_student_decision(student_qual, university_requirement):
        # get uni req for country and course applying to as a dict    

    # tell llm to get student values for those dicts

    STUDENT_GET_KEYS_DATA_PROMPT = f"""
    Below are qualifications of a student given across all the documents he has submitted. Given these qualifications and some university requirements in key,value json format.
    Create a new json keeping the university key, value pairs intact, but also adding student qualifications for the given key along with it to the same json.
    Make sure to provide only factual details of the student qualifications from the documents provided. Clearly mention if the student qualifications do not have the qualifications corresponding to a key present in the updated json you provide.
    Here are the student qualifications - \n {student_qual}. \n
    Here are the key, value json for university requirements for the country and course student has applied to - {university_requirement}.\n
    If the requirements have more than one course or levels of course, add student qualifications for each.
    Dont output any other information but the updated json and dont output any key, value pairs that isnt about a university requirement criteria.
    """
    student_value_pairs = get_llm_response(
        STUDENT_GET_KEYS_DATA_PROMPT, 
        system_prompt="You are an expert in extracting information from texts in a given key, value pair format for a given set of keys"
    )
    print("Student Value Pairs Extracted")
    #$pdb.set_trace()
    # print(student_value_pairs)
    # print("\n\n\n\n")
    # tell llm to decide math or not
    # this works without math for now.
    # check if we need, functio  32n is above only

    GET_KEYS_DECISION_PROMPT = f"""
    Given a json showing university requirements for a given course, along with student qualifications for each, append a new field for each key with the decision of if the student meets criteria or not.
    The decision can be pass, fail or ambiguous along with reasoning for each. Decision is to be ambiguous only if student qualifications for that university requirement arent clear.
    Dont output anything but the json. here is the json with requirement, qualifications - {str(student_value_pairs.split("```")[1])}
    """
    student_decision_pairs = get_llm_response(
        GET_KEYS_DECISION_PROMPT, 
        system_prompt="You are an expert in evaluating if a students qualifications meets a given university requirements both in terms of academics, english and subjective requirements by the university"
    )

    print("Student Decision Pairs Extracted")
    # print(student_decision_pairs)
    # print("\n\n\n")

    
    print("\n---------------------------FINAL DECISION-----------------------\n")
    # get final decision
    FINAL_DECISION_PROMPT = f"""
    Given a json with university requirements for a course admission, student qualifications for each requirement, and a decision for each requirement,
    generate a final decision report summarizing final decision, point of failure in meeting requirements, points of success in meeting requirements and points of ambiguity where more information is either needed 
    from a human evaluator or from the student to provide more info. Here is the json - {student_decision_pairs}
    """
    
    final_decision_report = get_llm_response(
        FINAL_DECISION_PROMPT, 
        system_prompt="You are an expert in generating summarized reports from given json data"
    )
    
    print("Final Decision Report Generated")
    # print(final_decision_report)
    # print("\n\n\n\n")

    return final_decision_report


def get_university_requirements(university_name, country, course):
    uni_reqs = json.load(open(os.path.join(university_data_dir, university_name, "course_x_country_requirements.json")))
    uni_req = uni_reqs[country][course][0].split("```")[1]
    return uni_req


def get_student_decison_for_university(university_name, student_data):
    extract_country_x_course_requirements(uni_name=university_name)
    course, country = student_data['course'], student_data['country']
    university_requirements = get_university_requirements(university_name, country, course)
    student_qualifications = get_student_data(str(student_data['student_id']))
    decision = get_student_decision(student_qualifications, university_requirements)
    response = {
        "university_requirements": university_requirements,
        "student_qualifications": student_qualifications,
        "student_decision": decision
    }
    return response


if __name__ == "__main__":
    university_name = "northumbria"
    extract_country_x_course_requirements(uni_name=university_name)    

    student_id = "10445379"
    country = "Bangladesh"
    course = "MSc Digital Marketing (with Advanced Practice)"

    university_requirements = get_university_requirements(university_name, country, course)
    student_qualifications = get_student_data(student_id)
    decision = get_student_decision(student_qualifications, university_requirements)


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

