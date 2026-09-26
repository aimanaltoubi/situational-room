# c17_html_js.py
# HTML Part 3: JavaScript
# Auto-extracted from Cell 17

_P3 = ("""

<script>
const CESIUM_TOKEN  = '__TOKEN__';
const GEMINI_KEY    = '__GEMINI_KEY__';
const _war_day_num  = __WAR_DAY__;
const SAT_DATA      = __SAT_JSON__;
const JAM_DATA      = __JAM_JSON__;
const GPSJAM_DATA   = __GPSJAM_JSON__;
const FLIGHT_DATA   = __FLIGHT_JSON__;
const INTEL_DATA    = __INTEL_JSON__;
const WAR_EVENTS    = __WAR_JSON__;
const HIST_SAT_DATA = __HIST_SAT_JSON__;
const TELEGRAM_DATA = __TELEGRAM_JSON__;
const MARINE_DATA   = __MARINE_JSON__;
const ATTACKED_VESSELS     = __ATTACKED_JSON__;
const ESCALATION_ANALYSIS  = __ESCALATION_JSON__;
const ISR_CUEING           = __ISR_CUEING_JSON__;
const ATTACK_PATTERNS      = __ATTACK_PATTERNS_JSON__;

const POLITICAL_ANALYSIS  = __POLITICAL_JSON__;
const DIPLOMATIC_INDEX    = __DIPLOMATIC_JSON__;
const MARITIME_THREAT     = __MARITIME_JSON__;
const JAMMING_CORRELATION = __JAM_CORR_JSON__;
const VIP_INTELLIGENCE    = __VIP_JSON__;
const CONFLICT_PREDICTION = __PREDICTION_JSON__;
const FLIGHT_HIST_DATA    = __FLIGHT_HIST_JSON__;

const SATELLITES    = SAT_DATA.satellites || [];
const SAT_CATS      = SAT_DATA.cats || {};
const $ = id => document.getElementById(id);
</""" + """script>

<script>
// Attacked vessels state — declared here so IIFE can safely reference them
var _attackedEntities = [];
var _attackedVisible  = false;
var _attackedRoutes   = [];

const CAT_COLOR={spy:'#ffd700',military:'#ff6b35',starlink:'#7ec8a0',oneweb:'#90caf9',leo:'#a0c4ff',geo:'#d4b8e0'};
const layerOn={spy:true,military:true,starlink:false,oneweb:false,leo:false,geo:false};

function makeSatIcon(body,panel,glow,sz){
  const svg=`<svg xmlns='http://www.w3.org/2000/svg' width='${sz}' height='${sz}' viewBox='0 0 48 48'>`+
    `<defs><filter id='g'><feGaussianBlur stdDeviation='2' result='b'/>`+
    `<feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge></filter></defs>`+
    `<rect x='2' y='20' width='12' height='8' rx='1' fill='${panel}' opacity='.9' filter='url(#g)'/>`+
    `<rect x='14' y='23' width='5' height='2' fill='${body}' opacity='.8'/>`+
    `<rect x='19' y='17' width='10' height='14' rx='2' fill='${body}' filter='url(#g)'/>`+
    `<line x1='24' y1='11' x2='24' y2='17' stroke='${glow}' stroke-width='1.2' opacity='.9'/>`+
    `<circle cx='24' cy='10' r='2' fill='${glow}' opacity='.9'/>`+
    `<rect x='29' y='23' width='5' height='2' fill='${body}' opacity='.8'/>`+
    `<rect x='34' y='20' width='12' height='8' rx='1' fill='${panel}' opacity='.9' filter='url(#g)'/>`+
    `</svg>`;
  return 'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);}
const SAT_ICONS={
  spy:makeSatIcon('#b08000','#1a3668','#ffd700',52),
  military:makeSatIcon('#7a1a00','#2a1008','#ff6b35',44),
  starlink:makeSatIcon('#1a4228','#0d2418','#7ec8a0',30),
  oneweb:makeSatIcon('#0d2444','#0a1428','#90caf9',30),
  leo:makeSatIcon('#1a2840','#0d1828','#a0c4ff',26),
  geo:makeSatIcon('#28183a','#180d28','#d4b8e0',24),
};
var SAT_SCALE={};
function initSatScale(){SAT_SCALE={
  spy:new Cesium.NearFarScalar(5e5,1.6,2e7,0.55),
  military:new Cesium.NearFarScalar(5e5,1.3,2e7,0.45),
  starlink:new Cesium.NearFarScalar(5e5,1.0,2e7,0.35),
  oneweb:new Cesium.NearFarScalar(5e5,1.0,2e7,0.35),
  leo:new Cesium.NearFarScalar(5e5,0.9,2e7,0.30),
  geo:new Cesium.NearFarScalar(5e5,0.8,2e7,0.28),
};}

function setMsg(m,p){$('ld-msg').textContent=m;if(p!==undefined)$('pb').style.width=p+'%';}
function hideLoader(){const l=$('loader');l.style.transition='opacity .6s';l.style.opacity=0;setTimeout(()=>{l.remove();if(viewer){try{viewer.resize();viewer.scene.requestRender();}catch(e){}}},700);}
window.addEventListener('resize',function(){if(viewer){try{viewer.resize();viewer.scene.requestRender();}catch(e){}}});


var viewer,satEntities={},labelLayer=null,currentMode='satellite';
const ESRI={
  satellite:'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer',
  topo:'https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer',
  darkCanvas:'https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer',
  refLight:'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer',
  refDark:'https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer',
};
async function esriLayer(url){return await Cesium.ArcGisMapServerImageryProvider.fromUrl(url);}
async function applyMode(mode){
  if(!viewer)return;viewer.imageryLayers.removeAll();labelLayer=null;
  try{
    if(mode==='satellite'){const b=await Cesium.IonImageryProvider.fromAssetId(2);viewer.imageryLayers.addImageryProvider(b);const r=await esriLayer(ESRI.refLight);labelLayer=viewer.imageryLayers.addImageryProvider(r);labelLayer.alpha=0.85;}
    else if(mode==='night'){const b=await esriLayer(ESRI.darkCanvas);viewer.imageryLayers.addImageryProvider(b);const r=await esriLayer(ESRI.refDark);labelLayer=viewer.imageryLayers.addImageryProvider(r);labelLayer.alpha=1.0;viewer.scene.globe.enableLighting=true;}
    else if(mode==='natural'){const b=await esriLayer(ESRI.topo);viewer.imageryLayers.addImageryProvider(b);}
    else if(mode==='terrain'){const b=await Cesium.IonImageryProvider.fromAssetId(2);viewer.imageryLayers.addImageryProvider(b);viewer.imageryLayers.get(0).brightness=0.85;viewer.imageryLayers.get(0).contrast=1.3;viewer.imageryLayers.get(0).saturation=0.5;const r=await esriLayer(ESRI.refLight);labelLayer=viewer.imageryLayers.addImageryProvider(r);labelLayer.alpha=0.9;}
  }catch(e){console.error('applyMode',e);}
}
async function setMode(el,mode){document.querySelectorAll('.mode-btn').forEach(b=>b.classList.remove('active'));el.classList.add('active');currentMode=mode;await applyMode(mode);}

function topSyncChip(id,state){const el=$(id);if(el)el.classList.toggle('active',!!state);}
function topToggleSatellites(){const anyOn=layerOn.spy||layerOn.military;['spy','military'].forEach(cat=>{layerOn[cat]=!anyOn;const t=$('lt-'+cat);if(t){t.classList.toggle('on',layerOn[cat]);t.classList.toggle('off',!layerOn[cat]);}});topSyncChip('lchip-sat',layerOn.spy);propagateAndRender(true);}
function topToggleBases(){const chip=$('lchip-bases'),anyOn=chip&&chip.classList.contains('active');topSyncChip('lchip-bases',!anyOn);['nuclear','usbase','chokepoint','city'].forEach(t=>{const tog=$('lt-'+t);if(tog){tog.classList.toggle('on',!anyOn);tog.classList.toggle('off',anyOn);}});if(!anyOn)renderAllIntel();else clearAllIntel();}

function showDayBrief(indices,dayNum){
  const card=$('war-brief-card');if(!card)return;
  const $id=$('wbc-id');if($id)$id.textContent='\u0627\u0644\u064a\u0648\u0645 '+dayNum;
  const $time=$('wbc-time');if($time)$time.textContent=indices.length+' \u062d\u062f\u062b \u0645\u0633\u062c\u0651\u0644';
  const $tl=$('wbc-type-label');if($tl)$tl.textContent='\u062c\u062f\u0648\u0644 \u0627\u0644\u0623\u062d\u062f\u0627\u062b';
  const $title=$('wbc-title');if($title)$title.textContent='\u0623\u062d\u062f\u0627\u062b \u0627\u0644\u064a\u0648\u0645 '+dayNum;
  const $detail=$('wbc-detail');
  if($detail){
    $detail.style.maxHeight='180px';$detail.style.overflowY='auto';
    $detail.style.padding='0';$detail.style.borderLeft='none';
    $detail.innerHTML=indices.map(i=>{
      const e=WEVS[i];if(!e)return'';
      const c=e.col||'#ff8800';
      const t=(e.t||e.date||'').slice(11,16)||'';
      const desc=(e.detail||e.label||'').slice(0,80);
      const loc=e.location||'';
      return '<div onclick="warSeekTo('+i+',true)" style="padding:6px 8px;border-bottom:1px solid #f0e0e8;cursor:pointer;display:flex;gap:8px;align-items:flex-start;">'
        +'<span style="font-family:JetBrains Mono,monospace;font-size:9px;color:'+c+';flex-shrink:0;padding-top:2px;min-width:34px">'+t+'</span>'
        +'<div style="flex:1;min-width:0"><div style="font-size:10px;font-weight:600;color:#3a0016;line-height:1.4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+desc+'</div>'
        +(loc?'<div style="font-size:8px;color:#888;margin-top:1px">&#128205; '+loc+'</div>':'')
        +'</div></div>';
    }).join('');
  }
  const $meta=$('wbc-meta');
  if($meta)$meta.innerHTML='<span class="wbc-chip">&#128197; <b>'+indices.length+'</b> \u062d\u062f\u062b</span>';
  card.classList.add('visible');
}


function showDayBrief(indices,dayNum){const card=$('war-brief-card');if(!card)return;const _s=(id,val)=>{const el=$(id);if(el)el.textContent=val;};_s('wbc-id','اليوم '+dayNum);_s('wbc-time',indices.length+' حدث مسجّل');_s('wbc-type-label','جدول الأحداث');_s('wbc-title','أحداث اليوم '+dayNum);const $det=$('wbc-detail');if($det){$det.style.maxHeight='180px';$det.style.overflowY='auto';$det.style.padding='0';$det.style.borderLeft='none';$det.innerHTML=indices.map(i=>{const e=WEVS[i];if(!e)return'';const c=e.col||'#888888';const t=(e.t||e.date||'').slice(11,16)||'';const desc=(e.detail||e.label||'').slice(0,80);const loc=e.location||'';return '<div onclick="warSeekTo('+i+',true)" style="padding:6px 8px;border-bottom:1px solid #f0e0e8;cursor:pointer;display:flex;gap:8px;align-items:flex-start;">'+'<span style="font-family:JetBrains Mono,monospace;font-size:9px;color:'+c+';flex-shrink:0;padding-top:2px;min-width:34px">'+t+'</span>'+'<div style="flex:1;min-width:0"><div style="font-size:10px;font-weight:600;color:#3a0016;line-height:1.4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'+desc+'</div>'+(loc?'<div style="font-size:8px;color:#888;margin-top:1px">&#128205; '+loc+'</div>':'')+'</div></div>';}).join('');}const $meta=$('wbc-meta');if($meta)$meta.innerHTML='<span class="wbc-chip">&#128197; <b>'+indices.length+'</b> حدث</span>';card.classList.add('visible');}

function showJamBrief(hotspot,day){const card=$('war-brief-card');if(!card)return;const col='#ff1111';const _s=(id,val)=>{const el=$(id);if(el)el.textContent=val;};_s('wbc-id','J'+String(day.dayNum).padStart(4,'0'));_s('wbc-time',day.date);const dot=$('wbc-type-dot');if(dot){dot.style.width='8px';dot.style.height='8px';dot.style.borderRadius='50%';dot.style.flexShrink='0';dot.style.background=col;}_s('wbc-type-label','GPS JAMMING');_s('wbc-title',hotspot.label||('تشويش GPS في '+hotspot.lat.toFixed(1)+'° / '+hotspot.lon.toFixed(1)+'°'));const $det=$('wbc-detail');if($det){$det.style.maxHeight='';$det.style.overflowY='';$det.style.padding='';$det.style.borderLeft='';$det.textContent='شدة: '+Math.round((hotspot.intensity||0)*100)+'% | D'+day.dayNum+' | '+hotspot.lat.toFixed(2)+'°, '+hotspot.lon.toFixed(2)+'°';}const $meta=$('wbc-meta');if($meta)$meta.innerHTML='<span class="wbc-chip" style="border-color:#ff1111;color:#ff1111">GPS '+Math.round((hotspot.intensity||0)*100)+'% تشويش</span>';card.style.borderLeftColor=col;card.classList.add('visible');const fill=$('wbc-progress-fill');if(fill){fill.style.transition='none';fill.style.width='100%';fill.getBoundingClientRect();fill.style.transition='width 10s linear';fill.style.width='0%';}clearTimeout(window._wbcTimer);window._wbcTimer=setTimeout(closeWarBrief,10000);}

var jamTlOn=false;function buildJamDailyData(){const WAR_START=new Date('2026-02-28').getTime();const today=new Date();today.setUTCHours(0,0,0,0);const days=[];let d=new Date(WAR_START);const hist=(GPSJAM_DATA&&GPSJAM_DATA.history)||[];while(d<=today){const ds=d.toISOString().slice(0,10);const hEntry=hist.find(h=>h.date===ds);const dayNum=Math.round((d.getTime()-WAR_START)/86400000)+1;let intensity;if(hEntry){intensity=hEntry.me_avg||hEntry.top_intensity||0;}else{const base=Math.max(0.3,0.92-(dayNum-1)*0.018);const spike=[1,2,4,7,11,13].includes(dayNum)?0.12:0;intensity=Math.min(0.98,base+spike+(Math.sin(dayNum*0.7)*0.05));}days.push({date:ds,dayNum,intensity:Math.max(0,intensity)});d.setUTCDate(d.getUTCDate()+1);}return days;}

const JAM_DAY_MAP={1:{lat:26.5,lon:56.5,intensity:0.95,label:'مضيق هرمز'},2:{lat:26.22,lon:50.59,intensity:0.88,label:'البحرين'},3:{lat:35.69,lon:51.39,intensity:0.93,label:'طهران'},4:{lat:26.5,lon:56.5,intensity:0.92,label:'مضيق هرمز'},5:{lat:6.03,lon:80.22,intensity:0.85,label:'جالي - سريلانكا'},6:{lat:39.21,lon:45.41,intensity:0.75,label:'نخجيفان'},7:{lat:25.12,lon:51.31,intensity:0.88,label:'قاعدة العديد'},8:{lat:29.04,lon:48.17,intensity:0.90,label:'ميناء شعيبة'},9:{lat:33.49,lon:48.35,intensity:0.82,label:'فلك الأفلاك'},10:{lat:26.27,lon:50.65,intensity:0.88,label:'مطار البحرين'},11:{lat:26.5,lon:56.5,intensity:0.95,label:'مضيق هرمز'},12:{lat:33.34,lon:44.40,intensity:0.80,label:'بغداد'},13:{lat:29.25,lon:50.32,intensity:0.92,label:'جزيرة خارك'},14:{lat:32.66,lon:51.68,intensity:0.88,label:'أصفهان'},15:{lat:27.09,lon:57.08,intensity:0.85,label:'ميناء ميناب'},16:{lat:25.20,lon:55.27,intensity:0.82,label:'مطار دبي'},17:{lat:24.34,lon:56.74,intensity:0.80,label:'صحار - عمان'}};

function buildJamTimeline(){const canvas=$('tl-jam-canvas'),density=$('tl-jam-density');if(!canvas||!density)return;density.innerHTML='';const days=buildJamDailyData();if(!days.length)return;const n=days.length;const maxI=Math.max(...days.map(d=>d.intensity),0.01);const WAR_START=new Date('2026-02-28').getTime();const WAR_END=new Date(days[days.length-1].date).getTime();const span=Math.max(WAR_END-WAR_START,86400000);days.forEach((day)=>{const t=new Date(day.date).getTime();const pct=((t-WAR_START)/span)*94+3;const hp=Math.max(4,Math.round((day.intensity/maxI)*40));const alpha=0.4+0.55*(day.intensity/maxI);const r=day.intensity>0.7?Math.round(30+200*day.intensity):Math.round(day.intensity*60);const g2=day.intensity<0.5?Math.round(150+50*day.intensity):Math.round(180-100*(day.intensity-0.5));const bar=document.createElement('div');bar.className='jam-bar';bar.style.cssText='left:'+pct.toFixed(2)+'%;width:'+Math.max(0.8,(94/n)).toFixed(2)+'%;height:'+hp+'px;background:rgba('+r+','+g2+',40,'+alpha.toFixed(2)+')';bar.title='D'+day.dayNum+' ('+day.date+'): '+Math.round(day.intensity*100)+'% تشويش';bar.addEventListener('click',()=>{const cur=$('jam-cursor');if(cur)cur.style.left=pct.toFixed(2)+'%';const td=$('jam-time-display');if(td)td.textContent=day.date;const id=$('jam-intensity-display');if(id)id.textContent='D'+day.dayNum+' — '+Math.round(day.intensity*100)+'%';const mapped=JAM_DAY_MAP[day.dayNum];const cells=(GPSJAM_DATA&&GPSJAM_DATA.cells)||[];let top;if(mapped){const found=cells.find(c=>Math.abs(c.lat-mapped.lat)<0.5&&Math.abs(c.lon-mapped.lon)<0.5);top=found||mapped;if(!top.label)top.label=mapped.label;}else{const sorted=cells.slice().sort((a,b)=>(b.intensity||0)-(a.intensity||0));top=sorted[day.dayNum%Math.max(sorted.length,1)]||sorted[0];}if(!top||!viewer)return;clearJamming();jammingOn=true;const tog=$('lt-jam-tl');if(tog){tog.classList.add('on');tog.classList.remove('off');}const jalpha=Math.min(0.40+top.intensity*0.55,0.95);const jcol=Cesium.Color.fromCssColorString('#ff1111').withAlpha(jalpha);const radius=50000+top.intensity*130000;const ent=viewer.entities.add({name:top.label||'GPS Jamming',position:Cesium.Cartesian3.fromDegrees(top.lon,top.lat,500),point:{pixelSize:Math.round(10+top.intensity*14),color:jcol,outlineColor:Cesium.Color.WHITE.withAlpha(0.85),outlineWidth:1.5,disableDepthTestDistance:Number.POSITIVE_INFINITY,scaleByDistance:new Cesium.NearFarScalar(5e5,1.4,2e7,0.5)},ellipse:{semiMajorAxis:radius,semiMinorAxis:radius,height:0,material:new Cesium.ColorMaterialProperty(Cesium.Color.fromCssColorString('#ff1111').withAlpha(0.07)),outline:true,outlineColor:Cesium.Color.fromCssColorString('#ff1111').withAlpha(0.45),outlineWidth:1}});ent._jamLat=top.lat;ent._jamLon=top.lon;ent._jamData=top;jamEntities.push(ent);showJamBrief(top,day);viewer.camera.cancelFlight();viewer.camera.flyTo({destination:Cesium.Cartesian3.fromDegrees(top.lon,top.lat,500000),duration:1.5,easingFunction:Cesium.EasingFunction.CUBIC_IN_OUT});});density.appendChild(bar);if(day.dayNum%3===1||day.dayNum===1){const line=document.createElement('div');line.className='jam-day-line';line.style.left=pct.toFixed(2)+'%';density.appendChild(line);const lbl2=document.createElement('div');lbl2.className='jam-day-lbl';lbl2.style.left=pct.toFixed(2)+'%';lbl2.textContent='D'+day.dayNum;density.appendChild(lbl2);}});}

function toggleJamTimeline(){jamTlOn=!jamTlOn;const tog=$('lt-jam-tl'),label=$('jam-toggle-label'),canvas=$('tl-jam-canvas');if(tog){tog.classList.toggle('on',jamTlOn);tog.classList.toggle('off',!jamTlOn);}if(label)label.textContent=jamTlOn?'GPS جدول تشويش ✓':'GPS جدول تشويش';if(canvas)canvas.style.display=jamTlOn?'block':'none';if(jamTlOn){buildJamTimeline();const td=$('jam-time-display');if(td)td.textContent='منذ 28 فبراير 2026';if(!jammingOn)toggleJamming();}else{const td=$('jam-time-display');if(td)td.textContent='التشويش متوقف';const id=$('jam-intensity-display');if(id)id.textContent='';}}
function toggleBtEventList(){const el=$('war-event-list'),btn=$('bt-event-list-btn');if(!el)return;const open=el.style.display==='block';el.style.display=open?'none':'block';if(btn)btn.textContent=open?'أحداث ▲':'أحداث ▼';}

var currentView='sa';
function switchView(view){
  if(view===currentView)return;
  currentView=view;
  const isSA=view==='sa';
  $('vsw-sa').classList.toggle('active',isSA);$('vsw-analytics').classList.toggle('active',!isSA);
  ['left-panel','right-panel','bottombar'].forEach(id=>{const el=$(id);if(el)el.style.display=isSA?'':'none';});
  const g=$('globe');if(g){g.style.visibility=isSA?'visible':'hidden';g.style.pointerEvents=isSA?'':'none';}
  const layers=$('topbar-layers');if(layers){layers.style.visibility=isSA?'visible':'hidden';layers.style.pointerEvents=isSA?'':'none';}
  const an=$('analytics-view');if(an)an.style.display=isSA?'none':'block';
  if(isSA&&viewer){setTimeout(()=>{try{viewer.resize();viewer.scene.requestRender();}catch(e){}},50);}
  if(!isSA){initAnalytics();try{populateAnalytics();}catch(e){}}
  if(!isSA&&typeof warStop==='function')warStop();}

(async()=>{
  if(typeof Cesium==='undefined'){setMsg('ERROR: Cesium CDN failed');return;}
  if(typeof satellite==='undefined'){setMsg('ERROR: satellite.js CDN failed');return;}
  try{
    Cesium.Ion.defaultAccessToken=CESIUM_TOKEN;initSatScale();
    setMsg('\u0625\u0646\u0634\u0627\u0621 \u0627\u0644\u0643\u0631\u0629 \u0627\u0644\u0623\u0631\u0636\u064a\u0629\u2026',15);
    viewer=new Cesium.Viewer('globe',{sceneMode:Cesium.SceneMode.SCENE3D,baseLayerPicker:false,geocoder:false,homeButton:false,sceneModePicker:false,navigationHelpButton:false,animation:false,timeline:false,fullscreenButton:false,infoBox:false,selectionIndicator:false});
    viewer.scene.globe.enableLighting=true;viewer.scene.fog.enabled=true;viewer.scene.fog.density=0.0002;viewer.scene.backgroundColor=Cesium.Color.BLACK;
    
    setMsg('\u062a\u062d\u0645\u064a\u0644 \u0627\u0644\u0635\u0648\u0631\u2026',30);await applyMode('satellite');
    viewer.camera.setView({destination:Cesium.Cartesian3.fromDegrees(50,20,19000000),orientation:{heading:0,pitch:Cesium.Math.toRadians(-90),roll:0}});
    setMsg('\u062d\u0633\u0627\u0628 \u0627\u0644\u0645\u062f\u0627\u0631\u0627\u062a\u2026',60);
    initBadges();propagateAndRender();initControls();renderBriefingFeed();
    // Auto-show war events and jamming on startup
    initWarTimeline();warOn=true;renderWarMarkers();
    const _lt=$('lt-war');if(_lt){_lt.classList.add('on');_lt.classList.remove('off');}
    topSyncChip('lchip-war',true);
    jammingOn=true;renderJamming();
    const _lj=$('lt-jam');if(_lj){_lj.classList.add('on');_lj.classList.remove('off');}
    topSyncChip('lchip-jam',true);
    // Attacked vessels shown on demand via button click
    setInterval(propagateAndRender,15000);viewer.screenSpaceEventHandler.
setInputAction(function(click){
    const picked=viewer.scene.pick(click.position);
    if(!Cesium.defined(picked)||!picked.id)return;
    const ent=picked.id;
    // War event click
    if(ent._wevsIdx!=null&&WEVS[ent._wevsIdx]){warSeekTo(ent._wevsIdx,true);return;}
    // Jamming click
    if(ent._jamLat!=null){
      const fakeDay={dayNum:1,date:new Date().toISOString().slice(0,10)};
      showJamBrief(ent._jamData||{lat:ent._jamLat,lon:ent._jamLon,intensity:0.8,label:ent.name||''},fakeDay);
      viewer.camera.cancelFlight();
      viewer.camera.flyTo({destination:Cesium.Cartesian3.fromDegrees(ent._jamLon,ent._jamLat,400000),duration:1.5,easingFunction:Cesium.EasingFunction.CUBIC_IN_OUT});

    // Marine vessel click handler
    viewer.screenSpaceEventHandler.setInputAction(function(click){
      var picked=viewer.scene.pick(click.position);
      if(Cesium.defined(picked)&&picked.id&&picked.id._marineData){
        var v=picked.id._marineData;
        var details=[];
        details.push(['MMSI',v.mmsi||'\u2014']);
        if(v.imo)details.push(['IMO',v.imo]);
        if(v.callsign)details.push(['Callsign',v.callsign]);
        details.push(['Name',v.name||'\u2014']);
        details.push(['Type',v.type_specific||v.type||'\u2014']);
        details.push(['Category',v.category||'\u2014']);
        details.push(['Flag',flagEmoji(v.flag)+' '+v.flag+(v.country_name?' ('+v.country_name+')':'')]);
        if(v.beneficial_owner)details.push(['Owner',v.beneficial_owner]);
        if(v.owner_country)details.push(['Owner Country',v.owner_country]);
        details.push(['Speed',v.speed?v.speed+' kts':'\u2014']);
        if(v.nav_status)details.push(['Status',v.nav_status]);
        details.push(['Destination',v.destination||v.dest||'\u2014']);
        if(v.eta_utc)details.push(['ETA',v.eta_utc.replace('T',' ').slice(0,16)]);
        if(v.length)details.push(['Size',v.length+'m x '+(v.breadth||'?')+'m']);
        if(v.gross_tonnage)details.push(['Gross Tonnage',Number(v.gross_tonnage).toLocaleString()+' GT']);
        if(v.deadweight)details.push(['Deadweight',Number(v.deadweight).toLocaleString()+' DWT']);
        if(v.year_built)details.push(['Built',v.year_built]);
        details.push(['Zone',v.zone_name||v.zone||'\u2014']);
        if(v.going_dark)details.push(['\u26a0 STATUS','DARK - AIS OFF']);
        if(v.sat_e_lat)details.push(['SAT-E',v.sat_e_lat+', '+v.sat_e_lon]);
        var subtitle=(v.category==='military'||v.category==='warship'?'\u2693 ':'')+((v.type_specific||v.type||'VESSEL')).toUpperCase();
        if(v.flag)subtitle+=' \u00b7 '+flagEmoji(v.flag)+' '+v.flag;
        showEntityInfo(v.name||v.mmsi,subtitle,details,v.name+' vessel ship');
      }
    },Cesium.ScreenSpaceEventType.LEFT_CLICK);

    // Marine vessel click handler — show info card when clicking ship on globe
    viewer.screenSpaceEventHandler.setInputAction(function(mv){
      var picked=viewer.scene.pick(mv.position);
      if(!Cesium.defined(picked)||!picked.id||!picked.id._marineData)return;
      var v=picked.id._marineData;
      var details=[];
      details.push(['MMSI',v.mmsi||'\u2014']);
      if(v.imo)details.push(['IMO',v.imo]);
      if(v.callsign)details.push(['Callsign',v.callsign]);
      details.push(['Name',v.name||'\u2014']);
      details.push(['Type',v.type_specific||v.type||'\u2014']);
      details.push(['Flag',flagEmoji(v.flag)+' '+v.flag+(v.country_name?' ('+v.country_name+')':'')]);
      if(v.beneficial_owner)details.push(['Owner',v.beneficial_owner]);
      details.push(['Speed',v.speed?v.speed+' kts':'\u2014']);
      if(v.nav_status)details.push(['Status',v.nav_status]);
      details.push(['Destination',v.destination||v.dest||'\u2014']);
      if(v.length)details.push(['Size',v.length+'m x '+(v.breadth||'?')+'m']);
      if(v.gross_tonnage)details.push(['Tonnage',Number(v.gross_tonnage).toLocaleString()+' GT']);
      if(v.year_built)details.push(['Built',v.year_built]);
      details.push(['Zone',v.zone_name||v.zone||'\u2014']);
      if(v.going_dark)details.push(['\u26a0 STATUS','DARK - AIS OFF']);
      var sub=(v.category==='military'||v.category==='warship'?'\u2693 ':'')+((v.type_specific||v.type||'VESSEL')).toUpperCase();
      showEntityInfo(v.name||v.mmsi,sub,details,v.name+' vessel');
    },Cesium.ScreenSpaceEventType.LEFT_CLICK);
      return;
    }
    // Aircraft click
    if(ent._fltData){
      const a=ent._fltData;
      const col={commercial:'#00d4ff',military:'#ff6b35',cargo:'#ffaa00',private:'#aa88ff',unknown:'#aaaaaa'}[a.ac_type]||'#aaaaaa';
      showEntityInfo(
        (a.callsign||a.icao||'رحلة مجهولة'),
        (a.ac_type||'aircraft').toUpperCase(),
        [
          ['رقم الرحلة', a.callsign||'—'],
          ['ICAO', a.icao||'—'],
          ['النوع', a.ac_type||'—'],
          ['الارتفاع', a.alt_ft ? a.alt_ft.toLocaleString()+' ft' : '—'],
          ['FIR', a.fir_name||a.fir||'—'],
          ['الموقع', (a.lat||'?').toString().slice(0,6)+'° / '+(a.lon||'?').toString().slice(0,6)+'°']
        ],
        (a.callsign||a.icao||'')+' flight'
      );
      return;
    }
    // Marine vessel (AIS) click
    if(ent._marineData){
      const v=ent._marineData;
      showEntityInfo(
        v.name||v.mmsi||'سفينة',
        (v.type||'vessel').toUpperCase()+' · AIS',
        [
          ['الاسم',        v.name||'—'],
          ['MMSI',         v.mmsi||'—'],
          ['IMO',          v.imo||'—'],
          ['العلم',        v.flag||'—'],
          ['النوع',        v.type||'—'],
          ['السرعة',       v.speed!=null ? v.speed+' kts' : '—'],
          ['الوجهة',       v.dest||'—'],
          ['الموقع',       v.lat&&v.lon ? v.lat.toFixed(3)+'° / '+v.lon.toFixed(3)+'°' : '—']
        ],
        (v.name||v.mmsi||'')+' vessel AIS'
      );
      return;
    }
    // Attacked vessel click
    if(ent._avData){ showAttackedBrief(ent._avData); return; }
        // Satellite click
    if(ent._satData){
      const sd=ent._satData;
      const catLabel={spy:'استطلاع',military:'عسكري',starlink:'Starlink',oneweb:'OneWeb',leo:'LEO',geo:'GEO'}[sd.cat]||sd.cat;
      showEntityInfo(
        sd.name,
        catLabel+' · قمر اصطناعي',
        [
          ['الاسم',     sd.name],
          ['NORAD ID',  sd.norad||'—'],
          ['التصنيف',   catLabel],
          ['الارتفاع',  sd.alt ? sd.alt+' km' : '—'],
          ['الموقع',    (sd.lat||'?')+'° / '+(sd.lon||'?')+'°'],
          ['المدار',    sd.alt>20000?'GEO (ثابت)':sd.alt>2000?'MEO':'LEO']
        ],
        sd.name+' satellite NORAD '+sd.norad
      );
      return;
    }
  },Cesium.ScreenSpaceEventType.LEFT_CLICK);
// ── ATTACKED VESSELS LAYER ────────────────────────────────────────
// _attacked* vars moved to top of script

function clearAttackedEntities(){
  (_attackedEntities||[]).forEach(e=>{try{viewer.entities.remove(e);}catch(ex){}});
  (_attackedRoutes||[]).forEach(e=>{try{viewer.entities.remove(e);}catch(ex){}});
  _attackedEntities=[];_attackedRoutes=[];
}

function toggleAttackedVessels(){
  const vessels = (ATTACKED_VESSELS && ATTACKED_VESSELS.vessels)||[];
  if(!_attackedVisible && !vessels.length){
    // No data — show a brief message on the war brief card
    const card=$('war-brief-card');
    if(card){
      const _s=(id,v)=>{const el=$(id);if(el)el.textContent=v;};
      _s('wbc-id','---');
      _s('wbc-type-label','لا توجد بيانات');
      _s('wbc-title','السفن المهاجمة — لا توجد بيانات');
      _s('wbc-detail','يتطلب ملف vessels-attack-dataset.txt في مجلد data/ — راجع README');
      const mm=$('wbc-meta');if(mm)mm.innerHTML='';
      card.classList.add('visible');
      clearTimeout(window._wbcTimer);
      window._wbcTimer=setTimeout(closeWarBrief,4000);
    }
    return;
  }
  _attackedVisible = !_attackedVisible;
  const chip = $('lchip-attacked');
  if(chip) chip.classList.toggle('active', _attackedVisible);
  if(_attackedVisible) renderAttackedVessels();
  else clearAttackedEntities();
}

function renderAttackedVessels(){
  clearAttackedEntities();
  if(!viewer) return;
  const vessels = (ATTACKED_VESSELS && ATTACKED_VESSELS.vessels)||[];
  if(!vessels.length) return;

  vessels.forEach(v=>{
    if(!v.lat||!v.lon) return;
    const col = Cesium.Color.fromCssColorString(v.col||'#ff4400');

    // Strike point — pulsing red ring
    const ring = viewer.entities.add({
      position: Cesium.Cartesian3.fromDegrees(v.lon, v.lat),
      ellipse:{
        semiMajorAxis: 45000,
        semiMinorAxis: 45000,
        material: col.withAlpha(0.18),
        outline: true,
        outlineColor: col.withAlpha(0.8),
        outlineWidth: 2,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
      },
      label:{
        text: '⚠',
        font: '14px sans-serif',
        fillColor: Cesium.Color.WHITE,
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 2,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cesium.Cartesian2(0,-2),
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
      _avData: v,
    });
    _attackedEntities.push(ring);

    // Route line from departure to strike (if known)
    if(v.from_lat && v.from_lon){
      // Departure marker
      const dep = viewer.entities.add({
        position: Cesium.Cartesian3.fromDegrees(v.from_lon, v.from_lat),
        point:{
          pixelSize: 6,
          color: Cesium.Color.fromCssColorString('#00cc88'),
          outlineColor: Cesium.Color.WHITE,
          outlineWidth: 1,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        label:{
          text: v.from_port ? v.from_port.split(',')[0].split('(')[0].trim().substring(0,18) : 'Departure',
          font: '9px monospace',
          fillColor: Cesium.Color.fromCssColorString('#00cc88'),
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 1,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          pixelOffset: new Cesium.Cartesian2(0,-12),
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          show: true,
        },
      });
      _attackedRoutes.push(dep);

      // Route polyline departure → strike
      const route = viewer.entities.add({
        polyline:{
          positions: Cesium.Cartesian3.fromDegreesArray([
            v.from_lon, v.from_lat,
            v.lon, v.lat,
          ]),
          width: 1.5,
          material: new Cesium.PolylineDashMaterialProperty({
            color: col.withAlpha(0.55),
            dashLength: 12,
          }),
          clampToGround: true,
        },
      });
      _attackedRoutes.push(route);
    }
  });

  console.log('[AttackedVessels] rendered', vessels.length, 'vessels');
}

function showAttackedBrief(v){
  if(!v) return;
  const cas = (v.killed||0) > 0
    ? `<span style="color:#ff4444">${v.killed} killed</span>`
    : '';
  const inj = (v.injured||0) > 0
    ? `<span style="color:#ffaa00">${v.injured} injured</span>`
    : '';
  const casLine = [cas,inj].filter(Boolean).join('  ') || 'no casualties reported';
  const routeLine = v.from_port
    ? `<div style="margin-top:6px;font-size:10px;color:#aaa">
          From: ${v.from_port.split('(')[0].trim()}<br>
          To: ${v.to_port||'unknown destination'}<br>
         [box] Cargo: ${v.cargo||'unknown'}
       </div>`
    : '';
  const imoLine = v.imo
    ? `<div style="font-size:9px;color:#888;margin-top:4px">IMO: ${v.imo}</div>`
    : '';

  showInfoPanel(`
    <div style="font-family:Inter,sans-serif">
      <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px">
        ⚠ VESSEL ATTACK — Day ${v.day} (${v.date})
        ${v.time_utc ? ' at '+v.time_utc+' UTC' : ''}
      </div>
      <div style="font-size:15px;font-weight:700;color:#ff4444;margin-bottom:2px">
        ${v.vessel}
      </div>
      <div style="font-size:11px;color:#ccc;margin-bottom:6px">
        ${v.flag||''} ${v.type||''}
      </div>
      <div style="font-size:11px;margin-bottom:4px">
        <b>Location:</b> ${v.location}<br>
        <b>Zone:</b> ${v.zone}
      </div>
      <div style="font-size:11px;margin-bottom:4px">
        <b>Weapon:</b> ${v.weapon_cat}<br>
        <b>Actor:</b> ${v.actor}
      </div>
      <div style="font-size:11px;margin-bottom:4px">
        <b>Damage:</b> ${v.damage}
      </div>
      <div style="font-size:12px;font-weight:600;margin-bottom:4px">
        ${casLine}
      </div>
      <div style="font-size:11px;color:#aaa">
        <b>Outcome:</b> ${v.outcome}
      </div>
      ${routeLine}
      ${imoLine}
      ${v.imo ? `<div style="font-size:9px;color:#555;margin-top:4px">
        <a href="https://www.vesselfinder.com/vessels/details/${v.imo}"
           style="color:#4488ff" target="_blank">
          VesselFinder track ↗
        </a>
      </div>` : ''}
    </div>
  `);
}


    setInterval(()=>{const now=new Date();const tc=$('topbar-clock');if(tc)tc.textContent=now.toISOString().slice(11,19)+' UTC';const td=$('topbar-date');if(td)td.textContent=now.toISOString().slice(0,10);},1000);
    setInterval(updateAge,30000);updateAge();
    setMsg('\u0627\u0644\u0646\u0638\u0627\u0645 \u064a\u0639\u0645\u0644 \u0628\u0634\u0643\u0644 \u0637\u0628\u064a\u0639\u064a',100);setTimeout(hideLoader,600);initLiveDropdown();
  }catch(e){setMsg('ERROR: '+e.message);if($('ld-msg'))$('ld-msg').style.color='#ff8888';console.error(e);}
})();

function initBadges(){
  const c=SAT_CATS;
  const tlcSat=$('tlc-sat');if(tlcSat)tlcSat.textContent=(c.spy||0)+' \u0627\u0633\u062a\u062e\u0628\u0627\u0631\u0627\u062a\u064a';
  const tlcCiv=$('tlc-civ');if(tlcCiv)tlcCiv.textContent=(FLIGHT_DATA.total||0)+' \u0637\u0627\u0626\u0631\u0629';
  const tlcBases=$('tlc-bases');if(tlcBases)tlcBases.textContent=((INTEL_DATA.counts&&INTEL_DATA.counts.usbase)||0)+' \u0642\u0627\u0639\u062f\u0629';
  const tlcJam=$('tlc-jam');if(tlcJam)tlcJam.textContent=(Array.isArray(JAM_DATA)?JAM_DATA.length:0)+' \u0637\u0627\u0626\u0631\u0629';
  const tlcWar=$('tlc-war');if(tlcWar)tlcWar.textContent=(Array.isArray(WAR_EVENTS)?WAR_EVENTS.length:0)+' \u062d\u062f\u062b';
  const counts={};SATELLITES.forEach(s=>counts[s.cat]=(counts[s.cat]||0)+1);
  Object.entries(counts).forEach(([cat,n])=>{const el=$('lc-'+cat);if(el)el.textContent=n+' \u0642\u0645\u0631';});
  const jl=$('j-live');if(jl)jl.textContent=Array.isArray(JAM_DATA)?JAM_DATA.length:0;
  const jc=$('j-cells');if(jc)jc.textContent=(GPSJAM_DATA.cells||[]).length;
  const ja=$('j-avg');if(ja)ja.textContent=Math.round((GPSJAM_DATA.me_avg||0)*100)+'%';
  const jd=$('j-days');if(jd)jd.textContent=(GPSJAM_DATA.history||[]).length+' \u064a\u0648\u0645';
  const ft=$('f-total');if(ft)ft.textContent=FLIGHT_DATA.total||0;
  const fa=$('f-alerts');if(fa)fa.textContent=(FLIGHT_DATA.proximity_alerts||[]).length;
  if(INTEL_DATA.counts)Object.entries(INTEL_DATA.counts).forEach(([t,n])=>{const el=$('lc-'+t);if(el)el.textContent=n+' \u0645\u0648\u0642\u0639';});
  const lcCiv=$('lc-civ');if(lcCiv)lcCiv.textContent=(FLIGHT_DATA.total||0)+' \u0631\u062d\u0644\u0629';
  const lcJam=$('lc-jam');if(lcJam)lcJam.textContent=(Array.isArray(JAM_DATA)?JAM_DATA.length:0)+' \u0637\u0627\u0626\u0631\u0629';

  const tlcMarine=$('tlc-marine');if(tlcMarine)tlcMarine.textContent=(MARINE_DATA&&MARINE_DATA.count||0)+' \u0633\u0641\u064a\u0646\u0629';
  const nucCount=(INTEL_DATA.counts&&INTEL_DATA.counts.nuclear)||0;
  const tlcNuc=$('tlc-nuclear');if(tlcNuc)tlcNuc.textContent=nucCount+' \u0645\u0648\u0642\u0639';
}
function toggleLayer(cat){layerOn[cat]=!layerOn[cat];const t=$('lt-'+cat);if(t){t.classList.toggle('on',layerOn[cat]);t.classList.toggle('off',!layerOn[cat]);}if(cat==='spy'||cat==='military')topSyncChip('lchip-sat',layerOn.spy||layerOn.military);propagateAndRender(cat==='spy'||cat==='military');}
function updateStats(){const c=SAT_CATS;$('s-total').textContent=SAT_DATA.count||0;$('s-spy').textContent=c.spy||0;$('s-mil').textContent=c.military||0;$('s-stl').textContent=c.starlink||0;$('s-leo').textContent=c.leo||0;$('s-geo').textContent=c.geo||0;}
function updateAge(){const m=Math.round((Date.now()-new Date(SAT_DATA.fetched_at))/60000);const el=$('s-age');if(el)el.textContent=m<1?'\u0627\u0644\u0622\u0646':m+' \u062f\u0642\u064a\u0642\u0629';}
function toggleSection(id,headEl){const body=$(id);if(!body)return;const arrow=headEl?headEl.querySelector('.sec-arrow'):null;const col=body.classList.contains('collapsed');body.classList.toggle('collapsed',!col);if(arrow)arrow.classList.toggle('collapsed',!col);}
function _toggleSection(bodyId,arrowId){const body=$(bodyId);if(!body)return;const arrow=$(arrowId);const col=body.classList.contains('collapsed');body.classList.toggle('collapsed',!col);if(arrow)arrow.classList.toggle('collapsed',!col);}
function switchTab(name){document.querySelectorAll('.tab-pane').forEach(p=>p.classList.remove('active'));document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));const pane=$('tab-'+name),btn=$('tb-'+name);if(pane)pane.classList.add('active');if(btn)btn.classList.add('active');}

const IRAN_BOX={latMin:25,latMax:40,lonMin:44,lonMax:64};
const LAT_BUF=100/111,LON_BUF=100/(111*Math.cos(32.5*Math.PI/180));
function isOverIran(lat,lon,alt){return lat>=IRAN_BOX.latMin&&lat<=IRAN_BOX.latMax&&lon>=IRAN_BOX.lonMin&&lon<=IRAN_BOX.lonMax&&alt>80&&alt<2000;}
function isApproachingIran(lat,lon,alt){if(isOverIran(lat,lon,alt))return false;return lat>=IRAN_BOX.latMin-LAT_BUF&&lat<=IRAN_BOX.latMax+LAT_BUF&&lon>=IRAN_BOX.lonMin-LON_BUF&&lon<=IRAN_BOX.lonMax+LON_BUF&&alt>80&&alt<2000;}
function updateIranNow(){
  if(!SATELLITES||typeof satellite==='undefined')return;
  const now=new Date(),over=[],approach=[];
  SATELLITES.filter(s=>s.cat==='spy').forEach(s=>{try{const rec=satellite.twoline2satrec(s.l1,s.l2),pv=satellite.propagate(rec,now);if(!pv||!pv.position)return;const gmst=satellite.gstime(now),pos=satellite.eciToGeodetic(pv.position,gmst);const lat=satellite.radiansToDegrees(pos.latitude),lon=satellite.radiansToDegrees(pos.longitude),alt=pos.height;if(isOverIran(lat,lon,alt))over.push({s,lat,lon,alt});else if(isApproachingIran(lat,lon,alt))approach.push({s,lat,lon,alt});}catch{}});
  const ne=$('iran-now');if(ne)ne.textContent=over.length||0;
  const ae=$('iran-approach-count');if(ae)ae.textContent=approach.length||0;
  const ol=$('iran-over-list');if(ol)ol.innerHTML=over.length===0?'<div style="padding:8px 10px;font-size:9px;color:var(--text-muted)">\u0644\u0627 \u064a\u0648\u062c\u062f \u062d\u0627\u0644\u064a\u0627\u064b</div>':over.map(({s,lat,lon,alt})=>`<div style="padding:5px 10px;border-bottom:1px solid var(--ui-border);font-size:9px"><div style="font-weight:600;color:var(--gold)">${s.name}</div><div style="color:var(--text-muted);font-family:JetBrains Mono,monospace;font-size:8px">${lat.toFixed(1)}\u00b0 ${lon.toFixed(1)}\u00b0 \u00b7 ${Math.round(alt)}km</div></div>`).join('');
  const al=$('iran-approach-list');if(al)al.innerHTML=approach.length===0?'<div style="padding:8px 10px;font-size:9px;color:var(--text-muted)">\u0644\u0627 \u064a\u0648\u062c\u062f \u0645\u0642\u062a\u0631\u0628</div>':approach.map(({s,lat,lon,alt})=>`<div style="padding:5px 10px;border-bottom:1px solid var(--ui-border);font-size:9px"><div style="font-weight:600;color:var(--burg-400)">${s.name}</div><div style="color:var(--text-muted);font-family:JetBrains Mono,monospace;font-size:8px">${lat.toFixed(1)}\u00b0 ${lon.toFixed(1)}\u00b0 \u00b7 ${Math.round(alt)}km</div></div>`).join('');}
setTimeout(()=>{updateIranNow();setInterval(updateIranNow,15000);},1500);

var jammingOn=false,jamEntities=[];
function toggleJamming(){jammingOn=!jammingOn;const tog=$('lt-jam');if(tog){tog.classList.toggle('on',jammingOn);tog.classList.toggle('off',!jammingOn);}topSyncChip('lchip-jam',jammingOn);if(jammingOn)renderJamming();else clearJamming();}
function clearJamming(){jamEntities.forEach(e=>{try{viewer.entities.remove(e);}catch{}});jamEntities=[];}
function renderJamming(){
  if(!viewer)return;clearJamming();
  const jamList=Array.isArray(JAM_DATA)?JAM_DATA:[];
  jamList.forEach(a=>{const ent=viewer.entities.add({position:Cesium.Cartesian3.fromDegrees(a.lon,a.lat,a.alt_m||8000),point:{pixelSize:8,color:Cesium.Color.fromCssColorString('#ff3355').withAlpha(0.9),outlineColor:Cesium.Color.WHITE.withAlpha(0.6),outlineWidth:1,disableDepthTestDistance:Number.POSITIVE_INFINITY,scaleByDistance:new Cesium.NearFarScalar(5e5,1.2,2e7,0.4)},label:{text:(a.callsign||a.icao||'').trim(),font:'500 9px Inter,sans-serif',fillColor:Cesium.Color.fromCssColorString('#ff8888'),outlineColor:Cesium.Color.BLACK,outlineWidth:2,style:Cesium.LabelStyle.FILL_AND_OUTLINE,pixelOffset:new Cesium.Cartesian2(0,-18),distanceDisplayCondition:new Cesium.DistanceDisplayCondition(0,3e6),disableDepthTestDistance:Number.POSITIVE_INFINITY},description:`<div style="padding:10px;font-family:Inter,sans-serif;min-width:200px;border-top:3px solid #ff3355"><b>${a.callsign||a.icao}</b><br>\u0646\u0648\u0639 \u0627\u0644\u062a\u062f\u0647\u0648\u0631: ${a.degraded_type||'GPS degraded'}<br>\u0627\u0644\u0627\u0631\u062a\u0641\u0627\u0639: ${a.alt_ft?a.alt_ft.toLocaleString()+' ft':'\u2014'}</div>`});jamEntities.push(ent);});
  const cells=(GPSJAM_DATA.cells||[]).sort((a,b)=>(b.intensity||0)-(a.intensity||0)).slice(0,150);cells.forEach(c=>{if((c.intensity||0)<0.05)return;const alpha=Math.min(0.40+c.intensity*0.55,0.95);const jcol=Cesium.Color.fromCssColorString('#ff1111').withAlpha(alpha);const dotSize=Math.round(8+c.intensity*14);const radius=50000+c.intensity*130000;const jpt=viewer.entities.add({name:c.label||('تشويش GPS '+Math.round(c.intensity*100)+'%'),position:Cesium.Cartesian3.fromDegrees(c.lon,c.lat,500),point:{pixelSize:dotSize,color:jcol,outlineColor:Cesium.Color.WHITE.withAlpha(0.85),outlineWidth:1.5,disableDepthTestDistance:Number.POSITIVE_INFINITY,scaleByDistance:new Cesium.NearFarScalar(5e5,1.4,2e7,0.5)},ellipse:{semiMajorAxis:radius,semiMinorAxis:radius,height:0,material:new Cesium.ColorMaterialProperty(Cesium.Color.fromCssColorString('#ff1111').withAlpha(0.07)),outline:true,outlineColor:Cesium.Color.fromCssColorString('#ff1111').withAlpha(0.45),outlineWidth:1},description:'<div style="padding:10px;font-family:Inter,sans-serif;min-width:200px;border-top:3px solid #ff1111"><b>'+(c.label||'GPS Jamming')+'</b><br>شدة: '+Math.round(c.intensity*100)+'%<br>موقع: '+c.lat.toFixed(2)+'\u00b0, '+c.lon.toFixed(2)+'\u00b0</div>'});jpt._jamLat=c.lat;jpt._jamLon=c.lon;jpt._jamData=c;jamEntities.push(jpt);});}

var civFlightsOn=false,civFlightEntities=[];
function makePlaneIcon(col,label){const bg=col+'44',sz=36;const svg=`<svg xmlns='http://www.w3.org/2000/svg' width='${sz}' height='${sz}'><circle cx='${sz/2}' cy='${sz/2}' r='${sz/2-2}' fill='${bg}' stroke='${col}' stroke-width='2.5'/><text x='${sz/2}' y='${sz/2+6}' text-anchor='middle' font-size='16' fill='${col}'>✈</text></svg>`;return 'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);}
const FLIGHT_ICONS={commercial:makePlaneIcon('#00d4ff'),military:makePlaneIcon('#ff6b35'),cargo:makePlaneIcon('#ffaa00'),private:makePlaneIcon('#aa88ff'),unknown:makePlaneIcon('#888888')};
function toggleCivFlights(){civFlightsOn=!civFlightsOn;const tog=$('lt-civ');if(tog){tog.classList.toggle('on',civFlightsOn);tog.classList.toggle('off',!civFlightsOn);}topSyncChip('lchip-civ',civFlightsOn);if(civFlightsOn)renderCivFlights();else clearCivFlights();renderFIRList();}
function clearCivFlights(){civFlightEntities.forEach(e=>{try{viewer.entities.remove(e);}catch{}});civFlightEntities=[];}
function renderCivFlights(){
  if(!viewer)return;clearCivFlights();
  const aircraft=FLIGHT_DATA.aircraft||[];
  aircraft.forEach(a=>{const altM=a.alt_m||0,heading=Cesium.Math.toRadians(a.heading||0);const col={commercial:'#00d4ff',military:'#ff6b35',cargo:'#ffaa00',private:'#aa88ff',unknown:'#aaaaaa'}[a.ac_type]||'#aaaaaa';const ent=viewer.entities.add({position:Cesium.Cartesian3.fromDegrees(a.lon,a.lat,altM),billboard:{image:FLIGHT_ICONS[a.ac_type]||FLIGHT_ICONS.unknown,rotation:-heading,alignedAxis:Cesium.Cartesian3.UNIT_Z,width:36,height:36,verticalOrigin:Cesium.VerticalOrigin.CENTER,disableDepthTestDistance:Number.POSITIVE_INFINITY,scaleByDistance:new Cesium.NearFarScalar(5e5,1.4,2e7,0.5)},label:{text:a.callsign||a.icao,font:'500 9px Inter,sans-serif',fillColor:Cesium.Color.fromCssColorString('#c8e6ff'),outlineColor:Cesium.Color.BLACK,outlineWidth:2,style:Cesium.LabelStyle.FILL_AND_OUTLINE,pixelOffset:new Cesium.Cartesian2(0,-20),distanceDisplayCondition:new Cesium.DistanceDisplayCondition(0,3e6),disableDepthTestDistance:Number.POSITIVE_INFINITY},description:`<div style="padding:10px;font-family:Inter,sans-serif;min-width:220px;border-top:3px solid ${col}"><b>\u2708 ${a.callsign||a.icao}</b><br>\u0646\u0648\u0639: ${a.ac_type||'\u2014'}<br>\u0627\u0644\u0627\u0631\u062a\u0641\u0627\u0639: ${a.alt_ft?a.alt_ft.toLocaleString()+' ft':'\u2014'}<br>FIR: ${a.fir_name||a.fir||'\u2014'}</div>`});ent._fltData=a;civFlightEntities.push(ent);});}
function renderFIRList(){const el=$('flight-fir-list');if(!el)return;const firs=(FLIGHT_DATA.fir_summary||[]).slice(0,12);el.innerHTML=firs.length?firs.map(f=>`<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 10px;border-bottom:1px solid var(--ui-border);font-size:10px"><span>${f.name||f.fir}</span><span style="font-family:JetBrains Mono,monospace;font-weight:700;color:var(--burg-700)">${f.count}</span></div>`).join(''):'<div style="padding:8px 10px;font-size:9px;color:var(--text-muted)">\u0644\u0627 \u0628\u064a\u0627\u0646\u0627\u062a</div>';}

const intelState={nuclear:false,usbase:false,chokepoint:false,city:false};
const intelEntities={nuclear:[],usbase:[],chokepoint:[],city:[]};
const INTEL_CFG={nuclear:{color:'#00e5ff',icon:'\u2622'},usbase:{color:'#1565c0',icon:'\u2605'},chokepoint:{color:'#ff9800',icon:'\u2693'},city:{color:'#bdbdbd',icon:'\u25cf'}};
function toggleIntel(type){intelState[type]=!intelState[type];const tog=$('lt-'+type);if(tog){tog.classList.toggle('on',intelState[type]);tog.classList.toggle('off',!intelState[type]);}if(intelState[type])renderIntelType(type);else clearIntelType(type);}
function clearIntelType(type){intelEntities[type].forEach(e=>{try{viewer.entities.remove(e);}catch{}});intelEntities[type]=[];}
function renderAllIntel(){['nuclear','usbase','chokepoint','city'].forEach(t=>{if(!intelState[t]){intelState[t]=true;const tog=$('lt-'+t);if(tog){tog.classList.add('on');tog.classList.remove('off');}renderIntelType(t);}});}
function clearAllIntel(){['nuclear','usbase','chokepoint','city'].forEach(t=>{if(intelState[t]){intelState[t]=false;const tog=$('lt-'+t);if(tog){tog.classList.add('off');tog.classList.remove('on');}clearIntelType(t);}});}
function renderIntelType(type){
  if(!viewer)return;clearIntelType(type);
  const cfg=INTEL_CFG[type],sites=(INTEL_DATA.sites||[]).filter(s=>s.type===type||s.category===type);
  const lc=$('lc-'+type);if(lc)lc.textContent=sites.length+' \u0645\u0648\u0642\u0639';
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><circle cx="12" cy="12" r="10" fill="${cfg.color}22" stroke="${cfg.color}" stroke-width="1.5"/><text x="12" y="16" text-anchor="middle" font-size="13">${cfg.icon}</text></svg>`;
  const icon='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);
  sites.forEach(site=>{const ent=viewer.entities.add({position:Cesium.Cartesian3.fromDegrees(site.lon,site.lat,0),billboard:{image:icon,width:24,height:24,verticalOrigin:Cesium.VerticalOrigin.BOTTOM,heightReference:Cesium.HeightReference.CLAMP_TO_GROUND,disableDepthTestDistance:Number.POSITIVE_INFINITY,scaleByDistance:new Cesium.NearFarScalar(5e5,1.6,2e7,0.6)},label:{text:site.name_en||site.name,font:'500 11px Inter,sans-serif',fillColor:Cesium.Color.WHITE,outlineColor:Cesium.Color.BLACK,outlineWidth:2,style:Cesium.LabelStyle.FILL_AND_OUTLINE,pixelOffset:new Cesium.Cartesian2(0,-22),distanceDisplayCondition:new Cesium.DistanceDisplayCondition(0,type==='city'?5e6:12e6),disableDepthTestDistance:Number.POSITIVE_INFINITY,showBackground:true,backgroundColor:Cesium.Color.fromBytes(0,0,0,160),backgroundPadding:new Cesium.Cartesian2(5,3)},description:`<div style="padding:14px;font-family:Inter,sans-serif;min-width:240px;border-top:3px solid ${cfg.color}"><div style="font-size:14px;font-weight:700;color:#18000e;margin-bottom:4px">${cfg.icon} ${site.name_en||site.name}</div><div style="font-size:10px;color:#888">${site.category||type} \u00b7 ${site.country||''}</div><div style="margin-top:8px;font-size:11px;color:#333;line-height:1.7">${site.notes||site.detail||''}</div></div>`});intelEntities[type].push(ent);});}

const WAR_TYPE_COL={strike:'#ff2200',airstrike:'#ff2200',military:'#ff8800',retaliation:'#ff4400',political:'#4488ff',diplomatic:'#4488ff',humanitarian:'#44cc88',missile:'#ff2200',naval:'#0088ff'};
var warOn=false,warPlaying=false,warSpeed=1,warTimer=null,warNow=0,warEntities=[],dragInitialized=false;
var WAR_T0=0,WAR_T1=0;
const WEVS=Array.isArray(WAR_EVENTS)?WAR_EVENTS:[];
const _C85_REPORT='__REPORT_TEXT__';  // Replaced by Cell 18 with C8.5 HTML
function warSpan(){return WAR_T1-WAR_T0||1;}
function tPct(ms){return Math.max(0,Math.min(100,((ms-WAR_T0)/warSpan())*100));}
function pctT(p){return WAR_T0+(p/100)*warSpan();}
function clientXToPct(x){const r=($('tl-pin-row')||$('tl-canvas')).getBoundingClientRect();return Math.max(0,Math.min(100,((x-r.left)/r.width)*100));}
function closestIdx(ms){if(!WEVS.length)return -1;let best=0,bd=Infinity;WEVS.forEach((e,i)=>{const t=new Date(e.date||e.t||'').getTime();const d=Math.abs(t-ms);if(d<bd){bd=d;best=i;}});return best;}
function initWarTimeline(){if(WEVS.length){const dates=WEVS.map(e=>new Date(e.date||e.t||'').getTime()).filter(t=>!isNaN(t)).sort((a,b)=>a-b);WAR_T0=dates[0];WAR_T1=dates[dates.length-1];if(WAR_T1-WAR_T0<14*86400000)WAR_T1=WAR_T0+14*86400000;}else{WAR_T0=new Date('2026-02-26').getTime();WAR_T1=WAR_T0+21*86400000;}warNow=WAR_T0;}
function warSeekTime(ms,brief){warNow=Math.max(WAR_T0,Math.min(WAR_T1,ms));updateWarDisplay();if(brief){const i=closestIdx(warNow);if(i>=0&&WEVS[i])showWarBrief(WEVS[i],i);}}
function warSeekTo(i,brief){if(!WEVS[i])return;warNow=new Date(WEVS[i].date||WEVS[i].t||'').getTime();updateWarDisplay();if(brief)showWarBrief(WEVS[i],i);}
function warSeek(dir){const cur=Math.max(0,closestIdx(warNow));warSeekTo(Math.max(0,Math.min(WEVS.length-1,cur+dir)),true);}
function warPlayPause(){if(!warOn){toggleWarTimeline();return;}warPlaying=!warPlaying;const btn=$('war-btn-play');if(btn)btn.textContent=warPlaying?'\u23f8':'\u25b6';if(warPlaying){warTimer=setInterval(()=>{warNow=Math.min(warNow+3600000*warSpeed,WAR_T1);updateWarDisplay();if(warNow>=WAR_T1)warPlayPause();},150);}else{clearInterval(warTimer);warTimer=null;}}
function warStop(){if(warPlaying)warPlayPause();}
function setWarSpeed(s){warSpeed=s;['1x','2x','5x'].forEach(id=>{const el=$('spd-'+id);if(el)el.classList.toggle('rst',id===s+'x');});if(warPlaying){warStop();warPlayPause();}}
function toggleWarTimeline(){
  warOn=!warOn;const tog=$('lt-war'),label=$('bt-toggle-label');
  if(tog){tog.classList.toggle('on',warOn);tog.classList.toggle('off',!warOn);}
  if(label)label.textContent=warOn?'\u0627\u0644\u062c\u062f\u0648\u0644 \u0627\u0644\u0632\u0645\u0646\u064a \u2713':'\u0627\u0644\u062c\u062f\u0648\u0644 \u0627\u0644\u0632\u0645\u0646\u064a';
  topSyncChip('lchip-war',warOn);
  if(warOn){initWarTimeline();renderWarMarkers();buildTimeline();initDrag();warSeekTime(WAR_T1,false);}
  else{warStop();clearWarEntities();clearHistSatEntities();const td=$('war-time-display');if(td)td.textContent='\u0627\u0644\u062c\u062f\u0648\u0644 \u0645\u062a\u0648\u0642\u0641';const en=$('bt-event-name');if(en)en.textContent='\u0641\u0639\u0651\u0644 \u0627\u0644\u062c\u062f\u0648\u0644 \u0627\u0644\u0632\u0645\u0646\u064a \u0644\u0644\u0628\u062f\u0621';const cursor=$('tl-cursor');if(cursor)cursor.style.left='0%';const elapsed=$('tl-elapsed');if(elapsed)elapsed.style.width='0%';}}
function buildWarEventList(){const el=$('war-event-list');if(!el||!WEVS.length)return;el.innerHTML=WEVS.map((e,i)=>{const col=e.col||WAR_TYPE_COL[e.category||e.type]||'#ff8800';return `<div style="padding:7px 10px;border-left:3px solid ${col};margin-bottom:1px;cursor:pointer;transition:background .12s" onmouseover="this.style.background='#f7f2f4'" onmouseout="this.style.background=''" onclick="warSeekTo(${i},true)"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px"><span style="font-size:9px;font-weight:600;color:var(--text-primary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1">${e.title_ar||e.title||e.label||''}</span><span style="font-size:8px;color:var(--text-muted);font-family:JetBrains Mono,monospace;flex-shrink:0;margin-left:6px">${(e.date||e.t||'').slice(5,10)}</span></div><div style="font-size:8px;color:var(--text-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${e.location||''}</div></div>`;}).join('');}
function clearWarEntities(){warEntities.forEach(({ring,pt})=>{if(ring){try{viewer.entities.remove(ring);}catch{}}if(pt){try{viewer.entities.remove(pt);}catch{}}});warEntities=[];}
function renderWarMarkers(){
  clearWarEntities();if(!viewer||!WEVS.length)return;
  const BATCH=30,evs=WEVS;
  function addBatch(start){
    if(!viewer)return;
    const end=Math.min(start+BATCH,evs.length);
    for(let i=start;i<end;i++){
      const e=evs[i];
      if(!e)continue;
      const lat=parseFloat(e.lat),lon=parseFloat(e.lon);
      if(!lat||!lon||isNaN(lat)||isNaN(lon))continue;
      const rawCol=e.col||WAR_TYPE_COL[e.category||e.type]||'#ff8800';
      const col=Cesium.Color.fromCssColorString(rawCol);
      const pt=viewer.entities.add({
        position:Cesium.Cartesian3.fromDegrees(lon,lat,2000),
        point:{
          pixelSize:10,
          color:col.withAlpha(0.92),
          outlineColor:Cesium.Color.WHITE.withAlpha(0.8),
          outlineWidth:1.5,
          disableDepthTestDistance:Number.POSITIVE_INFINITY,
          scaleByDistance:new Cesium.NearFarScalar(5e5,1.3,2e7,0.5)
        },
        show:true
      });
      pt._wevsIdx=i;
      warEntities.push({ring:null,pt,t:new Date(e.date||e.t||'').getTime()});
    }
    if(end<evs.length)setTimeout(()=>addBatch(end),16);
  }
  addBatch(0);
}
// showWarBrief v1 removed — using v2 below
function showWarBrief(ev,idx){
  if(!ev)return;
  // show card immediately
  const card=$('war-brief-card');if(!card)return;
  const col=ev.col||WAR_TYPE_COL[ev.category||ev.type]||'#ff8800';
  const _s=(id,val)=>{const el=$(id);if(el)el.textContent=val;};
  _s('wbc-id','W'+String(idx).padStart(4,'0'));
  _s('wbc-time',(ev.date||ev.t||'').slice(0,10));
  const dot=$('wbc-type-dot');if(dot){dot.style.width='8px';dot.style.height='8px';dot.style.borderRadius='50%';dot.style.flexShrink='0';dot.style.background=col;}
  _s('wbc-type-label',(ev.category||ev.type||'CONFLICT').toUpperCase());
  _s('wbc-title',ev.title_ar||ev.title||ev.label||'\u2014');
  const $det=$('wbc-detail');if($det){$det.style.maxHeight='';$det.style.overflowY='';$det.style.padding='';$det.style.borderLeft='';$det.textContent=ev.detail||'\u2014';}
  _s('wbc-loc',ev.location||'\u2014');
  _s('wbc-actors','');
  const urlEl=$('wbc-url');if(urlEl)urlEl.innerHTML='';
  const $meta=$('wbc-meta');if($meta)$meta.innerHTML='';
  card.classList.add('visible');
  const fill=$('wbc-progress-fill');if(fill){fill.style.transition='none';fill.style.width='100%';fill.getBoundingClientRect();fill.style.transition='width 10s linear';fill.style.width='0%';}
  clearTimeout(window._wbcTimer);window._wbcTimer=setTimeout(closeWarBrief,10000);
  buildWarEventList();
  // fly camera — independent of card
  if(viewer&&ev.lat!=null&&ev.lon!=null&&(ev.lat!==0||ev.lon!==0)){
    viewer.camera.cancelFlight();
    viewer.camera.flyTo({destination:Cesium.Cartesian3.fromDegrees(parseFloat(ev.lon),parseFloat(ev.lat),400000),duration:1.5,easingFunction:Cesium.EasingFunction.CUBIC_IN_OUT});
  }
}
function closeWarBrief(){clearTimeout(window._wbcTimer);const card=$('war-brief-card');if(card)card.classList.remove('visible');}
function buildTimeline(){
  const axisRow=$('tl-axis-row');if(!axisRow)return;
  ['war','jam','sat','flt'].forEach(id=>{const c=$('tl-canvas-'+id);if(c)c.innerHTML='';});
  axisRow.innerHTML='';
  const span=warSpan();
  const WAR_START_MS=new Date('2026-02-28').getTime();
  const totalDays=Math.ceil(span/86400000);

  // ── ROW 1: WAR EVENTS — binned by DAY ──────────────────────────
  // FIX: bin by full day (86400000ms) not 6h bins.
  // 93% of timestamps are inferred (spread 30min apart from 06:00)
  // so 6h binning created false intra-day clusters.
  // Daily binning is honest: one bar = one day, height = event count.
  const warCanvas=$('tl-canvas-war');
  if(warCanvas&&WEVS.length){
    // Count events per day
    const dayBins={};
    WEVS.forEach(ev=>{
      const t=new Date(ev.date||ev.t||'').getTime();
      if(isNaN(t))return;
      const dk=Math.floor((t-WAR_T0)/86400000);
      if(!dayBins[dk])dayBins[dk]={count:0,indices:[],col:ev.col||'#ff8800',t};
      dayBins[dk].count++;
      dayBins[dk].indices.push(WEVS.indexOf(ev));
    });
    const maxCount=Math.max(...Object.values(dayBins).map(b=>b.count),1);
    const barW=Math.max(0.4,(100/totalDays)).toFixed(3);

    // Draw day bars
    for(let dk=0;dk<totalDays;dk++){
      const t=WAR_T0+dk*86400000;
      const pct=((t-WAR_T0)/span)*100;
      if(pct<0||pct>100)continue;
      const b=dayBins[dk];
      if(!b)continue;
      const hp=Math.max(4,Math.round((b.count/maxCount)*100));
      const intensity=b.count/maxCount;
      const bar=document.createElement('div');
      bar.className='tl-bar';
      bar.style.cssText='left:'+pct.toFixed(3)+'%;width:'+barW+'%;height:'+hp+'%;'
        +'position:absolute;bottom:0;border-radius:1px 1px 0 0;'
        +'background:rgba('+(Math.round(160+90*intensity))+',20,40,'
        +(0.45+0.5*intensity).toFixed(2)+')';
      bar.title='D'+(dk+1)+': '+b.count+' event'+(b.count>1?'s':'');
      bar.addEventListener('click',e=>{
        e.stopPropagation();
        showDayBrief(b.indices, dk+1);
        warSeekTime(t, false);
      });
      warCanvas.appendChild(bar);
    }

    // Day badges (count labels above bars)
    Object.entries(dayBins).sort((a,b)=>+a[0]-+b[0]).forEach(([dk,g])=>{
      const pct=tPct(g.t);
      const badge=document.createElement('div');
      badge.className='tl-day-badge';
      badge.style.cssText='left:'+pct.toFixed(3)+'%;border-color:'+g.col+';color:'+g.col;
      badge.textContent=g.count>1?g.count:'\u25cf';
      badge.title='Day '+(+dk+1)+': '+g.count+' event'+(g.count>1?'s':'');
      badge.addEventListener('click',ev=>{ev.stopPropagation();showDayBrief(g.indices,+dk+1);});
      warCanvas.appendChild(badge);
    });
  }

  // ── ROW 2: GPS JAMMING — real vs estimated visually distinct ───
  // FIX: real bars (from accumulator) = solid color
  //      estimated bars (synthetic fill) = faint with dashed border
  //      so you can immediately see which days have actual data
  const jamCanvas=$('tl-canvas-jam');
  if(jamCanvas){
    const jamDays=buildJamDailyData();
    if(jamDays.length){
      const maxI=Math.max(...jamDays.map(d=>d.intensity),0.01);
      const n=jamDays.length;
      const realDates=new Set((GPSJAM_DATA&&GPSJAM_DATA.history||[]).map(h=>h.date));
      jamDays.forEach(day=>{
        const t=new Date(day.date).getTime();
        const pct=((t-WAR_T0)/span)*100;
        if(pct<0||pct>100)return;
        const hp=Math.max(3,Math.round((day.intensity/maxI)*100));
        const isReal=realDates.has(day.date);
        const alpha=isReal?(0.5+0.45*(day.intensity/maxI)):(0.15+0.1*(day.intensity/maxI));
        const r=day.intensity>0.7?Math.round(30+200*day.intensity):Math.round(day.intensity*60);
        const g2=day.intensity<0.5?Math.round(150+50*day.intensity):Math.round(180-100*(day.intensity-0.5));
        const bar=document.createElement('div');
        bar.className='tl-bar';
        // Real = solid, Estimated = faint + dashed outline
        bar.style.cssText='left:'+pct.toFixed(2)+'%;width:'+Math.max(0.5,(100/n)).toFixed(2)+'%;'
          +'height:'+hp+'%;position:absolute;bottom:0;border-radius:1px 1px 0 0;'
          +'background:rgba('+r+','+g2+',40,'+alpha.toFixed(2)+');'
          +(isReal?'':'border:1px dashed rgba('+r+','+g2+',40,0.4);box-sizing:border-box;');
        bar.title=(isReal?'[REAL] ':'[EST] ')+'D'+day.dayNum+' ('+day.date+'): '
          +Math.round(day.intensity*100)+'% jamming';
        bar.addEventListener('click',()=>{
          const cells=(GPSJAM_DATA&&GPSJAM_DATA.cells)||[];
          const top=cells.slice().sort((a,b)=>(b.intensity||0)-(a.intensity||0))[0];
          if(top){
            showJamBrief(top,day);
            if(viewer)viewer.camera.flyTo({
              destination:Cesium.Cartesian3.fromDegrees(top.lon,top.lat,500000),
              duration:1.5
            });
          }
        });
        jamCanvas.appendChild(bar);
      });

      // Add "real data" count label
      const realCount=realDates.size;
      const totalCount=jamDays.length;
      if(realCount < totalCount){
        const note=document.createElement('div');
        note.style.cssText='position:absolute;top:2px;right:4px;font-size:8px;'
          +'color:rgba(255,100,60,0.8);font-family:JetBrains Mono,monospace;'
          +'background:rgba(0,0,0,0.3);padding:1px 4px;border-radius:2px;pointer-events:none;z-index:10';
        note.textContent=realCount+'/'+totalCount+' real';
        note.title=realCount+' days have real MLAT data. '+( totalCount-realCount)+' days are estimated — run Cell C5 more frequently to build real history.';
        jamCanvas.style.position='relative';
        jamCanvas.appendChild(note);
      }
    }
  }

  // ── ROW 3: SATELLITE OVERFLIGHTS ───────────────────────────────
  // FIX 1: show ALL days — not just days with iran_count > 0
  //   Days with satellites present but not over Iran = faint bar
  //   Days with zero satellite data = empty (honest gap)
  // FIX 2: if HIST_SAT_DATA is empty, show "no data" message
  const satCanvas=$('tl-canvas-sat');
  if(satCanvas){
    if(!HIST_SAT_DATA||!HIST_SAT_DATA.days||!HIST_SAT_DATA.days.length){
      // No satellite data — show honest placeholder
      const msg=document.createElement('div');
      msg.style.cssText='position:absolute;inset:0;display:flex;align-items:center;'
        +'justify-content:center;font-size:9px;color:rgba(255,215,0,0.4);'
        +'font-family:JetBrains Mono,monospace;pointer-events:none';
      msg.textContent='لا توجد بيانات — أعد تشغيل C3';
      msg.title='HIST_SAT_DATA is empty. Delete ~/.ifs_hist_positions.json and re-run Cell C3.';
      satCanvas.style.position='relative';
      satCanvas.appendChild(msg);
    } else {
      const days=HIST_SAT_DATA.days;
      const dayMap={};
      days.forEach(d=>dayMap[d.date]=d);
      const maxCount=Math.max(...days.map(d=>d.iran_count||0),1);
      const barW=Math.max(0.4,(100/totalDays)).toFixed(3);

      for(let dk=0;dk<totalDays;dk++){
        const t=WAR_T0+dk*86400000;
        const dateStr=new Date(t).toISOString().slice(0,10);
        const pct=((t-WAR_T0)/span)*100;
        if(pct<0||pct>100)continue;

        const dayData=dayMap[dateStr];
        if(!dayData)continue; // honest gap — no data for this day

        const iranCount=dayData.iran_count||0;
        const totalSats=dayData.satellites?dayData.satellites.length:0;

        const bar=document.createElement('div');
        bar.className='tl-bar';

        if(iranCount>0){
          // Satellites over Iran — full gold bar
          const hp=Math.max(4,Math.round((iranCount/maxCount)*100));
          const alpha=0.4+0.55*(iranCount/maxCount);
          bar.style.cssText='left:'+pct.toFixed(2)+'%;width:'+barW+'%;height:'+hp+'%;'
            +'position:absolute;bottom:0;border-radius:1px 1px 0 0;'
            +'background:rgba(220,180,0,'+alpha.toFixed(2)+')';
          bar.title='D'+(dk+1)+' ('+dateStr+'): '+iranCount+' ISR satellites over Iran'
            +' | '+totalSats+' total tracked';
        } else if(totalSats>0){
          // Satellites tracked but none over Iran — faint bar
          bar.style.cssText='left:'+pct.toFixed(2)+'%;width:'+barW+'%;height:20%;'
            +'position:absolute;bottom:0;border-radius:1px 1px 0 0;'
            +'background:rgba(180,140,0,0.18);'
            +'border-top:1px solid rgba(180,140,0,0.3)';
          bar.title='D'+(dk+1)+' ('+dateStr+'): 0 over Iran | '+totalSats+' sats tracked (out of range)';
        }

        bar.addEventListener('click',()=>{
          warSeekTime(t,false);
          showHistSatsForDay(dateStr);
          if(viewer)viewer.camera.flyTo({
            destination:Cesium.Cartesian3.fromDegrees(53,32,3200000),
            duration:1.8,
            easingFunction:Cesium.EasingFunction.CUBIC_IN_OUT
          });
        });
        satCanvas.appendChild(bar);
      }
    }
  }

  // ── ROW 4: FLIGHTS — honest display ────────────────────────────
  // FIX: remove the misleading inverse-event-density proxy.
  // The old code used (1 - events*0.05) as a "flight disruption"
  // proxy which was not flight data — it was inverted event density.
  // Replace with:
  //   - If FLIGHT_DATA has aircraft: show single bar at today
  //     representing current ME aircraft count (honest snapshot)
  //   - If no flight data: show "live data only" message
  //   - Historical flight data cannot be reconstructed without logs
  const fltCanvas=$('tl-canvas-flt');
  if(fltCanvas){
    const aircraft=(FLIGHT_DATA&&FLIGHT_DATA.aircraft)||[];
    const meCount=aircraft.filter(a=>
      a.lat>=12&&a.lat<=42&&a.lon>=29&&a.lon<=65
    ).length;

    if(meCount>0){
      // Show today's snapshot as a single bar at the rightmost position
      const todayT=Date.now();
      const pct=Math.min(99,((todayT-WAR_T0)/span)*100);
      const BASELINE_ME=2800;  // pre-war ME aircraft estimate
      const ratio=Math.min(1,meCount/BASELINE_ME);
      const hp=Math.max(4,Math.round(ratio*100));
      const bar=document.createElement('div');
      bar.className='tl-bar';
      bar.style.cssText='left:'+pct.toFixed(2)+'%;width:3%;height:'+hp+'%;'
        +'position:absolute;bottom:0;border-radius:1px 1px 0 0;'
        +'background:rgba(0,140,200,0.75);'
        +'border-left:2px solid rgba(0,200,255,0.9)';
      bar.title='Live snapshot: '+meCount+' aircraft in Middle East airspace'
        +' ('+Math.round(ratio*100)+'% of pre-war baseline)';
      bar.addEventListener('click',()=>{showFlightsForDay();});
      fltCanvas.appendChild(bar);

      // Add "live only" note
      const note=document.createElement('div');
      note.style.cssText='position:absolute;top:2px;left:4px;font-size:8px;'
        +'color:rgba(0,200,255,0.7);font-family:JetBrains Mono,monospace;'
        +'background:rgba(0,0,0,0.3);padding:1px 4px;border-radius:2px;'
        +'pointer-events:none;z-index:10';
      note.textContent='live only — '+meCount+' ac';
      note.title='Only current snapshot available. Run C6+C7 regularly to build history.';
      fltCanvas.style.position='relative';
      fltCanvas.appendChild(note);
    } else {
      // No flight data — honest empty state
      const msg=document.createElement('div');
      msg.style.cssText='position:absolute;inset:0;display:flex;align-items:center;'
        +'justify-content:center;font-size:9px;color:rgba(0,140,200,0.35);'
        +'font-family:JetBrains Mono,monospace;pointer-events:none';
      msg.textContent='لقطة مباشرة فقط — شغّل C6';
      msg.title='Flight history not available. Run Cell C6 to load current data.';
      fltCanvas.style.position='relative';
      fltCanvas.appendChild(msg);
    }
  }

  // ── Shared date axis ────────────────────────────────────────────
  var d=new Date(WAR_T0);d.setUTCHours(0,0,0,0);
  const endD=new Date(WAR_T1);endD.setUTCDate(endD.getUTCDate()+1);
  while(d<=endD){
    const pct=tPct(d.getTime());
    const isWS=d.getTime()===WAR_START_MS;
    const lbl=document.createElement('div');
    lbl.className='tl-day-lbl'+(isWS?' war-start':'');
    lbl.style.left=pct+'%';
    const dn=Math.round((d.getTime()-WAR_START_MS)/86400000)+1;
    lbl.textContent=dn>=1?'D'+dn:d.toISOString().slice(5,10);
    axisRow.appendChild(lbl);
    d.setUTCDate(d.getUTCDate()+1);
  }
  buildWarEventList();
}

function initDrag(){
  if(dragInitialized)return;dragInitialized=true;
  const canvas=$('tl-canvas'),handle=$('tl-handle');if(!canvas||!handle)return;
  handle.addEventListener('pointerdown',e=>{e.preventDefault();e.stopPropagation();handle.setPointerCapture(e.pointerId);handle.classList.add('dragging');if(viewer)viewer.scene.screenSpaceCameraController.enableInputs=false;warSeekTime(pctT(clientXToPct(e.clientX)),false);});
  handle.addEventListener('pointermove',e=>{if(!handle.hasPointerCapture(e.pointerId))return;warSeekTime(pctT(clientXToPct(e.clientX)),false);});
  handle.addEventListener('pointerup',e=>{if(!handle.hasPointerCapture(e.pointerId))return;handle.releasePointerCapture(e.pointerId);handle.classList.remove('dragging');if(viewer)viewer.scene.screenSpaceCameraController.enableInputs=true;const i=closestIdx(warNow);if(i>=0&&WEVS[i])showWarBrief(WEVS[i],i);});
  canvas.addEventListener('pointerdown',e=>{if(e.target===handle||e.target.classList.contains('tl-pin'))return;e.preventDefault();warSeekTime(pctT(clientXToPct(e.clientX)),true);});}
function updateWarDisplay(){
  if(!WAR_T0||!WAR_T1)return;
  const pct=tPct(warNow);
  const cursor=$('tl-cursor-line');if(cursor)cursor.style.left=pct+'%';
  const elapsed=$('tl-elapsed-overlay');if(elapsed)elapsed.style.width=pct+'%';
  const dstr=new Date(warNow).toISOString().slice(0,16).replace('T',' ')+' UTC';
  const td=$('war-time-display');if(td)td.textContent=dstr;
  const i=closestIdx(warNow);
  if(i>=0&&WEVS[i]){
    const ev=WEVS[i];
    const en=$('bt-event-name');if(en)en.textContent=ev.title_ar||ev.title||ev.label||'';
    const el=$('bt-event-loc');if(el)el.textContent=ev.location?'&#128205; '+ev.location:'';
  }
  warEntities.forEach(({ring,pt,t})=>{const v=t<=warNow;if(ring)ring.show=v;if(pt)pt.show=v;});
  // FIX: removed propagateAndRender() — live sats must not overwrite historical positions
  showHistSatsForDay(new Date(warNow).toISOString().slice(0,10));
}

function propagateAndRender(forceRender){
  if(!viewer||typeof satellite==='undefined')return;
  // In timeline mode, only render satellites if user explicitly toggled them
  if(warOn && !forceRender && !(layerOn.spy||layerOn.military)){
    Object.values(satEntities).forEach(e=>{try{viewer.entities.remove(e);}catch{}});
    satEntities={};
    const el=$('s-rend');if(el)el.textContent='TL';
    return;
  }
  clearHistSatEntities();
  Object.values(satEntities).forEach(e=>{try{viewer.entities.remove(e);}catch{}});satEntities={};
  const now=new Date();let rendered=0;
  SATELLITES.forEach(s=>{
    if(!layerOn[s.cat])return;
    try{
      const satrec=satellite.twoline2satrec(s.l1,s.l2),pv=satellite.propagate(satrec,now);
      if(!pv||!pv.position)return;
      const gmst=satellite.gstime(now),pos=satellite.eciToGeodetic(pv.position,gmst);
      const lat=satellite.radiansToDegrees(pos.latitude),lon=satellite.radiansToDegrees(pos.longitude),alt=pos.height;
      if(alt<80||isNaN(lat)||isNaN(lon))return;
      const isSpy=s.cat==='spy'||s.cat==='military';
      let rotation=0;
      try{
        const vel=pv.velocity;
        if(vel){
          const ahead={x:pv.position.x+vel.x*60,y:pv.position.y+vel.y*60,z:pv.position.z+vel.z*60};
          const ag=satellite.eciToGeodetic(ahead,gmst);
          const dLat=satellite.radiansToDegrees(ag.latitude)-lat,dLon=satellite.radiansToDegrees(ag.longitude)-lon;
          rotation=-Math.atan2(dLon,dLat);
        }
      }catch{}
      const col=CAT_COLOR[s.cat]||'#ffd700';
      const ent=viewer.entities.add({
        name:s.name,
        position:Cesium.Cartesian3.fromDegrees(lon,lat,alt*1000),
        billboard:isSpy?{image:SAT_ICONS[s.cat],rotation,alignedAxis:Cesium.Cartesian3.UNIT_Z,scaleByDistance:SAT_SCALE[s.cat],translucencyByDistance:new Cesium.NearFarScalar(1e5,1.0,5e7,0.4),verticalOrigin:Cesium.VerticalOrigin.CENTER,horizontalOrigin:Cesium.HorizontalOrigin.CENTER,disableDepthTestDistance:Number.POSITIVE_INFINITY}:undefined,
        point:!isSpy?{pixelSize:5,color:Cesium.Color.fromCssColorString(col).withAlpha(0.95),outlineColor:Cesium.Color.WHITE.withAlpha(0.8),outlineWidth:1,scaleByDistance:SAT_SCALE[s.cat],disableDepthTestDistance:Number.POSITIVE_INFINITY}:undefined,
        label:isSpy?{text:s.name,font:'600 11px Inter,sans-serif',fillColor:Cesium.Color.WHITE,outlineColor:Cesium.Color.BLACK,outlineWidth:3,style:Cesium.LabelStyle.FILL_AND_OUTLINE,pixelOffset:new Cesium.Cartesian2(0,-22),distanceDisplayCondition:new Cesium.DistanceDisplayCondition(0,10e6),disableDepthTestDistance:Number.POSITIVE_INFINITY,showBackground:true,backgroundColor:Cesium.Color.fromCssColorString('#12000a').withAlpha(0.82),backgroundPadding:new Cesium.Cartesian2(5,3)}:undefined,
        description:''
      });
      // FIX: tag with _satData so click handler can show popup
      ent._satData={name:s.name,norad:s.norad||'',cat:s.cat,alt:Math.round(alt),lat:lat.toFixed(2),lon:lon.toFixed(2)};
      satEntities[s.norad]=ent;
      rendered++;
    }catch{}
  });
  const el=$('s-rend');if(el)el.textContent=rendered;
}

function initControls(){
  const CAM=viewer.camera,alt=()=>Cesium.Cartographic.fromCartesian(CAM.position).height;
  const _on=(id,fn)=>{const e=$(id);if(e)e.addEventListener('click',fn);};
  _on('btn-zi',()=>CAM.zoomIn(alt()*0.35));_on('btn-zo',()=>CAM.zoomOut(alt()*0.5));_on('btn-rl',()=>CAM.rotateLeft(Cesium.Math.toRadians(20)));_on('btn-rr',()=>CAM.rotateRight(Cesium.Math.toRadians(20)));_on('btn-up',()=>CAM.lookUp(Cesium.Math.toRadians(10)));_on('btn-dn',()=>CAM.lookDown(Cesium.Math.toRadians(10)));
  const _brs=$('btn-rs');if(_brs)_brs.addEventListener('click',()=>CAM.flyTo({destination:Cesium.Cartesian3.fromDegrees(50,20,19000000),orientation:{heading:0,pitch:Cesium.Math.toRadians(-90),roll:0},duration:1.2}));
  const _btop=$('btn-top');if(_btop)_btop.addEventListener('click',()=>{const p=Cesium.Cartographic.fromCartesian(CAM.position);CAM.flyTo({destination:Cesium.Cartesian3.fromRadians(p.longitude,p.latitude,p.height),orientation:{heading:CAM.heading,pitch:Cesium.Math.toRadians(-90),roll:0},duration:.7});});
  const _bobs=$('btn-obs');if(_bobs)_bobs.addEventListener('click',()=>{const p=Cesium.Cartographic.fromCartesian(CAM.position);CAM.flyTo({destination:Cesium.Cartesian3.fromRadians(p.longitude,p.latitude,p.height),orientation:{heading:CAM.heading,pitch:Cesium.Math.toRadians(-45),roll:0},duration:.7});});
  const _bside=$('btn-side');if(_bside)_bside.addEventListener('click',()=>{const p=Cesium.Cartographic.fromCartesian(CAM.position);CAM.flyTo({destination:Cesium.Cartesian3.fromRadians(p.longitude,p.latitude,p.height),orientation:{heading:CAM.heading,pitch:Cesium.Math.toRadians(-12),roll:0},duration:.7});});
  function hold(id,fn,ms=100){let t=null;const el=$(id);if(!el)return;const go=()=>{fn();t=setInterval(fn,ms)};const stop=()=>clearInterval(t);el.addEventListener('mousedown',go);el.addEventListener('touchstart',go,{passive:true});el.addEventListener('mouseup',stop);el.addEventListener('mouseleave',stop);el.addEventListener('touchend',stop);}
  hold('btn-zi',()=>CAM.zoomIn(alt()*0.06));hold('btn-zo',()=>CAM.zoomOut(alt()*0.06));hold('btn-rl',()=>CAM.rotateLeft(Cesium.Math.toRadians(3)));hold('btn-rr',()=>CAM.rotateRight(Cesium.Math.toRadians(3)));hold('btn-up',()=>CAM.lookUp(Cesium.Math.toRadians(2)));hold('btn-dn',()=>CAM.lookDown(Cesium.Math.toRadians(2)));}



function _inZone(lat,lon,zone){
  const la=parseFloat(lat),lo=parseFloat(lon);
  if(isNaN(la)||isNaN(lo))return false;
  return la>=zone.lat[0]&&la<=zone.lat[1]&&lo>=zone.lon[0]&&lo<=zone.lon[1];
}




var _histSatEntities=[];
function clearHistSatEntities(){_histSatEntities.forEach(e=>{try{viewer.entities.remove(e);}catch{}});_histSatEntities=[];}

function showHistSatsForDay(dateStr){
  if(!HIST_SAT_DATA||!HIST_SAT_DATA.days||!dateStr)return;
  const de=HIST_SAT_DATA.days.find(d=>d.date===dateStr);
  if(!de)return;
  const ne=$('iran-now');if(ne)ne.textContent=de.iran_count||0;
  if(!viewer)return;
  clearHistSatEntities();
  const sats=de.satellites||[];
  sats.forEach(s=>{
    if(s.lat==null||s.lon==null||s.alt_km==null)return;
    if(!layerOn[s.cat])return;
    const col=CAT_COLOR[s.cat]||'#ffd700';
    const isSpy=s.cat==='spy'||s.cat==='military';
    const ent=viewer.entities.add({
      name:s.name,
      position:Cesium.Cartesian3.fromDegrees(s.lon,s.lat,s.alt_km*1000),
      billboard:isSpy?{
        image:SAT_ICONS[s.cat]||SAT_ICONS.spy,
        rotation:0,
        alignedAxis:Cesium.Cartesian3.UNIT_Z,
        scaleByDistance:SAT_SCALE[s.cat]||SAT_SCALE.spy,
        translucencyByDistance:new Cesium.NearFarScalar(1e5,1.0,5e7,0.4),
        verticalOrigin:Cesium.VerticalOrigin.CENTER,
        horizontalOrigin:Cesium.HorizontalOrigin.CENTER,
        disableDepthTestDistance:Number.POSITIVE_INFINITY
      }:undefined,
      // FIX: pixelSize 4->9, white outline for visibility on satellite imagery
      point:!isSpy?{
        pixelSize:9,
        color:Cesium.Color.fromCssColorString(col).withAlpha(1.0),
        outlineColor:Cesium.Color.WHITE.withAlpha(0.9),
        outlineWidth:2,
        scaleByDistance:SAT_SCALE[s.cat]||SAT_SCALE.leo,
        disableDepthTestDistance:Number.POSITIVE_INFINITY
      }:undefined,
      // FIX: white fill + black outline instead of faint yellow on imagery
      label:isSpy?{
        text:s.name,
        font:'600 12px Inter,sans-serif',
        fillColor:Cesium.Color.WHITE,
        outlineColor:Cesium.Color.BLACK,
        outlineWidth:3,
        style:Cesium.LabelStyle.FILL_AND_OUTLINE,
        pixelOffset:new Cesium.Cartesian2(0,-22),
        distanceDisplayCondition:new Cesium.DistanceDisplayCondition(0,8e6),
        disableDepthTestDistance:Number.POSITIVE_INFINITY,
        showBackground:true,
        backgroundColor:Cesium.Color.fromCssColorString('#12000a').withAlpha(0.82),
        backgroundPadding:new Cesium.Cartesian2(5,3)
      }:undefined,
      description:''
    });
    // FIX: tag with _satData so click handler can show popup
    ent._satData={
      name:s.name,
      norad:s.norad||'',
      cat:s.cat,
      alt:Math.round(s.alt_km),
      lat:typeof s.lat==='number'?s.lat.toFixed(2):s.lat,
      lon:typeof s.lon==='number'?s.lon.toFixed(2):s.lon
    };
    _histSatEntities.push(ent);
  });
}

var _histFltEntities=[];
function clearHistFltEntities(){_histFltEntities.forEach(e=>{try{viewer.entities.remove(e);}catch{}});_histFltEntities=[];}

function showFlightsForDay(){
  // Flights are current data only — show them on globe and fly to region
  if(!civFlightsOn){toggleCivFlights();}
  if(viewer){viewer.camera.flyTo({
    destination:Cesium.Cartesian3.fromDegrees(50,28,3500000),
    duration:1.8,easingFunction:Cesium.EasingFunction.CUBIC_IN_OUT
  });}
}
function renderBriefingFeed(){
  const feed=$('briefing-feed');if(!feed)return;
  const data=TELEGRAM_DATA;
  const ftEl=$('tg-fetch-time');
  if(!data||data.error||!data.messages||!data.messages.length){
    feed.innerHTML='<div class="briefing-error">\u062a\u0639\u0630\u0651\u0631 \u062a\u062d\u0645\u064a\u0644 \u0627\u0644\u062a\u063a\u0630\u064a\u0629.<br><br><a href="https://t.me/iranmonitor_org" target="_blank">\u2197 \u0627\u0644\u0642\u0646\u0627\u0629</a></div>';
    return;}
  if(ftEl)ftEl.textContent=data.fetched_at?data.fetched_at.slice(0,16).replace('T',' ')+' UTC':'\u2014';

  // Filter to Morning Briefing only
  var briefs=data.messages.filter(function(m){
    return (m.text||'').indexOf('Morning Briefing')>=0 || (m.text||'').indexOf('Morning Brief')>=0;
  });

  if(!briefs.length){
    feed.innerHTML='<div style="padding:12px;text-align:center;color:var(--text-muted);font-size:12px;">\u0644\u0627 \u062a\u0648\u062c\u062f \u0625\u062d\u0627\u0637\u0629 \u0635\u0628\u0627\u062d\u064a\u0629 \u062d\u0627\u0644\u064a\u0627\u064b<br><a href="https://t.me/iranmonitor_org" target="_blank" style="color:var(--burg-500);">\u2197 \u0627\u0644\u0642\u0646\u0627\u0629</a></div>';
    return;
  }

  feed.innerHTML=briefs.map(function(msg){
    var url=msg.url||'https://t.me/iranmonitor_org';
    var raw=(msg.text||'');
    // Extract title
    var dashIdx=raw.indexOf(' The ');
    if(dashIdx<0) dashIdx=raw.indexOf('. ');
    var title=dashIdx>0?raw.slice(0,dashIdx).trim():'Morning Briefing';
    var body=dashIdx>0?raw.slice(dashIdx+1).trim():raw;
    body=body.replace(/</g,'&lt;').replace(/>/g,'&gt;');
    // Split into sentences for readability
    var sentences=body.split(/(?<=[.!?])\\s+/).filter(function(s){return s.length>10;});

    return '<div style="padding:12px 10px;border-bottom:1px solid var(--ui-border2);">'
      +'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
      +'<span style="font-size:12px;font-weight:700;color:var(--burg-700);">'+title.replace(/</g,'&lt;')+'</span>'
      +'<span style="font-size:9px;color:var(--text-muted);">'+(msg.time||'')+'</span>'
      +'</div>'
      +sentences.map(function(s){
        return '<div style="font-size:11px;color:var(--text-secondary);line-height:1.7;padding:3px 0;border-bottom:1px solid var(--ui-border2);">'+s+'</div>';
      }).join('')
      +'<a href="'+url+'" target="_blank" rel="noopener" style="display:inline-block;margin-top:8px;font-size:10px;color:var(--burg-500);text-decoration:none;">\u2197 \u0627\u0644\u0645\u0635\u062f\u0631</a>'
      +'</div>';
  }).join('');
}
function showEntityInfo(name,subtitle,details,searchQuery){
  const card=$('war-brief-card');if(!card)return;
  clearTimeout(window._wbcTimer);
  const _s=(id,v)=>{const el=$(id);if(el)el.textContent=v;};
  _s('wbc-id','INFO');_s('wbc-time',subtitle);
  const dot=$('wbc-type-dot');if(dot)dot.style.background='#4488ff';
  _s('wbc-type-label',subtitle.toUpperCase());
  const ti=$('wbc-title');
  if(ti){
    ti.innerHTML='<span id="eic-sp" style="user-select:all;cursor:text;font-family:JetBrains Mono,monospace;font-size:13px"></span>'
      +' <button id="eic-btn" style="margin-left:8px;padding:3px 8px;border-radius:4px;border:1px solid #b80038;background:#fff;color:#b80038;cursor:pointer;font-size:12px">Copy</button>';
    const sp=document.getElementById('eic-sp');if(sp)sp.textContent=name;
    const btn=document.getElementById('eic-btn');
    if(btn){btn.setAttribute('data-name',name);btn.onclick=function(){const s=this;navigator.clipboard.writeText(this.getAttribute('data-name')).then(()=>{s.textContent='\u2713';setTimeout(()=>{s.textContent='Copy';},1500);});};}
  }
  const dd=$('wbc-detail');
  if(dd){dd.style.padding='6px 0';dd.style.borderLeft='none';
    dd.innerHTML=details.map(p=>'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #f0e0e8;font-size:12px"><span style="color:#9a6070">'+p[0]+'</span><span style="font-family:JetBrains Mono,monospace;color:#5c0020;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+p[1]+'</span></div>').join('');}
  const mm=$('wbc-meta');
  if(mm){const q=encodeURIComponent(searchQuery||name);const np=details.find(p=>p[0]==='NORAD ID');const nq=np?encodeURIComponent(np[1]):encodeURIComponent(name);
    mm.innerHTML='<a href="https://www.google.com/search?q='+q+'" target="_blank" style="padding:4px 10px;border-radius:4px;background:#4285f4;color:#fff;font-size:12px;text-decoration:none">Google</a>'
      +' <a href="https://www.n2yo.com/?s='+nq+'" target="_blank" style="padding:4px 10px;border-radius:4px;background:#34a853;color:#fff;font-size:12px;text-decoration:none;margin-left:4px">N2YO</a>';}
  card.style.borderLeftColor='#4488ff';card.classList.add('visible');
}

// ═══════════════════════════════════════════════════════════
// SEARCH ENGINE
// ═══════════════════════════════════════════════════════════

function showDayVesselBrief(vlist, dayNum){
  const card=$('war-brief-card');if(!card)return;
  const _s=(id,v)=>{const el=$(id);if(el)el.textContent=v;};
  _s('wbc-id','اليوم '+dayNum);
  _s('wbc-time',vlist.length+' هجوم بحري');
  _s('wbc-type-label','السفن المهاجمة');
  _s('wbc-title','هجمات اليوم '+dayNum);
  const $det=$('wbc-detail');
  if($det){
    $det.style.maxHeight='160px';$det.style.overflowY='auto';
    $det.style.padding='0';$det.style.borderLeft='none';
    $det.innerHTML=vlist.map((v,vi)=>{
      const col=v.col||'#ff4400';
      const icon=v.vessel_category&&v.vessel_category.includes('Naval')?'⚓ ':'[ship] ';
      return '<div data-vi="'+vi+'" class="vessel-day-row" style="padding:6px 8px;border-bottom:1px solid #f0e0e8;cursor:pointer;">'+
        '<div style="font-size:10px;font-weight:600;color:'+col+'">'+icon+(v.vessel_name||'سفينة مجهولة')+'</div>'+
        '<div style="font-size:9px;color:#888">'+(v.location_name||v.zone||'')+'</div>'+
        '</div>';
    }).join('');
    // Wire clicks via event delegation (safe, no inline JS with embedded coords)
    $det.querySelectorAll('.vessel-day-row').forEach(row=>{
      const vi=parseInt(row.getAttribute('data-vi'));
      const v=vlist[vi];
      if(!v)return;
      row.addEventListener('click',()=>{
        if(v.lat&&v.lon&&viewer){
          viewer.camera.flyTo({
            destination:Cesium.Cartesian3.fromDegrees(parseFloat(v.lon),parseFloat(v.lat),500000),
            duration:1.5
          });
        }
        showVesselBrief(v);
      });
    });
  }
  const $meta=$('wbc-meta');if($meta)$meta.innerHTML='<span class="wbc-chip" style="border-color:#ff4400;color:#ff4400">⚓ '+vlist.length+' هجوم</span>';
  card.style.borderLeftColor='#ff4400';
  card.classList.add('visible');
  const fill=$('wbc-progress-fill');if(fill){fill.style.transition='none';fill.style.width='100%';fill.getBoundingClientRect();fill.style.transition='width 10s linear';fill.style.width='0%';}
  clearTimeout(window._wbcTimer);window._wbcTimer=setTimeout(closeWarBrief,10000);
}

const CITY_DB=[
  {n:'Tehran',ar:'\u0637\u0647\u0631\u0627\u0646',lat:35.69,lon:51.39,co:'Iran'},
  {n:'Isfahan',ar:'\u0623\u0635\u0641\u0647\u0627\u0646',lat:32.66,lon:51.68,co:'Iran'},
  {n:'Shiraz',ar:'\u0634\u064a\u0631\u0627\u0632',lat:29.59,lon:52.58,co:'Iran'},
  {n:'Mashhad',ar:'\u0645\u0634\u0647\u062f',lat:36.27,lon:59.57,co:'Iran'},
  {n:'Tabriz',ar:'\u062a\u0628\u0631\u064a\u0632',lat:38.08,lon:46.30,co:'Iran'},
  {n:'Bushehr',ar:'\u0628\u0648\u0634\u0647\u0631',lat:28.97,lon:50.84,co:'Iran'},
  {n:'Natanz',ar:'\u0646\u0637\u0646\u0632',lat:33.52,lon:51.92,co:'Iran'},
  {n:'Fordow',ar:'\u0641\u0648\u0631\u062f\u0648',lat:34.88,lon:50.57,co:'Iran'},
  {n:'Arak',ar:'\u0623\u0631\u0627\u0643',lat:34.09,lon:49.69,co:'Iran'},
  {n:'Bandar Abbas',ar:'\u0628\u0646\u062f\u0631 \u0639\u0628\u0627\u0633',lat:27.19,lon:56.27,co:'Iran'},
  {n:'Parchin',ar:'\u0628\u0627\u0631\u0634\u064a\u0646',lat:35.52,lon:51.77,co:'Iran'},
  {n:'Kharg Island',ar:'\u062c\u0632\u064a\u0631\u0629 \u062e\u0627\u0631\u0643',lat:29.25,lon:50.32,co:'Iran'},
  {n:'Baghdad',ar:'\u0628\u063a\u062f\u0627\u062f',lat:33.34,lon:44.40,co:'Iraq'},
  {n:'Mosul',ar:'\u0627\u0644\u0645\u0648\u0635\u0644',lat:36.34,lon:43.13,co:'Iraq'},
  {n:'Basra',ar:'\u0627\u0644\u0628\u0635\u0631\u0629',lat:30.51,lon:47.82,co:'Iraq'},
  {n:'Erbil',ar:'\u0623\u0631\u0628\u064a\u0644',lat:36.19,lon:44.01,co:'Iraq'},
  {n:'Damascus',ar:'\u062f\u0645\u0634\u0642',lat:33.51,lon:36.29,co:'Syria'},
  {n:'Aleppo',ar:'\u062d\u0644\u0628',lat:36.20,lon:37.16,co:'Syria'},
  {n:'Deir ez-Zor',ar:'\u062f\u064a\u0631 \u0627\u0644\u0632\u0648\u0631',lat:35.34,lon:40.14,co:'Syria'},
  {n:'Tel Aviv',ar:'\u062a\u0644 \u0623\u0628\u064a\u0628',lat:32.08,lon:34.78,co:'Israel'},
  {n:'Jerusalem',ar:'\u0627\u0644\u0642\u062f\u0633',lat:31.77,lon:35.22,co:'Israel'},
  {n:'Haifa',ar:'\u062d\u064a\u0641\u0627',lat:32.82,lon:34.99,co:'Israel'},
  {n:'Dimona',ar:'\u062f\u064a\u0645\u0648\u0646\u0627',lat:31.07,lon:35.03,co:'Israel'},
  {n:'Beirut',ar:'\u0628\u064a\u0631\u0648\u062a',lat:33.89,lon:35.50,co:'Lebanon'},
  {n:'Gaza',ar:'\u063a\u0632\u0629',lat:31.51,lon:34.47,co:'Palestine'},
  {n:'West Bank',ar:'\u0627\u0644\u0636\u0641\u0629 \u0627\u0644\u063a\u0631\u0628\u064a\u0629',lat:32.00,lon:35.25,co:'Palestine'},
  {n:'Sanaa',ar:'\u0635\u0646\u0639\u0627\u0621',lat:15.35,lon:44.21,co:'Yemen'},
  {n:'Hudaydah',ar:'\u0627\u0644\u062d\u062f\u064a\u062f\u0629',lat:14.80,lon:42.95,co:'Yemen'},
  {n:'Marib',ar:'\u0645\u0623\u0631\u0628',lat:15.47,lon:45.33,co:'Yemen'},
  {n:'Aden',ar:'\u0639\u062f\u0646',lat:12.78,lon:45.04,co:'Yemen'},
  {n:'Riyadh',ar:'\u0627\u0644\u0631\u064a\u0627\u0636',lat:24.69,lon:46.72,co:'Saudi Arabia'},
  {n:'Jeddah',ar:'\u062c\u062f\u0629',lat:21.49,lon:39.19,co:'Saudi Arabia'},
  {n:'Najran',ar:'\u0646\u062c\u0631\u0627\u0646',lat:17.49,lon:44.13,co:'Saudi Arabia'},
  {n:'Al Udeid',ar:'\u0642\u0627\u0639\u062f\u0629 \u0627\u0644\u0639\u062f\u064a\u062f',lat:25.12,lon:51.31,co:'Qatar'},
  {n:'Dubai',ar:'\u062f\u0628\u064a',lat:25.20,lon:55.27,co:'UAE'},
  {n:'Abu Dhabi',ar:'\u0623\u0628\u0648\u0638\u0628\u064a',lat:24.47,lon:54.37,co:'UAE'},
  {n:'Al Dhafra',ar:'\u0642\u0627\u0639\u062f\u0629 \u0627\u0644\u0638\u0641\u0631\u0629',lat:24.25,lon:54.55,co:'UAE'},
  {n:'Manama',ar:'\u0627\u0644\u0645\u0646\u0627\u0645\u0629',lat:26.22,lon:50.59,co:'Bahrain'},
  {n:'Kuwait City',ar:'\u0645\u062f\u064a\u0646\u0629 \u0627\u0644\u0643\u0648\u064a\u062a',lat:29.37,lon:47.97,co:'Kuwait'},
  {n:'Muscat',ar:'\u0645\u0633\u0642\u0637',lat:23.59,lon:58.41,co:'Oman'},
  {n:'Amman',ar:'\u0639\u0645\u0651\u0627\u0646',lat:31.95,lon:35.93,co:'Jordan'},
  {n:'Cairo',ar:'\u0627\u0644\u0642\u0627\u0647\u0631\u0629',lat:30.06,lon:31.25,co:'Egypt'},
  {n:'Ankara',ar:'\u0623\u0646\u0642\u0631\u0629',lat:39.93,lon:32.85,co:'Turkey'},
  {n:'Baku',ar:'\u0628\u0627\u0643\u0648',lat:40.41,lon:49.87,co:'Azerbaijan'},
  {n:'Kabul',ar:'\u0643\u0627\u0628\u0648\u0644',lat:34.53,lon:69.17,co:'Afghanistan'},
  {n:'Strait of Hormuz',ar:'\u0645\u0636\u064a\u0642 \u0647\u0631\u0645\u0632',lat:26.56,lon:56.45,co:'Strategic'},
  {n:'Bab el-Mandeb',ar:'\u0628\u0627\u0628 \u0627\u0644\u0645\u0646\u062f\u0628',lat:12.58,lon:43.37,co:'Strategic'},
  {n:'Suez Canal',ar:'\u0642\u0646\u0627\u0629 \u0627\u0644\u0633\u0648\u064a\u0633',lat:30.58,lon:32.33,co:'Strategic'},
];

var _srIdx=-1,_srItems=[];

function _srNorm(s){return (s||'').toLowerCase().trim();}

function renderSearchDropdown(results){
  const body=$('search-results-body');
  const emptyEl=$('search-empty');
  const dd=$('search-dropdown');
  if(!body||!dd)return;
  if(!results||!results.length){
    body.innerHTML='';
    if(emptyEl)emptyEl.style.display='block';
    dd.style.display='block';dd.classList.add('open');
    _srItems=[];_srIdx=-1;
    return;
  }
  if(emptyEl)emptyEl.style.display='none';
  const order=['ship','sat','flt','war','loc','intel'];
  const groupNames={
    ship:'\u0633\u0641\u0646',
    sat:'\u0623\u0642\u0645\u0627\u0631 \u0627\u0635\u0637\u0646\u0627\u0639\u064a\u0629',
    flt:'\u0631\u062d\u0644\u0627\u062a',
    war:'\u0623\u062d\u062f\u0627\u062b \u0627\u0644\u062d\u0631\u0628',
    loc:'\u0645\u062f\u0646 \u0648\u0645\u0648\u0627\u0642\u0639',
    intel:'\u0645\u0648\u0627\u0642\u0639 \u0627\u0633\u062a\u062e\u0628\u0627\u0631\u0627\u062a\u064a\u0629'
  };
  const groups={};
  results.forEach(r=>{if(!groups[r.type])groups[r.type]=[];groups[r.type].push(r);});
  var html='';_srItems=[];
  order.forEach(type=>{
    const items=groups[type];if(!items||!items.length)return;
    html+='<div class="sr-group-head">'+groupNames[type]+'</div>';
    items.forEach(r=>{
      const idx=_srItems.length;_srItems.push(r);
      html+='<div class="sr-item" data-idx="'+idx+'" onclick="selectSearchResult('+idx+')">'
        +'<span class="sr-cat '+type+'">'+r.catLabel+'</span>'
        +'<span class="sr-name">'+r.label+'</span>'
        +'<span class="sr-sub">'+r.sub+'</span>'
        +'</div>';
    });
  });
  body.innerHTML=html;
  // Position dropdown below search bar (fixed positioning)
  var wrap=$('search-wrap');
  if(wrap){
    var rect=wrap.getBoundingClientRect();
    dd.style.top=rect.bottom+'px';
    dd.style.left=rect.left+'px';
    dd.style.width=rect.width+'px';
  }
  dd.style.display='block';dd.classList.add('open');
  _srIdx=-1;
}

function selectSearchResult(idx){
  const r=_srItems[idx];if(!r||!viewer)return;
  closeSearchDropdown();
  const inp=$('search-input');if(inp)inp.value='';
  const cl=$('search-clear');if(cl)cl.style.display='none';

  if(r.type==='sat'){
    const s=r.satObj;
    if(s&&typeof satellite!=='undefined'){
      try{
        const rec=satellite.twoline2satrec(s.l1,s.l2),pv=satellite.propagate(rec,new Date());
        if(pv&&pv.position){
          const gmst=satellite.gstime(new Date()),pos=satellite.eciToGeodetic(pv.position,gmst);
          const lat=satellite.radiansToDegrees(pos.latitude),lon=satellite.radiansToDegrees(pos.longitude),alt=pos.height;
          viewer.camera.flyTo({destination:Cesium.Cartesian3.fromDegrees(lon,lat,alt*1000+700000),duration:1.8,easingFunction:Cesium.EasingFunction.CUBIC_IN_OUT});
          showEntityInfo(s.name,s.cat.toUpperCase()+' SATELLITE',
            [['NORAD ID',s.norad],['Category',s.cat],['Altitude',Math.round(alt)+' km']],
            s.name+' satellite NORAD '+s.norad);
        }
      }catch(e){console.warn('sat search fly error',e);}
    }
  }
  else if(r.type==='flt'){
    if(!civFlightsOn)toggleCivFlights();
    viewer.camera.flyTo({
      destination:Cesium.Cartesian3.fromDegrees(r.lon,r.lat,r.alt+300000),
      duration:1.8,easingFunction:Cesium.EasingFunction.CUBIC_IN_OUT
    });
    const a=r.fltObj;
    showEntityInfo(r.label,(a.ac_type||'FLIGHT').toUpperCase(),
      [['Callsign',a.callsign||'\u2014'],['ICAO',a.icao||'\u2014'],['Type',a.ac_type||'\u2014'],
       ['Altitude',a.alt_ft?a.alt_ft.toLocaleString()+' ft':'\u2014'],['FIR',a.fir_name||a.fir||'\u2014']],
      r.label+' flight');
  }
  else if(r.type==='war'){
    warSeekTo(r.evIdx,true);
  }
  else if(r.type==='ship'){
    // Hide marine layer so gold arrow stands out
    if(marineOn){toggleMarine();}
    // Remove previous search highlight if any
    if(window._searchHighlight){try{viewer.entities.remove(window._searchHighlight);}catch(e){}}
    window._searchHighlight=null;

    var lat=parseFloat(r.lat), lon=parseFloat(r.lon);
    if(!lat||!lon||isNaN(lat)||isNaN(lon)){
      console.warn('Ship has no coordinates:',r.label);
      // Still show info card even without coordinates
      var v=r.shipObj;
      showEntityInfo(r.label,(v.type_specific||v.type||'VESSEL').toUpperCase(),
        [['MMSI',v.mmsi||'\u2014'],['Flag',v.flag||'\u2014'],['Type',v.type_specific||v.type||'\u2014']],
        r.label+' vessel');
      return;
    }

    // Normal ship icon + gold perimeter ring
    var v=r.shipObj;
    var cat=v.category||'other';
    var shipIcon=SHIP_ICONS[cat]||SHIP_ICONS.other;
    if(cat==='military'||cat==='warship')shipIcon=SHIP_ICONS.warship;
    var shipHeading=parseFloat(v.heading)||0;

    // Ship arrow — normal size, same as all other vessels
    window._searchHighlight=viewer.entities.add({
      name:'SEARCH: '+r.label,
      position:Cesium.Cartesian3.fromDegrees(lon,lat,0),
      billboard:{
        image:shipIcon,
        rotation:-Cesium.Math.toRadians(shipHeading),
        alignedAxis:Cesium.Cartesian3.UNIT_Z,
        width:20,height:28,
        verticalOrigin:Cesium.VerticalOrigin.CENTER,
        horizontalOrigin:Cesium.HorizontalOrigin.CENTER,
        heightReference:Cesium.HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance:Number.POSITIVE_INFINITY,
        scaleByDistance:new Cesium.NearFarScalar(2e5,1.6,8e6,0.5)
      },
      label:{
        text:r.label,
        font:'700 12px Inter,sans-serif',
        fillColor:Cesium.Color.WHITE,
        outlineColor:Cesium.Color.fromCssColorString('#b8860b'),
        outlineWidth:3,
        style:Cesium.LabelStyle.FILL_AND_OUTLINE,
        pixelOffset:new Cesium.Cartesian2(0,-24),
        showBackground:true,
        backgroundColor:Cesium.Color.fromCssColorString('#b8860b').withAlpha(0.85),
        backgroundPadding:new Cesium.Cartesian2(6,3),
        disableDepthTestDistance:Number.POSITIVE_INFINITY
      },
      ellipse:{
        semiMajorAxis:3000,
        semiMinorAxis:3000,
        height:0,
        material:Cesium.Color.fromCssColorString('#ffd700').withAlpha(0.08),
        outline:true,
        outlineColor:Cesium.Color.fromCssColorString('#ffd700').withAlpha(0.9),
        outlineWidth:3
      },
    });
    // Tag with marine data so click handler works
    window._searchHighlight._marineData=r.shipObj;

    // Fly to the vessel
    viewer.camera.flyTo({
      destination:Cesium.Cartesian3.fromDegrees(lon,lat,30000),
      duration:2.0,easingFunction:Cesium.EasingFunction.CUBIC_IN_OUT
    });

    // Auto-remove highlight after 60 seconds
    setTimeout(function(){
      if(window._searchHighlight&&!marineOn){
        try{viewer.entities.remove(window._searchHighlight);}catch(e){}
        window._searchHighlight=null;
      }
    },60000);

    // Show rich info card
    var v=r.shipObj;
    var details=[];
    details.push(['MMSI',v.mmsi||'\u2014']);
    if(v.imo)details.push(['IMO',v.imo]);
    if(v.callsign)details.push(['Callsign',v.callsign]);
    details.push(['Name',v.name||'\u2014']);
    details.push(['Type',v.type_specific||v.type||'\u2014']);
    details.push(['Category',v.category||'\u2014']);
    details.push(['Flag',v.flag+(v.country_name?' ('+v.country_name+')':'')]);
    if(v.beneficial_owner)details.push(['Owner',v.beneficial_owner]);
    if(v.owner_country)details.push(['Owner Country',v.owner_country]);
    if(v.operator)details.push(['Operator',v.operator]);
    details.push(['Position',lat.toFixed(3)+', '+lon.toFixed(3)]);
    details.push(['Speed',v.speed?v.speed+' kts'+(v.speed_max?' (max '+v.speed_max+')':''):'\u2014']);
    if(v.course)details.push(['Course',v.course+'\u00b0']);
    if(v.heading)details.push(['Heading',v.heading+'\u00b0']);
    if(v.nav_status)details.push(['Status',v.nav_status]);
    details.push(['Destination',v.destination||v.dest||'\u2014']);
    if(v.eta_utc)details.push(['ETA',v.eta_utc.replace('T',' ').slice(0,16)]);
    if(v.length)details.push(['Size',v.length+'m x '+(v.breadth||'?')+'m']);
    if(v.gross_tonnage)details.push(['Gross Tonnage',Number(v.gross_tonnage).toLocaleString()+' GT']);
    if(v.deadweight)details.push(['Deadweight',Number(v.deadweight).toLocaleString()+' DWT']);
    if(v.teu)details.push(['TEU Capacity',Number(v.teu).toLocaleString()]);
    if(v.draught)details.push(['Draught',v.draught+'m']);
    if(v.year_built)details.push(['Built',v.year_built]);
    details.push(['Zone',v.zone_name||v.zone||'\u2014']);
    if(v.last_pos_utc)details.push(['Last AIS',v.last_pos_utc.replace('T',' ').slice(0,16)]);
    if(v.going_dark)details.push(['\u26a0 STATUS','DARK - AIS OFF >2hrs']);
    if(v.sat_e_lat)details.push(['SAT-E Est.',v.sat_e_lat+', '+v.sat_e_lon]);
    if(v.distance_km)details.push(['Distance',Math.round(v.distance_km)+' km']);

    var subtitle=(v.category==='military'||v.category==='warship'?'\u2693 ':'')+((v.type_specific||v.type||'VESSEL')).toUpperCase();
    if(v.flag)subtitle+=' \u00b7 '+flagEmoji(v.flag)+' '+v.flag;
    showEntityInfo(r.label,subtitle,details, r.label+' vessel ship '+v.mmsi);
  }
  else if(r.type==='loc'||r.type==='intel'){
    viewer.camera.flyTo({
      destination:Cesium.Cartesian3.fromDegrees(r.lon,r.lat,200000),
      duration:1.8,easingFunction:Cesium.EasingFunction.CUBIC_IN_OUT
    });
    const card=$('war-brief-card');
    if(card){
      const _s=(id,v)=>{const el=$(id);if(el)el.textContent=v;};
      _s('wbc-id',r.type==='intel'?r.catLabel:'CITY');
      _s('wbc-time',r.sub);
      _s('wbc-type-label',r.type==='intel'?'INTEL SITE':'LOCATION');
      _s('wbc-title',r.label);
      const dd=$('wbc-detail');if(dd){dd.style.padding='';dd.style.borderLeft='';dd.textContent=r.sub;}
      const mm=$('wbc-meta');
      if(mm){const q=encodeURIComponent(r.label);mm.innerHTML='<a href="https://www.google.com/maps/search/'+q+'" target="_blank" rel="noopener" style="padding:4px 10px;border-radius:4px;background:#4285f4;color:#fff;font-size:12px;text-decoration:none">Google Maps</a>';}
      card.style.borderLeftColor='var(--burg-400)';card.classList.add('visible');
      const fill=$('wbc-progress-fill');
      if(fill){fill.style.transition='none';fill.style.width='100%';fill.getBoundingClientRect();fill.style.transition='width 8s linear';fill.style.width='0%';}
      clearTimeout(window._wbcTimer);window._wbcTimer=setTimeout(closeWarBrief,8000);
    }
  }
}

function highlightSearchItem(newIdx){
  const items=document.querySelectorAll('.sr-item');
  items.forEach(el=>el.classList.remove('sr-active'));
  if(newIdx>=0&&newIdx<_srItems.length){
    _srIdx=newIdx;
    const el=document.querySelector('.sr-item[data-idx="'+newIdx+'"]');
    if(el){el.classList.add('sr-active');el.scrollIntoView({block:'nearest'});}
  }
}

function onSearchInput(val){
  const cl=$('search-clear');if(cl)cl.style.display=val?'inline':'none';
  const kbd=$('search-kbd');if(kbd)kbd.style.display=val?'none':'inline';
  if(!val||val.length<2){closeSearchDropdown();return;}
  const results=buildSearchResults(val,_searchTab);
  renderSearchDropdown(results);
}

function onSearchFocus(){
  const inp=$('search-input');
  if(inp&&inp.value&&inp.value.length>=2){
    const results=buildSearchResults(inp.value,_searchTab);
    renderSearchDropdown(results);
  }
}

function onSearchKey(e){
  const dd=$('search-dropdown');
  if(e.key==='Escape'){closeSearchDropdown();const inp=$('search-input');if(inp)inp.blur();return;}
  if(e.key==='ArrowDown'){e.preventDefault();highlightSearchItem(_srIdx+1);return;}
  if(e.key==='ArrowUp'){e.preventDefault();highlightSearchItem(Math.max(0,_srIdx-1));return;}
  if(e.key==='Enter'){
    e.preventDefault();
    if(_srIdx>=0&&_srIdx<_srItems.length)selectSearchResult(_srIdx);
    else if(_srItems.length>0)selectSearchResult(0);
    return;}
}

function closeSearchDropdown(){
  const dd=$('search-dropdown');if(dd){dd.classList.remove('open');dd.style.display='none';}
  _srIdx=-1;
}

function clearSearch(){
  const inp=$('search-input');if(inp)inp.value='';
  const cl=$('search-clear');if(cl)cl.style.display='none';
  const kbd=$('search-kbd');if(kbd)kbd.style.display='inline';
  closeSearchDropdown();
  const inp2=$('search-input');if(inp2)inp2.focus();
}

// Close dropdown when clicking outside
document.addEventListener('click',function(e){
  const wrap=$('search-wrap');
  if(wrap&&!wrap.contains(e.target))closeSearchDropdown();
});

// Keyboard shortcut: / to focus search
document.addEventListener('keydown',function(e){
  if(e.key==='/'&&e.target.tagName!=='INPUT'&&e.target.tagName!=='TEXTAREA'){
    e.preventDefault();
    const inp=$('search-input');if(inp){inp.focus();inp.select();}
  }
});


// ── Print Analytics — opens clean page with charts as images ──
function printAnalytics(){
  var body = $('an-body');
  if(!body) return;

  // 1. Convert all canvases to images
  var canvases = body.querySelectorAll('canvas');
  var imgMap = {};
  canvases.forEach(function(c){
    try{ imgMap[c.id] = c.toDataURL('image/png'); }catch(e){}
  });

  // 2. Clone the analytics content
  var clone = body.cloneNode(true);

  // 3. Replace canvases with images in the clone
  clone.querySelectorAll('canvas').forEach(function(c){
    if(imgMap[c.id]){
      var img = document.createElement('img');
      img.src = imgMap[c.id];
      img.style.cssText = 'width:100%;max-height:400px;object-fit:contain;';
      c.parentNode.replaceChild(img, c);
    }
  });

  // 4. Remove buttons and loaders
  clone.querySelectorAll('button, #report-loader, #report-status, #report-steps').forEach(function(el){
    el.remove();
  });

  // 5. Build clean HTML page
  var html = '<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8">'
    + '<title>لوحة التحليلات — طباعة</title>'
    + '<style>'
    + '* { box-sizing:border-box; margin:0; padding:0; }'
    + 'body { font-family:"Noto Naskh Arabic",serif; direction:rtl; color:#0f172a; font-size:13px; line-height:1.6; padding:20px 30px; }'
    + '.an-section { margin-bottom:16px; page-break-inside:avoid; }'
    + '.an-section-title { font-size:15px; font-weight:800; color:#7a0028; margin-bottom:8px; padding-bottom:6px; border-bottom:3px solid #c0406a; display:flex; align-items:center; gap:6px; }'
    + '.an-section-title::before { content:""; display:block; width:4px; height:16px; background:#c0406a; border-radius:2px; flex-shrink:0; }'
    + '.an-card { background:#fff; border-radius:8px; padding:14px 16px; margin-bottom:10px; border:1px solid #e8d0d8; page-break-inside:avoid; }'
    + '.an-card-title { font-size:11px; font-weight:700; color:#7a0028; margin-bottom:8px; }'
    + '.an-grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:10px; }'
    + '.an-grid-3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-bottom:10px; }'
    + '.an-stat-card { text-align:center; padding:12px; }'
    + '.an-stat-value { font-family:monospace; font-size:22px; font-weight:800; color:#7a0028; }'
    + '.an-stat-label { font-size:10px; color:#666; margin-top:3px; }'
    + '.an-bar-row { display:flex; align-items:center; gap:6px; padding:3px 0; border-bottom:1px solid #f0e0e8; }'
    + '.an-bar-label { font-size:10px; color:#333; width:120px; flex-shrink:0; text-align:right; }'
    + '.an-bar-wrap { flex:1; background:#f0e0e8; border-radius:3px; height:12px; overflow:hidden; }'
    + '.an-bar-fill { height:100%; border-radius:3px; }'
    + '.an-bar-value { font-family:monospace; font-size:10px; font-weight:700; color:#7a0028; width:35px; text-align:left; }'
    + '.an-coincidence { padding:8px 10px; background:#faf5f7; border-radius:6px; margin-bottom:6px; border-right:3px solid #cc6600; }'
    + '.an-score-badge { display:inline-block; padding:3px 12px; border-radius:5px; font-size:12px; font-weight:700; }'
    + '.an-score-badge.low { background:rgba(40,120,64,.12); color:#287840; }'
    + '.an-score-badge.medium { background:rgba(200,120,0,.12); color:#c87800; }'
    + '.an-score-badge.high { background:rgba(184,0,56,.12); color:#b80038; }'
    + '.an-score-badge.critical { background:rgba(255,26,94,.15); color:#ff1a5e; }'
    + 'table { width:100%; border-collapse:collapse; font-size:11px; }'
    + 'th { text-align:right; padding:5px 6px; font-size:10px; font-weight:700; color:#7a0028; background:#faf5f7; border-bottom:2px solid #e8d0d8; }'
    + 'td { padding:4px 6px; border-bottom:1px solid #f0e0e8; }'
    + 'img { max-width:100%; height:auto; }'
    + 'svg { max-width:100%; }'
    + '@media print { body { padding:10px 15px; } .an-grid-2, .an-grid-3 { display:block; } .an-grid-2 > *, .an-grid-3 > * { margin-bottom:8px; } }'
    + '</style></head><body>'
    + '<div style="text-align:center;margin-bottom:16px;padding:14px;background:linear-gradient(135deg,#3a0012,#7a0028);color:#fff;border-radius:8px;">'
    + '<div style="font-size:18px;font-weight:700;">لوحة التحليلات</div>'
    + '<div style="font-size:11px;opacity:.8;">منظومة الدمج الاستخباري · ' + new Date().toLocaleDateString('ar-SA') + '</div>'
    + '</div>'
    + clone.innerHTML
    + '<div style="margin-top:16px;padding:8px;border-top:1px solid #e8d0d8;font-size:9px;color:#999;text-align:center;">'
    + 'منظومة الدمج الاستخباري · ' + new Date().toISOString().slice(0,10)
    + '</div>'
    + '</body></html>';

  // 6. Open new window and print
  var w = window.open('', '_blank');
  w.document.write(html);
  w.document.close();
  setTimeout(function(){ w.print(); }, 500);
}

// ── Marine layer ──────────────────────────────────────────────
// Ship icons use the classic AIS maritime arrow style:
// pointed bow at top, wider stern at bottom, rotated to heading.
// Colour-coded by vessel type matching MarineTraffic convention.

// Flag emoji helper
function flagEmoji(code){
  if(!code||code.length!==2)return '';
  try{var a=code.toUpperCase().charCodeAt(0)-65+0x1F1E6,b=code.toUpperCase().charCodeAt(1)-65+0x1F1E6;return String.fromCodePoint(a,b);}catch(e){return '';}
}
var marineOn=false,marineEntities=[];

function makeShipIcon(fillCol,strokeCol,sz){
  sz=sz||20;
  // AIS-style elongated diamond/arrow: pointed bow (top), flat stern (bottom)
  // viewBox 20x28 — bow at top centre, stern at bottom
  const svg='<svg xmlns="http://www.w3.org/2000/svg" width="'+sz+'" height="'+Math.round(sz*1.4)+'" viewBox="0 0 20 28">'
    // main hull: pointed at top, flat cut at bottom
    +'<polygon points="10,1 18,22 10,18 2,22" fill="'+fillCol+'" stroke="'+strokeCol+'" stroke-width="1.5" stroke-linejoin="round"/>'
    // stern transom line
    +'<line x1="4" y1="22" x2="16" y2="22" stroke="'+strokeCol+'" stroke-width="1.2"/>'
    +'</svg>';
  return 'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);
}

// Colour scheme matches MarineTraffic convention:
// tanker=green, cargo=dark green, warship=grey, passenger=blue,
// highspeed=orange, other=light grey
const SHIP_ICONS={
  tanker:    makeShipIcon('#2ecc40','#1a7a25',20),   // green
  cargo:     makeShipIcon('#01a300','#006600',18),   // dark green
  warship:   makeShipIcon('#7f8c8d','#4a5568',18),   // grey
  passenger: makeShipIcon('#3498db','#1a5f8a',18),   // blue
  highspeed: makeShipIcon('#e67e22','#9a4e00',16),   // orange
  other:     makeShipIcon('#bdc3c7','#7f8c8d',14),   // light grey
};
function toggleMarine(){
  marineOn=!marineOn;
  topSyncChip('lchip-marine',marineOn);
  if(marineOn)renderMarine();else clearMarine();
}
function clearMarine(){marineEntities.forEach(e=>{if(e===window._searchHighlight)return;try{viewer.entities.remove(e);}catch(x){}});marineEntities=[];}
function renderMarine(){
  if(!viewer||!MARINE_DATA||!MARINE_DATA.vessels)return;
  clearMarine();
  MARINE_DATA.vessels.forEach(v=>{
    if(!v.lat||!v.lon)return;
    var cat=v.category||'other';
    var icon=SHIP_ICONS[cat]||SHIP_ICONS.other;
    if(cat==='military'||cat==='warship')icon=SHIP_ICONS.warship;
    const heading=Cesium.Math.toRadians(v.heading||0);
    const ent=viewer.entities.add({
      position:Cesium.Cartesian3.fromDegrees(v.lon,v.lat,0),
      billboard:{image:icon,
        // Cesium rotation: 0=up=north, positive=clockwise viewed from above
        // Ship heading 0=north, so rotation = -toRadians(heading)
        rotation:-Cesium.Math.toRadians(v.heading||0),
        alignedAxis:Cesium.Cartesian3.UNIT_Z,
        width:20,height:28,
        verticalOrigin:Cesium.VerticalOrigin.CENTER,
        horizontalOrigin:Cesium.HorizontalOrigin.CENTER,
        heightReference:Cesium.HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance:Number.POSITIVE_INFINITY,
        scaleByDistance:new Cesium.NearFarScalar(2e5,1.6,8e6,0.5),
        translucencyByDistance:new Cesium.NearFarScalar(1e4,1.0,1e7,0.6)},
      description:''
    });
    ent._marineData=v;
    marineEntities.push(ent);
  });
  console.log('[Marine] rendered',marineEntities.length,'vessels');
}

// ── Intel chip shortcut (nuclear from topbar row 3) ───────────
function toggleIntelChip(type){
  toggleIntel(type);
  topSyncChip('lchip-nuclear',intelState[type]);
}

// ── Search tab (Option C) ─────────────────────────────────────
var _searchTab='all';
const SEARCH_PLACEHOLDERS={
  all:  '\u0628\u062d\u062b \u0641\u064a \u0643\u0644 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a\u2026',
  sat:  '\u0627\u0633\u0645 \u0627\u0644\u0642\u0645\u0631 \u0623\u0648 \u0631\u0642\u0645 NORAD\u2026',
  flt:  '\u0631\u0645\u0632 \u0627\u0644\u0631\u062d\u0644\u0629 \u0623\u0648 ICAO\u2026',
  ship: '\u0627\u0633\u0645 \u0627\u0644\u0633\u0641\u064a\u0646\u0629 \u0623\u0648 MMSI\u2026',
  war:  '\u062d\u062f\u062b\u060c \u0645\u0648\u0642\u0639\u060c \u062a\u0641\u0635\u064a\u0644\u2026'
};
function setSearchTab(el,cat){
  document.querySelectorAll('.stab').forEach(t=>t.classList.remove('on'));
  el.classList.add('on');_searchTab=cat;
  const inp=$('search-input');
  if(inp){inp.placeholder=SEARCH_PLACEHOLDERS[cat]||SEARCH_PLACEHOLDERS.sat;inp.focus();}
  const val=inp?inp.value:'';
  if(val&&val.length>=2){const results=buildSearchResults(val,cat);renderSearchDropdown(results);}
  else closeSearchDropdown();
}

// ── Marine vessels in search results ─────────────────────────
function buildSearchResults(q,tab){
  tab=tab||_searchTab;
  if(!q||q.length<2)return[];
  const nq=(q||'').toLowerCase().trim();
  const results=[];
  const want=cat=>tab==='all'||tab===cat;

  if(want('sat')){
    SATELLITES.filter(s=>
      (s.name||'').toLowerCase().includes(nq)||
      String(s.norad).includes(nq)||
      (s.cat||'').toLowerCase().includes(nq)
    ).slice(0,5).forEach(s=>results.push({
      type:'sat',catLabel:'ISR',label:s.name,
      sub:s.norad+' \u00b7 '+s.cat,norad:s.norad,satObj:s
    }));
  }
  if(want('flt')){
    const aircraft=(FLIGHT_DATA&&FLIGHT_DATA.aircraft)||[];
    aircraft.filter(a=>
      (a.callsign||'').toLowerCase().includes(nq)||
      (a.icao||'').toLowerCase().includes(nq)||
      (a.ac_type||'').toLowerCase().includes(nq)
    ).slice(0,4).forEach(a=>results.push({
      type:'flt',catLabel:'FLIGHT',label:a.callsign||a.icao,
      sub:(a.alt_ft?Math.round(a.alt_ft/100)*100+' ft \u00b7 ':'')+( a.fir_name||a.fir||''),
      lat:a.lat,lon:a.lon,alt:a.alt_m||8000,fltObj:a
    }));
  }
  if(want('ship')){
    const vessels=(MARINE_DATA&&MARINE_DATA.vessels)||[];
    // Country name aliases for search
    const _cnames={'us':'us','usa':'us','united states':'us','american':'us','navy':'military',
      'gb':'gb','uk':'gb','united kingdom':'gb','british':'gb','hms':'gb',
      'cn':'cn','china':'cn','chinese':'cn','plan':'cn',
      'ru':'ru','russia':'ru','russian':'ru',
      'il':'il','israel':'il','israeli':'il',
      'military':'_mil','warship':'_mil','naval':'_mil','combat':'_mil',
      'tanker':'_tanker','ناقلة':'_tanker',
      'عسكري':'_mil','أمريكي':'us','بريطاني':'gb','صيني':'cn','روسي':'ru','إسرائيلي':'il',
      'الولايات المتحدة':'us','المملكة المتحدة':'gb','الصين':'cn','روسيا':'ru','إسرائيل':'il'};
    var countryFilter=_cnames[nq]||null;
    var catFilter=null;
    if(countryFilter==='_mil') catFilter='military';
    else if(countryFilter==='_tanker') catFilter='tanker';

    vessels.filter(v=>{
      if(countryFilter && countryFilter!=='_mil' && countryFilter!=='_tanker'){
        return (v.flag||'').toLowerCase()===countryFilter || (v.owner_country||'').toLowerCase().includes(countryFilter);
      }
      if(catFilter){
        return v.category===catFilter || v.category==='warship';
      }
      return (v.name||'').toLowerCase().includes(nq)||
        (v.mmsi||'').includes(nq)||
        (v.type||'').toLowerCase().includes(nq)||
        (v.type_specific||'').toLowerCase().includes(nq)||
        (v.flag||'').toLowerCase().includes(nq)||
        (v.destination||v.dest||'').toLowerCase().includes(nq)||
        (v.category||'').toLowerCase().includes(nq)||
        (v.beneficial_owner||'').toLowerCase().includes(nq)||
        (v.owner_country||'').toLowerCase().includes(nq)||
        (v.flag_country||'').toLowerCase().includes(nq);
    }).slice(0,8).forEach(v=>{
      var catBadge=v.category==='military'||v.category==='warship'?'\u2693 ':'';
      var ownerInfo=v.beneficial_owner?' \u00b7 '+v.beneficial_owner:'';
      results.push({
        type:'ship',catLabel:catBadge+(v.category||'VESSEL').toUpperCase().slice(0,7),
        label:v.name||v.mmsi,
        sub:v.flag+ownerInfo+' \u00b7 '+(v.speed||0)+' kts'+(v.destination||v.dest?' \u2192 '+(v.destination||v.dest):''),
        lat:v.lat,lon:v.lon,shipObj:v
      });
    });
  }
  if(want('war')){
    WEVS.filter(e=>
      ((e.title_ar||e.title||e.label||'')).toLowerCase().includes(nq)||
      (e.location||'').toLowerCase().includes(nq)||
      (e.detail||'').toLowerCase().includes(nq)
    ).slice(0,4).forEach(e=>results.push({
      type:'war',catLabel:'EVENT',
      label:e.title_ar||e.title||e.label||'',
      sub:(e.date||e.t||'').slice(0,10)+' \u00b7 '+(e.location||''),
      evIdx:WEVS.indexOf(e)
    }));
  }
  if(want('loc')){
    CITY_DB.filter(c=>
      c.n.toLowerCase().includes(nq)||c.ar.includes(q)||c.co.toLowerCase().includes(nq)
    ).slice(0,5).forEach(c=>results.push({
      type:'loc',catLabel:'CITY',
      label:c.n+' \u2014 '+c.ar,
      sub:c.co+' \u00b7 '+c.lat.toFixed(1)+'\u00b0 '+c.lon.toFixed(1)+'\u00b0',
      lat:c.lat,lon:c.lon
    }));
  }
  if(want('intel')){
    const sites=(INTEL_DATA&&INTEL_DATA.sites)||[];
    sites.filter(s=>
      (s.name_en||s.name||'').toLowerCase().includes(nq)||
      (s.type||s.category||'').toLowerCase().includes(nq)
    ).slice(0,3).forEach(s=>results.push({
      type:'intel',catLabel:(s.type||s.category||'SITE').toUpperCase().slice(0,8),
      label:s.name_en||s.name,sub:s.country||'',
      lat:s.lat,lon:s.lon
    }));
  }
  return results;
}

// ═══════════════════════════════════════════════════════════
// LIVE LAYER DROPDOWN — centred at top of globe
// ═══════════════════════════════════════════════════════════
var _liveDropOpen = false;

function initLiveDropdown(){
  // Create the trigger button + dropdown and inject into the globe div
  const globe = document.getElementById('globe');
  if(!globe) return;

  const wrap = document.createElement('div');
  wrap.id = 'live-drop-wrap';
  wrap.style.cssText = 'position:absolute;top:0;left:0;right:0;display:flex;flex-direction:column;align-items:center;z-index:500;pointer-events:none;';

  wrap.innerHTML =
    '<div id="live-trigger" onclick="toggleLiveDropdown()" style="'
    + 'display:flex;align-items:center;gap:8px;'
    + 'background:rgba(10,10,28,.88);'
    + 'border:1px solid rgba(0,212,255,.45);'
    + 'border-top:none;border-radius:0 0 8px 8px;'
    + 'padding:5px 18px;cursor:pointer;pointer-events:auto;'
    + 'transition:background .15s,border-color .15s;">'
    + '<div id="live-pulse-dot" style="width:7px;height:7px;border-radius:50%;background:#00d4ff;animation:liveblink 1.5s ease-in-out infinite;flex-shrink:0;"></div>'
    + '<span style="font-size:11px;font-weight:700;color:#00d4ff;letter-spacing:.5px;white-space:nowrap;">بيانات مباشرة</span>'
    + '<span id="live-arrow" style="font-size:10px;color:#00d4ff;transition:transform .2s;">▼</span>'
    + '</div>'
    + '<div id="live-dropdown" style="'
    + 'display:none;flex-direction:column;gap:4px;'
    + 'background:rgba(8,8,22,.95);'
    + 'border:1px solid rgba(0,212,255,.35);'
    + 'border-radius:0 0 8px 8px;border-top:none;'
    + 'padding:8px 10px;min-width:220px;pointer-events:auto;">'
    + _buildLiveItem('ldi-civ',   '#0088cc', 'رحلات جوية',  false, toggleCivFlights)
    + _buildLiveItem('ldi-jam',   '#ff1144', 'تشويش GPS',   false, toggleJamming)
    + _buildLiveItem('ldi-marine','#00b4d8', 'سفن بحرية',   false, toggleMarine)
    + _buildLiveItem('ldi-sat',   '#ffd700', 'أقمار اصطناعية', true, topToggleSatellites)
    + '</div>';

  globe.appendChild(wrap);

  // Wire up click handlers after DOM insert
  document.getElementById('ldi-civ')   .onclick = function(){ toggleCivFlights();    syncLiveItem('ldi-civ',   civFlightsOn); };
  document.getElementById('ldi-jam')   .onclick = function(){ toggleJamming();       syncLiveItem('ldi-jam',   jammingOn);    };
  document.getElementById('ldi-marine').onclick = function(){ toggleMarine();         syncLiveItem('ldi-marine',marineOn);     };
  document.getElementById('ldi-sat')   .onclick = function(){ topToggleSatellites(); syncLiveItem('ldi-sat',   layerOn.spy||layerOn.military); };
}

function _buildLiveItem(id, color, label, isOn, fn){
  return '<div id="' + id + '" style="'
    + 'display:flex;align-items:center;gap:8px;padding:6px 10px;'
    + 'border-radius:5px;cursor:pointer;border:1px solid transparent;'
    + 'transition:all .12s;margin-bottom:2px;'
    + (isOn ? 'background:rgba(0,212,255,.10);border-color:rgba(0,212,255,.3);' : '')
    + '">'
    + '<div style="width:8px;height:8px;border-radius:50%;background:' + color + ';flex-shrink:0;"></div>'
    + '<span style="font-size:12px;font-weight:700;color:#fff;flex:1;">' + label + '</span>'
    + '<span id="' + id + '-badge" style="font-size:9px;font-weight:700;padding:2px 7px;border-radius:10px;'
    + (isOn
      ? 'background:rgba(0,220,150,.2);color:#00dc96;border:1px solid rgba(0,220,150,.3);'
      : 'background:rgba(255,255,255,.07);color:#666;border:1px solid rgba(255,255,255,.1);')
    + '">' + (isOn ? 'ON' : 'OFF') + '</span>'
    + '</div>';
}

function syncLiveItem(id, isOn){
  const el = document.getElementById(id);
  const badge = document.getElementById(id + '-badge');
  if(el){
    el.style.background = isOn ? 'rgba(0,212,255,.10)' : '';
    el.style.borderColor = isOn ? 'rgba(0,212,255,.3)' : 'transparent';
  }
  if(badge){
    badge.textContent = isOn ? 'ON' : 'OFF';
    badge.style.background    = isOn ? 'rgba(0,220,150,.2)'           : 'rgba(255,255,255,.07)';
    badge.style.color         = isOn ? '#00dc96'                      : '#666';
    badge.style.borderColor   = isOn ? 'rgba(0,220,150,.3)'           : 'rgba(255,255,255,.1)';
  }
}

function toggleLiveDropdown(){
  _liveDropOpen = !_liveDropOpen;
  const dd    = document.getElementById('live-dropdown');
  const arrow = document.getElementById('live-arrow');
  const trig  = document.getElementById('live-trigger');
  if(dd)    dd.style.display    = _liveDropOpen ? 'flex' : 'none';
  if(arrow) arrow.style.transform = _liveDropOpen ? 'rotate(180deg)' : '';
  if(trig)  trig.style.borderColor = _liveDropOpen ? 'rgba(0,212,255,.75)' : 'rgba(0,212,255,.45)';
}

// Close dropdown when clicking outside
document.addEventListener('click', function(e){
  const wrap = document.getElementById('live-drop-wrap');
  if(wrap && !wrap.contains(e.target)) {
    if(_liveDropOpen) toggleLiveDropdown();
  }
});


// ══════════════════════════════════════════════════════════════
// TIMELINE — Category Selector
// ══════════════════════════════════════════════════════════════
var tlCurrentCat = 'war';
var tlPlaying = false;
var tlSpeed = 1;
var tlDragging = false;
var tlCurrentDay = 1;
const TL_TOTAL_DAYS = 28;
const TL_WAR_START  = new Date('2026-02-28').getTime();

function tlSetCategory(cat){
  tlCurrentCat = cat;
  // Update selector highlight
  ['war','flt','sat','jam','vessel','marine'].forEach(c=>{
    const el = $('tlcat-'+c);
    if(el) el.classList.toggle('active', c===cat);
  });
  tlBuildCanvas();
}

function tlBuildCanvas(){
  const canvas = $('tl-canvas');
  if(!canvas) return;
  canvas.innerHTML = '';
  // Re-add cursor and elapsed
  const elapsed = document.createElement('div');
  elapsed.id = 'tl-elapsed';
  canvas.appendChild(elapsed);
  const cursor = document.createElement('div');
  cursor.id = 'tl-cursor';
  const handle = document.createElement('div');
  handle.id = 'tl-cursor-handle';
  handle.onmousedown = tlHandleDrag;
  cursor.appendChild(handle);
  canvas.appendChild(cursor);

  switch(tlCurrentCat){
    case 'war':    tlBuildWar(canvas);    break;
    case 'flt':    tlBuildFlights(canvas); break;
    case 'sat':    tlBuildSat(canvas);    break;
    case 'jam':    tlBuildJam(canvas);    break;
    case 'vessel': tlBuildVessels(canvas); break;
    case 'marine': tlBuildMarine(canvas); break;
  }
  tlBuildAxis();
  tlMoveCursor(tlCurrentDay);
}

function tlBuildAxis(){
  const axis = $('tl-axis');
  if(!axis) return;
  axis.innerHTML = '';
  for(let d=1; d<=TL_TOTAL_DAYS; d++){
    const pct = ((d-1)/(TL_TOTAL_DAYS-1))*100;
    const line = document.createElement('div');
    line.className = 'tl-day-line' + (d===1?' war-start':'');
    line.style.left = pct.toFixed(2)+'%';
    axis.appendChild(line);
    if(d===1 || d%5===0 || d===TL_TOTAL_DAYS){
      const lbl = document.createElement('div');
      lbl.className = 'tl-day-lbl' + (d===1?' war-start':'');
      lbl.style.left = pct.toFixed(2)+'%';
      const dt = new Date(TL_WAR_START + (d-1)*86400000);
      lbl.textContent = 'D'+d;
      axis.appendChild(lbl);
    }
  }
}

// WAR EVENTS timeline
function tlBuildWar(canvas){
  const dayBins = {};
  (WEVS||[]).forEach(ev=>{
    const t = new Date(ev.date||ev.t||'').getTime();
    if(isNaN(t)) return;
    const dk = Math.max(0, Math.floor((t - TL_WAR_START)/86400000));
    if(!dayBins[dk]) dayBins[dk] = {count:0, indices:[], killed:0};
    dayBins[dk].count++;
    dayBins[dk].indices.push((WEVS||[]).indexOf(ev));
    dayBins[dk].killed += parseInt(ev.killed||0)||0;
  });
  const maxC = Object.values(dayBins).reduce((m,b)=>Math.max(m,b.count),1)||1;
  const barW = (100/TL_TOTAL_DAYS).toFixed(3);
  for(let dk=0; dk<TL_TOTAL_DAYS; dk++){
    const b = dayBins[dk];
    if(!b) continue;
    const pct = (dk/TL_TOTAL_DAYS)*100;
    const hp  = Math.max(6, Math.round((b.count/maxC)*90));
    const inten = b.count/maxC;
    const r = Math.round(160+90*inten), g=20, a=(0.45+0.5*inten).toFixed(2);
    const bar = document.createElement('div');
    bar.className = 'tl-bar';
    bar.style.cssText = `left:${pct.toFixed(2)}%;width:${barW}%;height:${hp}%;
      background:rgba(${r},${g},40,${a});cursor:pointer;`;
    bar.title = `D${dk+1}: ${b.count} حدث${b.killed?' · '+b.killed+' قتيل':''}`;
    bar.addEventListener('click', e=>{
      e.stopPropagation();
      tlCurrentDay = dk+1;
      tlMoveCursor(dk+1);
      showDayBrief(b.indices, dk+1);
    });
    canvas.appendChild(bar);
  }
  // Update count badge
  const cc = $('tlcc-war');
  if(cc) cc.textContent = (WEVS||[]).length;
}

// FLIGHTS timeline — VIP gold icons + private grey
function tlBuildFlights(canvas){
  const fltHist = FLIGHT_HIST_DATA || {};
  const summary = fltHist.daily_summary || {};
  const flights  = fltHist.flights || [];

  // Count for badge
  const cc = $('tlcc-flt');
  if(cc) cc.textContent = Object.values(summary).reduce((a,s)=>a+(s.vip_count||0),0);

  const barW = (100/TL_TOTAL_DAYS).toFixed(3);
  const allTotals = Object.values(summary).map(s=>s.total_flights||0);
  const maxT = Math.max(...allTotals, 1);

  for(let d=1; d<=TL_TOTAL_DAYS; d++){
    const dt  = new Date(TL_WAR_START+(d-1)*86400000);
    const key = dt.toISOString().slice(0,10);
    const s   = summary[key] || {};
    const total = s.total_flights || 0;
    const vip   = s.vip_count || 0;
    const priv  = s.private_count || 0;
    const pct   = ((d-1)/TL_TOTAL_DAYS)*100;

    if(total > 0){
      const hp = Math.max(4, Math.round((total/maxT)*80));
      const bar = document.createElement('div');
      bar.className = 'tl-bar';
      bar.style.cssText = `left:${pct.toFixed(2)}%;width:${barW}%;height:${hp}%;
        background:rgba(184,134,11,0.25);cursor:pointer;`;
      bar.title = `D${d}: ${total} رحلة · ${vip} كبار مسؤولين`;
      bar.addEventListener('click', e=>{
        e.stopPropagation();
        tlCurrentDay = d;
        tlMoveCursor(d);
        showFlightDayBrief(d, key);
      });
      canvas.appendChild(bar);
    }

    // VIP icon
    if(vip > 0){
      const icon = document.createElement('div');
      icon.className = 'tl-aircraft-icon vip';
      icon.style.left = (pct + parseFloat(barW)/2).toFixed(2)+'%';
      icon.textContent = '✈';
      icon.title = `D${d}: ${vip} رحلة كبار مسؤولين`;
      icon.addEventListener('click', e=>{
        e.stopPropagation();
        tlCurrentDay = d;
        showFlightDayBrief(d, key);
      });
      canvas.appendChild(icon);
    } else if(priv > 0){
      const icon = document.createElement('div');
      icon.className = 'tl-aircraft-icon private';
      icon.style.left = (pct + parseFloat(barW)/2).toFixed(2)+'%';
      icon.textContent = '✈';
      icon.title = `D${d}: ${priv} طائرة خاصة`;
      canvas.appendChild(icon);
    }
  }
}

// SATELLITE timeline
function tlBuildSat(canvas){
  const hist = (HIST_SAT_DATA&&HIST_SAT_DATA.days) ? HIST_SAT_DATA.days : [];
  const cc = $('tlcc-sat');
  if(cc) cc.textContent = SATELLITES.length;

  const barW = (100/TL_TOTAL_DAYS).toFixed(3);
  hist.forEach(day=>{
    const dk = (day.day_num||1) - 1;
    const pct = (dk/TL_TOTAL_DAYS)*100;
    const cnt = day.iran_count || 0;
    const hp  = Math.max(4, Math.round((cnt/Math.max(cnt,8))*80));
    const bar = document.createElement('div');
    bar.className = 'tl-bar';
    bar.style.cssText = `left:${pct.toFixed(2)}%;width:${barW}%;height:${hp}%;
      background:rgba(184,134,11,${(0.3+0.6*(cnt/8)).toFixed(2)});cursor:pointer;`;
    bar.title = `D${day.day_num}: ${cnt} قمر فوق إيران`;
    bar.addEventListener('click', e=>{
      e.stopPropagation();
      tlCurrentDay = day.day_num;
      tlMoveCursor(day.day_num);
      if(typeof showHistSatsForDay==='function') showHistSatsForDay(day.date);
    });
    canvas.appendChild(bar);
  });
}

// JAMMING timeline
function tlBuildJam(canvas){
  const history = (GPSJAM_DATA && GPSJAM_DATA.history) ? GPSJAM_DATA.history : [];
  const cc = $('tlcc-jam');
  if(cc) cc.textContent = history.length + 'ي';

  const barW = (100/TL_TOTAL_DAYS).toFixed(3);
  const maxAvg = history.reduce((m,h)=>Math.max(m,h.me_avg||0), 0.01);

  history.forEach((h,idx)=>{
    const dk  = Math.max(0, Math.floor((new Date(h.date).getTime()-TL_WAR_START)/86400000));
    const pct = (dk/TL_TOTAL_DAYS)*100;
    const avg = h.me_avg || 0;
    const hp  = Math.max(4, Math.round((avg/maxAvg)*90));
    const inten = avg/maxAvg;
    const bar = document.createElement('div');
    bar.className = 'tl-bar';
    bar.style.cssText = `left:${pct.toFixed(2)}%;width:${barW}%;height:${hp}%;
      background:rgba(255,${Math.round(17+80*(1-inten))},68,${(0.4+0.5*inten).toFixed(2)});cursor:pointer;`;
    bar.title = `D${dk+1}: ${(avg*100).toFixed(0)}% متوسط تشويش`;
    canvas.appendChild(bar);
  });
}

// VESSEL ATTACKS timeline
function tlBuildVessels(canvas){
  const vessels = (ATTACKED_VESSELS && ATTACKED_VESSELS.vessels) ? ATTACKED_VESSELS.vessels : [];
  const cc = $('tlcc-vessel');
  if(cc) cc.textContent = vessels.length;

  const dayBins = {};
  vessels.forEach(v=>{
    const dk = Math.max(0, (parseInt(v.day_of_war)||1) - 1);
    if(!dayBins[dk]) dayBins[dk] = [];
    dayBins[dk].push(v);
  });

  const barW = (100/TL_TOTAL_DAYS).toFixed(3);
  Object.entries(dayBins).forEach(([dk, vlist])=>{
    const pct = (parseInt(dk)/TL_TOTAL_DAYS)*100;
    const hp  = Math.max(10, Math.min(80, vlist.length*20));
    const bar = document.createElement('div');
    bar.className = 'tl-bar';
    bar.style.cssText = `left:${pct.toFixed(2)}%;width:${barW}%;height:${hp}%;
      background:rgba(0,170,170,0.4);cursor:pointer;`;
    bar.title = `D${parseInt(dk)+1}: ${vlist.length} هجوم`;
    bar.addEventListener('click', e=>{
      e.stopPropagation();
      // Show attacked vessels on globe and fly to first of this day
      if(!_attackedVisible){ _attackedVisible=true; renderAttackedVessels(); }
      const first = vlist[0];
      if(first && first.lat && first.lon && viewer){
        viewer.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(
            parseFloat(first.lon), parseFloat(first.lat), 800000),
          duration: 1.5
        });
      }
      if(vlist.length===1) showVesselBrief(vlist[0]);
      else showDayVesselBrief(vlist, parseInt(dk)+1);
    });
    canvas.appendChild(bar);

    // Ship icon for each attack
    vlist.forEach((v,i)=>{
      const icon = document.createElement('div');
      icon.className = 'tl-vessel-icon';
      const offset = (i - (vlist.length-1)/2) * 8;
      icon.style.left = (pct + parseFloat(barW)/2).toFixed(2)+'%';
      icon.style.top  = (50 + offset)+'%';
      icon.textContent = v.vessel_category && v.vessel_category.includes('Naval') ? '⚓' : '[ship]';
      icon.title = v.vessel_name + ' · ' + v.location_name;
      icon.addEventListener('click', e=>{
        e.stopPropagation();
        showVesselBrief(v);
        if(v.lat && v.lon && viewer){
          viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(
              parseFloat(v.lon), parseFloat(v.lat), 800000),
            duration: 1.8
          });
        }
      });
      canvas.appendChild(icon);
    });
  });
}

// MARINE timeline
function tlBuildMarine(canvas){
  const zones = (MARITIME_THREAT && MARITIME_THREAT.zones) ? MARITIME_THREAT.zones : [];
  const cc = $('tlcc-marine');
  const total = (MARINE_DATA && MARINE_DATA.total) || 0;
  if(cc) cc.textContent = total + ' AIS';

  // Just show a static summary bar for now (live data not day-indexed)
  const msg = document.createElement('div');
  msg.style.cssText = `position:absolute;top:50%;left:50%;
    transform:translate(-50%,-50%);font-size:12px;color:var(--text-muted);
    direction:rtl;text-align:center;`;
  msg.innerHTML = `${total} سفينة مباشرة · ${zones.filter(z=>z.risk_level==='critical'||z.risk_level==='high').length} مناطق خطر`;
  canvas.appendChild(msg);
}

// Cursor movement
function tlMoveCursor(day){
  const cursor = $('tl-cursor');
  const elapsed = $('tl-elapsed');
  if(!cursor) return;
  const pct = ((day-1)/(TL_TOTAL_DAYS-1))*100;
  cursor.style.left = pct.toFixed(2)+'%';
  if(elapsed) elapsed.style.width = pct.toFixed(2)+'%';
  // Update day label
  const lbl = $('tl-day-label');
  if(lbl) lbl.textContent = 'اليوم ' + day;
}

function tlClick(e){
  const rect = e.currentTarget.getBoundingClientRect();
  const pct  = (e.clientX - rect.left) / rect.width;
  const day  = Math.max(1, Math.min(TL_TOTAL_DAYS, Math.round(pct*(TL_TOTAL_DAYS-1))+1));
  tlCurrentDay = day;
  tlMoveCursor(day);
}

function tlHandleDrag(e){
  e.preventDefault();
  e.stopPropagation();
  tlDragging = true;
  const handle = $('tl-cursor-handle');
  if(handle) handle.classList.add('dragging');
  document.onmousemove = tlDrag;
  document.onmouseup   = tlEndDrag;
}
function tlDrag(e){
  if(!tlDragging) return;
  const canvas = $('tl-canvas');
  if(!canvas) return;
  const rect = canvas.getBoundingClientRect();
  const pct  = Math.max(0,Math.min(1,(e.clientX-rect.left)/rect.width));
  const day  = Math.max(1, Math.min(TL_TOTAL_DAYS, Math.round(pct*(TL_TOTAL_DAYS-1))+1));
  tlCurrentDay = day;
  tlMoveCursor(day);
}
function tlEndDrag(){
  tlDragging = false;
  const handle = $('tl-cursor-handle');
  if(handle) handle.classList.remove('dragging');
  document.onmousemove = null;
  document.onmouseup   = null;
}
function tlStartDrag(e){ /* handled by canvas click */ }
function tlTogglePlay(){
  tlPlaying = !tlPlaying;
  const btn = $('tl-play-btn');
  if(btn) btn.textContent = tlPlaying ? '⏸' : '▶';
  if(tlPlaying) tlPlayTick();
}
function tlPlayTick(){
  if(!tlPlaying) return;
  tlCurrentDay = Math.min(TL_TOTAL_DAYS, tlCurrentDay + 1);
  tlMoveCursor(tlCurrentDay);
  if(tlCurrentDay >= TL_TOTAL_DAYS){ tlPlaying=false; const btn=$('tl-play-btn');if(btn)btn.textContent='▶'; return; }
  setTimeout(tlPlayTick, 1200/tlSpeed);
}
function tlCycleSpeed(){
  const speeds = [1,2,5,10];
  const idx = speeds.indexOf(tlSpeed);
  tlSpeed = speeds[(idx+1)%speeds.length];
  const el = $('tl-speed');
  if(el) el.textContent = '×'+tlSpeed;
}

// ══════════════════════════════════════════════════════════════
// VESSEL BRIEF CARD
// ══════════════════════════════════════════════════════════════
function showVesselBrief(v){
  const card = $('war-brief-card');
  if(!card) return;
  const _s = (id,val)=>{const el=$(id);if(el)el.textContent=val;};
  const catColor = v.vessel_category && v.vessel_category.includes('Naval') ? '#ff4444' : '#00aaaa';
  _s('wbc-id', 'D'+v.day_of_war+' · هجوم بحري');
  _s('wbc-time', v.date||'—');
  const dot=$('wbc-type-dot');if(dot)dot.style.background=catColor;
  _s('wbc-type-label', v.vessel_category||'سفينة تجارية');
  _s('wbc-title', v.vessel_name + ' — ' + v.location_name);
  _s('wbc-detail', v.description||'—');
  const meta=$('wbc-meta');
  if(meta) meta.innerHTML = [
    v.flag          ? `<div class="wbc-meta-item"><strong>العلم:</strong> ${v.flag}</div>` : '',
    v.vessel_type   ? `<div class="wbc-meta-item"><strong>النوع:</strong> ${v.vessel_type}</div>` : '',
    v.attacker      ? `<div class="wbc-meta-item"><strong>المهاجم:</strong> ${v.attacker}</div>` : '',
    v.attack_type   ? `<div class="wbc-meta-item"><strong>السلاح:</strong> ${v.attack_type}</div>` : '',
    v.damage_level  ? `<div class="wbc-meta-item"><strong>الضرر:</strong> ${v.damage_level}</div>` : '',
    (v.killed>0||v.injured>0||v.missing>0)
      ? `<div class="wbc-meta-item"><strong>خسائر:</strong> ${v.killed||0} قتيل · ${v.injured||0} مصاب · ${v.missing||0} مفقود</div>` : '',
    v.confirmed==='True'
      ? `<div class="wbc-meta-item badge badge-green">✓ مؤكد</div>`
      : `<div class="wbc-meta-item badge badge-gold">⚠ جزئي</div>`,
  ].join('');
  card.classList.add('visible');
}

// ══════════════════════════════════════════════════════════════
// FLIGHT DAY BRIEF
// ══════════════════════════════════════════════════════════════
function showFlightDayBrief(day, dateKey){
  const card = $('war-brief-card');
  if(!card) return;
  const _s = (id,val)=>{const el=$(id);if(el)el.textContent=val;};
  const fltHist = FLIGHT_HIST_DATA || {};
  const byDay   = fltHist.by_day || {};
  const dayFlts = byDay[day] || [];
  const vipFlts = dayFlts.filter(f=>f.category==='VIP_KNOWN');

  _s('wbc-id', 'D'+day+' \u00b7 \u062d\u0631\u0643\u0629 \u0627\u0644\u0631\u062d\u0644\u0627\u062a');
  _s('wbc-time', dateKey||'\u2014');
  const dot=$('wbc-type-dot');if(dot)dot.style.background='#b8860b';
  _s('wbc-type-label','\u0631\u062d\u0644\u0627\u062a \u0643\u0628\u0627\u0631 \u0627\u0644\u0645\u0633\u0624\u0648\u0644\u064a\u0646');
  _s('wbc-title', '\u0627\u0644\u064a\u0648\u0645 '+day+': '+dayFlts.length+' \u0631\u062d\u0644\u0629 \u00b7 '+vipFlts.length+' VIP');

  // Build clickable flight list
  const dd=$('wbc-detail');
  if(dd){
    dd.style.padding='4px 0';dd.style.borderLeft='none';
    dd.innerHTML = vipFlts.length===0
      ? '<div style="color:#999;font-size:11px;padding:8px 0;">\u0644\u0627 \u062a\u0648\u062c\u062f \u0631\u062d\u0644\u0627\u062a VIP</div>'
      : vipFlts.slice(0,12).map(function(f,i){
        var dep = f.dep_city || f.dep_iata || '\u063a\u064a\u0631 \u0645\u062d\u062f\u062f';
        var arr = f.arr_city || f.arr_iata || '\u063a\u064a\u0631 \u0645\u062d\u062f\u062f';
        var owner = f.owner || '';
        var time = '';
        if(f.dep_time) time = f.dep_time.slice(11,16);
        var hasRoute = f.dep_lat && f.arr_lat;
        return '<div onclick="flyToFlight('+day+','+i+')" style="'
          +'padding:8px 10px;margin-bottom:4px;border-radius:6px;cursor:pointer;'
          +'background:rgba(184,134,11,.06);border:1px solid rgba(184,134,11,.15);'
          +'border-right:3px solid #b8860b;direction:rtl;transition:background .15s;'
          +'">'
          +'<div style="display:flex;justify-content:space-between;align-items:center;">'
          +'<span style="font-size:12px;font-weight:700;color:#5c3a00;">'+owner+'</span>'
          +(time?'<span style="font-size:10px;color:#999;font-family:monospace;">'+time+'</span>':'')
          +'</div>'
          +'<div style="font-size:11px;color:#333;margin-top:3px;">'
          +'<span style="color:#b8860b;font-weight:600;">'+dep+'</span>'
          +' \u2192 '
          +'<span style="color:#b8860b;font-weight:600;">'+arr+'</span>'
          +'</div>'
          +'<div style="font-size:9px;color:#888;margin-top:2px;">'+f.label+' \u00b7 '+(f.reg||'')+'</div>'
          +(hasRoute?'':'<div style="font-size:9px;color:#cc6600;margin-top:2px;">\u26a0 \u0644\u0627 \u062a\u0648\u062c\u062f \u0625\u062d\u062f\u0627\u062b\u064a\u0627\u062a \u0644\u0644\u0645\u0633\u0627\u0631</div>')
          +'</div>';
      }).join('');
  }

  // Store flights for click handler
  window._dayVipFlights = vipFlts;

  const meta=$('wbc-meta');
  if(meta) meta.innerHTML =
    '<div style="display:flex;gap:12px;font-size:11px;color:#666;padding:4px 0;">'
    +'<span>\u0625\u062c\u0645\u0627\u0644\u064a: <strong>'+dayFlts.length+'</strong></span>'
    +'<span>VIP: <strong>'+vipFlts.length+'</strong></span>'
    +'</div>';

  card.style.borderLeftColor='#b8860b';
  card.classList.add('visible');

  // Draw all VIP arcs on globe
  if(viewer) clearHistFltEntities();
  vipFlts.slice(0,15).forEach(function(f){
    if(!f.dep_lat||!f.arr_lat||!viewer) return;
    try{
      var ent=viewer.entities.add({
        polyline:{
          positions: Cesium.Cartesian3.fromDegreesArray([
            parseFloat(f.dep_lon), parseFloat(f.dep_lat),
            parseFloat(f.arr_lon), parseFloat(f.arr_lat)
          ]),
          width:1.5,
          material: new Cesium.PolylineGlowMaterialProperty({
            glowPower:0.15,
            color:Cesium.Color.fromCssColorString('#b8860b').withAlpha(0.5)
          }),
          arcType: Cesium.ArcType.GEODESIC,
          clampToGround: false,
        }
      });
      _histFltEntities.push(ent);
    }catch(e){}
  });
}

// Click handler for individual flight in the day list
function flyToFlight(day, idx){
  var flts = window._dayVipFlights || [];
  var f = flts[idx];
  if(!f||!viewer) return;

  // Clear previous highlights
  if(window._fltHighlight){try{viewer.entities.remove(window._fltHighlight);}catch(e){}}
  if(window._fltHighlight2){try{viewer.entities.remove(window._fltHighlight2);}catch(e){}}
  window._fltHighlight=null;window._fltHighlight2=null;

  if(!f.dep_lat||!f.arr_lat){
    // No coordinates — show info only
    showEntityInfo(f.owner||f.label, (f.label||'FLIGHT').toUpperCase(),
      [['Reg',f.reg||'\u2014'],['From',f.dep_city||'\u063a\u064a\u0631 \u0645\u062d\u062f\u062f'],
       ['To',f.arr_city||'\u063a\u064a\u0631 \u0645\u062d\u062f\u062f'],['Owner',f.owner||'\u2014']],
      f.label+' flight');
    return;
  }

  var dLat=parseFloat(f.dep_lat),dLon=parseFloat(f.dep_lon);
  var aLat=parseFloat(f.arr_lat),aLon=parseFloat(f.arr_lon);
  var midLat=(dLat+aLat)/2, midLon=(dLon+aLon)/2;

  // Highlight this specific route in bright gold
  window._fltHighlight=viewer.entities.add({
    polyline:{
      positions:Cesium.Cartesian3.fromDegreesArray([dLon,dLat,aLon,aLat]),
      width:4,
      material:new Cesium.PolylineGlowMaterialProperty({glowPower:0.3,color:Cesium.Color.fromCssColorString('#ffd700')}),
      arcType:Cesium.ArcType.GEODESIC,clampToGround:false
    }
  });

  // Departure marker
  window._fltHighlight2=viewer.entities.add({
    position:Cesium.Cartesian3.fromDegrees(dLon,dLat,5000),
    point:{pixelSize:10,color:Cesium.Color.fromCssColorString('#00cc66'),outlineColor:Cesium.Color.WHITE,outlineWidth:2,disableDepthTestDistance:Number.POSITIVE_INFINITY},
    label:{text:f.dep_city||f.dep_iata||'DEP',font:'700 11px Inter',fillColor:Cesium.Color.WHITE,outlineColor:Cesium.Color.BLACK,outlineWidth:2,style:Cesium.LabelStyle.FILL_AND_OUTLINE,pixelOffset:new Cesium.Cartesian2(0,-18),showBackground:true,backgroundColor:Cesium.Color.fromCssColorString('#006633').withAlpha(0.85),backgroundPadding:new Cesium.Cartesian2(5,3),disableDepthTestDistance:Number.POSITIVE_INFINITY}
  });

  // Arrival marker
  var arrEnt=viewer.entities.add({
    position:Cesium.Cartesian3.fromDegrees(aLon,aLat,5000),
    point:{pixelSize:10,color:Cesium.Color.fromCssColorString('#ff4444'),outlineColor:Cesium.Color.WHITE,outlineWidth:2,disableDepthTestDistance:Number.POSITIVE_INFINITY},
    label:{text:f.arr_city||f.arr_iata||'ARR',font:'700 11px Inter',fillColor:Cesium.Color.WHITE,outlineColor:Cesium.Color.BLACK,outlineWidth:2,style:Cesium.LabelStyle.FILL_AND_OUTLINE,pixelOffset:new Cesium.Cartesian2(0,-18),showBackground:true,backgroundColor:Cesium.Color.fromCssColorString('#cc0020').withAlpha(0.85),backgroundPadding:new Cesium.Cartesian2(5,3),disableDepthTestDistance:Number.POSITIVE_INFINITY}
  });
  _histFltEntities.push(arrEnt);

  // Fly to midpoint
  viewer.camera.flyTo({
    destination:Cesium.Cartesian3.fromDegrees(midLon,midLat,2500000),
    duration:1.8,easingFunction:Cesium.EasingFunction.CUBIC_IN_OUT
  });

  // Show info card
  showEntityInfo(f.owner||f.label, f.label,
    [['Reg',f.reg||'\u2014'],
     ['Owner',f.owner||'\u2014'],
     ['From',f.dep_city||'\u063a\u064a\u0631 \u0645\u062d\u062f\u062f'],
     ['To',f.arr_city||'\u063a\u064a\u0631 \u0645\u062d\u062f\u062f'],
     ['Dep Time',(f.dep_time||'').slice(0,16)],
     ['Arr Time',(f.arr_time||'').slice(0,16)]],
    f.label+' flight route '+f.dep_city+' '+f.arr_city);

  // Auto-cleanup after 30s
  setTimeout(function(){
    if(window._fltHighlight){try{viewer.entities.remove(window._fltHighlight);}catch(e){}}
    if(window._fltHighlight2){try{viewer.entities.remove(window._fltHighlight2);}catch(e){}}
    window._fltHighlight=null;window._fltHighlight2=null;
  },30000);
}

// ══════════════════════════════════════════════════════════════
// LIVE VIEW TOGGLE
// ══════════════════════════════════════════════════════════════
var liveViewOn = false;
function toggleLiveView(){
  liveViewOn = !liveViewOn;
  if(liveViewOn){
    renderCivFlights();
  } else {
    clearCivFlights();
  }
}

// ══════════════════════════════════════════════════════════════
// TOP TOGGLE (generic chip toggle)
// ══════════════════════════════════════════════════════════════
function topToggle(cat){
  const chip = $('lchip-'+cat);
  if(!chip) return;
  const on = chip.classList.toggle('active');
  if(cat==='war'){
    layerOn.war = on;
    if(on) renderWarMarkers(); else clearWarEntities();
  } else if(cat==='flt'){
    layerOn.flt = on;
    if(on) renderCivFlights(); else clearCivFlights();
  } else if(cat==='jam'){
    layerOn.jam = on;
    if(on) renderJamming(); else clearJamming();
  } else if(cat==='vessel'){
    layerOn.vessel = on;
    _attackedVisible = on;
    const ltap=$('lt-attacked-panel');if(ltap){ltap.classList.toggle('on',on);ltap.classList.toggle('off',!on);}
    if(on) renderAttackedVessels(); else clearAttackedEntities();
  }
}


// ══════════════════════════════════════════════════════════════════
// ANALYTICS PAGE — RENDER FUNCTIONS
// Reads from Cell 10 output variables (ESCALATION_ANALYSIS, etc.)
// ══════════════════════════════════════════════════════════════════

var anReady=false, anChartEsc=null, anChartPol=null, anChartAlign=null, anChartDom=null, anChartJam=null, anChartJamCorr=null;

function initAnalytics(){
  if(anReady)return;
  requestAnimationFrame(function(){
    anReady=true;
    try{ renderWarStatus(); }catch(e){ console.error('[Analytics] status:',e); }
    try{ renderEscalationChart(); }catch(e){ console.error('[Analytics] escalation:',e); }
    try{ renderCountryHeatmap(); }catch(e){ console.error('[Analytics] heatmap:',e); }
    try{ renderWhoHitWhom(); }catch(e){ console.error('[Analytics] whohit:',e); }
    try{ renderCountryRanking(); }catch(e){ console.error('[Analytics] countries:',e); }
    try{ renderPoliticalChart(); }catch(e){ console.error('[Analytics] political:',e); }
    try{ renderMilestones(); }catch(e){ console.error('[Analytics] milestones:',e); }
    try{ renderAlignmentChart(); }catch(e){ console.error('[Analytics] alignment:',e); }
    try{ renderDomainChart(); }catch(e){ console.error('[Analytics] domains:',e); }
    try{ renderActorRanking(); }catch(e){ console.error('[Analytics] actors:',e); }
    try{ renderContradictions(); }catch(e){ console.error('[Analytics] contradictions:',e); }
    try{ renderJammingChart(); }catch(e){ console.error('[Analytics] jamming:',e); }
    try{ renderJamZones(); }catch(e){ console.error('[Analytics] jamzones:',e); }
    try{ renderJamCorrelation(); }catch(e){ console.error('[Analytics] jamcorr:',e); }
    try{ renderMaritimeSection(); }catch(e){ console.error('[Analytics] maritime:',e); }
    try{ renderHormuzFlow(); }catch(e){ console.error('[Analytics] hormuz-flow:',e); }
    try{ renderSeaRoutes(); }catch(e){ console.error('[Analytics] sea-routes:',e); }
    try{ renderGlobalMilitary(); }catch(e){ console.error('[Analytics] global-mil:',e); }
    try{ renderVesselHistories(); }catch(e){ console.error('[Analytics] vessel-hist:',e); }
    try{ renderInspections(); }catch(e){ console.error('[Analytics] inspections:',e); }
    try{ renderCompanyProfiles(); }catch(e){ console.error('[Analytics] companies:',e); }
    try{ renderCountryPresence(); }catch(e){ console.error('[Analytics] countryPresence:',e); }
    try{ renderCasualtiesAndSatE(); }catch(e){ console.error('[Analytics] casualties:',e); }
    try{ renderFlightIntel(); }catch(e){ console.error('[Analytics] flights:',e); }
    try{ renderISRSection(); }catch(e){ console.error('[Analytics] isr:',e); }
    try{ renderThreatScore(); }catch(e){ console.error('[Analytics] threat:',e); }
  });
}

// ═══ A. WAR STATUS STRIP ═════════════════════════════════════════
function renderWarStatus(){
  var ea=ESCALATION_ANALYSIS||{}, pa=POLITICAL_ANALYSIS||{}, cp=CONFLICT_PREDICTION||{};
  var el;
  el=$('stat-events');if(el)el.textContent=(ea.days||[]).reduce(function(s,d){return s+d.n;},0);
  el=$('stat-countries');if(el)el.textContent=(ea.country_ranking||[]).length;
  // Escalation direction
  var days=ea.days||[],last7=days.slice(-7),prior7=days.slice(-14,-7);
  var avgL=last7.reduce(function(s,d){return s+d.n;},0)/Math.max(last7.length,1);
  var avgP=prior7.reduce(function(s,d){return s+d.n;},0)/Math.max(prior7.length,1);
  var pctChange=avgP>0?((avgL-avgP)/avgP*100):0;
  el=$('stat-direction');if(el){
    if(pctChange>10){el.textContent='\u2197 \u062a\u0635\u0627\u0639\u062f\u064a '+Math.round(pctChange)+'%';el.style.color='#ff4444';}
    else if(pctChange<-10){el.textContent='\u2198 \u062a\u0631\u0627\u062c\u0639\u064a '+Math.round(pctChange)+'%';el.style.color='#44cc66';}
    else{el.textContent='\u2192 \u0645\u0633\u062a\u0642\u0631';el.style.color='#ccaa00';}
  }
  el=$('stat-pol-trend');if(el){
    var t=pa.trend||'';
    if(t.includes('escalatory'))el.textContent='\u2191 \u062a\u0635\u0627\u0639\u062f\u064a';
    else if(t.includes('de-escalatory'))el.textContent='\u2193 \u062a\u0647\u062f\u0626\u0629';
    else el.textContent='\u2194 \u0645\u062e\u062a\u0644\u0637';
  }
  el=$('stat-threat');if(el)el.textContent=Math.round(cp.score||0)+'/100';
  // War phase
  var phases=pa.war_phases||[];
  el=$('an-war-phase');if(el&&phases.length)el.textContent=phases[phases.length-1].phase;
}

// ═══ B4+5: ESCALATION CHART ═════════════════════════════════════
function renderEscalationChart(){
  var ea=ESCALATION_ANALYSIS||{}, days=ea.days||[];
  if(!days.length)return;
  var ctx=document.getElementById('an-chart-escalation');
  if(!ctx||typeof Chart==='undefined')return;
  if(anChartEsc){anChartEsc.destroy();anChartEsc=null;}
  var labels=days.map(function(d){return 'D'+d.day;});
  var weaponTypes=['airstrike','missile_strike','drone_strike','naval_attack','ground_operation','assassination','interception'];
  var weaponLabels=['\u063a\u0627\u0631\u0629 \u062c\u0648\u064a\u0629','\u0635\u0627\u0631\u0648\u062e','\u0645\u0633\u064a\u0651\u0631\u0629','\u0647\u062c\u0648\u0645 \u0628\u062d\u0631\u064a','\u0628\u0631\u064a','\u0627\u063a\u062a\u064a\u0627\u0644','\u0627\u0639\u062a\u0631\u0627\u0636'];
  var weaponColors=['rgba(220,50,50,.8)','rgba(255,120,0,.8)','rgba(255,200,0,.8)','rgba(0,120,200,.8)','rgba(80,160,80,.8)','rgba(180,0,180,.8)','rgba(100,100,100,.6)'];
  var datasets=weaponTypes.map(function(wt,wi){
    return {label:weaponLabels[wi],data:days.map(function(d){return(d.types||{})[wt]||0;}),backgroundColor:weaponColors[wi],stack:'types',borderWidth:0};
  });
  // Actor overlay lines
  var actors=['Israel','USA/Israel','Iran','USA'];
  var actorColors=['#0066cc','#2222aa','#ff3355','#22aa44'];
  var actorLabels=['\u0625\u0633\u0631\u0627\u0626\u064a\u0644','USA/\u0625\u0633\u0631\u0627\u0626\u064a\u0644','\u0625\u064a\u0631\u0627\u0646','\u0627\u0644\u0648\u0644\u0627\u064a\u0627\u062a \u0627\u0644\u0645\u062a\u062d\u062f\u0629'];
  actors.forEach(function(act,ai){
    datasets.push({label:actorLabels[ai],data:days.map(function(d){return(d.actors||{})[act]||0;}),type:'line',borderColor:actorColors[ai],borderWidth:1.5,pointRadius:2,fill:false,yAxisID:'y1'});
  });
  anChartEsc=new Chart(ctx,{type:'bar',data:{labels:labels,datasets:datasets},
    options:{responsive:true,maintainAspectRatio:false,animation:false,
      plugins:{legend:{display:true,labels:{color:'var(--text-muted)',font:{size:9},boxWidth:10,padding:4}},tooltip:{mode:'index'}},
      scales:{x:{ticks:{font:{size:8},maxRotation:45},grid:{display:false},stacked:true},
        y:{ticks:{font:{size:9}},grid:{color:'rgba(0,0,0,.05)'},beginAtZero:true,stacked:true,title:{display:true,text:'\u0623\u062d\u062f\u0627\u062b',font:{size:9}}},
        y1:{type:'linear',position:'left',ticks:{font:{size:9}},grid:{display:false},beginAtZero:true,title:{display:true,text:'\u0628\u0627\u0644\u0641\u0627\u0639\u0644',font:{size:9}}}
      }
    }
  });
}

// ═══ B6: COUNTRY HEATMAP ═════════════════════════════════════════
function renderCountryHeatmap(){
  var ea=ESCALATION_ANALYSIS||{}, matrix=ea.country_day_matrix||{}, countries=ea.all_countries||[];
  var el=$('an-country-heatmap');if(!el)return;
  if(!countries.length){el.innerHTML='<div style="text-align:center;color:var(--text-muted);padding:20px;">\u0644\u0627 \u062a\u0648\u062c\u062f \u0628\u064a\u0627\u0646\u0627\u062a</div>';return;}
  var maxVal=1;
  countries.forEach(function(c){(matrix[c]||[]).forEach(function(v){if(v>maxVal)maxVal=v;});});
  var html='<table style="border-collapse:collapse;font-size:10px;width:100%;"><thead><tr><th style="text-align:right;padding:3px 6px;font-size:10px;color:var(--burg-600);position:sticky;right:0;background:var(--ui-bg2);z-index:1;">\u0627\u0644\u062f\u0648\u0644\u0629</th>';
  var days=ea.days||[];
  days.forEach(function(d){html+='<th style="padding:2px;font-size:8px;color:var(--text-muted);min-width:18px;">D'+d.day+'</th>';});
  html+='</tr></thead><tbody>';
  countries.forEach(function(c){
    var row=matrix[c]||[];
    html+='<tr><td style="text-align:right;padding:3px 6px;font-weight:700;font-size:10px;white-space:nowrap;position:sticky;right:0;background:var(--ui-bg2);">'+c+'</td>';
    row.forEach(function(v){
      var intensity=v/maxVal;
      var bg=v===0?'transparent':'rgba(184,0,56,'+(0.1+intensity*0.8).toFixed(2)+')';
      var txt=v>0?v:'';
      html+='<td style="text-align:center;padding:2px;background:'+bg+';color:'+(intensity>0.5?'#fff':'var(--text-muted)')+';font-size:8px;font-weight:'+(v>0?'700':'400')+';border:1px solid var(--ui-border2);">'+txt+'</td>';
    });
    html+='</tr>';
  });
  html+='</tbody></table>';
  el.innerHTML=html;
}

// ═══ B8: WHO HIT WHOM ═══════════════════════════════════════════
function renderWhoHitWhom(){
  // Removed — actor-level data from curated subset; use ACLED for authoritative totals
  var el=$('an-who-hit-whom');if(!el)return;
  el.parentElement.style.display='none';
}

// ═══ B9: COUNTRY RANKING ════════════════════════════════════════
function renderCountryRanking(){
  var ea=ESCALATION_ANALYSIS||{}, data=ea.country_ranking||[];
  var el=$('an-country-ranking');if(!el)return;
  if(!data.length)return;
  var maxE=data[0].events;
  el.innerHTML=data.slice(0,14).map(function(r){
    var pct=Math.round(r.events/maxE*100);
    return '<div class="an-bar-row"><div class="an-bar-label">'+r.country+'</div><div class="an-bar-wrap"><div class="an-bar-fill" style="width:'+pct+'%;background:var(--burg-400);"></div></div><div class="an-bar-value">'+r.events+'</div></div>';
  }).join('');
}

// ═══ C10+11: POLITICAL CHART ════════════════════════════════════
function renderPoliticalChart(){
  var pa=POLITICAL_ANALYSIS||{}, days=pa.days||[];
  if(!days.length)return;
  var ctx=document.getElementById('an-chart-political');
  if(!ctx||typeof Chart==='undefined')return;
  if(anChartPol){anChartPol.destroy();anChartPol=null;}
  var labels=days.map(function(d){return 'D'+d.day;});
  anChartPol=new Chart(ctx,{type:'bar',data:{labels:labels,datasets:[
    {label:'\u062a\u0635\u0627\u0639\u062f\u064a',data:days.map(function(d){return d.esc_count;}),backgroundColor:'rgba(220,0,30,.7)',stack:'pol'},
    {label:'\u062a\u0647\u062f\u0626\u0629',data:days.map(function(d){return -d.de_esc_count;}),backgroundColor:'rgba(40,120,64,.7)',stack:'pol'},
    {label:'\u0645\u062d\u0627\u064a\u062f',data:days.map(function(d){return d.neut_count;}),backgroundColor:'rgba(150,150,150,.4)',stack:'pol'},
    {label:'\u0627\u0644\u0636\u063a\u0637 \u0627\u0644\u062a\u0631\u0627\u0643\u0645\u064a',data:days.map(function(d){return d.cumulative;}),type:'line',borderColor:'#b80038',borderWidth:2,pointRadius:1,fill:false,yAxisID:'y1'}
  ]},options:{responsive:true,maintainAspectRatio:false,animation:false,
    plugins:{legend:{display:true,labels:{font:{size:9},boxWidth:10}},tooltip:{mode:'index'}},
    scales:{x:{ticks:{font:{size:8}},grid:{display:false},stacked:true},
      y:{stacked:true,ticks:{font:{size:9}},grid:{color:'rgba(0,0,0,.05)'},title:{display:true,text:'\u0623\u062d\u062f\u0627\u062b/\u064a\u0648\u0645',font:{size:9}}},
      y1:{type:'linear',position:'left',ticks:{font:{size:9}},grid:{display:false},title:{display:true,text:'\u062a\u0631\u0627\u0643\u0645\u064a',font:{size:9}}}
    }
  }});
}

// ═══ C12: MILESTONES ════════════════════════════════════════════
function renderMilestones(){
  var pa=POLITICAL_ANALYSIS||{}, ms=pa.milestones||[];
  var el=$('an-milestones');if(!el)return;
  if(!ms.length){el.innerHTML='<div style="color:var(--text-muted);padding:10px;">\u0644\u0627 \u062a\u0648\u062c\u062f \u0645\u062d\u0637\u0627\u062a</div>';return;}
  el.innerHTML=ms.slice(0,40).map(function(m){
    var badge=m.direction==='Escalatory'?'<span class="badge-esc">\u2191 \u062a\u0635\u0627\u0639\u062f\u064a</span>':m.direction==='De-escalatory'?'<span class="badge-deesc">\u2193 \u062a\u0647\u062f\u0626\u0629</span>':'';
    var phBadge=m.phase?'<span style="font-size:9px;color:var(--text-muted);background:var(--ui-bg3);padding:1px 5px;border-radius:3px;">'+m.phase+'</span>':'';
    return '<div class="an-milestone"><div style="display:flex;justify-content:space-between;align-items:center;"><span class="day">D'+m.day+' \xb7 '+m.date+'</span><span>'+badge+' '+phBadge+'</span></div><div class="actor">'+m.actor+'</div><div class="desc">'+m.desc+'</div></div>';
  }).join('');
}

// ═══ C13: ALIGNMENT CHART ═══════════════════════════════════════
function renderAlignmentChart(){
  var pa=POLITICAL_ANALYSIS||{}, days=pa.alignment_days||[];
  if(!days.length)return;
  var ctx=document.getElementById('an-chart-alignment');
  if(!ctx||typeof Chart==='undefined')return;
  if(anChartAlign){anChartAlign.destroy();anChartAlign=null;}
  var labels=days.map(function(d){return 'D'+d.day;});
  anChartAlign=new Chart(ctx,{type:'bar',data:{labels:labels,datasets:[
    {label:'\u062a\u062d\u0627\u0644\u0641 US-\u0625\u0633\u0631\u0627\u0626\u064a\u0644',data:days.map(function(d){return d['US-Israel Coalition']||0;}),backgroundColor:'rgba(0,100,200,.7)',stack:'a'},
    {label:'\u0645\u062d\u0648\u0631 \u0625\u064a\u0631\u0627\u0646',data:days.map(function(d){return d['Iran-Axis']||0;}),backgroundColor:'rgba(220,0,30,.7)',stack:'a'},
    {label:'\u0645\u062d\u0627\u064a\u062f / \u0648\u0633\u064a\u0637',data:days.map(function(d){return d['Neutral/Mediator']||0;}),backgroundColor:'rgba(180,180,0,.6)',stack:'a'},
    {label:'\u062f\u0648\u0644\u064a',data:days.map(function(d){return d['International/Other']||0;}),backgroundColor:'rgba(100,100,100,.4)',stack:'a'}
  ]},options:{responsive:true,maintainAspectRatio:false,animation:false,
    plugins:{legend:{display:true,labels:{font:{size:9},boxWidth:10}}},
    scales:{x:{ticks:{font:{size:8}},grid:{display:false},stacked:true},y:{stacked:true,ticks:{font:{size:9}},grid:{color:'rgba(0,0,0,.04)'}}}
  }});
}

// ═══ C16: DOMAIN CHART ══════════════════════════════════════════
function renderDomainChart(){
  var pa=POLITICAL_ANALYSIS||{}, data=pa.domain_breakdown||[];
  if(!data.length)return;
  var ctx=document.getElementById('an-chart-domains');
  if(!ctx||typeof Chart==='undefined')return;
  if(anChartDom){anChartDom.destroy();anChartDom=null;}
  var colors=['#b80038','#cc6600','#0066cc','#287840','#8844aa','#cc0066','#448844','#886600'];
  anChartDom=new Chart(ctx,{type:'doughnut',data:{
    labels:data.map(function(d){return d.domain;}),
    datasets:[{data:data.map(function(d){return d.count;}),backgroundColor:colors.slice(0,data.length),borderWidth:1}]
  },options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'right',labels:{font:{size:10},boxWidth:10,padding:6}}}}});
}

// ═══ C14: ACTOR RANKING ═════════════════════════════════════════
function renderActorRanking(){
  var di=DIPLOMATIC_INDEX||{}, actors=di.top_actors||[];
  var el=$('an-actor-ranking');if(!el)return;
  if(!actors.length)return;
  var maxN=actors[0].n;
  el.innerHTML=actors.slice(0,12).map(function(a){
    var escPct=a.n>0?Math.round(a.esc/a.n*100):0;
    var deescPct=a.n>0?Math.round(a.de_esc/a.n*100):0;
    return '<div class="an-bar-row"><div class="an-bar-label" style="width:150px;">'+a.actor.slice(0,30)+'</div><div class="an-bar-wrap"><div style="display:flex;height:100%;"><div style="width:'+escPct+'%;background:rgba(220,0,30,.7);"></div><div style="width:'+(100-escPct-deescPct)+'%;background:rgba(150,150,150,.3);"></div><div style="width:'+deescPct+'%;background:rgba(40,120,64,.7);"></div></div></div><div class="an-bar-value" style="width:55px;font-size:9px;">'+a.esc+'\u2191 '+a.de_esc+'\u2193</div></div>';
  }).join('');
}

// ═══ C15: CONTRADICTIONS ════════════════════════════════════════
function renderContradictions(){
  var di=DIPLOMATIC_INDEX||{}, data=di.contradictions||[];
  var el=$('an-contradictions');if(!el)return;
  if(!data.length){el.innerHTML='<div style="color:var(--text-muted);padding:10px;">\u0644\u0627 \u062a\u0648\u062c\u062f \u062a\u0646\u0627\u0642\u0636\u0627\u062a</div>';return;}
  el.innerHTML=data.map(function(c){
    return '<div style="padding:8px;border-bottom:1px solid var(--ui-border2);direction:rtl;"><div style="font-weight:700;color:var(--burg-700);font-size:12px;">D'+c.day+' \xb7 '+c.date+'</div><div style="font-size:11px;color:var(--text-secondary);">'+c.label+'</div></div>';
  }).join('');
}

// ═══ D17: JAMMING DAILY CHART ═══════════════════════════════════
function renderJammingChart(){
  var jc=JAMMING_CORRELATION||{}, days=jc.daily||[];
  if(!days.length)return;
  var ctx=document.getElementById('an-chart-jamming');
  if(!ctx||typeof Chart==='undefined')return;
  if(anChartJam){anChartJam.destroy();anChartJam=null;}
  var labels=days.map(function(d){return d.date?d.date.slice(5):'';});
  var data=days.map(function(d){return d.me_avg_pct||0;});
  var colors=data.map(function(v){return v>15?'rgba(255,17,68,.85)':v>8?'rgba(255,136,0,.85)':'rgba(255,204,68,.7)';});
  anChartJam=new Chart(ctx,{type:'bar',data:{labels:labels,datasets:[{label:'\u062a\u0634\u0648\u064a\u0634 GPS %',data:data,backgroundColor:colors,borderWidth:0,borderRadius:2}]},
    options:{responsive:true,maintainAspectRatio:false,animation:false,
      plugins:{legend:{display:false}},
      scales:{x:{ticks:{font:{size:8},maxRotation:45},grid:{display:false}},y:{ticks:{font:{size:9}},grid:{color:'rgba(0,0,0,.05)'},beginAtZero:true}}
    }});
}

// ═══ D18: JAMMING BY ZONE ═══════════════════════════════════════
function renderJamZones(){
  var jc=JAMMING_CORRELATION||{}, zoneData=jc.zone_daily||{};
  var el=$('an-jam-zones');if(!el)return;
  if(!jc.has_cell_data){el.innerHTML='<div style="color:var(--text-muted);padding:10px;">\u0644\u0627 \u062a\u0648\u062c\u062f \u0628\u064a\u0627\u0646\u0627\u062a \u062e\u0644\u0627\u064a\u0627</div>';return;}
  var zones=['Hormuz','Gulf','Iraq','Lebanon','Iran','Red Sea'];
  var zoneAr={Hormuz:'\u0647\u0631\u0645\u0632',Gulf:'\u0627\u0644\u062e\u0644\u064a\u062c',Iraq:'\u0627\u0644\u0639\u0631\u0627\u0642',Lebanon:'\u0644\u0628\u0646\u0627\u0646',Iran:'\u0625\u064a\u0631\u0627\u0646','Red Sea':'\u0627\u0644\u0628\u062d\u0631 \u0627\u0644\u0623\u062d\u0645\u0631'};
  var maxDays=0;
  zones.forEach(function(z){var d=zoneData[z]||[];var active=d.filter(function(dd){return dd.avg_pct>1;}).length;if(active>maxDays)maxDays=active;});
  el.innerHTML=zones.map(function(z){
    var d=zoneData[z]||[];
    var activeDays=d.filter(function(dd){return dd.avg_pct>1;}).length;
    var pct=maxDays>0?Math.round(activeDays/maxDays*100):0;
    return '<div class="an-bar-row"><div class="an-bar-label">'+zoneAr[z]+'</div><div class="an-bar-wrap"><div class="an-bar-fill" style="width:'+pct+'%;background:'+(activeDays>20?'#ff1144':activeDays>10?'#ff8800':'#ffcc44')+';"></div></div><div class="an-bar-value">'+activeDays+' \u064a\u0648\u0645</div></div>';
  }).join('');
}

// ═══ D19: JAMMING VS STRIKES ════════════════════════════════════
function renderJamCorrelation(){
  var jc=JAMMING_CORRELATION||{}, days=jc.correlation_days||[];
  if(!days.length)return;
  var ctx=document.getElementById('an-chart-jam-corr');
  if(!ctx||typeof Chart==='undefined')return;
  if(anChartJamCorr){anChartJamCorr.destroy();anChartJamCorr=null;}
  var labels=days.map(function(d){return 'D'+d.day;});
  anChartJamCorr=new Chart(ctx,{type:'bar',data:{labels:labels,datasets:[
    {label:'\u0623\u062d\u062f\u0627\u062b \u0639\u0633\u0643\u0631\u064a\u0629',data:days.map(function(d){return d.events;}),backgroundColor:'rgba(184,0,56,.6)',borderWidth:0,yAxisID:'y'},
    {label:'\u062a\u0634\u0648\u064a\u0634 %',data:days.map(function(d){return d.jam_pct;}),type:'line',borderColor:'#ff8800',borderWidth:2,pointRadius:2,fill:false,yAxisID:'y1'}
  ]},options:{responsive:true,maintainAspectRatio:false,animation:false,
    plugins:{legend:{display:true,labels:{font:{size:9},boxWidth:10}}},
    scales:{x:{ticks:{font:{size:8}},grid:{display:false}},
      y:{ticks:{font:{size:9}},grid:{color:'rgba(0,0,0,.04)'},beginAtZero:true,title:{display:true,text:'\u0623\u062d\u062f\u0627\u062b',font:{size:9}}},
      y1:{type:'linear',position:'left',ticks:{font:{size:9}},grid:{display:false},beginAtZero:true,title:{display:true,text:'\u062a\u0634\u0648\u064a\u0634 %',font:{size:9}}}
    }
  }});
}

// ═══ E. MARITIME SECTION ════════════════════════════════════════
function renderMaritimeSection(){
  var mt=MARITIME_THREAT||{};
  var el;
  el=$('mar-total-vessels');if(el)el.textContent=(mt.total_vessels||0).toLocaleString();
  el=$('mar-tanker-disruption');if(el)el.textContent=(mt.tanker_disruption_pct||0)+'%';
  el=$('mar-attacks');if(el)el.textContent=mt.vessel_attacks||0;

  // Zone risk table
  var zones=mt.zones||[];
  el=$('an-mar-zones');if(el){
    var lmap={critical:'\u062d\u0631\u062c',high:'\u0645\u0631\u062a\u0641\u0639',medium:'\u0645\u062a\u0648\u0633\u0637',low:'\u0645\u0646\u062e\u0641\u0636'};
    var cmap={critical:'#cc0020',high:'#cc6600',medium:'#997700',low:'#287840'};
    el.innerHTML=zones.map(function(z){
      return '<div class="an-bar-row"><div class="an-bar-label" style="width:160px;">'+z.name+'</div><div style="font-size:10px;font-weight:700;color:'+cmap[z.risk_level]+';width:50px;text-align:center;">'+lmap[z.risk_level]+'</div><div class="an-bar-wrap"><div class="an-bar-fill" style="width:'+z.risk_score+'%;background:'+cmap[z.risk_level]+';"></div></div><div class="an-bar-value">'+z.risk_score+'</div></div>';
    }).join('');
  }

  // Hormuz flags
  var flags=mt.hormuz_by_flag||[];
  el=$('an-hormuz-flags');if(el&&flags.length){
    var maxF=flags[0].count;
    el.innerHTML=flags.slice(0,10).map(function(f){
      var pct=Math.round(f.count/maxF*100);
      var emoji='';try{var a=f.flag.toUpperCase().charCodeAt(0)-65+0x1F1E6,b=f.flag.toUpperCase().charCodeAt(1)-65+0x1F1E6;emoji=String.fromCodePoint(a,b);}catch(e){}
      return '<div class="an-bar-row"><div class="an-bar-label" style="width:80px;">'+emoji+' '+f.flag+'</div><div class="an-bar-wrap"><div class="an-bar-fill" style="width:'+pct+'%;background:#00659a;"></div></div><div class="an-bar-value">'+f.count+'</div></div>';
    }).join('');
  }

  // Tanker flow
  el=$('an-tanker-flow');if(el){
    var total=Math.max((mt.moving_tankers||0)+(mt.stopped_tankers||0),1);
    var movPct=Math.round((mt.moving_tankers||0)/total*100);
    el.innerHTML='<div style="display:flex;gap:16px;margin-bottom:10px;direction:rtl;"><div style="text-align:center;flex:1;"><div style="font-family:JetBrains Mono,monospace;font-size:20px;font-weight:700;color:#287840;">'+(mt.moving_tankers||0)+'</div><div style="font-size:10px;color:var(--text-muted);">\u0645\u062a\u062d\u0631\u0643\u0629</div></div><div style="text-align:center;flex:1;"><div style="font-family:JetBrains Mono,monospace;font-size:20px;font-weight:700;color:#cc0020;">'+(mt.stopped_tankers||0)+'</div><div style="font-size:10px;color:var(--text-muted);">\u0645\u062a\u0648\u0642\u0641\u0629</div></div><div style="text-align:center;flex:1;"><div style="font-family:JetBrains Mono,monospace;font-size:20px;font-weight:700;color:#0066cc;">'+(mt.hormuz_vessels||0)+'</div><div style="font-size:10px;color:var(--text-muted);">\u0641\u064a \u0647\u0631\u0645\u0632</div></div></div>'
    +'<div style="background:var(--ui-border2);border-radius:4px;height:16px;overflow:hidden;"><div style="width:'+movPct+'%;height:100%;background:#287840;display:inline-block;"></div><div style="width:'+(100-movPct)+'%;height:100%;background:#cc0020;display:inline-block;"></div></div>'
    +(mt.blockade_signal?'<div style="margin-top:6px;padding:4px 8px;background:rgba(220,0,30,.1);border-radius:4px;font-size:11px;font-weight:700;color:#cc0020;direction:rtl;">\u26a0 \u0625\u0634\u0627\u0631\u0629 \u062d\u0635\u0627\u0631 — \u0627\u0644\u0645\u062a\u0648\u0642\u0641\u0629 \u0623\u0643\u062b\u0631 \u0645\u0646 \u0636\u0639\u0641 \u0627\u0644\u0645\u062a\u062d\u0631\u0643\u0629</div>':'');
  }

  // High interest
  el=$('an-high-interest');if(el){
    var hi=mt.high_interest||{};
    var gd=mt.going_dark||{};
    el.innerHTML='<div style="direction:rtl;font-size:12px;"><div style="margin-bottom:8px;"><span style="font-weight:700;color:var(--burg-600);">\u0633\u0641\u0646 \u0639\u0627\u0644\u064a\u0629 \u0627\u0644\u0627\u0647\u062a\u0645\u0627\u0645:</span> '+(hi.count||0)+'</div>'
    +'<div style="margin-bottom:8px;"><span style="font-weight:700;color:var(--burg-600);">\u0623\u0642\u0641\u0644\u062a AIS:</span> '+(gd.count||0)+'</div>'
    +(hi.by_flag?'<div style="font-size:11px;color:var(--text-muted);">\u0623\u0639\u0644\u0627\u0645: '+Object.entries(hi.by_flag).map(function(e){return e[0]+': '+e[1];}).join(' \xb7 ')+'</div>':'')
    +'</div>';
  }

  // Attacked vessels analysis
  el=$('an-av-analysis');if(el){
    var avz=mt.av_by_zone||{}, ava=mt.av_by_attacker||{}, avf=mt.av_by_flag||[];
    var html='';
    // By zone
    html+='<div class="an-card"><div class="an-card-title">\u062d\u0633\u0628 \u0627\u0644\u0645\u0646\u0637\u0642\u0629</div>';
    Object.entries(avz).sort(function(a,b){return b[1]-a[1];}).forEach(function(e){
      html+='<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:11px;border-bottom:1px solid var(--ui-border2);"><span>'+e[0]+'</span><span style="font-weight:700;">'+e[1]+'</span></div>';
    });
    html+='</div>';
    // By attacker
    html+='<div class="an-card"><div class="an-card-title">\u062d\u0633\u0628 \u0627\u0644\u0645\u0647\u0627\u062c\u0645</div>';
    Object.entries(ava).sort(function(a,b){return b[1]-a[1];}).forEach(function(e){
      html+='<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:11px;border-bottom:1px solid var(--ui-border2);"><span>'+e[0]+'</span><span style="font-weight:700;">'+e[1]+'</span></div>';
    });
    html+='</div>';
    // By flag
    html+='<div class="an-card"><div class="an-card-title">\u062d\u0633\u0628 \u0639\u0644\u0645 \u0627\u0644\u0633\u0641\u064a\u0646\u0629</div>';
    avf.slice(0,8).forEach(function(f){
      html+='<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:11px;border-bottom:1px solid var(--ui-border2);"><span>'+f.flag+'</span><span style="font-weight:700;">'+f.count+'</span></div>';
    });
    html+='</div>';
    el.innerHTML=html;
  }
}


// ═══ NEW MARITIME RENDER FUNCTIONS ═══

function renderHormuzFlow(){
  var el=document.getElementById('an-hormuz-flow');if(!el||!MARITIME_THREAT)return;
  var mt=MARITIME_THREAT;
  var tankers=mt.hormuz_tankers||0,stopped=mt.hormuz_stopped||0,moving=mt.hormuz_moving||0,flow=mt.hormuz_flow_pct||0,disrupt=mt.tanker_disruption_pct||0;
  el.innerHTML='<div style="flex:1;min-width:140px;text-align:center;padding:16px;background:#fef2f2;border-radius:10px;border:1px solid #fecaca;">'
    +'<div style="font-size:36px;font-weight:800;color:#dc2626;font-family:monospace;">'+disrupt+'%</div>'
    +'<div style="font-size:11px;color:#666;margin-top:4px;">تعطل الناقلات</div></div>'
    +'<div style="flex:1;min-width:140px;text-align:center;padding:16px;background:#fefce8;border-radius:10px;border:1px solid #fde68a;">'
    +'<div style="font-size:36px;font-weight:800;color:#d97706;font-family:monospace;">'+flow+'%</div>'
    +'<div style="font-size:11px;color:#666;margin-top:4px;">تدفق فعلي</div></div>'
    +'<div style="flex:1;min-width:140px;text-align:center;padding:16px;background:#f0f9ff;border-radius:10px;border:1px solid #bae6fd;">'
    +'<div style="font-size:36px;font-weight:800;color:#0284c7;font-family:monospace;">'+tankers+'</div>'
    +'<div style="font-size:11px;color:#666;margin-top:4px;">ناقلة في هرمز</div></div>'
    +'<div style="flex:1;min-width:300px;padding:16px;background:#faf5f7;border-radius:10px;border:1px solid #e0c8d0;">'
    +'<div style="font-size:12px;color:#333;line-height:1.8;">'
    +'<span style="color:#dc2626;font-weight:700;">'+stopped+'</span> متوقفة · '
    +'<span style="color:#16a34a;font-weight:700;">'+moving+'</span> متحركة · '
    +(mt.vessel_attacks||0)+' هجوم بحري · '
    +(mt.blockade_signal?'حصار مؤكد':'حصار غير مؤكد')+'</div></div>';
}

function renderSeaRoutes(){
  var el=document.getElementById('an-sea-routes');if(!el||!MARITIME_THREAT)return;
  var mt=MARITIME_THREAT,hormuz=mt.route_hormuz_nm||0,cape=mt.route_cape_nm||0,diff=mt.route_diversion_nm||0;
  var pct=hormuz>0?Math.round(diff/hormuz*100):0,divs=mt.diversions_count||0;
  if(!hormuz&&!cape){el.innerHTML='<div style="color:#999;font-size:12px;">لا تتوفر بيانات المسارات</div>';return;}
  var mx=Math.max(hormuz,cape,1);
  el.innerHTML='<div style="margin-bottom:16px;">'
    +'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;"><span style="font-size:11px;width:120px;text-align:left;">مسار هرمز</span>'
    +'<div style="flex:1;height:24px;background:#f0e0e8;border-radius:4px;overflow:hidden;"><div style="width:'+Math.round(hormuz/mx*100)+'%;height:100%;background:linear-gradient(90deg,#16a34a,#22c55e);border-radius:4px;display:flex;align-items:center;padding:0 8px;">'
    +'<span style="font-size:10px;color:white;font-weight:700;">'+Math.round(hormuz)+' nm</span></div></div></div>'
    +'<div style="display:flex;align-items:center;gap:10px;"><span style="font-size:11px;width:120px;text-align:left;">رأس الرجاء</span>'
    +'<div style="flex:1;height:24px;background:#f0e0e8;border-radius:4px;overflow:hidden;"><div style="width:'+Math.round(cape/mx*100)+'%;height:100%;background:linear-gradient(90deg,#dc2626,#ef4444);border-radius:4px;display:flex;align-items:center;padding:0 8px;">'
    +'<span style="font-size:10px;color:white;font-weight:700;">'+Math.round(cape)+' nm</span></div></div></div></div>'
    +'<div style="display:flex;gap:12px;flex-wrap:wrap;">'
    +'<div style="padding:10px 16px;background:#fef2f2;border-radius:8px;border:1px solid #fecaca;"><span style="font-size:20px;font-weight:800;color:#dc2626;">+'+Math.round(diff)+'</span><span style="font-size:11px;color:#666;margin-right:6px;"> ميل إضافي</span></div>'
    +'<div style="padding:10px 16px;background:#fef2f2;border-radius:8px;border:1px solid #fecaca;"><span style="font-size:20px;font-weight:800;color:#dc2626;">+'+pct+'%</span><span style="font-size:11px;color:#666;margin-right:6px;"> أطول</span></div>'
    +(divs>0?'<div style="padding:10px 16px;background:#fefce8;border-radius:8px;border:1px solid #fde68a;"><span style="font-size:20px;font-weight:800;color:#d97706;">'+divs+'</span><span style="font-size:11px;color:#666;margin-right:6px;"> سفن محوّلة</span></div>':'')+'</div>';
}

function renderGlobalMilitary(){
  var el=document.getElementById('an-global-mil');if(!el||!MARITIME_THREAT)return;
  var gm=MARITIME_THREAT.global_military||{},cp=MARITIME_THREAT.country_presence||[];
  var countries=[{code:'US',name:'الولايات المتحدة',color:'#1d4ed8'},{code:'GB',name:'المملكة المتحدة',color:'#7c3aed'},{code:'CN',name:'الصين',color:'#dc2626'},{code:'RU',name:'روسيا',color:'#059669'},{code:'IL',name:'إسرائيل',color:'#d97706'}];
  var rows=countries.map(function(c){
    var gc=(gm[c.code]||{}).count||0,rc=0;
    cp.forEach(function(p){if(p.code===c.code)rc=p.military||0;});
    return '<tr><td style="padding:8px 10px;font-weight:600;border-bottom:1px solid #f0e0e8;">'+c.name+'</td>'
      +'<td style="padding:8px 10px;text-align:center;border-bottom:1px solid #f0e0e8;color:'+c.color+';font-weight:700;">'+gc+'</td>'
      +'<td style="padding:8px 10px;text-align:center;border-bottom:1px solid #f0e0e8;font-weight:700;">'+rc+'</td></tr>';
  }).join('');
  el.innerHTML='<table style="width:100%;border-collapse:collapse;font-size:12px;"><thead><tr style="background:#faf5f7;"><th style="padding:8px 10px;text-align:right;border-bottom:2px solid #c0406a;">الدولة</th>'
    +'<th style="padding:8px 10px;text-align:center;border-bottom:2px solid #c0406a;">عالمياً (AIS)</th>'
    +'<th style="padding:8px 10px;text-align:center;border-bottom:2px solid #c0406a;">في المنطقة</th></tr></thead><tbody>'+rows+'</tbody></table>'
    +'<div style="font-size:10px;color:#999;margin-top:6px;">* السفن العسكرية التي تبث AIS فقط — السفن الحربية الفعلية لا تبث موقعها</div>';
}

function renderVesselHistories(){
  var el=document.getElementById('an-vessel-hist');if(!el||!MARITIME_THREAT)return;
  var vh=MARITIME_THREAT.vessel_histories||{},keys=Object.keys(vh);
  if(!keys.length){el.innerHTML='<div style="color:#999;font-size:12px;">لا توجد بيانات تاريخية</div>';return;}
  var rows=keys.map(function(mmsi){
    var h=vh[mmsi],pos=h.positions||[],first=pos[0]||{},last=pos[pos.length-1]||{};
    var fe='';try{var f=h.flag||'';if(f.length===2){var a=f.toUpperCase().charCodeAt(0)-65+0x1F1E6,b=f.toUpperCase().charCodeAt(1)-65+0x1F1E6;fe=String.fromCodePoint(a,b)+' ';}}catch(e){}
    return '<tr><td style="padding:6px 8px;font-weight:600;border-bottom:1px solid #f0e0e8;">'+fe+(h.name||mmsi)+'</td>'
      +'<td style="padding:6px 8px;text-align:center;border-bottom:1px solid #f0e0e8;">'+h.flag+'</td>'
      +'<td style="padding:6px 8px;text-align:center;border-bottom:1px solid #f0e0e8;">'+(h.category||'—')+'</td>'
      +'<td style="padding:6px 8px;text-align:center;border-bottom:1px solid #f0e0e8;">'+pos.length+'</td>'
      +'<td style="padding:6px 8px;font-size:10px;border-bottom:1px solid #f0e0e8;">'+(first.date||'').slice(0,10)+'</td>'
      +'<td style="padding:6px 8px;font-size:10px;border-bottom:1px solid #f0e0e8;">'+(last.date||'').slice(0,10)+'</td></tr>';
  }).join('');
  el.innerHTML='<table style="width:100%;border-collapse:collapse;font-size:11px;"><thead><tr style="background:#faf5f7;">'
    +'<th style="padding:6px 8px;text-align:right;border-bottom:2px solid #c0406a;">السفينة</th>'
    +'<th style="padding:6px 8px;text-align:center;border-bottom:2px solid #c0406a;">العلم</th>'
    +'<th style="padding:6px 8px;text-align:center;border-bottom:2px solid #c0406a;">النوع</th>'
    +'<th style="padding:6px 8px;text-align:center;border-bottom:2px solid #c0406a;">مواقع</th>'
    +'<th style="padding:6px 8px;text-align:center;border-bottom:2px solid #c0406a;">أول رصد</th>'
    +'<th style="padding:6px 8px;text-align:center;border-bottom:2px solid #c0406a;">آخر رصد</th></tr></thead><tbody>'+rows+'</tbody></table>';
}

function renderInspections(){
  var el=document.getElementById('an-inspections');if(!el||!MARITIME_THREAT)return;
  var insp=MARITIME_THREAT.inspections||[],total=MARITIME_THREAT.inspections_total||0,detained=MARITIME_THREAT.inspections_detained||0;
  if(!insp.length){el.innerHTML='<div style="color:#999;font-size:12px;">لا توجد تفتيشات مسجّلة في المنطقة</div>';return;}
  var rows=insp.map(function(r){
    return '<tr><td style="padding:6px 8px;font-weight:600;border-bottom:1px solid #f0e0e8;">'+(r.vessel_name||'—')+'</td>'
      +'<td style="padding:6px 8px;border-bottom:1px solid #f0e0e8;">'+(r.port||'—')+'</td>'
      +'<td style="padding:6px 8px;font-size:10px;border-bottom:1px solid #f0e0e8;">'+(r.date||'').slice(0,10)+'</td>'
      +'<td style="padding:6px 8px;text-align:center;border-bottom:1px solid #f0e0e8;">'+(r.deficiencies||0)+'</td>'
      +'<td style="padding:6px 8px;text-align:center;border-bottom:1px solid #f0e0e8;">'+(r.detained?'<span style="color:#dc2626;font-weight:700;">محتجزة</span>':'—')+'</td></tr>';
  }).join('');
  el.innerHTML='<div style="display:flex;gap:10px;margin-bottom:12px;">'
    +'<div style="padding:8px 14px;background:#f0f9ff;border-radius:6px;font-size:11px;">إجمالي: <strong>'+total+'</strong></div>'
    +'<div style="padding:8px 14px;background:#fef2f2;border-radius:6px;font-size:11px;">محتجزة: <strong style="color:#dc2626;">'+detained+'</strong></div></div>'
    +'<table style="width:100%;border-collapse:collapse;font-size:11px;"><thead><tr style="background:#faf5f7;">'
    +'<th style="padding:6px 8px;text-align:right;border-bottom:2px solid #c0406a;">السفينة</th>'
    +'<th style="padding:6px 8px;text-align:right;border-bottom:2px solid #c0406a;">الميناء</th>'
    +'<th style="padding:6px 8px;text-align:center;border-bottom:2px solid #c0406a;">التاريخ</th>'
    +'<th style="padding:6px 8px;text-align:center;border-bottom:2px solid #c0406a;">مخالفات</th>'
    +'<th style="padding:6px 8px;text-align:center;border-bottom:2px solid #c0406a;">الحالة</th></tr></thead><tbody>'+rows+'</tbody></table>';
}

function renderCompanyProfiles(){
  var el=document.getElementById('an-companies');if(!el||!MARITIME_THREAT)return;
  var cp=MARITIME_THREAT.company_profiles||{},keys=Object.keys(cp);
  if(!keys.length){el.innerHTML='<div style="color:#999;font-size:12px;">لا توجد بيانات شركات</div>';return;}
  var rows=keys.map(function(name){
    var c=cp[name];
    return '<tr><td style="padding:6px 8px;font-weight:600;border-bottom:1px solid #f0e0e8;">'+(c.name||name)+'</td>'
      +'<td style="padding:6px 8px;border-bottom:1px solid #f0e0e8;">'+(c.country||'—')+'</td>'
      +'<td style="padding:6px 8px;border-bottom:1px solid #f0e0e8;">'+(c.type||'—')+'</td>'
      +'<td style="padding:6px 8px;text-align:center;border-bottom:1px solid #f0e0e8;">'+(c.fleet_size||'—')+'</td>'
      +'<td style="padding:6px 8px;border-bottom:1px solid #f0e0e8;">'+(c.status||'—')+'</td></tr>';
  }).join('');
  el.innerHTML='<table style="width:100%;border-collapse:collapse;font-size:11px;"><thead><tr style="background:#faf5f7;">'
    +'<th style="padding:6px 8px;text-align:right;border-bottom:2px solid #c0406a;">الشركة</th>'
    +'<th style="padding:6px 8px;text-align:right;border-bottom:2px solid #c0406a;">الدولة</th>'
    +'<th style="padding:6px 8px;text-align:right;border-bottom:2px solid #c0406a;">النوع</th>'
    +'<th style="padding:6px 8px;text-align:center;border-bottom:2px solid #c0406a;">الأسطول</th>'
    +'<th style="padding:6px 8px;text-align:right;border-bottom:2px solid #c0406a;">الحالة</th></tr></thead><tbody>'+rows+'</tbody></table>';
}


// ═══ E0. COUNTRY PRESENCE ═══════════════════════════════════════
function renderCountryPresence(){
  var mt=MARITIME_THREAT||{};
  var cp=mt.country_presence||[];
  if(!cp.length)return;

  // Stat cards
  var el=$('an-country-presence-cards');
  if(el){
    var flagEmoji=function(code){
      try{var a=code.toUpperCase().charCodeAt(0)-65+0x1F1E6,b=code.toUpperCase().charCodeAt(1)-65+0x1F1E6;return String.fromCodePoint(a,b);}catch(e){return '';}
    };
    el.innerHTML=cp.map(function(c){
      return '<div class="an-card an-stat-card" style="padding:10px;">'
        +'<div style="font-size:20px;">'+flagEmoji(c.code)+'</div>'
        +'<div class="an-stat-value">'+c.total+'</div>'
        +'<div class="an-stat-label">'+c.name_ar+'</div>'
        +'<div style="font-size:10px;color:var(--text-muted);margin-top:4px;">'
        +c.military+' \u0639\u0633\u0643\u0631\u064a | '+c.tanker+' \u0646\u0627\u0642\u0644\u0629'
        +'</div></div>';
    }).join('');
  }

  // Country vessels chart
  var ctx=document.getElementById('an-chart-country-vessels');
  if(ctx&&typeof Chart!=='undefined'){
    var labels=cp.map(function(c){return c.name_ar;});
    new Chart(ctx,{type:'bar',data:{labels:labels,datasets:[
      {label:'\u0639\u0633\u0643\u0631\u064a',data:cp.map(function(c){return c.military;}),backgroundColor:'rgba(220,0,30,.8)',stack:'s'},
      {label:'\u0646\u0627\u0642\u0644\u0627\u062a',data:cp.map(function(c){return c.tanker;}),backgroundColor:'rgba(0,120,200,.7)',stack:'s'},
      {label:'\u0628\u0636\u0627\u0626\u0639',data:cp.map(function(c){return c.cargo;}),backgroundColor:'rgba(80,160,80,.7)',stack:'s'},
      {label:'\u0623\u062e\u0631\u0649',data:cp.map(function(c){return c.other;}),backgroundColor:'rgba(150,150,150,.5)',stack:'s'}
    ]},options:{responsive:true,maintainAspectRatio:false,animation:false,
      plugins:{legend:{display:true,labels:{font:{size:9},boxWidth:10}}},
      scales:{x:{stacked:true,ticks:{font:{size:10}},grid:{display:false}},y:{stacked:true,ticks:{font:{size:9}},grid:{color:'rgba(0,0,0,.04)'},beginAtZero:true}}
    }});
  }

  // Military vessels table
  el=$('an-mil-vessels');
  if(el){
    var allMil=[];
    cp.forEach(function(c){
      (c.military_vessels||[]).forEach(function(v){
        v._country=c.name_ar;v._code=c.code;
        allMil.push(v);
      });
    });
    if(!allMil.length){
      el.innerHTML='<div style="color:var(--text-muted);padding:10px;font-size:11px;">\u0644\u0627 \u062a\u0648\u062c\u062f \u0633\u0641\u0646 \u0639\u0633\u0643\u0631\u064a\u0629 \u0645\u0631\u0635\u0648\u062f\u0629</div>';
      return;
    }
    el.innerHTML='<table style="width:100%;border-collapse:collapse;font-size:11px;"><thead><tr style="background:var(--ui-bg3);">'
      +'<th style="text-align:right;padding:5px 8px;">\u0627\u0644\u062f\u0648\u0644\u0629</th>'
      +'<th style="text-align:right;padding:5px 8px;">\u0627\u0644\u0633\u0641\u064a\u0646\u0629</th>'
      +'<th style="padding:5px 8px;">\u0627\u0644\u0646\u0648\u0639</th>'
      +'<th style="padding:5px 8px;">\u0627\u0644\u0645\u0646\u0637\u0642\u0629</th>'
      +'<th style="padding:5px 8px;">\u0627\u0644\u0633\u0631\u0639\u0629</th>'
      +'<th style="padding:5px 8px;">\u0627\u0644\u062d\u0627\u0644\u0629</th></tr></thead><tbody>'
      +allMil.map(function(v){
        var dark=v.going_dark?'<span style="color:#cc0020;font-weight:700;">\u0645\u0638\u0644\u0645\u0629</span>':'<span style="color:#287840;">\u0646\u0634\u0637\u0629</span>';
        return '<tr><td style="padding:4px 8px;border-bottom:1px solid var(--ui-border2);font-weight:700;">'+v._country+'</td>'
          +'<td style="padding:4px 8px;border-bottom:1px solid var(--ui-border2);font-family:JetBrains Mono,monospace;font-size:10px;">'+v.name+'</td>'
          +'<td style="padding:4px 8px;border-bottom:1px solid var(--ui-border2);">'+v.type+'</td>'
          +'<td style="padding:4px 8px;border-bottom:1px solid var(--ui-border2);">'+v.zone+'</td>'
          +'<td style="padding:4px 8px;border-bottom:1px solid var(--ui-border2);font-family:monospace;">'+(v.speed||0)+' kn</td>'
          +'<td style="padding:4px 8px;border-bottom:1px solid var(--ui-border2);">'+dark+'</td></tr>';
      }).join('')
      +'</tbody></table>';
  }
}

// ═══ E. CASUALTIES + SAT-E ══════════════════════════════════════
function renderCasualtiesAndSatE(){
  var mt=MARITIME_THREAT||{};

  // Casualties count
  var el=$('an-casualties-count');
  if(el) el.textContent=mt.casualties_count||0;

  // Casualties list
  var cas=mt.casualties||[];
  el=$('an-casualties-list');
  if(el){
    if(!cas.length){
      el.innerHTML='<div style="color:var(--text-muted);padding:10px;font-size:11px;">\u0644\u0627 \u062a\u0648\u062c\u062f \u0628\u064a\u0627\u0646\u0627\u062a</div>';
    } else {
      el.innerHTML=cas.slice(0,10).map(function(c){
        return '<div style="padding:6px 8px;border-bottom:1px solid var(--ui-border2);direction:rtl;">'
          +'<div style="display:flex;justify-content:space-between;align-items:center;">'
          +'<span style="font-weight:700;font-size:11px;color:var(--burg-700);">'+(c.vessel_name||'?')+'</span>'
          +'<span style="font-size:9px;font-weight:700;padding:2px 6px;border-radius:3px;background:rgba(220,0,30,.1);color:#cc0020;">'+(c.type||'')+'</span>'
          +'</div>'
          +'<div style="font-size:10px;color:var(--text-muted);margin-top:2px;">'+(c.date||'').slice(0,10)+'</div>'
          +'<div style="font-size:10px;color:var(--text-secondary);margin-top:2px;line-height:1.5;">'+(c.details||'').slice(0,150)+'...</div>'
          +'</div>';
      }).join('');
    }
  }

  // SAT-E count
  el=$('an-sate-count');
  if(el) el.textContent=mt.sat_e_count||0;

  // SAT-E list
  var sate=mt.sat_e_vessels||[];
  el=$('an-sate-list');
  if(el){
    if(!sate.length){
      el.innerHTML='<div style="color:var(--text-muted);padding:10px;font-size:11px;">\u0644\u0627 \u062a\u0648\u062c\u062f \u0633\u0641\u0646 \u0645\u0638\u0644\u0645\u0629</div>';
    } else {
      el.innerHTML=sate.map(function(s){
        return '<div style="padding:6px 8px;border-bottom:1px solid var(--ui-border2);direction:rtl;">'
          +'<div style="font-weight:700;font-size:11px;color:#cc6600;">'+(s.name||s.mmsi)+'</div>'
          +'<div style="font-size:10px;color:var(--text-muted);">\u0639\u0644\u0645: '+(s.flag||'?')+' | \u0645\u0648\u0642\u0639 \u062a\u0642\u062f\u064a\u0631\u064a: '+(s.est_lat||'?')+', '+(s.est_lon||'?')+'</div>'
          +'</div>';
      }).join('');
    }
  }
}


// ═══ F. FLIGHT INTELLIGENCE ═════════════════════════════════════
function renderFlightIntel(){
  var vi=VIP_INTELLIGENCE||{};
  var el;
  el=$('flt-total-vip');if(el)el.textContent=vi.total_vip||0;
  el=$('flt-evac-idx');if(el)el.textContent='+'+(vi.evacuation_index||0)+'%';
  el=$('flt-coincidences');if(el)el.textContent=(vi.coincidences||[]).length;

  // Coincidences
  var coinc=vi.coincidences||[];
  el=$('an-coincidences');if(el){
    el.innerHTML=coinc.map(function(c){
      var gapClass=c.gap_days===0?'same':'near';
      var gapTxt=c.gap_days===0?'\u0646\u0641\u0633 \u0627\u0644\u064a\u0648\u0645':c.gap_days+' \u064a\u0648\u0645';
      return '<div class="an-coincidence"><span class="gap '+gapClass+'">'+gapTxt+'</span> <span class="city">'+c.city+'</span><div class="actor-line">D'+c.day_1+': <strong>'+c.actor_1+'</strong> (\u0645\u0646 '+c.from_1+')</div><div class="actor-line">D'+c.day_2+': <strong>'+c.actor_2+'</strong> (\u0645\u0646 '+c.from_2+')</div></div>';
    }).join('');
  }

  // Shuttle corridors
  var corr=vi.shuttle_corridors||[];
  el=$('an-shuttle-corridors');if(el&&corr.length){
    var maxV=corr[0].vip;
    el.innerHTML=corr.slice(0,12).map(function(r){
      var pct=Math.round(r.vip/maxV*100);
      return '<div class="an-bar-row"><div class="an-bar-label" style="width:200px;font-size:10px;">'+r.route+'</div><div class="an-bar-wrap"><div class="an-bar-fill" style="width:'+pct+'%;background:#b8860b;"></div></div><div class="an-bar-value">'+r.vip+'</div></div>';
    }).join('');
  }

  // Airports
  var arr=vi.top_arrivals||[];
  el=$('an-airports');if(el&&arr.length){
    var maxA=arr[0].total;
    el.innerHTML=arr.slice(0,10).map(function(a){
      var pct=Math.round(a.total/maxA*100);
      return '<div class="an-bar-row"><div class="an-bar-label">'+a.city+'</div><div class="an-bar-wrap"><div class="an-bar-fill" style="width:'+pct+'%;background:#0066cc;"></div></div><div class="an-bar-value" style="width:70px;">'+a.total+' ('+a.vip+' VIP)</div></div>';
    }).join('');
  }

  // Flight log — chronological per VIP
  var fl=vi.flight_log||[];
  el=$('an-dest-timeline');if(el&&fl.length){
    var html='';
    fl.slice(0,12).forEach(function(vip){
      html+='<div style="margin-bottom:16px;border:1px solid var(--ui-border2);border-radius:8px;overflow:hidden;">';
      html+='<div style="background:var(--burg-50,#faf5f7);padding:10px 14px;border-bottom:1px solid var(--ui-border2);display:flex;justify-content:space-between;align-items:center;direction:rtl;">';
      html+='<span style="font-weight:700;font-size:13px;color:var(--burg-700,#7a0028);">'+vip.owner+'</span>';
      html+='<span style="font-size:11px;color:var(--text-muted,#999);font-family:monospace;">'+vip.total+' رحلة</span></div>';
      html+='<div style="padding:8px 14px;direction:rtl;">';
      vip.flights.forEach(function(f,i){
        var isLast=i===vip.flights.length-1;
        var lineColor=f.dep!=='غير محدد'&&f.arr!=='غير محدد'?'var(--burg-400,#c0406a)':'var(--text-muted,#ccc)';
        html+='<div style="display:flex;gap:10px;align-items:flex-start;padding:4px 0;">';
        html+='<div style="min-width:36px;font-family:monospace;font-size:10px;font-weight:700;color:var(--burg-500,#a0304a);padding-top:2px;">D'+f.day+'</div>';
        html+='<div style="width:2px;min-height:20px;background:'+(isLast?'transparent':lineColor)+';margin:0 4px;"></div>';
        html+='<div style="font-size:12px;line-height:1.6;">';
        if(f.dep!=='غير محدد'&&f.arr!=='غير محدد'){
          html+='<span style="color:var(--text-main,#1a1a2e);">'+f.dep+'</span>';
          html+=' <span style="color:var(--burg-400,#c0406a);font-weight:700;"> ← </span> ';
          html+='<span style="font-weight:600;color:var(--burg-700,#7a0028);">'+f.arr+'</span>';
        } else if(f.arr!=='غير محدد'){
          html+='<span style="font-weight:600;color:var(--burg-700,#7a0028);">→ '+f.arr+'</span>';
        } else {
          html+='<span style="color:var(--text-main,#1a1a2e);">'+f.dep+' →</span>';
        }
        html+='</div></div>';
      });
      html+='</div></div>';
    });
    el.innerHTML=html;
  }

  // VIP ranking
  var rank=vi.vip_ranking||[];
  el=$('an-vip-ranking');if(el&&rank.length){
    el.innerHTML=rank.map(function(r){
      return '<div style="padding:8px 10px;border-bottom:1px solid var(--ui-border2);direction:rtl;"><div style="display:flex;justify-content:space-between;"><span style="font-weight:700;font-size:12px;color:var(--burg-700);">'+r.owner+'</span><span style="font-family:JetBrains Mono,monospace;font-size:11px;color:var(--burg-500);">'+r.flights+' \u0631\u062d\u0644\u0629 \xb7 '+r.active_days+' \u064a\u0648\u0645</span></div><div style="font-size:10px;color:var(--text-muted);margin-top:2px;">\u0627\u0644\u0645\u062f\u0646: '+r.cities.join(' \xb7 ')+'</div></div>';
    }).join('');
  }
}

// ═══ G. ISR SECTION ═════════════════════════════════════════════
function renderISRSection(){
  var ia=ISR_CUEING||{};
  var el;
  // Stat cards
  el=$('isr-sat-count');if(el)el.textContent=ia.sat_count||0;
  el=$('isr-active-me');if(el)el.textContent=ia.active_over_me||0;
  el=$('isr-avg-daily');if(el)el.textContent=ia.avg_daily||0;

  // Daily passes chart — spy vs military stacked with day labels
  var days=ia.daily_overflights||[];
  var ctx=document.getElementById('an-chart-isr');
  if(ctx&&days.length&&typeof Chart!=='undefined'){
    var labels=days.map(function(d){return 'D'+d.day_num+(d.date?' ('+d.date.slice(5)+')':'');});
    new Chart(ctx,{type:'bar',data:{labels:labels,datasets:[
      {label:'\u0627\u0633\u062a\u0637\u0644\u0627\u0639',data:days.map(function(d){return d.spy||0;}),backgroundColor:'rgba(184,0,56,.75)',stack:'s',borderWidth:0,borderRadius:2},
      {label:'\u0639\u0633\u0643\u0631\u064a',data:days.map(function(d){return d.military||0;}),backgroundColor:'rgba(200,150,0,.75)',stack:'s',borderWidth:0,borderRadius:2}
    ]},options:{responsive:true,maintainAspectRatio:false,animation:false,
      plugins:{legend:{display:true,labels:{font:{size:9},boxWidth:10,padding:6}}},
      scales:{x:{stacked:true,ticks:{font:{size:7},maxRotation:60},grid:{display:false}},y:{stacked:true,ticks:{font:{size:9}},grid:{color:'rgba(0,0,0,.05)'},beginAtZero:true}}
    }});
  }

  // Top recon satellites
  var sats=ia.top_recon_sats||[];
  el=$('an-top-sats');if(el){
    if(!sats.length){el.innerHTML='<div style="color:var(--text-muted);padding:10px;font-size:11px;direction:rtl;">\u0644\u0627 \u062a\u0648\u062c\u062f \u0628\u064a\u0627\u0646\u0627\u062a \u0623\u0642\u0645\u0627\u0631</div>';return;}
    var maxD=sats[0].days_over_me;
    var catAr={spy:'\u0627\u0633\u062a\u0637\u0644\u0627\u0639',military:'\u0639\u0633\u0643\u0631\u064a'};
    el.innerHTML='<table style="width:100%;border-collapse:collapse;font-size:11px;"><thead><tr style="background:var(--ui-bg3);"><th style="text-align:right;padding:6px 8px;">\u0627\u0644\u0642\u0645\u0631</th><th style="padding:6px 8px;">\u0627\u0644\u0646\u0648\u0639</th><th style="padding:6px 8px;width:40%;">\u0623\u064a\u0627\u0645 \u0641\u0648\u0642 \u0627\u0644\u0645\u0646\u0637\u0642\u0629</th></tr></thead><tbody>'
    +sats.map(function(s){
      var pct=Math.round(s.days_over_me/maxD*100);
      var catName=catAr[s.cat]||s.cat;
      return '<tr><td style="padding:4px 8px;font-weight:700;font-family:JetBrains Mono,monospace;font-size:10px;border-bottom:1px solid var(--ui-border2);">'+s.name+'</td>'
        +'<td style="padding:4px 8px;border-bottom:1px solid var(--ui-border2);"><span style="font-size:9px;padding:2px 6px;border-radius:3px;background:'+(s.cat==='spy'?'rgba(184,0,56,.1);color:#b80038':'rgba(0,100,180,.1);color:#0066aa')+'">'+catName+'</span></td>'
        +'<td style="padding:4px 8px;border-bottom:1px solid var(--ui-border2);"><div style="display:flex;align-items:center;gap:6px;"><div style="flex:1;background:var(--ui-border2);border-radius:3px;height:10px;overflow:hidden;"><div style="width:'+pct+'%;height:100%;background:'+(s.cat==='spy'?'var(--burg-400)':'#0066aa')+';border-radius:3px;"></div></div><span style="font-family:JetBrains Mono,monospace;font-size:10px;font-weight:700;min-width:25px;">'+s.days_over_me+'</span></div></td></tr>';
    }).join('')
    +'</tbody></table>';
  }
}

// ═══ H. THREAT SCORE ════════════════════════════════════════════
function renderThreatScore(){
  var cp=CONFLICT_PREDICTION||{};
  var score=cp.score||0, level=cp.level||'unknown', comps=cp.components||{};
  var el=$('an-score-pct');if(el)el.textContent=Math.round(score);
  var arc=$('an-arc');if(arc){var circ=251.33;arc.style.strokeDashoffset=circ-(circ*score/100);arc.style.stroke=score<30?'#287840':score<55?'#c87800':score<80?'#b80038':'#ff1a5e';}
  var badge=$('an-score-badge');if(badge){
    var cls=score<30?'low':score<55?'medium':score<80?'high':'critical';
    var txt=score<30?'\u0645\u0646\u062e\u0641\u0636':'\u0645\u062a\u0648\u0633\u0637';
    if(score>=55)txt='\u0645\u0631\u062a\u0641\u0639';
    if(score>=75)txt='\u062d\u0631\u062c';
    badge.className='an-score-badge '+cls;badge.textContent=txt;
  }
  // Component labels in Arabic
  var compLabels={
    'Escalation momentum':'\u0632\u062e\u0645 \u0627\u0644\u062a\u0635\u0627\u0639\u062f \u0627\u0644\u0639\u0633\u0643\u0631\u064a',
    'Political pressure':'\u0627\u0644\u0636\u063a\u0637 \u0627\u0644\u0633\u064a\u0627\u0633\u064a',
    'Maritime threat':'\u062a\u0647\u062f\u064a\u062f \u0628\u062d\u0631\u064a (\u0647\u0631\u0645\u0632)',
    'GPS jamming signal':'\u0646\u0634\u0627\u0637 \u0627\u0644\u062a\u0634\u0648\u064a\u0634',
    'VIP activity index':'\u062d\u0631\u0643\u0629 \u0643\u0628\u0627\u0631 \u0627\u0644\u0645\u0633\u0624\u0648\u0644\u064a\u0646'
  };
  var compDescs={
    'Escalation momentum':'\u0645\u0628\u0646\u064a \u0639\u0644\u0649 \u0639\u062f\u062f \u0627\u0644\u0636\u0631\u0628\u0627\u062a \u0648\u062d\u062f\u062a\u0647\u0627 \u0641\u064a \u0622\u062e\u0631 3 \u0623\u064a\u0627\u0645',
    'Political pressure':'\u0635\u0627\u0641\u064a \u0627\u0644\u0623\u062d\u062f\u0627\u062b \u0627\u0644\u062a\u0635\u0627\u0639\u062f\u064a\u0629 \u0645\u0642\u0627\u0628\u0644 \u0627\u0644\u062a\u0647\u062f\u0626\u0629',
    'Maritime threat':'\u062f\u0631\u062c\u0629 \u062e\u0637\u0648\u0631\u0629 \u0645\u0636\u064a\u0642 \u0647\u0631\u0645\u0632',
    'GPS jamming signal':'\u0634\u062f\u0629 \u0627\u0644\u062a\u0634\u0648\u064a\u0634 \u0627\u0644\u0625\u0644\u0643\u062a\u0631\u0648\u0646\u064a',
    'VIP activity index':'\u0639\u062f\u062f \u0631\u062d\u0644\u0627\u062a \u0643\u0628\u0627\u0631 \u0627\u0644\u0645\u0633\u0624\u0648\u0644\u064a\u0646'
  };
  el=$('pred-components');if(el){
    var maxComp=20;
    el.innerHTML=Object.entries(comps).map(function(e){
      var pct=Math.round(e[1]/maxComp*100);
      var label=compLabels[e[0]]||e[0];
      var desc=compDescs[e[0]]||'';
      var maxPts=e[0]==='Escalation momentum'?30:e[0]==='Political pressure'?20:e[0]==='Maritime threat'?20:e[0]==='GPS jamming signal'?15:15;
      return '<div style="margin-bottom:8px;direction:rtl;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;"><span style="font-size:12px;font-weight:700;color:var(--burg-700);">'+label+'</span><span style="font-family:JetBrains Mono,monospace;font-size:11px;font-weight:700;color:var(--burg-500);">'+e[1]+' / '+maxPts+'</span></div><div class="an-bar-wrap"><div class="an-bar-fill" style="width:'+Math.round(e[1]/maxPts*100)+'%;background:'+(pct>60?'#b80038':pct>30?'#cc6600':'#287840')+';"></div></div><div style="font-size:9px;color:var(--text-muted);margin-top:1px;">'+desc+'</div></div>';
    }).join('');
  }
  el=$('pred-interpretation');if(el){
    var interpAr=score>=75?'\u0645\u0633\u062a\u0648\u0649 \u0627\u0644\u062a\u0647\u062f\u064a\u062f \u062d\u0631\u062c \u2014 \u0627\u062d\u062a\u0645\u0627\u0644\u064a\u0629 \u0639\u0627\u0644\u064a\u0629 \u0644\u062a\u0635\u0639\u064a\u062f \u0639\u0633\u0643\u0631\u064a \u0643\u0628\u064a\u0631 \u0641\u064a \u0627\u0644\u0623\u064a\u0627\u0645 \u0627\u0644\u0642\u0627\u062f\u0645\u0629'
      :score>=55?'\u0645\u0633\u062a\u0648\u0649 \u0627\u0644\u062a\u0647\u062f\u064a\u062f \u0645\u0631\u062a\u0641\u0639 \u2014 \u0627\u0644\u0645\u0624\u0634\u0631\u0627\u062a \u062a\u0634\u064a\u0631 \u0625\u0644\u0649 \u0627\u0633\u062a\u0645\u0631\u0627\u0631 \u0627\u0644\u0646\u0634\u0627\u0637 \u0627\u0644\u0639\u0633\u0643\u0631\u064a \u0628\u0648\u062a\u064a\u0631\u0629 \u0645\u0644\u0645\u0648\u0633\u0629'
      :score>=35?'\u0645\u0633\u062a\u0648\u0649 \u0627\u0644\u062a\u0647\u062f\u064a\u062f \u0645\u062a\u0648\u0633\u0637 \u2014 \u0646\u0634\u0627\u0637 \u0639\u0633\u0643\u0631\u064a \u0645\u062d\u062f\u0648\u062f \u0645\u0639 \u0627\u062d\u062a\u0645\u0627\u0644\u064a\u0629 \u0627\u0644\u062a\u0635\u0639\u064a\u062f'
      :'\u0645\u0633\u062a\u0648\u0649 \u0627\u0644\u062a\u0647\u062f\u064a\u062f \u0645\u0646\u062e\u0641\u0636 \u2014 \u0627\u0644\u0648\u0636\u0639 \u0647\u0627\u062f\u0626 \u0646\u0633\u0628\u064a\u0627\u064b';
    el.textContent=interpAr;
  }
}


</""" + """script>""")

print("Part 3 written:", len(_P3), "chars")