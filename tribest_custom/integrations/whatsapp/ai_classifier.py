import re

VALID_TICKET_TYPES = [
    "Follow up",
    "Complaint",
    "Applicant Inquiry",
    "Candidate Inquiry",
    "Staff Inquiry",
    "Internal Operation/HR",
    "Technical Support",
    "Client Management"
]


KEYWORD_MAP = {
    "Technical Support": [
        "error", "bug", "system", "login", "cannot access",
        "not working", "issue", "problem", "crash"
    ],
    "Complaint": [
        "complain", "bad service", "not happy", "angry",
        "poor service", "unacceptable"
    ],
    "Applicant Inquiry": [
        "apply", "application", "job", "resume",
        "cv", "career"
    ],
    "Candidate Inquiry": [
        "candidate", "interview", "shortlisted",
        "assessment"
    ],
    "Staff Inquiry": [
        "staff", "employee", "leave",
        "salary", "attendance"
    ],
    "Internal Operation/HR": [
        "hr", "policy", "internal process",
        "benefits"
    ],
    "Client Management": [
        "invoice", "payment", "client",
        "contract", "account"
    ]
}


def classify_ticket_type(message: str) -> str:
    msg = message.lower()
    scores = {category: 0 for category in VALID_TICKET_TYPES}

    for category, keywords in KEYWORD_MAP.items():
        for word in keywords:
            if re.search(rf"\b{re.escape(word)}\b", msg):
                scores[category] += 1

    # Get highest score
    best_category = max(scores, key=scores.get)

    if scores[best_category] == 0:
        return "Follow up"

    return best_category