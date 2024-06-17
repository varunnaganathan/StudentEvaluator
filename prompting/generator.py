from prompting.templates import (
    STUDENT_QUALIFICATION_EVALUATION
)

def student_evaluation_prompt(
        student_doc_content,
        course_entry_requirements,
        country_entry_requirements=None
    ):
    """
    Prompt the student to evaluate the entry requirements
    """
    if country_entry_requirements is None:
        country_entry_requirements = "No specific country requirements"

    return STUDENT_QUALIFICATION_EVALUATION.format(
        student_doc_content=student_doc_content,
        course_entry_requirements=course_entry_requirements,
        country_entry_requirements=country_entry_requirements
    )