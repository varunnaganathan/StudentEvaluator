from abc import abstractmethod


class UniversityDataHandler:
    def __init__(self, uni_name, uni_url):
        self.name = uni_name
        self.website = uni_url

        self.courses_data = dict()
        self.countries_data = dict()

    @abstractmethod
    def set_courses(self, courses_data):
        pass
    
    @abstractmethod
    def set_countries(self, countries_data):
        pass

    @abstractmethod
    def get_courses_data(self):
        pass

    @abstractmethod
    def get_country_data(self):
        pass

    @property
    def courses(self):
        return self.courses_data

    @property
    def countries(self):
        return self.countries_data