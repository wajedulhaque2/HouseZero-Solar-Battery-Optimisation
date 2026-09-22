"""Interactive HouseZero solar and battery model built from cached workbook inputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from model import Scenario, calculate


ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="HouseZero | solar & battery", page_icon="☀️", layout="wide")
st.sidebar.title("HouseZero")
dark = st.sidebar.toggle("Dark mode", value=False)
BG, SURFACE, TEXT, MUTED, GRID, BORDER, TEAL, GOLD, BLUE = (
    ("#101B26", "#1C2D3B", "#F5F8FA", "#B8C9D3", "#314757", "#3B5060", "#40C6C1", "#FFC45B", "#84AFFF")
    if dark else
    ("#F5F8FA", "#FFFFFF", "#173348", "#516879", "#E3EBEF", "#DCE6EB", "#168A84", "#D68B20", "#416B9B")
)
st.markdown(f"""
<style>
.stApp {{background:{BG};color:{TEXT};}}
[data-testid="stHeader"] {{background:{BG};}}
[data-testid="stSidebar"] {{background:{SURFACE};border-right:1px solid {BORDER};color:{TEXT};}}
.stApp h1,.stApp h2,.stApp h3,.stApp p,.stApp label,[data-testid="stSidebar"] h1,[data-testid="stSidebar"] label {{color:{TEXT};}}
.stApp [data-testid="stCaptionContainer"] p,[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{color:{MUTED};}}
[data-testid="stMetric"],[data-testid="stPlotlyChart"],[data-testid="stDataFrame"] {{background:{SURFACE};border:1px solid {BORDER};border-radius:10px;}}
[data-testid="stMetric"] {{padding:.85rem 1rem;min-height:115px;}}
[data-testid="stMetric"] label,[data-testid="stMetricValue"] {{color:{TEXT};}}
[data-testid="stPlotlyChart"],[data-testid="stDataFrame"] {{padding:.3rem;}}
.scope {{background:{'#263F49' if dark else '#E6F3F0'};border-left:4px solid {TEAL};padding:.75rem 1rem;margin:.4rem 0 1.1rem;color:{TEXT};}}
[data-baseweb="select"] > div,[data-baseweb="input"] > div {{background:{SURFACE};color:{TEXT};border-color:{BORDER};}}
[data-baseweb="select"] *,[data-baseweb="input"] input,[data-baseweb="popover"] li {{color:{TEXT};}}
[data-baseweb="popover"],[data-baseweb="popover"] li {{background:{SURFACE};}}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "hourly.csv.gz", parse_dates=["local_time"])


@st.cache_data
def run(pv_kwp: int, battery_kwh: int, export_fraction: float):
    return calculate(load(), Scenario(float(pv_kwp), float(battery_kwh), export_fraction))


def plot(fig: go.Figure, height: int = 410, bottom: int = 55) -> None:
    fig.update_layout(
        template="plotly_dark" if dark else "plotly_white", height=height,
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE, font={"family": "Arial", "size": 12, "color": TEXT},
        title={"x": .025, "xanchor": "left", "font": {"size": 18}},
        margin={"l": 48, "r": 34, "t": 65, "b": bottom},
        hoverlabel={"font": {"family": "Arial"}},
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, automargin=True)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, automargin=True)
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})


st.sidebar.caption("Source-backed energy and retrofit screening")
view = st.sidebar.radio("View", ["Overview", "Energy patterns", "Scenario economics", "Sources & method"])
st.sidebar.divider()
pv_kwp = st.sidebar.slider("Total solar PV (kWp)", 15, 30, 15, 1)
battery_kwh = st.sidebar.slider("Battery capacity (kWh)", 0, 20, 10, 1)
export_pct = st.sidebar.slider("Export compensation (% of import tariff)", 0, 100, 100, 5)
hourly, metrics, cash = run(pv_kwp, battery_kwh, export_pct / 100)

