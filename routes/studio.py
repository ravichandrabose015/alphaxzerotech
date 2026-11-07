import json
import re
import uuid
from pathlib import Path
from urllib.parse import urlsplit
from flask import Blueprint, Response, abort, current_app, flash, redirect, render_template, request, url_for, send_file
from database.database import get_db
from database.studio import KINDS, items, record
from security.auth import current_admin, super_admin_required
from security.csrf import validate_csrf

studio = Blueprint('studio', __name__)

CONTROL_SCREENS = {
    'pages': ('Page Builder', ('settings',)),
    'ticker': ('Ticker & OTC Settings', ('settings',)),
    'services': ('Company & Services', ('company','service')),
    'brand': ('Menus & Brand', ('settings','menu','logo')),
    'news': ('News Manager', ('news',)),
    'imports': ('Threat Import Inbox', ('news','threat')),
    'sources': ('Source Controls', ()),
    'tools': ('Tools Manager', ('tool',)),
    'courses': ('Courses & Lessons', ('course',)),
    'resources': ('Resources & Downloads', ('blog','research','download')),
    'motion': ('Motion Settings', ('settings',)),
    'publish': ('Preview / Publish / History', KINDS),
}

@studio.get('/admin/control/<screen>')
@super_admin_required
def control(screen):
    if screen not in CONTROL_SCREENS:
        abort(404)
    title,kinds=CONTROL_SCREENS[screen]
    rows=items(preview=True)
    query=request.args.get('q','').strip()[:120]
    records=[item for item in rows if item['kind'] in kinds and query.casefold() in item.get('title','').casefold()]
    status=request.args.get('status','')
    if status:
        db=get_db()
        ids={r['id'] for r in db.execute('SELECT id FROM studio_items WHERE published IS '+('NULL' if status=='draft' else 'NOT NULL')).fetchall()}
        records=[item for item in records if item['id'] in ids]
    trash=[]
    if screen=='publish':
        for row in get_db().execute('SELECT id,kind,draft,revision FROM studio_items WHERE deleted=1 ORDER BY id DESC').fetchall():
            trash.append(dict(json.loads(row['draft']),id=row['id'],kind=row['kind'],revision=row['revision']))
    history=get_db().execute('SELECT h.*, i.revision, i.deleted FROM studio_history h JOIN studio_items i ON i.id=h.item_id ORDER BY h.id DESC LIMIT 30').fetchall()
    return render_template('studio/control.html',screen=screen,heading=title,records=records,kinds=kinds,query=query,history=history,trash=trash)

def media_root():
    root = Path(current_app.config['CONTENT_HUB_UPLOAD_ROOT']) / 'studio'
    root.mkdir(parents=True, exist_ok=True)
    return root

@studio.get('/studio-media/<name>')
def media(name):
    if not re.fullmatch(r'[a-f0-9]{32}\.png',name):
        abort(404)
    # Draft uploads remain private until referenced by a published visible item.
    media_url = '/studio-media/'+name
    published = any(item.get('image')==media_url for item in items())
    if not published and not current_admin():
        abort(404)
    return send_file(media_root()/name, mimetype='image/png', max_age=0)

@studio.post('/admin/studio/import-news')
@super_admin_required
def import_news():
    validate_csrf()
    from services.news_import import import_cisa
    try:
        count = import_cisa(current_admin()['id'])
        flash(f'{count} new CISA entries imported as drafts for review.', 'success')
    except Exception:
        get_db().rollback()
        flash('The source could not be refreshed. Existing content is unchanged.', 'error')
    return redirect(url_for('studio.index'))

def context(preview=False):
    all_items = items(preview=preview)
    groups = {kind: [item for item in all_items if item['kind']==kind] for kind in KINDS}
    groups['threat'] = groups['threat'] + [item for item in groups['news'] if item.get('label','').startswith('CISA')]
    return dict(groups=groups, site=(groups['settings'] or [{}])[0], preview=preview)

