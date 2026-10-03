# c15_html_css.py
# HTML Part 1: CSS + head
# Auto-extracted from Cell 15

# CELL 8 — Part 1 of 4  [REDESIGNED]
# CSS + HTML head
# Key changes:
#   1. Timeline redesigned: side category selector + single active row
#   2. Timeline categories: War/Flights/Satellites/Jamming/Vessels/Marine
#   3. Analytics page: new panels for all Cell 9 modules
#   4. Flights layer: VIP (gold) + Private Jets (white) toggles
#   5. Vessel attacks on globe with brief card
#   6. Fonts scaled up throughout for readability
#   7. New CSS for analytics charts, risk panels, prediction score

_P1 = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__SYSTEM_NAME__ — __WORKSPACE_NAME__</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@400;500;700;900&family=JetBrains+Mono:wght@400;700&family=IBM+Plex+Sans+Arabic:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{
  /* ── Burgundy palette ──────────────────────────── */
  --burg-900:#1a0008;--burg-800:#3a0012;--burg-700:#5c0020;
  --burg-600:#7a0028;--burg-500:#960030;--burg-400:#b80038;
  --burg-300:#d4003a;--burg-200:#e8004a;--burg-100:#ff1a5e;
  --gold:#b8860b;--gold-lt:#d4a017;--gold-dim:#7a5a08;
  --green:#1a7a3a;--green-lt:#22a050;
  --blue:#0055aa;--blue-lt:#0077cc;
  --red-alert:#ff2200;

  /* ── UI surfaces ───────────────────────────────── */
  --ui-bg:#ffffff;--ui-bg2:#f7f2f4;--ui-bg3:#f0e8ec;--ui-bg4:#e8dce2;
  --ui-border:rgba(180,0,56,.12);
  --ui-border2:rgba(180,0,56,.22);
  --ui-border3:rgba(180,0,56,.38);

  /* ── Text ──────────────────────────────────────── */
  --text-primary:#1a0008;--text-secondary:#5c2030;
  --text-muted:#9a6070;--text-faint:#c8a0b0;

  /* ── Layout ────────────────────────────────────── */
  --topbar-h:56px;
  --bottom-h:160px;   /* single-row timeline — compact */
  --panel-w:180px;
  --right-w:285px;
  --tl-selector-w:110px;  /* category selector sidebar */
}

/* ── Reset & base ──────────────────────────────────────────────── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;background:#e8e0e4;
  font-family:'IBM Plex Sans Arabic','Noto Naskh Arabic',sans-serif;
  color:var(--text-primary);overflow:hidden;}

/* ── Globe ─────────────────────────────────────────────────────── */
#globe{
  position:fixed;
  top:var(--topbar-h);
  bottom:var(--bottom-h);
  left:var(--panel-w);
  right:var(--right-w);
  z-index:0;
}
.cesium-widget,.cesium-widget canvas{width:100%!important;height:100%!important}
.cesium-widget-credits,.cesium-viewer-toolbar,
.cesium-viewer-animationContainer,.cesium-viewer-timelineContainer,
.cesium-viewer-bottom{display:none!important}

/* ── Panels ────────────────────────────────────────────────────── */
.panel{
  position:fixed;top:var(--topbar-h);bottom:var(--bottom-h);
  z-index:100;background:var(--ui-bg);
  display:flex;flex-direction:column;overflow:hidden;
}
#left-panel{
  left:0;width:var(--panel-w);
  border-right:1px solid var(--ui-border3);
  box-shadow:3px 0 18px rgba(100,0,30,.08);
}
#right-panel{
  right:0;width:var(--right-w);
  border-left:1px solid var(--ui-border3);
  box-shadow:-3px 0 18px rgba(100,0,30,.08);
}
.p-head{
  display:flex;align-items:center;justify-content:space-between;
  padding:6px 10px;flex-shrink:0;
  background:linear-gradient(135deg,var(--burg-800),var(--burg-600));
}
.p-head-title{
  font-family:'Noto Naskh Arabic',serif;font-size:13px;font-weight:700;
  color:#fff;direction:rtl;
}
.p-body{
  flex:1;overflow-y:auto;overflow-x:hidden;
  padding:8px;display:flex;flex-direction:column;gap:6px;
}
.p-body::-webkit-scrollbar{width:4px}
.p-body::-webkit-scrollbar-thumb{background:var(--burg-300);border-radius:2px}

