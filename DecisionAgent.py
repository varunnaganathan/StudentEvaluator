import sys
#import Tools
#from langchain_openai import ChatOpenAI
#from langchain.agents import create_tool_calling_agent
#from langchain.agents import AgentExecutor
from agents.utils import get_llm_response, run_multithreaded_handler
import json, pickle,os
from prompting.templates import STUDENT_CERTIFICATE_SUMMARIZATION_PROMPT


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
        
def get_json_requirements_countryXcourse():
    # parse uni req
    # get all courses and countries
    f = open("./university_data/northumbria/courses.json",'r')
    requirements = json.loads(f.read())
    courses = requirements.keys()

    f1 = open("./university_data/northumbria/countries.json",'r')
    requirements_country = json.loads(f1.read())
    countries = requirements_country.keys()

    Final_Req = {}

    for course in courses:
        for country in countries:
            if country not in ["India","Bangladesh"]:
                continue
            country_specific_req = requirements_country[country]
            r = requirements[course]
            # call llm call for every course X country and store
            prompt_get_course_req = f"""
            given the requirements for entry into university below, 
            extract and summarize in very short  the fields structurally in json isolating - academic, english, work experience, documents needed and other requirements separately . 
            if there are multiple levels or types of sub courses, isolate them as well. Dont output anything else but the json and dont make up any requirement that isnt mentioned. 
            Provide any notes you have in a separate column in the json.
            here is the requirements - {r}
            """

            prompt_translate_req_country_specific = f"""
            You are given the requirements for entry into university below for a student from UK, 
            and rules below for a student applying from a different country - {country}, recreate above json for university requirements for same course 
            if student is from {country} by correctly mapping and altering requirements given based on the rules given . 
            Dont output anything else but the json and dont make up any requirement that isnt mentioned. 
            Provide any notes you have in a separate column in the json about the replacements in entry requirements you made.
            here are the rules for a student applying from {country} - {country_specific_req}
            """

            json_req = get_llm_response(
                    user_prompt=prompt_get_course_req, 
                    system_prompt="You are an expert in extracting summarized information in structured json format from unstructured text"
                )
            print(json_req)
            print("\n\n\n\n")


            
            json_modified_req = get_llm_response(
                    prompt_translate_req_country_specific + str(json_req), 
                    system_prompt="You are an expert in extracting summarized information in structured json format from unstructured text"
                )
            print(json_modified_req)
            print("\n\n\n---------------------------------\n\n\n")
            Final_Req[(country, course)] = [str(json_modified_req), str(json_req)]
            print(country)
    pickle.dump(Final_Req, open("./university_data/northumbria/modified_country_course_req_india_bangladesh.pickle",'wb'))



# provide folder with extarcted data in txt form
# call llm, to summarize cook and create a student profile here from a single folder with all student docs

def getStudentDataForDecision(folder):
    summarized_contents = {}
    outfolder = folder + "LLM_Summary/"
    os.makedirs(outfolder)
    for path in os.listdir(folder):
        # check if current path is a file
        if os.path.isfile(os.path.join(folder, path)): #and str(os.path.join(folder, path)).endswith(".pdf"):
            fname = os.path.join(folder, path)
            print(fname)
            contents = open(fname,'rb').read()
            print(contents)
            # give to llm to summarize 
            content_summary = get_llm_response(
                STUDENT_CERTIFICATE_SUMMARIZATION_PROMPT + str(contents), 
                system_prompt="You are an expert in summarizing broken text extracted from an ocr model on documents")
            print(fname)
            print("\n\n")
            print(content_summary)
            print("\n\n----------------------------------\n\n")
            summarized_contents[fname] = content_summary
            # write summary to new file
            # not needed as done once
            """
            outf = outfolder + path
            
            fout = open(outf,'w+')
            print(outf)
            fout.write(content_summary)
            """
    return summarized_contents


import pdb

