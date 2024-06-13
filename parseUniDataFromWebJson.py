"""
used to parse json for country and course work crawled from the website
parse into dicts and pickle
To do:
add llm parsing 


"""


import os
import json, pickle


def get_course_name(url):
    return url.split("/")[-2].strip("\n")

# get llm summary of requirement for this particular course
def getLLMSummary(s):
    return ""

# get per course requirements as mentioned
def getRequirementPerCourse(filepath):
    courseReq = {}
    courseReqLLM = {}

    with open(filepath,'r') as f:
        content = json.loads(f.read())
        for req in content:
            courseReq[get_course_name(req["url"])] = req["entry_requirements"]
            courseReqLLM[get_course_name(req["url"])] = getLLMSummary(req["entry_requirements"])

    return courseReq, courseReqLLM


def getCountryRequirement(filepath):
    countryReq = {}
    countryReqLLM = {}

    with open(filepath,'r') as f:
        content = json.loads(f.read())
        for continent in content:
            for countrydata in continent:
                countryReq[countrydata["country"]] = countrydata["table"]
                countryReqLLM[countrydata["country"]] = getLLMSummary(countrydata["table"])
    
    return countryReq, countryReqLLM


if __name__ == "__main__":
    filepathCourseReq = "./universityData/courses_data.json"
    courseReq, courseReqLLM = getRequirementPerCourse(filepath=filepathCourseReq)

    filepathCountryReq = "./universityData/continent_countries.json"
    countryReq, countryReqLLM = getCountryRequirement(filepathCountryReq)

    print(courseReq)
    print("\n\n\n")
    print(countryReq)

    #pickle.dump(courseReq,open("./universityData/northUmbria/courseRequirements.pickle",'wb'))
    #pickle.dump(countryReq,open("./universityData/northUmbria/countryRequirements.pickle",'wb'))