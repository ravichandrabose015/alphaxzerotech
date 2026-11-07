"""Reviewed, versioned content snapshot. Never downloads during app startup."""
import json
from pathlib import Path
from database.database import get_db

def refresh_editorial():
    db=get_db()
    migration='compact-motion-editorial-2026-v1'
    if db.execute('SELECT 1 FROM studio_migrations WHERE name=?',(migration,)).fetchone():
        return
    db.execute('CREATE TABLE IF NOT EXISTS imported_sources (source_key TEXT PRIMARY KEY, item_id INTEGER NOT NULL)')
    snapshot=json.loads((Path(__file__).resolve().parents[1]/'data/editorial-2026.json').read_text(encoding='utf-8'))
    for payload in snapshot['news']:
        raw=json.dumps(payload)
        # A prior manual draft is preserved for review, never overwritten.
        existing=db.execute('SELECT item_id FROM imported_sources WHERE source_key=?',(payload['source_key'],)).fetchone()
        if existing:
            continue
        item_id=db.execute('INSERT INTO studio_items(kind,draft,published) VALUES (?,?,?)',('news',raw,raw)).lastrowid
        db.execute('INSERT INTO imported_sources VALUES (?,?)',(payload['source_key'],item_id))
    reports=[
        dict(title='ENISA Threat Landscape 2026',summary='A research briefing on dependencies, ransomware and geopolitical cyber activity affecting the European Union.',body='Published on 22 September 2026. This edition analyses incidents observed from January through December 2025. Its publication year must not be confused with the year in which the underlying events occurred.\n\nUse the report to examine how interconnected suppliers and services influence exposure. Compare its observations with your own asset inventory, response planning and sector context. Read the original report for its methodology and limitations.',source='https://www.enisa.europa.eu/publications/enisa-threat-landscape-2026',label='ENISA · 22 Sep 2026',category='Threat research',image='/static/images/visuals/research.svg'),
        dict(title='2026 Data Breach Investigations Report',summary='Verizon’s annual research provides context for vulnerability exploitation, human risk and third-party exposure.',body='The 2026 DBIR draws on breach and incident data. Its findings should be interpreted within the report’s observation periods and methodology.\n\nFor a practical review, map your internet-facing systems, patching process, identity controls and third-party dependencies against the risks described in the report. This is an AlphaX editorial reading guide, not an independent reproduction of the research.',source='https://www.verizon.com/business/resources/reports/dbir/',label='Verizon · 2026 DBIR',category='Breach research',image='/static/images/visuals/intelligence.svg'),
    ]
    blogs=[
        dict(title='API authorization: check the object, not just the login',summary='A practical review of access boundaries in application APIs.',body='A successful sign-in establishes who a caller is. The application still needs to decide whether that caller may read or change each requested object.\n\nDefine ownership and permissions on the server. Test with two accounts and confirm that changing an identifier cannot expose another account’s records. Repeat the checks for list, export, update and delete endpoints.\n\nKeep response fields limited to the caller’s needs, record important administrative actions and retest access controls after changes. Use the OWASP API Security guidance as a review checklist.',source='https://owasp.org/www-project-api-security/',category='Application security',label='AlphaX practical guide',image='/static/images/visuals/code.svg'),
        dict(title='Prepare your team before the next security incident',summary='A short plan for contacts, evidence, communication and recovery.',body='Start with an agreed response contact list and clear ownership. Identify which systems and records matter most, and decide how the team will communicate if normal channels are unavailable.\n\nPreserve relevant logs and record a timeline. Separate confirmed facts from assumptions. Agree who may isolate systems and who can authorize recovery.\n\nPractise a small tabletop scenario, test restoration from backups and capture improvements after the exercise. This guide is educational; incident handling should follow your organization’s agreed procedures.',source='https://www.cisa.gov/stopransomware',category='Incident readiness',label='AlphaX practical guide',image='/static/images/visuals/forensics.svg'),
    ]
    for kind,records in [('research',reports),('blog',blogs)]:
        for index,payload in enumerate(records):
            payload['position']=index
            raw=json.dumps(payload)
            db.execute('INSERT INTO studio_items(kind,draft,published) VALUES (?,?,?)',(kind,raw,raw))
    for row in db.execute("SELECT * FROM studio_items WHERE kind IN ('course','tool','company','blog','research','settings')").fetchall():
        for field in ('draft','published'):
            if not row[field]:
                continue
            payload=json.loads(row[field])
            if row['kind']=='settings':
                payload['ticker_visible']=False
            elif row['kind']=='company' and payload.get('title')=='Security with purpose.':
                payload.update(title='About Me',summary='Cybersecurity Analyst | Ethical Hacker | VAPT Specialist',body='Cybersecurity enthusiast with hands-on experience in penetration testing, vulnerability assessment, web application security and network security. I am passionate about learning, solving real-world security challenges and contributing to a safer digital ecosystem.')
            elif not payload.get('image'):
                name=payload.get('title','')
                visual='cloud' if 'Cloud' in name else 'web' if 'Web' in name or name=='ZAP' else 'learning' if row['kind']=='course' else 'network' if name=='Wazuh' else 'forensics' if name=='YARA' else 'identity' if row['kind']=='blog' else 'research'
                payload['image']='/static/images/visuals/'+visual+'.svg'
            # Identifiers are chosen from a fixed tuple above, not user input.
            db.execute('UPDATE studio_items SET '+field+'=? WHERE id=?',(json.dumps(payload),row['id']))
    db.execute('INSERT INTO studio_migrations VALUES (?)',(migration,))
    db.commit()
