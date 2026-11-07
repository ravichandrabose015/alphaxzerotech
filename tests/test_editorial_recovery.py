from tests.test_studio import app, login, token
from database.database import get_db

def test_trash_restore_is_hidden_and_checks_revision(app):
    owner=login(app)
    csrf=token(owner,'/admin/studio')
    assert owner.post('/admin/studio/2/remove',data={'csrf_token':csrf,'revision':1}).status_code==302
    assert app.test_client().get('/read/2').status_code==404
    assert b'Restore hidden item' in owner.get('/admin/control/publish').data
    assert owner.post('/admin/studio/2/restore',data={'csrf_token':csrf,'revision':1}).status_code==409
    assert owner.post('/admin/studio/2/restore',data={'csrf_token':csrf,'revision':2}).status_code==302
    assert app.test_client().get('/read/2').status_code==404
    assert owner.post('/admin/studio/2/show',data={'csrf_token':csrf,'revision':3}).status_code==302
    assert app.test_client().get('/read/2').status_code==200

def test_revision_restore_is_private_and_bound_to_item(app):
    owner=login(app)
    csrf=token(owner,'/admin/studio')
    for revision,title in [(1,'First revision'),(2,'Second revision')]:
        assert owner.post('/admin/studio/edit/2',data={'csrf_token':csrf,'revision':revision,'title':title,'position':0}).status_code==302
    with app.app_context():
        history=get_db().execute("SELECT id FROM studio_history WHERE item_id=2 ORDER BY id LIMIT 1").fetchone()['id']
    path=f'/admin/studio/2/revision/{history}/restore'
    assert owner.post(path,data={'csrf_token':csrf,'revision':2}).status_code==409
    assert owner.post(path,data={'csrf_token':csrf,'revision':3}).status_code==302
    assert b'First revision' in owner.get('/admin/studio/2/preview').data
    public=app.test_client().get('/read/2')
    assert b'First revision' not in public.data
    assert b'Web Application Security' in public.data
    assert owner.post(f'/admin/studio/3/revision/{history}/restore',data={'csrf_token':csrf,'revision':1}).status_code==404

def test_recovery_requires_owner_and_csrf(app):
    assert app.test_client().post('/admin/studio/2/restore').status_code==302
    editor=login(app,'editor')
    assert editor.post('/admin/studio/2/restore').status_code==302
    owner=login(app)
    assert owner.post('/admin/studio/2/restore',data={'revision':1}).status_code==400
