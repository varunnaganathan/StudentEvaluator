import uuid
from settings import db_file
import sqlite3
import os
from llama_index.core.schema import Document
from storage.constants import (
    DOC_CONTENT,
    DOC_FILE_NAME,
    DOC_ID,
    DOC_STUDENT_ID,
    DOC_SUMMARY,
    DOC_TABLE,
    STUDENT_FIRST_NAME,
    STUDENT_LAST_NAME,
    STUDENT_EMAIL,
    STUDENT_COUNTRY,
    STUDENT_TABLE,
    STUDENT_ID,
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
            {STUDENT_COUNTRY} TEXT NOT NULL
        )
        ''')

        # Create Docs table
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {DOC_TABLE} (
            {DOC_ID} INTEGER PRIMARY KEY AUTOINCREMENT,
            {DOC_FILE_NAME} TEXT NOT NULL,
            {DOC_SUMMARY} TEXT NOT NULL,
            {DOC_CONTENT} TEXT NOT NULL,
            {DOC_STUDENT_ID} TEXT NOT NULL,
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
            PRIMARY KEY ({UNIVERSITY_COUNTRY_UNI_ID}, {UNIVERSITY_COUNTRY_COUNTRY_NAME}),
            FOREIGN KEY ({UNIVERSITY_COUNTRY_UNI_ID}) REFERENCES {UNIVERSITY_TABLE}({UNIVERSITY_WEBSITE})
        )
        ''')

        # Create {UNIVERSITY_COURSE_TABLE}s table
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {UNIVERSITY_COURSE_TABLE} (
            {UNIVERSITY_COURSE_NAME} TEXT NOT NULL,
            {UNIVERSITY_COURSE_ENTRY_REQ} TEXT NOT NULL,
            {UNIVERSITY_COUNTRY_UNI_ID} TEXT NOT NULL,
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


    def add_student(self, s_id, email, first_name, last_name, country):
        conn, cursor = get_conn_and_cursor(self.db)

        cursor.execute(f'''
        SELECT 1 FROM {STUDENT_TABLE}
        WHERE {STUDENT_ID} = ?
        ''', (s_id,))

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
            {STUDENT_COUNTRY}
        )
        VALUES (?, ?, ?, ?, ?)
        ''', (s_id, email, first_name, last_name, country))
        conn.commit()
        conn.close()
        print("Student added successfully")

    
    def check_document_exists(self, student_id, doc: Document):
        conn, cursor = get_conn_and_cursor(self.db)

        cursor.execute(f'''
        SELECT 1 FROM {DOC_TABLE}
            WHERE {DOC_STUDENT_ID} = ? AND {DOC_FILE_NAME} = ?
            ''', (student_id, doc.metadata[DOC_FILE_NAME]))


        result = cursor.fetchone()
        conn.close()

        return result is not None


    def add_student_doc(self, student_id, doc: Document):
        conn, cursor = get_conn_and_cursor(self.db)
        result = self.check_document_exists(student_id, doc)
        if result:
            print("Document already exists")
            return

        cursor.execute(f'''
        INSERT INTO {DOC_TABLE} (
            {DOC_STUDENT_ID},
            {DOC_FILE_NAME},
            {DOC_SUMMARY},
            {DOC_CONTENT}
        )
        VALUES (?, ?, ?, ?)
        ''', (str(student_id), doc.metadata[DOC_FILE_NAME], doc.metadata[DOC_SUMMARY], doc.text))
        
        conn.commit()


    def retrieve_student(self, s_id):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT {STUDENT_FIRST_NAME}, {STUDENT_LAST_NAME}, {STUDENT_EMAIL}, {STUDENT_COUNTRY} FROM {STUDENT_TABLE}
        WHERE {STUDENT_ID} = ?
        ''', (s_id,))
        f_name, l_name, email, country = cursor.fetchone()
        country = country if country else 'Not specified'

        conn.close()
        return f_name, l_name, email, country
    

    def retrieve_student_doc(self, s_id):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT {DOC_SUMMARY} FROM {DOC_TABLE}
        WHERE {DOC_STUDENT_ID} = ?
        ''', (s_id,))
        doc_content = cursor.fetchone()[0]
        conn.close()
        return doc_content
    

    def retrieve_student_docs(self, s_id):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT {DOC_SUMMARY} FROM {DOC_TABLE}
        WHERE {DOC_STUDENT_ID} = ?
        ''', (s_id,))
        doc_contents = [i[0] for i in cursor.fetchall()]
        conn.close()
        return doc_contents


    def add_university(self, university_id, university_name):
        conn, cursor = get_conn_and_cursor(self.db)

        cursor.execute(f'''
        SELECT 1 FROM {UNIVERSITY_TABLE}
        WHERE {UNIVERSITY_WEBSITE} = ?
        ''', (university_id,))

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
        ''', (university_name, university_id))
        conn.commit()
        conn.close()
        print("University added successfully")
    

    def add_university_country(self, university_id, country_name, entry_requirements):
        conn, cursor = get_conn_and_cursor(self.db)
        ## Add country if it doesn't exist

        cursor.execute(f'''
        SELECT 1 FROM {UNIVERSITY_COUNTRY_TABLE} 
        WHERE university_id = ? AND country_name = ?
        ''', (university_id, country_name))
        
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
            ''', (university_id, country_name, entry_requirements))
            conn.commit()
            print("Country added successfully")
        else:
            print("Country already exists")
        
        conn.close()
    

    def add_university_countries(self, university_id, countries):
        for country_name, entry_requirements in countries.items():
            print("Adding country: ", country_name)
            self.add_university_country(
                university_id, 
                country_name, 
                entry_requirements
            )
        
        print("Countries added successfully")
    

    def retrieve_country_details(self, university_id, country_name):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT {UNIVERSITY_COUNTRY_ENTRY_REQ} FROM {UNIVERSITY_COUNTRY_TABLE}
        WHERE {UNIVERSITY_COUNTRY_UNI_ID} = ? AND {UNIVERSITY_COUNTRY_NAME} = ?
        ''', (university_id, country_name))
        entry_requirements = cursor.fetchone()[0]
        conn.close()
        return entry_requirements


    def add_univerisity_course(self, university_id, course_name, entry_requirements):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT 1 FROM {UNIVERSITY_COURSE_TABLE} 
        WHERE {UNIVERSITY_COURSE_UNI_ID} = ? AND {UNIVERSITY_COURSE_NAME} = ?
        ''', (university_id, course_name))
        
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
            ''', (university_id, course_name, entry_requirements))
            conn.commit()
            print("Course added successfully")
        else:
            print("Course already exists")
        

    def add_university_courses(self, university_id, courses):
        for course_name, entry_requirements in courses.items():
            print("Adding course: ", course_name)
            self.add_univerisity_course(university_id, course_name, entry_requirements)
        
        print("Courses added successfully")
    

    def retrieve_course_details(self, university_id, course_name):
        conn, cursor = get_conn_and_cursor(self.db)
        cursor.execute(f'''
        SELECT {UNIVERSITY_COURSE_ENTRY_REQ} FROM {UNIVERSITY_COURSE_TABLE}
        WHERE {UNIVERSITY_COURSE_UNI_ID} = ? AND {UNIVERSITY_COURSE_NAME} = ?
        ''', (university_id, course_name))
        entry_requirements = cursor.fetchone()[0]
        conn.close()
        return entry_requirements