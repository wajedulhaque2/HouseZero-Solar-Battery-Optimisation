# Data Sources & Assumptions

The workbook's `Sources_Assumptions` sheet records the following source categories and modelling notes.

| Item | Base value | Source / basis | Modelling note |
|---|---:|---|---|
| Existing PV capacity | 15 kWp | HouseZero dataset/report | Existing asset treated as sunk |
| Grid import tariff | $0.2512/kWh | EIA / external data | Massachusetts commercial electricity price |
| Solar export rate | $0.2512/kWh | Base-case assumption | Set equal to import tariff |
| PV installed cost | $3,450/kWp | Cost assumption | Applied only to additional PV |
| Battery installed cost | $1,325/kWh | Cost assumption | Battery retrofit cost |
| O&M rate | 1.35% | Modelling assumption | Annual % of retrofit CAPEX |
| Discount rate | 6.0% | Modelling assumption | NPV discount rate |
| Electricity-price growth | 2.0% | Modelling assumption | Annual energy-value escalation |
| PV degradation | 0.5% | Technical assumption | Annual reduction in PV-related benefit |
| Battery replacement | Year 12 | Modelling assumption | Replacement timing |
| Replacement cost | 60% | Modelling assumption | % of original battery cost |
| Project life | 25 years | Modelling assumption | Financial appraisal horizon |

## Source-data note

Measured hourly data covers 1 June 2023 to 31 May 2024. The portfolio workbook contains the cached hourly dataset so reviewers can inspect the model without reconnecting to the original source location.

## Interpretation note

The assumptions sheet distinguishes sourced values from explicit modelling assumptions. This is important because battery economics are particularly sensitive to export compensation, installed battery cost, degradation, replacement cost and the discount rate.