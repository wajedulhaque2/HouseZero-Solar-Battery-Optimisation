# Formula, Query & Model Guide

## 1. Power Query

The workbook contains two query connections:

- `q_Loads_Raw` - source ingestion;
- `q_Loads_Clean` - cleaned hourly data loaded into the workbook/model.

The methodology states that the model covers **1 June 2023 to 31 May 2024**, giving 8,784 hourly observations.

## 2. Named ranges

The final workbook defines named ranges including:

```text
Existing_PV_kWp
Scenario_PV_kWp
Battery_Capacity_kWh
Battery_Charge_kW
Battery_Discharge_kW
Charge_Efficiency
Discharge_Efficiency
Minimum_SOC
Maximum_SOC
Initial_SOC
Model_Hours
Import_Tariff
Export_Rate
PV_Capex_per_kWp
Battery_Capex_per_kWh
OandM_Rate
Discount_Rate
Energy_Price_Growth
PV_Degradation
Battery_Replacement_Year
Battery_Replacement_Pct
Battery_Incentive
Project_Life
```

These names keep the hourly battery equations readable and make scenario changes easier to audit.

## 3. Hourly solar and battery dispatch

The `Hourly_Data` table contains the main dispatch engine.

### Scenario PV generation

```excel
=tblHourlyData[[#This Row],[PV_Generation_kWh]]
 * Scenario_PV_kWp / Existing_PV_kWp
```

### Direct PV consumption

```excel
=MIN(
 tblHourlyData[[#This Row],[Building_Demand_kWh]],
 tblHourlyData[[#This Row],[Scenario_PV_kWh]]
)
```

### PV surplus

```excel
=MAX(
 tblHourlyData[[#This Row],[Scenario_PV_kWh]]
 - tblHourlyData[[#This Row],[Building_Demand_kWh]],
 0
)
```

### Load deficit

```excel
=MAX(
 tblHourlyData[[#This Row],[Building_Demand_kWh]]
 - tblHourlyData[[#This Row],[Scenario_PV_kWh]],
 0
)
```

### Starting state of charge

```excel
=IF(
 tblHourlyData[[#This Row],[Row_ID]]=1,
 Initial_SOC*Battery_Capacity_kWh,
 INDEX(
   tblHourlyData[Battery_SOC_End_kWh],
   tblHourlyData[[#This Row],[Row_ID]]-1
 )
)
```

### Battery charge

```excel
=MAX(0,MIN(
 tblHourlyData[[#This Row],[PV_Surplus_kWh]],
 Battery_Charge_kW,
 (Maximum_SOC*Battery_Capacity_kWh
  -tblHourlyData[[#This Row],[SOC_Start_kWh]])/Charge_Efficiency
))
```

### Battery discharge

```excel
=MAX(0,MIN(
 tblHourlyData[[#This Row],[Load_Deficit_kWh]],
 Battery_Discharge_kW,
 (tblHourlyData[[#This Row],[SOC_Start_kWh]]
  -Minimum_SOC*Battery_Capacity_kWh)*Discharge_Efficiency
))
```

### Ending state of charge

```excel
=MIN(
 Maximum_SOC*Battery_Capacity_kWh,
 MAX(
   Minimum_SOC*Battery_Capacity_kWh,
   tblHourlyData[[#This Row],[SOC_Start_kWh]]
   +tblHourlyData[[#This Row],[Battery_Charge_kWh]]*Charge_Efficiency
   -tblHourlyData[[#This Row],[Battery_Discharge_kWh]]/Discharge_Efficiency
 )
)
```

### Scenario grid import

```excel
=MAX(
 tblHourlyData[[#This Row],[Load_Deficit_kWh]]
 -tblHourlyData[[#This Row],[Battery_Discharge_kWh]],
 0
)
```

### Scenario grid export

```excel
=MAX(
 tblHourlyData[[#This Row],[PV_Surplus_kWh]]
 -tblHourlyData[[#This Row],[Battery_Charge_kWh]],
 0
)
```

### Battery losses

```excel
=tblHourlyData[[#This Row],[Battery_Charge_kWh]]*(1-Charge_Efficiency)
 +tblHourlyData[[#This Row],[Battery_Discharge_kWh]]*(1/Discharge_Efficiency-1)
```

## 4. Financial model

### Additional PV CAPEX

```excel
=MAX(Scenario_PV_kWp-Existing_PV_kWp,0)*PV_Capex_per_kWp
```

### Battery CAPEX

```excel
=Battery_Capacity_kWh*Battery_Capex_per_kWh
```

### Net incremental investment

```excel
=Additional_PV_CAPEX + MAX(Battery_CAPEX-Battery_Incentive,0)
```

### Year-1 / annual benefit growth

```excel
=$E$5*(1+Energy_Price_Growth)^(Year-1)
     *(1-PV_Degradation)^(Year-1)
```

### Annual O&M

```excel
=$E$9*(1+Energy_Price_Growth)^(Year-1)
```

### Battery replacement

```excel
=IF(
 Year=Battery_Replacement_Year,
 Initial_Battery_CAPEX*Battery_Replacement_Pct,
 0
)
```

### Discount factor

```excel
=1/(1+Discount_Rate)^Year
```

### Discounted cash flow

```excel
=Net_Cash_Flow*Discount_Factor
```

### NPV

```excel
=SUM($G$21:$G$46)
```

### IRR

```excel
=IF($E$8=0,"N/A",IFERROR(IRR($E$21:$E$46),"No IRR"))
```

The workbook tests whether cumulative cash flow ever becomes non-negative and returns `No payback` when it does not.

## 5. Scenario analysis

The workbook uses two-variable Excel Data Tables to test NPV across:

- total PV capacities from 15 to 30 kWp;
- battery capacities from 0 to 20 kWh;
- alternative export compensation from 0% to 100% of the import tariff.

Dedicated Data Table driver cells are stored in `Scenario Analysis!M2:M5` and linked through the named ranges `Scenario_PV_kWp`, `Battery_Capacity_kWh` and `Export_Rate`.

The break-even section records Goal Seek-style outputs for battery cost/incentive requirements rather than hiding them inside the hourly calculation table.

## 6. Model-audit observations

Auditability is strong because the final workbook separates:

```text
sources/assumptions -> named inputs -> hourly dispatch -> annual energy summary
-> financial cash flows -> NPV/IRR/payback -> scenario/break-even analysis -> dashboard
```

A reviewer can therefore trace a dashboard result back to annual cash flow and then back to the underlying hourly dispatch equations.