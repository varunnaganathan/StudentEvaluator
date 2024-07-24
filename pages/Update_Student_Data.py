import asyncio
import streamlit as st

from data import (
    load_student_data
)

from decision_agent import (
    get_student_data
)

from evaluator_app.data_processing_utils import (
    ocr_student_documents
)


def update_student_data():
    students = load_student_data()

    with st.form(key='update_student_form', clear_on_submit=True):
        st.markdown('##### Upload Student Data to Update')

        st.selectbox(
            'Select Student to Update', 
            list(students.keys()),
            index=None,
            key='student_id'
        )

        st.file_uploader(
            "Upload Document Zip File", 
            type=['zip'], 
            key='data_file', 
            accept_multiple_files=False, 
            help='Upload a zip file containing student\'s relevant documents'
        )
        
        update = st.form_submit_button("Update Student Data")

        if update:
            student_id = st.session_state['student_id']
            student_data = get_student_data(student_id)
            student_data['student_id'] = student_id
            student_data['data_file'] = st.session_state.get('data_file')
            return student_id
    
    return None


async def process_student_documents(student_id):
    ocr_student_documents(student_id)
    st.success("Student Documents OCRed Successfully")
    get_student_data(student_id)
    st.success("Student Data Processed Successfully")



st.title("Update Student Data")

student_updated_id = update_student_data()



if student_updated_id:
    asyncio.run(process_student_documents(student_updated_id))
