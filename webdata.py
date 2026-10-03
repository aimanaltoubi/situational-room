"""Data management pages and APIs: file editor, change log, drill-down records,
annotations, analytics layout config and official sanctions-list import."""

import json
import os
import threading
from datetime import datetime, timezone

from flask import (Blueprint, Response, abort, jsonify, redirect, render_template_string,
                   request, send_file, url_for, flash)

from tools import datastore as ds
from tools import workspace as ws

PREFERRED_COLS = ["date", "entity_id", "name", "type", "country", "location", "event_type", "actor_grouped", "actor",
                  "target", "killed", "injured", "program", "authority", "designation_date", "status", "source",
                  "relation", "ownership_pct", "confidence", "ref_value", "note", "tag"]

STYLE = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{min-height:100vh;padding:24px 16px;background:radial-gradient(circle at 50% 10%,#3a0012,#1a0008 70%);
  font-family:'IBM Plex Sans Arabic','Noto Naskh Arabic',Arial,sans-serif;color:#f0e8ec}
a{color:#fff}.wrap{max-width:1300px;margin:0 auto}
h1{font-size:24px;color:#fff;margin-bottom:4px}.sub{color:#e0c4cf;font-size:12px;margin-bottom:16px}
.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:14px}
.btn{display:inline-block;padding:8px 16px;font-size:13px;font-weight:700;text-decoration:none;color:#3a0012;
  background:#fff;border:none;border-radius:6px;cursor:pointer;font-family:inherit}
.btn.secondary{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.5)}
.btn.danger{background:#e8004a;color:#fff}.btn:disabled{opacity:.5;cursor:default}
.btn.small{padding:3px 9px;font-size:11px}
input[type=text],input[type=search],select,textarea{padding:7px 10px;background:#2a0410;color:#fff;
  border:1px solid rgba(255,255,255,.3);border-radius:6px;font-family:inherit;font-size:13px}
.flash{background:rgba(34,160,80,.15);border:1px solid #22a050;color:#a8f5c4;padding:8px 14px;border-radius:6px;margin-bottom:14px;font-size:13px}
.err{background:rgba(232,0,74,.15);border-color:#e8004a;color:#ffb3c7}
.card{background:rgba(26,0,8,.55);border:1px solid rgba(255,255,255,.22);border-radius:12px;padding:18px;margin-bottom:14px}
table{width:100%;border-collapse:collapse;font-size:12px}
th,td{padding:6px 8px;border-bottom:1px solid rgba(255,255,255,.12);text-align:right;vertical-align:top}
th{color:#fff;background:rgba(255,255,255,.07);white-space:nowrap;position:sticky;top:0}
td[contenteditable]{min-width:70px;max-width:360px;outline:none}
td[contenteditable]:focus{background:rgba(255,255,255,.12);outline:1px solid #fff}
td.dirty{background:rgba(224,160,32,.25)}tr.hl td{background:rgba(255,255,255,.18)}
.scroll{overflow:auto;max-height:68vh;border:1px solid rgba(255,255,255,.15);border-radius:8px}
.muted{color:#e0c4cf}
"""

INDEX_TEMPLATE = """<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>ملفات البيانات — {{ w.name_ar }}</title>
<style>{{ style }}</style></head><body><div class="wrap">
<h1>ملفات بيانات المساحة</h1><div class="sub">{{ w.name_ar }} · كل ملف قابل للتعديل مباشرة وكل تعديل مسجَّل</div>
{% with messages = get_flashed_messages() %}{% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}{% endwith %}
<div class="bar"><a class="btn secondary" href="{{ url_for('workspace_home', slug=w.slug) }}">&rarr; المساحة</a>
<a class="btn secondary" href="{{ url_for('data.changes_page', slug=w.slug) }}">سجل التغييرات</a>
{% if w.analytics_profile == 'sanctions' %}
{% for k, label in imports.items() %}
<form method="post" action="{{ url_for('data.import_list', slug=w.slug, which=k) }}" style="display:inline">
<button class="btn secondary" type="submit">استيراد: {{ label }}</button></form>{% endfor %}{% endif %}</div>
<div class="card"><table><tr><th>الملف</th><th>الاسم</th><th>السجلات</th><th>آخر تعديل</th><th></th></tr>
{% for f in files %}<tr><td>{{ f.label }}</td><td dir="ltr">{{ f.name }}</td>
<td>{{ f.rows if f.exists else '—' }}</td><td>{{ f.mtime or 'غير موجود' }}</td>
<td><a class="btn small" href="{{ url_for('data.editor', slug=w.slug, key=f.key) }}">{{ 'تعديل' if f.exists else 'إنشاء' }}</a>
{% if f.exists %}<a class="btn small secondary" href="{{ url_for('data.export', slug=w.slug, key=f.key) }}">تنزيل</a>{% endif %}</td></tr>{% endfor %}
</table></div></div></body></html>"""

EDITOR_TEMPLATE = """<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{{ label }} — {{ w.name_ar }}</title>
<style>{{ style }}</style></head><body><div class="wrap">
<h1>{{ label }}</h1><div class="sub">{{ w.name_ar }} · انقر على أي خانة لتعديلها — يُحفظ تلقائياً ويُسجَّل في سجل التغييرات</div>
<div id="msg"></div>
<div class="bar"><a class="btn secondary" href="{{ url_for('data.index', slug=w.slug) }}">&rarr; كل الملفات</a>
{% if text %}<button class="btn" onclick="saveText()">حفظ النص</button>
{% else %}
<input type="search" id="q" placeholder="بحث…" oninput="onSearch()" style="min-width:220px">
<button class="btn small" onclick="addRow()">+ سطر</button>
<button class="btn small secondary" onclick="addCol()">+ عمود</button>
<button class="btn small secondary" onclick="undo()">↶ تراجع</button>
<a class="btn small secondary" href="{{ url_for('data.export', slug=w.slug, key=key) }}">تنزيل CSV</a>{% endif %}
<form method="post" action="{{ url_for('rebuild_workspace', slug=w.slug) }}" style="display:inline">
<button class="btn small" type="submit">حفظ وإعادة بناء المساحة</button></form></div>
{% if text %}<textarea id="txt" style="width:100%;height:65vh;direction:ltr">{{ content }}</textarea>
{% else %}<div id="info" class="muted" style="margin-bottom:6px"></div>
<div class="scroll"><table id="tbl"></table></div>
<div class="bar" style="margin-top:10px"><button class="btn small secondary" onclick="go(-1)">السابق</button>
<span id="pg" class="muted"></span><button class="btn small secondary" onclick="go(1)">التالي</button></div>{% endif %}
<script>
const BASE={{ base|tojson }}, SIZE=100, HL={{ row|tojson }};
let page=0,q='',cols=[],total=0,timer=null;
const msg=(t,err)=>{const m=document.getElementById('msg');m.className='flash'+(err?' err':'');m.textContent=t;setTimeout(()=>{m.textContent='';m.className='';},4000);};
async function api(url,opts){opts=opts||{};opts.headers=Object.assign({'X-Requested-With':'fetch','Content-Type':'application/json'},opts.headers||{});
  const r=await fetch(url,opts);const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.error||('HTTP '+r.status));return j;}
async function saveText(){try{await api(BASE.replace('/data/','/text/'),{method:'POST',body:JSON.stringify({text:document.getElementById('txt').value})});msg('تم الحفظ');}catch(e){msg(e.message,1);}}
function onSearch(){clearTimeout(timer);timer=setTimeout(()=>{q=document.getElementById('q').value;page=0;load();},250);}
function go(d){const last=Math.max(0,Math.ceil(total/SIZE)-1);page=Math.min(last,Math.max(0,page+d));load();}
async function load(){
  if(HL!==null&&!q&&!window._hlDone){page=Math.floor(HL/SIZE);}
  try{const j=await api(BASE+'?page='+page+'&size='+SIZE+'&q='+encodeURIComponent(q));cols=j.columns;total=j.total;render(j.rows);}catch(e){msg(e.message,1);}}
function render(rows){
  const t=document.getElementById('tbl');t.textContent='';
  const hr=document.createElement('tr');cols.concat(['']).forEach(c=>{const th=document.createElement('th');th.textContent=c;hr.appendChild(th);});t.appendChild(hr);
  rows.forEach(r=>{const tr=document.createElement('tr');if(HL!==null&&r._i===HL&&!window._hlDone)tr.className='hl';
    cols.forEach(c=>{const td=document.createElement('td');td.contentEditable='true';td.textContent=r[c];td.dataset.orig=r[c];
      td.addEventListener('blur',()=>saveCell(td,r._i,c));td.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();td.blur();}});tr.appendChild(td);});
    const ac=document.createElement('td');const b=document.createElement('button');b.className='btn small danger';b.textContent='حذف';
    b.onclick=()=>delRow(r._i);ac.appendChild(b);tr.appendChild(ac);t.appendChild(tr);
    if(tr.className==='hl'){setTimeout(()=>tr.scrollIntoView({block:'center'}),50);}});
  window._hlDone=true;
  document.getElementById('info').textContent=total.toLocaleString()+' سجل';
  document.getElementById('pg').textContent=' صفحة '+(page+1)+' من '+Math.max(1,Math.ceil(total/SIZE))+' ';}
async function saveCell(td,i,c){const v=td.textContent;if(v===td.dataset.orig)return;
  try{await api(BASE+'/row',{method:'POST',body:JSON.stringify({i:i,values:{[c]:v}})});td.dataset.orig=v;td.classList.remove('dirty');msg('تم الحفظ');}
  catch(e){td.classList.add('dirty');msg(e.message,1);}}
async function addRow(){try{const j=await api(BASE+'/row',{method:'POST',body:JSON.stringify({values:{}})});q='';document.getElementById('q').value='';window._hlDone=true;
  const r=await api(BASE+'?page=0&size=1');page=Math.floor((r.total-1)/SIZE);await load();msg('أُضيف سطر جديد في النهاية');}catch(e){msg(e.message,1);}}
async function delRow(i){if(!confirm('حذف هذا السطر؟ (يمكن التراجع عنه)'))return;try{await api(BASE+'/row/'+i,{method:'DELETE'});load();msg('تم الحذف');}catch(e){msg(e.message,1);}}
async function addCol(){const n=prompt('اسم العمود الجديد');if(!n)return;try{await api(BASE+'/column',{method:'POST',body:JSON.stringify({name:n})});load();}catch(e){msg(e.message,1);}}
async function undo(){try{const j=await api(BASE+'/undo',{method:'POST',body:'{}'});msg('تم التراجع: '+j.summary);load();}catch(e){msg(e.message,1);}}
if(!document.getElementById('txt'))load();
</script></div></body></html>"""

CHANGES_TEMPLATE = """<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>سجل التغييرات — {{ w.name_ar }}</title>
<style>{{ style }}</style></head><body><div class="wrap"><h1>سجل التغييرات</h1><div class="sub">{{ w.name_ar }}</div>
<div class="bar"><a class="btn secondary" href="{{ url_for('data.index', slug=w.slug) }}">&rarr; ملفات البيانات</a></div>
<div class="card"><table><tr><th>الوقت (UTC)</th><th>المستخدم</th><th>الملف</th><th>العملية</th><th>التفاصيل</th></tr>
{% for c in items %}<tr><td dir="ltr">{{ c.ts.replace('T',' ') }}</td><td>{{ c.user }}</td><td>{{ c.file }}</td><td>{{ c.op }}</td><td>{{ c.summary }}</td></tr>
{% else %}<tr><td colspan="5" class="muted">لا توجد تغييرات مسجّلة بعد.</td></tr>{% endfor %}</table></div></div></body></html>"""


def create_blueprint(start_build, is_building):
    bp = Blueprint("data", __name__)

    # ── helpers ──────────────────────────────────────────────────────────
    def _ws(slug):
        w = ws.get_workspace(slug)
        if not w:
            abort(404)
        return w

    def _user():
        a = request.authorization
        return a.username if a and a.username else "مستخدم"

    def _guard_write():
        # custom header: a cross-site form post cannot set it
        if request.headers.get("X-Requested-With") != "fetch":
            abort(400)

    def _err(e, code=400):
        return jsonify({"error": str(e)}), code

    def _key(slug, key):
        try:
            ds.check_key(slug, key)
        except ds.DataError:
            abort(404)

    # ── pages ────────────────────────────────────────────────────────────
    @bp.route("/w/<slug>/data/")
    def index(slug):
        w = _ws(slug)
        files = []
        for key in ds.allowed_keys(slug):
            name, label = ws.DATA_FILES[key]
            p = ds.file_path(slug, key)
            exists = os.path.exists(p)
            rows = 0
            if exists and key not in ws.TEXT_KEYS:
                with open(p, encoding="utf-8-sig") as f:
                    rows = max(0, sum(1 for _ in f) - 1)
            files.append({"key": key, "name": name, "label": label, "exists": exists, "rows": rows,
                          "mtime": datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M") if exists else ""})
        return render_template_string(INDEX_TEMPLATE, style=STYLE, w=w, files=files,
                                      imports={"ofac": "قائمة OFAC (SDN)", "un": "قائمة مجلس الأمن (UN)"})

    @bp.route("/w/<slug>/data/<key>")
    def editor(slug, key):
        w = _ws(slug)
        _key(slug, key)
        text = key in ws.TEXT_KEYS
        row = request.args.get("row", type=int)
        return render_template_string(
            EDITOR_TEMPLATE, style=STYLE, w=w, key=key, label=ws.DATA_FILES[key][1], text=text,
            content=ds.read_text(slug, key) if text else "", row=row,
            base=url_for("data.api_table", slug=slug, key=key))

    @bp.route("/w/<slug>/data/<key>/export")
    def export(slug, key):
        _ws(slug)
        _key(slug, key)
        p = ds.file_path(slug, key)
        if not os.path.exists(p):
            cols, _ = ds.read_table(slug, key)
            ds.write_table(slug, key, cols, [])
        return send_file(p, as_attachment=True, download_name=ws.DATA_FILES[key][0])

    @bp.route("/w/<slug>/changes")
    def changes_page(slug):
        w = _ws(slug)
        return render_template_string(CHANGES_TEMPLATE, style=STYLE, w=w, items=ds.changes(slug, limit=500))

    # ── editor API ───────────────────────────────────────────────────────
    @bp.route("/w/<slug>/api/data/<key>")
    def api_table(slug, key):
        _ws(slug)
        _key(slug, key)
        res = ds.query(slug, key, q=request.args.get("q", ""), page=request.args.get("page", 0, int),
                       size=min(request.args.get("size", 100, int), 500))
        return jsonify(res)

    @bp.route("/w/<slug>/api/data/<key>/row", methods=["POST"])
    def api_row(slug, key):
        _ws(slug)
        _key(slug, key)
        _guard_write()
        body = request.get_json(silent=True) or {}
        try:
            if body.get("i") is None:
                i = ds.insert_row(slug, key, body.get("values") or {}, _user())
                return jsonify({"i": i})
            ds.update_row(slug, key, int(body["i"]), body.get("values") or {}, _user())
            return jsonify({"ok": True})
        except (ds.DataError, ValueError, TypeError) as e:
            return _err(e)

    @bp.route("/w/<slug>/api/data/<key>/row/<int:i>", methods=["DELETE"])
    def api_row_delete(slug, key, i):
        _ws(slug)
        _key(slug, key)
        _guard_write()
        try:
            ds.delete_row(slug, key, i, _user())
        except ds.DataError as e:
            return _err(e)
        return jsonify({"ok": True})

    @bp.route("/w/<slug>/api/data/<key>/column", methods=["POST"])
    def api_column(slug, key):
        _ws(slug)
        _key(slug, key)
        _guard_write()
        try:
            ds.add_column(slug, key, (request.get_json(silent=True) or {}).get("name"), _user())
        except ds.DataError as e:
            return _err(e)
        return jsonify({"ok": True})

    @bp.route("/w/<slug>/api/data/<key>/undo", methods=["POST"])
    def api_undo(slug, key):
        _ws(slug)
        _key(slug, key)
        _guard_write()
        try:
            return jsonify({"summary": ds.undo_last(slug, key, _user())})
        except ds.DataError as e:
            return _err(e)

    @bp.route("/w/<slug>/api/text/<key>", methods=["POST"])
    def api_text(slug, key):
        _ws(slug)
        _key(slug, key)
        _guard_write()
        if key not in ws.TEXT_KEYS:
            abort(404)
        try:
            ds.write_text(slug, key, (request.get_json(silent=True) or {}).get("text", ""), _user())
        except ds.DataError as e:
            return _err(e)
        return jsonify({"ok": True})

    # ── drill-down records for the dashboard ─────────────────────────────
    @bp.route("/w/<slug>/api/records")
    def api_records(slug):
        _ws(slug)
        try:
            targets = json.loads(request.args.get("t", "[]"))
        except ValueError:
            return _err("bad request")
        limit = min(request.args.get("limit", 200, int), 1000)
        out = []
        for t in targets[:4]:
            key = t.get("file", "")
            try:
                ds.check_key(slug, key)
                res = ds.query(slug, key, filters=t.get("filters") or [], limit=limit)
            except ds.DataError:
                continue
            show = [c for c in PREFERRED_COLS if c in res["columns"]][:8] or res["columns"][:8]
            ref = t.get("ref", "")
            out.append({"file": key, "label": ws.DATA_FILES[key][1], "columns": show, "total": res["total"],
                        "rows": [{"_i": r["_i"], **{c: r[c] for c in show}} for r in res["rows"]],
                        "annotations": ds.annotations_for(slug, key, ref) if ref else []})
        return jsonify(out)

    @bp.route("/w/<slug>/api/annotations", methods=["POST"])
    def api_annotation(slug):
        _ws(slug)
        _guard_write()
        b = request.get_json(silent=True) or {}
        try:
            ds.check_key(slug, b.get("file", ""))
            ds.insert_row(slug, "annotations", {
                "ref_file": b["file"], "ref_value": str(b.get("ref", ""))[:300], "note": str(b.get("note", ""))[:2000],
                "tag": str(b.get("tag", ""))[:40], "author": _user(),
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}, _user())
        except (ds.DataError, KeyError) as e:
            return _err(e)
        return jsonify({"ok": True})

    # ── analytics layout (rename / hide / reorder / chart type) ──────────
    def _cfg_path(slug):
        return os.path.join(ws.workspace_dir(slug), "analytics_config.json")

    @bp.route("/w/<slug>/api/analytics-config", methods=["GET", "POST"])
    def api_analytics_config(slug):
        _ws(slug)
        p = _cfg_path(slug)
        if request.method == "GET":
            if not os.path.exists(p):
                return jsonify({"widgets": {}, "order": []})
            with open(p, encoding="utf-8") as f:
                return jsonify(json.load(f))
        _guard_write()
        b = request.get_json(silent=True) or {}
        widgets, order = b.get("widgets"), b.get("order", [])
        if not isinstance(widgets, dict) or not isinstance(order, list) or len(json.dumps(b)) > 100_000:
            return _err("bad config")
        clean = {}
        for wid, c in widgets.items():
            if not isinstance(c, dict):
                continue
            item = {}
            if isinstance(c.get("title"), str):
                item["title"] = c["title"][:200]
            if c.get("hidden") is True:
                item["hidden"] = True
            if c.get("kind") in ("bar", "line", "doughnut", "hbar"):
                item["kind"] = c["kind"]
            clean[str(wid)[:80]] = item
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"widgets": clean, "order": [str(o)[:80] for o in order][:500]}, f, ensure_ascii=False)
        ds.log_change(slug, _user(), "analytics", "layout", "تعديل تخطيط التحليلات")
        return jsonify({"ok": True})

    # ── official sanctions list import ───────────────────────────────────
    @bp.route("/w/<slug>/import-list/<which>", methods=["POST"])
    def import_list(slug, which):
        w = _ws(slug)
        if w["analytics_profile"] != "sanctions" or which not in ("ofac", "un"):
            abort(404)
        from tools import sanction_lists
        user = _user()

        def work():
            try:
                n = sanction_lists.import_list(slug, which, user)
                ds.log_change(slug, user, "sanctions_entities", "import", f"استيراد {which.upper()}: {n} جهة جديدة")
            except Exception as e:  # network / parsing problems are reported in the log, not raised
                ds.log_change(slug, user, "sanctions_entities", "import-failed", f"فشل استيراد {which.upper()}: {e}")

        threading.Thread(target=work, daemon=True).start()
        flash("بدأ الاستيراد في الخلفية — تابع «سجل التغييرات» ثم أعد بناء المساحة.")
        return redirect(url_for("data.index", slug=slug))

    return bp
