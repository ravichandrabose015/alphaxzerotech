"""Seed the editable AlphaX starter catalogue without overwriting admin changes."""

import json

from database.content_hub import slugify
from database.marketplace_database import marketplace_cursor


TOOLS = (
    {
        "name": "Nuclei", "version": "3.11", "category": "Vulnerability Scanner", "license": "MIT",
        "os": "Windows, Linux, macOS", "platform": "CLI",
        "image": "/static/images/tools/nuclei.svg",
        "short": "Fast template-based vulnerability scanning for authorised security assessments.",
        "full": "Nuclei helps security teams run repeatable checks against web applications, APIs, networks and cloud services. Its signed community templates make it useful for validation, exposure discovery and continuous security testing.",
        "install": "1. Open the official releases page.\n2. Choose the package for your operating system.\n3. Verify the published checksum or signature.\n4. Install the official nuclei-templates collection.\n5. Test only assets you own or have written permission to assess.",
        "notes": "Starter listing points only to the verified ProjectDiscovery repository and official documentation.",
        "repo": "https://github.com/projectdiscovery/nuclei", "download": "https://github.com/projectdiscovery/nuclei/releases", "docs": "https://docs.projectdiscovery.io/tools/nuclei/overview",
    },
    {
        "name": "OWASP ZAP", "version": "2.17", "category": "Web & API Testing", "license": "Apache-2.0",
        "os": "Windows, Linux, macOS", "platform": "Desktop, CLI, Docker",
        "image": "/static/images/tools/owasp-zap.svg",
        "short": "Open-source web application and API security testing maintained by the ZAP project.",
        "full": "OWASP ZAP provides intercepting proxy, passive scanning, automated scanning and API testing workflows. It is suited to secure development, QA validation and supervised penetration testing.",
        "install": "1. Use the official ZAP download or GitHub release page.\n2. Select the supported installer, package or container image.\n3. Review the official getting-started guide.\n4. Configure a test context and exclude out-of-scope systems.\n5. Begin with passive scanning before any active test.",
        "notes": "Use active scanning only with explicit authorisation and a defined test scope.",
        "repo": "https://github.com/zaproxy/zaproxy", "download": "https://github.com/zaproxy/zaproxy/releases", "docs": "https://www.zaproxy.org/docs/",
    },
    {
        "name": "Wazuh", "version": "4.14", "category": "SIEM & XDR", "license": "GPL-2.0",
        "os": "Linux server; Windows, Linux and macOS agents", "platform": "Server, Agent, Cloud",
        "image": "/static/images/tools/wazuh.svg",
        "short": "Open-source SIEM and XDR for endpoint telemetry, log analysis and threat detection.",
        "full": "Wazuh combines endpoint agents, log collection, file-integrity monitoring, vulnerability visibility and detection rules. It supports central monitoring for organisations building a SOC or improving security operations.",
        "install": "1. Review the official architecture and sizing guidance.\n2. Use the official installation assistant or supported deployment method.\n3. Secure the manager, indexer and dashboard credentials.\n4. Enrol a small pilot group of agents.\n5. Tune rules and retention before wider deployment.",
        "notes": "Plan storage, TLS, role-based access and log retention before production rollout.",
        "repo": "https://github.com/wazuh/wazuh", "download": "https://github.com/wazuh/wazuh/releases", "docs": "https://documentation.wazuh.com/current/index.html",
    },
    {
        "name": "Suricata", "version": "8.0", "category": "Network IDS/IPS", "license": "GPL-2.0",
        "os": "Linux, FreeBSD, Windows", "platform": "Network sensor",
        "image": "/static/images/tools/suricata.svg",
        "short": "High-performance network IDS, IPS and security monitoring engine.",
        "full": "Suricata analyses network traffic using signatures, protocol parsing and flow records. Security teams use it for intrusion detection, network visibility and incident investigation.",
        "install": "1. Follow the official installation guide for your operating system.\n2. Place the sensor at an authorised monitoring point.\n3. Update trusted rules from approved sources.\n4. Start in IDS mode and validate alerts.\n5. Tune noisy rules before considering inline IPS mode.",
        "notes": "Inline blocking can affect production traffic; validate and tune in detection mode first.",
        "repo": "https://github.com/OISF/suricata", "download": "https://github.com/OISF/suricata/releases", "docs": "https://docs.suricata.io/",
    },
    {
        "name": "MISP", "version": "2.5", "category": "Threat Intelligence", "license": "AGPL-3.0",
        "os": "Linux server", "platform": "Web platform, API, TAXII",
        "image": "/static/images/tools/misp.svg",
        "short": "Threat intelligence platform for collecting, correlating and sharing indicators.",
        "full": "MISP organises indicators, events, relationships and taxonomies so analysts can collaborate on threat intelligence. It supports structured sharing and integrations with security platforms.",
        "install": "1. Review the official supported installation options.\n2. Deploy on a dedicated, patched Linux host.\n3. Configure TLS, background workers and restricted administrator access.\n4. Define sharing groups and distribution rules before importing data.\n5. Back up the database, attachments and encryption keys.",
        "notes": "Threat intelligence may contain sensitive operational data; configure sharing permissions carefully.",
        "repo": "https://github.com/MISP/MISP", "download": "https://github.com/MISP/MISP/releases", "docs": "https://www.misp-project.org/documentation/",
    },
)


