from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = Path("/Users/koushiktata/Downloads/Bike_Sharing_Demand_Estimation_Final_Report.docx")
OUT = ROOT / "reports" / "Bike_Sharing_Demand_Estimation_Report_Koushik.docx"
DATA = ROOT / "data" / "hour.csv"
SCREENSHOT_DIR = Path("/Users/koushiktata/Desktop")
BLUE = "365F91"
ACCENT = "4F81BD"
INK = "17212B"
GRAY = "66717B"
PALE = "EAF0F6"
LIGHT = "F4F6F8"
CODE_BG = "F2F3F5"


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_margins(cell, top=65, start=90, bottom=65, end=90):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_run(run, *, name="Times New Roman", size=10.5, bold=False, italic=False, color=INK):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)


def paragraph(doc, text="", *, size=10.5, bold=False, italic=False, color=INK, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
              before=0, after=5, line=1.08, style=None):
    p = doc.add_paragraph(style=style)
    p.alignment = align
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = line
    run = p.add_run(text)
    set_run(run, size=size, bold=bold, italic=italic, color=color)
    return p


def rich_paragraph(doc, runs, *, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=5, size=10.5):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.08
    for text, opts in runs:
        r = p.add_run(text)
        set_run(r, size=opts.get("size", size), bold=opts.get("bold", False), italic=opts.get("italic", False), color=opts.get("color", INK), name=opts.get("name", "Times New Roman"))
    return p


