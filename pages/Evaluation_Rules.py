import streamlit as st
from settings import eval_rules_dir
import json
import os


def get_rules():
    rules = json.load(open(os.path.join(eval_rules_dir, "rules.json")))
    return rules


def get_schema():
    schema = json.load(open(os.path.join(eval_rules_dir, "schema.json")))
    return schema


def show_evaluation_rules():
    rules = get_rules()
    for i, rule in enumerate(rules):
        st.write(f"### Rule {i+1}")
        st.write(f"**Type**: {rule['type']}")
        st.write(f"**Description**: {rule['description']}")
    
    add_rule = st.button('Add Student Application Rule', key='add_rule_button')
    if add_rule:
        st.session_state['add_rule'] = True
    
    if st.session_state.get('add_rule', False):
        add_evaluation_rule()


def add_evaluation_rule():
    schema = get_schema()
    rules: list = get_rules()
    new_rule_id = len(rules) + 1
    
    properties: dict = schema['properties']

    with st.form(key='add_rule_form', clear_on_submit=True):
        for property, property_attributes in properties.items():
            property_type = property_attributes['type']
            property_description = property_attributes['description']

            if property in schema:
                st.selectbox(
                    property,
                    options=schema[property],
                    key=property,
                    help=property_description
                )
            elif property_type == 'string':
                st.text_input(
                    property,
                    key=property,
                    help=property_description
                )

        submit = st.form_submit_button('Add a New Rule')
        if submit:
            print("Adding Rule")
            new_rule = {property: st.session_state[property] for property in properties}
            new_rule['id'] = new_rule_id
            rules.append(new_rule)
            print("Added Rule: ", new_rule)
            json.dump(rules, open(os.path.join(eval_rules_dir, "rules.json"), 'w'), indent=4)
            print("Rules Updated")
            print(get_rules()[-1])
            st.session_state['add_rule'] = False
            st.rerun()

st.markdown("## Student Application Evaluation Rules")
show_evaluation_rules()