COURSES = (
    ("Ethical Hacking & Web Security", "Beginner", "Web Security", "Reconnaissance\nNetwork and web scanning\nOWASP Top 10\nAuthentication and session testing\nSafe vulnerability validation\nProfessional reporting"),
    ("SOC Analyst & SIEM Operations", "Intermediate", "Security Operations", "SOC workflow\nLog sources and parsing\nSIEM dashboards\nAlert triage\nDetection engineering\nIncident escalation and reporting"),
    ("Multi-Cloud & AI Security", "Intermediate", "Cloud Security", "Cloud shared-responsibility model\nAWS, Azure and Google Cloud IAM\nSecure configuration\nCloud logging and monitoring\nContainer security\nAI workload risk controls"),
    ("Incident Response & Threat Hunting", "Intermediate", "Incident Response", "Preparation and playbooks\nEvidence collection\nIOC and behaviour analysis\nThreat-hunting hypotheses\nContainment and recovery\nPost-incident review"),
    ("Digital Forensics & Malware Investigation", "Advanced", "Digital Forensics", "Evidence handling\nDisk and memory fundamentals\nNetwork forensics\nMalware behaviour analysis\nTimeline creation\nForensic reporting"),
)


THREATS = (
    ("Critical PHP security updates require immediate patching", "critical", "Application Security", "PHP", "CVE-2026-109618, CVE-2026-109619", "PHP published security releases addressing critical unauthenticated remote-code-execution risk. Inventory supported PHP branches, test the fixed release and patch exposed systems promptly.", "https://www.php.net/"),
    ("Oracle October 2026 Java security update", "critical", "Java Security", "Oracle", "Oracle Java SE CPU October 2026", "Oracle's October 2026 update includes a large set of Java SE security fixes. Organisations should identify deployed JDK and JRE versions, test supported updates and move to the current security baseline.", "https://www.oracle.com/security-alerts/cpuoct2026.html"),
    ("Chainalysis platform security incident", "high", "Crypto Security", "Chainalysis", "Vendor incident notice", "Chainalysis reported an ongoing security response affecting parts of its platform. Customers should follow the vendor's current instructions, rotate reused credentials and review access activity.", "https://www.chainalysis.com/blog/security-incident-october-30/"),
    ("GitHub expands push protection for AI-detected secrets", "medium", "Software Supply Chain", "GitHub", "Secret scanning update", "GitHub introduced a public preview that can block additional secrets based on their surrounding code context. Maintainers can review secret-scanning and push-protection settings for eligible repositories.", "https://github.blog/changelog/2026-10-28-push-protection-beyond-predefined-secret-patterns/"),
)


