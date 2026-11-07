import json
import re
import pytest
from app import create_app
from database.admin_users import create_admin
from database.database import get_db

@pytest.fixture
def app(tmp_path):
    app = create_app({'TESTING':True,'DATABASE':str(tmp_path/'app.db'),'SECRET_KEY':'test-only','MARKETPLACE_DATABASE_URL':''})
    with app.app_context():
        create_admin('owner','LongPassphrase#2026')
        create_admin('editor','LongPassphrase#2026',role='editor')
    return app

def token(client, path='/admin/login'):
    page = client.get(path)
    return re.search(r'name="csrf_token" value="([^"]+)"',page.get_data(as_text=True)).group(1)

def login(app, name='owner'):
    client = app.test_client()
    assert client.post('/admin/login', data={'csrf_token':token(client),'username':name,'password':'LongPassphrase#2026'}).status_code==302
    return client

def test_draft_publish_hide_remove_and_conflict(app):
    owner = login(app)
    csrf = token(owner,'/admin/studio')
    assert owner.post('/admin/studio/edit/0?kind=news',data={'csrf_token':csrf,'title':'Private draft','body':'<script>alert(1)</script>','position':'0'}).status_code==302
    with app.app_context():
        id = get_db().execute('SELECT max(id) FROM studio_items').fetchone()[0]
    public = app.test_client()
    assert public.get(f'/read/{id}').status_code==404
    assert public.get('/admin/studio/preview').status_code==302
    assert b'Private draft' in owner.get('/admin/studio/preview').data
    assert owner.post(f'/admin/studio/{id}/publish',data={'csrf_token':csrf,'revision':1}).status_code==302
    page = public.get(f'/read/{id}')
    assert page.status_code==200 and b'&lt;script&gt;' in page.data
    assert b'<script>alert' not in page.data
    assert owner.post(f'/admin/studio/{id}/hide',data={'csrf_token':csrf,'revision':1}).status_code==409
    assert owner.post(f'/admin/studio/{id}/hide',data={'csrf_token':csrf,'revision':2}).status_code==302
    assert public.get(f'/read/{id}').status_code==404
    assert owner.post(f'/admin/studio/{id}/show',data={'csrf_token':csrf,'revision':3}).status_code==302
    assert public.get(f'/read/{id}').status_code==200
    assert owner.post(f'/admin/studio/{id}/remove',data={'csrf_token':csrf,'revision':4}).status_code==302
    assert public.get(f'/read/{id}').status_code==404

def test_auth_csrf_and_role_checks(app):
    assert app.test_client().post('/admin/studio/2/publish').status_code==302
    editor = login(app,'editor')
    assert editor.get('/admin/studio').status_code==302
    owner = login(app)
    assert owner.post('/admin/studio/2/publish').status_code==400
    assert owner.get('/admin/studio/2/publish').status_code==405

@pytest.mark.parametrize('source',['javascript:alert(1)','//evil.example','http://example.com','https://user:pass@example.com'])
def test_unsafe_links_rejected(app,source):
    client = login(app)
    csrf = token(client,'/admin/studio')
    result = client.post('/admin/studio/edit/0?kind=news', data={'csrf_token':csrf,'title':'Link','source':source})
    assert result.status_code==200 and b'HTTPS' in result.data
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM studio_items WHERE kind='news' AND json_extract(draft,'$.title')='Link'").fetchone()[0]==0

def test_logout_invalidates_stolen_cookie(app):
    client = login(app)
    cookie = client.get_cookie('session').value
    csrf = token(client,'/admin/studio')
    assert client.post('/admin/logout',data={'csrf_token':csrf}).status_code==302
    stolen = app.test_client()
    stolen.set_cookie('session',cookie)
    assert stolen.get('/admin/studio').status_code==302