/* ── Cards ─────────────────────────────────────────────────────── */
.card{
  background:var(--ui-bg2);border:1px solid var(--ui-border);
  border-radius:6px;padding:10px;
}
.card-title{
  font-size:11px;font-weight:800;color:var(--burg-600);
  letter-spacing:1.5px;text-transform:uppercase;
  margin-bottom:8px;direction:rtl;
}
.s-row{
  display:flex;justify-content:space-between;align-items:center;
  padding:4px 0;border-bottom:1px solid var(--ui-border);
}
.s-row:last-child{border-bottom:none}
.s-lbl{color:var(--text-muted);font-size:12px;direction:rtl;}
.s-val{
  font-weight:700;font-family:'JetBrains Mono',monospace;
  font-size:12px;color:var(--text-primary);
}
.s-val.gold{color:var(--gold)}.s-val.burg{color:var(--burg-400)}
.s-val.green{color:var(--green-lt)}.s-val.red{color:var(--red-alert)}

/* ── Legend dots ───────────────────────────────────────────────── */
.legend-row{display:flex;align-items:center;gap:8px;padding:4px 0;font-size:12px;color:var(--text-secondary);}
.l-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.l-name{font-size:13px;font-weight:600;color:var(--text-primary)}
.l-count{font-size:11px;color:var(--text-muted)}

/* ── Left panel — camera controls ─────────────────────────────── */
.left-controls{
  flex-shrink:0;border-bottom:2px solid var(--ui-border3);
  overflow-y:auto;max-height:38vh;min-height:80px;
}
.zoom-row{display:flex;gap:4px;justify-content:center;padding:4px 0;}
.dpad{display:grid;grid-template-columns:repeat(3,30px);gap:3px;justify-content:center;}
.presets{display:flex;gap:4px;justify-content:center;flex-wrap:wrap;}
.cb{
  width:30px;height:26px;border-radius:4px;cursor:pointer;
  font-size:13px;font-weight:700;display:flex;align-items:center;
  justify-content:center;border:1px solid var(--ui-border2);
  background:var(--ui-bg2);color:var(--text-secondary);
  transition:all .15s;user-select:none;
}
.cb.wide{width:62px}.cb.xwide{width:94px}
.cb.rst{background:rgba(180,0,56,.10);border-color:rgba(180,0,56,.35);color:var(--burg-500);}
.cb:hover{background:var(--ui-bg3);color:var(--burg-700);border-color:var(--burg-300);}
.cb:active{transform:scale(.92)}
.cb.empty{background:none;border:none;cursor:default}.cb.empty:active{transform:none}
.mode-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px;}
.mode-btn{
  display:flex;flex-direction:column;align-items:center;gap:3px;
  padding:8px 4px;border-radius:5px;cursor:pointer;border:1px solid var(--ui-border2);
  background:var(--ui-bg2);transition:all .15s;
}
.mode-btn:hover{background:var(--ui-bg3);border-color:var(--burg-300);}
.mode-btn.active{background:rgba(180,0,56,.1);border-color:var(--burg-400);}
.mode-icon{font-size:16px}.mode-label{font-size:11px;color:var(--text-muted);font-weight:600;}

/* ── Left panel — filter sections ─────────────────────────────── */
.filter-section{padding:8px 10px;border-bottom:1px solid var(--ui-border2);}
.filter-section-title{
  font-size:11px;font-weight:800;color:var(--burg-600);
  letter-spacing:1px;text-transform:uppercase;
  margin-bottom:6px;direction:rtl;
}
.layer-row{
  display:flex;justify-content:space-between;align-items:center;
  padding:5px 0;border-bottom:1px solid var(--ui-border);
  cursor:pointer;
}
.layer-row:last-child{border-bottom:none}
.layer-row:hover{background:var(--ui-bg3);margin:0 -10px;padding:5px 10px;border-radius:4px;}
.layer-left{display:flex;align-items:center;gap:8px;}

/* Toggle switch */
.tog{
  width:34px;height:19px;border-radius:10px;position:relative;
  transition:background .2s;cursor:pointer;flex-shrink:0;
}
.tog::after{
  content:'';position:absolute;top:2px;
  width:15px;height:15px;border-radius:50%;background:#fff;
  transition:transform .2s;box-shadow:0 1px 4px rgba(0,0,0,.2);
}
.tog.on{background:var(--burg-400)}.tog.on::after{transform:translateX(17px)}
.tog.off{background:#d0c0c8}.tog.off::after{transform:translateX(2px)}
.sec-arrow{transition:transform .2s;display:inline-block;color:var(--text-muted);}

/* ── Topbar ────────────────────────────────────────────────────── */
#topbar{
  position:fixed;top:0;left:0;right:0;height:var(--topbar-h);
  z-index:1000;background:#ffffff;
  border-bottom:1px solid var(--ui-border3);
  box-shadow:0 2px 12px rgba(100,0,30,.08);
  display:flex;flex-direction:column;
}
#topbar-row1{
  display:flex;align-items:center;gap:6px;
  padding:0 10px;height:34px;flex-shrink:0;overflow:hidden;
}
#topbar-row2{
  height:22px;flex-shrink:0;
  border-top:1px solid var(--ui-border2);
  display:flex;align-items:center;padding:0 10px;gap:6px;
  overflow-x:auto;overflow-y:hidden;
}
#topbar-row2::-webkit-scrollbar{display:none}

