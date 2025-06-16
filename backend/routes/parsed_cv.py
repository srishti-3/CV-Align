import fitz
import re
import spacy
import json

nlp = spacy.load("en_core_web_sm")

TECH_KEYWORDS = [
    "c", "c++", "java", "python", "go", "ruby", "rust", "kotlin", "typescript", "javascript", "php", "scala", "perl", "swift",
    "html", "css", "react", "angular", "vue", "next.js", "node.js", "express.js", "django", "flask", "spring boot",
    "flutter", "react native", "android", "ios", "swiftui",
    "mysql", "postgresql", "mongodb", "sqlite", "oracle", "cassandra", "redis", "firebase", "sql", "nosql",
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "jenkins", "terraform", "ansible", "linux", "nginx", "apache",
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn", "keras", "xgboost", "huggingface", "opencv", "llm", "langchain",
    "pandas", "numpy", "matplotlib", "seaborn", "big data", "hadoop", "spark", "hive", "airflow", "power bi", "tableau",
    "selenium", "junit", "pytest", "postman", "cypress",
    "git", "github", "bitbucket", "jira", "agile", "scrum", "ci/cd", "rest api", "graphql", "json", "yaml", "xml"
]

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join([page.get_text() for page in doc])

def extract_sections(text):
    sections = {}
    patterns = {
        "education": r"(?i)Education\n(.*?)(?=\n(?:Projects|Achievements|Technical Skills|Key courses taken|Extracurricular(?: Activities)?|Positions of Responsibility)\n|$)",
        "projects": r"(?i)Projects\n(.*?)(?=\n(?:Education|Achievements|Technical Skills|Key courses taken|Extracurricular(?: Activities)?|Positions of Responsibility)\n|$)",
        "achievements": r"(?i)Achievements\n(.*?)(?=\n(?:Projects|Education|Technical Skills|Key courses taken|Extracurricular(?: Activities)?|Positions of Responsibility)\n|$)",
        "skills": r"(?i)Technical Skills\n(.*?)(?=\n(?:Projects|Achievements|Education|Key courses taken|Extracurricular(?: Activities)?|Positions of Responsibility)\n|$)",
        "courses": r"(?i)Key courses taken\n(.*?)(?=\n(?:Projects|Achievements|Technical Skills|Education|Extracurricular(?: Activities)?|Positions of Responsibility)\n|$)",
        "extracurriculars": r"(?i)Extracurricular(?: Activities)?\n(.*?)(?=\n(?:Projects|Achievements|Technical Skills|Education|Key courses taken|Positions of Responsibility)\n|$)",
        "positions": r"(?i)Positions of Responsibility\n(.*?)(?=\n(?:Projects|Achievements|Technical Skills|Education|Key courses taken|Extracurricular(?: Activities)?)\n|$)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL)
        if match:
            sections[key] = match.group(1).strip()
    return sections

def extract_name(text):
    lines = text.split("\n")
    for line in lines[:5]:
        line = line.strip()
        if len(re.findall(r"\b[A-Za-z]{2,}\b", line)) >= 2 and "@" not in line:
            return line
    return ""

def extract_emails(text):
    return list(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)))

def extract_phone(text):
    matches = re.findall(r"(?:(?:\+91[\s\-]*)|(?:\b0))?[6-9]\d{9}\b", text)
    return list(set(matches))

def extract_skills(text):
    skills = {}
    lines = text.split("\n")
    for line in lines:
        line = line.strip("•*- ").strip()
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip().lower()
            items = [s.strip("* ").strip() for s in val.split(",") if s.strip()]
            if items:
                skills[key] = items
    return skills

def extract_education(text):
    degrees = []
    rows = text.strip().split("\n")
    i = 0
    while i < len(rows):
        row = rows[i].lower()
        if "b.tech" in row or "secondary" in row:
            entry = {
                "degree": rows[i],
                "institution": rows[i+1] if i+1 < len(rows) else "",
                "score": rows[i+2] if i+2 < len(rows) else "",
                "year": rows[i+3] if i+3 < len(rows) else ""
            }
            degrees.append(entry)
            i += 4
        else:
            i += 1
    return degrees

def extract_projects(text):
    projects = []
    blocks = re.split(r"• ", text)
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) >= 2:
            title = lines[0].strip()
            date = lines[1].strip()
            details = " ".join([l.strip("– ").strip() for l in lines[2:]])
            if title:
                projects.append({
                    "title": title,
                    "date": date,
                    "summary": details
                })
    return projects

def extract_achievements(text):
    cleaned = []
    lines = text.split("\n")
    for line in lines:
        line = line.strip("•–\t ").replace("–", "-").replace("\u2019", "'").replace("\u2013", "-").replace("\u2014", "-")
        if line:
            cleaned.append(line)
    return cleaned

def extract_courses(text):
    lines = text.split("\n")
    grouped = {}
    current = ""
    for line in lines:
        line = line.strip("•*- ").strip()
        if ":" in line:
            current, content = line.split(":", 1)
            current = current.strip().lower()
            grouped[current] = [c.strip() for c in content.split(",") if c.strip()]
        elif current:
            grouped[current] += [c.strip() for c in line.split(",") if c.strip()]
    return grouped

def extract_extracurriculars(text):
    lines = re.split(r"•|\n", text)
    return [line.strip("•–\t ").replace("–", "-") for line in lines if line.strip()]

def extract_positions(text):
    lines = re.split(r"•|\n", text)
    return [line.strip("•–\t ").replace("–", "-") for line in lines if line.strip()]

def extract_degree_and_cgpa(text, education_data):
    degree = ""
    cgpa = ""

    match_deg = re.search(r"B\.?Tech\.?\s*-\s*(.*)", text)
    if match_deg:
        degree = match_deg.group(1).strip()

    for edu in education_data:
        if "b.tech" in edu["degree"].lower() and "major" in edu["degree"].lower():
            match = re.search(r"\b(\d\.\d{1,2})\b", edu["score"])
            if match:
                cgpa = match.group(1)
                break

    return degree, cgpa

def extract_flat_skills(skills_dict: dict, keyword_list: list) -> list:
    """Flatten and match resume skills against TECH_KEYWORDS"""
    combined = " ".join(skill.lower() for skills in skills_dict.values() for skill in skills)
    matched = set()
    for kw in keyword_list:
        kw_pattern = re.escape(kw.lower())
        if re.search(r"[^\w\s]", kw):
            pattern = rf"(?<!\w){kw_pattern}(?!\w)"
        else:
            pattern = rf"\b{kw_pattern}\b"
        if re.search(pattern, combined):
            matched.add(kw.lower())
    return sorted(matched)

def parse_cv(pdf_path):
    raw_text = extract_text_from_pdf(pdf_path)
    sections = extract_sections(raw_text)
    education_data = extract_education(sections.get("education", ""))
    degree, cgpa = extract_degree_and_cgpa(raw_text, education_data)
    skills_dict = extract_skills(sections.get("skills", ""))

    structured = {
        "name": extract_name(raw_text),
        "emails": extract_emails(raw_text),
        "phones": extract_phone(raw_text),
        "branch": degree,
        "cgpa": cgpa,
        "education": education_data,
        "projects": extract_projects(sections.get("projects", "")),
        "achievements": extract_achievements(sections.get("achievements", "")),
        "skills": skills_dict,
        "extracted_skills": extract_flat_skills(skills_dict, TECH_KEYWORDS),
        "courses": extract_courses(sections.get("courses", "")),
        "extracurriculars": extract_extracurriculars(sections.get("extracurriculars", "")),
        "positions": extract_positions(sections.get("positions", ""))
    }
    return structured

