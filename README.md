# Loan Performance Intelligence Engine — "The Observatory"

> **Intain Campus FinTech Challenge 2026 — AI Track**
> An ML-first loan performance system: profiling, prediction, survival modeling, anomaly detection, scenario simulation, explainability, and a grounded LLM reviewer copilot — with a live 3D dashboard.

## At a Glance

| | |
|---|---|
| Dataset | 15,000 synthetic loans, 54-month panel, ~576K performance rows |
| Data Quality Score | 86.7 / 100 (realistic, intentionally imperfect data — see below) |
| Prediction models | 4 binary + 1 multiclass, LightGBM (calibrated) vs. Logistic Regression baseline |
| Best test AUC | 0.79 (12-month default prediction) |
| Survival model | Cox PH, concordance 0.64 |
| Anomaly detection | IsolationForest + Autoencoder ensemble, 25 curated reviewer examples |
| LLM Copilot | Groq `openai/gpt-oss-120b`, RAG-grounded, fully audit-logged |
| Submission file | 14,890 rows × 13 columns, matches required template exactly |

---

## What Makes This Stand Out

- **Non-LLM ML core, LLM-explained layer** — every probability, hazard rate, and anomaly score comes from a trained statistical/ML model. The LLM only explains results in plain English and is explicitly barred from making the risk call (every answer is labeled *"RECOMMENDATION — NOT A DECISION"*).
- **3D Risk Terrain** — an interactive mesh where height/color encode predicted default risk across credit-band × vintage; dragging the scenario slider live-morphs the terrain from Base to Adverse Credit in real time.
- **Audited Prompt / Trust Ledger** — every Copilot call is logged with its prompt, grounding source, model, and a human-review verdict (accepted / edited / rejected), including real examples where the LLM was caught being vague or overconfident and corrected.
- **"The Observatory" design system** — a custom brass/ink/paper visual identity (Fraunces + Inter + JetBrains Mono), built deliberately to avoid the generic dark-mode SaaS template look.

---

## What This Project Does

Given messy, loan-level panel data, this system answers one core question for a portfolio reviewer:

**"Which loans should I worry about, why, and what happens if the economy gets worse?"**

It does this using **real trained ML models** for every prediction (not an LLM wrapper), with an AI copilot layered on top purely to *explain* findings in plain English — never to make the actual risk decision.

---

## Dataset

**We used a fully synthetic dataset, not a real-world dataset.** No Fannie Mae, Freddie Mac, or HMDA data was used or downloaded. Per the challenge's own instructions (Section 5 of the problem statement), the organizer was expected to provide a curated synthetic or preprocessed dataset so participants wouldn't need to register with external data portals or learn raw mortgage-performance schemas during the hackathon. Since no organizer-provided data pack was supplied, we generated our own — this is explicitly allowed and expected by the challenge.

`scripts/01_generate_synthetic_data.py` produces the entire dataset from scratch, styled after the field structure of real public loan-performance sources:

- 15,000 unique synthetic loans with correlated origination attributes (credit score band, LTV, DTI, state, loan purpose, occupancy, property type)
- A 54-month monthly performance panel (~576K rows) with realistic hazard-driven state transitions (Current → 30/60/90 DPD → Default / Prepaid / Closed)
- Deliberately injected data-quality issues — missing values (MCAR + MNAR), invalid dates, outlier balances, cross-field contradictions — required so Task 1's profiling engine has real problems to detect
- Full supporting data pack: static attributes, monthly performance (train/test, time-split), a second-source servicer feed with intentional conflicts, a data dictionary, deterministic validation rules, macro scenario assumptions, and the submission template

**Why synthetic, not real data:** it lets the project demonstrate every required capability (profiling, leakage-safe splits, rare-event modeling, anomaly detection, scenario stress-testing) without any licensing, privacy, or data-access constraints — while still mirroring the structure and challenges of real mortgage-performance data.

---

## What Output Does the AI Engine Produce?

The system's job is to turn raw loan records into decision-ready intelligence for a portfolio reviewer. Concretely, for every loan, the engine outputs:

