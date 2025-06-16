import fitz
import re
import json
import unicodedata
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

import re
import spacy
from typing import Dict

# Load models
nlp = spacy.load("en_core_web_sm")

# --- Branches ---
BRANCH_KEYWORDS = [
    "computer science", "information technology", "data science", "artificial intelligence",
    "machine learning", "cybersecurity", "software engineering", "electronics and communication",
    "electronics engineering", "electrical engineering", "electrical and electronics", "instrumentation engineering",
    "robotics", "control systems", "engineering physics", "applied physics", "applied mathematics",
    "mathematics and computing", "mathematical sciences", "quantum computing", "bioinformatics",
    "computational biology", "mechanical engineering", "civil engineering", "chemical engineering",
    "metallurgical engineering", "aerospace engineering", "aeronautical engineering", "marine engineering",
    "mining engineering", "automobile engineering", "industrial engineering", "production engineering",
    "petroleum engineering", "textile engineering", "ceramic engineering", "nuclear engineering",
    "agricultural engineering", "biotechnology", "biochemical engineering", "ocean engineering",
    "materials science", "engineering design", "engineering management", "business analytics",
    "operations research", "economics", "cognitive science", "design", "humanities",
    "environmental engineering", "energy science", "rural technology", "management", "mba", "bba", "statistics", "geoinformatics"
]

# --- Tech Keywords ---
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

# --- Non-Tech Keywords ---
NON_TECH_KEYWORDS = [
    "strategy", "management consulting", "business consulting", "financial modeling", "valuation", "investment banking",
    "private equity", "venture capital", "equity research", "derivatives", "hedging", "mergers and acquisitions", "m&a",
    "capital markets", "asset management", "wealth management", "risk management", "audit", "due diligence", "compliance",
    "product management", "business development", "sales strategy", "marketing", "growth", "user research", "go-to-market",
    "product analytics", "roadmap", "market research", "competitive analysis", "customer success", "crm", "kpis", "roi", "unit economics",
    "excel", "powerpoint", "google sheets", "tableau", "power bi", "salesforce", "hubspot", "lookerstudio", "figma", "miro",
    "communication", "problem solving", "stakeholder management", "leadership", "collaboration", "presentation skills", "design thinking"
]

ALL_KEYWORDS = TECH_KEYWORDS + NON_TECH_KEYWORDS

DOMAIN_KEYWORDS = {
    "Finance": ["finance", "bank", "investment", "trading", "capital market", "equity", "hedge fund", "fintech"],
    "Healthcare": ["health", "hospital", "clinical", "biotech", "medtech", "pharmaceutical", "medical"],
    "Technology": ["software", "developer", "tech", "cloud", "ai", "ml", "it services", "cybersecurity"],
    "Consulting": ["consulting", "advisory", "client delivery", "strategy consulting", "business analysis"],
    "Product": ["product manager", "product management", "roadmap", "feature", "user research"],
    "Education": ["edtech", "teaching", "curriculum", "learning", "academic", "school", "university"],
    "Legal": ["law", "legal", "compliance", "regulatory"],
    "Retail": ["ecommerce", "retail", "consumer", "supply chain", "inventory", "logistics"],
    "Energy": ["renewable", "solar", "wind", "energy", "oil", "gas", "power", "climate"],
    "Government": ["public sector", "policy", "governance", "ministry", "bureaucracy", "civil services"],
    "Telecom": ["telecom", "network", "5g", "broadband"],
    "Design": ["ui", "ux", "figma", "adobe", "interface", "design thinking"],
    "Media": ["media", "advertising", "content", "branding", "digital marketing", "journalism"],
    "Manufacturing": ["factory", "industrial", "mechanical", "automation", "production", "assembly line"]
}

def detect_domain(text: str) -> str:
    text_lower = text.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            return domain
    return "General"  # fallback

import re
from typing import Dict

import fitz
import re
import json
import unicodedata

def clean_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.replace('\u2019', "'")
    text = text.replace('\u2013', '-')
    text = re.sub(r"[\u200b\u200e]+", "", text)
    return text.strip()

def ensure_list(text_or_list):
    if isinstance(text_or_list, list):
        return [clean_text(x) for x in text_or_list]
    return [clean_text(x) for x in re.split(r"\.\s+", text_or_list) if x.strip()]

def split_bullets(text):
    items = re.split(r"(?:^|\n|\.)(?=\s*[•●\u25cf\u2022\-–])", text)
    lines = []
    for item in items:
        line = item.strip()
        if not line:
            continue
        line = re.sub(r"^[•●\u25cf\u2022\-–\s]+", "", line)
        if line:
            lines.append(line)
    return lines

