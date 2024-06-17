import json
import os
from tqdm.auto import tqdm
import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
from handlers.base import UniversityDataHandler
from settings import university_data_dir


courses_url = "https://london.northumbria.ac.uk/courses/"
course_url_prefix = "https://london.northumbria.ac.uk/course/"
country_entry_req_url = "https://london.northumbria.ac.uk/international-students/entry-requirements/"


def df_to_str(df, delim='|'):
    final_str = ""
    for _, r in df.iterrows():
        values = [f"{k}: {v}".format(k, v) for k, v in r.to_dict().items()]
        final_str += f" {delim} ".join(values) + "\n"
    
    return final_str


def get_table_data(table):
    rows = table.find_all('tr')
    table_data = []

    for row in rows:
        col_label = 'td' if row.find('td') else 'th'
        cols = row.find_all(col_label)
        cols = [ele.text.strip() for ele in cols]
        table_data.append([re.sub(r'\s+', ' ', ele).strip() for ele in cols if ele])
    
    return table_data


def get_text_in_div_class(soup, class_name):
    txt = ""
    for i in soup.find('div', class_=class_name):
        result = f"{i.text.strip()}\n"
        result = re.sub(r'\s+', ' ', result).strip()
        if result:
            txt += f"{result}\n"
    return txt


def get_soup(url):
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.content, 'html.parser')
    return None


def extract_entry_requirements(soup):
    entry_requirements = soup.find('div', id='entry-requirements')
    table = entry_requirements.find('table')
    if table is None:
        entry_req_str = entry_requirements.text
    else:
        table_data = get_table_data(table)

        # Create DataFrame
        header = ["Level"]
        if len(table_data[1]) <= 2:
            header += ["Requirement"]
            data = table_data
        else:
            header += table_data[0]
            data = table_data[1:]
        df = pd.DataFrame(data, columns=header)
        df = df.ffill()
        entry_req_str = df_to_str(df)
    # Extract paragraph data
    paragraphs = entry_requirements.find_all('p')
    paragraphs_text = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
    paragraphs_text = "\n".join([re.sub(r'\s+', ' ', p).strip() for p in paragraphs_text])

    return entry_req_str + paragraphs_text


def process_table(table):
    table_data = get_table_data(table)
    df = pd.DataFrame(table_data[1:], columns=table_data[0])
    df.ffill(inplace=True)
    df.fillna("", inplace=True)
    entry_req_str = df_to_str(df, delim=',')
    return entry_req_str


def get_courses_data() -> dict[str, str]:
    fp = f"{storage_path}/courses.json"
    if os.path.exists(fp):
        return json.load(open(fp, 'r'))

    response = requests.get(courses_url)
    
    soup = BeautifulSoup(response.content, 'html.parser')
    course_links = list({l.get('href') for l in soup.find_all('a')\
                    if l.get('href') and l.get('href').startswith(course_url_prefix)})


    courses_data = dict()
    for course_link in tqdm(course_links, desc="Extracting courses data"):
        course_soup = get_soup(course_link)
        name = course_soup.find('h1').text.strip()
        courses_data[name] = extract_entry_requirements(course_soup)
    
    with open(fp, 'w') as f:
        json.dump(courses_data, f, indent=4)

    return courses_data


def get_country_data() -> dict[str, str]:
    fp = f"{storage_path}/countries.json"
    if os.path.exists(fp):
        return json.load(open(fp, 'r'))

    entry_req_soup = get_soup(country_entry_req_url)
    accodion_group = entry_req_soup.find('div', class_='accordion-group')
    continent_countries = dict()

    for div in accodion_group.find_all('div'):
        if div.find('table'):
            if div.find('h3'):
                countries = div.find_all('h3')
                tables = div.find_all('table')
                for country, table in zip(countries, tables):
                    continent_countries[country.text.strip()] = process_table(table)
            else:
                non_specific_tables = div.find('table')
                continent_countries["Non-specific"] = process_table(non_specific_tables)

    with open(fp, 'w') as f:
        json.dump(continent_countries, f, indent=4)

    return continent_countries



### Each University handler should have --
# 1. university_name (str)
# 2. university_url (str)
# 3. A class that inherits from UniversityDataHandler
# 4. A function that gets courses data in a dict: key = course_name, value = entry_requirements
# 5. A function that gets country data in a dict: key = country_name, value = entry_requirements


university_name = 'Northumbria'
university_url = "https://london.northumbria.ac.uk/"
storage_path = f"{university_data_dir}/{university_name.lower()}"
os.makedirs(f"{storage_path}", exist_ok=True)


class NorthUmbriaWebDataHandler(UniversityDataHandler):
    def __init__(self):
        self.courses_data = get_courses_data()
        self.country_data = get_country_data()
        super().__init__(
            uni_name=university_name,
            uni_url=university_url,
            courses_data=self.courses_data, 
            countries_data=self.country_data
        )