#topbar-brand{display:flex;flex-direction:column;justify-content:center;flex-shrink:0;}
#topbar-name{
  font-family:'Noto Naskh Arabic',serif;font-size:14px;font-weight:900;
  color:var(--burg-800);direction:rtl;white-space:nowrap;letter-spacing:-.3px;
}
#topbar-tagline{
  font-family:'Noto Naskh Arabic',serif;font-size:10px;font-weight:600;
  color:var(--burg-400);direction:rtl;
}

/* View switcher */
#view-switcher{
  display:flex;gap:3px;padding:3px;
  background:var(--ui-bg2);border-radius:7px;border:1px solid var(--ui-border2);
  flex-shrink:0;
}
.vsw-btn{
  display:flex;align-items:center;gap:4px;padding:3px 10px;
  border-radius:4px;cursor:pointer;font-size:12px;font-weight:700;
  color:var(--text-secondary);transition:all .15s;border:none;background:none;
  white-space:nowrap;
}
.vsw-btn:hover{color:var(--burg-600);background:var(--ui-bg3);}
.vsw-btn.active{background:var(--burg-600);color:#fff;box-shadow:0 2px 8px rgba(180,0,56,.3);}

/* Layer chips (topbar row 2) */
#topbar-layers{display:flex;gap:5px;align-items:center;}
.lchip{
  display:flex;align-items:center;gap:3px;padding:2px 7px;
  border-radius:4px;cursor:pointer;border:1px solid var(--ui-border2);
  background:var(--ui-bg2);transition:all .15s;user-select:none;
}
.lchip:hover{background:var(--ui-bg3);border-color:var(--burg-300);}
.lchip.active{
  background:rgba(180,0,56,.10);border-color:var(--burg-400);
}
.lchip.active .lchip-name{color:var(--burg-600);}
.lchip-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0;}
.lchip-name{font-size:11px;font-weight:700;color:var(--text-secondary);white-space:nowrap;}

/* Live badge */
.live-badge{
  display:inline-flex;align-items:center;gap:3px;
  padding:1px 5px;border-radius:3px;
  background:rgba(220,0,0,.1);border:1px solid rgba(220,0,0,.3);
  font-size:10px;font-weight:700;color:#cc0000;
}
.live-dot{width:5px;height:5px;border-radius:50%;background:#cc0000;
  animation:blink 1.2s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}

/* Topbar right stats */
#topbar-right{
  display:flex;flex-direction:column;align-items:flex-end;
  gap:1px;flex-shrink:0;min-width:100px;
}
#war-day-badge{
  font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;
  color:var(--burg-500);
}
#war-date-str{font-size:11px;color:var(--text-muted);font-family:'JetBrains Mono',monospace;}
#clock{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--text-secondary);}

/* ── War brief card ────────────────────────────────────────────── */
#war-brief-card{
  position:fixed;
  bottom:calc(var(--bottom-h) + 14px);
  right:calc(var(--right-w) + 14px);
  width:420px;max-height:380px;
  background:var(--ui-bg);
  border:1px solid var(--ui-border3);
  border-radius:10px;
  box-shadow:0 8px 32px rgba(100,0,30,.18);
  z-index:500;overflow:hidden;display:none;
  flex-direction:column;
}
#war-brief-card.visible{display:flex;}
#wbc-header{
  display:flex;align-items:center;justify-content:space-between;
  padding:10px 12px 8px;
  background:linear-gradient(135deg,var(--burg-800),var(--burg-600));
}
#wbc-id{font-family:'JetBrains Mono',monospace;font-size:12px;color:rgba(255,255,255,.7);}
#wbc-close{background:none;border:none;cursor:pointer;color:rgba(255,255,255,.7);font-size:18px;line-height:1;}
#wbc-close:hover{color:#fff;}
#wbc-body{padding:12px;overflow-y:auto;flex:1;}
#wbc-type-row{display:flex;align-items:center;gap:6px;margin-bottom:6px;}
#wbc-type-dot{width:8px;height:8px;border-radius:50%;}
#wbc-type-label{font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:.8px;}
#wbc-title{
  font-family:'Noto Naskh Arabic',serif;font-size:15px;font-weight:700;
  color:var(--burg-800);line-height:1.5;margin-bottom:8px;direction:rtl;
}
#wbc-detail{
  font-size:13px;color:var(--text-secondary);line-height:1.7;
  border-right:2px solid var(--burg-200);padding-right:10px;
  direction:rtl;
}
#wbc-meta{
  margin-top:10px;padding-top:8px;border-top:1px solid var(--ui-border);
  display:flex;gap:12px;flex-wrap:wrap;
}
.wbc-meta-item{font-size:12px;color:var(--text-muted);}
.wbc-meta-item strong{color:var(--burg-600);}
#wbc-progress{height:3px;background:var(--ui-border);position:absolute;bottom:0;left:0;right:0;}
#wbc-progress-fill{height:100%;background:var(--burg-400);width:0%;transition:width .3s;}