@studio.get('/pages/<kind>')
def listing(kind):
    if kind not in (*KINDS,'resource') or kind in ('settings','logo','menu'):
        abort(404)
    ctx=context()
    records=ctx['groups'].get(kind,[])
    if kind=='resource':
        records=sum((ctx['groups'][key] for key in ('blog','research','download')),[])
    query=request.args.get('q','').strip()[:120]
    category=request.args.get('category','').strip()[:80]
    level=request.args.get('level','').strip()[:40]
    categories=sorted({item.get('category','General') for item in records})
    records=[item for item in records if query.casefold() in (item.get('title','')+' '+item.get('summary','')).casefold() and (not category or item.get('category','General')==category) and (not level or item.get('level','Beginner')==level)]
    template='studio/company.html' if kind=='company' else 'studio/catalogue.html'
    return render_template(template,kind=kind,records=records,query=query,categories=categories,selected_category=category,selected_level=level,**ctx)

def detail_template(item):
    return {'service':'studio/service_detail.html','course':'studio/course_detail.html','tool':'studio/tool_detail.html','threat':'studio/advisory_detail.html','news':'studio/advisory_detail.html'}.get(item['kind'],'studio/detail.html')

@studio.get('/other-services')
def other_services():
    return render_template('studio/otc.html',**context())

@studio.route('/training-enquiry',methods=['GET','POST'])
def training_enquiry():
    from routes.contact import index
    return index()

@studio.get('/read/<int:item_id>')
def detail(item_id):
    item = next((i for i in items() if i['id']==item_id and i['kind'] not in ('settings','logo')), None)
    if not item:
        abort(404)
    return render_template(detail_template(item), item=item, **context())

@studio.get('/read/<int:item_id>/download')
def download(item_id):
    item = next((i for i in items() if i['id']==item_id and i['kind']=='download'),None)
    if not item:
        abort(404)
    return Response(item.get('title','')+'\n\n'+item.get('body',''),mimetype='text/plain',headers={'Content-Disposition':f'attachment; filename="alphax-resource-{item_id}.txt"'})

@studio.get('/admin/studio')
@super_admin_required
def index():
    return render_template('studio/admin.html', records=items(preview=True), kinds=KINDS, history=get_db().execute('SELECT * FROM studio_history ORDER BY id DESC LIMIT 20').fetchall())

@studio.get('/admin/studio/preview')
@super_admin_required
def preview():
    return render_template('studio/home.html', **context(True))

@studio.get('/admin/studio/<int:item_id>/preview')
@super_admin_required
def preview_item(item_id):
    item = next((i for i in items(preview=True) if i['id']==item_id),None)
    if not item:
        abort(404)
    return render_template(detail_template(item), item=item, **context(True))

def clean_payload(form, kind):
    data = {key: form.get(key,'').strip() for key in ('title','summary','body','source','image','label','email','location','ticker','hero','otc_title','otc_description','otc_button','phone','social','maps','category','level','scope','deliverables','faq','curriculum','outcomes','features','usecases','affected','impact','mitigation')}
    if not data['title'] or len(data['title'])>180 or any(len(value)>20000 for value in data.values()):
        raise ValueError('Provide a title (up to 180 characters) and content within 20,000 characters.')
    for key in ('social','maps'):
        if data[key] and (urlsplit(data[key]).scheme != 'https' or not urlsplit(data[key]).hostname):
            raise ValueError('Social and map links must use HTTPS.')
    source = urlsplit(data['source'])
    if kind=='menu':
        if not re.fullmatch(r'/(?:[A-Za-z0-9_-]+/?)*',data['source']):
            raise ValueError('Menu links must be local paths such as /pages/service.')
    elif data['source'] and (source.scheme!='https' or not source.hostname or source.username or source.password or any(c.isspace() for c in data['source'])):
        raise ValueError('Source links must be complete HTTPS URLs.')
    if data['image'] and not (re.fullmatch(r'/static/images/[A-Za-z0-9_/-]+\.(?:png|jpg|webp|svg)',data['image']) or re.fullmatch(r'/studio-media/[a-f0-9]{32}\.png',data['image'])):
        raise ValueError('Choose a local image path under /static/images/.')
    if data['email'] and not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',data['email']):
        raise ValueError('Enter a valid email address.')
    data['position'] = max(0,min(999,int(form.get('position',0))))
    if kind=='settings':
        data['speed'] = str(max(20,min(120,int(form.get('speed',40)))))
        for key in ('motion','ticker_visible','otc_visible','logos_visible'):
            data[key] = form.get(key)=='on'
    return data

