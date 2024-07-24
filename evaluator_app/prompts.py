# prompt order to get uni req for a course X country
# firts get uk req in json
# then get country specific in json with same keys
# now get student req for same keys and then compare

prompt_get_course_req = """
given the requirements for entry into university below, 
extract and summarize in very short  the fields structurally in json isolating - academic, english, work experience, documents and othe rrequirements separately . 
if there are multiple levels or types of sub courses, isolate them as well. here is the requirement - 
"""

prompt_translate_req_country_specific = f"""
given the requirements for entry into university below for a student from UK, 
and rules below for a student applying from {country}, recreate above json for university requirements for same course 
if student is from {country}. here are the rules for a student applying from bangladesh 
"""

