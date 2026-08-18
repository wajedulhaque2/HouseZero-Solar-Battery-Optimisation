# Workbook Architecture

```text
HouseZero hourly source data
        |
        v
Power Query: q_Loads_Raw -> q_Loads_Clean
        |
        v
Hourly_Data table (8,784 observations)
        |
        +-----------------------------+
        |                             |
        v                             v
Model_Inputs                    Sources_Assumptions
        |                             |
        +-------------+---------------+
                      |
                      v
           Hourly battery dispatch
                      |
                      v
              Financial_Model
                      |
              +-------+-------+
              |               |
              v               v
      Scenario Analysis    Chart Support
              |               |
              +-------+-------+
                      |
                      v
                  Dashboard
```

## Worksheet roles

- `README` - start here and headline investment conclusion.
- `Dashboard` - selected retrofit and economics summary.
- `Model_Inputs` - system settings and energy KPIs.
- `Hourly_Data` - hourly demand/PV/dispatch engine.
- `Sources_Assumptions` - source register and base modelling assumptions.
- `Financial_Model` - 25-year incremental cash-flow appraisal.
- `Scenario Analysis` - two-variable NPV sensitivity and break-even analysis.
- `Methodology` - modelling approach and limitations.
- `Chart Support` - supporting PivotTables/aggregations for visuals.

The workbook is structured as an analytical model rather than a simple dashboard: source assumptions, operating logic, financial calculations and presentation outputs are kept in separate layers.