def heading(doc, text, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(8 if level == 1 else 5)
    p.paragraph_format.space_after = Pt(5 if level == 1 else 3)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(text)
    set_run(r, size=14 if level == 1 else 11.5, bold=True, color=BLUE if level == 1 else ACCENT)
    return p


def bullet(doc, text, *, level=0):
    p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    p.paragraph_format.left_indent = Inches(.27 + .22 * level)
    p.paragraph_format.first_line_indent = Inches(-.16)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.05
    set_run(p.add_run(text), size=10.2)
    return p


def numbered(doc, text):
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.left_indent = Inches(.27)
    p.paragraph_format.first_line_indent = Inches(-.16)
    p.paragraph_format.space_after = Pt(3)
    set_run(p.add_run(text), size=10.2)
    return p


def add_table(doc, headers, rows, widths=None, *, font_size=8.8):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.autofit = False
    set_repeat_table_header(t.rows[0])
    for i, label in enumerate(headers):
        c = t.rows[0].cells[i]
        set_cell_shading(c, "DCE6F1")
        set_cell_margins(c)
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if len(headers) <= 4 else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(0)
        set_run(p.add_run(str(label)), size=font_size, bold=True, color=BLUE)
    for row_idx, row in enumerate(rows):
        cells = t.add_row().cells
        for i, value in enumerate(row):
            c = cells[i]
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(c)
            if row_idx % 2 == 1:
                set_cell_shading(c, LIGHT)
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == 0 or len(headers) > 4 else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            set_run(p.add_run(str(value)), size=font_size, color=INK)
    if widths:
        for row in t.rows:
            for idx, width in enumerate(widths):
                row.cells[idx].width = Inches(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return t


def callout(doc, label, body, fill="EAF2F8"):
    t = doc.add_table(rows=1, cols=1)
    t.autofit = False
    cell = t.cell(0, 0)
    set_cell_shading(cell, fill)
    set_cell_margins(cell, 110, 140, 110, 140)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.05
    set_run(p.add_run(label + "  "), size=10, bold=True, color=BLUE)
    set_run(p.add_run(body), size=10, color=INK)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def codebox(doc, code):
    t = doc.add_table(rows=1, cols=1)
    c = t.cell(0, 0)
    set_cell_shading(c, CODE_BG)
    set_cell_margins(c, 100, 130, 100, 130)
    p = c.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(code)
    set_run(r, name="Consolas", size=8.6, color="29323A")
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def caption(doc, text):
    p = doc.add_paragraph(style="Caption")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(5)
    set_run(p.add_run(text), size=9, italic=True, color="5C6470")
    return p


def add_figure(doc, path: Path, caption_text: str, width=6.35):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    p.add_run().add_picture(str(path), width=Inches(width))
    caption(doc, caption_text)


def next_page(doc):
    doc.add_page_break()


def find_screenshot(prefix: str) -> Path:
    matches = sorted(SCREENSHOT_DIR.glob(prefix + "*.png"))
    if not matches:
        raise FileNotFoundError(f"Screenshot not found for {prefix}")
    return matches[0]


def test_stats(df):
    rush = df[df.hr.isin([7, 8, 9, 16, 17, 18, 19])].cnt.to_numpy(float)
    other = df[~df.hr.isin([7, 8, 9, 16, 17, 18, 19])].cnt.to_numpy(float)
    v1, v2 = rush.var(ddof=1), other.var(ddof=1)
    se = math.sqrt(v1/len(rush) + v2/len(other))
    t = (rush.mean()-other.mean())/se
    p = .5*math.erfc(t/math.sqrt(2))
    pooled = math.sqrt(((len(rush)-1)*v1+(len(other)-1)*v2)/(len(rush)+len(other)-2))
    return rush, other, t, p, (rush.mean()-other.mean())/pooled


def write_page_titles(doc, sections):
    for title, page in sections:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.tab_stops.add_tab_stop(Inches(6.0))
        set_run(p.add_run(title), size=11, color=INK)
        set_run(p.add_run("\t" + str(page)), size=11, color=GRAY)


def build():
    if not REFERENCE.exists():
        raise FileNotFoundError(REFERENCE)
    df = pd.read_csv(DATA, parse_dates=["dteday"])
    rush, other, t_stat, p_value, effect = test_stats(df)
    p_text = "< 1 × 10⁻¹⁶" if p_value < 1e-16 else f"= {p_value:.3g}"
    metrics = {
        "r2": 0.845, "mae": 58.3, "rmse": 86.8,
        "train_rows": 13915, "test_rows": 3464,
        "train_through": "2012-08-07", "test_from": "2012-08-08",
    }
    # These values are generated by the current implementation and its actual fitted pipeline.
    from backend.main import model_bundle, prediction
    bundle = model_bundle()
    metrics = bundle["metrics"]
    names = bundle["pipeline"].named_steps["features"].get_feature_names_out()
    importances = bundle["pipeline"].named_steps["model"].feature_importances_
    aggregate = defaultdict(float)
    for name, value in zip(names, importances):
        base = name.split("__", 1)[1]
        if name.startswith("categorical__"):
            base = base.rsplit("_", 1)[0]
        aggregate[base] += float(value)
    top_features = sorted(aggregate.items(), key=lambda item: item[1], reverse=True)
    scenario = {"season":3,"yr":1,"mnth":9,"hr":17,"holiday":0,"weekday":2,"workingday":1,"weathersit":1,
                "temp":20/41,"atemp":22/50,"hum":.55,"windspeed":12/67}
    scenario_prediction = prediction(scenario)["model_estimate"]
    p95 = float(df.cnt.quantile(.95))
    p95_fleet = math.ceil(p95*1.15*.5/.9)
    scenario_fleet = math.ceil(scenario_prediction*1.15*.5/.9)

    # Build on a working copy of the supplied report to retain its section, style system, and page-number field.
    doc = Document(str(REFERENCE))
    doc._body.clear_content()
    section = doc.sections[0]
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    # Retain source title and heading hierarchy while setting readable consistent body styles.
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string(INK)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.08
    doc.styles["Heading 1"].font.name = "Times New Roman"
    doc.styles["Heading 1"].font.size = Pt(14)
    doc.styles["Heading 1"].font.bold = True
    doc.styles["Heading 1"].font.color.rgb = RGBColor.from_string(BLUE)
    doc.styles["Heading 2"].font.name = "Times New Roman"
    doc.styles["Heading 2"].font.size = Pt(11.5)
    doc.styles["Heading 2"].font.bold = True
    doc.styles["Heading 2"].font.color.rgb = RGBColor.from_string(ACCENT)
    doc.core_properties.title = "Bike Sharing Demand Estimation"
    doc.core_properties.subject = "Demand modelling, interface design, and fleet planning case study"
    doc.core_properties.author = "TATA VENKATA SATYA SAI KOUSHIK"

    # PAGE 1 — cover, closely following the centered reference title page.
    for _ in range(5):
        paragraph(doc, "", align=WD_ALIGN_PARAGRAPH.CENTER, after=0)
    paragraph(doc, "Bike-Sharing Demand Estimation", size=25, bold=True, color="111111", align=WD_ALIGN_PARAGRAPH.CENTER, after=10)
    paragraph(doc, "Hourly demand modelling, hypothesis testing and fleet-sizing decision support", size=14, color="222222", align=WD_ALIGN_PARAGRAPH.CENTER, after=28)
    paragraph(doc, "Data Science Project Report", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=15)
    paragraph(doc, "Name: TATA VENKATA SATYA SAI KOUSHIK", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=7)
    paragraph(doc, "Roll No: B231284EE", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=12)
    paragraph(doc, "Capital Bikeshare hourly and daily data · Washington, D.C. · 2011–2012", size=10.5, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, after=0)
    next_page(doc)

    # PAGE 2 — executive summary and contents.
    heading(doc, "Executive Summary", 1)
    paragraph(doc, "This case study builds an operations-facing demand estimation prototype for a bike-sharing system. Using 17,379 hourly observations from 2011–2012, the project checks data quality, describes when completed rentals rise, tests whether rush-hour mean demand exceeds demand in other hours, trains a chronological Random Forest forecast, and turns a prediction into a transparent capacity illustration.")
    paragraph(doc, f"The hourly file is complete and internally consistent. Average observed demand is {df.cnt.mean():.1f} rentals per hour. The implemented Random Forest reaches R² = {metrics['r2']:.3f}, MAE = {metrics['mae']:.1f}, and RMSE = {metrics['rmse']:.1f} on the final chronological holdout. Rush hours average {rush.mean():.1f} rentals per hour compared with {other.mean():.1f} in other hours (Welch t = {t_stat:.2f}, p {p_text}, Cohen's d = {effect:.3f}).")
    callout(doc, "Decision boundary", "The data measures completed citywide rentals. It has no station inventories, denied-rental attempts, trip duration, or rebalancing logs. It supports timing and demand planning, but it cannot determine whether the operator should buy bikes or redistribute existing bikes.")
    heading(doc, "Contents", 2)
    write_page_titles(doc, [("1. Problem statement and objectives",3),("2. Dataset and data dictionary",4),("3. Data quality and preparation",5),("4. Exploratory demand analysis",6),("5. Dashboard overview",7),("6. Demand lab",8),("7. Hypothesis testing",9),("8. Hypothesis dashboard",10),("9. Forecasting task and features",11),("10. Preprocessing algorithms",12),("11. Random Forest algorithm",13),("12. Model evaluation and results",14),("13. Fleet sizing simulator",15),("14. Fleet planner interface",16),("15. System architecture and API",17),("16. Natural-language explorer",18),("17. Business recommendation and limitations",19),("18. Conclusion, setup, and sources",20)])
    next_page(doc)

    # PAGE 3 — case problem and objectives.
    heading(doc, "1. Problem Statement", 1)
    heading(doc, "1.1 The operating question", 2)
    paragraph(doc, "The supplied candidate brief presents a familiar bike-share complaint: riders report difficulty finding bikes while some bicycles appear unused elsewhere. The management question is whether to purchase more bicycles. This is a capacity and distribution decision, and the same rider experience can result from two different conditions: too few bicycles in total, or enough bicycles in the system but in the wrong places at the wrong times.")
    heading(doc, "1.2 Project objectives", 2)
    for item in ["Audit the supplied hourly and daily data and create readable features for exploration.","Describe demand variation by hour, day type, season, year, and weather.","Test one explicit hypothesis about peak demand with a stated statistical method.","Train a model to estimate hourly completed rentals using conditions available before the hour.","Provide an operations prototype that accepts both structured controls and natural-language scenarios.","Convert a demand estimate into an assumption-labelled system-wide capacity illustration."]:
        bullet(doc, item)
    heading(doc, "1.3 Evidence boundary", 2)
    paragraph(doc, "The files contain aggregate completed rentals. They do not identify pickup or return stations, station capacity, available bicycles at a timestamp, failed rental attempts, trip lengths, or staff redistribution activity. Consequently, “demand is high at this hour” is observable, while “this station ran out of bikes” is not. The report treats the purchase question as unresolved until additional operational evidence is collected.")
    callout(doc, "Scope", "The model predicts historical completed hourly rentals. It does not estimate latent demand from riders who could not rent.")
    next_page(doc)

    # PAGE 4 — dataset and schema.
    heading(doc, "2. Dataset and Data Dictionary", 1)
    paragraph(doc, "The source is the Capital Bikeshare dataset described in the supplied Readme.txt and attributed to Hadi Fanaee-T and Joao Gama. It covers Washington, D.C. from 1 January 2011 through 31 December 2012. The download contains an hourly file (17,379 records) and a daily file (731 records). Hourly records are used to train and evaluate the model; both files are retained in the project data folder.")
    paragraph(doc, "Table 1 summarizes the hourly schema. The target is `cnt`; weather variables are normalized values in the source and are rescaled for user-facing controls.", size=10.2)
    schema = [
        ("instant","Record index"),("dteday","Date (2011–2012)"),("season","1 spring, 2 summer, 3 fall, 4 winter"),("yr","0 = 2011, 1 = 2012"),("mnth","Month, 1–12"),("hr","Hour of day, 0–23"),("holiday","Holiday flag, 0/1"),("weekday","Day of week, 0–6"),("workingday","Neither weekend nor holiday, 0/1"),("weathersit","Clear, mist/cloud, light precipitation, heavy precipitation"),("temp","Normalized temperature; multiply by 41 °C"),("atemp","Normalized feels-like temperature; multiply by 50 °C"),("hum","Normalized humidity; multiply by 100%"),("windspeed","Normalized wind; multiply by 67 km/h"),("casual","Completed casual-user rentals"),("registered","Completed registered-user rentals"),("cnt","Total completed rentals; prediction target")]
    add_table(doc,["Field","Meaning / encoding"],schema,widths=[1.6,4.9],font_size=8.5)
    caption(doc,"Table 1. Hourly source fields and their interpretation, adapted from the supplied dataset Readme.")
    next_page(doc)

    # PAGE 5 — quality audit and derived features.
    heading(doc, "3. Data Cleaning and Feature Preparation", 1)
    heading(doc, "3.1 Data-quality checks", 2)
    checks = [("Hourly records",f"{len(df):,}","Expected two-year hourly file"),("Date range",f"{df.dteday.min().date()} to {df.dteday.max().date()}","Full supplied period"),("Missing cells",str(int(df.isna().sum().sum())),"No row or field imputation required for the supplied data"),("Duplicate rows",str(int(df.duplicated().sum())),"No duplicate removal required"),("Negative `cnt`",str(int((df.cnt<0).sum())),"All demand counts are non-negative"),("`cnt` identity failures",str(int((df.cnt!=df.casual+df.registered).sum())),"Total equals casual + registered"),("Weather category 4",str(int((df.weathersit==4).sum()))+" hours","Sparse; descriptive average is unstable")]
    add_table(doc,["Check","Observed result","Interpretation"],checks,widths=[1.55,1.45,3.5],font_size=8.5)
    heading(doc, "3.2 Preparation and derived features", 2)
    paragraph(doc, "Dates are parsed into datetime values and category codes are mapped to readable season and weather labels for presentation. The API derives temperature in Celsius and a rush-hour indicator for the hypothesis test. The model retains the original normalized weather fields because those are the values used when it is trained.")
    for item in ["No rows were dropped: the supplied hourly file passes the key integrity checks.","Categorical features are season, year, month, hour, holiday, weekday, workingday, and weathersit.","Continuous weather inputs are temp, atemp, hum, and windspeed.","`casual`, `registered`, and `cnt` are excluded from model inputs to avoid post-outcome leakage."]:
        bullet(doc,item)
    callout(doc,"Rare-category caution","Only three hourly records are labeled as the most severe weather category. The model can encode this category, but its specific learned pattern is weakly supported.","FCEFD9")
    next_page(doc)

    # PAGE 6 — demand EDA.
    heading(doc, "4. Exploratory Demand Analysis", 1)
    paragraph(doc, "Hourly demand is highly uneven. The overall mean is {:.1f}, the median is {:.0f}, the 95th percentile is {:.1f}, and the maximum is {} rentals in an hour. The maximum occurred on {} at {:02d}:00. A single daily average hides large differences between low-demand nights and high-demand commuting periods.".format(df.cnt.mean(),df.cnt.median(),df.cnt.quantile(.95),int(df.cnt.max()),df.loc[df.cnt.idxmax(),"dteday"].date(),int(df.loc[df.cnt.idxmax(),"hr"])))
    wd = df.groupby(["workingday","hr"]).cnt.mean()
    hourly_rows = [(f"{h:02d}:00",f"{wd.loc[1,h]:.1f}",f"{wd.loc[0,h]:.1f}",note) for h,note in [(8,"working-day AM peak"),(13,"non-working midday peak"),(17,"working-day PM peak"),(18,"second PM peak"),(3,"overnight low")]]
    add_table(doc,["Hour","Working day mean","Non-working mean","Pattern"],hourly_rows,widths=[.8,1.35,1.45,2.9],font_size=8.7)
    season_names={1:"Spring",2:"Summer",3:"Fall",4:"Winter"}
    weather_names={1:"Clear / partly cloudy",2:"Mist / cloudy",3:"Light rain / snow",4:"Heavy rain / snow"}
    wx=df.groupby("weathersit").cnt.agg(["size","mean"])
    eda_rows=[("Season",season_names[k],f"{df.loc[df.season==k,'cnt'].mean():.1f} rentals/hour","") for k in []]
    eda_rows += [("Season",season_names[k],f"{df.loc[df.season==k,'cnt'].mean():.1f}","") for k in [1,2,3,4]]
    eda_rows += [("Weather",weather_names[k],f"{wx.loc[k,'mean']:.1f}",f"n = {int(wx.loc[k,'size']):,}") for k in [1,2,3,4]]
    add_table(doc,["Group","Category","Mean hourly rentals","Sample size / note"],eda_rows,widths=[.85,2.0,1.5,2.15],font_size=8.4)
    paragraph(doc,"Fall is the busiest season on average (236.0 rentals/hour) and spring the quietest (111.1). The 2012 hourly mean (234.7) is higher than 2011 (143.8), a rise of about 63%; historical growth cautions against assuming a stationary demand level.",size=10)
    next_page(doc)

    # PAGE 7 — dashboard screenshot.
    heading(doc, "5. Prototype Walkthrough: Overview", 1)
    paragraph(doc,"The Overview page is designed for a quick operational scan: record count and date range, average hourly demand, busiest typical hour, registered-rider share, a working-day versus non-working-day demand curve, a seasonal comparison, and quality-check results.")
    add_figure(doc,find_screenshot("Screenshot 2026-11-10 at 11.59.38"),"Figure 1. CycleSight Overview page showing headline data indicators, hourly demand curves, and the seasonal view.")
    paragraph(doc,"The screenshot reports 17,379 observations, approximately 190 rentals per hour, a typical peak at 17:00, and 81.2% of completed trips from registered riders. The hourly profile shows two sharper weekday peaks and a broader non-working-day midday curve. The page pairs those patterns with a reminder that aggregate rentals do not locate station shortages.")
    next_page(doc)

    # PAGE 8 — demand lab screenshot.
    heading(doc, "6. Demand Lab", 1)
    paragraph(doc,"The Demand Lab expands the exploratory view. The Hourly Shape tab lets a user compare day types and see the full 24-hour curve. The Conditions tab presents averages by season and weather, with category counts available on hover. These are descriptive summaries of the historical sample rather than forecasts.")
    add_figure(doc,find_screenshot("Screenshot 2026-11-10 at 11.59.51"),"Figure 2. Demand Lab, with day-type comparison and hourly curve for all 24 hours.")
    heading(doc,"How to read the figure",2)
    paragraph(doc,"Working-day demand rises sharply at 08:00 and again at 17:00–18:00. Non-working-day activity builds more gradually and peaks around midday. The two profiles argue for shift planning by hour and day type. They do not reveal whether the number of bikes in the system was sufficient at any particular station.")
    callout(doc,"Weather sample size","The displayed severe-weather average is based on three observations; it should not be used as a stable operational estimate.","FCEFD9")
    next_page(doc)

    # PAGE 9 — hypothesis method.
    heading(doc, "7. Hypothesis Testing", 1)
    heading(doc,"7.1 Testable question",2)
    paragraph(doc,"The implemented test asks whether mean hourly completed rentals are higher during rush hours—07:00–09:00 and 16:00–19:00—than during all remaining hours. The rush group contains 5,097 observations and the comparison group contains 12,282.")
    add_table(doc,["Component","Specification"],[("Null hypothesis (H₀)","Mean hourly rentals during rush hours are no higher than during other hours."),("Alternative (H₁)","Mean hourly rentals are higher during rush hours."),("Test statistic","Welch two-sample t statistic for unequal variances."),("Tail","One-sided, because the alternative is directional."),("Significance level","α = 0.05."),("P-value calculation","Large-sample normal approximation applied to the t statistic."),("Effect size","Cohen’s d using pooled sample standard deviation.")],widths=[1.75,4.75],font_size=9)
    heading(doc,"7.2 Equations",2)
    codebox(doc,"SE = sqrt(s_rush² / n_rush + s_other² / n_other)\nt = (mean_rush − mean_other) / SE\np ≈ 1 − Φ(t)   [normal approximation]\nd = (mean_rush − mean_other) / pooled_standard_deviation")
    paragraph(doc,"Welch’s standard error accommodates unequal group variances. The code reports a one-sided normal-tail approximation instead of a Student-t tail with Welch–Satterthwaite degrees of freedom. The approximation is suitable for the very large sample sizes here, but it should be stated transparently. Hourly records are serially related, so the test is descriptive rather than causal evidence.")
    next_page(doc)

    # PAGE 10 — hypothesis results screenshot.
    heading(doc,"8. Hypothesis Results and Interface",1)
    add_table(doc,["Measure","Rush hours","Other hours"],[("Sample size",f"{len(rush):,}",f"{len(other):,}"),("Mean rentals/hour",f"{rush.mean():.1f}",f"{other.mean():.1f}"),("Median rentals/hour",f"{np.median(rush):.0f}",f"{np.median(other):.0f}")],widths=[2.1,2.2,2.2],font_size=9)
    paragraph(doc,f"The observed difference is substantial: rush-hour mean demand is about {rush.mean()/other.mean():.2f} times the mean for other hours. Welch t = {t_stat:.2f}; the large-sample one-sided p-value is {p_text}; Cohen’s d = {effect:.3f}. At α = .05, the null hypothesis is rejected. This supports targeted planning around the commute periods, not a conclusion about fleet sufficiency.")
    add_figure(doc,find_screenshot("Screenshot 2026-11-10 at 12.00.01"),"Figure 3. Hypothesis page displaying the rush-hour comparison, test statistic, effect size, and interpretation caveat.",width=6.3)
    paragraph(doc,"The interface presents H₀ and H₁, group means and counts, the test statistic, effect size, and the approximation caveat in the same view. This makes the conclusion reviewable rather than leaving the manager with a p-value alone.",size=9.8)
    next_page(doc)

    # PAGE 11 — forecasting formulation.
    heading(doc,"9. Forecasting Task and Feature Design",1)
    paragraph(doc,"The supervised learning task predicts `cnt`, total completed rentals for one hour, from contextual fields known for that hour. Each historical row is one training example. The output is a non-negative rental-count estimate; the API rounds a model estimate to a whole number for display.")
    heading(doc,"9.1 Predictor set",2)
    add_table(doc,["Feature family","Fields","Reason to include"],[("Calendar","season, yr, mnth, hr, holiday, weekday, workingday","Captures recurring schedules, annual change, and commute timing."),("Weather category","weathersit","Represents clear, mist, rain/snow conditions."),("Weather measurements","temp, atemp, hum, windspeed","Represents perceived and measured environment."),("Target","cnt","Total rentals to estimate; never used as an input."),("Post-outcome counts","casual, registered","Excluded because the counts are only known after rentals occur.")],widths=[1.35,2.6,2.55],font_size=8.6)
    heading(doc,"9.2 Chronological holdout",2)
    paragraph(doc,"Unique dates are sorted and the 80th percentile date is used as the boundary. Records through 7 August 2012 form training (13,915 rows); observations beginning 8 August through 31 December 2012 form the test set (3,464 rows). This preserves temporal order and better resembles forecasting a later period than a random row split.")
    callout(doc,"Leakage control","The model uses no same-hour rental subcounts, target-derived rolling averages, or future observations. Categorical labels and numeric weather fields are fitted only within the training pipeline.")
    next_page(doc)

    # PAGE 12 — data transformation algorithms.
    heading(doc,"10. Preprocessing Algorithms",1)
    paragraph(doc,"Preprocessing is implemented in a Scikit-learn ColumnTransformer and Pipeline. Fitting the entire pipeline on the training partition keeps category dictionaries and imputation values from being learned from the holdout period.")
    heading(doc,"10.1 One-hot encoding",2)
    paragraph(doc,"The eight discrete predictors are converted into indicator columns. For example, hour 17 becomes a binary column for that hour, rather than implying a numeric distance between hour codes. `handle_unknown='ignore'` lets inference continue if an unseen category appears, although the supported ranges are validated by the API.")
    heading(doc,"10.2 Median imputation",2)
    paragraph(doc,"`SimpleImputer(strategy='median')` replaces missing numeric weather values with the corresponding median calculated on the training split. The supplied file contains no missing values, so no substitution is expected in this run; the step makes the pipeline robust to future rows with absent measurements.")
    heading(doc,"10.3 Standard scaling",2)
    paragraph(doc,"`StandardScaler` centers and scales the four continuous weather fields using training data. A tree model does not require scale normalization for split ordering, but scaling is retained as an explicit, reproducible preprocessing stage and supports consistent pipeline inputs.")
    codebox(doc,"categorical = OneHotEncoder(handle_unknown='ignore')\nnumeric = Pipeline([\n  ('impute', SimpleImputer(strategy='median')),\n  ('scale', StandardScaler()),\n])\nfeatures = ColumnTransformer([\n  ('categorical', categorical, CATEGORICAL),\n  ('numeric', numeric, NUMERIC),\n])")
    paragraph(doc,"The pipeline packages all transformations with the estimator so training and prediction apply the same steps in the same order. No manually calculated dummy columns are maintained in the Streamlit layer.")
    next_page(doc)

    # PAGE 13 — Random Forest algorithm.
    heading(doc,"11. Random Forest Regression",1)
    paragraph(doc,"A Random Forest is a bagging ensemble of decision trees. Each tree is fitted to a bootstrap sample of the training rows and considers a random subset of predictors at candidate splits. A regression tree partitions feature space into terminal regions and predicts the average target value in each region. The forest averages the tree predictions:")
    codebox(doc,"ŷ(x) = (1 / B) × Σ[b=1..B] T_b(x)\n\nfor b in 1..B:\n    sample rows with replacement\n    grow a regression tree using random feature subsets\n    store tree T_b\nreturn average(T_1(x), ..., T_B(x))")
    heading(doc,"11.1 Configuration used",2)
    add_table(doc,["Parameter","Configured value","Role"],[("n_estimators","180","Number of trees whose predictions are averaged."),("min_samples_leaf","3","Minimum training rows represented by a terminal leaf; reduces highly local fits."),("max_features","0.9","Fraction of transformed features considered at candidate splits."),("random_state","42","Makes the fit repeatable in the same software environment."),("n_jobs","-1","Uses available CPU workers for tree fitting and prediction.")],widths=[1.55,1.2,3.75],font_size=8.7)
    paragraph(doc,"The estimator is trained through a Pipeline: transform the training features, fit the forest on `cnt`, then predict on the untouched later dates. Negative estimates are clipped to zero before metrics and before user-facing display. The forest can represent nonlinear interactions between time, calendar, and weather without specifying a linear equation for each effect.")
    next_page(doc)

    # PAGE 14 — metrics and results.
    heading(doc,"12. Model Evaluation and Results",1)
    paragraph(doc,"The holdout metrics below were generated from the fitted application pipeline using the project’s hourly CSV. Training covers 1 January 2011–7 August 2012; the test period runs 8 August–31 December 2012. This is a single chronological split, not repeated cross-validation.")
    add_table(doc,["Metric","Holdout result","Meaning"],[("R²",f"{metrics['r2']:.3f}","Fraction of holdout target variance explained relative to the test-set mean baseline."),("MAE",f"{metrics['mae']:.1f} rentals/hour","Average absolute prediction error; treats all errors linearly."),("RMSE",f"{metrics['rmse']:.1f} rentals/hour","Square-root mean squared error; gives larger misses more weight."),("Training rows",f"{metrics['train_rows']:,}",f"Through {metrics['train_through']}"),("Test rows",f"{metrics['test_rows']:,}",f"From {metrics['test_from']} through 2012-12-31")],widths=[1.35,1.7,3.45],font_size=8.7)
    codebox(doc,"R²   = 1 − Σ(yᵢ − ŷᵢ)² / Σ(yᵢ − mean(y))²\nMAE  = (1/n) × Σ |yᵢ − ŷᵢ|\nRMSE = sqrt((1/n) × Σ (yᵢ − ŷᵢ)²)")
    heading(doc,"12.1 Aggregate feature importance",2)
    paragraph(doc,"Random Forest impurity-based importances sum contributions across the one-hot columns belonging to each source feature. They describe how much a feature helped split the training trees; they are not causal effects.",size=10)
    importance_rows=[(name, f"{value*100:.1f}%") for name,value in top_features[:8]]
    add_table(doc,["Source feature","Aggregated forest importance"],importance_rows,widths=[3.2,3.3],font_size=8.8)
    callout(doc,"Interpretation","The model performs reasonably on this later 2012 holdout, but an hourly MAE of about 58 rentals is material near peaks. Monitor errors by hour and high-demand quantile before relying on it for a live service level.")
    next_page(doc)

    # PAGE 15 — fleet formula.
    heading(doc,"13. Fleet Size Estimation Simulator",1)
    paragraph(doc,"Hourly rentals are not the same as concurrent bicycles in use. The prototype therefore estimates a rough concurrency proxy using an explicit trip duration and operating reserves. It displays its assumptions next to the result so managers can change them and inspect sensitivity.")
    codebox(doc,"buffered_hourly_demand = predicted_rentals × (1 + buffer_pct / 100)\nconcurrent_bikes = buffered_hourly_demand × trip_minutes / 60\nplanning_fleet = ceil(concurrent_bikes / (1 - reserve_pct / 100))")
    add_table(doc,["Assumption","Default","Effect"],[("Average trip duration","30 minutes","Longer trips increase the number of rentals active at once."),("Demand buffer","15%","Adds a cushion above the point forecast."),("Maintenance reserve","10%","Reduces the share of the fleet counted as available."),("Rounding","Ceiling","Returns a whole-bike planning quantity.")],widths=[2.0,1.35,3.15],font_size=8.8)
    heading(doc,"13.1 Worked illustrations",2)
    add_table(doc,["Demand input","Assumptions","Planning result"],[(f"Historical P95: {p95:.1f} rentals/hour","30-min trip; 15% buffer; 10% reserve",f"{p95_fleet} bikes, approximate system-wide concurrency"),(f"Model scenario: {scenario_prediction:.1f} rentals/hour at 17:00 fall working-day","Same defaults",f"{scenario_fleet} bikes, scenario-specific planning estimate")],widths=[2.1,2.25,2.15],font_size=8.5)
    paragraph(doc,"The second row is a model scenario with September, 2012, a working day, clear weather, 20 °C, 22 °C feels-like temperature, 55% humidity, and 12 km/h wind. Its estimate depends on those settings and on the 30-minute duration assumption; it is not an inventory target for each station.")
    callout(doc,"Critical limitation","The data does not record trip durations, station inventory, denied rentals, docking capacity, or redistribution routes. These formulas cannot prove the total fleet requirement or locate a shortage.","FCEFD9")
    next_page(doc)

    # PAGE 16 — fleet UI.
    heading(doc,"14. Fleet Planner Interface",1)
    paragraph(doc,"The Fleet Planner exposes the forecast inputs—season, month, hour, working-day and holiday flags, weather, temperature, feels-like temperature, humidity, and wind. A second group exposes trip duration, demand buffer, and maintenance reserve. The operator submits one scenario and receives predicted rentals, concurrent bikes, and the buffered planning figure.")
    add_figure(doc,find_screenshot("Screenshot 2026-11-10 at 12.00.09"),"Figure 4. Fleet Planner page showing the condition controls and the three planning assumptions.",width=6.3)
    paragraph(doc,"The screenshot was captured before the user submitted a scenario, so no forecast result is visible in the image. The live planner returns those figures after submission and opens the calculation formula and assumption values for review. Changing trip duration has a direct proportional effect on concurrent bikes; changing the reserve affects the denominator and therefore the final planning fleet.")
    next_page(doc)

    # PAGE 17 — architecture and endpoints.
    heading(doc,"15. System Architecture and API",1)
    paragraph(doc,"CycleSight is split into a Streamlit presentation layer and a FastAPI analytical service. The frontend submits HTTP JSON requests; the API reads the CSV, computes summary statistics, validates scenario inputs, and calls the cached model for predictions. The browser receives JSON values that the UI renders as cards, tables, and interactive charts.")
    add_table(doc,["Layer","Technology","Responsibility"],[("Presentation","Streamlit + Plotly","Dashboard navigation, filters, charts, scenario forms, and answer display."),("Service","FastAPI + Pydantic","HTTP routes, request validation, model invocation, and JSON responses."),("Data","hour.csv / day.csv","Historical rentals and calendar/weather context."),("Model pipeline","Scikit-learn","One-hot and numeric preprocessing plus Random Forest regression."),("Runtime","Uvicorn","Serves FastAPI on local port 8000; Streamlit defaults to port 8501.")],widths=[1.25,1.55,3.95],font_size=8.6)
    add_table(doc,["Method + route","Response purpose"],[("GET /health","Model status and chronological holdout metrics."),("GET /overview","Data checks, headline KPIs, hourly/season/weather series, and daily totals."),("GET /hypothesis","Rush-hour versus other-hour Welch test and group summaries."),("POST /predict","Rental estimate for explicitly supplied hourly features."),("POST /fleet","Prediction plus assumption-driven fleet arithmetic."),("POST /ask","Scenario extraction, forecast, and explanatory answer.")],widths=[2.2,4.3],font_size=8.6)
    codebox(doc,"Streamlit UI (:8501)  ──HTTP JSON──>  FastAPI (:8000)\n                                      ├── CSV loader and checks\n                                      ├── cached preprocessing + Random Forest\n                                      └── hypothesis, parser, and fleet services")
    paragraph(doc,"The codebase has separate `frontend/` and `backend/` packages. BIKE_API_URL configures the frontend service origin; BIKE_DATA_DIR points the API to another data directory. The detailed component diagram and API notes are in `docs/architecture.md`.")
    next_page(doc)

    # PAGE 18 — natural-language parser and screenshot.
    heading(doc,"16. Natural-Language Demand Explorer",1)
    paragraph(doc,"Ask CycleSight accepts short questions such as “What is demand at 8 AM on a working day in summer?” The backend applies a deterministic rule-based parser, not a general-purpose language model. It detects common hour expressions with regular expressions, maps season and weather words to source categories, infers working versus non-working day, and fills unspecified conditions from defaults.")
    codebox(doc,"extract scenario from question:\n  season     ← spring / summer / fall / winter keyword\n  hour       ← regex hour + AM/PM, or 24-hour notation\n  day_type   ← working day / weekday / weekend keyword\n  weather    ← clear / mist / rain / snow / storm keyword\n  temperature ← numeric value followed by °C, if present\n  other fields ← stated default assumptions\npredict scenario → calculate fleet proxy → format answer")
    add_figure(doc,find_screenshot("Screenshot 2026-11-10 at 12.00.17"),"Figure 5. Ask CycleSight interface, including a sample demand question and suggested prompts.",width=6.25)
    paragraph(doc,"The interface repeats the parsed scenario and displays a disclaimer that the answer is aggregate. The parser is intentionally bounded: unsupported wording, ambiguous times, or unusual phrases may be interpreted using defaults. Users should inspect “What CycleSight understood” before acting on an estimate.",size=9.8)
    next_page(doc)

    # PAGE 19 — decision and limits.
    heading(doc,"17. Business Recommendation and Limitations",1)
    heading(doc,"17.1 Evidence-backed recommendation",2)
    paragraph(doc,"Use the time-of-day signal to plan availability checks and pilot redistribution around the weekday commute peaks. Do not approve or reject a purchase from these aggregate rentals alone. A system-level fleet might be sufficient while station-level supply is misplaced, or the total fleet may be too small at certain periods; this dataset cannot distinguish the cases.")
    heading(doc,"17.2 Highest-value data to collect",2)
    add_table(doc,["Additional evidence","Decision it enables"],[("Station inventory and dock capacity by timestamp","Locate empty stations and full docks during reported shortages."),("Attempted and denied rental events","Measure unmet demand that completed-rental counts omit."),("Trip start/end stations and durations","Estimate station-to-station flows and concurrent bike use."),("Rebalancing vehicle movements and work time","Measure how much supply can be shifted and at what operating cost."),("Controlled redistribution pilot","Test whether targeted moves reduce customer complaints before capital spend.")],widths=[2.9,3.6],font_size=8.6)
    heading(doc,"17.3 Limitations",2)
    for item in ["Historical coverage ends in 2012; current demand may have changed.","The training target is successful rentals, so unmet demand is unobserved.","The holdout period is one contiguous segment; repeated seasonal backtests would strengthen validation.","Random Forest impurity importance is predictive, not causal.","The hypothesis test treats serially related hourly records approximately as independent.","Fleet arithmetic assumes trip duration and simple concurrency; it ignores spatial dynamics and driver constraints.","The natural-language parser is rules-based and may use defaults when a query is ambiguous."]:
        bullet(doc,item)
    next_page(doc)

    # PAGE 20 — conclusion, run instructions and citations.
    heading(doc,"18. Conclusion",1)
    paragraph(doc,"This project turns the supplied bike-sharing logs into a connected Streamlit and FastAPI prototype. The hourly data passes core integrity checks. A clear commuting pattern appears in the exploratory analysis and the implemented directional test. A Random Forest trained chronologically achieves R² 0.845 with MAE 58.3 and RMSE 86.8 on the held-out portion of this historical dataset. The application lets an operator explore conditions, estimate demand, and inspect a simple fleet-planning calculation.")
    paragraph(doc,"The evidence supports planning by time window. It does not establish whether more bikes should be purchased. Station inventory, trip duration, and denied-rental information are needed to turn the prototype’s citywide planning proxy into a specific operational or capital decision.")
    heading(doc,"Run the local prototype",2)
    codebox(doc,"Terminal 1:  .venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000\nTerminal 2:  .venv/bin/streamlit run frontend/app.py --server.port 8501\nOpen:        http://localhost:8501")
    heading(doc,"References",2)
    for ref in ["Candidate Case Study, supplied PDF. Case question and requested project objectives.","Bike Sharing Dataset Readme.txt, supplied with the hourly and daily CSV files. Dataset fields, time coverage, and source citation.","Fanaee-T, Hadi, and Joao Gama. “Event labeling combining ensemble detectors and background knowledge.” Progress in Artificial Intelligence (2013). DOI: 10.1007/s13748-013-0040-3.","Bike_Sharing_Demand_Estimation_Final_Report.docx, supplied reference. Used for the nine-section organization, table and figure-caption conventions, and prototype walkthrough structure; reference-only results were not attributed to this implementation."]:
        numbered(doc,ref)
    paragraph(doc,"Report prepared for TATA VENKATA SATYA SAI KOUSHIK · B231284EE",size=9,color=GRAY,align=WD_ALIGN_PARAGRAPH.CENTER,before=8,after=0)

    OUT.parent.mkdir(exist_ok=True)
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