RESOURCES = (
    ("StackWarp: Confidential VM integrity under cross-core manipulation", "Research", "research paper", "A practical summary of recent research into deterministic stack-pointer manipulation and confidential virtual-machine integrity.", "https://www.usenix.org/conference/usenixsecurity26/cycle1-accepted-papers"),
    ("PHILTER: Security gaps in AI phishing detection research", "Research", "research paper", "A research brief on real-world robustness, privacy and interpretability gaps in AI-based phishing website detection.", "https://www.usenix.org/conference/usenixsecurity26/cycle1-accepted-papers"),
    ("PASSKEYS-RADAR: Measuring passkey deployment security", "Research", "research paper", "A concise review of large-scale passkey deployment findings and the configuration weaknesses identified by researchers.", "https://www.usenix.org/conference/usenixsecurity26/cycle1-accepted-papers"),
    ("Inside the evolution of a Mirai-based DDoS service", "Research", "research paper", "A defensive research note on botnet infrastructure, commercial DDoS operations and lessons for network defenders.", "https://www.usenix.org/conference/usenixsecurity26/cycle1-accepted-papers"),
    ("Building a dependable monthly patch cycle", "Blog", "blog", "A practical AlphaX guide to asset inventory, risk-based testing, maintenance windows and patch verification.", ""),
    ("How to adopt open-source security tools safely", "Blog", "blog", "A checklist for checking official sources, release signatures, permissions, scope and operational ownership.", ""),
    ("Turning threat intelligence into action", "Blog", "blog", "How teams can connect verified intelligence to detection, prioritisation and measurable response decisions.", ""),
    ("Web application assessment for a growing SaaS team", "Case Studies", "case study", "An illustrative case study showing how scoped testing, risk prioritisation and retesting can improve release confidence.", ""),
    ("Reducing cloud exposure through IAM review", "Case Studies", "case study", "An illustrative case study covering identity review, excessive permissions, monitoring and remediation validation.", ""),
    ("Improving incident readiness for a small business", "Case Studies", "case study", "An illustrative case study on playbooks, contacts, backups and a focused tabletop exercise.", ""),
    ("Chainalysis publishes continuing incident updates", "News", "news", "The blockchain analytics provider published continuing updates on a cybersecurity incident and service restoration.", "https://www.chainalysis.com/blog/security-incident-october-30/"),
    ("Mercado Bitcoin response freezes part of stolen funds", "News", "news", "Chainalysis described a coordinated response following a reported incident at Mercado Bitcoin.", "https://www.chainalysis.com/blog/chainalysis-response-mercado-bitcoin/"),
    ("Critical PHP security releases published", "News", "news", "PHP maintainers urged supported users to install current security releases addressing critical vulnerabilities.", "https://www.php.net/"),
    ("Oracle publishes October 2026 Java security baseline", "News", "news", "New Java runtime releases were published as part of Oracle's October 2026 Critical Patch Update.", "https://docs.oracle.com/en-us/iaas/releasenotes/java-management/jdk-cpu-october-2026.htm"),
    ("GitHub extends push protection beyond known patterns", "News", "news", "GitHub announced context-aware protection for additional potential secrets in eligible repositories.", "https://github.blog/changelog/2026-10-28-push-protection-beyond-predefined-secret-patterns/"),
    ("Phishing Identification Checklist", "Downloads", "security guide", "A quick awareness checklist for recognising suspicious messages, links, attachments and login requests.", ""),
    ("Ransomware Response Checklist", "Downloads", "security guide", "A concise first-response checklist covering isolation, escalation, evidence preservation and recovery.", ""),
    ("Password and MFA Security Guide", "Downloads", "security guide", "Practical guidance for unique passwords, password managers, multi-factor authentication and recovery codes.", ""),
    ("Employee Cybersecurity Awareness Guide", "Downloads", "security guide", "Everyday guidance for email, devices, remote work, data handling and incident reporting.", ""),
    ("Small Business Incident Response Checklist", "Downloads", "security guide", "A lightweight preparation and response checklist for small organisations.", ""),
)


DOWNLOAD_FILES = {
    "Phishing Identification Checklist": "phishing-identification-checklist.pdf",
    "Ransomware Response Checklist": "ransomware-response-checklist.pdf",
    "Password and MFA Security Guide": "password-mfa-security-guide.pdf",
    "Employee Cybersecurity Awareness Guide": "employee-cybersecurity-awareness-guide.pdf",
    "Small Business Incident Response Checklist": "small-business-incident-response-checklist.pdf",
}


