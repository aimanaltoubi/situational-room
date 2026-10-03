# c16_html_body.py
# HTML Part 2: body
# Auto-extracted from Cell 16

# CELL 8 — Part 2 of 4  [FIXED — all missing IDs restored]
# HTML body: loader, topbar, panels, globe,
# war brief card, bottom timeline with side selector,
# analytics view with all Cell 9 panels

_P2 = """
</head>
<body>

<!-- ═══════════════════════ LOADER ════════════════════════════ -->
<div id="loader">
  <div id="ld-title">__SYSTEM_NAME__</div>
  <div id="ld-msg">جاري تحميل المنظومة… · __WORKSPACE_NAME__</div>
  <div id="pb-wrap"><div id="pb"></div></div>
  <div style="font-family:'JetBrains Mono',monospace;font-size:12px;
              color:rgba(255,255,255,.3);margin-top:8px;">
    International Data Analytics System
  </div>
</div>

<!-- ═══════════════════════ TOPBAR ════════════════════════════ -->
<div id="topbar">
  <div id="topbar-row1">

    <div id="topbar-brand">
      <div id="topbar-name">__SYSTEM_NAME__</div>
      <div id="topbar-tagline">__WORKSPACE_NAME__</div>
    </div>

    <div id="view-switcher">
      <a class="vsw-btn" href="./" style="text-decoration:none" title="__WORKSPACE_NAME__">↩ المساحة</a>
      <button class="vsw-btn active" id="vsw-sa"
              onclick="switchView('sa')">🌍 ميداني</button>
      <button class="vsw-btn" id="vsw-analytics"
              onclick="switchView('analytics')">📊 تحليلات</button>
    </div>

    <!-- layer toggles live only in the left panel (طبقات الخريطة) -->
    <div id="topbar-layers" style="flex:1;min-width:0;"></div>

    <!-- Right: live · date · time · war day — all in one row -->
    <div id="topbar-right">
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:nowrap;">
        <button id="dq-btn" onclick="toggleDataQuality()" title="حالة مصادر البيانات">
          <span id="dq-dot"></span>جودة البيانات<span id="dq-count"></span>
        </button>
        <div class="live-badge"><div class="live-dot"></div>مباشر</div>
        <div id="topbar-date" style="font-size:11px;color:var(--text-muted);">—</div>
        <div id="topbar-clock" style="font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--text-secondary);">—</div>
        <div id="war-day-badge" style="font-size:11px;">اليوم —</div>
      </div>
      <span id="clock" style="display:none;"></span><!-- alias for legacy JS -->
    </div>
  </div>

  <!-- Row 2: search -->
  <div id="topbar-row2">
    <div id="search-tabs">
      <div class="stab on"  data-cat="all"  onclick="setSearchTab(this,'all')">الكل</div>
      <div class="stab"     data-cat="war"  onclick="setSearchTab(this,'war')">أحداث</div>
      <div class="stab"     data-cat="sat"  onclick="setSearchTab(this,'sat')">أقمار</div>
      <div class="stab"     data-cat="flt"  onclick="setSearchTab(this,'flt')">رحلات</div>
      <div class="stab"     data-cat="ship" onclick="setSearchTab(this,'ship')">سفن</div>
      <div class="stab"     data-cat="intel"onclick="setSearchTab(this,'intel')">مواقع</div>
    </div>
    <div id="search-wrap" style="flex:1;position:relative;display:flex;align-items:center;">
      <div id="search-input-wrap" style="flex:1;display:flex;align-items:center;gap:6px;padding:0 8px;">
        <span id="search-kbd" style="font-size:10px;color:var(--text-faint);font-family:'JetBrains Mono',monospace;">/</span>
        <input id="search-input" type="text" placeholder="بحث…"
               style="flex:1;border:none;background:transparent;font-size:12px;
                      outline:none;direction:rtl;color:var(--text-primary);"
               oninput="onSearchInput(this.value)"
               onkeydown="onSearchKey(event)"/>
        <span id="search-clear"
              style="display:none;cursor:pointer;color:var(--text-muted);font-size:14px;"
              onclick="clearSearch()">✕</span>
        <span style="color:var(--text-faint);font-size:12px;">🔍</span>
      </div>
      <div id="search-dropdown" style="display:none;position:fixed;
            background:var(--ui-bg);border:1px solid var(--ui-border3);
            border-top:none;max-height:400px;overflow-y:auto;z-index:9999;
            box-shadow:0 8px 24px rgba(100,0,30,.18);border-radius:0 0 8px 8px;">
        <div id="search-results-body"></div>
        <div id="search-empty" style="display:none;padding:12px;text-align:center;
             color:var(--text-muted);font-size:12px;">لا توجد نتائج</div>
      </div>
    </div>
  </div>
</div>

<!-- Globe -->
<div id="globe"></div>

<!-- Data quality modal -->
<div id="dq-modal" onclick="if(event.target===this)toggleDataQuality()">
  <div id="dq-box">
    <div id="dq-head">
      <span>جودة البيانات — __WORKSPACE_NAME__</span>
      <button onclick="toggleDataQuality()" aria-label="إغلاق">✕</button>
    </div>
    <div id="dq-sub"></div>
    <div id="dq-list"></div>
  </div>
</div>

<!-- ═══════════════════ LEFT PANEL ════════════════════════════ -->
<div class="panel" id="left-panel">
  <div class="p-head">
    <span class="p-head-title">لوحة التحكم</span>
  </div>

  <!-- ── Camera Controls (always visible) ── -->
  <div style="padding:8px 10px;border-bottom:1px solid var(--ui-border2);flex-shrink:0;">
    <div class="zoom-row">
      <button class="cb" id="btn-zi" title="تكبير">+</button>
      <button class="cb" id="btn-zo" title="تصغير">−</button>
      <button class="cb rst wide" id="btn-rs">↺ إعادة</button>
    </div>
    <div class="dpad">
      <button class="cb empty"></button>
      <button class="cb" id="btn-up" title="إمالة للأعلى">↑</button>
      <button class="cb empty"></button>
      <button class="cb" id="btn-rl" title="تدوير لليسار">←</button>
      <button class="cb rst" id="btn-obs" title="منظور مائل 45°">◎</button>
      <button class="cb" id="btn-rr" title="تدوير لليمين">→</button>
      <button class="cb empty"></button>
      <button class="cb" id="btn-dn" title="إمالة للأسفل">↓</button>
      <button class="cb empty"></button>
    </div>
    <div class="zoom-row" style="margin-top:2px;">
      <button class="cb wide" id="btn-top">⊙ علوي</button>
      <button class="cb wide" id="btn-side">◑ جانبي</button>
    </div>
  </div>

  <!-- ── Map Style (always visible) ── -->
  <div style="padding:6px 10px;border-bottom:1px solid var(--ui-border2);flex-shrink:0;">
    <div class="mode-grid">
      <button class="mode-btn active" onclick="setMode(this,'satellite')">
        <span class="mode-icon">🛰</span><span class="mode-label">قمر</span>
      </button>
      <button class="mode-btn" onclick="setMode(this,'night')">
        <span class="mode-icon">🌙</span><span class="mode-label">ليل</span>
      </button>
      <button class="mode-btn" onclick="setMode(this,'natural')">
        <span class="mode-icon">🌿</span><span class="mode-label">طبيعي</span>
      </button>
      <button class="mode-btn" onclick="setMode(this,'terrain')">
        <span class="mode-icon">⛰</span><span class="mode-label">تضاريس</span>
      </button>
    </div>
  </div>

  <!-- ── Fly To Presets (always visible) ── -->
  <div style="padding:6px 10px;border-bottom:1px solid var(--ui-border2);flex-shrink:0;">
    <div class="presets">
      <button class="cb wide" onclick="if(viewer)viewer.camera.flyTo({destination:Cesium.Cartesian3.fromDegrees(44,30,4000000),duration:1.5})">المنطقة</button>
      <button class="cb wide" onclick="if(viewer)viewer.camera.flyTo({destination:Cesium.Cartesian3.fromDegrees(56.5,26.5,800000),duration:1.5})">هرمز</button>
      <button class="cb wide" onclick="if(viewer)viewer.camera.flyTo({destination:Cesium.Cartesian3.fromDegrees(51.4,35.7,500000),duration:1.5})">طهران</button>
      <button class="cb wide" onclick="if(viewer)viewer.camera.flyTo({destination:Cesium.Cartesian3.fromDegrees(35.2,31.8,400000),duration:1.5})">القدس</button>
    </div>
  </div>

  <div id="left-scroll">

<!-- ── طبقات الخريطة — collapsible ── -->
  <div class="filter-section">
    <div class="filter-section-title" onclick="_toggleSection('layers-body','arr-layers')">
      <span>طبقات الخريطة</span>
      <span class="sec-arrow" id="arr-layers">▾</span>
    </div>
    <div class="filter-section-body" id="layers-body">
      <div style="padding:0 10px;">
        <div class="layer-row" onclick="toggleWarTimeline()">
          <div class="layer-left">
            <div class="l-dot" style="background:#b80038"></div>
            <div class="l-name">__LBL_EVENTS__</div>
          </div>
          <div class="tog on" id="lt-war"></div>
        </div>
        <div class="layer-row" onclick="toggleJamming()">
          <div class="layer-left">
            <div class="l-dot" style="background:#ff1144"></div>
            <div class="l-name">تشويش GPS</div>
          </div>
          <div class="tog on" id="lt-jam"></div>
        </div>
        <div class="layer-row" onclick="toggleCivFlights()">
          <div class="layer-left">
            <div class="l-dot" style="background:#0088cc"></div>
            <div class="l-name">الرحلات الجوية</div>
          </div>
          <div class="tog off" id="lt-civ"></div>
        </div>
        <div class="layer-row" onclick="toggleMarine()">
          <div class="layer-left">
            <div class="l-dot" style="background:#00b4d8"></div>
            <div class="l-name">السفن البحرية (AIS)</div>
          </div>
          <div class="tog off" id="lt-vessel"></div>
        </div>
        <div class="layer-row" onclick="toggleAttackedVessels()">
          <div class="layer-left">
            <div class="l-dot" style="background:#ff4400"></div>
            <div class="l-name">السفن المهاجمة</div>
          </div>
          <div class="tog off" id="lt-attacked-panel"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- ── الأقمار — collapsible ── -->
  <div class="filter-section">
    <div class="filter-section-title" onclick="_toggleSection('sat-filter','arr-sat')">
      <span>الأقمار</span>
      <span class="sec-arrow" id="arr-sat">▾</span>
    </div>
    <div class="filter-section-body" id="sat-filter">
      <div style="padding:0 10px;">
        <div class="layer-row" onclick="toggleLayer('spy')">
          <div class="layer-left">
            <div class="l-dot" style="background:#ffd700"></div>
            <div>
              <div class="l-name">استطلاع / رصد</div>
              <div class="l-count" id="lc-spy">— قمر</div>
            </div>
          </div>
          <div class="tog on" id="lt-spy"></div>
        </div>
        <div class="layer-row" onclick="toggleLayer('military')">
          <div class="layer-left">
            <div class="l-dot" style="background:#ff6b35"></div>
            <div>
              <div class="l-name">عسكري</div>
              <div class="l-count" id="lc-military">— قمر</div>
            </div>
          </div>
          <div class="tog on" id="lt-military"></div>
        </div>
        <div class="layer-row" onclick="toggleLayer('starlink')">
          <div class="layer-left">
            <div class="l-dot" style="background:#7ec8a0"></div>
            <div>
              <div class="l-name">Starlink</div>
              <div class="l-count" id="lc-starlink">— قمر</div>
            </div>
          </div>
          <div class="tog off" id="lt-starlink"></div>
        </div>
        <div class="layer-row" onclick="toggleLayer('oneweb')">
          <div class="layer-left">
            <div class="l-dot" style="background:#90caf9"></div>
            <div>
              <div class="l-name">OneWeb / LEO</div>
              <div class="l-count" id="lc-oneweb">— قمر</div>
            </div>
          </div>
          <div class="tog off" id="lt-oneweb"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- ── الرحلات — collapsible ── -->
  <div class="filter-section">
    <div class="filter-section-title" onclick="_toggleSection('flt-filter','arr-flt')">
      <span>تصنيف الرحلات</span>
      <span class="sec-arrow" id="arr-flt">▾</span>
    </div>
    <div class="filter-section-body" id="flt-filter">
      <div style="padding:0 10px;">
        <div class="layer-row" onclick="toggleLayer('vip')">
          <div class="layer-left">
            <div class="l-dot" style="background:#b8860b"></div>
            <div>
              <div class="l-name">رؤساء الدول / VIP</div>
              <div class="l-count" id="lc-vip">— رحلة</div>
            </div>
          </div>
          <div class="tog on" id="lt-vip"></div>
        </div>
        <div class="layer-row" onclick="toggleLayer('private')">
          <div class="layer-left">
            <div class="l-dot" style="background:#aaaaaa"></div>
            <div>
              <div class="l-name">طائرات خاصة</div>
              <div class="l-count" id="lc-private">— رحلة</div>
            </div>
          </div>
          <div class="tog on" id="lt-private"></div>
        </div>
      </div>
    </div>
  </div>

  </div><!-- /left-scroll -->

<!-- Hidden IDs for JS compatibility -->
  <div style="display:none;">
    <span id="s-total"></span><span id="s-spy"></span><span id="s-mil"></span>
    <span id="s-stl"></span><span id="s-leo"></span><span id="s-geo"></span>
    <span id="s-rend"></span><span id="s-age"></span>
    <span id="iran-now"></span><span id="iran-approach-count"></span>
    <div id="iran-over-list"></div><div id="iran-approach-list"></div>
    <span id="j-live"></span><span id="j-cells"></span>
    <span id="j-avg"></span><span id="j-days"></span>
    <span id="f-total"></span><span id="f-alerts"></span>
    <div id="flight-fir-list"></div>
    <span id="tlc-war"></span><span id="tlc-sat"></span><span id="tlc-civ"></span>
    <span id="tlc-bases"></span><span id="tlc-jam"></span><span id="tlc-marine"></span>
    <span id="tlc-nuclear"></span><span id="lc-civ"></span><span id="lc-jam"></span>
    <span id="lt-jam-tl"></span>
    <span id="lt-nuclear"></span><span id="lt-usbase"></span>
    <span id="lt-chokepoint"></span><span id="lt-city"></span>
    <span id="arr-intel"></span>
  </div>
</div>

<!-- ═══════════════════ RIGHT PANEL — Telegram Feed ══════════════ -->
<div class="panel" id="right-panel">
  <div class="p-head">
    <span class="p-head-title">نشرة مباشرة · @__TELEGRAM_CHANNEL__</span>
    <div class="live-badge"><div class="live-dot"></div>مباشر</div>
  </div>
  <div style="padding:4px 10px;font-size:10px;color:var(--text-faint);border-bottom:1px solid var(--ui-border);">
    آخر تحديث: <span id="tg-fetch-time">—</span>
  </div>
  <div id="briefing-feed" class="p-body" style="padding:0;gap:0;">
    <div style="padding:12px;text-align:center;color:var(--text-muted);font-size:13px;">
      جاري تحميل النشرة…
    </div>
  </div>
</div>

<!-- ═══════════════════ WAR BRIEF CARD ═══════════════════════════ -->
<div id="war-brief-card">
  <div id="wbc-header">
    <div id="wbc-id" style="font-family:'JetBrains Mono',monospace;font-size:12px;
                             color:rgba(255,255,255,.7);">—</div>
    <div style="display:flex;align-items:center;gap:8px;">
      <div id="wbc-time" style="font-family:'JetBrains Mono',monospace;font-size:11px;
                                  color:rgba(255,255,255,.6);">—</div>
      <button id="wbc-close" onclick="closeWarBrief()">✕</button>
    </div>
  </div>
  <div id="wbc-body">
    <div id="wbc-type-row">
      <div id="wbc-type-dot"></div>
      <div id="wbc-type-label">—</div>
    </div>
    <div id="wbc-title">—</div>
    <div id="wbc-loc" style="font-size:11px;color:var(--text-muted);margin-top:2px;"></div>
    <div id="wbc-detail">—</div>
    <div id="wbc-actors" style="font-size:10px;color:var(--text-faint);margin-top:3px;"></div>
    <div id="wbc-meta"></div>
    <div id="wbc-url" style="margin-top:4px;"></div>
  </div>
  <div id="wbc-progress"><div id="wbc-progress-fill"></div></div>
</div>

<!-- ═══════════════ BOTTOM BAR — TIMELINE ════════════════════════ -->
<div id="bottombar">

  <!-- Top controls row -->
  <div id="tl-controls">
    <button id="tl-play-btn" onclick="tlTogglePlay()">▶</button>
    <span id="tl-speed" onclick="tlCycleSpeed()">×1</span>
    <div id="tl-info">
      <span id="tl-day-label">اليوم —</span>
      <span id="tl-event-count"></span>
    </div>
    <!-- War timeline legacy controls (used by old JS) -->
    <div style="display:flex;align-items:center;gap:6px;margin-right:auto;">
      <span id="war-time-display" style="font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--text-muted);"></span>
      <button id="war-btn-play" onclick="warPlayPause ? warPlayPause() : null"
              style="display:none;">▶</button>
      <span id="bt-event-name" style="font-size:11px;color:var(--text-primary);max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"></span>
      <span id="bt-event-loc" style="font-size:10px;color:var(--text-muted);"></span>
    </div>
    <button id="bt-event-list-btn" onclick="toggleBtEventList()"
            style="font-size:11px;padding:2px 8px;border-radius:4px;border:1px solid var(--ui-border2);background:var(--ui-bg2);cursor:pointer;">
      أحداث ▲
    </button>
    <span id="bt-toggle-label" style="font-size:11px;color:var(--text-muted);"></span>
  </div>

  <!-- War event list (collapsible) -->
  <div id="war-event-list"
       style="display:none;max-height:140px;overflow-y:auto;
              border-top:1px solid var(--ui-border);background:var(--ui-bg2);">
  </div>

  <!-- Jam timeline canvas (legacy) -->
  <div id="tl-jam-canvas" style="display:none;position:relative;height:32px;overflow:hidden;">
    <div id="tl-jam-density" style="position:relative;width:100%;height:100%;"></div>
    <div id="jam-cursor" style="position:absolute;top:0;bottom:0;width:2px;background:#ff1144;pointer-events:none;left:0;"></div>
  </div>
  <div style="display:none;font-size:10px;padding:2px 8px;font-family:'JetBrains Mono',monospace;">
    <span id="jam-time-display"></span>
    <span id="jam-toggle-label" style="margin-right:8px;"></span>
    <span id="jam-intensity-display" style="color:#ff1144;"></span>
  </div>

  <!-- Main timeline area: category selector + canvas -->
  <div id="tl-main">

    <!-- Category selector -->
    <div id="tl-selector">
      <div class="tl-cat active" id="tlcat-war" onclick="tlSetCategory('war')">
        <div class="tl-cat-dot" style="background:#b80038"></div>
        <span class="tl-cat-label">__LBL_TIMELINE__</span>
        <span class="tl-cat-count" id="tlcc-war"></span>
      </div>
      <div class="tl-cat" id="tlcat-flt" onclick="tlSetCategory('flt')">
        <div class="tl-cat-dot" style="background:#b8860b"></div>
        <span class="tl-cat-label">الرحلات</span>
        <span class="tl-cat-count" id="tlcc-flt"></span>
      </div>
      <div class="tl-cat" id="tlcat-sat" onclick="tlSetCategory('sat')">
        <div class="tl-cat-dot" style="background:#ffd700"></div>
        <span class="tl-cat-label">الأقمار</span>
        <span class="tl-cat-count" id="tlcc-sat"></span>
      </div>
      <div class="tl-cat" id="tlcat-jam" onclick="tlSetCategory('jam')">
        <div class="tl-cat-dot" style="background:#ff1144"></div>
        <span class="tl-cat-label">التشويش</span>
        <span class="tl-cat-count" id="tlcc-jam"></span>
      </div>
      <div class="tl-cat" id="tlcat-vessel" onclick="tlSetCategory('vessel')">
        <div class="tl-cat-dot" style="background:#ff4400"></div>
        <span class="tl-cat-label">السفن المهاجمة</span>
        <span class="tl-cat-count" id="tlcc-vessel"></span>
      </div>
      <!-- hidden marine alias kept for JS -->
      <span id="tlcat-marine" style="display:none;"></span>
      <span id="tlcc-marine" style="display:none;"></span>
    </div>

    <!-- Canvas + axis -->
    <div id="tl-canvas-area">
      <div id="tl-canvas"
           onmousedown="tlStartDrag(event)"
           onmousemove="tlDrag(event)"
           onmouseup="tlEndDrag()"
           onclick="tlClick(event)">
        <div id="tl-elapsed"></div>
        <div id="tl-elapsed-overlay" style="position:absolute;top:0;left:0;height:100%;background:rgba(180,0,56,.07);pointer-events:none;"></div>
        <div id="tl-cursor">
          <div id="tl-cursor-handle" onmousedown="tlHandleDrag(event)"></div>
        </div>
        <div id="tl-pin-row" style="position:absolute;top:0;left:0;right:0;height:100%;pointer-events:none;"></div>
        <!-- bars and icons injected by JS -->
      </div>
      <!-- Legacy per-category canvases (hidden, used by old buildTimeline JS) -->
      <div id="tl-canvas-war"  style="display:none;position:absolute;inset:0;"></div>
      <div id="tl-canvas-flt"  style="display:none;position:absolute;inset:0;"></div>
      <div id="tl-canvas-sat"  style="display:none;position:absolute;inset:0;"></div>
      <div id="tl-canvas-jam"  style="display:none;position:absolute;inset:0;"></div>
      <div id="tl-cursor-line" style="display:none;position:absolute;top:0;bottom:0;width:1px;background:#b80038;pointer-events:none;"></div>
      <div id="tl-handle"      style="display:none;"></div>
      <div id="tl-axis-row"    style="display:none;position:absolute;bottom:0;left:0;right:0;height:16px;"></div>
      <div id="tl-axis">
        <!-- day lines and labels injected by JS -->
      </div>
    </div>

  </div><!-- #tl-main -->
</div><!-- #bottombar -->

<!-- ═══════════════ ANALYTICS VIEW ═══════════════════════════════ -->
<div id="analytics-view">
  <div id="an-body" style="max-width:1400px;margin:0 auto;">
    <div id="an-dq-banner" onclick="toggleDataQuality()"></div>

    <!-- Header -->
    <div id="an-header">
      <div>
        <div id="an-title">__ANALYTICS_NAME__</div>
        <div id="an-subtitle" style="font-size:13px;color:var(--text-muted);direction:rtl;margin-top:3px;">
          __SYSTEM_NAME__ · تقييم يوم <span id="an-war-day">—</span>
          · <span id="an-war-phase" style="font-weight:700;color:var(--burg-500);"></span>
          · بُني في <span id="an-ts">__BUILD_TIME__</span>
        </div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:flex-start;gap:8px;">
        <div style="display:flex;gap:8px;">
          <button id="generate-report-btn" onclick="generateReport()">
            ⚡ توليد تقرير التحليلات
          </button>
          <button id="print-analytics-btn" onclick="printAnalytics()" style="background:var(--ui-bg3);color:var(--burg-700);border:1px solid var(--burg-200);padding:8px 16px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;font-family:inherit;">
            طباعة التحليلات
          </button>
        </div>
        <div id="report-status"></div>
        <div id="report-loader" style="display:none;width:260px;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
            <span id="report-status-text" style="font-size:11px;color:var(--burg-500);font-weight:600;flex:1;">جاري التحضير…</span>
            <span id="report-pct-label" style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--burg-600);font-weight:700;">0%</span>
          </div>
          <div style="background:var(--ui-border3);border-radius:4px;height:5px;overflow:hidden;">
            <div id="report-progress-bar" style="height:100%;width:0%;background:linear-gradient(90deg,var(--burg-700),var(--burg-300));border-radius:4px;transition:width .5s;"></div>
          </div>
          <div id="report-steps" style="display:flex;flex-direction:column;gap:3px;margin-top:6px;"></div>
        </div>
      </div>
    </div>

    <!-- ═══ A. WAR STATUS STRIP ═══════════════════════════════════ -->
    <div class="an-card" style="background:linear-gradient(135deg,var(--burg-900),var(--burg-700));color:#fff;border-radius:10px;padding:16px 20px;margin-bottom:14px;">
      <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;text-align:center;">
        <div><div id="stat-events" style="font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:700;">—</div><div style="font-size:10px;opacity:.6;">إجمالي الأحداث</div></div>
        <div><div id="stat-countries" style="font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:700;">—</div><div style="font-size:10px;opacity:.6;">دولة منخرطة</div></div>
        <div><div id="stat-direction" style="font-size:18px;font-weight:700;">—</div><div style="font-size:10px;opacity:.6;">اتجاه التصعيد</div></div>
        <div><div id="stat-pol-trend" style="font-size:18px;font-weight:700;">—</div><div style="font-size:10px;opacity:.6;">المسار السياسي</div></div>
        <div><div id="stat-threat" style="font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:700;">—</div><div style="font-size:10px;opacity:.6;">درجة التهديد</div></div>
      </div>
    </div>

    <!-- ═══ B. ESCALATION ARC ═════════════════════════════════════ -->
    <div class="an-section">
      <div class="an-section-title">__LBL_ESCALATION__</div>

      <!-- B4: Daily strikes by weapon type + actor overlay -->
      <div class="an-card" style="height:340px;position:relative;">
        <canvas id="an-chart-escalation"></canvas>
      </div>

      <!-- B6: Country-over-time heatmap -->
      <div class="an-card">
        <div class="an-card-title">خريطة حرارية — الأحداث حسب الدولة واليوم</div>
        <div id="an-country-heatmap" style="overflow-x:auto;"></div>
      </div>

      <div class="an-grid-2">

        <!-- B9: Country ranking -->
        <div class="an-card">
          <div class="an-card-title">ترتيب الدول حسب عدد الأحداث</div>
          <div id="an-country-ranking"></div>
        </div>
      </div>
    </div>

    <!-- ═══ C. POLITICAL TRAJECTORY ═══════════════════════════════ -->
    <div class="an-section">
      <div class="an-section-title">المسار السياسي — الأحداث التصعيدية والتهدئة يومياً</div>

      <!-- C10: Cumulative pressure line + C11: daily bars -->
      <div class="an-card" style="height:300px;position:relative;">
        <canvas id="an-chart-political"></canvas>
      </div>






    </div>

    <!-- ═══ D. GPS JAMMING ════════════════════════════════════════ -->
    <div class="an-section">
      <div class="an-section-title">التشويش الإلكتروني أثناء الحرب</div>

      <!-- D17: Daily jamming -->
      <div class="an-card" style="height:260px;position:relative;">
        <div class="an-card-title">شدة التشويش اليومية — الشرق الأوسط</div>
        <canvas id="an-chart-jamming"></canvas>
      </div>

      <div class="an-grid-2">
        <!-- D18: Jamming by zone -->
        <div class="an-card">
          <div class="an-card-title">التشويش حسب المنطقة — أيام التشويش النشط</div>
          <div id="an-jam-zones"></div>
        </div>
        <!-- D19: Jamming vs strikes -->
        <div class="an-card" style="height:260px;position:relative;">
          <div class="an-card-title">التشويش مقابل الضربات — هل يرتبطان؟</div>
          <canvas id="an-chart-jam-corr"></canvas>
        </div>
      </div>
    </div>

    <!-- ═══ E0. MILITARY PRESENCE ═════════════════════════════════ -->
    <div class="an-section">
      <div class="an-section-title">التواجد البحري للقوى الكبرى</div>

      <div id="an-country-presence-cards" style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:12px;"></div>

      <!-- Country vessels chart -->
      <div class="an-card" style="height:260px;position:relative;">
        <div class="an-card-title">السفن في المنطقة حسب الدولة والنوع</div>
        <canvas id="an-chart-country-vessels"></canvas>
      </div>

      <!-- Military vessels table -->
      <div class="an-card">
        <div class="an-card-title">السفن العسكرية المرصودة — حسب الدولة</div>
        <div id="an-mil-vessels" style="max-height:300px;overflow-y:auto;"></div>
      </div>
    </div>

    <!-- ═══ E. MARITIME ═══════════════════════════════════════════ -->
    <div class="an-section">
      <div class="an-section-title">الوضع البحري — هرمز والممرات المائية</div>

      <div class="an-grid-3">
        <div class="an-card an-stat-card">
          <div class="an-stat-value" id="mar-total-vessels">—</div>
          <div class="an-stat-label">سفينة مرصودة</div>
        </div>
        <div class="an-card an-stat-card">
          <div class="an-stat-value" id="mar-tanker-disruption" style="color:#cc0020;">—</div>
          <div class="an-stat-label">نسبة تعطل الناقلات</div>
        </div>
        <div class="an-card an-stat-card">
          <div class="an-stat-value" id="mar-attacks">—</div>
          <div class="an-stat-label">هجوم على سفن</div>
        </div>
      </div>

      <div class="an-grid-2">
        <!-- E21: Zone risk table -->
        <div class="an-card">
          <div class="an-card-title">مناطق التهديد البحري</div>
          <div id="an-mar-zones"></div>
        </div>
        <!-- E23: Vessels by flag in Hormuz -->
        <div class="an-card">
          <div class="an-card-title">أعلام السفن في مضيق هرمز</div>
          <div id="an-hormuz-flags"></div>
        </div>
      </div>

      <div class="an-grid-2">
        <!-- E22: Tanker flow -->
        <div class="an-card">
          <div class="an-card-title">تدفق الناقلات — متحركة مقابل متوقفة</div>
          <div id="an-tanker-flow"></div>
        </div>
        <!-- E25+26: Going dark + high interest -->
        <div class="an-card">
          <div class="an-card-title">سفن عالية الاهتمام + أعلام مراقبة</div>
          <div id="an-high-interest"></div>
        </div>
      </div>

      <!-- E27-31: Attacked vessels -->
      <div class="an-card">
        <div class="an-card-title">الهجمات على السفن — تحليل شامل</div>
        <div class="an-grid-3" id="an-av-analysis"></div>
      </div>

      <!-- Ship Casualties (verified damage) -->
      <div class="an-card">
        <div class="an-card-title">أضرار مؤكدة على السفن — بيانات موثقة</div>
        <div class="an-grid-2">
          <div>
            <div id="an-casualties-count" style="font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:800;color:#cc0020;text-align:center;padding:10px 0;">—</div>
            <div style="font-size:10px;color:var(--text-muted);text-align:center;">حادث بحري مؤكد في المنطقة</div>
          </div>
          <div id="an-casualties-list" style="max-height:200px;overflow-y:auto;"></div>
        </div>
      </div>

      <!-- SAT-E Dark Vessels -->
      <div class="an-card">
        <div class="an-card-title">سفن مظلمة — تتبع بالأقمار الاصطناعية (SAT-E)</div>
        <div class="an-grid-2">
          <div>
            <div id="an-sate-count" style="font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:800;color:#cc6600;text-align:center;padding:10px 0;">—</div>
            <div style="font-size:10px;color:var(--text-muted);text-align:center;">سفينة مظلمة تم تتبعها بالقمر</div>
          </div>
          <div id="an-sate-list" style="max-height:200px;overflow-y:auto;"></div>
        </div>
      </div>
    </div>

    <!-- ═══ MARITIME DETAIL CARDS (hidden when the room has no marine feature) ═══ -->
    <div class="an-card-container" id="an-hormuz-flow-section">
      <h3 class="an-card-title">تدفق الناقلات في مضيق هرمز</h3>
      <div id="an-hormuz-flow" style="display:flex;gap:12px;flex-wrap:wrap;"></div>
    </div>
    <div class="an-card-container" id="an-sea-routes-section">
      <h3 class="an-card-title">المسارات البحرية — هرمز مقابل رأس الرجاء الصالح</h3>
      <div id="an-sea-routes" style="padding:10px;"></div>
    </div>
    <div class="an-card-container" id="an-global-mil-section">
      <h3 class="an-card-title">القوات البحرية العالمية — المنطقة مقابل العالم</h3>
      <div id="an-global-mil" style="padding:10px;"></div>
    </div>
    <div class="an-card-container" id="an-vessel-hist-section">
      <h3 class="an-card-title">تاريخ حركة السفن المشبوهة — آخر 30 يوماً</h3>
      <div id="an-vessel-hist" style="padding:10px;"></div>
    </div>
    <div class="an-card-container" id="an-inspections-section">
      <h3 class="an-card-title">التفتيشات والاحتجازات في موانئ المنطقة</h3>
      <div id="an-inspections" style="padding:10px;"></div>
    </div>
    <div class="an-card-container" id="an-companies-section">
      <h3 class="an-card-title">الشركات البحرية المرتبطة بالسفن المرصودة</h3>
      <div id="an-companies" style="padding:10px;"></div>
    </div>

    <!-- ═══ F. FLIGHT INTELLIGENCE ════════════════════════════════ -->
    <div class="an-section">
      <div class="an-section-title">تحليل حركة الطيران — حركة كبار المسؤولين</div>

      <div class="an-grid-3">
        <div class="an-card an-stat-card">
          <div class="an-stat-value" id="flt-total-vip">—</div>
          <div class="an-stat-label">رحلة VIP</div>
        </div>
        <div class="an-card an-stat-card">
          <div class="an-stat-value" id="flt-evac-idx" style="color:#cc6600;">—</div>
          <div class="an-stat-label">مؤشر الإخلاء اليوم الأول</div>
        </div>
        <div class="an-card an-stat-card">
          <div class="an-stat-value" id="flt-coincidences">—</div>
          <div class="an-stat-label">تقاطع دبلوماسي</div>
        </div>
      </div>

      <!-- F33: Diplomatic coincidences -->
      <div class="an-card">
        <div class="an-card-title">تقاطعات دبلوماسية — قادة في نفس المدينة خلال 3 أيام</div>
        <div id="an-coincidences"></div>
      </div>

      <div class="an-grid-2">
        <!-- F34: Shuttle corridors -->
        <div class="an-card">
          <div class="an-card-title">ممرات الدبلوماسية المكوكية — أكثر المسارات نشاطاً</div>
          <div id="an-shuttle-corridors"></div>
        </div>
        <!-- F37: Busiest airports -->
        <div class="an-card">
          <div class="an-card-title">أكثر المطارات نشاطاً أثناء الحرب</div>
          <div id="an-airports"></div>
        </div>
      </div>

      <!-- F35: Destination timeline -->
      <div class="an-card">
        <div class="an-card-title">جدول تنقلات القادة — أين ذهب كل قائد في كل يوم</div>
        <div id="an-dest-timeline" style="overflow-x:auto;"></div>
      </div>

      <!-- F38: VIP entity ranking -->
      <div class="an-card">
        <div class="an-card-title">ترتيب الشخصيات — الأكثر نشاطاً</div>
        <div id="an-vip-ranking"></div>
      </div>
    </div>

    <!-- ═══ G. RECONNAISSANCE SATELLITES ═════════════════════════ -->
    <div class="an-section">
      <div class="an-section-title">أقمار الاستطلاع — النشاط فوق المنطقة أثناء الحرب</div>

      <div class="an-grid-3">
        <div class="an-card an-stat-card">
          <div class="an-stat-value" id="isr-sat-count">—</div>
          <div class="an-stat-label">قمر استطلاع مُتتبَّع</div>
        </div>
        <div class="an-card an-stat-card">
          <div class="an-stat-value" id="isr-active-me">—</div>
          <div class="an-stat-label">قمر مرّ فوق المنطقة</div>
        </div>
        <div class="an-card an-stat-card">
          <div class="an-stat-value" id="isr-avg-daily">—</div>
          <div class="an-stat-label">متوسط التموضعات يومياً</div>
        </div>
      </div>

      <!-- Daily overflights chart -->
      <div class="an-card" style="height:220px;position:relative;">
        <div class="an-card-title">تموضعات أقمار الاستطلاع فوق الشرق الأوسط — يومياً منذ بداية الحرب</div>
        <canvas id="an-chart-isr"></canvas>
      </div>

      <!-- Most active recon satellites -->
      <div class="an-card">
        <div class="an-card-title">أكثر أقمار الاستطلاع نشاطاً — مرتبة حسب عدد أيام التموضع فوق المنطقة</div>
        <div id="an-top-sats" style="max-height:300px;overflow-y:auto;"></div>
      </div>
    </div>

    <!-- ═══ H. THREAT ASSESSMENT ═════════════════════════════════ -->
    <div class="an-section">
      <div class="an-section-title">تقييم مستوى التهديد الحالي — بناءً على آخر 3 أيام من البيانات</div>
      <div class="an-card">
        <div style="display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap;">
          <!-- Gauge -->
          <div style="text-align:center;flex-shrink:0;">
            <svg width="200" height="120" viewBox="0 0 200 120" style="margin:0 auto;">
              <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="var(--ui-border3)" stroke-width="12" stroke-linecap="round"/>
              <path id="an-arc" d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="var(--burg-400)" stroke-width="12" stroke-linecap="round" stroke-dasharray="251.33" stroke-dashoffset="251.33"/>
              <text x="100" y="85" text-anchor="middle" font-size="28" font-weight="800" fill="var(--burg-700)" font-family="'JetBrains Mono',monospace"><tspan id="an-score-pct">—</tspan></text>
              <text x="100" y="105" text-anchor="middle" font-size="11" fill="var(--text-muted)">من 100</text>
            </svg>
            <div id="an-score-badge" class="an-score-badge" style="margin-top:4px;">—</div>
            <div style="font-size:10px;color:var(--text-muted);margin-top:6px;direction:rtl;">يُحسب من آخر 3 أيام للمؤشرات أدناه</div>
          </div>
          <!-- Components -->
          <div style="flex:1;min-width:280px;">
            <div style="font-size:12px;font-weight:700;color:var(--burg-600);margin-bottom:8px;direction:rtl;">ما الذي يرفع مستوى التهديد؟</div>
            <div id="pred-components"></div>
            <div id="pred-interpretation" style="margin-top:12px;font-size:12px;color:var(--text-secondary);direction:rtl;line-height:1.7;padding:8px;background:var(--ui-bg3);border-radius:6px;"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom spacer -->
    <div style="height:80px;"></div>

  </div><!-- #an-body -->
</div><!-- #analytics-view -->



"""

print("Part 2 written:", len(_P2), "chars")