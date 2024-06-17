

class UniversityDataHandler:
    def __init__(self, uni_name, uni_url, courses_data, countries_data):
        self.name = uni_name
        self.website = uni_url
        self.courses_data = courses_data
        self.countries_data = countries_data

    @property
    def courses(self):
        return self.courses_data

    @property
    def countries(self):
        return self.countries_data