st.title({"Overview": "Solar & battery retrofit", "Energy patterns": "Hourly energy patterns",
          "Scenario economics": "Scenario economics", "Sources & method": "Sources and model rules"}[view])
st.caption("HouseZero · 8,784 measured hourly observations · 1 Jun 2023–31 May 2024")
st.markdown(f'<div class="scope">{pv_kwp} kWp total PV · {battery_kwh} kWh battery · {export_pct}% export compensation</div>',
            unsafe_allow_html=True)

if view == "Overview":
    cards = st.columns(4)
    cards[0].metric("25-year NPV", f"${metrics['npv']:,.0f}")
    cards[1].metric("Grid imports", f"{metrics['grid_import']:,.0f} kWh")
    cards[2].metric("Electricity self-sufficiency", f"{metrics['self_sufficiency']:.1%}")
    cards[3].metric("Incremental investment", f"${metrics['investment']:,.0f}")
    st.caption("NPV uses the workbook's annual bill floor at $0. Exports cannot produce a negative annual bill in this model.")

    totals = pd.DataFrame({"Case": ["Existing 15 kWp", "Selected retrofit"],
                           "Grid import": [metrics["baseline_import"], metrics["grid_import"]],
                           "Grid export": [metrics["baseline_export"], metrics["grid_export"]]})
    long = totals.melt(id_vars="Case", var_name="Flow", value_name="kWh")
    fig = px.bar(long, x="kWh", y="Case", color="Flow", barmode="group", orientation="h",
                 color_discrete_map={"Grid import": BLUE, "Grid export": GOLD}, text_auto=",.0f")
    fig.update_layout(title="Annual grid energy: existing system versus selected retrofit", legend_title=None,
                      legend={"orientation": "h", "y": -0.27, "x": 0})
    fig.update_yaxes(title=None, showgrid=False)
    fig.update_traces(textposition="outside", cliponaxis=False)
    plot(fig, 360, 95)

    month = hourly.assign(month=hourly.local_time.dt.to_period("M").astype(str)).groupby("month", as_index=False).agg(
        demand=("demand_kwh", "sum"), pv=("pv_kwh", "sum"), imports=("grid_import_kwh", "sum"))
    monthly = month.melt(id_vars="month", var_name="Measure", value_name="kWh")
    fig = px.line(monthly, x="month", y="kWh", color="Measure", markers=True,
                  color_discrete_map={"demand": BLUE, "pv": GOLD, "imports": TEAL})
    fig.update_layout(title="Monthly demand, solar generation and grid imports", legend_title=None,
                      legend={"orientation": "h", "y": -0.3, "x": 0})
    fig.update_xaxes(title=None, tickangle=0)
    plot(fig, 430, 100)

elif view == "Energy patterns":
    month = st.selectbox("Inspect month", ["All months", *[f"{m:02d}" for m in range(1, 13)]],
                         format_func=lambda x: "All months" if x == "All months" else pd.Timestamp(2024, int(x), 1).strftime("%B"))
    selected = hourly if month == "All months" else hourly.loc[hourly.local_time.dt.month.eq(int(month))]
    day = selected.assign(hour=selected.local_time.dt.hour).groupby("hour", as_index=False).agg(
        demand=("demand_kwh", "mean"), pv=("pv_kwh", "mean"), imports=("grid_import_kwh", "mean"),
        charge=("charge_kwh", "mean"), discharge=("discharge_kwh", "mean"))
    profile = day.melt(id_vars="hour", value_vars=["demand", "pv", "imports"], var_name="Measure", value_name="kWh per hour")
    fig = px.line(profile, x="hour", y="kWh per hour", color="Measure", markers=True,
                  color_discrete_map={"demand": BLUE, "pv": GOLD, "imports": TEAL})
    fig.update_layout(title="Typical hourly profile (mean across selected days)", legend_title=None,
                      legend={"orientation": "h", "y": -0.26, "x": 0})
    fig.update_xaxes(dtick=2, title="Local hour")
    plot(fig, 430, 95)
    battery = day.melt(id_vars="hour", value_vars=["charge", "discharge"], var_name="Flow", value_name="kWh per hour")
    fig = px.bar(battery, x="hour", y="kWh per hour", color="Flow", barmode="group",
                 color_discrete_map={"charge": GOLD, "discharge": TEAL})
    fig.update_layout(title="Typical battery charging and discharge", legend_title=None,
                      legend={"orientation": "h", "y": -0.25, "x": 0})
    fig.update_xaxes(dtick=2, title="Local hour")
    plot(fig, 380, 95)
    st.caption(f"Selected hours: {len(selected):,}. Profiles are mean hourly energy, not peaks or installed capacity.")

