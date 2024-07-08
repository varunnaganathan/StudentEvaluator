import io
import os
import streamlit as st
from data import (
    update_students_db
)

from settings import (
    student_data_dir
)

from zipfile import ZipFile

from decision_agent import (
    get_student_data
)

from data_processing_utils import (
    ocr_student_documents
)

import asyncio

st.title("Insert Student")

def add_student():

    with st.form(key='add_student_form', clear_on_submit=True):
        st.markdown('##### Add a Student to the Database')
        
        cols = st.columns(3)
        
        cols[0].text_input('Student ID', key='form_student_id')
        cols[1].text_input('First Name', key='first_name')
        cols[2].text_input('Last Name', key='last_name')
        
        st.text_input('Email', key='email')

        cols = st.columns(2)
        cols[0].text_input('Course', key='course')
        cols[1].text_input('Country', key='country')

        st.file_uploader(
            "Upload Document Zip File", 
            type=['zip'], 
            key='data_file', 
            accept_multiple_files=False, 
            help='Upload a zip file containing student\'s relevant documents'
        )
        
        student_data = {
            'student_id': st.session_state['form_student_id'],
            'first_name': st.session_state['first_name'],
            'last_name': st.session_state['last_name'],
            'email': st.session_state['email'],
            'course': st.session_state['course'],
            'country': st.session_state['country'],
        }

        data_file = st.session_state.get('data_file')

        submit = st.form_submit_button('Add Student')
        if submit:
            validate_and_submit(student_data, data_file)
            return student_data['student_id']
    
    return None


def validate_and_submit(data, data_file):
    print(data, data_file)
    required_fields = ['student_id', 'course', 'country']
    error = False
    for req_field in required_fields:
        if not data[req_field]:
            st.error(f"Field '{req_field}' is required")
            error = True


    if not data_file:
        st.error("Please upload a document file")
        error = True

    if error:
        return False


    update_students_db(data)
    process_zip_file(data['student_id'], data_file)



def process_zip_file(student_id, data_file):
    print("Processing Zip File")
    print(student_id, data_file)
    zip_dir = os.path.join(student_data_dir, student_id)
    with st.spinner("Processing Zip File"):
        os.makedirs(zip_dir, exist_ok=True)
        with io.BytesIO(data_file.read()) as z:
            with ZipFile(data_file, 'r') as z:
                z.extractall(zip_dir)
                st.success("Zip File Processed Successfully")

    folder_name = os.listdir(zip_dir)[0]
    for item in os.listdir(os.path.join(zip_dir, folder_name)):
        source_path = os.path.join(zip_dir, folder_name, item)
        dest_path = os.path.join(zip_dir, item)
        os.rename(source_path, dest_path)

    os.rmdir(os.path.join(zip_dir, folder_name))


async def process_student_documents(student_id):
    ocr_student_documents(student_id)
    st.success("Student Documents OCRed Successfully")
    get_student_data(student_id)
    st.success("Student Data Processed Successfully")


student_added_id = add_student()
if student_added_id:
    asyncio.run(process_student_documents(student_added_id))
