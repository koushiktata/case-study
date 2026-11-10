from __future__ import annotations

import math
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
DATA = ROOT / "data" / "hour.csv"
OUT = ROOT / "reports" / "Bike_Sharing_Demand_Estimation_Report.docx"
NAVY = "15313A"
TEAL = "147D6E"
MINT = "E5F5EF"
PALE = "F1F5F4"
GRAY = "61777B"


def shade(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, value, *, bold=False, color=NAVY, size=9):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(1)
    run = p.add_run(str(value))
    run.bold = bold
    run.font.name = "Aptos"
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.autofit = False
    for i, label in enumerate(headers):
        set_cell_text(t.rows[0].cells[i], label, bold=True, color="FFFFFF", size=8)
        shade(t.rows[0].cells[i], NAVY)
    for idx, row in enumerate(rows):
        cells = t.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value, size=8.5)
            if idx % 2 == 1:
                shade(cells[i], PALE)
    if widths:
        for row in t.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Inches(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def callout(doc, title, body, fill=MINT):
    t = doc.add_table(rows=1, cols=1)
    cell = t.cell(0, 0)
    shade(cell, fill)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(5)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(title + "  ")
    r.bold = True
    r.font.color.rgb = RGBColor.from_string(TEAL)
    r.font.size = Pt(10)
    r = p.add_run(body)
    r.font.color.rgb = RGBColor.from_string(NAVY)
    r.font.size = Pt(9.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def page_field(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("CYCLESIGHT  ·  ")
    run.font.name = "Aptos"
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor.from_string(GRAY)
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    paragraph._p.append(field)


def build():
    df = pd.read_csv(DATA, parse_dates=["dteday"])
    rush = df[df.hr.isin([7, 8, 9, 16, 17, 18, 19])].cnt.to_numpy(float)
    other = df[~df.hr.isin([7, 8, 9, 16, 17, 18, 19])].cnt.to_numpy(float)
    v1, v2 = rush.var(ddof=1), other.var(ddof=1)
    se = math.sqrt(v1 / len(rush) + v2 / len(other))
    t_stat = (rush.mean() - other.mean()) / se
    pval = 0.5 * math.erfc(t_stat / math.sqrt(2))
    pooled = math.sqrt(((len(rush)-1)*v1 + (len(other)-1)*v2) / (len(rush)+len(other)-2))
    d_effect = (rush.mean() - other.mean()) / pooled

    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(.72)
    sec.bottom_margin = Inches(.68)
    sec.left_margin = Inches(.82)
    sec.right_margin = Inches(.82)
    styles = doc.styles
    styles["Normal"].font.name = "Aptos"
    styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "Aptos")
    styles["Normal"].font.size = Pt(9.5)
    styles["Normal"].font.color.rgb = RGBColor.from_string(NAVY)
    styles["Normal"].paragraph_format.space_after = Pt(6)
    for key, size, color in [("Heading 1", 19, NAVY), ("Heading 2", 12, TEAL), ("Heading 3", 10, NAVY)]:
        st = styles[key]
        st.font.name = "Aptos Display"
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor.from_string(color)
        st.paragraph_format.space_before = Pt(10)
        st.paragraph_format.space_after = Pt(5)
    # Remove Word's built-in blue rule from the Title paragraph style.
    title_style = styles["Title"]
    title_style.font.name = "Aptos Display"
    title_ppr = title_style._element.get_or_add_pPr()
    for border in title_ppr.findall(qn("w:pBdr")):
        title_ppr.remove(border)
    footer = sec.footer.paragraphs[0]
    page_field(footer)

    # Cover and executive summary
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(42)
    r = p.add_run("CYCLESIGHT  /  CASE STUDY")
    r.bold = True
    r.font.name = "Aptos"
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor.from_string(TEAL)
    title = doc.add_paragraph(style="Title")
    title.paragraph_format.space_before = Pt(13)
    title.paragraph_format.space_after = Pt(7)
    title_run = title.add_run("Bike Sharing Demand Estimation")
    title_run.font.name = "Aptos Display"
    title_run.font.size = Pt(32)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor.from_string(NAVY)
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(20)
    sr = subtitle.add_run("A forecasting prototype and evidence-led fleet planning study")
    sr.font.size = Pt(14)
    sr.font.color.rgb = RGBColor.from_string(GRAY)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    r = p.add_run("REPORT  ·  NOVEMBER 2026\n")
    r.bold = True
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor.from_string(TEAL)
    r2 = p.add_run("Capital Bikeshare hourly data · Washington, D.C. · 2011–2012")
    r2.font.size = Pt(10)
    r2.font.color.rgb = RGBColor.from_string(GRAY)
    doc.add_paragraph()
    callout(doc, "Executive finding", "Demand is concentrated around weekday commute periods and shifts with season and weather. The data supports forecasting when the system is busy. It cannot establish where bikes are unavailable or whether a larger total fleet is needed.")
    doc.add_heading("Decision in brief", level=2)
    doc.add_paragraph("Use the forecast as a timing aid for operations and test redistribution with station-level inventory and denied-rental data. Do not make a purchase decision from citywide rental totals alone. The dataset records completed trips; a rider who tried and failed to rent is invisible in these files.")
    table(doc, ["Evidence", "Observed result", "Operational reading"], [
        ["Data integrity", f"{len(df):,} hourly rows; no missing cells, duplicate rows, negative counts, or count-identity failures", "Suitable for this descriptive analysis"],
        ["Peak pattern", f"Mean demand peaks at {df.groupby('hr').cnt.mean().idxmax():02d}:00 ({df.groupby('hr').cnt.mean().max():.1f} rentals/hour)", "Plan around specific hours"],
        ["Rush-hour test", f"{rush.mean():.1f} vs {other.mean():.1f} rentals/hour; d = {d_effect:.2f}", "Strong difference in timing; descriptive test"],
        ["Capacity illustration", "About 360 bikes at the historical P95 hour under stated defaults", "System-wide concurrency proxy, not a purchase recommendation"],
        ["Fleet decision", "Station stock and failed rental records are absent", "Evidence is insufficient to decide buy vs redistribute"],
    ], widths=[1.15, 3.0, 2.65])
    doc.add_page_break()

    doc.add_heading("1. Case question and scope", level=1)
    doc.add_paragraph("The candidate case study asks whether complaints about bike availability should lead the operator to purchase bicycles. It requests data quality and feature exploration, a testable hypothesis, a model-based estimate of bike need, and a prototype that accepts natural-language demand questions.")
    doc.add_paragraph("This deliverable addresses each request with an explicit scope boundary: the source data is a two-year, citywide aggregate rental log. It measures completed rental counts and contextual variables, not station inventory or unmet requests. Forecasting observed rentals can inform hourly planning, but it is not a direct measurement of unconstrained demand.")
    doc.add_heading("Analysis objective", level=2)
    doc.add_paragraph("Estimate hourly completed rentals from calendar and weather features, present demand patterns in an operations-facing interface, and demonstrate how a forecast can be translated into an assumption-based system-wide capacity estimate.")
    doc.add_heading("2. Data and preparation", level=1)
    doc.add_paragraph("The supplied files contain 17,379 hourly observations and 731 daily observations covering January 2011 through December 2012. The hourly file contains 17 source columns, including the target count `cnt`, user-type counts, calendar fields, season, weather situation, and normalized weather measurements. The daily file supports daily-level summaries; the forecasting model is hourly.")
    table(doc, ["Quality check", "Result", "Treatment"], [
        ["Hourly rows", f"{len(df):,}", "Retained all records"],
        ["Missing cells", str(int(df.isna().sum().sum())), "No imputation needed for supplied file"],
        ["Duplicate rows", str(int(df.duplicated().sum())), "No rows removed"],
        ["Negative target counts", str(int((df.cnt < 0).sum())), "None found"],
        ["Count identity", str(int((df.cnt != df.casual + df.registered).sum())) + " failures", "cnt equals casual + registered"],
        ["Heaviest weather group", f"{int((df.weathersit == 4).sum())} hours", "Keep, but interpret its average cautiously"],
    ], widths=[1.65, 1.6, 3.55])
    doc.add_paragraph("The target has a mean of {:.1f}, median of {:.0f}, and 95th percentile of {:.1f} rentals per hour. Its maximum is {} rentals, recorded on {} at {:02d}:00. Registered riders account for {:.1f}% of completed rentals.".format(df.cnt.mean(), df.cnt.median(), df.cnt.quantile(.95), int(df.cnt.max()), df.loc[df.cnt.idxmax(),"dteday"].date(), int(df.loc[df.cnt.idxmax(),"hr"]), df.registered.sum()/df.cnt.sum()*100))
    doc.add_heading("Feature design", level=2)
    doc.add_paragraph("The model uses season, year, month, hour, holiday, weekday, working-day flag, weather category, temperature, feels-like temperature, humidity, and wind speed. The raw temperature values are normalized in the source files; the dashboard converts them to human-readable units for exploration. The target and post-rental user counts are excluded from predictors to avoid leakage.")
    doc.add_page_break()

    doc.add_heading("3. Demand exploration", level=1)
    hourly = df.groupby("hr").cnt.mean().sort_values(ascending=False)
    table(doc, ["Pattern", "Finding", "Planning meaning"], [
        ["Hourly peak", "17:00 averages {:.1f}; 18:00 {:.1f}; 08:00 {:.1f} rentals/hour".format(hourly.loc[17],hourly.loc[18],hourly.loc[8]), "Plan around recurring peaks, not daily averages"],
        ["Working day", "Mean {:.1f}; non-working day mean {:.1f}".format(df[df.workingday==1].cnt.mean(),df[df.workingday==0].cnt.mean()), "Total means are close; profiles differ by hour"],
        ["Season", "Fall {:.1f}; summer {:.1f}; winter {:.1f}; spring {:.1f} rentals/hour".format(*[df[df.season==i].cnt.mean() for i in [3,2,4,1]]), "Expected seasonal demand varies materially"],
        ["Weather", "Clear {:.1f}; mist {:.1f}; light precipitation {:.1f}; heavy weather {:.1f}".format(*[df[df.weathersit==i].cnt.mean() for i in range(1,5)]), "Worsening weather aligns with lower completed rentals; severe group is sparse"],
        ["Year", "2011 {:.1f}; 2012 {:.1f} mean rentals/hour".format(df[df.yr==0].cnt.mean(),df[df.yr==1].cnt.mean()), "Historical growth cautions against treating the level as stationary"],
    ], widths=[1.1, 3.0, 2.7])
    doc.add_paragraph("Working days have pronounced morning and evening commuting peaks. Non-working days show a broader midday profile. This difference in shape matters more to dispatch timing than the modest difference between the overall day-type averages. Fall is the highest-demand season in these observations; spring is the lowest.")
    callout(doc, "Reading the weather result", "There are only three hours in the heaviest weather category. Its mean is descriptive and unstable, so the dashboard shows the group size beside the average.", fill="FFF3DF")

    doc.add_heading("4. Hypothesis test", level=1)
    doc.add_paragraph("The prototype tests one directional question: is mean completed rental demand higher during rush hours (07:00–09:00 and 16:00–19:00) than during the remaining hours?")
    table(doc, ["Element", "Specification"], [
        ["Null hypothesis", "Mean hourly rentals in rush hours are no higher than in other hours."],
        ["Alternative", "Mean hourly rentals are higher in rush hours."],
        ["Test", "One-sided Welch two-sample t-test; large-sample normal approximation for the p-value."],
        ["Observed means", "Rush {:.1f} (n={:,}); other {:.1f} (n={:,}) rentals/hour.".format(rush.mean(),len(rush),other.mean(),len(other))],
        ["Statistic", "t = {:.2f}; {}; Cohen's d = {:.3f}.".format(t_stat,"p < 1e-16" if pval < 1e-16 else f"p = {pval:.3g}",d_effect)],
        ["Decision at α = 0.05", "Reject the null; rush-hour mean demand is higher in this historical sample."],
    ], widths=[1.55, 5.25])
    doc.add_paragraph("The standardized difference is large, supporting focused planning for those periods. The p-value is approximate and hourly observations are temporally related, so the result is descriptive rather than a causal or fully independent-sample claim. A stronger inferential analysis could compare daily matched profiles or use block bootstrap confidence intervals.")

    doc.add_heading("5. Forecasting model", level=1)
    doc.add_paragraph("The API builds a Scikit-learn pipeline with one-hot encoding for categorical calendar and weather fields, median imputation and scaling for continuous weather fields, and a Random Forest regressor for hourly `cnt`. A chronological split places the earliest 80% of dates in training and the latest 20% in the holdout set. This better reflects the future-prediction task than randomly mixing hours from the same dates across both sets.")
    doc.add_paragraph("The API calculates holdout R², mean absolute error, and root mean squared error at first model load. These values are returned by `/health` and shown in the dashboard. The model is designed to forecast completed rentals under the historical data-generating process; it cannot observe latent or denied demand. The report does not quote a score before that runtime evaluation has been run.")
    doc.add_page_break()

    doc.add_heading("6. Capacity planning simulator", level=1)
    doc.add_paragraph("The fleet planner turns a predicted hourly rental count into an illustrative concurrent-bike requirement. It exposes the assumed average trip duration, demand buffer, and maintenance reserve so the operator can inspect sensitivity instead of receiving a falsely precise number.")
    callout(doc, "Planning formula", "ceil(predicted hourly rentals × (1 + demand buffer) × trip duration in hours ÷ (1 − maintenance reserve share))")
    table(doc, ["Input", "Default", "Status"], [
        ["Average trip duration", "30 minutes", "User-set assumption; absent from files"],
        ["Demand buffer", "15%", "User-set planning allowance"],
        ["Maintenance reserve", "10%", "User-set allowance for unavailable bikes"],
    ], widths=[2.0, 1.5, 3.3])
    doc.add_paragraph("The output is a system-wide concurrency approximation, not a recommended purchase quantity. The data lacks trip duration, station capacity, bike locations, station-level stock, rebalancing movements, and failed rental attempts. The estimate also does not model round-trip return timing or spatial imbalance.")
    p95_plan = math.ceil(float(df.cnt.quantile(.95)) * 1.15 * (30/60) / (1-.10))
    doc.add_paragraph("Worked example using the historical 95th-percentile hour: {:.1f} rentals/hour × 1.15 demand buffer × 0.5 trip-hours ÷ 0.90 available-fleet share gives about {} bikes. This is a transparent arithmetic illustration using observed demand, not a model forecast or a fleet purchase recommendation.".format(df.cnt.quantile(.95), p95_plan))

    doc.add_heading("7. Prototype and architecture", level=1)
    doc.add_paragraph("CycleSight pairs a Streamlit interface with a FastAPI JSON service. The interface includes an executive overview, interactive demand lab, hypothesis page, fleet planner, and natural-language explorer. The explorer uses a transparent local parser for common hour, season, day-type, weather, and temperature phrases, then calls the same prediction and planning services as the form-based planner.")
    table(doc, ["Layer", "Responsibility"], [
        ["Streamlit frontend", "Charts, controls, scenario questions, and clear display of assumptions and limitations."],
        ["FastAPI backend", "Data summaries, validation, model caching, inference, hypothesis calculation, and fleet arithmetic."],
        ["Data and model", "Supplied CSV files; chronological split; fitted Random Forest pipeline."],
        ["Connection", "Frontend sends HTTP JSON to backend routes; local defaults use ports 8501 and 8000."],
    ], widths=[1.6, 5.2])
    doc.add_paragraph("Key routes are `/health`, `/overview`, `/hypothesis`, `/predict`, `/fleet`, and `/ask`. The component diagram, environment variables, and deployment notes are in `docs/architecture.md`.")

    doc.add_heading("8. Recommendation and next evidence", level=1)
    doc.add_paragraph("Use hourly forecasts to schedule availability checks and redistribution trials around the commute peaks. Do not approve or reject a fleet purchase on the basis of this aggregate dataset. The complaint could arise from local station imbalance, a genuinely undersized fleet, or both; the available files cannot distinguish those explanations.")
    table(doc, ["Collect next", "Why it matters"], [
        ["Station inventory and dock capacity by timestamp", "Shows where bikes and empty docks are located when demand arrives."],
        ["Attempted and denied rentals", "Measures unmet demand missing from completed-trip counts."],
        ["Trip start/end stations and duration", "Enables station-level flows and a defensible concurrent-bike estimate."],
        ["Rebalancing vehicle movements and labor time", "Measures whether targeted redistribution reduces shortages."],
        ["A controlled redistribution pilot", "Tests operational effect before committing capital."],
    ], widths=[2.85, 3.95])
    doc.add_heading("Conclusion", level=2)
    doc.add_paragraph("The case supports building an hourly demand tool and planning around recurring peaks. The supplied data is clean, demand varies strongly by hour and context, and a chronological forecasting pipeline is implemented in the connected prototype. A buy-versus-redistribute recommendation requires station-level inventory and unmet-demand evidence that the dataset does not contain.")

    doc.add_heading("Sources", level=1)
    doc.add_paragraph("1. Candidate Case Study, supplied PDF. Problem statement and requested deliverables.")
    doc.add_paragraph("2. Bike Sharing Dataset Readme, supplied with the CSV files. Dataset fields, coverage, and license citation.")
    doc.add_paragraph("3. Fanaee-T, Hadi, and Joao Gama. “Event labeling combining ensemble detectors and background knowledge.” Progress in Artificial Intelligence (2013). DOI: 10.1007/s13748-013-0040-3.")
    doc.add_paragraph("4. Bike Sharing Demand Estimation Final Report, supplied DOCX. Used as a structural and analytical reference; case-specific operational claims were not imported unless supported by the supplied candidate brief or dataset.")

    OUT.parent.mkdir(exist_ok=True)
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
