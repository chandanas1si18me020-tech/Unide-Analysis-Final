import streamlit as st
import streamlit.components.v1 as components
import folium
import json
import os
import math
import pandas as pd

st.set_page_config(
    page_title="Unide Store Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global dark theme ──────────────────────────────────────────────
st.markdown("""
<style>
    html, body, [class*="css"], .stApp {
        background-color: #0D1B2A !important;
        color: white !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #091521 !important;
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    .stSelectbox label { color: white !important; }
    .stCheckbox label  { color: white !important; }
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #1A2F45 !important;
        color: white !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0D1B2A !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: rgba(255,255,255,0.55) !important;
        font-size: 14px;
    }
    .stTabs [aria-selected="true"] {
        color: #E67E22 !important;
        border-bottom: 2px solid #E67E22 !important;
    }
    .stDataFrame, .stDataFrame * {
        background-color: #0D1B2A !important;
        color: white !important;
    }
    .stDataFrame thead th {
        background-color: #1A2F45 !important;
        color: white !important;
    }
    .stProgress > div > div {
        background-color: #E67E22 !important;
    }
    div[data-testid="stMetricValue"]  { color: white !important; }
    div[data-testid="stMetricLabel"]  { color: rgba(255,255,255,0.6) !important; }
    .stInfo, .stSuccess, .stWarning   { color: white !important; }
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: white !important;
    }
    hr { border-color: rgba(255,255,255,0.1) !important; }
    .stCaption { color: rgba(255,255,255,0.5) !important; }
    /* Dropdown options */
    [data-baseweb="popover"] * { 
        background-color: #1A2F45 !important; 
        color: white !important; 
    }
</style>
""", unsafe_allow_html=True)

# ── Load data ──────────────────────────────────────────────────────
BASE = "./"

@st.cache_data
def load_data():
    with open(BASE + "unide_app_data.json") as f:
        data = json.load(f)
    geojson = None
    if os.path.exists(BASE + "census_boundaries.geojson"):
        with open(BASE + "census_boundaries.geojson") as f:
            geojson = json.load(f)
    return data, geojson

APP_DATA, GEOJSON = load_data()
STORES     = APP_DATA["stores"]
COMPS      = APP_DATA["competitors"]
SPOILAGE   = APP_DATA["spoilage"]
SHELF_LIFE = APP_DATA["shelf_life"]
LOOKUP     = {s["store_id"]: s for s in STORES}

RC = {0:"#1A7A4A", 1:"#D4AC0D", 2:"#E67E22", 3:"#C0392B"}
RL = {0:"Well Matched", 1:"Low Risk", 2:"Medium Risk", 3:"High Risk"}

SNAMES = {
    s["store_id"]: f"{s['brand']}  —  {s['city']}  ({s['province']})"
    for s in STORES
}
SOPTS = [SNAMES[s["store_id"]] for s in sorted(STORES, key=lambda x: int(x["store_id"]))]
NID   = {v: k for k, v in SNAMES.items()}

def gs(name):
    return LOOKUP.get(NID.get(name))

# ── Card using st.markdown — no iframe white background ────────────
def md_card(label, value, sub=""):
    sub_html = f"<p style='margin:0;font-size:11px;color:rgba(255,255,255,0.45);'>{sub}</p>" if sub else ""
    st.markdown(
        f"""<div style="background:#112236;border:1px solid rgba(255,255,255,0.10);
        border-radius:10px;padding:16px 12px;text-align:center;margin-bottom:10px;">
        <p style="margin:0 0 6px 0;font-size:10px;color:#E67E22;
        text-transform:uppercase;letter-spacing:1.5px;">{label}</p>
        <p style="margin:0;font-size:24px;font-weight:700;color:white;">{value}</p>
        {sub_html}</div>""",
        unsafe_allow_html=True
    )

# ── Haversine ──────────────────────────────────────────────────────
def haversine(lat1, lng1, lat2, lng2):
    R = 6371.0
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lng2-lng1)/2)**2
    return R * 2 * math.asin(math.sqrt(a))