if __name__ == "__main__":
    #get_json_requirements_countryXcourse()
    # below is a one time job to get student req
    #summarized_content = getStudentDataForDecision("./student_data/10445379/output_docs/")
    
    
    # get a single student all llm summaries
    data_dir = "./student_data/10445379/output_docs/LLM_Summary/"
    student_qual = ""
    for path in os.listdir(data_dir):
        # check if current path is a file
        if os.path.isfile(os.path.join(data_dir, path)): #and str(os.path.join(folder, path)).endswith(".pdf"):
            fname = os.path.join(data_dir, path)
            student_qual += open(fname,'r').read()
    country = "Bangladesh"
    course = "MSc Digital Marketing (with Advanced Practice)"

    # get uni req for country and course applying to as a dict
    uni_reqs = pickle.load(open("./university_data/northumbria/modified_country_course_req_india_bangladesh.pickle",'rb'))
    uni_req = uni_reqs[(country,course)]
    uni_req = str(json.loads(uni_req[0].split("```")[1]))
    

    # tell llm to get student values for those dicts

    STUDENT_GET_KEYS_DATA_PROMPT = f"""
    Below are qualifications of a student given across all the documents he has submitted. Given these qualifications and some university requirements in key,value json format.
    Create a new json keeping the university key, value pairs intact, but also adding student qualifications for the given key along with it to the same json.
    Make sure to provide only factual details of the student qualifications from the documents provided. Clearly mention if the student qualifications do not have the qualifications corresponding to a key present in the updated json you provide.
    Here are the student qualifications - \n {student_qual}. \n
    Here are the key, value json for university requirements for the country and course student has applied to - {uni_req}.\n
    If the requirements have more than one course or levels of course, add student qualifications for each.
    Dont output any other information but the updated json and dont output any key, value pairs that isnt about a university requirement criteria.
    """
    student_value_pairs = get_llm_response(
                STUDENT_GET_KEYS_DATA_PROMPT, 
                system_prompt="You are an expert in extracting information from texts in a given key, value pair format for a given set of keys")
    #$pdb.set_trace()
    print(student_value_pairs)
    print("\n\n\n\n")
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
                system_prompt="You are an expert in evaluating if a students qualifications meets a given university requirements both in terms of academics, english and subjective requirements by the university")
    print(student_decision_pairs)
    print("\n\n\n")

    
    print("\n---------------------------FINAL DECISION-----------------------\n")
    # get final decision
    FINAL_DECISION_PROMPT = f"""
    Given a json with university requirements for a course admission, student qualifications for each requirement, and a decision for each requirement,
    generate a final decision report summarizing final decision, point of failure in meeting requirements, points of success in meeting requirements and points of ambiguity where more information is either needed 
    from a human evaluator or from the student to provide more info. Here is the json - {student_decision_pairs}
    """
    
    final_decision_report = get_llm_response(
                FINAL_DECISION_PROMPT, 
                system_prompt="You are an expert in generating summarized reports from given json data")
    print(final_decision_report)
    print("\n\n\n\n")
    


    """

    # sampler here
    #f = pickle.load(open("./university_data/northumbria/modified_country_course_req_india_bangladesh.pickle",'rb'))
        uni_req = \"\"\"
        {
            "MSc Business with Hospitality and Tourism Management (with Advanced Practice)": {
                "Academic": {
                "Standard": {
                    "Public University": "3 or 4 year Bachelor Degree with a minimum 2.5 GPA",
                    "Private University": "3 or 4 year Bachelor Degree with a minimum 2.7 GPA"
                },
                "Non-standard": "Substantial experience in a business organisation and/or a relevant professional qualification"
                },
                "English": {
                "Standard": "IELTS 6.0 (with no component below 5.5)",
                "Pre-Sessional": "IELTS 5.5 – 6.0 may join Pre-Sessional English and Study Skills programme"
                },
                "Documents": [
                "Certified translations (if qualifications are not in English)"
                ],
                "Other Requirements": [
                "Wide range of international qualifications accepted. Visit entry requirements page for details."
                ],
                "Pathway Courses": {
                "Masters Foundation Programme": "For students needing additional support to meet entry requirements",
                "Pre-Sessional English and Study Skills": "For students with IELTS 5.5 – 6.0 to develop language skills"
                },
                "Enquire": "Enquire now"
            }
        }
        \"\"\"
        student_q = \"\"\"
        
        CGPA of 4.5 / 5 in Bachelors degree.
        IELTS Score of 4.9.

        \"\"\"

        decision = get_llm_response(
                        prompt_agentic + "University requirements - " + str(uni_req) + "\nStudent qualifications - " + str(student_q), 
                        system_prompt="You are an expert in evaluating if given student qualifications meets requirements from a university"
                    )
        print(decision)
        print("\n\n\n---------------------------------\n\n\n")

        decisions = json.loads(str(decision).split("```")[1:2])
        
    """

