from agents.utils import get_llm_response, run_multithreaded_handler
import json
import os
from prompting.templates import STUDENT_CERTIFICATE_SUMMARIZATION_PROMPT
from settings import (
    university_data_dir, 
    student_output_docs_dir, 
    summary_folder, 
    student_data_dir
)


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


def get_student_doc_map(student_id):
    student_docs_folder = os.path.join(student_data_dir, student_id, student_output_docs_dir)
    student_doc_map = json.load(open(os.path.join(student_data_dir, "student_doc_map.json")))
    for f in os.listdir(student_docs_folder):
        if student_id not in student_doc_map:
            student_doc_map[student_id] = dict()

        if os.path.isfile(os.path.join(student_docs_folder, f)):
            if f not in student_doc_map[student_id]:
                student_doc_map[student_id][f] = len(student_doc_map[student_id]) + 1
    
    json.dump(student_doc_map, open(os.path.join(student_data_dir, "student_doc_map.json"), 'w'), indent=4)

    reverse = {v: k for k, v in student_doc_map[student_id].items()}
    json.dump(reverse, open(os.path.join(student_data_dir, "student_doc_map_inv.json"), 'w'), indent=4)
    
    return student_doc_map


def get_student_data(student_id):
    student_doc_map = get_student_doc_map(student_id)
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
                f.write(f"file_name: {os.path.basename(out_file_path)}\nContent: {response}")

    student_data = f"\n{'-'*20}\n{'-'*20}\n".join([
        f"Doc ID: {student_doc_map[student_id][file_name]}\n\n{open(os.path.join(out_dir, file_name)).read()}"
        for file_name in os.listdir(out_dir) if os.path.isfile(os.path.join(out_dir, file_name))
    ])
    return student_data