/* ── Bottom bar — timeline ─────────────────────────────────────── */
#bottombar{
  position:fixed;bottom:0;left:0;right:0;
  height:var(--bottom-h);z-index:1000;
  background:var(--ui-bg);
  border-top:2px solid var(--ui-border3);
  box-shadow:0 -4px 20px rgba(100,0,30,.10);
  display:flex;flex-direction:column;overflow:hidden;
}

/* Timeline top controls row */
#tl-controls{
  display:flex;align-items:center;gap:6px;
  padding:4px 10px;flex-shrink:0;
  border-bottom:1px solid var(--ui-border2);
  min-height:30px;
}
#tl-play-btn{
  width:26px;height:26px;border-radius:50%;
  background:var(--burg-600);color:#fff;border:none;
  cursor:pointer;font-size:13px;
  display:flex;align-items:center;justify-content:center;
  flex-shrink:0;transition:all .15s;
}
#tl-play-btn:hover{background:var(--burg-400);transform:scale(1.05);}
#tl-speed{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--text-muted);cursor:pointer;}
#tl-speed:hover{color:var(--burg-500);}
#tl-info{
  flex:1;display:flex;align-items:center;gap:8px;
  font-size:12px;overflow:hidden;white-space:nowrap;
  min-width:0;direction:rtl;
}
#tl-day-label{font-family:'JetBrains Mono',monospace;font-weight:700;color:var(--burg-500);}
#tl-event-count{color:var(--text-muted);}

/* ── Timeline main area: selector + canvas ─────────────────────── */
#tl-main{
  flex:1;display:flex;min-height:0;
}

/* Category selector — left sidebar of timeline */
#tl-selector{
  width:var(--tl-selector-w);flex-shrink:0;
  display:flex;flex-direction:column;
  border-left:1px solid var(--ui-border2);
  overflow:hidden;
}
.tl-cat{
  flex:1;display:flex;align-items:center;gap:6px;
  padding:0 8px;cursor:pointer;
  border-bottom:1px solid var(--ui-border);
  transition:all .15s;position:relative;
  direction:rtl;
}
.tl-cat:last-child{border-bottom:none;}
.tl-cat:hover{background:var(--ui-bg2);}
.tl-cat.active{
  background:rgba(180,0,56,.08);
  border-right:3px solid var(--burg-400);
}
.tl-cat-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0;}
.tl-cat-label{font-size:11px;font-weight:700;color:var(--text-secondary);white-space:nowrap;}
.tl-cat.active .tl-cat-label{color:var(--burg-600);}
.tl-cat-count{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--text-faint);margin-right:auto;}

/* Timeline canvas area */
#tl-canvas-area{
  flex:1;display:flex;flex-direction:column;min-width:0;position:relative;
}
#tl-canvas{
  flex:1;position:relative;overflow:hidden;cursor:pointer;
}

/* Timeline axis */
#tl-axis{
  height:20px;flex-shrink:0;position:relative;overflow:hidden;
  background:var(--ui-bg2);border-top:1px solid var(--ui-border);
}
.tl-day-line{
  position:absolute;top:0;bottom:0;width:1px;
  background:rgba(180,0,56,.18);pointer-events:none;z-index:1;
}
.tl-day-line.war-start{background:var(--burg-300);width:2px;box-shadow:0 0 5px rgba(220,0,60,.4);}
.tl-day-lbl{
  position:absolute;top:3px;transform:translateX(50%);
  font-family:'JetBrains Mono',monospace;font-size:10px;
  color:var(--text-faint);white-space:nowrap;pointer-events:none;z-index:2;
}
.tl-day-lbl.war-start{color:var(--burg-500);font-weight:700;}

/* Timeline bars */
.tl-bar{
  position:absolute;bottom:0;border-radius:2px 2px 0 0;
  transition:opacity .1s;
}
.tl-bar:hover{opacity:.75!important;}

