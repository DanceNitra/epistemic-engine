# Vault vs External World: Comparison Methodology

From session 2026-06-16/17 — validated that the vault's claims are largely
unpublished. Methodology for future vault-vs-world audits.

## Process That Worked

1. **Extract vault claims** — find the strongest, most unique claims
   (Grounding-Coupling Law, Anti-calibration r=0.15-0.36, Structural Isomorphisms,
   Percolation 72% threshold, Crucible/Replication Ledger)

2. **Search external** — delegate_task with toolsets=["web"], one task per claim.
   Search published literature, arXiv, industry reports.

3. **Compare** — for each claim, ask: (a) Does it exist in published form?
   (b) If so, what's different? (c) What's the gap?

4. **Report table** — | Claim | Published? | Key Difference |

## Key Findings (June 2026)

| Vault Claim | Published? | Key Difference |
|---|---|---|
| Grounding-Coupling Law (g parameter) | ❌ NO — fully novel | Formal mathematical law with `g` not found in literature |
| Anti-calibration (r=0.15-0.36) | ⚠️ Partially — poor calibration known | Vault calls it "anti-calibration" vs published "miscalibration" |
| Structural Isomorphisms (303 Bridges) | ⚠️ Partially — analogy theory exists | Vault claims literal identity ("IS"), lit treats as partial mapping |
| Percolation 72% universal threshold | ⚠️ Partially — percolation known | No published source supports 72% as universal; thresholds vary by topology |
| Replication Ledger / Crucible | ⚠️ Partially — replication efforts exist | "FAILED" framing is stronger than papers' "weak correlation" |

## gstack Comparison

Garry Tan's gstack (97K GitHub stars) = 47 skills about *how to build software*.
Epistemic Engine = skills about *what is true*. Complementary, not competing.

| gstack skill | What it does | Epistemic Engine equivalent |
|---|---|---|
| /review | Pre-landing code review | /crucible — which claims are true/false |
| /qa | Browser testing | /ground — how grounded is this claim |
| /cso | Security audit | /percolation — is this domain in crisis |
| /ship | Release pipeline | /calibrate — how calibrated is this output |
| /office-hours | YC forcing questions | /label — epistemic metadata for any text |

## When to Run This

- When user asks "what does the outside world know about X?"
- When validating whether vault IP is novel before publication
- After a wave of concept creation — scan for uniqueness

## Known Limitations

- Google CAPTCHA blocks headless browsers — use curl + DuckDuckGo Lite as fallback
- Academic paywalls limit paper access — focus on arXiv/open-access
- LLM-as-subagent may misrepresent findings — always require specific citations