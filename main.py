import PyPDF2
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

GEMINI_API_KEY = "YOUR_API_KEY"
client = genai.Client(api_key=GEMINI_API_KEY)



def extract_text_from_pdf(file_storage):
    extracted_text = ""
    pdf_reader = PyPDF2.PdfReader(file_storage)
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            extracted_text += page_text
        return extracted_text

def parse_resume(resume_text):
    prompt = f"You are a resume parser. Extract Skills, Experience summary, Education, and Tools & technologies from this resume in bullet points. Do not use hashtags: {resume_text}"
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text

def parse_job_description(jd_text):
    prompt = f"Extract Required skills, Responsibilities, and Preferred qualifications from this Job Description in bullet points. Do not use hashtags: {jd_text}"
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text

def ats_match(parsed_resume, parsed_jd):
    prompt = f"""
    You are an Applicant Tracking System. Compare the resume and job description.
    
    Resume Data: {parsed_resume}
    Job Data: {parsed_jd}
    
    Provide:
    1. Match percentage (0-100)
    2. Matching skills
    3. Missing skills
    4. Strengths
    5. Improvement suggestions
    
    IMPORTANT: Format clearly. Do not use hashtags (#) or bold markdown stars (**).
    """
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text

# ==============================
# ROUTES
# ==============================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files or 'job_description' not in request.form:
        return jsonify({"error": "Missing file or description"})
    
    file = request.files['resume']
    jd_raw = request.form.get('job_description')

    # Step 1: Extract Text
    resume_raw = extract_text_from_pdf(file)
    if not resume_raw:
        return jsonify({"error": "PDF text extraction failed"})

    # Step 2: Parse Entities (Categorization)
    p_resume = parse_resume(resume_raw)
    p_jd = parse_job_description(jd_raw)

    # Step 3: Match & Score (The final result)
    final_analysis = ats_match(p_resume, p_jd)

    return jsonify({
        "analysis": final_analysis
    })

if __name__ == '__main__':

    app.run(debug=True, port=8080)
