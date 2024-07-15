import json
import streamlit as st
from data import (
    load_student_data, 
)
import os
from settings import student_data_dir
from streamlit_pdf_viewer import pdf_viewer

from agents.utils import (
    get_llm_response
)

from decision_agent import (
    get_student_data,
    get_student_data_keys,
    get_student_final_decision,
    get_student_decision_keys,
    get_university_requirements
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


def show_decision_pairs(decision_pairs, student_data):
    import ast
    if '```' in decision_pairs:
        # with st.expander("Show Decision Data"):
            
        decision_pairs = ast.literal_eval(decision_pairs.split('```')[1])
        for i, key in enumerate(decision_pairs):
            value = decision_pairs[key]
            st.markdown(f"##### Decision-based on {key}")
            show_decision_pair(value, student_data, i+1)


def view_pdf(f, count):
    # print("Viewing PDF: ", f)
    # print("Count: ", count)
    viewing_pdf = st.session_state.get(f"viewing_pdf_{count}", False)
    if viewing_pdf:
        pdf_viewer(f, key=f"pdf_viewer_{count}")
        button = st.button(
            "Close",
            key=f"close_{count}"
        )
        if button:
            st.session_state['viewing_pdf'] = False
            st.rerun()
    else:
        st.button(
            "View PDF",
            on_click=lambda: st.session_state.update(viewing_pdf=True),
            key=f"view_{count}"
        )

        
def show_decision_pair(decision_pair, student_data, count):
    file_available = False
    student_id = student_data['student_id']
    doc_id_to_f_name = json.load(open(os.path.join(student_data_dir, 'student_doc_map_inv.json')))


    decision = decision_pair['decision'] if 'decision' in decision_pair else "Not Available"
    decision_emoji = ":white_check_mark:" if decision == 'pass' else (':x:' if decision == 'fail' else (':question:' if decision == 'ambiguous' else ':grey_question:'))
    st.write(f"Decision: {decision} {decision_emoji}")
    support_doc_id = decision_pair['support_doc_id'] if 'support_doc_id' in decision_pair else "Not Available"
    file_name = doc_id_to_f_name[support_doc_id] if support_doc_id in doc_id_to_f_name else "Not Available"
    st.write(f"Support File Name: {file_name}")
    
    file_path = os.path.join(student_data_dir, str(student_id), file_name).split('.txt')[0] + ".pdf"
    if os.path.exists(file_path):
        # st.write(f"Support File Path: {file_path}")
        view_pdf(file_path, count)


    supporting_text = decision_pair['supporting_text'] if 'supporting_text' in decision_pair else "Not Available"
    st.write(f"Supporting Text: {supporting_text}")

    return file_available




def show_university_requirements(uni_reqs: str):
    def print_dict(d, indent=0):
        for key, value in d.items():
            st.write('##### ' + str(key))
            if isinstance(value, dict):
                print_dict(value, indent + 1)
            else:
                st.write(str(value))

    uni_reqs = json.loads(uni_reqs)
    print_dict(uni_reqs)


def show_final_decision_report(final_decision_report):
    st.write(f"##### Final Decision Report\n{final_decision_report}")


def evaluate_student(re_evaluate=False):
    assert st.session_state['university'], st.error("Please select a university first")
    university_name = st.session_state['university']
    student_id = st.session_state['student_id']
    if not student_id:
        st.error("Please select a student first")
        return
    st.markdown(f"Evaluate Student ID: {student_id}")
    student_data = load_student_data()[student_id]

    student_evaluated = st.session_state.get('student_evaluated', False)
    print("Student Evaluated: ", student_evaluated)
    if student_evaluated and not re_evaluate:
        student_info = st.session_state.get('student_info', {})
        student_response = student_info[student_id]['student_decision']

        university_requirements = student_response['university_requirements']
        student_decision_pairs = student_response['student_decision_pairs']
        final_decision_report = student_response['student_decision']

        show_university_requirements(university_requirements)
        show_decision_pairs(student_decision_pairs, student_data)
        show_final_decision_report(final_decision_report)
    else:
        st.session_state['evaluating'] = True
        with st.spinner('Evaluating Student...'):
            student_decision_response = get_decision_result(
                university_name,
                student_data
            )

        student_info = st.session_state.get('student_info', {})
        student_info[student_id] = {
            "student_data": student_data,
            "student_decision": student_decision_response
        }
        st.session_state['student_info'] = student_info
        st.session_state['evaluating'] = False
    
    st.session_state['student_evaluated'] = True


def reset_student_session_data():
    st.session_state['student_evaluated'] = False


def get_decision_result(university_name, student_data):

    university_requirements = get_university_requirements(university_name, student_data)
    
    student_id = str(student_data['student_id'])
    student_qualifications = get_student_data(student_id)
    student_value_pairs = get_student_data_keys(university_requirements, student_qualifications)
    student_decision_pairs = get_student_decision_keys(student_value_pairs, student_id)

    # student_decision_pairs = {
    #     "English Proficiency": {
    #         "decision": "pass",
    #         "support_doc_id": "1",
    #         "supporting_text": "Student has met the English Proficiency requirement"
    #     },
    #     "Academic Qualifications": {
    #         "decision": "pass",
    #         "support_doc_id": "2",
    #         "supporting_text": "Student has met the Academic Qualifications requirement"
    #     },
    #     "Work Experience": {
    #         "decision": "fail",
    #         "support_doc_id": "3",
    #         "supporting_text": "Student has not met the Work Experience requirement"
    #     }
    # }
    # student_decision_pairs = f"```{student_decision_pairs}```"
    
    show_university_requirements(university_requirements)
    show_decision_pairs(student_decision_pairs, student_data)

    final_decision_report = get_student_final_decision(student_decision_pairs)
    # final_decision_report = "Student has met all the requirements"
    show_final_decision_report(final_decision_report)


    response = {
        "university_requirements": university_requirements,
        "student_qualifications": student_qualifications,
        "student_value_pairs": student_value_pairs,
        "student_decision_pairs": student_decision_pairs,
        "student_decision": final_decision_report
    }
    return response


def student_evaluator_flow():
    students = load_student_data()
    print(list(students.keys()))
    st.selectbox(
        'Select Student to Evaluate', 
        list(students.keys()),
        key='student_id',
        on_change=reset_student_session_data,
        index=None,
    )
    student_info = st.session_state.get('student_info', {})
    student_id = st.session_state.get('student_id', None)
    student_evaluated = student_info and student_id in student_info

    print("Student Evaluated: ", student_evaluated)

    if st.session_state['student_id']:
        re_evaluate = False
        evaluate = st.button(
            "Evaluate Student"
        )
        if student_evaluated:
            re_evaluate = st.button(
                "Re-Evaluate Student"
            )

        if re_evaluate:
            evaluate_student(re_evaluate=True)

        elif evaluate or student_evaluated:
            evaluate_student()


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
