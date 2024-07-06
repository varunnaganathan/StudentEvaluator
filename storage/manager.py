from storage.data import (
    Student, 
    StudentDocument, 
    University, 
    UniversityCountry, 
    UniversityCourse
)
from typing import List
import uuid
from settings import db_file
import sqlite3
import os
from storage.constants import (
    APPLICATION_COUNTRY_ID,
    APPLICATION_COURSE_ID,
    APPLICATION_ID,
    APPLICATION_STATUS,
    APPLICATION_STUDENT_ID,
    APPLICATION_TABLE,
    APPLICATION_UNIVERSITY_ID,
    DOC_CONTENT,
    DOC_FILE_NAME,
    DOC_ID,
    DOC_STUDENT_ID,
    DOC_SUMMARY,
    DOC_TABLE,
    DOC_UNIVERSITY_NAME,
    STUDENT_APPLICATION_ID,
    STUDENT_COURSE,
    STUDENT_FIRST_NAME,
    STUDENT_LAST_NAME,
    STUDENT_EMAIL,
    STUDENT_COUNTRY,
    STUDENT_STUDY_LEVEL,
    STUDENT_TABLE,
    STUDENT_ID,
    UNIVERSITY_COUNTRY_ENTRY_REQ_JSON,
    UNIVERSITY_COURSE_ENTRY_REQ_JSON,
    UNIVERSITY_COURSE_UNI_ID,
    UNIVERSITY_NAME,
    UNIVERSITY_TABLE,
    UNIVERSITY_WEBSITE,
    UNIVERSITY_COUNTRY_COUNTRY_NAME,
    UNIVERSITY_COUNTRY_ENTRY_REQ,
    UNIVERSITY_COUNTRY_NAME,
    UNIVERSITY_COUNTRY_TABLE,
    UNIVERSITY_COUNTRY_UNI_ID,
    UNIVERSITY_COURSE_ENTRY_REQ,
    UNIVERSITY_COURSE_NAME,
    UNIVERSITY_COURSE_TABLE
)


def get_conn_and_cursor(file):
    conn = sqlite3.connect(file)
    cursor = conn.cursor()
    return conn, cursor


def get_random_id(bit_size = 63):
    return uuid.uuid4().int % (2**(bit_size))