/* Timeline cursor */
#tl-cursor{
  position:absolute;top:0;bottom:0;width:2px;
  background:var(--burg-500);pointer-events:none;z-index:10;
  box-shadow:0 0 6px rgba(180,0,56,.5);
}
#tl-cursor-handle{
  position:absolute;bottom:-1px;left:50%;
  transform:translateX(-50%);
  width:12px;height:12px;border-radius:50%;
  background:var(--burg-500);border:2px solid #fff;
  box-shadow:0 2px 6px rgba(180,0,56,.4);
  pointer-events:all;cursor:grab;
}
#tl-cursor-handle.dragging{cursor:grabbing;}
#tl-elapsed{
  position:absolute;top:0;bottom:0;left:0;width:0%;
  pointer-events:none;
  background:linear-gradient(to right,rgba(180,0,56,.06),rgba(180,0,56,.02));
}

/* Aircraft icon on timeline */
.tl-aircraft-icon{
  position:absolute;top:50%;transform:translate(-50%,-50%);
  font-size:14px;cursor:pointer;z-index:15;
  transition:transform .1s;
}
.tl-aircraft-icon:hover{transform:translate(-50%,-50%) scale(1.4);}
.tl-aircraft-icon.vip{color:var(--gold);}
.tl-aircraft-icon.private{color:#aaaaaa;}

/* Vessel attack icon on timeline */
.tl-vessel-icon{
  position:absolute;top:50%;transform:translate(-50%,-50%);
  font-size:13px;cursor:pointer;z-index:15;
}
.tl-vessel-icon:hover{transform:translate(-50%,-50%) scale(1.4);}

/* ── Search / quick-find overlay ───────────────────────────────── */
#search-overlay{
  position:fixed;top:var(--topbar-h);left:50%;
  transform:translateX(-50%);
  width:420px;max-height:400px;
  background:var(--ui-bg);border:1px solid var(--ui-border3);
  border-radius:0 0 10px 10px;
  box-shadow:0 8px 32px rgba(100,0,30,.15);
  z-index:800;display:none;flex-direction:column;overflow:hidden;
}
#search-overlay.open{display:flex;}
#search-tabs{display:flex;gap:0;flex-shrink:0;border-bottom:1px solid var(--ui-border2);}
.stab{
  padding:5px 12px;font-size:11px;font-weight:700;
  color:var(--text-muted);border-bottom:2px solid transparent;
  cursor:pointer;transition:all .15s;
}
.stab:hover{color:var(--burg-600);}
.stab.on{color:var(--burg-600);border-bottom-color:var(--burg-400);}
#search-results{flex:1;overflow-y:auto;}
.sr-group-head{
  padding:4px 12px;font-size:10px;font-weight:700;
  color:var(--burg-600);letter-spacing:1.2px;text-transform:uppercase;
  background:var(--ui-bg2);
}
.sr-item{
  display:flex;align-items:center;gap:8px;
  padding:8px 12px;border-bottom:1px solid var(--ui-border);
  cursor:pointer;transition:background .1s;direction:rtl;
}
.sr-item:hover{background:var(--ui-bg3);}
.sr-item.sr-active{background:var(--ui-bg3)!important;outline:2px solid var(--burg-400);outline-offset:-2px;}
.sr-item-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.sr-item-name{font-size:13px;font-weight:600;color:var(--text-primary);}
.sr-item-sub{font-size:11px;color:var(--text-muted);}

/* ── Analytics view ────────────────────────────────────────────── */
#analytics-view{
  position:fixed;
  top:var(--topbar-h);bottom:0;left:0;right:0;
  z-index:50;overflow-y:auto;overflow-x:hidden;
  background:var(--ui-bg2);display:none;
  padding:16px;
}
#analytics-view::-webkit-scrollbar{width:6px}
#analytics-view::-webkit-scrollbar-thumb{background:var(--burg-300);border-radius:3px}

#an-header{
  display:flex;align-items:flex-start;justify-content:space-between;
  padding-bottom:14px;border-bottom:2px solid var(--ui-border3);
  margin-bottom:16px;
}
#an-title{
  font-family:'Noto Naskh Arabic',serif;font-size:20px;font-weight:900;
  color:var(--burg-800);direction:rtl;
}
#an-subtitle{font-size:13px;color:var(--text-muted);direction:rtl;margin-top:2px;}

/* Analytics grid */
#an-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:14px;
}
#an-grid-full{
  display:grid;
  grid-template-columns:1fr;
  gap:14px;
  margin-top:14px;
}

/* Analytics cards */
.an-card{
  background:var(--ui-bg);border:1px solid var(--ui-border2);
  border-radius:10px;padding:14px;overflow:hidden;
}
.an-card-title{
  font-size:12px;font-weight:800;color:var(--burg-700);
  letter-spacing:1.5px;text-transform:uppercase;
  margin-bottom:12px;direction:rtl;
  padding-bottom:8px;border-bottom:1px solid var(--ui-border);
}

/* Chart containers */
.an-chart{
  width:100%;height:180px;position:relative;overflow:hidden;
}
.an-chart-tall{
  width:100%;height:220px;position:relative;overflow:hidden;
}

