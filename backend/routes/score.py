import re
from .train_model import model

BRANCH_EQUIVALENTS = {
    "cs": ["computer science", "cse", "computer science and engineering", "cs", "it", "information technology"],
    "dsai": ["artificial intelligence", "ai", "dsai", "artificial intelligence and data science", "data science and artificial intelligence", "data science"],
    "ece": ["electronics", "electronics and communication engineering", "ece"],
    "ee": ["electrical", "ee", "electrical engineering"],
    "me": ["mechanical", "me", "mech", "mechanical engineering"],
    "civil": ["civil", "civil engineering"],
    "math": ["mathematics", "math", "mathematics and computing"],
    "chemical": ["chemical engineering", "chemical", "che", "chem"],
    "ep": ["engineering physics", "ep"],
    "bsbe": ["biosciences and bioengineering", "bsbe", "bioengineering", "biotechnology"]
}

def normalize_branch(branch_name: str) -> str:
    branch_name = branch_name.strip().lower()
    for canonical, synonyms in BRANCH_EQUIVALENTS.items():
        if branch_name in synonyms:
            return canonical
    return branch_name

def check_eligibility(jd_structured: dict, parsed_cv: dict) -> (bool, str):
    # --------- Branch Check ---------
    jd_branches = set(normalize_branch(b) for b in jd_structured.get("branches", []))
    cv_branches = set()

    # Check top-level branch
    if "branch" in parsed_cv:
        cv_branches.add(normalize_branch(parsed_cv["branch"]))

    # Also check from degree lines in education
    for edu in parsed_cv.get("education", []):
        degree_line = edu.get("degree", "").lower()
        for canonical, synonyms in BRANCH_EQUIVALENTS.items():
            if any(syn in degree_line for syn in synonyms):
                cv_branches.add(canonical)

    # Compare normalized branch sets
    if jd_branches and not cv_branches.intersection(jd_branches):
        return False, "Branch not allowed"

    # --------- CGPA Check ---------
    min_cgpa = jd_structured.get("min_cgpa")
    if min_cgpa is not None:
        for edu in parsed_cv.get("education", []):
            score_str = edu.get("score", "")
            match = re.search(r"(\d{1,2}(?:\.\d{1,2})?)", score_str)
            if match:
                try:
                    cgpa = float(match.group(1))
                    if cgpa >= min_cgpa:
                        return True, "Eligible"
                except ValueError:
                    continue
        return False, "CGPA below required minimum"

    return True, "Eligible"

from sentence_transformers import SentenceTransformer, util
from rapidfuzz import fuzz

def course_match_score(
    jd_structured: dict,
    jd_sections: dict,
    cv_courses: dict,
    sbert_model,
    top_k: int = 5
):
    # Safely flatten any list fields to strings
    def to_text(val):
        return " ".join(val) if isinstance(val, list) else str(val)

    jd_text_parts = [
        " ".join(jd_structured.get("technologies", [])),
        to_text(jd_sections.get("job_role", "")),
        to_text(jd_sections.get("required_skills", "")),
        to_text(jd_sections.get("preferred_skills", ""))
    ]

    jd_text = " ".join([part for part in jd_text_parts if part.strip()])


    if not jd_text or not cv_courses:
        return {"score": 0.0, "top_matches": []}

    # Flatten CV course titles
    cv_course_list = []
    for group in cv_courses.values():
        cv_course_list.extend(group)

    if not cv_course_list:
        return {"score": 0.0, "top_matches": []}

    # SBERT scoring
    jd_emb = sbert_model.encode(jd_text, convert_to_tensor=True)
    course_embs = sbert_model.encode(cv_course_list, convert_to_tensor=True)
    sbert_scores = util.cos_sim(jd_emb, course_embs)[0].cpu().numpy()

    sbert_matches = [
        {"course": course, "score": float(score), "match_type": "sbert"}
        for course, score in zip(cv_course_list, sbert_scores)
    ]

    # Fuzzy scoring
    fuzzy_matches = [
        {
            "course": course,
            "score": fuzz.partial_ratio(course.lower(), jd_text.lower()) / 100,
            "match_type": "fuzzy"
        }
        for course in cv_course_list
    ]

    # Combine and deduplicate by course name (keep max score per course)
    combined = {}
    for match in sbert_matches + fuzzy_matches:
        course = match["course"]
        if course not in combined or match["score"] > combined[course]["score"]:
            combined[course] = match

    # Get top-k matches
    top_matches = sorted(combined.values(), key=lambda x: x["score"], reverse=True)[:top_k]
    avg_score = round(sum(m["score"] for m in top_matches) / len(top_matches), 3) if top_matches else 0.0

    return {
        "score": avg_score,
        "top_matches": [
            {"course": m["course"], "score": round(m["score"], 3), "match_type": m["match_type"]}
            for m in top_matches
        ]
    }


import numpy as np
from numpy.linalg import norm


def get_avg_vector(skills, model): # vec_model
    vectors = [model.wv[s] for s in skills if s in model.wv]
    return np.mean(vectors, axis=0) if vectors else np.zeros(model.vector_size)