class DatabaseManager:
    def __init__(
            self, 
            file = db_file, 
            overwrite=False,
        ):
        self.db = file

        if os.path.exists(self.db) and overwrite:
            print("Removing existing database")
            os.remove(self.db)
        
        self.create_db()


    def create_db(self):
        conn, cursor = get_conn_and_cursor(self.db)
        # Create Student table
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {STUDENT_TABLE} (
            {STUDENT_ID} TEXT PRIMARY KEY,
            {STUDENT_FIRST_NAME} TEXT NOT NULL,
            {STUDENT_LAST_NAME} TEXT NOT NULL,
            {STUDENT_EMAIL} TEXT NOT NULL,
            {STUDENT_COUNTRY} TEXT NOT NULL,
            {STUDENT_STUDY_LEVEL} TEXT NOT NULL,
            {STUDENT_COURSE} TEXT NOT NULL
        )
        ''')

        # cursor.execute(f'''
        # CREATE TABLE IF NOT EXISTS {APPLICATION_TABLE} (
        #     {APPLICATION_ID} INTEGER PRIMARY KEY AUTOINCREMENT,
        #     {APPLICATION_STUDENT_ID} TEXT NOT NULL,
        #     {APPLICATION_UNIVERSITY_ID} TEXT NOT NULL,
        #     {APPLICATION_COURSE_NAME} TEXT NOT NULL,
        #     {APPLICATION_COUNTRY_NAME} TEXT NOT NULL,
        #     {APPLICATION_STATUS} TEXT NOT NULL,
        #     FOREIGN KEY ({APPLICATION_STUDENT_ID}) REFERENCES {STUDENT_TABLE}({STUDENT_ID}),
        #     FOREIGN KEY ({APPLICATION_UNIVERSITY_ID}) REFERENCES {UNIVERSITY_TABLE}({UNIVERSITY_WEBSITE}),
        #     FOREIGN KEY ({APPLICATION_COURSE_ID}) REFERENCES {UNIVERSITY_COURSE_TABLE}({UNIVERSITY_COURSE_NAME}, {UNIVERSITY_COURSE_UNI_ID})
        #     FOREIGN KEY ({APPLICATION_COUNTRY_ID}) REFERENCES {UNIVERSITY_COUNTRY_TABLE}({UNIVERSITY_COUNTRY_COUNTRY_NAME}, {UNIVERSITY_COUNTRY_UNI_ID})
        # )
        # ''')

        # Create Docs table
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {DOC_TABLE} (
            {DOC_ID} INTEGER PRIMARY KEY AUTOINCREMENT,
            {DOC_FILE_NAME} TEXT NOT NULL,
            {DOC_UNIVERSITY_NAME} TEXT NOT NULL,
            {DOC_STUDENT_ID} TEXT NOT NULL,
            {DOC_SUMMARY} TEXT NOT NULL,
            {DOC_CONTENT} TEXT NOT NULL,
            FOREIGN KEY ({DOC_STUDENT_ID}) REFERENCES {STUDENT_TABLE}({STUDENT_ID})
        )
        ''')
        
        # Create University table
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {UNIVERSITY_TABLE} (
            {UNIVERSITY_WEBSITE} TEXT PRIMARY KEY,
            {UNIVERSITY_NAME} TEXT NOT NULL
        )
        ''')

        # Create {UNIVERSITY_COUNTRY_TABLE} table
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {UNIVERSITY_COUNTRY_TABLE} (
            {UNIVERSITY_COUNTRY_UNI_ID} TEXT,
            {UNIVERSITY_COUNTRY_COUNTRY_NAME} TEXT NOT NULL,
            {UNIVERSITY_COUNTRY_ENTRY_REQ} TEXT NOT NULL,
            {UNIVERSITY_COUNTRY_ENTRY_REQ_JSON} TEXT,
            PRIMARY KEY ({UNIVERSITY_COUNTRY_UNI_ID}, {UNIVERSITY_COUNTRY_COUNTRY_NAME}),
            FOREIGN KEY ({UNIVERSITY_COUNTRY_UNI_ID}) REFERENCES {UNIVERSITY_TABLE}({UNIVERSITY_WEBSITE})
        )
        ''')

        # Create {UNIVERSITY_COURSE_TABLE}s table
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {UNIVERSITY_COURSE_TABLE} (
            {UNIVERSITY_COUNTRY_UNI_ID} TEXT NOT NULL,
            {UNIVERSITY_COURSE_NAME} TEXT NOT NULL,
            {UNIVERSITY_COURSE_ENTRY_REQ} TEXT NOT NULL,
            {UNIVERSITY_COURSE_ENTRY_REQ_JSON} TEXT,
            PRIMARY KEY ({UNIVERSITY_COUNTRY_UNI_ID}, {UNIVERSITY_COURSE_NAME}),
            FOREIGN KEY ({UNIVERSITY_COUNTRY_UNI_ID}) REFERENCES {UNIVERSITY_TABLE}({UNIVERSITY_WEBSITE})
        )
        ''')

        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        print("Database created successfully")


    def set_university(self, university_id, university_name):
        self.university = university_id
        self.university_name = university_name


    def add_student(self, student: Student):
        conn, cursor = get_conn_and_cursor(self.db)

        cursor.execute(f'''
        SELECT 1 FROM {STUDENT_TABLE}
        WHERE {STUDENT_ID} = ?
        ''', (student.student_id,))

        # Fetch one result
        result = cursor.fetchone()

        if result:
            print("Student already exists")
            return

        cursor.execute(f'''
        INSERT INTO {STUDENT_TABLE} (
            {STUDENT_ID}, 
            {STUDENT_EMAIL}, 
            {STUDENT_FIRST_NAME}, 
            {STUDENT_LAST_NAME}, 
            {STUDENT_COUNTRY},
            {STUDENT_STUDY_LEVEL},
            {STUDENT_COURSE}
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student.student_id, 
              student.email, 
              student.first_name, 
              student.last_name, 
              student.country, 
              student.course,
              student.level
            ))
        conn.commit()
        conn.close()
        print("Student added successfully")

    
    def check_document_exists(self, doc: StudentDocument):
        conn, cursor = get_conn_and_cursor(self.db)

        cursor.execute(f'''
        SELECT 1 FROM {DOC_TABLE}
            WHERE {DOC_STUDENT_ID} = ? AND {DOC_FILE_NAME} = ? AND {DOC_UNIVERSITY_NAME} = ?
            ''', (doc.student_id, doc.file_name, doc.university_name))

        result = cursor.fetchone()
        conn.close()

        return result is not None


    def add_student_doc(self, doc: StudentDocument):
        conn, cursor = get_conn_and_cursor(self.db)
        result = self.check_document_exists(
            doc.student_id, doc.content, doc.university_name
        )
        if result:
            print("Document already exists")
            return

        cursor.execute(f'''
        INSERT INTO {DOC_TABLE} (
            {DOC_STUDENT_ID},
            {DOC_FILE_NAME},
            {DOC_SUMMARY},
            {DOC_CONTENT},
            {DOC_UNIVERSITY_NAME}
        )
        VALUES (?, ?, ?, ?, ?)
        ''', (
            str(doc.student_id), 
            doc.file_name, 
            doc.summary, 
            doc.content,
            doc.university_name
        ))
        
        conn.commit()


    def retrieve_student(self, s_id: str):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT * FROM {STUDENT_TABLE}
        WHERE {STUDENT_ID} = ?
        ''', (s_id,))
        student_data = cursor.fetchone()
        conn.close()

        if student_data:
            student = Student(*student_data)
            return student
        return None


    def retrieve_student_doc(self, s_id: str):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT * FROM {DOC_TABLE}
        WHERE {DOC_STUDENT_ID} = ?
        ''', (s_id,))
        doc_data = cursor.fetchone()
        conn.close()

        if doc_data:
            doc = StudentDocument(*doc_data)
            return doc
        return None
    

    def retrieve_student_docs(self, s_id: str):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT * FROM {DOC_TABLE}
        WHERE {DOC_STUDENT_ID} = ?
        ''', (s_id,))
        doc_data = cursor.fetchall()
        conn.close()

        if doc_data:
            docs = [StudentDocument(*doc) for doc in doc_data]
            return docs
        return None
    

    def check_student_document_exists(self, d: StudentDocument):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT 1 FROM {DOC_TABLE}
        WHERE {DOC_STUDENT_ID} = ? AND {DOC_FILE_NAME} = ? AND {DOC_UNIVERSITY_NAME} = ?
        ''', (d.student_id, d.file_name, d.university_name))
        result = cursor.fetchone()
        conn.close()

        return result is not None


    def update_student_doc(self, doc: StudentDocument):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        UPDATE {DOC_TABLE}
        SET {DOC_SUMMARY} = ? AND {DOC_CONTENT} = ?
        WHERE {DOC_STUDENT_ID} = ? AND {DOC_FILE_NAME} = ? AND {DOC_UNIVERSITY_NAME} = ?
        ''', (doc.summary, doc.content, doc.student_id, doc.file_name, doc.university_name))
        conn.commit()
        conn.close()
        print("Document updated successfully")


    def add_university(self, university: University):
        conn, cursor = get_conn_and_cursor(self.db)

        cursor.execute(f'''
        SELECT 1 FROM {UNIVERSITY_TABLE}
        WHERE {UNIVERSITY_WEBSITE} = ?
        ''', (university.website,))

        # Fetch one result
        result = cursor.fetchone()

        if result:
            print("University already exists")
            return

        cursor.execute(f'''
        INSERT INTO {UNIVERSITY_TABLE} (
            {UNIVERSITY_NAME},
            {UNIVERSITY_WEBSITE}
        )
        VALUES (?, ?)
        ''', (university.name, university.website))
        conn.commit()
        conn.close()
        print("University added successfully")
    

    def add_university_country(self, university_country: UniversityCountry):
        conn, cursor = get_conn_and_cursor(self.db)
        ## Add country if it doesn't exist

        cursor.execute(f'''
        SELECT 1 FROM {UNIVERSITY_COUNTRY_TABLE} 
        WHERE university_id = ? AND country_name = ?
        ''', (university_country.uni_id, university_country.country_name))
        
        # Fetch one result
        result = cursor.fetchone()

        if not result:
            print(f"Adding country to {UNIVERSITY_COUNTRY_TABLE} table")
            cursor.execute(f'''
            INSERT INTO {UNIVERSITY_COUNTRY_TABLE} (
                {UNIVERSITY_COUNTRY_UNI_ID},
                {UNIVERSITY_COUNTRY_NAME},
                {UNIVERSITY_COUNTRY_ENTRY_REQ}
            )
            VALUES (?, ?, ?)
            ''', (
                university_country.uni_id, 
                university_country.country_name, 
                university_country.entry_req
            ))
            conn.commit()
            print("Country added successfully")
        else:
            print("Country already exists")
        
        conn.close()
    

    def add_university_countries(self, university_countries: List[UniversityCountry]):
        for univeristy_country in university_countries:
            print("Adding country: ", univeristy_country.country_name)
            self.add_university_country(
                univeristy_country
            )
        
        print("Countries added successfully")


    def retrieve_country(self, uni_id, country_name):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT * FROM {UNIVERSITY_COUNTRY_TABLE}
        WHERE {UNIVERSITY_COUNTRY_UNI_ID} = ? AND {UNIVERSITY_COUNTRY_NAME} = ?
        ''', (uni_id, country_name))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return UniversityCountry(*result)
        return None
    
    def retrieve_university_countries(self, uni_id):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT * FROM {UNIVERSITY_COUNTRY_TABLE}
        WHERE {UNIVERSITY_COUNTRY_UNI_ID} = ?
        ''', (uni_id,))
        result = cursor.fetchall()
        conn.close()
        
        if result:
            return [UniversityCountry(*r) for r in result]
        return None
    
    def retrieve_university_courses(self, uni_id):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT * FROM {UNIVERSITY_COURSE_TABLE}
        WHERE {UNIVERSITY_COURSE_UNI_ID} = ?
        ''', (uni_id,))
        result = cursor.fetchall()
        conn.close()
        
        if result:
            return [UniversityCourse(*r) for r in result]
        return None


    def check_country_structured_requirements(self, name, uni_id):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT {UNIVERSITY_COUNTRY_ENTRY_REQ_JSON} FROM {UNIVERSITY_COUNTRY_TABLE}
        WHERE {UNIVERSITY_COUNTRY_UNI_ID} = ? AND {UNIVERSITY_COUNTRY_NAME} = ?
        ''', (uni_id, name))
        result = cursor.fetchone()[0]
        conn.close()

        return result


    def check_course_structured_requirements(self, uni_course: UniversityCourse):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT {UNIVERSITY_COURSE_ENTRY_REQ_JSON} FROM {UNIVERSITY_COURSE_TABLE}
        WHERE {UNIVERSITY_COURSE_UNI_ID} = ? AND {UNIVERSITY_COURSE_NAME} = ?
        ''', (uni_course.uni_id, uni_course.name))
        result = cursor.fetchone()[0]
        conn.close()

        return result


    def update_country(self, uni_country: UniversityCountry):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        UPDATE {UNIVERSITY_COUNTRY_TABLE}
        SET {UNIVERSITY_COUNTRY_ENTRY_REQ_JSON} = ?
        WHERE {UNIVERSITY_COUNTRY_UNI_ID} = ? AND {UNIVERSITY_COUNTRY_NAME} = ?
        ''', (
            uni_country.entry_req_json, 
            uni_country.uni_id, 
            uni_country.country_name
        ))
        conn.commit()
        conn.close()
        print("Country details updated successfully")


    def add_univerisity_course(self, university_course: UniversityCourse):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT 1 FROM {UNIVERSITY_COURSE_TABLE} 
        WHERE {UNIVERSITY_COURSE_UNI_ID} = ? AND {UNIVERSITY_COURSE_NAME} = ?
        ''', (university_course.uni_id, university_course.name))
        
        # Fetch one result
        result = cursor.fetchone()

        if not result:
            print(f"Adding course to {UNIVERSITY_COURSE_TABLE} table")
            cursor.execute(f'''
            INSERT INTO {UNIVERSITY_COURSE_TABLE} (
                {UNIVERSITY_COURSE_UNI_ID},
                {UNIVERSITY_COURSE_NAME},
                {UNIVERSITY_COURSE_ENTRY_REQ}
            )
            VALUES (?, ?, ?)
            ''', (university_course.uni_id, university_course.name, university_course.entry_req))
            conn.commit()
            print("Course added successfully")
        else:
            print("Course already exists")
        

    def add_university_courses(self, uni_courses: List[UniversityCourse]):
        for uni_course in uni_courses:
            print("Adding course: ", uni_course.name)
            self.add_univerisity_course(uni_course)
        
        print("Courses added successfully")
    

    def retrieve_course(self, uni_id, course_name):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT * FROM {UNIVERSITY_COURSE_TABLE}
        WHERE {UNIVERSITY_COURSE_UNI_ID} = ? AND {UNIVERSITY_COURSE_NAME} = ?
        ''', (uni_id, course_name))
        result = cursor.fetchone()[0]
        conn.close()
        
        if result:
            return UniversityCourse(*result)
        return None

    
    def update_course(self, uni_course: UniversityCourse):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        UPDATE {UNIVERSITY_COURSE_TABLE}
        SET {UNIVERSITY_COURSE_ENTRY_REQ_JSON} = ?
        WHERE {UNIVERSITY_COURSE_UNI_ID} = ? AND {UNIVERSITY_COURSE_NAME} = ?
        ''', (uni_course.entry_req_json, uni_course.uni_id, uni_course.name))
        conn.commit()
        conn.close()
        print("Course details updated successfully")


if __name__ == '__main__':
    dbm = DatabaseManager()
    dbm.create_db()