/* Chart bars (escalation) */
.esc-bar-wrap{
  position:absolute;bottom:20px;top:4px;
  display:flex;flex-direction:column;align-items:center;justify-content:flex-end;
  cursor:pointer;transition:opacity .12s;
}
.esc-bar-wrap:hover{opacity:.8;}
.esc-bar{
  border-radius:2px 2px 0 0;width:100%;transition:height .3s ease;
}
.esc-bar-label{
  position:absolute;bottom:2px;font-size:8px;color:var(--text-muted);
  white-space:nowrap;font-family:'JetBrains Mono',monospace;
}
.esc-bar:hover{opacity:.75;}
.esc-bar-label{
  font-family:'JetBrains Mono',monospace;font-size:9px;
  color:var(--text-faint);text-align:center;margin-top:2px;
}

/* Political line chart */
.pol-svg{width:100%;height:100%;}
.pol-line{fill:none;stroke:var(--burg-400);stroke-width:2;}
.pol-area{fill:url(#polGrad);opacity:.3;}
.pol-zero{stroke:var(--ui-border3);stroke-width:1;stroke-dasharray:4,4;}

/* Risk zone panels */
.risk-zone-row{
  display:flex;align-items:center;gap:10px;
  padding:8px 0;border-bottom:1px solid var(--ui-border);
  direction:rtl;
}
.risk-zone-row:last-child{border-bottom:none;}
.risk-badge{
  padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;
  text-transform:uppercase;letter-spacing:.5px;flex-shrink:0;
}
.risk-badge.critical{background:rgba(220,0,30,.15);color:#cc0020;}
.risk-badge.high{background:rgba(220,100,0,.15);color:#cc6600;}
.risk-badge.medium{background:rgba(180,140,0,.15);color:#997700;}
.risk-badge.low{background:rgba(0,140,0,.15);color:#007000;}
.risk-zone-name{font-size:13px;font-weight:600;flex:1;}
.risk-zone-bar-wrap{width:80px;height:8px;background:var(--ui-bg3);border-radius:4px;overflow:hidden;}
.risk-zone-bar{height:100%;border-radius:4px;transition:width .5s;}

/* Conflict prediction score */
#pred-score-circle{
  width:80px;height:80px;border-radius:50%;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  border:4px solid var(--burg-400);flex-shrink:0;
}
#pred-score-num{font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:700;color:var(--burg-600);}
#pred-score-label{font-size:10px;color:var(--text-muted);text-transform:uppercase;font-weight:700;}
.pred-component-row{
  display:flex;align-items:center;gap:8px;
  padding:5px 0;border-bottom:1px solid var(--ui-border);direction:rtl;
}
.pred-component-row:last-child{border-bottom:none;}
.pred-comp-name{font-size:12px;color:var(--text-secondary);flex:1;}
.pred-comp-bar-wrap{width:100px;height:6px;background:var(--ui-bg3);border-radius:3px;overflow:hidden;}
.pred-comp-bar{height:100%;border-radius:3px;background:var(--burg-400);}
.pred-comp-val{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--text-muted);width:32px;text-align:left;}

/* Analytics tables */
.an-tbl{width:100%;border-collapse:collapse;font-size:13px;}
.an-tbl th{
  text-align:right;padding:7px 10px;
  color:var(--burg-700);font-weight:800;font-size:11px;
  letter-spacing:.8px;text-transform:uppercase;
  border-bottom:2px solid var(--ui-border3);
  background:var(--ui-bg2);
}
.an-tbl td{
  padding:7px 10px;border-bottom:1px solid var(--ui-border);
  color:var(--text-primary);vertical-align:middle;
}
.an-tbl tr:last-child td{border-bottom:none}
.an-tbl tr:hover td{background:#fdf5f7;}

/* VIP flight timeline row */
.vip-day-row{
  display:flex;align-items:center;gap:6px;
  padding:5px 0;border-bottom:1px solid var(--ui-border);direction:rtl;
}
.vip-day-num{
  font-family:'JetBrains Mono',monospace;font-size:11px;
  color:var(--burg-500);width:30px;flex-shrink:0;
}
.vip-day-bar{height:14px;border-radius:2px;background:rgba(184,134,11,.3);position:relative;}
.vip-day-count{font-size:11px;color:var(--text-muted);flex-shrink:0;}

/* Contradiction alerts */
.contradiction-alert{
  padding:8px 10px;border-radius:6px;margin-bottom:6px;
  background:rgba(220,0,30,.06);border:1px solid rgba(220,0,30,.2);
  direction:rtl;
}
.contradiction-alert:last-child{margin-bottom:0;}
.contradiction-day{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--burg-500);font-weight:700;}
.contradiction-text{font-size:12px;color:var(--text-secondary);margin-top:3px;}

/* Report button */
#generate-report-btn{
  display:flex;align-items:center;gap:8px;
  padding:10px 20px;border-radius:8px;
  background:linear-gradient(135deg,var(--burg-700),var(--burg-500));
  color:#fff;border:none;cursor:pointer;font-size:14px;font-weight:700;
  font-family:'Noto Naskh Arabic',serif;
  box-shadow:0 4px 16px rgba(180,0,56,.3);
  transition:all .2s;
}
#generate-report-btn:hover{
  background:linear-gradient(135deg,var(--burg-600),var(--burg-400));
  transform:translateY(-1px);box-shadow:0 6px 20px rgba(180,0,56,.4);
}
#generate-report-btn:active{transform:translateY(0);}
#report-status{font-size:12px;color:var(--text-muted);margin-top:6px;direction:rtl;}

/* ── Briefing feed (right panel) ───────────────────────────────── */
.briefing-msg{
  padding:10px 12px;border-bottom:1px solid var(--ui-border);
  cursor:pointer;transition:background .1s;direction:rtl;
}
.briefing-msg:hover{background:var(--ui-bg3);}
.briefing-msg:last-child{border-bottom:none;}
.briefing-msg-time{
  font-family:'JetBrains Mono',monospace;font-size:11px;
  color:var(--burg-500);margin-bottom:4px;
}
.briefing-msg-text{
  font-size:13px;color:var(--text-primary);line-height:1.6;
  font-family:'Noto Naskh Arabic',serif;
}

/* ── Loader ─────────────────────────────────────────────────────── */
#loader{
  position:fixed;inset:0;z-index:9999;
  background:linear-gradient(135deg,var(--burg-900) 0%,var(--burg-800) 100%);
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;
}
#ld-title{
  font-family:'Noto Naskh Arabic',serif;font-size:22px;font-weight:900;
  color:#fff;direction:rtl;
}
#ld-msg{font-size:14px;color:rgba(255,255,255,.6);direction:rtl;}
#pb-wrap{width:280px;height:6px;background:rgba(255,255,255,.15);border-radius:3px;overflow:hidden;}
#pb{height:100%;border-radius:3px;background:var(--burg-300);width:0%;transition:width .4s;}

