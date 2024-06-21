from prompting.templates import (
    STUDENT_QUALIFICATION_EVALUATION
)

def student_evaluation_prompt(
        student_doc_content,
        entry_requirements,
    ):
    """
    Prompt the student to evaluate the entry requirements
    """
    return STUDENT_QUALIFICATION_EVALUATION.format(
        student_doc_content=student_doc_content,
        entry_requirements=entry_requirements,
    )