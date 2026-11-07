"""Versioned editorial content. Drafts never enter public queries."""
import json
from datetime import datetime, timezone
from database.database import get_db

KINDS = ('settings', 'service', 'course', 'news', 'research', 'blog', 'download', 'tool', 'logo', 'company', 'threat', 'menu')

def init_studio():
    db = get_db()
    db.executescript('''
    CREATE TABLE IF NOT EXISTS studio_items (
        id INTEGER PRIMARY KEY, kind TEXT NOT NULL, draft TEXT NOT NULL,
        published TEXT, hidden INTEGER NOT NULL DEFAULT 0,
        deleted INTEGER NOT NULL DEFAULT 0, revision INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS studio_history (
        id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL, action TEXT NOT NULL,
        payload TEXT NOT NULL, admin_id INTEGER, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS security_limits (bucket TEXT NOT NULL, stamp REAL NOT NULL);
    CREATE INDEX IF NOT EXISTS security_limits_bucket ON security_limits(bucket, stamp);
    CREATE TABLE IF NOT EXISTS admin_sessions (token_hash TEXT PRIMARY KEY, admin_id INTEGER NOT NULL, expires REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS admin_pending_mfa (admin_id INTEGER PRIMARY KEY, secret TEXT NOT NULL);
    ''')
    if not db.execute('SELECT 1 FROM studio_items LIMIT 1').fetchone():
        seeds = [('settings', dict(title='AlphaX ZeroTech', summary='Secure by intelligence.', body='Cybersecurity services, practical training and research for a more resilient digital future.', email='alphaxzerotech@gmail.com', location='Rajapalayam, Tamil Nadu', ticker='USDT OTC Transaction Coordination & Brokerage Support • Contact Us for Enquiries', otc_title='OTC Digital Asset Services', otc_description='USDT OTC transaction coordination and brokerage support.', otc_button='Enquire Now', hero='Securing Your Digital Future.', speed='40', motion=True, ticker_visible=True, otc_visible=True, logos_visible=True))]
        for title, summary in [
            ('Web Application Security', 'Find weaknesses in your applications before they become incidents.'),
            ('Network Security', 'Review network exposure, segmentation and access controls.'),
            ('Cloud Security', 'Strengthen cloud configurations, identities and workloads.'),
            ('Mobile Security', 'Assess mobile applications and their connected services.'),
            ('API Security', 'Validate authentication, authorization and data protection.'),
            ('Penetration Testing', 'Understand real-world risk through an agreed testing scope.'),
            ('Security Audit', 'Review controls and prioritize practical improvements.'),
            ('SOC Monitoring', 'Discuss monitoring, detection and incident response requirements.')]:
            seeds.append(('service', dict(title=title, summary=summary, body='Start with a scoped consultation. We agree on systems, authorization, deliverables and timelines before any assessment. Contact us to discuss your requirements.')))
        for title in ['Cybersecurity Foundations', 'Web Security', 'Cloud Security']:
            seeds.append(('course', dict(title=title, summary='Practical learning with guided exercises and clear learning outcomes.', body='Course preview. Enquire for the syllabus, schedule, delivery mode and fees. Availability will be confirmed before enrolment.', label='Course preview')))
        seeds.append(('company', dict(title='Security with purpose.', summary='Based in Rajapalayam, Tamil Nadu. Founded by Ravichandran B.', body='AlphaX ZeroTech brings cybersecurity services, practical education and security research together. Our approach begins with understanding your requirements and defining an actionable scope.')))
        for title, summary, source in [
            ('ZAP', 'An open-source web application security testing tool for authorized assessments.', 'https://github.com/zaproxy/zaproxy'),
            ('Wazuh', 'An open-source platform for security monitoring, detection and response.', 'https://github.com/wazuh/wazuh'),
            ('YARA', 'A pattern-matching tool used in malware research and file classification.', 'https://github.com/VirusTotal/yara')]:
            seeds.append(('tool', dict(title=title, summary=summary, body='Community project. Review the official documentation and license before use. Run security testing only on systems you own or have permission to assess. AlphaX does not execute these tools through this website.', source=source, label='Community tool')))
        for title, file in [('Palo Alto Networks','paloalto.svg'),('CrowdStrike','crowdstrike.svg'),('Fortinet','fortinet.svg'),('Zscaler','zscaler.svg'),('SentinelOne','sentinelone.svg'),('Tenable','tenable.svg'),('Cisco','cisco-light.svg'),('Proofpoint','proofpoint.png'),('Cloudflare','cloudflare.svg'),('Bitdefender','bitdefender.webp')]:
            seeds.append(('logo',dict(title=title, image='/static/images/industry/'+file)))
        for position, (kind, payload) in enumerate(seeds):
            payload.setdefault('position', position)
            raw = json.dumps(payload)
            db.execute('INSERT INTO studio_items(kind,draft,published) VALUES (?,?,?)', (kind,raw,raw))
    # Versioned one-time seed markers prevent deleted content from returning.
    db.execute('CREATE TABLE IF NOT EXISTS studio_migrations (name TEXT PRIMARY KEY)')
    if not db.execute("SELECT 1 FROM studio_migrations WHERE name='editorial-v1'").fetchone():
        additions = []
        for position,(title,path) in enumerate([('Home','/'),('Company','/pages/company'),('Services','/pages/service'),('Tools','/pages/tool'),('Courses','/pages/course')]):
            additions.append(('menu',dict(title=title,source=path,position=position)))
        additions.extend([
            ('research',dict(title='Start with your attack surface.',summary='A practical approach to understanding what needs protection.',label='AlphaX field notes',body='Start by listing the applications, APIs, cloud accounts and internet-facing services your organization owns. Assign an owner to each asset.\n\nDocument how users authenticate and which data each system handles. Identify dependencies and integrations before choosing assessment methods.\n\nAgree on written testing authorization and scope. Record findings with reproducible evidence, business impact, recommended remediation and a retest outcome. Prioritize changes by risk rather than by the number of findings.')),
            ('blog',dict(title='Make MFA part of everyday security.',summary='Protect administrator accounts and plan recovery before an incident.',label='Practical guidance',body='Enable multi-factor authentication on privileged accounts. Prefer phishing-resistant authentication where supported. Give each administrator an individual account and only the permissions their work requires.\n\nKeep recovery codes in an approved secure location. Test the recovery process and remove access promptly when someone leaves.\n\nReview login alerts and administrative changes regularly. MFA is one control in a wider security process; it does not replace updates, backups or access reviews.')),
            ('download',dict(title='Security assessment preparation checklist',summary='A short checklist to prepare for a scoped assessment.',label='Checklist',body='1. Name the system owner and assessment contact.\n2. List the authorized assets and environments.\n3. Agree on permitted techniques, testing hours and exclusions.\n4. Prepare test accounts with appropriate permissions.\n5. Confirm backups and a recovery contact.\n6. Decide how findings and sensitive evidence will be shared.\n7. Schedule remediation and retesting.',source=''))
        ])
        for kind,payload in additions:
            raw=json.dumps(payload)
            db.execute('INSERT INTO studio_items(kind,draft,published) VALUES (?,?,?)',(kind,raw,raw))
        db.execute("INSERT INTO studio_migrations VALUES ('editorial-v1')")
    db.commit()

def items(kind=None, preview=False):
    rows = get_db().execute('SELECT * FROM studio_items WHERE deleted=0' + (' AND kind=?' if kind else ''), (kind,) if kind else ()).fetchall()
    result = []
    for row in rows:
        raw = row['draft'] if preview else row['published']
        if raw and (preview or not row['hidden']):
            result.append(dict(json.loads(raw), id=row['id'], kind=row['kind'], hidden=row['hidden'], revision=row['revision']))
    return sorted(result, key=lambda item: (item.get('position',0),item['id']))

def record(item_id, action, payload, admin_id):
    get_db().execute('INSERT INTO studio_history(item_id,action,payload,admin_id,created_at) VALUES (?,?,?,?,?)', (item_id,action,payload,admin_id,datetime.now(timezone.utc).isoformat()))