elif view == "Scenario economics":
    cards = st.columns(4)
    cards[0].metric("25-year NPV", f"${metrics['npv']:,.0f}")
    cards[1].metric("Year-1 energy savings", f"${metrics['annual_savings']:,.0f}")
    cards[2].metric("Baseline annual bill", f"${metrics['baseline_bill']:,.0f}")
    cards[3].metric("Retrofit annual bill", f"${metrics['retrofit_bill']:,.0f}")
    st.caption("Both bill figures use MAX(0, import cost − export credit), as in the workbook. At 100% export compensation, both may floor to zero.")
    comparison = []
    for capacity in (0, 5, 10, 15, 20):
        _, outcome, _ = run(pv_kwp, capacity, export_pct / 100)
        comparison.append({"Battery (kWh)": capacity, "NPV ($)": outcome["npv"]})
    fig = px.line(pd.DataFrame(comparison), x="Battery (kWh)", y="NPV ($)", markers=True, text="NPV ($)")
    fig.update_traces(line={"color": TEAL, "width": 3}, marker={"size": 9}, texttemplate="$%{y:,.0f}",
                      textposition="top center", cliponaxis=False)
    fig.add_hline(y=0, line_color=MUTED, line_dash="dash")
    fig.update_layout(title=f"Battery capacity sensitivity at {pv_kwp} kWp PV and {export_pct}% export compensation")
    plot(fig, 430)
    fig = px.bar(cash.loc[cash.year.gt(0)], x="year", y="cash_flow", color_discrete_sequence=[BLUE])
    fig.update_layout(title="Annual incremental net cash flow", xaxis_title="Project year", yaxis_title="Cash flow ($)")
    plot(fig, 370)
    st.caption(f"Simple payback: {metrics['payback'] if metrics['payback'] is not None else 'No payback within 25 years'}. Year 12 includes battery replacement at 60% of initial battery cost.")

else:
    st.markdown("""
### Source and coverage
The repository workbook `workbook/HouseZero_Solar_Battery_Optimisation_Portfolio.xlsx` contains the cached `Hourly_Data` table: 8,784 hourly demand and PV observations from 1 June 2023 to 31 May 2024. `dashboard/prepare_data.py` extracts the local timestamp, building demand and measured 15 kWp PV generation to the checked-in CSV snapshot. The original workbook remains the source of record.

### Operating scenario
Additional PV scales measured generation by total PV capacity / 15 kWp. Battery dispatch follows the workbook's 5 kW charge/discharge limits, 95% efficiency each way, 10–90% state-of-charge limits, and initial state of charge of 50%. No hourly price dispatch optimisation is assumed.

### Financial scenario
Import price is $0.2512/kWh. Export compensation is adjustable as a percentage of that tariff. Like the workbook, each annual bill is floored at zero before baseline-to-retrofit savings are calculated. The investment is $3,450 per additional kWp plus $1,325 per battery kWh, with annual O&M at 1.35% of CAPEX, 2% price/O&M growth, 0.5% PV-related benefit degradation, a battery replacement in year 12 at 60% of original battery cost, and a 6% discount rate over 25 years.

The existing 15 kWp array is a sunk asset. The financial result is an incremental screening model based on one measured year and fixed cost assumptions. It excludes outage resilience and unpriced non-financial benefits.
""")
