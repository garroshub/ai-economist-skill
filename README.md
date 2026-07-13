# Economics ML Skill

An installable agent skill for macroeconomic nowcasting, central-bank policy
diagnostics, and economist-style interpretation. The Python tools and dashboard
are bundled runtime utilities, not the primary interface.

<div align="center">
  <img src="assets/economics_ml_flow.svg" alt="Economics ML workflow" width="900" />
</div>

<br />

<div align="center">

[![Live Dashboard](https://img.shields.io/badge/View-Live_Dashboard-emerald?style=for-the-badge)](https://garroshub.github.io/ai-economist-skill/)
[![Discussions](https://img.shields.io/badge/Join-Discussions-0b5fff?style=for-the-badge)](https://github.com/garroshub/ai-economist-skill/discussions)

</div>

## What It Does

| Layer | Main Output | Role of ML |
| --- | --- | --- |
| GDP nowcast | Bridge-equation baseline by country and quarter | Bounded residual calibration, reported separately |
| Policy diagnostics | Base Taylor and Data-Enhanced Taylor readouts | Historical residual calibration against observable macro factors |
| Backtesting | Baseline vs calibrated OOS comparison | Prior-window calibration only, release-lag filtered |
| Agent report | Driven factors, data-through dates, validation notes | Structured interpretation, not a hidden predictor |

ML is not the primary forecaster. It is an auxiliary calibration and measurement
layer used to explain where the structural model may be missing information.

## Install As An Agent Skill

This repository is structured so the root folder can be installed as a skill:
`SKILL.md` is the skill entrypoint, while `src/`, `main.py`, `backtest_engine.py`,
and `dashboard/` are optional tools the agent may use when the user asks for live
data, reproducible runs, or dashboard output.

Install by cloning the repository into your Codex skills directory:

```bash
git clone https://github.com/garroshub/ai-economist-skill.git ~/.codex/skills/economics-ml
```

On Windows PowerShell:

```powershell
git clone https://github.com/garroshub/ai-economist-skill.git $env:USERPROFILE\.codex\skills\economics-ml
```

After installation, ask the agent for tasks such as:

```text
Use the Economics ML skill to explain the latest US and Canada GDP nowcast drivers.
Use the Economics ML skill to compare Base Taylor and Data-Enhanced Taylor signals.
Use the Economics ML skill to audit whether the backtest has forward-information leakage.
```

The skill should answer with target period, data-through date, baseline estimate,
data-enhanced estimate, driven factors, validation checks, and limitations. It
should not merely point the user to a Python command.

## Current Modules

### GDP Nowcasting

- Structural bridge model with SVD factor extraction.
- Ragged-edge filling for missing recent monthly observations.
- US high-frequency auxiliary variables: initial claims, housing, durable goods,
  real disposable income, financial conditions, and yield curve.
- Canada auxiliary variables: StatCan retail sales, CPI, CAD/USD, WTI oil, and
  US demand spillover measures.
- Baseline and ML-calibrated nowcasts shown side by side.

### Policy Rate Diagnostics

- Taylor 1993, Taylor 1999, and nonlinear inflation-response variants.
- Output-gap proxies from labor slack, HP-filtered GDP, and capacity utilization.
- Base Taylor result remains the main structural signal.
- Data-Enhanced Taylor result learns historical residual adjustments from
  activity, inflation pressure, financial conditions, external pressure, and
  labor cooling.
- Enhancement decomposition is reported in percentage-point contributions.

### Validation

- Expanding-window backtest for GDP nowcasts.
- Release-lag-aware pseudo-real-time feature filtering.
- Baseline R2/RMSE and ML-calibrated R2/RMSE shown on the same validation window.
- Revised-data limitation is disclosed rather than treated as a vintage-data test.

## Optional Runtime Tools

The skill can be used for analysis without running local scripts. Install the
runtime dependencies only when you want live data pulls, regenerated reports,
backtests, or local dashboard builds.

```bash
pip install -r requirements.txt
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

Build the dashboard:

```bash
cd dashboard
npm ci
npm run build
```

## Data Sources

- FRED API for macro indicators.
- BLS and Bank of Canada public data where available.
- Statistics Canada public CSV tables for retail-sales auxiliary features.
- Public news and outlook pages only when converted into structured measurement
  variables.

No private API key is stored in the repository. Set `FRED_API_KEY` locally before
running live workflows.

## Agent Output Contract

Reports should include the forecast target period, data-through date, source
coverage, structural baseline, calibrated result, driven-factor decomposition,
backtest window, leakage controls, and limitations. Causal claims require a
separate identification design.

## Repository Structure

```text
ai-economist-skill/
|-- SKILL.md
|-- README.md
|-- src/
|   |-- engine/
|   |   |-- policy_rate_engine.py
|   |   `-- gdp_nowcast_engine.py
|   |-- core/
|   |   |-- modeling_core.py
|   |   `-- visual_oracle.py
|   `-- data_utils/
|       |-- macro_data_fetcher.py
|       `-- statcan_fetcher.py
|-- dashboard/
|-- assets/
|-- backtest_engine.py
|-- main.py
`-- requirements.txt
```

For skill installation, `SKILL.md` is the required file. The Python, dashboard,
and tests are included because this repository also provides reproducible runtime
tools and a public live dashboard.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=garroshub/ai-economist-skill&type=Date)](https://www.star-history.com/#garroshub/ai-economist-skill&Date)
