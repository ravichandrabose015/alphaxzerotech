from tests.test_studio import app
from database.database import get_db
from database.editorial_refresh import refresh_editorial
from database.studio import items

def test_refined_home_has_only_section_ticker(app):
    response=app.test_client().get('/')
    assert response.status_code==200
    assert b'aria-label="Announcement"' not in response.data
    assert b'ambient-network' in response.data
    assert b'Other Services' in response.data
    assert b'OTC Digital Asset Services' in response.data

def test_curated_news_and_illustrations_are_published_once(app):
    with app.app_context():
        news=items('news')
        assert len(news)==10
        assert all(n['source'].startswith('https://www.cisa.gov/') for n in news)
        assert all(n['published_date'].startswith('2026-') for n in news)
        assert all(n.get('image') for n in news)
        refresh_editorial()
        assert len(items('news'))==10
        deleted_id=news[0]['id']
        get_db().execute('UPDATE studio_items SET deleted=1 WHERE id=?',(deleted_id,))
        get_db().commit()
        refresh_editorial()
        assert len(items('news'))==9
    client=app.test_client()
    for name in ['web','cloud','network','learning','privacy','intelligence','research','forensics','code','identity','mobile']:
        response=client.get('/static/images/visuals/'+name+'.svg')
        assert response.status_code==200
        assert b'<svg' in response.data

def test_company_restores_original_profile_text(app):
    page=app.test_client().get('/pages/company')
    assert b'Who We Are' not in page.data
    assert b'Founder. Visionary.' in page.data
    assert b'About Me' in page.data
    assert b'To help organizations strengthen their digital security' in page.data
