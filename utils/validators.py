import re


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_PATTERN = re.compile(r"^[0-9+() .-]{7,24}$")
SERVICES = {
    "Web Application Security", "Network Security", "Cloud Security",
    "Mobile Security", "API Security", "Security Audit",
    "Penetration Testing", "SOC Monitoring", "Other",
}
CONTACT_METHODS = {"Email", "Phone", "WhatsApp", "Video Call"}
CONTACT_TIMES = {"Morning", "Afternoon", "Evening", "Any Time"}


def clean(value, limit=250):
    return " ".join((value or "").strip().split())[:limit]


def validate_enquiry(form) -> tuple[dict, dict]:
    data = {
        "full_name": clean(form.get("full_name"), 100),
        "company_name": clean(form.get("company_name"), 120),
        "email_address": clean(form.get("email_address"), 254).lower(),
        "phone_number": clean(form.get("phone_number"), 24),
        "country": clean(form.get("country"), 80),
        "service_interested": clean(form.get("service_interested"), 80),
        "subject": clean(form.get("subject"), 160),
        "message": (form.get("message") or "").strip()[:5000],
        "preferred_contact_method": clean(form.get("preferred_contact_method"), 30),
        "preferred_contact_time": clean(form.get("preferred_contact_time"), 30),
    }
    errors = {}
    required = {
        "full_name": "Full name", "email_address": "Email address",
        "phone_number": "Phone number", "country": "Country",
        "service_interested": "Service", "subject": "Subject",
        "message": "Message", "preferred_contact_method": "Contact method",
        "preferred_contact_time": "Contact time",
    }
    for key, label in required.items():
        if not data[key]:
            errors[key] = f"{label} is required."
    if data["email_address"] and not EMAIL_PATTERN.fullmatch(data["email_address"]):
        errors["email_address"] = "Enter a valid email address."
    if data["phone_number"] and not PHONE_PATTERN.fullmatch(data["phone_number"]):
        errors["phone_number"] = "Enter a valid phone number."
    if data["service_interested"] and data["service_interested"] not in SERVICES:
        errors["service_interested"] = "Choose a valid service."
    if data["preferred_contact_method"] and data["preferred_contact_method"] not in CONTACT_METHODS:
        errors["preferred_contact_method"] = "Choose a valid contact method."
    if data["preferred_contact_time"] and data["preferred_contact_time"] not in CONTACT_TIMES:
        errors["preferred_contact_time"] = "Choose a valid contact time."
    if data["message"] and len(data["message"]) < 20:
        errors["message"] = "Please provide at least 20 characters."
    return data, errors


def validate_password(password: str) -> list[str]:
    errors = []
    if len(password) < 12:
        errors.append("Use at least 12 characters.")
    if not re.search(r"[A-Z]", password):
        errors.append("Include an uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Include a lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Include a number.")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("Include a special character.")
    return errors
