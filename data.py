import os
import streamlit as st
import pandas as pd
import json
from settings import student_data_dir, university_data_dir


def update_students_db(student_data):
    student_id = student_data['student_id']
    student_data = {student_id: student_data}
    students = load_student_data()
    students.update(student_data)
    students = pd.DataFrame(list(students.values()))
    students.to_excel(os.path.join(student_data_dir, "Students.xlsx"), index=False)
    load_student_data.clear()
    st.session_state['student_id'] = student_id


@st.cache_data
def load_student_data():
    students = pd.read_excel(os.path.join(student_data_dir, "Students.xlsx"))
    students = {
        str(r['student_id']): dict(r) for _, r in students.iterrows()
    }
    print("Number of Students: ", len(students))
    print("Students: ", list(students.keys()))
    return students


@st.cache_data
def load_university_data(university_name):
    uni_reqs = json.load(open(os.path.join(university_data_dir, university_name, "course_x_country_requirements.json")))
    return uni_reqs


@st.cache_data
def load_universities():
    universities = pd.read_excel(os.path.join(university_data_dir, "universities.xlsx"))
    universities = {
        r['uni_name']: dict(r) for _, r in universities.iterrows()
    }
    return universities