def _seed_tools(cursor):
    for order, tool in enumerate(TOOLS, 1):
        cursor.execute(
            """INSERT INTO security_tools(
                name,slug,thumbnail_path,banner_path,gallery_paths,short_description,full_description,
                version,category,price_cents,currency,license_name,operating_system,platform,
                repository_url,download_url,documentation_url,install_guide,tool_file_path,
                tool_file_name,tool_file_sha256,documentation_path,screenshot_paths,release_notes,
                status,is_featured,is_pinned,display_order,created_by,updated_by,published_at
            ) VALUES(%s,%s,%s,%s,'[]'::jsonb,%s,%s,%s,%s,0,'USD',%s,%s,%s,%s,%s,%s,%s,'','','','','[]'::jsonb,%s,'published',TRUE,%s,%s,0,0,NOW())
            ON CONFLICT(slug) DO NOTHING""",
            (tool["name"], slugify(tool["name"]), tool["image"], tool["image"], tool["short"], tool["full"], tool["version"], tool["category"], tool["license"], tool["os"], tool["platform"], tool["repo"], tool["download"], tool["docs"], tool["install"], tool["notes"], order == 1, order),
        )


def _insert_content(cursor, module, title, category, summary, full, metadata, *, severity="", difficulty="", tags=(), order=0, featured=True, asset_paths=None):
    cursor.execute(
        """INSERT INTO content_items(module,title,slug,short_description,full_description,category,tags,
           author_name,severity,difficulty,access_type,price_cents,currency,version,asset_paths,metadata,
           status,is_featured,is_pinned,display_order,published_at,created_by,updated_by)
           VALUES(%s,%s,%s,%s,%s,%s,%s,'AlphaX Editorial Team',%s,%s,'free',0,'USD','2026',%s::jsonb,%s::jsonb,
           'published',%s,FALSE,%s,NOW(),0,0) ON CONFLICT(module,slug) DO NOTHING""",
        (module, title, slugify(title), summary, full, category, list(tags), severity, difficulty, json.dumps(asset_paths or {}), json.dumps(metadata), featured, order),
    )


def _seed_content(cursor):
    for order, (title, level, category, syllabus) in enumerate(COURSES, 1):
        _insert_content(cursor, "training", title, category, f"A practical {level.lower()} course with an original AlphaX syllabus.", f"This course provides a structured, defensive learning path.\n\nSyllabus\n{syllabus}", {"course_category": category, "level": level, "duration": "Self-paced", "syllabus": syllabus, "prerequisites": "Basic computer and networking knowledge", "learning_objectives": "Understand the topic, practise safely and document findings clearly."}, difficulty=level.lower(), tags=(category, "Cybersecurity Course"), order=order)
    for order, (title, severity, category, vendor, reference, summary, source) in enumerate(THREATS, 1):
        _insert_content(cursor, "threat", title, category, summary, summary + "\n\nDefensive action: verify the affected product and version, follow the vendor advisory, test the update and record completion.", {"vendor": vendor, "cve_id": reference, "source": source, "release_date": "2026", "mitigation_steps": "Use the official vendor advisory, patch supported systems, monitor for suspicious activity and validate remediation.", "references": source}, severity=severity, tags=(vendor, category), order=order)
    for order, (title, category, resource_type, summary, source) in enumerate(RESOURCES, 1):
        filename = DOWNLOAD_FILES.get(title)
        asset_paths = {"resource_file": {"path": f"/static/downloads/{filename}", "name": filename}} if filename else None
        _insert_content(cursor, "resource", title, category, summary, summary + (f"\n\nVerified source: {source}" if source else "\n\nPrepared as original AlphaX ZeroTech awareness content."), {"resource_type": resource_type, "summary": summary, "source": source, "references": source, "target_audience": "Security teams, developers, business owners and learners", "language": "English", "download_enabled": category == "Downloads"}, tags=(category, resource_type), order=order, featured=category in {"News", "Research", "Downloads"}, asset_paths=asset_paths)


def seed_starter_catalog():
    """Create initial editable records once; existing admin-edited rows remain untouched."""
    with marketplace_cursor() as cursor:
        _seed_tools(cursor)
        _seed_content(cursor)
