from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf"
OUTPUT.mkdir(parents=True, exist_ok=True)
LOGO = ROOT / "static" / "images" / "logo-transparent.png"

GUIDES = {
    "phishing-identification-checklist.pdf": {
        "title": "Phishing Identification Checklist",
        "subtitle": "Pause, verify and report before you click.",
        "sections": [
            ("Check the sender", ["Compare the display name with the full email address.", "Treat unexpected messages from known contacts as unverified until confirmed through another channel.", "Watch for look-alike domains, extra characters and unusual reply-to addresses."]),
            ("Check the request", ["Be cautious with urgency, secrecy, payment changes, password resets and requests for one-time codes.", "Do not approve an MFA prompt you did not initiate.", "Never send passwords, recovery codes or private keys by email or chat."]),
            ("Check links and attachments", ["Hover over links and inspect the real destination before opening.", "Avoid unexpected archives, macro-enabled documents and executable files.", "Open important services from a trusted bookmark instead of the message link."]),
            ("If suspicious", ["Do not reply or forward the message to colleagues.", "Use the organisation's reporting process and preserve the original message.", "If you clicked, disconnect only when instructed, report immediately and change exposed credentials from a trusted device."]),
        ],
    },
    "ransomware-response-checklist.pdf": {
        "title": "Ransomware Response Checklist",
        "subtitle": "Contain safely, preserve evidence and recover through a controlled plan.",
        "sections": [
            ("First 15 minutes", ["Report the event through the emergency contact path.", "Isolate affected devices from wired, wireless and VPN connections without powering them off unless safety requires it.", "Record visible messages, time, device name and the first observed symptoms."]),
            ("Containment", ["Disable compromised accounts and risky remote access after collecting essential evidence.", "Identify shared drives, backup systems and neighbouring systems that may be exposed.", "Block verified malicious indicators at appropriate controls and monitor for recurrence."]),
            ("Evidence and decisions", ["Preserve logs, memory and disk evidence using approved procedures.", "Track decisions, owners and timestamps in a central incident record.", "Engage legal, insurance, communications and law enforcement contacts according to policy."]),
            ("Recovery", ["Rebuild from known-good images and restore only verified clean data.", "Patch the entry point, rotate credentials and validate monitoring before reconnecting.", "Complete a lessons-learned review and update controls, backups and playbooks."]),
        ],
    },
    "password-mfa-security-guide.pdf": {
        "title": "Password and MFA Security Guide",
        "subtitle": "Protect every account with unique credentials and phishing-resistant verification.",
        "sections": [
            ("Passwords", ["Use a unique password for every account.", "Create long passphrases and store them in an approved password manager.", "Change a password immediately when exposure or reuse is suspected."]),
            ("Multi-factor authentication", ["Prefer passkeys or hardware security keys when available.", "Use an authenticator app when stronger options are not available.", "Never share one-time codes and never approve an unexpected prompt."]),
            ("Recovery", ["Store recovery codes offline in a secure location.", "Keep recovery email and phone details current.", "Remove old devices, sessions and unused application passwords."]),
            ("Administrator accounts", ["Use a separate privileged account for administration.", "Require stronger MFA and shorter sessions for privileged access.", "Review account activity and access rights regularly."]),
        ],
    },
    "employee-cybersecurity-awareness-guide.pdf": {
        "title": "Employee Cybersecurity Awareness Guide",
        "subtitle": "Simple habits that reduce everyday security risk.",
        "sections": [
            ("Email and messaging", ["Verify unusual requests through a known contact method.", "Report suspicious messages instead of interacting with them.", "Do not send confidential data through unapproved channels."]),
            ("Devices and updates", ["Install approved updates promptly and do not disable security controls.", "Lock the screen when away and keep devices physically secure.", "Use approved software and avoid unknown USB devices."]),
            ("Remote work", ["Use trusted networks and the approved VPN where required.", "Prevent shoulder surfing and protect calls involving sensitive information.", "Keep work data out of personal accounts and consumer storage services."]),
            ("Report early", ["Report lost devices, accidental sharing and suspicious activity immediately.", "Provide clear facts without deleting messages or changing evidence.", "Early reporting helps the security team contain issues before they spread."]),
        ],
    },
    "small-business-incident-response-checklist.pdf": {
        "title": "Small Business Incident Response Checklist",
        "subtitle": "A lightweight preparation and response guide for small teams.",
        "sections": [
            ("Prepare", ["Name an incident leader and backup contact.", "Maintain an asset list, critical supplier contacts and an offline copy of the response plan.", "Test backups and record recovery priorities for important services."]),
            ("Detect and assess", ["Capture who noticed the issue, when it began and which systems are affected.", "Classify the impact on operations, customers, data and legal obligations.", "Avoid destructive changes until evidence and scope are understood."]),
            ("Contain and communicate", ["Isolate affected accounts and systems using documented procedures.", "Use a separate trusted channel for incident coordination.", "Provide accurate updates and avoid speculation."]),
            ("Recover and improve", ["Restore in priority order and verify systems before normal use.", "Monitor closely for recurrence and rotate exposed credentials.", "Document lessons, owners and due dates for corrective actions."]),
        ],
    },
}