def get_student_data_keys(university_requirement, student_qual):
    def get_response():
        output_example = """
        {
            "Requirement": "IELTS 6.5 (or above) with no single element below 5.5 or equivalent",
            "qualification": "No IELTS score mentioned",
            "qualification_result": "Does not meet the requirement",
            "doc_id": "1",
            "qualification_text": "No IELTS score mentioned",
        }
        """
        STUDENT_GET_KEYS_DATA_PROMPT = f"""
        Below are qualifications of a student given across all the documents he has submitted. Given these qualifications and some university requirements in key, value json format.
        Create a new JSON keeping the university key, value pairs intact, and add the following information.
        1. qualification: Student qualifications for the given key along with it to the same json.
        2. qualification_result: Clearly mention if the student qualifications does not have the qualifications corresponding to a key present in the updated json you provide. Make sure to provide only factual details of the student qualifications from the documents provided. 
        3. doc_id: Provide the document ID for the student document
        4. qualification_text: Provide the text extracted from the student document responsible for the qualification.

        
        Here are the student qualifications - \n {student_qual}. \n
        Here are the key, value json for university requirements for the country and course student has applied to - {university_requirement}.\n
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

    value_pairs = None
    while not value_pairs or '```' not in value_pairs:
        value_pairs = get_response()
    
    value_pairs = json.loads(value_pairs.split("```")[1])        

    return value_pairs


def get_student_decision_keys(student_value_pairs: dict, student_id):
    def get_response():
        output_example = """
        {
            "Requirement": "IELTS 6.5 (or above) with no single element below 5.5 or equivalent",
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
        Do not output anything but the JSON. Here is the json with requirement, qualifications - {str(student_value_pairs)}

        Output Example:
        {output_example}
        """

        student_decision_pairs = get_llm_response(
            GET_KEYS_DECISION_PROMPT, 
            system_prompt="You are an expert in evaluating if a students qualifications meets a given university requirements both in terms of academics, english and subjective requirements by the university"
        )
        print("Student Decision Pairs Extracted")

        return student_decision_pairs
    
    decision_pairs = None
    while not decision_pairs or '```' not in decision_pairs:
        decision_pairs = get_response()

    print("Student Decision Pairs Extracted")
    # update_file_paths(decision_pairs, student_id)

    # print("File Paths Updated")

    return decision_pairs


def get_student_final_decision(student_decision_pairs):
    FINAL_DECISION_PROMPT = f"""
    Given a JSON with university requirements for a course admission, student qualifications for each requirement, and a decision for each requirement,
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


def get_student_decision(univesity_name, student_data):
    student_value_pairs = get_student_data_keys(university_name=univesity_name, student_data=student_data)
    print(student_value_pairs)
    print("\n\n\n\n")
    student_decision_pairs = get_student_decision_keys(student_value_pairs)
    print("\n\n\n\n")
    print(student_decision_pairs)
    print("\n\n\n\n")
    final_decision_report = get_student_final_decision(student_decision_pairs)

    return final_decision_report, student_value_pairs, student_decision_pairs


def get_university_requirements(university_name, student_data):
    extract_country_x_course_requirements(uni_name=university_name)
    course, country = student_data['course'], student_data['country']
    uni_reqs = json.load(open(os.path.join(university_data_dir, university_name, "course_x_country_requirements.json")))
    uni_req = uni_reqs[country][course][0].split("```")[1]
    return uni_req


def update_file_paths(student_decision_pairs, student_id):
    if '```' in student_decision_pairs:
        student_decision_pairs = json.loads(student_decision_pairs.split('```')[1])
    else:
        return
    # print(json.dumps(student_decision_pairs, indent=4))
    existing_file_names = [
        f for f in os.listdir(os.path.join(student_data_dir, student_id))
        if os.path.isfile(os.path.join(student_data_dir, student_id, f))
    ]
    predicted_file_names = [
        v['support_file_name'] for _, v in student_decision_pairs.items()
        if 'support_file_name' in v and v['support_file_name'] != "-"\
    ]
    
    print(existing_file_names)
    print(predicted_file_names)

    output_example = """
    {
        "CV (Curriculum Vitae)": ["CV.pdf", "Resume.pdf"],
        "Consolidated Statement of Grades (Degree Certificate)": ["DEGREE PROVISIONAL.pdf", "Degree Certificate.pdf", "Degree.pdf"],
        "IELTS Certificate": "-",
    }
    """

    file_name_alignment_prompt = f"""
    Given a list of file names extracted from student documents and a list of file names of the student documents,
    align the file names to the correct file of the student documents. If a file name is not present in the student documents, mention add it as "-".
    In case there are multiple student document files that can be matched with a support file name, mention all the possible file names. 
    
    Here are the file names extracted from student documents - {existing_file_names}
    Here are the file names predicted to be responsible for a qualification - {predicted_file_names}


    Output Example:
    {output_example}
    """

    print(file_name_alignment_prompt)

    file_name_alignment = get_llm_response(
        file_name_alignment_prompt, 
        system_prompt="You are an expert in aligning file names to the correct file in a given list of files"
    )

    if '```' in file_name_alignment:
        file_name_alignment = json.loads(file_name_alignment.split("```")[1])

        for k, v in student_decision_pairs.items():
            if 'support_file_name' in v and v['support_file_name'] != "-":
                student_decision_pairs[k]['support_file_name'] = file_name_alignment[v['support_file_name']]

    return student_decision_pairs


def get_student_decison_for_university(university_name, student_data):
    student_id = str(student_data['student_id'])
    university_requirements = get_university_requirements(university_name, student_data)
    student_qualifications = get_student_data(student_id)
    
    student_value_pairs = get_student_data_keys(university_requirements, student_qualifications)
    student_decision_pairs = get_student_decision_keys(student_value_pairs, student_id)

    # update_file_paths(student_decision_pairs, student_id)

    final_decision_report = get_student_final_decision(student_decision_pairs)

    response = {
        "university_requirements": university_requirements,
        "student_qualifications": student_qualifications,
        "student_value_pairs": student_value_pairs,
        "student_decision_pairs": student_decision_pairs,
        "student_decision": final_decision_report
    }
    return response


if __name__ == "__main__":
    university_name = "northumbria"
    student_id = "10445379"
    country = "Bangladesh"
    course = "MSc Digital Marketing (with Advanced Practice)"

    student_data = {
        'student_id': student_id,
        'first_name': "John",
        'last_name': "Doe",
        'email': "",
        'course': course,
        'country': country
    }

    decision_result = get_student_decison_for_university(
        university_name=university_name, 
        student_data=student_data
    )

    with open("student_decision.json", 'w') as f:
        json.dump(decision_result, f, indent=4)

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

