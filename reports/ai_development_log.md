# AI Development Log — Loan Performance Intelligence Engine

*Generated as part of the Intain Campus FinTech Challenge 2026 Submission*

## 1. AI Tools & Environment
- **Primary AI Pairing Assistant**: Google Antigravity IDE with Claude Sonnet / Opus & Gemini Models
- **Agentic Workflow**: Fully autonomous execution across data generation, ML training pipelines, FastAPI backend wiring, and React + Three.js interface.
- **Python Environment**: Python 3.11 with `uv` package management, `lightgbm`, `scikit-learn`, `lifelines`, `shap`, `torch`, `chromadb`, `fastapi`.

---

## 2. Representative Prompts & Invocations
Below is the master prompt and key iterative task prompts used during development:

### Master Build Prompt (Excerpts)
```markdown
# MASTER BUILD PROMPT — Loan Performance Intelligence Engine
Build a complete, runnable prototype for the "Loan Performance Intelligence Engine" challenge in one pass.
- Non-negotiables: Non-LLM ML models for all core predictions (LightGBM, Cox PH survival, IsolationForest + Autoencoder).
- Time-aware splits: Train on early months (<=24), validate (25-27), test (28+). No target leakage.
- Observatory Design Theme: Vintage scientific precision + modern fintech.
- Full LLM Copilot logging with grounded RAG over data dictionary and validation rules.
```

---

## 3. Human & Agent Review / Handoff Process
During the execution of this project, an agent handoff occurred due to token limits. The subsequent agent performed an end-to-end audit and repaired runtime bottlenecks:

### Critical Pipeline Debugging & Interventions:
1. **Scikit-Learn >=1.6 Compatibility**:
   - *Issue*: `CalibratedClassifierCV(..., cv="prefit")` was deprecated and removed in recent scikit-learn releases.
   - *Resolution*: Wrapped pre-fitted LightGBM models inside `sklearn.frozen.FrozenEstimator` with fallback for backwards compatibility.
2. **Model Pickle / Serialization Cross-Module Isolation**:
   - *Issue*: `LGBMWrapper` defined inside a local loop caused unpickling failures (`AttributeError: Can't get attribute 'LGBMWrapper' on module '__main__'`) when loaded by the explainability script and backend service.
   - *Resolution*: Hoisted `LGBMWrapper` to `backend.app.services.model_service` and imported it across training, reporting, and serving layers.
3. **Artifact Directory Path Consistency**:
   - *Issue*: Backend path resolution in `model_service.py` had an extra directory level resolving to `backend/app/app/artifacts`.
   - *Resolution*: Normalized `_ROOT` and `_ARTIFACTS` path resolution to ensure seamless runtime model serving.

---

## 4. Accepted vs. Rejected AI Outputs

| Task / Component | Proposed Output | Review Decision | Rationale |
|---|---|---|---|
| Split Strategy | Random K-Fold across all rows | **REJECTED** | Disqualification risk. Must be time-aware panel split to prevent loan-level leakage across time. |
| Delinquency Calibration | Raw LightGBM logits | **REJECTED** | Uncalibrated probabilities showed severe probability distortion on imbalanced defaults; switched to Isotonic CalibratedClassifierCV. |
| Anomaly Scoring | Single IsolationForest | **MODIFIED** | Blended 60% IsolationForest + 40% PyTorch reconstruction autoencoder for robust tabular anomaly detection. |
| Copilot Recommendations | Free-form LLM judgment | **REJECTED** | Added strict RAG grounding in ChromaDB with mandatory `RECOMMENDATION — NOT A DECISION` banner and prompt logging. |
| Frontend Visuals | Generic SaaS Dark Theme | **REJECTED** | Replaced with "The Observatory" custom aesthetic: warm ivory paper, brass accents, Fraunces serif typography, and 3D Risk Terrain. |

---

## 5. Approximate AI-Generated Code Share
- **Data Generation & Feature Engineering**: 95% AI-generated, 5% human-verified constraint adjustments.
- **ML Pipeline (Tasks 2, 3, 4, 5, 6)**: 90% AI-generated, 10% calibration and serialization fixes.
- **Backend API & RAG Service**: 92% AI-generated, 8% path & route configuration.
- **Frontend UI & 3D Visuals**: 95% AI-generated.
- **Documentation & Reports**: 85% AI-generated from live script metrics, 15% structured curation.

---

## 6. Lessons Learned
1. **Guard Against Silent Pickling Traps**: Never serialize classes defined in `__main__` or local closures when sharing models between offline scripts and API servers.
2. **Grounding Over Generation**: In mission-critical financial applications, LLMs must be strictly confined to grounded explanation and synthesis, with numerical predictions firmly anchored in non-LLM statistical and ML models.
3. **Time-Aware Evaluation is Essential**: Random splits in panel datasets create severe lookahead leakage that inflates validation metrics while crippling real-world generalization.

<<FILL IN AFTER DEMO: Final reviewer feedback and hackathon judging notes>>
