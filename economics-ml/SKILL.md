# Economics ML Skill

Use this skill for macroeconomic nowcasting, central-bank policy diagnostics,
economics-oriented ML calibration, and validation reports.

## Interface

Treat this as an agent skill first. A runtime installation should include this
file, `requirements.txt`, `main.py`, `backtest_engine.py`, and `src/`. Use the
bundled Python scripts when the user asks for a live run, fresh backtest,
regenerated dashboard snapshot, or reproducible artifact. For interpretive
questions, answer from the latest available report, snapshot, user-supplied
numbers, or cited public data.

## Operating Principles

- Do not expose private keys, local machine identifiers, personal names, or
  unpublished private data in generated reports or dashboard text.
- Keep the structural economics model as the primary estimate.
- Use ML as an auxiliary calibration, measurement, nuisance-estimation,
  heterogeneity, or validation layer.
- Do not describe ML calibration as the main forecast.
- Keep causal language conservative. Separate measurement, prediction,
  association, identification, and policy evaluation.
- Treat boundary and discontinuity designs as nonparametric econometrics unless
  a specific ML method is actually used.

## Default Agent Behavior

When answering a user request, produce an economist-style readout rather than a
raw script result. Include:

- Forecast or policy target period.
- Data-through date and release-lag assumptions.
- Sources used and sources missing.
- Structural baseline result.
- Data-enhanced result when available, shown separately.
- Driven-factor decomposition.
- Directional interpretation of the largest positive and negative factors.
- Backtest window, observations, R2/RMSE where available.
- Leakage and overfit checks.
- Limitation note for revised-data, pseudo-real-time, or non-causal results.

## Non-Script Analysis Mode

Use this mode when the user asks what the results mean, why a country changed,
whether an enhancement is credible, or which factors are driving a forecast.
Do not simply tell the user to run a command.

Process:

- Start from the latest available report, dashboard snapshot, or values supplied
  by the user.
- Identify the baseline model result before discussing the enhanced result.
- Attribute the enhanced result to observable factors and state the sign of each
  material factor.
- Explain whether the enhanced layer changes the policy or forecast
  interpretation.
- Separate evidence from inference. Use cautious language when the data are
  revised, sparse, or pseudo-real-time.
- State what additional data would be needed before making a stronger claim.

Output should be concise but diagnostic:

```text
Bottom line:
Baseline signal:
Data-enhanced signal:
Main driven factors:
Validation check:
Interpretation:
What not to conclude:
```

## Supported Analysis Layers

1. Measurement layer: convert text, news, disclosures, patents, images, audio,
   web traces, and other raw inputs into structured variables.
2. Nuisance-function estimation: estimate selection probabilities, propensity
   scores, conditional expectations, control functions, or counterfactual
   outcomes.
3. Causal and policy evaluation: DID, DML, causal forests, QTE, policy
   heterogeneity, and targeting rules.
4. Structural and dynamic models: value functions, policy functions, state
   distributions, and equilibrium objects.
5. Interpretable multimodal prediction: use graph, time-series, text, audio, or
   video signals only when the prediction remains auditable.
6. Domain-specific economics: climate and energy, finance, labor automation,
   innovation, disclosure, platform governance, and supply chains.
7. Validation and auditing: construct validity, annotator reliability, leakage
   checks, calibration, and external validity.
8. Boundary and nonparametric caution: do not relabel identification designs as
   ML when the core contribution is econometric.

## Report Templates

### GDP Nowcast

Use this structure:

```text
Target period:
Data through:
Baseline bridge nowcast:
ML auxiliary calibration:
Final calibrated nowcast:
Driven factors:
- Activity:
- Labor:
- Prices:
- Financial conditions:
- External demand:
Validation:
Limitations:
```

Rules:

- State that ML is auxiliary calibration, not the main predictor.
- Report US and Canada separately when both are available.
- Do not compare calibrated and baseline results without the same validation
  window.
- Mention release-lag filtering when monthly data are used for current-quarter
  evaluation.

### Policy Rate Diagnostics

Use this structure:

```text
Central bank:
Data through:
Current policy rate:
Base Taylor rate:
Data-Enhanced Taylor rate:
Gap versus actual:
Driven factors:
- Activity gap:
- Inflation pressure:
- Financial conditions:
- External pressure:
- Labor cooling:
Policy interpretation:
Validation and limitations:
```

Rules:

- Base Taylor is the structural signal.
- Data-Enhanced Taylor is a learned historical residual adjustment.
- Do not tune parameters by hand to match official projections.
- Explain whether the enhancement moves the estimate closer to or farther from
  the current policy rate.
- Treat the result as a diagnostic, not a mechanical recommendation.

### Backtest Review

Use this structure:

```text
Window:
Observations:
Baseline R2 / RMSE:
ML-calibrated R2 / RMSE:
RMSE gain:
Leakage controls:
Residual risk:
```

Rules:

- Confirm that calibration uses only prior rows in rolling validation.
- Call out revised-data limitations.
- Do not report gains without baseline metrics.

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
- If live data are missing, report the missing source explicitly.
- Dashboard snapshot values should be generated from the Python workflow or
  clearly labeled as a static example.
