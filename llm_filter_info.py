class Prompts():
    prompts = {}
    def __init__(self):

        self.prompts = {
            "Student_Cert_summary_post_OCR":"""
                below is a snippet of text generate by an ocr model from parsing images in pdfs. 
                These are images of student cetificates and qualifications while applying to a university for masters or undergrad programs. 
                Summarize the qualifications for each of these while clearly calling out any ambiguous info and info that isnt clearly mentioned. Dont make assumptions. here is the text -    
            """,
            "Student_qualifies_marks":"""

            Given the below student qualification summary and the requirements of a university for their programs, evaluate if the student meets all the criteria. Output format - 
            1. Point of failure: Where the student doesnt meet criteria.
            2. Point of ambiguity: Ambiguous points where either data is absent or the criteria isnt clear. Need human intervention.
            3. Points of communication: Need to get back to the student since data needed isnt provided. here the data isnt ambiguous but isnt present at all.
            """,

        }

