import streamlit as st
from data import (
    load_student_data, 
    load_university_data, 
    load_universities,
    update_students_db
)

from agents.utils import (
    get_llm_response
)

from decision_agent import (
    get_student_decison_for_university
)
import random

def test_func():
    st.write("Hello World")

def add_student():
    student_id = f"{random.choice([101, 102, 103, 104])}{random.randint(10000, 99999)}"
    with st.form(key='student_data_form'):
        first_name = st.text_input("First Name", key='first_name')
        last_name = st.text_input("Last Name", key='last_name')
        email = st.text_input("Email", key='email')
        course = st.text_input("Course", key='course')
        country = st.text_input("Country", key='country')


        student_data = {
            'student_id': student_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'course': course,
            'country': country,
        }

        st.form_submit_button(
            "Submit", 
            on_click=update_students_db,
            args=(student_data,)
        )


def uploaded_file_handler(student_id):
    uploaded_file = st.session_state['uploaded_file']
    if uploaded_file:
        st.markdown(f"Uploaded File Handler for Student ID: {student_id}")
        st.markdown(f"Uploaded File: {uploaded_file.name}")
    else:
        st.markdown(f"No file uploaded for Student ID: {student_id}")


def upload_file(student_id):
    st.markdown(f"Upload File for Student ID: {student_id}")
    st.file_uploader(
        "Upload a Zip file",
        key='uploaded_file',
        on_change=uploaded_file_handler,
        args=(student_id,)
    )


def manage_student_data():
    st.selectbox(
        'Add/Update Student Data', 
        ['Add Student Data', 'Update Student Data'],
        key='add_update_student_data',
        index=None,
    )

    add_or_update = st.session_state['add_update_student_data']
    if add_or_update == 'Add Student Data':
        st.markdown("#### Upload a New Student Data")
        add_student()
        

    elif add_or_update == 'Update Student Data':
        st.markdown("#### Update Student Data")
        students = load_student_data()
        st.selectbox(
            'Select Student ID', 
            list(students.keys()), 
            index=None,
            key='student_id',
        )
    
    student_id = st.session_state.get('student_id')
    if student_id and add_or_update:
        if add_or_update == 'Update Student Data':
            students = load_student_data()
            student = students[student_id]
            name = student['first_name'] + " " + student['last_name']
            st.markdown(f"#### Update {name} Data")
        else:
            name = "New Student"
            st.markdown(f"#### Add New Student Data")



        upload_file(student_id)


def evaluate_student():
    assert st.session_state['university'], st.error("Please select a university first")
    university_name = st.session_state['university']
    student_id = st.session_state['student_id']
    if not student_id:
        st.error("Please select a student first")
        return
    st.markdown(f"Evaluate Student ID: {student_id}")
    student_data = load_student_data()[student_id]


    with st.spinner('Evaluating Student...'):
        student_decision_response = get_student_decison_for_university(
            university_name,
            student_data
        )
    

    student_decision = student_decision_response['student_decision']
    st.write(f"##### Student Decision\n{student_decision}")

    student_info = st.session_state.get('student_info', {})
    student_info[student_id] = {**student_data, **student_decision_response}
    st.session_state['student_info'] = student_info
    st.session_state['student_evaluated'] = True


def reset_student_session_data():
    st.session_state['student_evaluated'] = False



def student_evaluator_flow():
    students = load_student_data()
    print(list(students.keys()))
    st.selectbox(
        'Select Student to Evaluate', 
        list(students.keys()),
        key='student_id',
        index=None,
        on_change=reset_student_session_data
    )

    if st.session_state['student_id']:
        evaluate = st.button("Evaluate Student")
        if evaluate:
            evaluate_student()
        
        elif st.session_state.get('student_evaluated', False):
            student_decision = st.session_state['student_info'][st.session_state['student_id']]['student_decision']
            st.write(f"##### Student Decision\n{student_decision}")



def get_session_messages() -> list:
    messages = st.session_state.get("messages", [])
    student_id = st.session_state.get("student_id", None)
    eval_message = None
    if student_id and 'student_evaluated' in st.session_state and st.session_state['student_evaluated']:
        student_data: dict = st.session_state.get("student_info", {}).get(student_id, {})
        content = f"""
        #### Student Information
        - **Name**: {student_data.get('first_name', '')} {student_data.get('last_name', '')}
        - **Email**: {student_data.get('email', '')}
        - **Course**: {student_data.get('course', '')}
        - **Country**: {student_data.get('country', '')}
        
        #### Student Qualifications
        - **Qualifications**: {student_data.get('student_qualifications', '')}

        #### University Requirements
        - **University Requirements**: {student_data.get('university_requirements', '')}

        #### University Decision
        - **Decision**: {student_data.get('student_decision', '')}
        """
        eval_message = {"role": "user", "student": student_id, "content": content}


    if len(messages) == 0:
        return [eval_message] if eval_message else []
    
    if not eval_message:
        return messages
    
    if 'student' in messages[0] and messages[0]['student'] == student_id:
        return messages
    return [eval_message]


def chatbot():
    messages = get_session_messages()

    if chat_prompt := st.chat_input(
        "Ask me anything about the student application evaluation...",
        disabled='student_id' not in st.session_state
    ):
        messages.append({"role": "user", "content": chat_prompt})

        for message in messages:
            if 'student' in message or message['role'] == 'system':
                continue
            st.chat_message(message['role']).markdown(message['content'])
        
        with st.spinner('Fetching an answer...'):
            response = get_llm_response(
                chat_prompt, 
                system_prompt="You are an expert in student application evaluation.",
                messages=[{"role": m["role"], "content": m["content"]} for m in messages]
            )

        messages.append({"role": "assistant", "content": response})
        st.session_state["messages"] = messages
        st.chat_message("assistant").markdown(response)