| Output | What It Tells You | Produced By |
|---|---|---|
| **Delinquency probability** (3-month, 6-month) | Likelihood the loan becomes past-due soon | Calibrated LightGBM |
| **Default probability** (12-month) | Likelihood the loan defaults within a year | Calibrated LightGBM |
| **Prepayment probability** (12-month) | Likelihood the loan is paid off early | Calibrated LightGBM |
| **Predicted next state** | Most likely status next month (Current, 30DPD, Default, Prepaid, etc.) | LightGBM multiclass |
| **Survival curve / hazard estimate** | How default risk evolves over the loan's life | Cox Proportional Hazards |
| **State transition matrix** | Probability of moving between any two loan statuses month-to-month | Markov transition model |
| **Anomaly score (0–1)** | How unusual/suspicious a record looks | IsolationForest + Autoencoder ensemble |
| **Exception type** | What specifically is wrong (missing doc, balance mismatch, stale record, etc.) | Multiclass exception classifier |
| **Top SHAP drivers** | Which specific factors are pushing a loan's risk up or down, and by how much | SHAP (global + per-loan local explanations) |
| **Scenario projections** | How delinquency/default/prepayment rates shift under Base, Adverse Credit, and High Prepayment macro scenarios | Monte Carlo simulation over the transition matrix |
| **Grounded reviewer note** | A plain-English explanation of a loan's risk, citing only real retrieved data (never fabricated), always labeled "RECOMMENDATION — NOT A DECISION" | LLM Copilot (Groq `openai/gpt-oss-120b`) + RAG |

All of this is assembled per loan into the final **`submission.csv`** (14,890 rows × 13 columns), and is also served live through the FastAPI backend to power every tab of the dashboard.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data & ML | Python 3.11, pandas, scikit-learn, LightGBM, lifelines (Cox PH survival), SHAP, PyTorch (autoencoder), ChromaDB |
| Backend API | FastAPI, Uvicorn, Pydantic |
| LLM Copilot | Groq API (`openai/gpt-oss-120b`), OpenAI-compatible client, RAG grounding over data dictionary + validation rules |
| Frontend | React 18, TypeScript, Vite, TailwindCSS, react-three-fiber / drei (3D), Framer Motion, Recharts, Zustand |
| Design | "The Observatory" theme — ink/paper/brass palette, Fraunces + Inter + JetBrains Mono typography |

---

## Repository Structure

```
loan-intel-engine/
  scripts/              9 pipeline scripts (data generation -> submission)
  backend/
    app/
      main.py           FastAPI entrypoint, wires all routers
      routers/           predict, anomaly, scenario, explain, copilot, dev_log
      services/          model_service, rag_service, llm_client, scenario_engine
      artifacts/         trained models, SHAP values, scenario results (generated)
    tests/               pytest suite
  frontend/
    src/
      pages/             Landing, Overview, Data Intelligence, Prediction,
                         Survival & Hazards, Anomaly Triage, Stress Scenarios,
                         SHAP Explainability, AI Copilot, Dev Log
      components/3d/     RiskTerrain, LoanPassportCard3D, ScenarioSlider
  reports/               model_card.md, data_intelligence_report.md,
                         explainability_report.md, scenario_report.md,
                         ai_development_log.md, llm_prompt_log.jsonl
  data/                  raw + processed data (generated, not committed)
  submission.csv         final predictions
  requirements.txt
  .env.example
  docker-compose.yml
```

---

## How to Run

### 1. Install dependencies
```powershell
uv venv --python 3.11 .venv
.\.venv\Scripts\activate.ps1
uv pip install -r requirements.txt
```

