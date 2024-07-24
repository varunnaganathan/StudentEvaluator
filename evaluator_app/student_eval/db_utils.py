from student_eval.models import *


def get_university(
        university_name: str, 
        add_if_not_exists=False
    ) -> University:
    """
    Check if university exists in the database
    If yes return the university object
    If no return None
    """
    try:
        university = University.objects.get(name=university_name)
    except University.DoesNotExist:
        if not add_if_not_exists:
            return None
        university = University(name=university_name)
        university.save()

    return university


def get_university_course(
        university: University, 
        course_name: str, 
        requirements: str = None,
        add_if_not_exists=False
    ) -> UniversityCourse:
    """
    Check if course exists in the database
    If yes return the course object
    If no return None
    """
    try:
        course = UniversityCourse.objects.get(
            university=university, 
            name=course_name
        )
    except UniversityCourse.DoesNotExist:
        if not add_if_not_exists:
            return None
        course = UniversityCourse(
            university=university, 
            name=course_name,
            requirements=requirements
        )
        course.save()

    return course


def get_university_country(
        university: University, 
        country_name: str, 
        requirements: str = None,
        add_if_not_exists=False
    ) -> UniversityCountry:

    """
    Check if country exists in the database
    If yes return the country object
    If no return None
    """
    try:
        country = UniversityCountry.objects.get(
            university=university, 
            name=country_name
        )
    except UniversityCountry.DoesNotExist:
        if not add_if_not_exists:
            return None
        country = UniversityCountry(
            university=university, 
            name=country_name,
            requirements=requirements
        )
        country.save()

    return country


def set_course_requirements(
        course: UniversityCourse, 
        requirements: str
    ):
    """
    Set course requirements
    """
    course.requirements = requirements
    course.save()


def set_country_requirements(
        country: UniversityCountry, 
        requirements: str
    ):
    """
    Set country requirements
    """
    country.requirements = requirements
    country.save()


def get_course_country(
        university: University, 
        course: UniversityCourse, 
        country: UniversityCountry, 
        requirements: str = None,
        add_if_not_exists=False
    ) -> UniversityCourseXCountry:
    """
    Check if course country exists in the database
    If yes return the course country object
    If no return None
    """
    try:
        course_country = UniversityCourseXCountry.objects.get(
            university=university, 
            course=course, 
            country=country
        )
    except UniversityCourseXCountry.DoesNotExist:
        if not add_if_not_exists:
            return None
        course_country = UniversityCourseXCountry(
            university=university, 
            course=course, 
            country=country,
            requirements=requirements
        )
        course_country.save()

    return course_country


def set_course_country_requirements(
        course_country: UniversityCourseXCountry, 
        requirements: str
    ):
    """
    Set course country requirements
    """
    course_country.requirements = requirements
    course_country.save()



def set_student(
        student_id: int, 
        country: str, 
        email: str, 
        first_name: str,
        last_name: str, 
    ) -> Student:
    """
    Check if student exists in the database
    If yes return the student object
    If no return None
    """
    try:
        student = Student.objects.get(student_id=student_id)
        student.country = country
        student.email = email
        student.first_name = first_name
        student.last_name = last_name
        student.save()
    except Student.DoesNotExist:
        student = Student(
            student_id=student_id, 
            country=country, 
            email=email, 
            first_name=first_name,
            last_name=last_name
        )
        student.save()

    return student


def get_student(student_id: int):
    """
    Check if student exists in the database
    If yes return the student object
    If no return None
    """
    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        raise ValueError(f"Student with id {student_id} does not exist")

    return student


def get_student_document(
        student: Student, 
        file_name: str, 
    ) -> StudentDocument:
    """
    Check if student document exists in the database
    If yes return the student document object
    If no return None
    """
    try:
        student_document = StudentDocument.objects.get(
            student=student, 
            file_name=file_name
        )
    except StudentDocument.DoesNotExist:
        raise ValueError(f"Student document with file name {file_name} does not exist")

    return student_document


def add_student_document(
        student: Student, 
        file_name: str,
        text: str, 
        summary: str = None, 
    ) -> StudentDocument:
    """
    Add student document
    """
    student_document = StudentDocument(
        student=student, 
        text=text, 
        summary=summary, 
        file_name=file_name
    )
    student_document.save()

    return student_document


def update_student_document_summary(
        student_document: StudentDocument, 
        text: str, 
        summary: str
    ):
    """
    Update student document
    """
    student_document.summary = summary
    student_document.save()


def add_or_get_student_application(
        student: Student, 
        university: University,
        course: UniversityCourse, 
        country: UniversityCountry, 
    ) -> Application:
    """
    Add student application
    """

    try:
        application = Application.objects.get(
            student=student, 
            university=university, 
            course=course, 
            country=country
        )
    except Application.DoesNotExist:
        application = Application(
            student=student, 
            university=university, 
            course=course, 
            country=country
        )
        application.save()
    
    return application