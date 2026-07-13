# Economics ML Skill

Use this skill for domain-constrained macroeconomic analysis, GDP nowcasting,
central-bank policy diagnostics, and economics-oriented ML/causal evaluation.

## Operating Principles

- Do not expose private keys, local machine identifiers, personal names, or
  unpublished private data in generated reports or dashboard text.
- Use ML only where it adds measurement, nuisance estimation, heterogeneity
  analysis, validation, or interpretable signal extraction.
- When ML is used in the GDP workflow, describe it as bounded auxiliary
  calibration. The bridge model remains the main predictor.
- Keep causal language conservative. Separate measurement, prediction,
  association, identification, and policy evaluation.
- Treat boundary and discontinuity designs as nonparametric econometrics unless
  a specific ML method is actually used.

## Supported Layers

1. Measurement layer: convert text, news, disclosures, patents, images, audio,
   web traces, and other unstructured inputs into structured variables.
2. Nuisance-function estimation: estimate selection probabilities, propensity
   scores, conditional expectations, control functions, or counterfactual
   outcomes.
3. Causal and policy evaluation: DID, DML, causal forests, QTE, policy
   heterogeneity, and targeting rules.
4. Structural and dynamic models: value functions, policy functions, state
   distributions, and equilibrium objects.
5. Interpretable multimodal prediction: use graph, time-series, text, audio, or
   video signals only when predictions remain auditable.
6. Domain-specific economics: climate and energy, finance, labor automation,
   innovation, disclosure, platform governance, and supply chains.
7. Validation and auditing: construct validity, annotator/judge reliability,
   leakage checks, calibration, and external validity.
8. Boundary and nonparametric caution: do not relabel identification designs as
   ML when the core contribution is econometric.

## Commands

Install:

```bash
pip install -r requirements.txt
```

Run policy diagnostics:

```bash
python main.py policy --country US
python main.py policy --country Canada
```

Run GDP nowcast:

```bash
python main.py gdp --country US
python main.py gdp --country Canada
```

Run backtest:

```bash
python backtest_engine.py
```

## Data Requirements

- Set `FRED_API_KEY` in the environment before running live data workflows.
- If live data are missing, report the missing source explicitly instead of
  silently falling back to stale values.
- Dashboard snapshot values should be generated from the Python workflow or
  clearly labeled as a static example.

## Output Contract

Every generated report should include:

- Data-through date.
- Data sources used.
- Model family and measurement layer.
- Structural baseline estimate.
- ML auxiliary calibration result when available, shown separately from the
  structural baseline.
- Canada retail sales should be treated as an auxiliary calibration feature
  unless validation supports using it in the structural bridge model.
- Backtests should use release-lag-aware as-of dates when evaluating current
  quarter signals.
- Validation or uncertainty statement.
- A limitation note when the result is pseudo-real-time, revised-data based, or
  not causally identified.
