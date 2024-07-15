import ast
import json
import pandas as pd
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


def get_supporting_doc_path(doc_id):
    student_id = st.session_state.get('student_id', None)
    if not student_id:
        st.error("Student ID not found")
        return
    doc_id_to_f_name = json.load(open(os.path.join(student_data_dir, 'student_doc_map_inv.json')))
    file_name = doc_id_to_f_name[doc_id] if doc_id in doc_id_to_f_name else "Not Available"
    file_path = os.path.join(student_data_dir, str(student_id), file_name).split('.txt')[0] + ".pdf"
    return file_path if os.path.exists(file_path) else "File Not Found"



def view_pdf(f, count):
    viewing_pdf = st.session_state.get(f"viewing_pdf_{count}", False)
    if viewing_pdf:
        pdf_viewer(f, key=f"pdf_viewer_{count}")
        button = st.button(
            "Close",
            key=f"close_{count}"
        )
        if button:
            st.session_state[f'viewing_pdf_{count}'] = False
            st.rerun()


def set_viewing_pdf(i):
    st.session_state[f'viewing_pdf_{i}'] = True


def show_df(df):
    col_widths = {
        "Requirement": 2,
        "Qualification": 2,
        "Decision": 2,
        "Reason": 2,
        "Text": 2,
        "Document": 2
    }
    cols = st.columns(list(col_widths.values()))
    df_cols = list(col_widths.keys())

    for col, df_col in zip(cols, df_cols):
        col.markdown(f"###### {df_col}")

    for i, row in df.iterrows():
        cols = st.columns(list(col_widths.values()))
        for col, df_col in zip(cols[:-1], df_cols[:-1]):
            col.write(row[df_col])
        
        disabled = st.session_state.get(f"viewing_pdf_{i}", False)
        supporting_doc = row["Document"]
        cols[-1].button(
            f"{'View' if supporting_doc != 'Not Available' else 'NA'}",
            key=f"view_pdf_{i}",
            disabled=disabled or supporting_doc == "Not Available",
            on_click=set_viewing_pdf,
            args=(i,)
        )
        
    
    for i, row in df.iterrows():
        view_pdf(row["Document"], i)

    # st.dataframe(
    #     df.drop(columns=["Document"]),
    #     hide_index=True
    # )
    # documents = list({d for d in df["Document"].tolist()})
    # for i in range(0, len(documents), 3):
    #     button = st.button(
    #         f"View {documents[i].split(os.sep)[-1].split('.pdf')[0]}",
    #         key=f"view_pdf_{i}"
    #     )
    #     if button:
    #         view_pdf(documents[i], i)
        


def show_decision_pairs(decision_pairs):
    
    if '```' in decision_pairs:
        st.markdown("###### Decision Details")
        decision_pairs = ast.literal_eval(decision_pairs.split('```')[1])

        rows = list()
        for _, decision_key in enumerate(decision_pairs):
            decision_value = decision_pairs[decision_key]
            requirement = decision_value['requirement']
            qualification = decision_value['qualification'] + '\n' + decision_value['qualification_result']
            
            decision = decision_value['decision']
            decision_emoji = ":white_check_mark:" if decision == 'pass' else (':x:' if decision == 'fail' else (':question:' if decision == 'ambiguous' else ':grey_question:'))
            decision_emoji = "✅" if decision == 'pass' else ('❌' if decision == 'fail' else ('❓' if decision == 'ambiguous' else '❔'))
            decision = f"{decision_emoji}"

            reasoning = decision_value['reasoning']
            supporting_text = decision_value['supporting_text'] if 'supporting_text' in decision_value else "Not Available"
            
            support_doc_id = decision_value['support_doc_id'] if 'support_doc_id' in decision_value else "Not Available"
            doc_path = get_supporting_doc_path(support_doc_id)

            rows.append(
                {
                    "Requirement": requirement,
                    "Qualification": qualification,
                    "Decision": decision,
                    "Reason": reasoning,
                    "Text": supporting_text,
                    "Document": doc_path
                }
            )
        
        df = pd.DataFrame(rows)
        show_df(df)
    else:
        st.write("Unable to show decision details")


def show_university_requirements(uni_reqs: str):
    def print_dict(d, indent=0):
        for key, value in d.items():
            st.write(f'{"#"*(indent + 4)}' + ' ' + str(key))
            if isinstance(value, dict):
                print_dict(value, indent + 1)
            else:
                st.write(str(value))

    uni_reqs = json.loads(uni_reqs)
    with st.expander("University Requirements"):
        print_dict(uni_reqs)


def show_final_decision_report(final_decision_report):
    with st.expander("Final Decision Report"):
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
        show_decision_pairs(student_decision_pairs)
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
    final_decision_report = get_student_final_decision(student_decision_pairs)

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
    
    show_decision_pairs(student_decision_pairs)

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

    student_id = st.session_state.get('student_id', None)
    if student_id:
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
