from prompting.templates import (
    COUNTRY_REQUIREMENTS_TEMPLATE,
    COURSE_REQUIREMENTS_TEMPLATE,
    REQUIREMENTS_TEMPLATE_FORMAT,
    STUDENT_CONTENT_EXTRACTION_EXAMPLE,
    STUDENT_QUALIFICATION_EVALUATION,
    STUDENT_CONTENT_EXTRACTION_PROMPT
)
from storage.data import Student

def student_evaluation_prompt(
        student: Student,
        student_doc_content,
        entry_requirements,
    ):
    """
    Prompt the student to evaluate the entry requirements
    """
    return STUDENT_QUALIFICATION_EVALUATION.format(
        student_level=student.level,
        student_doc_content=student_doc_content,
        entry_requirements=entry_requirements,
    )


def get_requirements_structuring_prompt(requirements, country_name=None, course_name=None):
    assert country_name or course_name, "Either country_name or course_name should be provided."
    if country_name:
        requirements = COUNTRY_REQUIREMENTS_TEMPLATE.format(
            country_name=country_name, entry_requirements=requirements
        )
    elif course_name:
        requirements = COURSE_REQUIREMENTS_TEMPLATE.format(
            course_name=course_name, entry_requirements=requirements
        )
    
    return requirements + REQUIREMENTS_TEMPLATE_FORMAT


def get_doc_content_ext_prompt(doc, requirements):
    doc_prompt = STUDENT_CONTENT_EXTRACTION_PROMPT.format(
        student_doc_content=doc,
        requirement=requirements
    )
    doc_prompt += "\n\n" + STUDENT_CONTENT_EXTRACTION_EXAMPLE
    return doc_prompt