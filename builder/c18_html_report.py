# c18_html_report.py
# HTML Part 4: report + final assembly
# Auto-extracted from Cell 18

######################################################################
# CELL 8 — Part 4 of 4  [REDESIGNED]
# generateReport() — calls Claude API with war events context
# Opens full-screen professional Arabic report overlay
# Final assembly: HTML_TEMPLATE = _P1 + _P2 + _P3 + _P4
######################################################################

_P4 = ("""
<script>
// ══════════════════════════════════════════════════════════════════
// REPORT GENERATION
// Calls Claude API with war context from WAR_EVENTS + analytics
// Opens overlay in same tab (no popup blockers)
// ══════════════════════════════════════════════════════════════════

// Build daily event summary from WAR_EVENTS
function _buildDailyContext(){
  const evs = Array.isArray(WAR_EVENTS) ? WAR_EVENTS : [];
  const byDay = {};
  evs.forEach(e=>{
    const d = parseInt(e.day_of_war||e.day||0);
    if(!d) return;
    if(!byDay[d]) byDay[d]={day:d,total:0,strikes:0,airstrikes:0,casualties:0,categories:{}};
    byDay[d].total++;
    const cat = (e.category||e.type||'').toLowerCase();
    if(cat.includes('strike')||cat.includes('attack')) byDay[d].strikes++;
    if(cat.includes('air')) byDay[d].airstrikes++;
    byDay[d].casualties += (parseInt(e.killed||e.casualties||0)||0);
    byDay[d].categories[cat] = (byDay[d].categories[cat]||0)+1;
  });
  return Object.values(byDay).sort((a,b)=>a.day-b.day);
}

// Build category breakdown
function _buildCatSummary(){
  const evs = Array.isArray(WAR_EVENTS) ? WAR_EVENTS : [];
  const cats = {};
  evs.forEach(e=>{const c=e.category||e.type||'other';cats[c]=(cats[c]||0)+1;});
  return Object.entries(cats).sort((a,b)=>b[1]-a[1]).slice(0,10);
}

async function generateReport(){
  const btn = $('generate-report-btn');
  const loader = $('report-loader');
  const reportStatus = $('report-status');

  // ── PRIMARY PATH: open the pre-generated C8.5 report ─────────
  if(typeof _C85_REPORT === 'string' &&
     _C85_REPORT.length > 500 &&
     _C85_REPORT.length > 500){
    openFullReport(_C85_REPORT);
    return;
  }

  // ── FALLBACK: C8.5 not run yet — call Claude for text analysis ─
  if(btn) btn.disabled = true;
  if(loader) loader.style.display = 'block';

  const statusEl = $('report-status-text');
  const pctEl    = $('report-pct-label');
  const barEl    = $('report-progress-bar');
  const stepsEl  = $('report-steps');

  const steps = [
    { label:'جاري تجميع البيانات…',    pct: 10 },
    { label:'إرسال الطلب للنموذج…',    pct: 30 },
    { label:'تحليل البيانات…',          pct: 55 },
    { label:'جاري كتابة التقرير…',      pct: 80 },
    { label:'فتح التقرير…',             pct: 95 },
  ];
  const setStep = (i)=>{
    if(statusEl) statusEl.textContent = steps[i].label;
    if(pctEl)    pctEl.textContent    = steps[i].pct+'%';
    if(barEl)    barEl.style.width    = steps[i].pct+'%';
    if(stepsEl)  stepsEl.innerHTML    = steps.slice(0,i+1).map((s,j)=>
      `<div style="font-size:11px;color:${j===i?'var(--burg-500)':'var(--text-faint)'}">
        ${j<i?'✓':j===i?'▶':'○'} ${s.label}</div>`).join('');
  };

  try{
    setStep(0);
    const cp  = CONFLICT_PREDICTION  || {};
    const ea  = ESCALATION_ANALYSIS  || {};
    const pa  = POLITICAL_ANALYSIS   || {};
    const mt  = MARITIME_THREAT      || {};
    const vi  = VIP_INTELLIGENCE     || {};
    const di  = DIPLOMATIC_INDEX     || {};
    const jc  = JAMMING_CORRELATION  || {};
    const evs = Array.isArray(WAR_EVENTS) ? WAR_EVENTS : [];

    const dailyData = _buildDailyContext();
    const catSummary = _buildCatSummary();
    const last7 = dailyData.slice(-7);
    const last7Str = last7.map(d=>`اليوم ${d.day}: ${d.total} حدث (غارات=${d.airstrikes})`).join(' | ');
    const peakDay = dailyData.reduce((m,d)=>d.total>m.total?d:m, {total:0,day:0});
    const totalEvs = evs.length;
    const totalAir = dailyData.reduce((s,d)=>s+d.airstrikes,0);
    const totalKilled = ea.total_killed||0;
    const catStr = catSummary.map(([c,n])=>`${c}:${n}`).join('، ');
    const vipDests = (vi.top_destinations||[]).slice(0,5).map(d=>d[0]||d).join('، ');
    const recentJam = ((GPSJAM_DATA&&GPSJAM_DATA.history)||[]).slice(-7)
      .map(h=>`${(h.date||'').slice(5)}: ${Math.round((h.me_avg||0)*100)}%`).join(' | ');
    const maritimeZones = (mt.zones||[]).filter(z=>z.risk_level==='critical'||z.risk_level==='high')
      .map(z=>z.name).join('، ');

    const prompt = `أنت محلل سياسي وعالم بيانات رفيع المستوى. اكتب تقريراً تحليلياً شاملاً باللغة العربية مبنياً على البيانات أدناه فقط.
لا تذكر أي مصادر بيانات خارجية. استخدم فقط "وفق سجل الأحداث الموثقة".

البيانات — منذ اليوم 1 حتى اليوم ${_war_day_num}:
إجمالي الأحداث: ${totalEvs} | الغارات: ${totalAir} | القتلى: ${totalKilled}
يوم الذروة: اليوم ${peakDay.day} (${peakDay.total} حدث)
تصنيف الأحداث: ${catStr}
الأسبوع الأخير: ${last7Str}
اتجاه التصعيد: ${ea.trend||'—'} | درجة الخطر: ${cp.score||'—'}/100 (${cp.level||'—'})
تشويش GPS (7 أيام): ${recentJam||'—'}
VIP رحلات: ${vi.total_vip||0} | وجهات: ${vipDests||'—'}
المناطق البحرية الخطرة: ${maritimeZones||'—'}
هجمات سفن موثقة: ${mt.vessel_attacks||0}

# الملخص التنفيذي
# مسار التصعيد اليومي
# تشويش GPS والعمليات
# حركة طائرات كبار المسؤولين
# الوضع البحري
# التوقعات — الأسبوع القادم (3 سيناريوهات بنسب مجموعها 100%)
# التحقق من دقة التوقعات السابقة
# الخاتمة
نثر تحليلي كامل — 1500 كلمة على الأقل.`;

    setStep(1); await new Promise(r=>setTimeout(r,300)); setStep(2);

    const resp = await fetch('https://api.anthropic.com/v1/messages', {
      method:'POST',
      headers:{
        'Content-Type':'application/json',
        'x-api-key': ANTHROPIC_KEY,
        'anthropic-version':'2023-06-01',
        'anthropic-dangerous-direct-browser-access':'true',
      },
      body: JSON.stringify({model:'claude-opus-4-6',max_tokens:8000,
        messages:[{role:'user',content:prompt}]})
    });
    const data = await resp.json();
    if(data.error) throw new Error(data.error.message);
    const narrative = (data.content||[]).filter(b=>b.type==='text').map(b=>b.text).join('\\n').trim();
    setStep(3); await new Promise(r=>setTimeout(r,200));

    const formatted = narrative.split('\\n').map(line=>{
      line=line.trim(); if(!line) return '<br>';
      if(line.startsWith('# ')) return `<h2 style="font-size:18px;font-weight:800;color:#3a0012;margin:24px 0 8px;padding-right:14px;border-right:5px solid #c0406a;">${line.slice(2)}</h2>`;
      if(line.startsWith('## ')) return `<h3 style="font-size:15px;font-weight:700;color:#c0406a;margin:14px 0 6px;">${line.slice(3)}</h3>`;
      return `<p style="margin:9px 0;line-height:1.9;font-size:15px;color:#0f172a;font-family:'Noto Naskh Arabic',serif;">${line}</p>`;
    }).join('');

    setStep(4);
    // Wrap in the same report layout as C8.5
    openFullReport(buildTextReportHTML(formatted));

    if(loader) loader.style.display = 'none';
    if(btn){ btn.disabled=false; }

  } catch(err){
    if(loader) loader.style.display = 'none';
    if(btn){ btn.disabled=false; }
    if(reportStatus) reportStatus.textContent = 'خطأ: ' + err.message;
    console.error('[Report]', err);
  }
}

// Open the C8.5 report HTML directly in a full-screen overlay
function openFullReport(htmlContent){
  const existing = $('rpt-overlay');
  if(existing) existing.remove();
  const ov = document.createElement('div');
  ov.id = 'rpt-overlay';
  ov.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:999999;background:#f0f4f8;overflow-y:auto;direction:rtl;';
  // Close button bar at top
  const bar = document.createElement('div');
  bar.style.cssText = 'position:sticky;top:0;z-index:10;background:linear-gradient(135deg,#3a0012,#7a0028);color:#fff;padding:8px 24px;display:flex;justify-content:flex-start;align-items:center;gap:12px;box-shadow:0 2px 12px rgba(0,0,0,.3);';
  bar.innerHTML = `
    <button onclick="document.getElementById('rpt-overlay').remove();var b=$('generate-report-btn');if(b)b.disabled=false;"
      style="background:#c0406a;border:none;color:#fff;padding:6px 16px;border-radius:5px;cursor:pointer;font-size:13px;font-weight:700;font-family:'Noto Naskh Arabic',serif;">
      × إغلاق
    </button>
    <button onclick="window.print()"
      style="background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;padding:6px 14px;border-radius:5px;cursor:pointer;font-size:12px;font-family:'Noto Naskh Arabic',serif;">
      🖨 طباعة / PDF
    </button>
    <span style="font-size:13px;font-weight:700;font-family:'Noto Naskh Arabic',serif;">التقرير التحليلي الشامل</span>`;
  ov.appendChild(bar);
  // Report content
  const wrap = document.createElement('div');
  wrap.innerHTML = htmlContent;
  ov.appendChild(wrap);
  document.body.appendChild(ov);
  ov.scrollTop = 0;
}

// Build a simple text report layout (fallback when C8.5 not run)
function buildTextReportHTML(narrative){
  const evs = Array.isArray(WAR_EVENTS)?WAR_EVENTS:[];
  const ea = ESCALATION_ANALYSIS||{};
  const cp = CONFLICT_PREDICTION||{};
  const mt = MARITIME_THREAT||{};
  const dailyData = _buildDailyContext();
  const totalAir = dailyData.reduce((s,d)=>s+d.airstrikes,0);
  return `<div style="max-width:900px;margin:0 auto;padding:24px;font-family:'Noto Naskh Arabic',serif;direction:rtl;">
    <div style="background:linear-gradient(150deg,#3a0012,#7a0028);color:#fff;border-radius:10px;padding:24px;margin-bottom:20px;">
      <div style="font-size:22px;font-weight:700;margin-bottom:6px;">📊 التقرير التحليلي الشامل</div>
      <div style="font-size:12px;opacity:.65;">منظومة الدمج الاستخباري · اليوم ${_war_day_num} · ${new Date().toLocaleDateString('ar-SA')}</div>
      <div style="font-size:9px;color:rgba(255,255,255,.5);margin-top:8px;">★ الأرقام منذ بداية الحرب</div>
      <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;background:rgba(0,0,0,.2);border-radius:8px;padding:12px;margin-top:12px;">
        ${[['إجمالي الأحداث',evs.length],['الغارات الجوية',totalAir],['القتلى',ea.total_killed||0],
           ['درجة الخطر',(cp.score||'—')+'/100'],['هجمات سفن',mt.vessel_attacks||0]]
          .map(([l,v])=>`<div style="text-align:center;"><div style="font-size:17px;font-weight:700;">${v}</div><div style="font-size:9px;opacity:.5;">${l}</div></div>`).join('')}
      </div>
    </div>
    ${narrative}
  </div>`;
}

// ── Build inline daily events chart (SVG) ─────────────────────────
function _buildDailyChart(dailyData, type, color, label){
  if(!dailyData.length) return '';
  const vals = dailyData.map(d=> type==='total' ? d.total : type==='air' ? d.airstrikes : d.strikes);
  const maxV = Math.max(...vals, 1);
  const W=800, H=120, PAD=30, barW=Math.max(1,(W-PAD*2)/vals.length-1);
  const bars = vals.map((v,i)=>{
    const h = Math.round((v/maxV)*(H-20));
    const x = PAD + i*(barW+1);
    const y = H-h-15;
    const day = dailyData[i].day;
    return `<rect x="${x}" y="${y}" width="${barW}" height="${h}" fill="${color}" opacity="0.8" rx="1">
      <title>اليوم ${day}: ${v}</title></rect>
      ${day%7===1?`<text x="${x+barW/2}" y="${H-2}" text-anchor="middle" font-size="8" fill="#888">D${day}</text>`:''}`;
  }).join('');
  return `<div style="margin:12px 0;">
    <div style="font-size:11px;font-weight:700;color:#666;margin-bottom:4px;direction:rtl;">${label}</div>
    <svg viewBox="0 0 ${W} ${H}" style="width:100%;height:${H}px;overflow:visible;">
      <line x1="${PAD}" y1="${H-15}" x2="${W-PAD}" y2="${H-15}" stroke="#ddd" stroke-width="1"/>
      ${bars}
    </svg>
  </div>`;
}

// ── Build inline jamming trend chart ──────────────────────────────
function _buildJamChart(){
  const history = (GPSJAM_DATA&&GPSJAM_DATA.history)||[];
  if(!history.length) return '';
  const vals = history.map(h=>Math.round((h.me_avg||0)*100));
  const maxV = Math.max(...vals, 1);
  const W=800, H=80, PAD=30;
  const barW = Math.max(1,(W-PAD*2)/vals.length-1);
  const bars = vals.map((v,i)=>{
    const h = Math.round((v/maxV)*(H-15));
    const x = PAD + i*(barW+1);
    const col = v>60?'#ff1144':v>30?'#ff8800':'#ffcc44';
    return `<rect x="${x}" y="${H-h-5}" width="${barW}" height="${h}" fill="${col}" opacity="0.85" rx="1">
      <title>${(history[i].date||'').slice(5)}: ${v}%</title></rect>`;
  }).join('');
  return `<div style="margin:12px 0;">
    <div style="font-size:11px;font-weight:700;color:#666;margin-bottom:4px;direction:rtl;">متوسط تشويش GPS يومياً (%)</div>
    <svg viewBox="0 0 ${W} ${H}" style="width:100%;height:${H}px;">
      <line x1="${PAD}" y1="${H-5}" x2="${W-PAD}" y2="${H-5}" stroke="#ddd" stroke-width="1"/>
      ${bars}
    </svg>
  </div>`;
}

function openReportOverlay(htmlContent, rawText){
  const existing = $('rpt-overlay');
  if(existing) existing.remove();

  const ov = document.createElement('div');
  ov.id = 'rpt-overlay';
  ov.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:999999;background:#f5f0f2;overflow-y:auto;direction:rtl;';

  // ── Topbar ──────────────────────────────────────────────────────
  const bar = document.createElement('div');
  bar.style.cssText = 'position:sticky;top:0;z-index:10;background:linear-gradient(135deg,var(--burg-800),var(--burg-600));color:#fff;padding:10px 24px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 12px rgba(0,0,0,.3);';
  bar.innerHTML = `
    <div style="display:flex;align-items:center;gap:10px;">
      <span style="font-size:18px;">🔍</span>
      <div>
        <div style="font-family:'Noto Naskh Arabic',serif;font-size:15px;font-weight:900;">
          التقرير التحليلي الشامل
        </div>
        <div style="font-size:11px;color:rgba(255,255,255,.7);">
          منظومة الدمج الاستخباري · اليوم ${_war_day_num} · ${new Date().toLocaleDateString('ar-SA')}
        </div>
      </div>
    </div>
    <div style="display:flex;gap:8px;">
      <button onclick="window.print()"
        style="background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;padding:6px 14px;border-radius:5px;cursor:pointer;font-size:12px;font-family:'Noto Naskh Arabic',serif;">
        🖨 طباعة / PDF
      </button>
      <button onclick="document.getElementById('rpt-overlay').remove();var b=$('generate-report-btn');if(b)b.disabled=false;"
        style="background:#c0406a;border:none;color:#fff;padding:6px 16px;border-radius:5px;cursor:pointer;font-size:13px;font-weight:700;font-family:'Noto Naskh Arabic',serif;">
        × إغلاق
      </button>
    </div>`;
  ov.appendChild(bar);

  // ── Stats strip — clearly labeled as "منذ بداية الحرب" ─────────
  const evs = Array.isArray(WAR_EVENTS) ? WAR_EVENTS : [];
  const ea = ESCALATION_ANALYSIS||{};
  const mt = MARITIME_THREAT||{};
  const cp = CONFLICT_PREDICTION||{};
  const totalKilled = ea.total_killed||0;
  const airCount = evs.filter(e=>(e.category||e.type||'').toLowerCase().includes('air')).length;

  const statsBar = document.createElement('div');
  statsBar.style.cssText = 'background:#fff;border-bottom:2px solid var(--burg-200);padding:4px 24px 0;';
  statsBar.innerHTML = `
    <div style="font-size:10px;color:var(--text-muted);padding:4px 0 2px;direction:rtl;letter-spacing:.5px;font-weight:700;">
      إحصائيات منذ بداية الحرب (اليوم 1 → اليوم ${_war_day_num})
    </div>
    <div style="display:flex;flex-wrap:wrap;">
      ${[
        ['إجمالي الأحداث الموثقة', evs.length, '#7a0028'],
        ['الغارات الجوية', airCount, '#b80038'],
        ['الضحايا المسجلة', totalKilled, '#cc0020'],
        ['مستوى الخطر', `${cp.score||'—'}/100`, cp.level==='critical'?'#cc0020':cp.level==='high'?'#cc6600':'#557700'],
        ['اتجاه التصعيد', ea.trend==='escalating'?'📈 تصاعدي':ea.trend==='de-escalating'?'📉 تراجعي':'➡ مستقر', '#7a0028'],
        ['هجمات السفن', mt.vessel_attacks||0, '#0055aa'],
      ].map(([lbl,val,col])=>`
        <div style="padding:8px 16px 10px;border-left:1px solid var(--ui-border2);flex:1;min-width:110px;">
          <div style="font-size:10px;color:var(--text-muted);direction:rtl;margin-bottom:2px;">${lbl}</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700;color:${col};">${val}</div>
        </div>`).join('')}
    </div>`;
  ov.appendChild(statsBar);

  // ── Inline data charts ─────────────────────────────────────────
  const dailyData = _buildDailyContext();
  const chartsDiv = document.createElement('div');
  chartsDiv.style.cssText = 'max-width:900px;margin:0 auto;padding:16px 24px 0;';
  chartsDiv.innerHTML = `
    <div style="font-family:'Noto Naskh Arabic',serif;font-size:14px;font-weight:800;color:var(--burg-700);
                margin-bottom:10px;padding-bottom:5px;border-bottom:2px solid var(--burg-200);">
      📊 البيانات الإحصائية — يومياً منذ بداية الحرب
    </div>
    ${_buildDailyChart(dailyData,'total','#b80038','إجمالي الأحداث اليومية')}
    ${_buildDailyChart(dailyData,'air','#ff4400','الغارات الجوية اليومية')}
    ${_buildJamChart()}
    <div style="display:flex;gap:16px;margin-top:4px;font-size:10px;color:var(--text-muted);direction:rtl;">
      <span style="display:flex;align-items:center;gap:4px;"><span style="display:inline-block;width:10px;height:10px;background:#b80038;border-radius:1px;"></span>إجمالي الأحداث</span>
      <span style="display:flex;align-items:center;gap:4px;"><span style="display:inline-block;width:10px;height:10px;background:#ff4400;border-radius:1px;"></span>غارات جوية</span>
      <span style="display:flex;align-items:center;gap:4px;"><span style="display:inline-block;width:10px;height:10px;background:#ff1144;border-radius:1px;"></span>تشويش GPS (أحمر=عالٍ)</span>
    </div>`;
  ov.appendChild(chartsDiv);

  // ── Report narrative ───────────────────────────────────────────
  const content = document.createElement('div');
  content.style.cssText = 'max-width:900px;margin:0 auto;padding:24px;';
  content.innerHTML = htmlContent || `<div style="text-align:center;padding:60px;color:var(--text-muted);"><div style="font-size:40px;margin-bottom:16px;">🔍</div><div>لا يوجد محتوى للتقرير</div></div>`;
  ov.appendChild(content);

  document.body.appendChild(ov);
  ov.scrollTop = 0;
}

// ══════════════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════════════
window.addEventListener('load', function(){
  setTimeout(()=>{
    try{ tlBuildAxis(); tlBuildCanvas(); }catch(e){ console.warn('tl init:', e); }
  }, 500);

  const wd = $('war-day-badge');
  if(wd) wd.textContent = 'اليوم ' + _war_day_num;
  const ws = $('an-war-day');
  if(ws) ws.textContent = _war_day_num;

  function tick(){
    const now = new Date();
    const cl = $('clock');
    if(cl) cl.textContent = now.toUTCString().slice(17,25) + ' UTC';
    const tc = $('topbar-clock');
    if(tc) tc.textContent = now.toUTCString().slice(17,25) + ' UTC';
    const td = $('topbar-date');
    if(td) td.textContent = now.toLocaleDateString('ar-SA');
  }
  tick(); setInterval(tick, 1000);
});

""" + """</script>
</body>
</html>""")

# ── FINAL ASSEMBLY ────────────────────────────────────────────────
HTML_TEMPLATE = _P1 + _P2 + _P3 + _P4

print(f"✓ HTML_TEMPLATE assembled — {len(HTML_TEMPLATE):,} characters")
print(f"  Part 1: {len(_P1):,}  Part 2: {len(_P2):,}  Part 3: {len(_P3):,}  Part 4: {len(_P4):,}")
print("\n  Run Cell 18 next to build the HTML file")

######################################################################
# ► NEXT CELL: Cell 18 — Build HTML
######################################################################