@studio.route('/admin/studio/edit/<int:item_id>', methods=['GET','POST'])
@super_admin_required
def edit(item_id):
    db = get_db()
    row = db.execute('SELECT * FROM studio_items WHERE id=? AND deleted=0',(item_id,)).fetchone() if item_id else None
    if item_id and not row:
        abort(404)
    kind = row['kind'] if row else request.args.get('kind','news')
    if kind not in KINDS or (not row and kind=='settings'):
        abort(400)
    data = json.loads(row['draft']) if row else {}
    error = None
    if request.method=='POST':
        validate_csrf()
        try:
            data = clean_payload(request.form,kind)
            upload = request.files.get('image_file')
            if upload and upload.filename:
                from PIL import Image, UnidentifiedImageError
                import io
                raw_image = upload.stream.read(5_000_001)
                if len(raw_image)>5_000_000:
                    raise ValueError('Images must be smaller than 5 MB.')
                try:
                    with Image.open(io.BytesIO(raw_image)) as picture:
                        if picture.format not in ('PNG','JPEG','WEBP') or picture.width*picture.height>16_000_000:
                            raise ValueError('Use a PNG, JPEG or WebP image under 16 megapixels.')
                        picture.load()
                        picture.thumbnail((2400,2400))
                        name = uuid.uuid4().hex+'.png'
                        picture.convert('RGBA').save(media_root()/name,format='PNG')
                    data['image'] = '/studio-media/'+name
                except (UnidentifiedImageError,OSError,Image.DecompressionBombError) as exc:
                    raise ValueError('This image could not be decoded safely.') from exc
            raw = json.dumps(data)
            if row:
                revision = request.form.get('revision',type=int)
                cursor = db.execute('UPDATE studio_items SET draft=?,revision=revision+1 WHERE id=? AND revision=?',(raw,item_id,revision))
                if cursor.rowcount!=1:
                    db.rollback()
                    abort(409,description='Content changed in another session. Reload before saving.')
            else:
                item_id = db.execute('INSERT INTO studio_items(kind,draft) VALUES (?,?)',(kind,raw)).lastrowid
            record(item_id,'draft_saved',raw,current_admin()['id'])
            db.commit()
            flash('Draft saved. Preview it, then publish when ready.','success')
            return redirect(url_for('studio.edit',item_id=item_id))
        except (ValueError,TypeError) as exc:
            db.rollback()
            error = str(exc)
    return render_template('studio/edit.html', data=data, row=row, kind=kind, error=error)

@studio.post('/admin/studio/<int:item_id>/<action>')
@super_admin_required
def action(item_id,action):
    validate_csrf()
    if action not in ('publish','hide','show','remove','restore','unpublish'):
        abort(400)
    db = get_db()
    row = db.execute('SELECT * FROM studio_items WHERE id=? AND deleted=?',(item_id,int(action=='restore'))).fetchone()
    if not row:
        abort(404)
    if row['kind']=='settings' and action!='publish':
        abort(400)
    fields = {'publish':'published=draft','hide':'hidden=1','show':'hidden=0','remove':'deleted=1','restore':'deleted=0,hidden=1','unpublish':'published=NULL'}
    cursor = db.execute('UPDATE studio_items SET '+fields[action]+',revision=revision+1 WHERE id=? AND revision=?',(item_id,request.form.get('revision',type=int)))
    if cursor.rowcount!=1:
        db.rollback()
        abort(409)
    record(item_id,action,row['draft'],current_admin()['id'])
    db.commit()
    flash('Content '+action+' completed.','success')
    return redirect(url_for('studio.control',screen='publish'))

@studio.post('/admin/studio/<int:item_id>/revision/<int:history_id>/restore')
@super_admin_required
def restore_revision(item_id,history_id):
    validate_csrf()
    db=get_db()
    historical=db.execute('SELECT payload FROM studio_history WHERE id=? AND item_id=?',(history_id,item_id)).fetchone()
    if not historical:
        abort(404)
    cursor=db.execute('UPDATE studio_items SET draft=?,revision=revision+1 WHERE id=? AND revision=? AND deleted=0',(historical['payload'],item_id,request.form.get('revision',type=int)))
    if cursor.rowcount!=1:
        db.rollback()
        abort(409,description='Reload the latest revision before restoring.')
    record(item_id,'revision_restored_to_draft',historical['payload'],current_admin()['id'])
    db.commit()
    flash('Version restored as a private draft. Preview before publishing.','success')
    return redirect(url_for('studio.edit',item_id=item_id))
