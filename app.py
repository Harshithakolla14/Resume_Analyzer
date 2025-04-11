import gradio as gr
import PyPDF2
from docx import Document
import os
import json
import re
import google.generativeai as genai

# ✅ Gemini API Key (Replace with your own for production)
GENAI_API_KEY = "AIzaSyC-70KH4dxmweIdyztNWt8dOf3jA3yjSDs"  

genai.configure(api_key=GENAI_API_KEY)

# 📄 Extract text from uploaded resume
def extract_text(file):
    ext = os.path.splitext(file.name)[-1].lower()
    text = ""
    if ext == ".pdf":
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    elif ext == ".docx":
        doc = Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])
    return text.strip()

# 📊 Clean LLM response
def parse_response(text):
    try:
        clean = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE)
        return json.loads(clean)
    except:
        return {"alignment_score": "N/A", "strengths": [], "weaknesses": [], "recommendations": [text]}

# 🤖 Call Gemini LLM for analysis
def analyze_resume(resume_file, job_desc_input, job_desc_file):
    if not resume_file or (not job_desc_input and not job_desc_file):
        return "Please upload both a resume and job description.", None, None, None

    resume_text = extract_text(resume_file)
    job_text = job_desc_input.strip()
    
    if job_desc_file:
        job_text = extract_text(job_desc_file)

    prompt = (
        f"Analyze the following resume:\n{resume_text}\n\n"
        f"In the context of this job description:\n{job_text}\n\n"
        "Instructions:\n"
        "- Evaluate resume alignment with the job description.\n"
        "- List strengths, weaknesses, and give actionable suggestions to improve it.\n"
        "Format the response in JSON like this:\n"
        "{"
        "  'alignment_score': 'X/10',"
        "  'strengths': [...],"
        "  'weaknesses': [...],"
        "  'recommendations': [...]"
        "}"
    )

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    result = parse_response(response.text)

    return (
        f"📈 Alignment Score: {result.get('alignment_score', 'N/A')}",
        "\n".join(result.get("strengths", [])),
        "\n".join(result.get("weaknesses", [])),
        "\n".join(result.get("recommendations", [])),
    )

# 🌐 Gradio UI
demo = gr.Interface(
    fn=analyze_resume,
    inputs=[
        gr.File(label="Upload Resume (.pdf or .docx)", file_types=[".pdf", ".docx"]),
        gr.Textbox(label="Paste Job Description (Optional if uploading file)"),
        gr.File(label="Upload Job Description (.pdf or .docx)", file_types=[".pdf", ".docx"]),
    ],
    outputs=[
        gr.Textbox(label="🔍 Alignment Score"),
        gr.Textbox(label="✅ Strengths"),
        gr.Textbox(label="⚠️ Weaknesses"),
        gr.Textbox(label="💡 Recommendations"),
    ],
    title="📄 AI-Powered Resume Analyzer",
    description="Upload your resume and a job description to receive tailored feedback powered by Gemini AI.",
)

if __name__ == "__main__":
    demo.launch()
