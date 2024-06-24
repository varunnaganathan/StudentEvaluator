from dataclasses import dataclass
from typing import Optional

@dataclass
class Student:
    student_id: str
    first_name: str
    last_name: str
    email: str
    country: str
    level: str
    course: str


# @dataclass
# class Application:
#     id: str
#     student_id: str
#     university_id: str
#     course_name: str
#     country_name: str
#     status: str


@dataclass
class University:
    website: str
    name: str

@dataclass
class UniversityCountry:
    uni_id: str
    country_name: str
    entry_req: str
    entry_req_json: Optional[str] = None

@dataclass
class UniversityCourse:
    uni_id: str
    name: str
    entry_req: str
    entry_req_json: Optional[str] = None


@dataclass
class StudentDocument:
    doc_id: str
    file_name: str
    university_name: str
    student_id: str
    
    content: str
    summary: Optional[str] = None