/* ── Utility ────────────────────────────────────────────────────── */
.hidden{display:none!important;}
.badge{
  display:inline-flex;align-items:center;
  padding:1px 6px;border-radius:3px;
  font-size:10px;font-weight:700;text-transform:uppercase;
}
.badge-red{background:rgba(220,0,30,.12);color:#cc0020;}
.badge-gold{background:rgba(184,134,11,.12);color:var(--gold-dim);}
.badge-blue{background:rgba(0,85,170,.10);color:var(--blue);}
.badge-green{background:rgba(0,140,0,.10);color:var(--green);}

/* ── Collapsed sections ─────────────────────────────────── */
.filter-section-body.collapsed{display:none;}
.sec-arrow.collapsed{transform:rotate(-90deg);}

/* ── Left panel scrollable content area ─────────────────── */
#left-scroll{flex:1;overflow-y:auto;overflow-x:hidden;min-height:0;}
#left-scroll::-webkit-scrollbar{width:4px}
#left-scroll::-webkit-scrollbar-thumb{background:var(--burg-300);border-radius:2px}
/* ═══ Analytics Page Styles ═══ */
.an-section{margin-bottom:20px;}
.an-section-title{font-size:16px;font-weight:800;color:var(--burg-700);direction:rtl;margin-bottom:12px;padding-bottom:8px;border-bottom:3px solid var(--burg-200);display:flex;align-items:center;gap:8px;}
.an-section-title::before{content:"";display:block;width:5px;height:18px;background:var(--burg-500);border-radius:2px;flex-shrink:0;}
.an-card{background:var(--ui-bg2);border-radius:10px;padding:16px 18px;margin-bottom:12px;border:1px solid var(--ui-border2);}
.an-card-title{font-size:12px;font-weight:700;color:var(--burg-600);direction:rtl;margin-bottom:10px;letter-spacing:.5px;}
.an-grid-2{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.an-grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px;}
.an-stat-card{text-align:center;padding:14px;}
.an-stat-value{font-family:'JetBrains Mono',monospace;font-size:26px;font-weight:800;color:var(--burg-700);}
.an-stat-label{font-size:11px;color:var(--text-muted);margin-top:4px;}
.an-score-badge{display:inline-block;padding:4px 14px;border-radius:6px;font-size:13px;font-weight:700;}
.an-score-badge.low{background:rgba(40,120,64,.12);color:#287840;}
.an-score-badge.medium{background:rgba(200,120,0,.12);color:#c87800;}
.an-score-badge.high{background:rgba(184,0,56,.12);color:#b80038;}
.an-score-badge.critical{background:rgba(255,26,94,.15);color:#ff1a5e;}
.an-heatmap-cell{display:inline-block;width:18px;height:18px;border-radius:2px;margin:1px;font-size:0;}
.an-bar-row{display:flex;align-items:center;gap:8px;padding:4px 0;direction:rtl;border-bottom:1px solid var(--ui-border2);}
.an-bar-label{font-size:11px;color:var(--text-secondary);width:120px;flex-shrink:0;text-align:right;}
.an-bar-wrap{flex:1;background:var(--ui-border2);border-radius:3px;height:14px;overflow:hidden;}
.an-bar-fill{height:100%;border-radius:3px;transition:width .3s;}
.an-bar-value{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:700;color:var(--burg-600);width:40px;text-align:left;}
.an-milestone{padding:8px 10px;border-right:3px solid var(--burg-400);margin-bottom:6px;background:var(--ui-bg3);border-radius:0 6px 6px 0;direction:rtl;}
.an-milestone .day{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--burg-500);font-weight:700;}
.an-milestone .actor{font-size:11px;font-weight:700;color:var(--burg-700);}
.an-milestone .desc{font-size:11px;color:var(--text-secondary);line-height:1.5;margin-top:2px;}
.an-milestone .badge-esc{background:rgba(220,0,30,.1);color:#cc0020;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700;}
.an-milestone .badge-deesc{background:rgba(40,120,64,.1);color:#287840;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700;}
.an-coincidence{padding:10px 12px;background:var(--ui-bg3);border-radius:8px;margin-bottom:8px;direction:rtl;border-right:4px solid #cc6600;}
.an-coincidence .city{font-size:14px;font-weight:800;color:var(--burg-700);}
.an-coincidence .gap{font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px;display:inline-block;margin-bottom:4px;}
.an-coincidence .gap.same{background:rgba(220,0,30,.12);color:#cc0020;}
.an-coincidence .gap.near{background:rgba(200,120,0,.12);color:#cc6600;}
.an-coincidence .actor-line{font-size:12px;color:var(--text-secondary);padding:2px 0;}
@media(max-width:900px){.an-grid-2,.an-grid-3{grid-template-columns:1fr;}}

/* ═══ Responsive fit ═══ */
#war-brief-card{max-width:calc(100vw - var(--panel-w) - var(--right-w) - 28px);}
@media(max-width:1280px){:root{--panel-w:160px;--right-w:240px;}}
@media(max-width:1000px){
  :root{--right-w:0px;}
  #right-panel{display:none;}
}
@media(max-width:700px){
  :root{--panel-w:132px;--tl-selector-w:84px;}
  #topbar-tagline,#topbar-date,#topbar-clock,.live-badge{display:none;}
  .vsw-btn{padding:3px 6px;font-size:11px;}
  #war-brief-card{width:calc(100vw - var(--panel-w) - 24px);right:12px;}
}
/* short screens: let the whole left panel scroll so layer toggles stay reachable */
@media(max-height:780px){
  :root{--bottom-h:136px;}
  #left-panel{overflow-y:auto;}
  #left-scroll{flex:none;overflow:visible;}
}


/* ═══ Print Styles ═══ */
@media print {
  body, html { background:#fff !important; }
  #topbar, #left-panel, #right-panel, #globe, #timeline-bar,
  #loader, #generate-report-btn, #print-analytics-btn,
  #report-loader, #report-status, .lchip, .l-toggle,
  button { display:none !important; }
  #analytics-view { display:block !important; position:static !important; overflow:visible !important; }
  #an-body { max-width:100% !important; padding:0 !important; }
  .an-card { break-inside:avoid; page-break-inside:avoid; border:1px solid #ddd !important; box-shadow:none !important; margin-bottom:10px !important; }
  .an-section { break-inside:avoid; page-break-inside:avoid; }
  .an-section-title { font-size:14px !important; color:#000 !important; border-bottom:2px solid #333 !important; }
  .an-grid-2, .an-grid-3 { display:block !important; }
  .an-grid-2 > *, .an-grid-3 > * { margin-bottom:10px !important; }
  .an-stat-value { color:#333 !important; }
  canvas { max-height:300px !important; }
  #an-header { background:#f5f0f2 !important; color:#000 !important; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
  #an-title { color:#333 !important; font-size:18px !important; }
}
</style>

<!-- ── CDN Scripts ──────────────────────────────────────────── -->
<link href="https://cesium.com/downloads/cesiumjs/releases/1.114/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
<script src="https://cesium.com/downloads/cesiumjs/releases/1.114/Build/Cesium/Cesium.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/satellite.js/4.1.3/satellite.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
"""

print("Part 1 written:", len(_P1), "chars")