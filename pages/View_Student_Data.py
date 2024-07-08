import streamlit as st
from data import (
    load_student_data
)

from decision_agent import (
    get_student_data
)



def show_student():
    students = load_student_data()
    student_id = st.selectbox(
        'Select Student to View', 
        list(students.keys()),
        index=None
    )
    if student_id:
        student_info = students[student_id]
        student_data = get_student_data(student_id)
        st.write(f"##### Student ID: {student_id}")
        first_name = student_info['first_name']
        last_name = student_info['last_name']
        email = student_info['email']
        course = student_info['course']
        country = student_info['country']

        st.write(f"##### Student Information")
        st.write(f"First Name: {first_name}")
        st.write(f"Last Name: {last_name}")
        st.write(f"Email: {email}")
        st.write(f"Course: {course}")
        st.write(f"Country: {country}")

        st.write(f"##### Student Data")
        st.write(student_data)



st.title("View Student Data")
show_student()