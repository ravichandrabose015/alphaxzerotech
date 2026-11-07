"""Only fetch the fixed public CISA catalog; imported entries require review."""
import json
import urllib.request
from datetime import date, timedelta
from database.database import get_db
from database.studio import record

CATALOG = 'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def import_cisa(admin_id=None):
    request = urllib.request.Request(CATALOG, headers={'User-Agent':'AlphaX-Editorial/1.0'})
    with urllib.request.build_opener(NoRedirect).open(request, timeout=15) as response:
        raw = response.read(8_000_001)
    if len(raw)>8_000_000:
        raise ValueError('Catalog exceeds the allowed size.')
    entries = json.loads(raw).get('vulnerabilities', [])
    db = get_db()
    db.execute('CREATE TABLE IF NOT EXISTS imported_sources (source_key TEXT PRIMARY KEY, item_id INTEGER NOT NULL)')
    count = 0
    cutoff = (date.today()-timedelta(days=7)).isoformat()
    for entry in sorted(entries,key=lambda x:x.get('dateAdded',''),reverse=True)[:100]:
        added = entry.get('dateAdded','')
        if added < cutoff or added > date.today().isoformat():
            continue
        cve = str(entry.get('cveID',''))[:80]
        if not cve or db.execute('SELECT 1 FROM imported_sources WHERE source_key=?',(cve,)).fetchone():
            continue
        payload = dict(title=str(entry.get('vulnerabilityName',cve))[:180], summary=str(entry.get('shortDescription',''))[:1500], body=f"{cve}\nAdded to CISA KEV: {added}\n\nRequired action: {str(entry.get('requiredAction',''))[:3000]}\n\nThe catalog addition date is not necessarily the date an attack occurred.", label='CISA KEV · '+added, source='https://www.cisa.gov/known-exploited-vulnerabilities-catalog', position=0)
        text = json.dumps(payload)
        item_id = db.execute('INSERT INTO studio_items(kind,draft) VALUES (?,?)',('news',text)).lastrowid
        db.execute('INSERT INTO imported_sources VALUES (?,?)',(cve,item_id))
        record(item_id,'source_imported_draft',text,admin_id)
        count += 1
    db.commit()
    return count
