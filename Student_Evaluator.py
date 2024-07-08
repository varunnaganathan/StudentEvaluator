import streamlit as st
import ui_utils
from data import load_student_data, load_university_data, load_universities

st.title('Student Application Evaluator')


universities = load_universities()
uni_name_to_id = {u['name']: u['uni_name'] for u in universities.values()}
university_id = uni_name_to_id[st.selectbox(
    'Select University', 
    list(uni_name_to_id.keys()), 
    key='university_name',
)]

st.session_state['university'] = university_id
ui_utils.student_evaluator_flow()
ui_utils.chatbot()