styles = getSampleStyleSheet()
TITLE = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=24, leading=29, textColor=colors.HexColor("#082417"), alignment=TA_LEFT, spaceAfter=8)
SUBTITLE = ParagraphStyle("Subtitle", parent=styles["BodyText"], fontSize=10.5, leading=16, textColor=colors.HexColor("#587063"), spaceAfter=18)
HEADING = ParagraphStyle("Heading", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=colors.HexColor("#14852a"), spaceBefore=10, spaceAfter=6)
BODY = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=9.5, leading=14.5, textColor=colors.HexColor("#24372d"), leftIndent=8, firstLineIndent=-8, spaceAfter=4)
FOOT = ParagraphStyle("Foot", parent=styles["BodyText"], fontSize=8, leading=11, textColor=colors.HexColor("#6b7b72"))


def header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(colors.HexColor("#169b32"))
    canvas.rect(0, height - 7 * mm, width, 7 * mm, fill=1, stroke=0)
    canvas.setStrokeColor(colors.HexColor("#d9e8dd"))
    canvas.line(18 * mm, 15 * mm, width - 18 * mm, 15 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#607268"))
    canvas.drawString(18 * mm, 9.5 * mm, "AlphaX ZeroTech - Security Awareness")
    canvas.drawRightString(width - 18 * mm, 9.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build(filename, guide):
    target = OUTPUT / filename
    doc = SimpleDocTemplate(str(target), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=19 * mm, bottomMargin=21 * mm, title=guide["title"], author="AlphaX ZeroTech")
    story = []
    if LOGO.exists():
        logo = Image(str(LOGO), width=46 * mm, height=30 * mm)
        logo.hAlign = "LEFT"
        story.extend([logo, Spacer(1, 2 * mm)])
    story.extend([Paragraph(guide["title"], TITLE), Paragraph(guide["subtitle"], SUBTITLE)])
    cells = []
    for heading, bullets in guide["sections"]:
        body = [Paragraph(heading, HEADING)] + [Paragraph(f"- {bullet}", BODY) for bullet in bullets]
        cells.append(body)
    table = Table([[cells[0], cells[1]], [cells[2], cells[3]]], colWidths=[84 * mm, 84 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), .7, colors.HexColor("#d7e8da")), ("INNERGRID", (0, 0), (-1, -1), .5, colors.HexColor("#e3eee5")), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fbfefb")), ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    story.extend([table, Spacer(1, 6 * mm), Paragraph("Use this guide with your organisation's policies and incident contacts. For urgent events, follow the approved escalation path immediately.", FOOT)])
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    return target


if __name__ == "__main__":
    for name, guide in GUIDES.items():
        print(build(name, guide))
