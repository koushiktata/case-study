from __future__ import annotations

import os
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(page_title="CycleSight | Demand intelligence", page_icon="🚲", layout="wide", initial_sidebar_state="expanded")
API = os.getenv("BIKE_API_URL", "http://localhost:8000").rstrip("/")
INK, MUTED, MINT, BLUE, GOLD = "#10232c", "#789098", "#70e1c1", "#4ca7ff", "#f5bd68"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {{--ink:#e9f2ee;--muted:#91aaa7;--mint:#8cf0cf;--mint-deep:#4bc9a4;--paper:#09161b;--line:#274047}}
html, body, [class*="css"] {{font-family:'Manrope',sans-serif}}
.stApp {{background:radial-gradient(ellipse at 92% 0%,#123c383d 0,transparent 33rem),radial-gradient(ellipse at 5% 72%,#15354624 0,transparent 28rem),#09161b;color:#e9f2ee}}
header[data-testid="stHeader"] {{background:#09161b99}}
[data-testid="stToolbar"] {{right:1rem}}
[data-testid="stMainBlockContainer"] {{padding-top:1.5rem;padding-bottom:3rem;max-width:1500px}}
[data-testid="stSidebar"] {{background:linear-gradient(165deg,#071217 0%,#0c2025 58%,#09171b 100%);border-right:1px solid #203940}}
[data-testid="stSidebar"] * {{color:#d6e6df}}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{line-height:1.65}}
[data-testid="stSidebar"] hr {{border-color:#29434a;margin:1.3rem 0}}
.brand {{font-size:14px;font-weight:800;letter-spacing:2.5px;color:#8cf0cf;margin:12px 0 3px}}
.brand-sub {{font:10px 'DM Mono',monospace;color:#90aaa5;letter-spacing:1.2px;margin-bottom:24px}}
[data-testid="stSidebar"] [role="radiogroup"] {{gap:5px}}
[data-testid="stSidebar"] [role="radiogroup"] > label {{border:1px solid transparent;border-radius:11px;padding:10px 12px;margin:0;transition:all .18s ease;background:transparent}}
[data-testid="stSidebar"] [role="radiogroup"] > label:hover {{background:#ffffff12;border-color:#ffffff13}}
[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {{background:linear-gradient(90deg,#2b5b57,#214945);border-color:#4d8477;box-shadow:inset 3px 0 #81e4c4}}
[data-testid="stSidebar"] [role="radiogroup"] > label p {{font-size:13px;font-weight:650}}
.eyebrow {{font:10px 'DM Mono',monospace;letter-spacing:2px;color:#337e70;text-transform:uppercase;margin:0 0 8px}}
.hero {{background:linear-gradient(118deg,#10232b 0%,#10433f 56%,#16745d 100%);padding:36px 40px;border:1px solid #8cf0cf35;border-radius:25px;color:#f3fbf8;margin-bottom:24px;position:relative;overflow:hidden;box-shadow:0 22px 55px #020a0d80;isolation:isolate}}
.hero:before {{content:'';position:absolute;z-index:-1;right:-100px;top:-210px;width:480px;height:480px;border:1px solid #a1e7ca52;border-radius:50%;box-shadow:0 0 0 38px #a1e7ca12,0 0 0 80px #a1e7ca0b,0 0 0 125px #a1e7ca07}}
.hero:after {{content:'C';position:absolute;z-index:-1;right:65px;top:-95px;color:#e5fff112;font-size:340px;font-weight:800;line-height:1}}
.hero h1 {{font-size:clamp(34px,3.6vw,50px);line-height:1.04;margin:0 0 12px;color:#f3fbf8;letter-spacing:-2px;max-width:800px}}
.hero p {{color:#c5ddd5;margin:0;max-width:720px;font-size:14px;line-height:1.7}}
.hero .eyebrow {{color:#a0f6d7}}
.metric {{background:linear-gradient(145deg,#142a30 0%,#102229 100%);border:1px solid #2b454a;border-radius:18px;padding:17px 19px;min-height:116px;box-shadow:0 10px 28px #020a0d50;position:relative;overflow:hidden;transition:transform .18s ease,box-shadow .18s ease}}
.metric:before {{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#8cf0cf,#58c3cf,#91a8ff)}}
.metric:hover {{transform:translateY(-3px);border-color:#4a7775;box-shadow:0 16px 32px #020a0d80}}
.metric-label {{font:10px 'DM Mono',monospace;letter-spacing:1.05px;color:#9bb4b1;text-transform:uppercase}}
.metric-value {{font-size:29px;font-weight:800;letter-spacing:-1.2px;color:#f0f8f4;margin-top:8px}}
.metric-note {{font-size:11px;color:#91aaa7;margin-top:2px}}
.section-title {{font-size:19px;font-weight:800;letter-spacing:-.6px;color:#edf6f1;margin:14px 0 4px}}
.section-note {{color:#91aaa7;font-size:12px;margin:0 0 14px}}
.insight {{background:linear-gradient(100deg,#12352f,#142c2a);border:1px solid #27574a;border-left:4px solid #64d9b1;padding:14px 17px;border-radius:0 14px 14px 0;color:#cfebde;font-size:13px;line-height:1.7;box-shadow:0 8px 22px #020a0d55}}
.caution {{background:linear-gradient(100deg,#352a19,#2a251c);border:1px solid #594323;border-left:4px solid {GOLD};padding:14px 17px;border-radius:0 14px 14px 0;color:#f1dfbc;font-size:13px;line-height:1.7}}
.small {{font-size:11px;color:#809195}}
div[data-testid="stMetric"] {{background:#142a30;border:1px solid #2b454a;padding:14px 16px;border-radius:15px;box-shadow:0 8px 24px #020a0d50}}
div[data-testid="stPlotlyChart"] {{background:linear-gradient(145deg,#11252b,#0e2026);border:1px solid #263f46;border-radius:18px;padding:8px 7px 0;box-shadow:0 10px 26px #020a0d45}}
button[data-baseweb="tab"] {{font-weight:700;border-radius:10px 10px 0 0}}
button[data-baseweb="tab"][aria-selected="true"] {{color:#167968}}
div[data-testid="stDataFrame"] {{border:1px solid #263f46;border-radius:14px;overflow:hidden}}
div[data-testid="stExpander"] {{background:#11252b;border:1px solid #263f46;border-radius:14px}}
div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {{border-radius:12px;background:#13272d;border-color:#345058}}
div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button {{border-radius:11px;font-weight:750;min-height:43px}}
div[data-testid="stButton"] button[kind="primary"], div[data-testid="stFormSubmitButton"] button[kind="primary"] {{background:linear-gradient(105deg,#54c9a2,#8cf0cf);color:#08231e;border:0;box-shadow:0 8px 22px #54c9a240}}
div[data-testid="stButton"] button[kind="primary"]:hover, div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {{background:linear-gradient(105deg,#8cf0cf,#b0f7db);color:#08231e;box-shadow:0 10px 26px #54c9a260}}
div[data-testid="stSlider"] [role="slider"] {{background:#157b69}}
div[data-testid="stTabs"] [data-baseweb="tab-list"] {{gap:8px}}
@media(max-width:760px) {{.hero{{padding:26px 23px;border-radius:19px}}.hero:after{{right:5px;font-size:230px}}.metric{{padding:15px;min-height:104px}}.metric-value{{font-size:24px}}}}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def api_get(path: str):
    return requests.get(f"{API}{path}", timeout=40).json()


def api_post(path: str, body: dict):
    response = requests.post(f"{API}{path}", json=body, timeout=60)
    response.raise_for_status()
    return response.json()


def section(title: str, note: str | None = None):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if note: st.markdown(f'<div class="section-note">{note}</div>', unsafe_allow_html=True)


def metric(label: str, value: str, note: str = ""):
    st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)


def chart_layout(fig, height=310):
    fig.update_layout(height=height, margin=dict(l=8,r=8,t=20,b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Manrope",color="#b3c7c2",size=11), legend=dict(orientation="h",y=1.12,x=0,font=dict(color="#c6d9d3")),
                      xaxis=dict(showgrid=False,zeroline=False,color="#a9bfba"), yaxis=dict(showgrid=True,gridcolor="#263f46",zeroline=False,color="#a9bfba"))
    return fig


st.sidebar.markdown('<div class="brand">CYCLESIGHT</div><div class="brand-sub">DEMAND INTELLIGENCE / DC</div>', unsafe_allow_html=True)
page = st.sidebar.radio("WORKSPACE", ["Overview", "Demand lab", "Hypothesis", "Fleet planner", "Ask CycleSight"], label_visibility="visible")
st.sidebar.markdown("---")
st.sidebar.markdown("**MODEL STATUS**")
try:
    health = api_get("/health")
    ready = health.get("model_ready", False)
    st.sidebar.markdown(f"🟢 Model online · {health.get('rows',0):,} hourly records" if ready else "🟠 API online · model needs data")
except Exception:
    ready = False
    st.sidebar.markdown("🔴 API offline · start FastAPI first")
st.sidebar.markdown("---")
st.sidebar.caption("Capital Bikeshare · 2011–2012\nAggregate demand planning prototype")

try:
    data = api_get("/overview")
except Exception as exc:
    st.markdown('<div class="hero"><div class="eyebrow">CYCLESIGHT / CONNECTION REQUIRED</div><h1>Demand, in focus.</h1><p>Start the FastAPI service, then refresh this page to connect live forecasts and operations insights.</p></div>', unsafe_allow_html=True)
    st.error(f"Cannot reach API at {API}: {exc}")
    st.code("uvicorn backend.main:app --reload --port 8000\nstreamlit run frontend/app.py --server.port 8501", language="bash")
    st.stop()

if page == "Overview":
    st.markdown('<div class="hero"><div class="eyebrow">OPERATIONS INTELLIGENCE · WASHINGTON DC</div><h1>Demand, in focus.</h1><p>See when the fleet gets busy, explore the conditions behind demand, and turn an hourly forecast into a transparent planning estimate.</p></div>', unsafe_allow_html=True)
    q=data["quality"]; h=data["headline"]
    cols=st.columns(4)
    with cols[0]: metric("Hourly observations",f"{q['rows']:,}",f"{q['date_start']} — {q['date_end']}")
    with cols[1]: metric("Mean hourly demand",f"{h['mean_hourly']:.0f}","completed rentals / hour")
    with cols[2]: metric("Busiest typical hour",f"{h['peak_hour']:02d}:00",f"{h['peak_hour_mean']:.0f} rentals / hour")
    with cols[3]: metric("Registered riders",f"{h['registered_share_pct']:.1f}%","share of completed rentals")
    st.markdown("<br>",unsafe_allow_html=True)
    left,right=st.columns([1.55,1])
    with left:
        section("The daily rhythm","Average rentals by hour, split by working day")
        hourly=pd.DataFrame(data["hourly"]); hourly["day_type"]=hourly.workingday.map({0:"Non-working day",1:"Working day"})
        fig=px.line(hourly,x="hr",y="mean_rentals",color="day_type",markers=True,color_discrete_map={"Working day":MINT,"Non-working day":BLUE})
        fig.update_traces(line_width=3,marker_size=5); fig.update_xaxes(title="Hour of day",dtick=3); fig.update_yaxes(title="Mean rentals / hour")
        st.plotly_chart(chart_layout(fig),use_container_width=True)
    with right:
        section("Demand by season","Average hourly rentals across the full dataset")
        season=pd.DataFrame(data["season"])
        fig=px.bar(season,x="season_name",y="mean_rentals",color="mean_rentals",color_continuous_scale=["#cae9df","#36b695"])
        fig.update_layout(coloraxis_showscale=False); fig.update_xaxes(title=""); fig.update_yaxes(title="Mean rentals / hour")
        st.plotly_chart(chart_layout(fig),use_container_width=True)
    st.markdown('<div class="insight"><b>What the pattern says.</b> Commute peaks and broad weekend midday demand call for time-aware availability planning. This citywide dataset shows when demand occurs; it does not locate a shortage at a station.</div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    left,right=st.columns([1,1])
    with left:
        section("Data quality","Automated checks run against the loaded hourly file")
        st.dataframe(pd.DataFrame(data["quality_rows"]),hide_index=True,use_container_width=True)
    with right:
        section("Weather shifts demand","Read group sizes alongside the averages")
        wx=pd.DataFrame(data["weather"])
        fig=px.bar(wx,x="weather_name",y="mean_rentals",hover_data={"hours":True},color="mean_rentals",color_continuous_scale=["#dce8ef","#4ca7ff"])
        fig.update_layout(coloraxis_showscale=False); fig.update_xaxes(title="",tickangle=-12); fig.update_yaxes(title="Mean rentals / hour")
        st.plotly_chart(chart_layout(fig,260),use_container_width=True)
        st.caption("Heavy weather has very few historical observations; treat that average cautiously.")
    with st.expander("Model evaluation and split"):
        st.write("The backend fits a Random Forest on the first 80% of dates and evaluates on the latest 20%. The forecast is a historical planning estimate; future performance may differ.")
        st.json(health.get("metrics",{}))

elif page == "Demand lab":
    st.markdown('<div class="hero"><div class="eyebrow">01 / EXPLORE</div><h1>Find the demand signal.</h1><p>Compare hourly profiles, seasons, and weather groups before choosing a planning window.</p></div>', unsafe_allow_html=True)
    t1,t2=st.tabs(["Hourly shape","Conditions"])
    with t1:
        frame=pd.DataFrame(data["hourly"]); frame["Day type"]=frame.workingday.map({0:"Non-working",1:"Working"})
        selected=st.multiselect("Compare day types",frame["Day type"].unique(),default=list(frame["Day type"].unique()))
        frame=frame[frame["Day type"].isin(selected)]
        fig=px.area(frame,x="hr",y="mean_rentals",color="Day type",line_group="Day type",color_discrete_sequence=[MINT,BLUE],markers=True)
        fig.update_xaxes(title="Hour of day",dtick=1); fig.update_yaxes(title="Mean rentals / hour")
        st.plotly_chart(chart_layout(fig,390),use_container_width=True)
        st.caption("The reported hour is local dataset time. Data is aggregated across 2011–2012.")
    with t2:
        left,right=st.columns(2)
        with left:
            section("Seasonality")
            s=pd.DataFrame(data["season"]); f=px.bar(s,x="season_name",y="mean_rentals",color="mean_rentals",color_continuous_scale=["#c7e9df","#31af8e"]); f.update_layout(coloraxis_showscale=False); f.update_yaxes(title="Mean rentals / hour"); f.update_xaxes(title="")
            st.plotly_chart(chart_layout(f,350),use_container_width=True)
        with right:
            section("Weather sensitivity")
            w=pd.DataFrame(data["weather"]); f=px.bar(w,x="weather_name",y="mean_rentals",hover_data=["hours"],color="mean_rentals",color_continuous_scale=["#d8eaf6","#388cd0"]); f.update_layout(coloraxis_showscale=False); f.update_yaxes(title="Mean rentals / hour"); f.update_xaxes(title="",tickangle=-18)
            st.plotly_chart(chart_layout(f,350),use_container_width=True)
            st.caption("Hover to inspect category sample size. Severe weather is sparse.")

elif page == "Hypothesis":
    st.markdown('<div class="hero"><div class="eyebrow">02 / TEST</div><h1>Is rush-hour demand higher?</h1><p>A one-sided Welch test compares the two commute windows with all other hours, using the observed hourly counts.</p></div>', unsafe_allow_html=True)
    result=api_get("/hypothesis")
    st.markdown(f"**H₀** {result['null']}  \n**H₁** {result['alternative']}")
    cols=st.columns(4)
    with cols[0]: metric("Rush hour mean",str(result["rush"]["mean"]),f"n = {result['rush']['n']:,} hours")
    with cols[1]: metric("Other hours mean",str(result["other"]["mean"]),f"n = {result['other']['n']:,} hours")
    with cols[2]: metric("Welch statistic",str(result["statistic_t"]),"one-sided test")
    with cols[3]: metric("Cohen's d",str(result["effect_size_cohens_d"]),"standardized mean difference")
    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown(f'<div class="insight"><b>{result["decision"]} at α = {result["alpha"]:.2f}.</b> {result["p_value_text"]}. This supports time-aware demand planning. It does not establish why riders fail to find a bike or prove that the fleet is too small.</div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    st.markdown(f'<div class="caution"><b>Interpretation note.</b> This implementation uses a large-sample normal approximation for the one-sided p-value. Hourly records have time dependence, so treat the test as descriptive evidence and pair it with operational data. {result["note"]}</div>',unsafe_allow_html=True)
    st.caption(result["test"])

elif page == "Fleet planner":
    st.markdown('<div class="hero"><div class="eyebrow">03 / PLAN</div><h1>Translate demand into capacity.</h1><p>Adjust the conditions and planning assumptions. Every figure is shown with its inputs.</p></div>', unsafe_allow_html=True)
    with st.form("planner"):
        a,b,c=st.columns(3)
        with a:
            season=st.selectbox("Season",["Spring","Summer","Fall","Winter"],index=2); month=st.selectbox("Month",list(range(1,13)),index=8); hour=st.slider("Hour",0,23,17)
            working=st.toggle("Working day",value=True); holiday=st.toggle("Holiday",value=False)
        with b:
            weather=st.selectbox("Weather",["Clear / partly cloudy","Mist / cloudy","Light rain / snow","Heavy rain / snow"]); temp=st.slider("Temperature (°C)",-5,40,20); apparent=st.slider("Feels-like temperature (°C)",-5,50,22)
            humidity=st.slider("Humidity (%)",0,100,55); wind=st.slider("Wind speed (km/h)",0,67,12)
        with c:
            trip=st.slider("Average trip duration (minutes)",5,120,30,5); buffer=st.slider("Demand buffer (%)",0,50,15,5); reserve=st.slider("Maintenance reserve (%)",0,40,10,5)
            st.caption("Trip duration is an assumption; it is not in the source data.")
        submit=st.form_submit_button("Estimate planning fleet",type="primary",use_container_width=True)
    if submit:
        seasons={"Spring":1,"Summer":2,"Fall":3,"Winter":4}; weathers={"Clear / partly cloudy":1,"Mist / cloudy":2,"Light rain / snow":3,"Heavy rain / snow":4}
        conditions={"season":seasons[season],"yr":1,"mnth":month,"hr":hour,"holiday":int(holiday),"weekday":2 if working else 0,"workingday":int(working),"weathersit":weathers[weather],"temp":temp/41,"atemp":apparent/50,"hum":humidity/100,"windspeed":wind/67}
        try:
            result=api_post(f"/fleet?trip_minutes={trip}&buffer_pct={buffer}&reserve_pct={reserve}",conditions)
            x,y,z=st.columns(3)
            with x: metric("Predicted rentals",f"{result['predicted_rentals']:,}","in the selected hour")
            with y: metric("Concurrent bikes",f"{result['estimated_concurrent_bikes']:,}",f"based on {trip} min trips")
            with z: metric("Planning estimate",f"{result['planning_fleet']:,}","with buffer and reserve")
            st.markdown(f'<div class="caution"><b>Use with care.</b> {result["caveat"]}</div>',unsafe_allow_html=True)
            with st.expander("Calculation details"): st.write(result["formula"]); st.json(result["assumptions"])
        except Exception as exc: st.error(f"Forecast unavailable: {exc}")

else:
    st.markdown('<div class="hero"><div class="eyebrow">04 / ASK</div><h1>Ask a demand question.</h1><p>Type a planning question in plain language. CycleSight extracts the scenario, predicts demand, and explains the assumptions.</p></div>', unsafe_allow_html=True)
    left,right=st.columns([1.3,1])
    with left:
        st.markdown("#### Ask your question")
        question=st.text_input("Example",value="What is demand at 8 AM on a working day in fall with clear weather?",label_visibility="collapsed")
        with st.expander("Planning assumptions"):
            trip=st.slider("Average trip duration (minutes)",5,120,30,5,key="ask_trip"); buffer=st.slider("Demand buffer (%)",0,50,15,5,key="ask_buffer"); reserve=st.slider("Maintenance reserve (%)",0,40,10,5,key="ask_reserve")
        if st.button("Explore scenario",type="primary",use_container_width=True):
            try:
                result=api_post("/ask",{"question":question,"trip_minutes":trip,"buffer_pct":buffer,"reserve_pct":reserve})
                st.session_state["answer"]=result
            except Exception as exc: st.error(f"Could not complete the forecast: {exc}")
    with right:
        st.markdown("#### Try asking")
        st.markdown("- What is demand at 8 AM on a working day in summer?\n- How busy is 5 PM in fall when it rains?\n- Estimate 11 AM weekend demand in winter.")
        st.caption("The parser handles common hour, day type, season, weather, and temperature phrases. Review interpreted conditions before using the estimate.")
    if "answer" in st.session_state:
        answer=st.session_state["answer"]
        st.markdown("---")
        st.markdown('<div class="eyebrow">SCENARIO ANSWER</div>',unsafe_allow_html=True)
        st.markdown(f"### {answer['answer']}")
        st.caption(answer["disclaimer"])
        with st.expander("What CycleSight understood"):
            st.json(answer["interpreted_conditions"])
            st.json(answer["prediction"].get("metrics",{}))