def test_password_change_requires_current_password(app):
    client = login(app)
    csrf = token(client,'/admin/settings')
    client.post('/admin/settings',data={'csrf_token':csrf,'action':'password','new_password':'DifferentPassword#2026','confirm_password':'DifferentPassword#2026'})
    assert login(app).get('/admin/studio').status_code==200

def test_setup_requires_installation_token(tmp_path):
    application = create_app({'TESTING':False,'DATABASE':str(tmp_path/'setup.db'),'SECRET_KEY':'test','SETUP_TOKEN':'installation-token'})
    client = application.test_client()
    assert client.post('/admin/setup',data={'username':'attacker'}).status_code==404

def test_otc_service_and_public_routes(app):
    client = app.test_client()
    page = client.get('/contact?service=OTC+Digital+Asset+Services')
    assert b'<option selected>OTC Digital Asset Services</option>' in page.data
    for path in ['/', '/pages/service','/pages/course','/pages/company','/pages/tool','/pages/news','/pages/blog','/pages/research','/pages/download','/read/2','/healthz']:
        response = client.get(path)
        assert response.status_code==200, path
        assert response.headers['X-Content-Type-Options']=='nosniff'

def test_forwarded_header_does_not_bypass_limit(app):
    client = app.test_client()
    for index in range(10):
        assert client.get('/admin/login',headers={'X-Forwarded-For':f'10.0.0.{index}'}).status_code==200
    assert client.get('/admin/login',headers={'X-Forwarded-For':'8.8.8.8'}).status_code==429

def test_menu_rejects_external_destinations(app):
    client=login(app)
    csrf=token(client,'/admin/studio')
    result=client.post('/admin/studio/edit/0?kind=menu',data={'csrf_token':csrf,'title':'Unsafe menu','source':'//example.com'})
    assert b'Menu links must be local paths' in result.data

def test_download_is_published_only(app):
    client=app.test_client()
    with app.app_context():
        id=get_db().execute("SELECT id FROM studio_items WHERE kind='download'").fetchone()[0]
    result=client.get(f'/read/{id}/download')
    assert result.status_code==200
    assert result.headers['Content-Disposition'].startswith('attachment;')
    with app.app_context():
        get_db().execute('UPDATE studio_items SET hidden=1 WHERE id=?',(id,))
        get_db().commit()
    assert client.get(f'/read/{id}/download').status_code==404

def test_import_deduplicates_and_does_not_resurrect_deleted(app,monkeypatch):
    import io
    from datetime import date
    from services.news_import import import_cisa
    from urllib import request
    raw=json.dumps({'vulnerabilities':[dict(cveID='CVE-2026-12345',dateAdded=date.today().isoformat(),vulnerabilityName='Test advisory',shortDescription='Test only',requiredAction='Review')]}).encode()
    class Opener:
        def open(self,*args,**kwargs):
            return io.BytesIO(raw)
    monkeypatch.setattr(request,'build_opener',lambda *args: Opener())
    with app.app_context():
        assert import_cisa()==1
        assert import_cisa()==0
        row=get_db().execute("SELECT * FROM studio_items WHERE kind='news' AND json_extract(draft,'$.title')='Test advisory'").fetchone()
        assert row['published'] is None
        get_db().execute('UPDATE studio_items SET deleted=1 WHERE id=?',(row['id'],))
        get_db().commit()
        assert import_cisa()==0


def test_approved_public_page_families_and_admin_screens(app):
    public=app.test_client()
    for path in ['/pages/company','/pages/service','/other-services','/pages/course','/training-enquiry?course=Web+Security','/pages/tool','/pages/threat','/pages/resource','/pages/news','/read/2','/read/10','/read/14']:
        assert public.get(path).status_code==200,path
    owner=login(app)
    from routes.studio import CONTROL_SCREENS
    for screen in CONTROL_SCREENS:
        path='/admin/control/'+screen
        assert public.get(path).status_code==302,path
        response=owner.get(path)
        assert response.status_code==200,path
        assert CONTROL_SCREENS[screen][0] in __import__("html").unescape(response.get_data(as_text=True))