### 2. Set your API key (optional — for the live LLM Copilot)
Copy `.env.example` to `.env` and add your Groq API key:
```env
GROQ_API_KEY=your_key_here
```
Get a free key at [console.groq.com](https://console.groq.com). Without a key, the Copilot automatically falls back to rule-based templated explanations — the app never crashes either way.

### 3. Run the full ML pipeline (data -> models -> reports)
```powershell
$env:PYTHONUTF8=1
python scripts/01_generate_synthetic_data.py
python scripts/02_profiling_report.py
python scripts/03_feature_engineering.py
python scripts/04_train_prediction_models.py
python scripts/05_train_survival_model.py
python scripts/06_train_anomaly_models.py
python scripts/07_run_scenarios.py
python scripts/08_generate_explainability_report.py
python scripts/09_build_submission.py
```

### 4. Start the backend
```powershell
uvicorn backend.app.main:app --reload --port 8000
```
API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Start the frontend
```powershell
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173)

### 6. Run tests
```powershell
pytest backend/tests/ -v
```

---

## Challenge Task -> Deliverable Map

| Task | Output |
|---|---|
| 1. Data Intelligence & Profiling | `reports/data_intelligence_report.md` — Data Quality Score: **86.7/100** |
| 2. Prediction Models | `reports/model_card.md` — calibrated LightGBM vs. Logistic Regression baseline for delinquency, default, prepayment, next-state |
| 3. Survival / Transition Modeling | Cox PH model (concordance 0.64) + Markov transition matrix |
| 4. Anomaly & Exception Detection | IsolationForest + Autoencoder ensemble, 25 reviewer-ready examples |
| 5. Scenario & Stress Simulation | `reports/scenario_report.md` — Base / Adverse Credit / High Prepayment, Monte Carlo |
| 6. Explainability | `reports/explainability_report.md` — global + local SHAP, FP/FN analysis |
| 7. LLM-Assisted Reviewer Copilot | Groq-powered, RAG-grounded, fully logged in `reports/llm_prompt_log.jsonl` |
| 8. Agentic Development Evidence | `reports/ai_development_log.md` |
| Submission | `submission.csv` — 14,890 rows x 13 columns |

---

## Dashboard Guide

| Tab | What It Shows |
|---|---|
| Landing | Project introduction |
| Overview | Portfolio KPIs + 3D Risk Terrain |
| Data Intelligence | Profiling, missingness, drift, DQ score |
| Prediction | Model comparison, calibration |
| Survival & Hazards | Survival curves, transition matrix |
| Anomaly Triage | Flagged loans with driver explanations |
| Stress Scenarios | Live scenario slider with 3D terrain morphing |
| SHAP Explainability | Global + per-loan feature drivers |
| AI Copilot | Grounded reviewer chat with full audit log |
| Dev Log | AI development transparency record |

---

## Known Limitations

- **`next_12m_prepayment_flag`** shows a validation-to-test AUC gap (0.79 -> 0.55). Likely cause: 12-month-ahead prepayment depends on the future interest-rate environment, which isn't in the current static/lagged feature set — a documented, domain-consistent limitation rather than a bug.
- Loan performance panels start from a fixed calendar date (Jan 2020) regardless of each loan's actual origination month — a simplification of the synthetic generator, not a data-quality defect in the deliverables.

---

## Non-Negotiables Enforced

1. All predictions come from trained non-LLM models (LightGBM, Cox PH, IsolationForest, Autoencoder) — the LLM only explains, never predicts.
2. Strict time-aware panel split (train <= month 24, val 25-30, test 31-42) — no row-level leakage.
3. No target leakage — forward-looking targets are isolated via explicit observability filtering.
4. Every Copilot interaction is logged with prompt, grounding source, model, and human review status, labeled "RECOMMENDATION — NOT A DECISION."

---

## Troubleshooting

- **`ERROR:chromadb.telemetry...capture() takes 1 positional argument`** on backend startup — harmless. This is ChromaDB's anonymous telemetry ping failing; it does not affect RAG indexing or app functionality.
- **PowerShell + `curl.exe` returns a `422`/JSON decode error** — PowerShell mangles single-quoted JSON. Use `Invoke-RestMethod` instead:
  ```powershell
  Invoke-RestMethod -Uri http://127.0.0.1:8000/copilot/ask -Method Post -ContentType "application/json" -Body '{"loan_id":"LN000000","question":"..."}'
  ```
- **`.env` changes not taking effect** — the backend reads `.env` only at startup. Restart `uvicorn` after editing it; `--reload` watches code files, not `.env`.
- **Groq model 404** — Groq periodically retires models. If `openai/gpt-oss-120b` stops working, check `GET https://api.groq.com/openai/v1/models` for current options and update `backend/app/services/llm_client.py`.

---

## Team & License

Built for the Intain Campus FinTech Challenge 2026, AI Track.
*(Duvvuru Vandita)*

