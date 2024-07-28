from django.db import models

# Create your models here.


class University(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class UniversityCourse(models.Model):
    id = models.AutoField(primary_key=True)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    requirements = models.TextField()

    def __str__(self):
        return f"{self.university} | {self.name}"


class UniversityCountry(models.Model):
    id = models.AutoField(primary_key=True)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    requirements = models.TextField()

    def __str__(self):
        return f"{self.university} | {self.name}"
    

class UniversityCourseXCountry(models.Model):
    id = models.AutoField(primary_key=True)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    course = models.ForeignKey(UniversityCourse, on_delete=models.CASCADE)
    country = models.ForeignKey(UniversityCountry, on_delete=models.CASCADE)
    requirements = models.TextField()

    def __str__(self):
        return f"{self.university} | {self.course} | {self.country}"


class Student(models.Model):
    student_id = models.BigIntegerField(primary_key=True)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    email = models.EmailField(max_length=200)
    country = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.student_id} | {self.first_name} {self.last_name} | {self.email}"


class StudentDocument(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    text = models.TextField()
    summary = models.TextField()
    file_name = models.CharField(max_length=200)

    def __str__(self):
        return self.file_name


class Application(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    course = models.ForeignKey(UniversityCourse, on_delete=models.CASCADE)
    country = models.ForeignKey(UniversityCountry, on_delete=models.CASCADE)
    student_qualifications = models.TextField()
    university_requirements = models.TextField()
    processed_qualifications = models.TextField()
    academic_data = models.TextField()
    work_experience_data = models.TextField()
    english_data = models.TextField()
    visa_data = models.TextField()
    exceptions_data = models.TextField()
    app_notes = models.TextField()
    decision_data = models.TextField()
    status = models.CharField(max_length=200, default='pending')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} | {self.university} | {self.course.name} | {self.country.name} | {self.status}"