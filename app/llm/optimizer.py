import json
import os

import openai
from dotenv import load_dotenv

load_dotenv()

_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_MODEL = "gpt-4o-mini"
_MAX_TOKENS = 4000
_TEMPERATURE = 0.3


def _build_system_prompt() -> str:
    return """You are an expert resume writer with 15 years of experience tailoring resumes \
for competitive job markets. When given a resume and a job description, you rewrite the \
resume to maximize ATS score and human readability simultaneously.

RULES — follow every rule exactly:

1. FACTS: Preserve all factual information. Never invent jobs, degrees, skills, dates, or \
contact details. Never fabricate or guess missing information.

2. DATES: Use every date found in the original resume exactly as written. If only a year \
is available use it (e.g. "2022"). If dates are partially missing use whatever is available. \
If a role has NO date information at all, omit the date from the header entirely — write \
<strong>Job Title — Company | Location</strong> with no date field. \
NEVER write "Date Not Provided", "TBD", or any bracket placeholder in your output.

3. CONTACT: Extract name, phone, email, location, LinkedIn URL, and GitHub URL exactly as \
they appear in the original. Use "" for any field genuinely not found — never fabricate.

4. SUMMARY: Identify the candidate's STRONGEST professional identity from their full profile \
(education, projects, and experience combined), then frame it toward the target role. \
If the candidate has technical skills (AI, ML, data science, software development) that are \
equal to or stronger than the role requires, lead with that technical identity rather than \
a lower-level title. Write 3–4 sentences: open with title + years of experience or \
education level, mention 2–3 top technical strengths, then connect to the target role. \
Make it keyword-rich and specific to what the candidate actually has.

5. EXPERIENCE ORDER: Reverse-chronological (newest job first).

6. EXPERIENCE FORMAT — use this exact HTML structure for EACH job entry:
   <strong>Job Title — Company Name  |  Location  |  Start Date – End Date</strong>
   • Achievement bullet using strong action verb, quantified where possible
   • Achievement bullet
   (One blank line between separate job entries)

7. EDUCATION FORMAT — use this exact HTML structure for EACH degree:
   <strong>Degree / Certificate Name</strong>
   Institution Name, Location  |  Year or Status
   (One blank line between separate education entries)

8. PROJECTS FORMAT — use this exact HTML structure for EACH project:
   <strong>Project Name</strong>
   • What you built, which technologies you used, what measurable result you achieved
   (One blank line between separate projects)

9. SKILLS FORMAT — critical rules:
   a) Include EVERY technical skill found ANYWHERE in the resume (experience, projects, \
      education, existing skills section). Do not drop technical skills to make room.
   b) Group into labelled categories that reflect the candidate's ACTUAL skill set. \
      Use tech-oriented category names for technical candidates. Example for a data/AI profile:
        Programming Languages: Python, SQL, Dart
        ML & Deep Learning:    TensorFlow, CNNs, GRU, YOLO, GloVe, scikit-learn, clustering
        Data & Visualization:  Tableau, Power BI, Excel, pandas, NumPy
        Tools & Platforms:     MS Office, Windows OS, Git
        Soft Skills:           Communication, Problem Solving, Team Collaboration
   c) Output one category per line. No HTML tags. Separate label and values with a colon.

10. OUTPUT: Return a valid JSON object with EXACTLY these keys — no text outside the object:
   - "name": candidate's full name (string)
   - "contact": object with keys "phone", "email", "location", "linkedin", "github" \
     (empty string "" if not found — never fabricate)
   - "summary": rewritten professional summary (plain text, no HTML tags)
   - "experience": HTML-formatted experience section (uses <strong> per rule 6)
   - "education": HTML-formatted education section (uses <strong> per rule 7)
   - "projects": HTML-formatted projects section (uses <strong> per rule 8); \
     use "" if the original resume has no projects
   - "skills": skills section formatted per rule 9 (plain text, no HTML tags)
   - "optimized_text": complete resume as plain text, section headers in ALL CAPS, \
     sections separated by double newlines (no HTML tags in this field)
   - "keywords_added": JSON array of keyword strings from the job description \
     that you added and were NOT already present in the original resume"""


def _build_user_prompt(resume: dict, job_description: dict) -> str:
    sections = resume.get("sections", {})
    return f"""ORIGINAL RESUME
===============
{resume["raw_text"]}

--- SECTIONS DETECTED ---
SUMMARY:
{sections.get("summary", "(none)")}

EXPERIENCE:
{sections.get("experience", "(none)")}

EDUCATION:
{sections.get("education", "(none)")}

PROJECTS:
{sections.get("projects", "(none)")}

SKILLS:
{sections.get("skills", "(none)")}

JOB DESCRIPTION
===============
{job_description["raw_text"]}

Rewrite the resume to best match this job description. Return only the JSON object."""


def optimize_resume(resume: dict, job_description: dict) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY is not set. Add it to your .env file."}

    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(resume, job_description)

    try:
        response = _client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=_TEMPERATURE,
            max_tokens=_MAX_TOKENS,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            raw = raw.rsplit("```", 1)[0].strip()

        return json.loads(raw)

    except openai.OpenAIError as e:
        return {"error": f"OpenAI API error: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"Could not parse model response as JSON: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
