"""Hourly dispatch and discounted cash flow matching the workbook rules."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


EXISTING_PV = 15.0
IMPORT_TARIFF = 0.2512
PV_CAPEX = 3450.0
BATTERY_CAPEX = 1325.0
OM_RATE = 0.0135
DISCOUNT_RATE = 0.06
GROWTH = 0.02
DEGRADATION = 0.005
PROJECT_YEARS = 25


@dataclass(frozen=True)
class Scenario:
    pv_kwp: float = 15.0
    battery_kwh: float = 10.0
    export_fraction: float = 1.0


def calculate(hourly: pd.DataFrame, scenario: Scenario) -> tuple[pd.DataFrame, dict[str, float], pd.DataFrame]:
    demand = hourly.demand_kwh.to_numpy(dtype=float)
    pv = hourly.pv_kwh.to_numpy(dtype=float) * scenario.pv_kwp / EXISTING_PV
    surplus = np.maximum(pv - demand, 0)
    deficit = np.maximum(demand - pv, 0)
    capacity = scenario.battery_kwh
    soc = 0.5 * capacity
    charge = np.zeros(len(hourly))
    discharge = np.zeros(len(hourly))
    state = np.zeros(len(hourly))
    for i in range(len(hourly)):
        charge[i] = max(0, min(surplus[i], 5.0, (0.9 * capacity - soc) / 0.95))
        discharge[i] = max(0, min(deficit[i], 5.0, (soc - 0.1 * capacity) * 0.95))
        soc = min(0.9 * capacity, max(0.1 * capacity, soc + charge[i] * 0.95 - discharge[i] / 0.95))
        state[i] = soc

    result = hourly[["local_time", "demand_kwh"]].copy()
    result["pv_kwh"] = pv
    result["grid_import_kwh"] = deficit - discharge
    result["grid_export_kwh"] = surplus - charge
    result["charge_kwh"] = charge
    result["discharge_kwh"] = discharge
    result["soc_kwh"] = state

    base_import = float(np.maximum(demand - hourly.pv_kwh.to_numpy(dtype=float), 0).sum())
    base_export = float(np.maximum(hourly.pv_kwh.to_numpy(dtype=float) - demand, 0).sum())
    export_rate = IMPORT_TARIFF * scenario.export_fraction
    # This floor is part of the workbook's Financial_Model!E3:E5.
    baseline_bill = max(0, base_import * IMPORT_TARIFF - base_export * export_rate)
    retrofit_bill = max(0, result.grid_import_kwh.sum() * IMPORT_TARIFF - result.grid_export_kwh.sum() * export_rate)
    annual_savings = baseline_bill - retrofit_bill
    additional_pv = max(scenario.pv_kwp - EXISTING_PV, 0)
    battery_cost = capacity * BATTERY_CAPEX
    investment = additional_pv * PV_CAPEX + battery_cost
    om = investment * OM_RATE
    flows = [-investment]
    for year in range(1, PROJECT_YEARS + 1):
        gross = annual_savings * ((1 + GROWTH) * (1 - DEGRADATION)) ** (year - 1)
        upkeep = om * (1 + GROWTH) ** (year - 1)
        replacement = battery_cost * 0.6 if year == 12 else 0
        flows.append(gross - upkeep - replacement)
    cash = pd.DataFrame({"year": range(PROJECT_YEARS + 1), "cash_flow": flows})
    cash["discounted"] = cash.cash_flow / (1 + DISCOUNT_RATE) ** cash.year
    cash["cumulative"] = cash.cash_flow.cumsum()
    npv = float(cash.discounted.sum())
    payback = next((int(r.year) for r in cash.itertuples() if r.year > 0 and r.cumulative >= 0), None)

    metrics = {
        "demand": float(demand.sum()), "pv_generation": float(pv.sum()),
        "baseline_import": base_import, "baseline_export": base_export,
        "grid_import": float(result.grid_import_kwh.sum()), "grid_export": float(result.grid_export_kwh.sum()),
        "charge": float(charge.sum()), "discharge": float(discharge.sum()),
        "self_sufficiency": float(1 - result.grid_import_kwh.sum() / demand.sum()),
        "baseline_bill": baseline_bill, "retrofit_bill": retrofit_bill,
        "annual_savings": annual_savings, "investment": investment, "npv": npv,
        "payback": payback,
    }
    return result, metrics, cash
