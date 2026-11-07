import io
import json
from PIL import Image
from database.database import get_db
from tests.test_studio import app, login, token

def test_image_validation_and_draft_privacy(app,tmp_path):
    app.config['CONTENT_HUB_UPLOAD_ROOT']=str(tmp_path/'media')
    client=login(app)
    csrf=token(client,'/admin/studio')
    response=client.post('/admin/studio/edit/0?kind=logo',data={'csrf_token':csrf,'title':'Bad','image_file':(io.BytesIO(b'<script>bad</script>'),'bad.png')})
    assert b'could not be decoded safely' in response.data
    stream=io.BytesIO()
    Image.new('RGB',(20,20),'green').save(stream,format='PNG')
    stream.seek(0)
    assert client.post('/admin/studio/edit/0?kind=logo',data={'csrf_token':csrf,'title':'Good','image_file':(stream,'good.png')}).status_code==302
    with app.app_context():
        row=get_db().execute('SELECT * FROM studio_items ORDER BY id DESC LIMIT 1').fetchone()
        image=json.loads(row['draft'])['image']
    public=app.test_client()
    assert public.get(image).status_code==404
    assert client.get(image).status_code==200
    assert client.post(f"/admin/studio/{row['id']}/publish",data={'csrf_token':csrf,'revision':1}).status_code==302
    assert public.get(image).status_code==200
    assert public.get('/studio-media/../../config.py').status_code==404