# ── Build map ──────────────────────────────────────────────────────
def make_map(store, show_stores, show_comps, show_census, show_bounds):
    slat, slng = store["lat"], store["lng"]

    m = folium.Map(
        location=[slat, slng],
        zoom_start=13,
        tiles="CartoDB dark_matter"
    )

    # ── Census boundaries ──────────────────────────────────────────
    if show_bounds and GEOJSON:
        bbox  = 0.09
        feats = []
        for f in GEOJSON["features"]:
            coords = []
            def ex(obj):
                if isinstance(obj, list):
                    if obj and isinstance(obj[0], (int, float)):
                        coords.append(obj)
                    else:
                        for i in obj: ex(i)
            ex(f.get("geometry", {}).get("coordinates", []))
            if any(slat-bbox <= p[1] <= slat+bbox
                   and slng-bbox <= p[0] <= slng+bbox for p in coords):
                feats.append(f)
        if feats:
            folium.GeoJson(
                {"type":"FeatureCollection","features":feats},
                style_function=lambda f: {
                    "fillColor"  : f["properties"].get("color","#888"),
                    "color"      : "#FFFFFF",
                    "weight"     : 1.2,
                    "fillOpacity": 0.32,
                },
                highlight_function=lambda f: {
                    "fillColor"  : f["properties"].get("color","#888"),
                    "color"      : "#E67E22",
                    "weight"     : 3.0,
                    "fillOpacity": 0.58,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["Census Section","avg_demand","demand_band"],
                    aliases=["Section:","Avg Demand:","Band:"],
                    style=(
                        "background:rgba(13,27,42,0.96);color:white;"
                        "font-size:12px;padding:8px;border:1px solid #E67E22;"
                    )
                )
            ).add_to(m)

    # ── 2km catchment circle ───────────────────────────────────────
    folium.Circle(
        location=[slat, slng], radius=2000,
        color="#E67E22", weight=2.5,
        fill=True, fill_opacity=0.05,
        dash_array="10 5"
    ).add_to(m)

    # ── All Unide stores ───────────────────────────────────────────
    if show_stores:
        for s in STORES:
            try:
                lat, lng = float(s["lat"]), float(s["lng"])
                if math.isnan(lat) or math.isnan(lng): continue
                sel = s["store_id"] == store["store_id"]
                col = "#E67E22" if sel else RC.get(s["mismatch_score"], "#1B4F72")
                sz  = 28 if sel else 16
                bdr = "4px solid #FFFFFF" if sel else "2.5px solid rgba(255,255,255,0.6)"
                shadow = "0 0 12px rgba(230,126,34,0.8)" if sel else "0 2px 8px rgba(0,0,0,0.7)"
                folium.Marker(
                    location=[lat, lng],
                    icon=folium.DivIcon(
                        html=(
                            f"<div style='width:{sz}px;height:{sz}px;"
                            f"background:{col};border:{bdr};"
                            f"border-radius:4px;transform:rotate(45deg);"
                            f"box-shadow:{shadow};'></div>"
                        ),
                        icon_size=(sz, sz),
                        icon_anchor=(sz//2, sz//2)
                    ),
                    tooltip=folium.Tooltip(
                        f"{s['brand']} — {s['city']} | {s['mismatch_flag']}",
                        sticky=True
                    )
                ).add_to(m)
            except: continue

    # ── Census section points ──────────────────────────────────────
    if show_census:
        secs = store.get("census_sections", [])
        mw   = max((s["weight"] for s in secs), default=1) if secs else 1
        for sec in secs:
            try:
                sl, sln = float(sec["lat"]), float(sec["lng"])
                if math.isnan(sl) or math.isnan(sln): continue
                norm = sec["weight"] / max(mw, 0.001)
                sz   = max(12, int(norm * 22))
                line_w = max(4, norm * 8)
                # Weighted line
                folium.PolyLine(
                    locations=[[sl, sln],[slat, slng]],
                    color="#E67E22",
                    weight=line_w,
                    opacity=0.75,
                    dash_array="5 3"
                ).add_to(m)
                # Census dot
                folium.Marker(
                    location=[sl, sln],
                    icon=folium.DivIcon(
                        html=(
                            f"<div style='width:{sz}px;height:{sz}px;"
                            f"background:#5DADE2;"
                            f"border:3px solid #FFFFFF;"
                            f"border-radius:50%;"
                            f"box-shadow:0 0 8px rgba(93,173,226,0.7);'></div>"
                        ),
                        icon_size=(sz, sz),
                        icon_anchor=(sz//2, sz//2)
                    ),
                    tooltip=folium.Tooltip(
                        f"Section: {sec['section_id']} | "
                        f"{sec['distance_km']}km | weight={sec['weight']:.3f}",
                        sticky=True
                    )
                ).add_to(m)
            except: continue

    # ── Competitors ────────────────────────────────────────────────
    if show_comps:
        bbox  = 0.08
        shown = set()

        # Nearby competitors (larger triangles)
        for comp in store.get("competitors_nearby", []):
            try:
                clat = float(comp["comp_lat"])
                clng = float(comp["comp_lng"])
                if math.isnan(clat) or math.isnan(clng): continue
                key = f"{round(clat,4)}_{round(clng,4)}"
                shown.add(key)
                folium.Marker(
                    location=[clat, clng],
                    icon=folium.DivIcon(
                        html=(
                            "<div style='width:0;height:0;"
                            "border-left:13px solid transparent;"
                            "border-right:13px solid transparent;"
                            "border-bottom:24px solid #F39C12;"
                            "filter:drop-shadow(0 0 6px rgba(243,156,18,0.8));'></div>"
                        ),
                        icon_size=(26, 24),
                        icon_anchor=(13, 12)
                    ),
                    tooltip=folium.Tooltip(
                        f"{comp['comp_name']} | "
                        f"{comp['distance_km']}km | "
                        f"{int(comp['floor_size'])}m²",
                        sticky=True
                    )
                ).add_to(m)
            except: continue

        # Other competitors in view (smaller triangles)
        for comp in COMPS:
            try:
                clat = float(comp["lat"])
                clng = float(comp["lng"])
                if math.isnan(clat) or math.isnan(clng): continue
                if not (slat-bbox <= clat <= slat+bbox
                        and slng-bbox <= clng <= slng+bbox): continue
                key = f"{round(clat,4)}_{round(clng,4)}"
                if key in shown: continue
                folium.Marker(
                    location=[clat, clng],
                    icon=folium.DivIcon(
                        html=(
                            "<div style='width:0;height:0;"
                            "border-left:8px solid transparent;"
                            "border-right:8px solid transparent;"
                            "border-bottom:16px solid #C0392B;'></div>"
                        ),
                        icon_size=(16, 16),
                        icon_anchor=(8, 8)
                    ),
                    tooltip=folium.Tooltip(
                        f"{comp['comp_name']} | {int(comp['floor_size'])}m²",
                        sticky=True
                    )
                ).add_to(m)
            except: continue

    map_html = m._repr_html_()
    return (
        f"<div style='width:100%;height:700px;"
        f"border-radius:10px;overflow:hidden;"
        f"border:1px solid rgba(255,255,255,0.1);'>"
        f"{map_html}</div>"
    )

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        "<h2 style='color:white;margin-bottom:0;'>Unide Store Analysis</h2>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color:rgba(255,255,255,0.5);font-size:12px;'>"
        "Neighbourhood Demand & Spoilage Analysis</p>",
        unsafe_allow_html=True
    )
    st.divider()

    sel   = st.selectbox("SELECT STORE", SOPTS, index=0)
    store = gs(sel)
    st.divider()

    st.markdown("<p style='color:#E67E22;font-size:11px;letter-spacing:1.5px;'>MAP LAYERS</p>",
                unsafe_allow_html=True)
    show_stores = st.checkbox("All Unide Stores",  value=True)
    show_comps  = st.checkbox("Competitors",        value=True)
    show_census = st.checkbox("Census Points",      value=True)
    show_bounds = st.checkbox("Census Boundaries",  value=True)
    st.divider()

    if store:
        mc     = store["mismatch_score"]
        mc_col = RC.get(mc, "#888")
        st.markdown(
            f"<div style='background:{mc_col}22;border-left:4px solid {mc_col};"
            f"padding:10px;border-radius:6px;'>"
            f"<p style='margin:0;font-size:14px;font-weight:600;color:white;'>"
            f"{store['mismatch_flag']}</p>"
            f"<p style='margin:4px 0 0 0;font-size:11px;color:rgba(255,255,255,0.5);'>"
            f"Score {mc}/3</p></div>",
            unsafe_allow_html=True
        )
        st.divider()
        st.markdown(
            f"<p style='color:rgba(255,255,255,0.5);font-size:11px;line-height:1.8;'>"
            f"📍 {store.get('address','')}<br>"
            f"Store ID: {store['store_id']}<br>"
            f"Floor: {int(store['floor_size'])} m²<br>"
            f"Replenishment: {store['replenishment']}x / week<br>"
            f"Best match: {store['best_y']}x / week</p>",
            unsafe_allow_html=True
        )

if not store:
    st.info("Select a store from the sidebar")
    st.stop()

# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════
st.markdown(
    f"<h1 style='color:white;'>{store['brand']}  —  {store['city']}, {store['province']}</h1>",
    unsafe_allow_html=True
)
if store.get("address"):
    st.markdown(
        f"<p style='color:rgba(255,255,255,0.5);font-size:13px;'> {store['address']}  |  Store ID: {store['store_id']}</p>",
        unsafe_allow_html=True
    )

t1, t2, t3, t4, t5, t6 = st.tabs([
    "  Map & Overview",
    "  What-If Analysis",
    "  Competitor Threat",
    "  Category Risk",
    "  Spoilage Overview",
    "  Store Comparison"
])

# ── TAB 1 ──────────────────────────────────────────────────────────
with t1:
    col_map, col_ov = st.columns([5, 2])

    with col_map:
        with st.spinner("Loading map..."):
            components.html(
                make_map(store, show_stores, show_comps, show_census, show_bounds),
                height=720
            )

    with col_ov:
        st.markdown("<h3 style='color:white;'>Store Profile</h3>", unsafe_allow_html=True)
        a, b = st.columns(2)
        with a:
            md_card("Spending Power",  f"{store['spending_power']}", "/ 100")
            md_card("Potential Demand",f"{store['potential_demand']}", "/ 100")
        with b:
            md_card("Market Share",    f"{store['market_share']}%", "local area")
            md_card("Replenishment",   f"{store['replenishment']}x/wk", store['y_group'])

        st.divider()
        mc     = store["mismatch_score"]
        mc_col = RC.get(mc, "#888")
        st.markdown(
            f"<div style='background:{mc_col}18;border:1px solid {mc_col}44;"
            f"border-left:5px solid {mc_col};border-radius:8px;padding:14px;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
            f"<span style='font-size:15px;font-weight:600;color:white;'>{store['mismatch_flag']}</span>"
            f"<span style='background:{mc_col};padding:3px 12px;border-radius:4px;"
            f"font-size:11px;font-weight:700;color:white;'>Score {mc}/3</span></div>"
            f"<p style='margin:8px 0 0;font-size:11px;color:rgba(255,255,255,0.5);'>"
            f"Floor: {store['x_group']} | Demand: {store['pd_band']} | Best Y: {store['best_y']}x/week</p>"
            f"</div>",
            unsafe_allow_html=True
        )

        st.divider()
        st.markdown("<h3 style='color:white;'>Competitors</h3>", unsafe_allow_html=True)
        a, b, c = st.columns(3)
        with a: md_card("Count",       str(store["num_competitors_2km"]), "within 2km")
        with b: md_card("Threat",      store["threat_level"])
        with c: md_card("Combined m²", str(int(store["combined_comp_floor"])))

        st.divider()
        st.markdown(
            "<div style='background:#112236;border-radius:8px;padding:14px;"
            "border:1px solid rgba(255,255,255,0.08);'>"
            "<p style='margin:0 0 8px;font-size:11px;color:#E67E22;"
            "text-transform:uppercase;letter-spacing:1px;'>Methodology</p>"
            "<p style='margin:0;font-size:11px;color:rgba(255,255,255,0.55);line-height:1.9;'>"            "• 25 census variables (1/d² weighting)<br>"
            "• 17 positive + 3 negative + 5 contextual<br>"
            "• Spending Power → z-score → 0-100<br>"
            "• Market Share → census score comparison<br>"
            "• Demand = 60% Spending + 40% Market</p></div>",
            unsafe_allow_html=True
        )

# ── TAB 2 ──────────────────────────────────────────────────────────
with t2:
    st.markdown("<h3 style='color:white;'>What-If Replenishment Analysis</h3>",
                unsafe_allow_html=True)
    st.markdown(
        f"<p style='color:rgba(255,255,255,0.5);'>"
        f"Current: {store['replenishment']}x per week  |  "
        f"Best match: {store['best_y']}x per week</p>",
        unsafe_allow_html=True
    )

    sel_y = st.selectbox(
        "SIMULATE REPLENISHMENT",
        [f"{i}x per week" for i in range(1, 8)],
        index=store["replenishment"] - 1
    )
    y = int(sel_y.split("x")[0])
    w = store["whatif"].get(str(y), {})

    if w:
        if y == store["replenishment"]:
            st.info("This is the current replenishment frequency")
        if y == store["best_y"]:
            st.success("✓ Recommended best-match frequency")

        a, b, c, d = st.columns(4)
        with a: md_card("Coverage",   f"{w.get('coverage',0)}%",   "demand served")
        with b: md_card("Waste Rate", f"{w.get('waste_rate',0)}%", "est. spoilage")
        with c: md_card("Gap Days",   f"{w.get('gap_days',0)}d",   "between deliveries")
        with d: md_card("Risk Score", f"{w.get('score',0)}/3",     RL.get(w.get('score',0),""))

        st.divider()
        c1, c2 = st.columns([2, 1])
        with c1:
            sup = w.get("supply_level", 0)
            dem = w.get("demand_level", 0)
            gap = w.get("gap", 0)
            st.markdown(f"<p style='color:rgba(255,255,255,0.7);'>Supply Level — <b style='color:white;'>{sup}%</b></p>",
                        unsafe_allow_html=True)
            st.progress(min(sup/100, 1.0))
            st.markdown(f"<p style='color:rgba(255,255,255,0.7);'>Demand Level — <b style='color:white;'>{dem}%</b></p>",
                        unsafe_allow_html=True)
            st.progress(min(dem/100, 1.0))
            gap_col = "#1A7A4A" if -5 <= gap <= 20 else "#C0392B"
            st.markdown(
                f"<p style='color:{gap_col};font-weight:600;'>Supply–Demand Gap: {'+' if gap>=0 else ''}{gap}%</p>",
                unsafe_allow_html=True
            )
        with c2:
            flag_col = RC.get(w.get("score",0),"#888")
            st.markdown(
                f"<div style='background:{flag_col}18;border:1px solid {flag_col}44;"
                f"border-left:4px solid {flag_col};border-radius:8px;padding:14px;'>"
                f"<p style='margin:0 0 6px;font-size:14px;font-weight:600;color:white;'>"
                f"{w.get('flag','')}</p>"
                f"<p style='margin:0;font-size:11px;color:rgba(255,255,255,0.6);'>"
                f"{w.get('recommendation','')}</p></div>",
                unsafe_allow_html=True
            )

        ar = w.get("at_risk_categories", [])
        if ar:
            st.divider()
            st.markdown(f"<h4 style='color:white;'>Categories at Risk ({len(ar)})</h4>",
                        unsafe_allow_html=True)
            cols = st.columns(min(len(ar), 4))
            for i, cat in enumerate(ar[:8]):
                sl = SHELF_LIFE.get(cat, 0)
                with cols[i % min(len(ar), 4)]:
                    st.markdown(
                        f"<div style='background:rgba(192,57,43,0.14);"
                        f"border:1px solid rgba(192,57,43,0.45);"
                        f"border-radius:6px;padding:10px;text-align:center;'>"
                        f"<p style='margin:0;font-size:12px;font-weight:600;color:white;'>{cat}</p>"
                        f"<p style='margin:4px 0 0;font-size:10px;color:#E74C3C;'>{sl}d shelf life</p>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
        else:
            st.success("No categories at risk at this replenishment frequency")

# ── TAB 3 ──────────────────────────────────────────────────────────
with t3:
    st.markdown("<h3 style='color:white;'>Competitor Threat — Within 2km</h3>",
                unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    with a: md_card("Threat Level",   store["threat_level"])
    with b: md_card("Competitors",    str(store["num_competitors_2km"]), "within 2km")
    with c: md_card("Combined Floor", f"{int(store['combined_comp_floor'])}m²")
    with d: md_card("Threat Ratio",   f"{store['threat_ratio']}x")

    st.divider()
    nearby = store.get("competitors_nearby", [])
    if nearby:
        st.markdown(f"<h4 style='color:white;'>Nearby Competitors ({len(nearby)} closest)</h4>",
                    unsafe_allow_html=True)
        for comp in nearby:
            cs  = comp.get("competitor_score", 0)
            fa  = comp.get("floor_adjustment", 1.0)
            st.markdown(
                f"<div style='background:rgba(255,255,255,0.04);"
                f"border-radius:8px;padding:14px;margin-bottom:8px;"
                f"border-left:4px solid #C0392B;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                f"<div>"
                f"<p style='margin:0;font-size:15px;font-weight:600;color:white;'>{comp['comp_name']}</p>"
                f"<p style='margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.45);'>"
                f"{comp.get('comp_city','')} — {comp['distance_km']} km away</p>"
                f"</div>"
                f"<div style='text-align:right;'>"
                f"<p style='margin:0;font-size:15px;color:#E67E22;font-weight:600;'>{int(comp['floor_size'])} m²</p>"
                f"<p style='margin:3px 0 0;font-size:11px;color:rgba(255,255,255,0.4);'>"
                f"Score: {cs:.1f} | Adj: {fa:.2f}x</p>"
                f"</div></div></div>",
                unsafe_allow_html=True
            )
    else:
        st.success("No competitors within 2km — store has full local market share")

# ── TAB 4 ──────────────────────────────────────────────────────────
with t4:
    st.markdown("<h3 style='color:white;'>Category Spoilage Risk</h3>",
                unsafe_allow_html=True)
    risks = store.get("category_risk", [])
    if risks:
        risk_counts = {}
        for r in risks:
            risk_counts[r["risk"]] = risk_counts.get(r["risk"], 0) + 1
        a, b, c, d = st.columns(4)
        with a: md_card("High Risk",   str(risk_counts.get("High",0)),        "categories")
        with b: md_card("Medium Risk", str(risk_counts.get("Medium",0)),      "categories")
        with c: md_card("Low Risk",    str(risk_counts.get("Low",0)),         "categories")
        with d: md_card("Opportunity", str(risk_counts.get("Opportunity",0)), "categories")
        st.divider()

        for r in risks:
            risk   = r.get("risk","Low")
            cat    = r.get("category","")
            reason = r.get("reason","")
            sl     = r.get("shelf_life_days",0)
            yoy    = r.get("yoy_change",0)
            rate   = r.get("rate_2025",0)
            col    = {"High":"#C0392B","Medium":"#D4AC0D",
                      "Low":"#1A7A4A","Opportunity":"#1B4F72"}.get(risk,"#888")
            yc     = "#E74C3C" if yoy>0.5 else "#2ECC71" if yoy<-0.5 else "#F1C40F"
            sign   = "+" if yoy >= 0 else ""
            rate_p = (
                f"<p style='margin:8px 0 0;padding-top:6px;"
                f"border-top:1px solid rgba(255,255,255,0.08);"
                f"font-size:11px;color:rgba(255,255,255,0.6);'>"
                f"Rate 2025: <b style='color:white;'>{rate}%</b>  —  "
                f"YoY: <b style='color:{yc};'>{sign}{yoy}%</b></p>"
            ) if rate else ""
            sl_p = (
                f"<p style='margin:3px 0 0;font-size:10px;"
                f"color:rgba(255,255,255,0.3);'>Shelf life: {sl} days</p>"
            ) if sl > 0 else ""
            st.markdown(
                f"<div style='background:rgba(255,255,255,0.04);"
                f"border-radius:8px;padding:13px;margin-bottom:7px;"
                f"border-left:5px solid {col};'>"
                f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                f"<div style='flex:1;'>"
                f"<p style='margin:0;font-size:15px;font-weight:600;color:white;'>{cat}</p>"
                f"<p style='margin:4px 0 0;font-size:12px;color:rgba(255,255,255,0.5);'>{reason}</p>"
                f"{sl_p}</div>"
                f"<span style='background:{col};padding:4px 12px;border-radius:4px;"
                f"font-size:12px;font-weight:700;color:white;margin-left:12px;'>{risk}</span>"
                f"</div>{rate_p}</div>",
                unsafe_allow_html=True
            )
    else:
        st.info("No category risk data available")

# ── TAB 5 ──────────────────────────────────────────────────────────
with t5:
    st.markdown("<h3 style='color:white;'>Warehouse Spoilage Overview — All 18 Categories</h3>",
                unsafe_allow_html=True)
    df  = pd.DataFrame(SPOILAGE).sort_values("rate_2025", ascending=False)
    t24 = df["spoilage_2024"].sum()
    s24 = df["sales_2024"].sum()
    t25 = df["spoilage_2025"].sum()
    s25 = df["sales_2025"].sum()
    r24 = round(t24/s24*100,2) if s24>0 else 0
    r25 = round(t25/s25*100,2) if s25>0 else 0
    yov = round(r25-r24,2)

    a, b, c = st.columns(3)
    with a: md_card("Overall Rate 2024", f"{r24}%")
    with b: md_card("Overall Rate 2025", f"{r25}%")
    with c: md_card("YoY Change", f"{'+' if yov>0 else ''}{yov}%")

    st.divider()
    rows = []
    for _, row in df.iterrows():
        y2    = row.get("yoy_change",0)
        sl    = SHELF_LIFE.get(row["Category"],0)
        trend = " Worse" if y2>0.5 else " Better" if y2<-0.5 else "➡ Stable"
        sign  = "+" if y2>=0 else ""
        rows.append({
            "Category"  : row["Category"],
            "Shelf Life": f"{sl}d",
            "Rate 2024" : f"{round(row.get('rate_2024',0),2)}%",
            "Rate 2025" : f"{round(row.get('rate_2025',0),2)}%",
            "YoY"       : f"{sign}{round(y2,2)}%",
            "Trend"     : trend
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True,
                 hide_index=True, height=540)

# ── TAB 6 ──────────────────────────────────────────────────────────
with t6:
    st.markdown("<h3 style='color:white;'>Store Comparison</h3>",
                unsafe_allow_html=True)
    ca, cb = st.columns(2)
    with ca: na = st.selectbox("STORE A", SOPTS, index=0, key="sa")
    with cb: nb = st.selectbox("STORE B", SOPTS, index=1, key="sb")
    a = gs(na)
    b = gs(nb)

    if a and b and na != nb:
        st.divider()
        mc_a = RC.get(a["mismatch_score"],"#888")
        mc_b = RC.get(b["mismatch_score"],"#888")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f"<div style='background:{mc_a}18;border:1px solid {mc_a}44;"
                f"border-radius:8px;padding:16px;text-align:center;'>"
                f"<p style='margin:0 0 4px;font-size:10px;color:#E67E22;'>STORE A</p>"
                f"<p style='margin:0;font-size:17px;font-weight:700;color:white;'>{a['brand']}</p>"
                f"<p style='margin:3px 0;font-size:13px;color:rgba(255,255,255,0.7);'>"
                f"{a['city']}, {a['province']}</p>"
                f"<p style='margin:0;font-size:11px;color:rgba(255,255,255,0.4);'>"
                f"{a.get('address','')}</p></div>",
                unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                f"<div style='background:{mc_b}18;border:1px solid {mc_b}44;"
                f"border-radius:8px;padding:16px;text-align:center;'>"
                f"<p style='margin:0 0 4px;font-size:10px;color:#E67E22;'>STORE B</p>"
                f"<p style='margin:0;font-size:17px;font-weight:700;color:white;'>{b['brand']}</p>"
                f"<p style='margin:3px 0;font-size:13px;color:rgba(255,255,255,0.7);'>"
                f"{b['city']}, {b['province']}</p>"
                f"<p style='margin:0;font-size:11px;color:rgba(255,255,255,0.4);'>"
                f"{b.get('address','')}</p></div>",
                unsafe_allow_html=True
            )

        st.divider()
        metrics = [
            ("Floor Size (m²)",   a["floor_size"],         b["floor_size"],         True),
            ("Spending Power",    a["spending_power"],      b["spending_power"],      True),
            ("Market Share (%)",  a["market_share"],        b["market_share"],        True),
            ("Potential Demand",  a["potential_demand"],    b["potential_demand"],    True),
            ("Competitors (2km)", a["num_competitors_2km"], b["num_competitors_2km"], False),
            ("Mismatch Score",    a["mismatch_score"],      b["mismatch_score"],      False),
            ("Best Y (x/week)",   a["best_y"],              b["best_y"],              False),
        ]
        h1, h2, h3, h4 = st.columns([2,1,1,1])
        h1.markdown("<b style='color:white;'>Metric</b>",  unsafe_allow_html=True)
        h2.markdown("<b style='color:white;'>Store A</b>", unsafe_allow_html=True)
        h3.markdown("<b style='color:white;'>Store B</b>", unsafe_allow_html=True)
        h4.markdown("<b style='color:white;'>Better</b>",  unsafe_allow_html=True)
        st.divider()
        for label, va, vb, higher in metrics:
            c1, c2, c3, c4 = st.columns([2,1,1,1])
            if isinstance(va, float) and isinstance(vb, float):
                better = "🅰" if (va>vb)==higher else "🅱"
                va_s = f"{va:.1f}"; vb_s = f"{vb:.1f}"
            else:
                better = "🅰" if (va<vb)==(not higher) else "🅱"
                va_s = str(va);    vb_s = str(vb)
            c1.markdown(f"<span style='color:rgba(255,255,255,0.7);'>{label}</span>",
                        unsafe_allow_html=True)
            c2.markdown(f"<span style='color:white;'>{va_s}</span>",
                        unsafe_allow_html=True)
            c3.markdown(f"<span style='color:white;'>{vb_s}</span>",
                        unsafe_allow_html=True)
            c4.markdown(f"<b style='color:#E67E22;'>{better}</b>",
                        unsafe_allow_html=True)

        st.divider()
        better  = "A" if a["potential_demand"] > b["potential_demand"] else "B"
        riskier = ("A" if a["mismatch_score"]  > b["mismatch_score"]  else
                   "B" if b["mismatch_score"]  > a["mismatch_score"]  else "neither")
        st.info(
            f"Store {better} has higher potential demand.  " +
            (f"Store {riskier} carries higher mismatch risk."
             if riskier != "neither" else "Both stores carry equal mismatch risk.")
        )
    elif na == nb:
        st.warning("Please select two different stores to compare")
