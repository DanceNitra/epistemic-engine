---
title: Epistemic Engine — Grounding, Bridges, Crucible & Calibration
name: epistemic-engine
description: |
  One unified epistemic quality engine distilled from 6,422 vault concepts, 303 cross-domain bridges,
  25+ Breaktruth publications, and the Grounding-Coupling Law.
  Given any claim, returns: grounding score, crucible status, nearest bridges, calibration verdict.
  gstack for truth — not workflow, but epistemology.
domain: software-development
triggers:
  - epistemic engine
  - grounding coupling law
  - claim verifier
  - crucible test
  - bridge finder
  - epistemic label
  - percolation check
  - anti calibration
---

# Epistemic Engine

One tool to evaluate any claim against the vault's empirical epistemology.

**Author:** Rastislav Drahoš — epistemology engineer, vault architect, CSRD Comply founder

## Quick Start

```bash
cd ~/.hermes/skills/epistemic-engine
# Use the wrapper (auto-detects .venv for scikit-learn)
./epistemic claim "LLM confidence predicts accuracy"
# Or directly (zero deps, word-overlap fallback):
python engine.py claim "Phase transitions occur at 72% criticality"
```

## All Commands (engine.py)

| Command | What it does |
|---|---|
| `claim "..."` | Evaluate any claim — Crucible status, grounding score, nearest bridges, domain percolation |
| `bridge A B` | Find structural isomorphism connecting two domains |
| `label "..."` | Full epistemic verdict (grounding + calibration + bridges + phase) |
| `percolation "..."` | Check domain phase + criticality % |
| `bridges "..."` | List all bridges for a domain |
| `status` | Full engine dashboard |
| `sync-vault [--vault-path PATH]` | Live read from an Obsidian vault (6k+ concepts, bridges, percolation) |
| `report [--json] [--html FILE]` | Generate full report (CI/CD-ready JSON or standalone HTML) |
| `claim --json "..."` | JSON output for pipelines |
| `list-bridges` | Dump all bridges |

## Architecture

The engine wraps five detectors from the vault into one call:

```
                   ┌── CLAIM ──┐
                        │
            ┌───────────┼───────────┐
            │           │           │
       CRUCIBLE    GROUNDING    BRIDGE
       MATCHER     SCORER       FINDER
            │           │           │
            └───────────┼───────────┘
                        │
                  PERCOLATION
                    GAUGE
                        │
                  CALIBRATION
                     SCORE
```

## Matching Engine

- **TF-IDF (scikit-learn)** when scikit-learn is available in .venv — cosine similarity on n-gram vectors
- **Word-overlap (Jaccard)** fallback — zero dependencies
- Auto-detected at runtime, no config needed

## What We Know (Empirically Verified)

### Grounding-Coupling Law

**Self-consistency is not truth; only external grounding couples them.**

A system builds confidence from internal consistency (consensus or precision). That confidence tracks accuracy only in proportion to its external-grounding coupling `g`. As `g` falls, confidence and accuracy decouple: an overconfidence gap opens, pumped by internal effort rather than by truth.

| g | TEMPORAL gap (conf−acc) | STRUCTURAL gap |
|---|---|---|
| 1.0 | +0.00 (calibrated) | −0.05 (calibrated) |
| 0.4 | +0.00 | +0.95 |
| 0.05 | **+0.77** (conf 0.96 / acc 0.19) | **+0.95** (conf 0.95 / acc 0.00) |

**Parameters:** g=0.4 · r(confidence, accuracy)=0.25 · n=303 studies

**Implication:** Certainty is cheap and internal; truth is expensive and external.

### Crucible Results (15 claims tested)

| Claim | Status | n | Finding |
|---|---|---|---|
| LLM confidence predicts accuracy | **FAILED** | 47 | r=0.15–0.36; weak positive, not predictive |
| Dunning-Kruger affects LLMs | **FAILED** | 12 | LLMs do not show the metacognitive pattern |
| Hot-hand fallacy exists in LLMs | **FAILED** | 8 | No sequential bias |
| Model collapse degrades performance | **PASSED** | 6 | Training on own output causes degradation |
| Goodhart's law applies to metrics | **PASSED** | 5 | Metrics decay as optimization targets |
| Herding in multi-agent systems | **PASSED** | 4 | Agent crowds collapse to one member's competence |
| Finance IS Psychology | **PASSED** | 303 | Structural isomorphism via 303 bridges |
| Phase transitions at 72% criticality | **PASSED** | 8 | Consistent across health/finance/learning |
| Legal causation IS causal inference | **PASSED** | 6 | But-for test = Do-calculus |
| Attention IS an extractive industry | **PASSED** | 4 | Media structurally = mining |
| Corporation IS multi-agent system | **PASSED** | 5 | Governance = constitution design |
| CSF IS market microstructure | **PASSED** | 3 | Sleep clearance = drawdown clearance |
| Bloom's 2-sigma solved by LLMs | **FAILED** | 3 | Tutoring exists, far from 2-sigma |
| LLMs are conservative Bayesians | **FAILED** | 5 | Overconfident with weak evidence |
| Attention × Earth Systems percolation | **PASSED** | 3 | Cascades match regime shifts |

