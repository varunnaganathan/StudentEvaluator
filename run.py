from argparse import ArgumentParser
from tqdm.auto import tqdm
from agents.db_agent import DatabaseAgent
import pandas as pd
from settings import students_df_path


def parse_args():
    arg_parser = ArgumentParser()
    arg_parser.add_argument('--uni_name', type=str, default='NorthUmbria')
    arg_parser.add_argument('--db_overwrite', action='store_true')
    arg_parser.add_argument('--multithreading', action='store_true')
    args = arg_parser.parse_args()
    return args


if __name__ == '__main__':
    
    args = parse_args()
    dba = DatabaseAgent(uni_name=args.uni_name, db_overwrite=args.db_overwrite)
    uni_name, uni_id = dba.university_data_store.name, dba.university_data_store.website
    dba.add_university(uni_name)
    dba.add_university_courses()
    dba.add_university_courses_structure()
    dba.add_university_countries()
    dba.add_university_countries_structure()
    

    students_df = pd.read_excel(students_df_path)
    for i, r in students_df.iterrows():
        dba.add_student(dict(r))

    for i, r in tqdm(students_df.iterrows(), total=students_df.shape[0]):
        if not isinstance(r['course'], float):
            course_name = r['course']
            student_id = str(r['student_id'])
            student = dba.get_student(student_id)
            # print(dba.generate_evaluation_prompt(student_id, course_name))
            dba.evaluate_student(student)
            print("-"*100)
            print("-"*100)