def cosine_similarity(vec1, vec2):
    if norm(vec1) == 0 or norm(vec2) == 0:
        return 0.0
    return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

def score_cv_against_jd(cv_skills, required_techs, preferred_techs, model, alpha=0.7):
    cv_vec = get_avg_vector(cv_skills, model)
    required_vec = get_avg_vector(required_techs, model)
    preferred_vec = get_avg_vector(preferred_techs, model)

    required_score = cosine_similarity(cv_vec, required_vec)
    preferred_score = cosine_similarity(cv_vec, preferred_vec)

    final_score = alpha * required_score + (1 - alpha) * preferred_score
    return {
    "required_score": float(round(required_score, 3)),
    "preferred_score": float(round(preferred_score, 3)),
    "final_score": float(round(final_score, 3))
    }

import re
from sentence_transformers.util import cos_sim

def clean_text(text):
    return re.sub(r"\s+", " ", text.strip().lower())

def semantic_paragraph_match(jd_text: str, cv_texts: list, model, top_k: int = 3) -> dict:
    jd_text = clean_text(jd_text)
    cv_texts = [clean_text(txt) for txt in cv_texts if isinstance(txt, str) and txt.strip()]

    if not jd_text or not cv_texts:
        return {"score": 0.0, "top_matches": []}

    jd_emb = model.encode(jd_text, convert_to_tensor=True)
    cv_embs = model.encode(cv_texts, convert_to_tensor=True)

    sims = cos_sim(jd_emb, cv_embs)[0].cpu().tolist()
    top_matches = sorted(zip(cv_texts, sims), key=lambda x: x[1], reverse=True)[:min(top_k, len(sims))]
    avg_score = round(sum(score for _, score in top_matches) / len(top_matches), 3)

    return {
        "score": avg_score,
        "top_matches": [{"cv_text": txt[:120], "score": round(score, 3)} for txt, score in top_matches]
    }

def evaluate_subjective_fit(jd_sections: dict, parsed_cv: dict, model) -> dict:
    projects = [p.get("summary", "") for p in parsed_cv.get("projects", [])]
    extracurriculars = parsed_cv.get("extracurriculars", [])
    positions = parsed_cv.get("positions", [])
    achievements = parsed_cv.get("achievements", [])

    return {
        "job_role_fit": semantic_paragraph_match(jd_sections.get("job_role", ""), projects, model),
        "responsibility_alignment": semantic_paragraph_match(" ".join(jd_sections.get("responsibilities", [])), projects + positions + extracurriculars, model),
        "values_match": semantic_paragraph_match(" ".join(jd_sections.get("values", [])), achievements + extracurriculars + positions, model)
    }

def flatten_cv_skills(cv_skills_dict):
    return [skill.lower() for sublist in cv_skills_dict.values() for skill in sublist if isinstance(skill, str)]


def evaluate_cv(jd_structured, jd_sections, parsed_resume, skill2vec_model, sbert_model, skill_weight=0.7):
    result = {}

    # Step 1: Eligibility Check
    is_eligible, reason = check_eligibility(jd_structured, parsed_resume)
    result["eligible"] = is_eligible
    result["eligibility_reason"] = reason

    if not is_eligible:
        result["final_score"] = 0.0
        result["skill_score"] = {}
        result["semantic_score"] = 0.0
        result["semantic_components"] = {}
        return result

    course_score = course_match_score(jd_structured, jd_sections, parsed_resume["courses"],sbert_model)

    # Step 2: Skill Score
    skill_category_score_result = score_cv_against_jd(
        cv_skills=parsed_resume.get("skills", []),
        required_techs=jd_structured.get("technologies", []),
        preferred_techs=jd_sections.get("required_skills", []),
        model=skill2vec_model
    )
    flatten_techstacks = flatten_cv_skills(parsed_resume.get("skills", []))

    skill_score_result = score_cv_against_jd(
        cv_skills=flatten_techstacks,
        required_techs=jd_structured.get("technologies", []),
        preferred_techs=jd_sections.get("required_skills", []),
        model=skill2vec_model
    )

    skill_avg_score = {
    "required_score": round(0.2 * skill_category_score_result["required_score"] + 0.8 * skill_score_result["required_score"], 3),
    "preferred_score": round(0.2 * skill_category_score_result["preferred_score"] + 0.8 * skill_score_result["preferred_score"], 3),
    "final_score": round(0.2 * skill_category_score_result["final_score"] + 0.8 * skill_score_result["final_score"], 3)
    }

    # Step 3: Semantic Score
    semantic_components = evaluate_subjective_fit(jd_sections, parsed_resume, sbert_model)
    semantic_score = round(
        0.4 * semantic_components["job_role_fit"]["score"] +
        0.3 * semantic_components["responsibility_alignment"]["score"] +
        0.3 * semantic_components["values_match"]["score"], 3
    )

    # Step 4: Final Score
    final_score = round(skill_weight * skill_score_result["final_score"] + (1 - skill_weight) * semantic_score, 3)

    # Attach all scores
    result["course_score"] = course_score["score"]
    result["skill_score"] = skill_avg_score
    result["semantic_score"] = semantic_score
    result["semantic_components"] = semantic_components
    result["final_score"] = final_score

    return result