### Bridges (12 verified structural isomorphisms)

| Domain A | ↔ | Domain B | Mechanism | Falsifier |
|---|---|---|---|---|
| Finance | ↔ | Psychology | Market behavior = cognitive biases | Show a market without behavioral patterns |
| Software Eng | ↔ | Cell Biology | Code evolution = cellular processes | Code without selection pressure |
| Causal Inference | ↔ | Law | Do-calculus = legal causation | Law without counterfactuals |
| CSF | ↔ | Market Micro | Sleep clearance = drawdown clearance | Markets better without drawdowns |
| Immune System | ↔ | Epistemology | Self/non-self = falsification | Immune without self/non-self |
| Attention | ↔ | Extractive Ind. | Media = mining | Attention without depletion |
| Power Grid | ↔ | Brain | Blackouts = seizures (percolation) | Grid that cannot blackout |
| Percolation | ↔ | Cancer | Mutation threshold = percolation | Cancer without critical threshold |
| Percolation | ↔ | Learning | Learning = phase transitions | Learning without transitions |
| Vault | ↔ | Self | Knowledge structure = cognitive | Vault not reflecting creator |
| Control Theory | ↔ | Universal | Feedback loops everywhere | Domain without feedback loops |
| Corporation | ↔ | Multi-Agent | Governance = alignment | Corp without principal-agent problems |

### Domain Percolation Phases

| Domain | Phase | Criticality |
|---|---|---|
| AI Safety | 🔥 Crisis | 83% |
| Complexity | ⚠️ Tension | 62% |
| Finance | ⚠️ Tension | 55% |
| Learning | ✨ New Paradigm | 35% |
| Physics | ✨ New Paradigm | 30% |
| Economics | 📘 Stable | 21% |
| Psychology | 📘 Stable | 18% |
| Social | 📘 Stable | 15% |
| Cognition | 📘 Stable | 12% |
| Neuroscience | 📘 Stable | 9% |
| Knowledge | 📘 Stable | 8% |

## Files

- `engine.py` — Standalone CLI tool, 861 lines, pure Python, zero external dependencies
- `SKILL.md` — This document
- `epistemic` — Shell wrapper (auto-detects .venv for scikit-learn TF-IDF)
- `docs/index.html` — Landing page (GitHub Pages)
- `references/` — Validation docs, ideation methodology

## GitHub & Distribution

**repo:** `https://github.com/DanceNitra/epistemic-engine`
**Pages:** `https://dancenitra.github.io/epistemic-engine/`
**License:** MIT — fork, use, build upon

```bash
git clone https://github.com/DanceNitra/epistemic-engine.git
cd epistemic-engine
python engine.py claim "Phase transitions occur at 72% criticality"
```

## Known Limitations

1. **Static knowledge base** — crucible/bridge DB shipped with engine, updated manually.
2. **No real causal inference** — grounding scoring uses TF-IDF + heuristics.
3. **Percolation phases are engine snapshots** — live Agora PercolationEngine integration planned.
4. **TF-IDF requires scikit-learn** — auto-falls back to word overlap when unavailable.

## References

- Breaktruth #8-25 (Publications)
- Grounding-Coupling Law (Agora Lab 641d95)
- Bridges #53-#303 (Vault Bridge series)
- Why_X_Is_Y series (30+ structural isomorphism proofs)
- Percolation & Criticality — Threshold Phenomena Across Domains
- Cognoscope — Agent Senescence Detection
- Bridge Pattern Language
- Crucible Ledgers (24+ tested claims)
- The Learning Percolation Model
- `references/gstack-comparison-and-external-validation.md` — Vault claims vs published literature
- `references/vault-ideation-methodology.md` — Ideation methodology

## License

MIT — the data is free; the tool is free.