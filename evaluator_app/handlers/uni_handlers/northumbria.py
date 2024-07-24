import json
import os
from tqdm.auto import tqdm
import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
from handlers.base import UniversityDataHandler
from config import university_data_dir


def df_to_str(df, delim='|'):
    final_str = ""
    for _, r in df.iterrows():
        values = [f"{k}: {v}".format(k, v) for k, v in r.to_dict().items()]
        final_str += f" {delim} ".join(values) + "\n"
    
    return final_str


def get_table_data(table):
    rows = table.find_all('tr')
    header = [th.text.strip() for th in rows[0].find_all(['td', 'th'])]

    if len(header) <= 2:
        header = ['Level', 'Requirement']

    elif header[0] == '':
        header[0] = 'Level'

    ### Create dataframe of shape (len(rows), len(header))

    data = pd.DataFrame(columns=header, index=range(len(rows)-1))
    
    for row_id, row in enumerate(rows[1:]):
        cells = row.find_all('td')
        
        col_id = 0
        for cell in cells:
            rowspan = int(cell.get('rowspan', 1))
            try:
                while not isinstance(data.iat[row_id, col_id], float):
                        col_id += 1
            except Exception as e:
                print(table, row_id, col_id)
                raise e
            for i in range(rowspan):
                data.iat[row_id + i, col_id] = cell.text.strip()
    return data


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
        df = get_table_data(table)
        entry_req_str = df_to_str(df)
    # Extract paragraph data
    paragraphs = entry_requirements.find_all('p')
    paragraphs_text = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
    paragraphs_text = "\n".join([re.sub(r'\s+', ' ', p).strip() for p in paragraphs_text])

    return entry_req_str + paragraphs_text


def process_table(table):
    df = get_table_data(table)
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
courses_url = "https://london.northumbria.ac.uk/courses/"
course_url_prefix = "https://london.northumbria.ac.uk/course/"
country_entry_req_url = "https://london.northumbria.ac.uk/international-students/entry-requirements/"
storage_path = f"{university_data_dir}/{university_name.lower()}"
os.makedirs(f"{storage_path}", exist_ok=True)


class NorthUmbriaWebDataHandler(UniversityDataHandler):
    def __init__(self):
        super().__init__(
            uni_name=university_name,
            uni_url=university_url,
        )

    def set_courses(self):
        self.courses_data = get_courses_data()
    
    def set_countries(self):
        self.countries_data = get_country_data()

    def get_countries(self):
        if not self.countries_data:
            self.set_countries()
        
        return self.countries_data
    
    def get_courses(self):
        if not self.courses_data:
            self.set_courses()
        
        return self.courses_data