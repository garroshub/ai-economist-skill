# Economics ML Skill

Domain-constrained tooling for macroeconomic measurement, GDP nowcasting,
central-bank policy diagnostics, and economics-oriented ML workflows.

<div align="center">
  <img src="assets/economics_ml_framework.png" alt="Economics ML framework" width="800" />
</div>

<br />

<div align="center">

[![Live Dashboard](https://img.shields.io/badge/View-Live_Dashboard-emerald?style=for-the-badge)](https://garroshub.github.io/ai-economist-skill/)
[![Discussions](https://img.shields.io/badge/Join-Discussions-0b5fff?style=for-the-badge)](https://github.com/garroshub/ai-economist-skill/discussions)

</div>

---

## Scope

This project treats machine learning as an economics support layer, not as an
unconstrained forecasting oracle. The core goal is to make macroeconomic
measurement, policy diagnostics, and validation more reproducible and
interpretable.

The framework is organized around:

- Measurement layer: text, news, disclosures, patents, images, audio, web traces,
  and other raw signals converted into structured variables.
- Nuisance-function estimation: propensity scores, conditional expectations,
  selection probabilities, control functions, and counterfactual outcomes.
- Causal and policy evaluation: DID, DML, causal forests, QTE, policy
  heterogeneity, and targeting.
- Structural and dynamic models: value functions, policy functions, state
  distributions, and equilibrium objects.
- Interpretable multimodal prediction: graph, time-series, text, image, audio,
  and video signals used only with auditable feature logic.
- Domain-specific economics: climate and energy, finance, labor automation,
  innovation, disclosure, platform governance, and supply chains.
- Validation and auditing: construct validity, annotator reliability, data
  leakage, calibration, and external validity.
- Boundary and nonparametric caution: discontinuity and boundary designs are
  treated as identification problems unless an ML method is actually used.

---

## Modules

### 1. Policy Rate Diagnostics

The policy module estimates model-implied rates for the Federal Reserve and the
Bank of Canada using Taylor-rule variants and multiple output-gap proxies.

Current components:

- Taylor 1993, Taylor 1999, and nonlinear inflation-response variants.
- Output-gap proxies from labor-market slack, HP-filtered GDP, and capacity
  utilization.
- Bayesian-style uncertainty framing for policy-rate deviations.
- Sensitivity charts across inflation and output-gap scenarios.

### 2. GDPCastNow

The GDP module builds a bridge-equation nowcast from high-frequency indicators.
The structural bridge model remains the main predictor. ML is used only as a
bounded auxiliary calibration layer, and its adjustment is reported separately
from the structural baseline.

Current components:

- SVD factor extraction from monthly macro indicators.
- AR(1) ragged-edge filling for missing recent observations.
- Measurement adjustment from newsflow and official outlook text.
- Ridge-based post-model calibration with a bounded adjustment, shown separately
  for the US and Canada.
- Mixed-frequency auxiliary calibration in backtests using quarterly summaries
  of monthly indicators.
- Official Statistics Canada retail sales data as a Canada-only auxiliary
  calibration feature.
- Canada-specific open-economy auxiliary indicators: CPI, CAD/USD, WTI oil, and
  US demand spillover measures.
- US-only high-frequency auxiliary indicators: initial claims, housing starts,
  durable goods, real disposable income, financial conditions, and yield curve.
- Release-lag-aware pseudo-real-time backtests using quarter start plus 105 days
  as the as-of date.
- Explicit runtime errors when required live FRED data are unavailable.

### 3. Backtest Engine

The backtest module evaluates the GDP nowcast with an expanding-window design.
The current design uses revised historical data, so results should be read as
pseudo-real-time validation rather than a true vintage-data backtest.

The secondary comparison is a rolling out-of-sample residual calibration. It
uses only prior backtest rows, and reports baseline versus ML-calibrated results
on the same validation window.

---

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Set a FRED API key for live data:

```bash
set FRED_API_KEY=your_key_here
```

Run GDP nowcasts:

```bash
python main.py gdp --country US
python main.py gdp --country Canada
```

Run policy diagnostics:

```bash
python main.py policy --country US
python main.py policy --country Canada
```

Run backtests:

```bash
python backtest_engine.py
```

Run the dashboard build:

```bash
cd dashboard
npm ci
npm run build
```

---

## Data Sources

- FRED API for macro indicators.
- BLS and Bank of Canada public pages where available.
- StatCan Daily pages for Canadian GDP outlook parsing.
- Public RSS/news feeds for measurement adjustments.

No private API key is stored in the repository. Set `FRED_API_KEY` in your local
environment before running live workflows.

---

## Validation Notes

- Backtest results use currently available revised data.
- Measurement adjustments are small structured signals, not standalone
  predictions.
- ML calibration is auxiliary and bounded; it does not replace the structural
  bridge model.
- Causal claims require a separate identification design.
- Dashboard snapshot values are static unless regenerated by the Python
  workflow.

---

## Repository Structure

```text
ai-economist-skill/
├── src/
│   ├── engine/
│   │   ├── policy_rate_engine.py
│   │   └── gdp_nowcast_engine.py
│   ├── core/
│   │   ├── modeling_core.py
│   │   └── visual_oracle.py
│   └── data_utils/
│       └── macro_data_fetcher.py
├── dashboard/
├── assets/
├── backtest_engine.py
├── main.py
├── requirements.txt
└── SKILL.md
```

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=garroshub/ai-economist-skill&type=Date)](https://www.star-history.com/#garroshub/ai-economist-skill&Date)