def extract_jd_sections_from_text(text: str) -> dict:
    section_keywords = {
        "job_role": ["about the role", "introduction", "overview", "position overview"],
        "responsibilities": ["responsibilities", "what you'll do", "key responsibilities"],
        "required_skills": ["required skills", "technical skills", "required capabilities"],
        "preferred_skills": ["preferred skills", "preferred qualifications", "preferred capabilities", "good to have"],
        "eligibility": ["eligibility", "qualification criteria", "who can apply"],
        "locations": ["locations", "location", "you may join in"]
    }

    lines = text.split("\n")
    sections = {key: [] for key in section_keywords}
    current_section = None

    def is_section_header(line):
        normalized = line.strip().lower()
        normalized = re.sub(r"[^a-z\s]", "", normalized)
        for key, headers in section_keywords.items():
            for h in headers:
                if h in normalized:
                    return key
        return None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        detected = is_section_header(line)
        if detected:
            current_section = detected
            continue
        if current_section:
            sections[current_section].append(line)

    return {k: " ".join(v).strip() for k, v in sections.items() if v}

def clean_and_structure_jd_sections(raw_sections: dict) -> dict:
    structured = {}

    for key, value in raw_sections.items():
        if key in {"responsibilities", "required_skills", "preferred_skills"}:
            structured[key] = split_bullets(value)

            # Fallback if too few bullets (bad formatting)
            if len(structured[key]) <= 1:
                structured[key] = re.split(r"•|\n|\.\s+", value)
                structured[key] = [s.strip() for s in structured[key] if len(s.strip()) > 5]

        elif key == "locations":
            loc_match = re.findall(r"\b(Remote|On-site|Hybrid)\b", value, flags=re.IGNORECASE)
            structured["locations"] = ", ".join(loc_match) if loc_match else "Remote"

        else:
            structured[key] = value.strip()

    return structured


def final_polish(jd_data: dict) -> dict:
    polished = {}
    for key, value in jd_data.items():
        if key in {"responsibilities", "required_skills", "preferred_skills", "values"}:
            polished[key] = ensure_list(value)
        elif key == "locations":
            loc_match = re.findall(r"\b(Remote|On-site|Hybrid)\b", value, flags=re.IGNORECASE)
            polished["locations"] = ", ".join(loc_match) if loc_match else "Remote"
        elif isinstance(value, str):
            polished[key] = clean_text(value)
        else:
            polished[key] = value
    return polished

def extract_metadata(raw_text: str) -> dict:
    metadata = {}
    job_title_match = re.search(r"Job Title:\s*(.*)", raw_text)
    job_type_match = re.search(r"Job Type:\s*(.*)", raw_text)
    experience_match = re.search(r"Experience Level:\s*(.*)", raw_text)

    if job_title_match:
        metadata["job_title"] = clean_text(job_title_match.group(1))
    if job_type_match:
        metadata["job_type"] = clean_text(job_type_match.group(1))
    if experience_match:
        metadata["experience_level"] = clean_text(experience_match.group(1))

    return metadata

def parse_jd_pdf(file_path: str) -> dict:
    doc = fitz.open(file_path)
    text = "\n".join([page.get_text() for page in doc])
    doc.close()

    raw_sections = extract_jd_sections_from_text(text)
    structured = clean_and_structure_jd_sections(raw_sections)
    final_output = final_polish(structured)

    metadata = extract_metadata(text)
    final_output.update(metadata)
    return final_output


def extract_technologies_from_text(jd_text: str, model, threshold=0.8, top_k=5):
    jd_words = jd_text.lower().split()
    matched_skills = set()

    # Go through each vocab skill and check if it appears approximately in JD
    for vocab_skill in model.wv.index_to_key:
        for word in jd_words:
            if word in vocab_skill or vocab_skill in word:
                try:
                    sim = model.wv.similarity(word, vocab_skill)
                    if sim >= threshold:
                        matched_skills.add(vocab_skill)
                        break
                except KeyError:
                    continue

    return sorted(matched_skills)

# --- Extract Structured Fields ---
def detect_domain(text: str) -> str:
    text_lower = text.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            return domain
    return "General"  # fallback

import re
from typing import Dict

def extract_structured_values(sections: Dict, model) -> Dict:
    # Ensure all section values are strings
    clean_sections = {k: str(v) for k, v in sections.items()}
    full_text = " ".join(clean_sections.values()).lower()


    structured = {
        "branches": [],
        "technologies": [],
        "non_tech_skills": [],
        "domain": "",
        "min_cgpa": None
    }

    # Branches (exact match from pre-defined list)
    for branch in BRANCH_KEYWORDS:
        if re.search(rf"\b{re.escape(branch)}\b", full_text, re.IGNORECASE):
            structured["branches"].append(branch.title())

    # Technologies (semantic from trained model)
    structured["technologies"] = extract_technologies_from_text(full_text, model)

    # Non-tech keywords (static match from list)
    for kw in NON_TECH_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", full_text, re.IGNORECASE):
            structured["non_tech_skills"].append(kw)

    # CGPA (regex-based)
    cgpa_match = re.search(r"(?:CGPA|CPI|GPA)[^0-9]{0,5}(\d{1,2}(?:\.\d{1,2})?)", full_text, re.IGNORECASE)
    if cgpa_match:
        structured["min_cgpa"] = float(cgpa_match.group(1))

    # Domain detection
    structured["domain"] = detect_domain(full_text)

    return structured

