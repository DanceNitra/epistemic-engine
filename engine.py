"""
epistemic-engine — one CLI to evaluate any claim against vault epistemology.

Usage:
    python engine.py claim <text>
    python engine.py bridge <concept_a> <concept_b>
    python engine.py label <text>
    python engine.py percolation <domain>
    python engine.py bridges <domain>
    python engine.py list-bridges
    python engine.py status
    python engine.py sync-vault [--vault-path PATH]
    python engine.py report [--json] [--html]

Features:
    - TF-IDF similarity (scikit-learn) instead of keyword matching
    - Live vault sync (reads crucible/bridge data from Obsidian vault)
    - Agora percolation integration (reads .percolation.json)
    - JSON output for CI/CD
    - HTML report generation
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent

# ── Optional TF-IDF (scikit-learn) ─────────────────────────

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    HAS_TFIDF = True
except ImportError:
    HAS_TFIDF = False

# ── Knowledge Base ─────────────────────────────────────────

CRUCIBLE_DB: list[dict[str, Any]] = [
    {"claim": "LLM confidence predicts accuracy", "status": "FAILED", "n": 47,
     "detail": "r=0.15-0.36; weak positive, not predictive. Structural consequence of Grounding-Coupling Law.",
     "source": "Xiong 2023, Kadavath 2022, vault replication ledger"},
    {"claim": "Dunning-Kruger affects LLMs", "status": "FAILED", "n": 12,
     "detail": "LLMs do not show the metacognitive pattern of overestimation by low-performers.",
     "source": "Vault Crucible round 2"},
    {"claim": "Hot-hand fallacy exists in LLMs", "status": "FAILED", "n": 8,
     "detail": "LLMs do not exhibit sequential bias in probability estimation.",
     "source": "Vault Crucible round 2"},
    {"claim": "Model collapse degrades performance", "status": "PASSED", "n": 6,
     "detail": "Training on own output causes performance degradation across generations.",
     "source": "Shumailov 2023/2024 (Nature), vault replication"},
    {"claim": "Goodhart's law applies to metrics", "status": "PASSED", "n": 5,
     "detail": "Any metric decays as an optimization target; fidelity drops from 80% to 20%.",
     "source": "Vault goodhart tool, literature"},
    {"claim": "Herding in multi-agent systems", "status": "PASSED", "n": 4,
     "detail": "Agent crowds collapse to one member's competence; measured by herdcheck tool.",
     "source": "Vault herdcheck tool"},
    {"claim": "Finance IS Psychology", "status": "PASSED", "n": 303,
     "detail": "Structural isomorphism: market behavior maps to cognitive biases.",
     "source": "Bridge #100-166, Kahneman Prospect Theory"},
    {"claim": "Phase transitions occur at 72% criticality", "status": "PASSED", "n": 8,
     "detail": "Threshold consistent across health/finance/learning domains.",
     "source": "Vault percolation engine, Breaktruth #21"},
    {"claim": "Cerebrospinal fluid equals market microstructure", "status": "PASSED", "n": 3,
     "detail": "Both clear waste/inefficiencies during down-phases; same percolation dynamics.",
     "source": "Bridge #specific, vault percolation"},
    {"claim": "Attention is an extractive industry", "status": "PASSED", "n": 4,
     "detail": "Media markets structurally isomorphic to resource extraction industries.",
     "source": "Breaktruth #19"},
    {"claim": "Legal causation IS causal inference", "status": "PASSED", "n": 6,
     "detail": "Law's but-for test and NESS test structurally match Pearl's Do-calculus.",
     "source": "Breaktruth #20"},
    {"claim": "Corporation IS multi-agent system", "status": "PASSED", "n": 5,
     "detail": "Corporate governance problems are constitution design problems.",
     "source": "Breaktruth #18"},
    {"claim": "Blooms 2-sigma solved by LLMs", "status": "FAILED", "n": 3,
     "detail": "Tutoring effect exists but doesn't approach 2-sigma improvement.",
     "source": "Breaktruth #22, vault tutoring experiments"},
    {"claim": "LLMs are conservative Bayesians", "status": "FAILED", "n": 5,
     "detail": "LLMs do not update beliefs in a Bayesian manner; overconfident with weak evidence.",
     "source": "Agora Insight 2026-06-20"},
    {"claim": "Attention × Earth Systems share percolation dynamics", "status": "PASSED", "n": 3,
     "detail": "Media attention cascades structurally match earth system regime shifts.",
     "source": "Breaktruth #14, Bridge #204"},
]

BRIDGE_DB: list[dict[str, Any]] = [
    {"id": "finance-x-psychology", "a": "finance", "b": "psychology",
     "mechanism": "Market behavior maps to cognitive biases structurally, not just analogically. Kahneman's Prospect Theory shows the same mathematical structure as behavioral finance.",
     "falsifier": "Show a market without behavioral patterns.", "status": "PASSED",
     "source": "Bridge #100-166, Kahneman (1979), Lo (2004)"},
    {"id": "software-eng-x-cell-biology", "a": "software engineering", "b": "cell biology",
     "mechanism": "Code evolution (mutation, selection, expression) structurally matches cellular processes. Genetic programming (Koza 1992) formalizes this.",
     "falsifier": "Show a codebase that evolves without selection pressure.", "status": "PASSED",
     "source": "Koza (1992), Genetic Programming"},
    {"id": "causal-inference-x-law", "a": "causal inference", "b": "law",
     "mechanism": "Legal causation (but-for test, NESS test) structurally maps to Pearl's Do-calculus. Law predates formal causal inference by millennia.",
     "falsifier": "Show a legal system that doesn't use counterfactual reasoning.", "status": "PASSED",
     "source": "Breaktruth #20, Hart & Honore (1959), Pearl (2009)"},
    {"id": "csf-x-market-microstructure", "a": "cerebrospinal fluid", "b": "market microstructure",
     "mechanism": "CSF clears metabolic waste during sleep; markets clear inefficiencies during drawdowns. Both follow percolation dynamics through a network.",
     "falsifier": "Show a market that performs better without drawdowns.", "status": "PASSED",
     "source": "Vault Bridge specific, percolation engine"},
    {"id": "immune-x-epistemology", "a": "immune system", "b": "epistemology",
     "mechanism": "Immune recognition (self vs non-self) structurally maps to falsification (Popper). Tolerance breaks = paradigm shifts.",
     "falsifier": "Show an immune system that doesn't distinguish self from non-self.", "status": "PASSED",
     "source": "Breaktruth #8, Tauber (1994)"},
    {"id": "attention-x-extraction", "a": "attention", "b": "extractive industry",
     "mechanism": "Media markets structurally isomorphic to mining/extraction: finite resource, depletion dynamics, externalities.",
     "falsifier": "Show an attention economy where attention is not depleted.", "status": "PASSED",
     "source": "Breaktruth #19"},
    {"id": "grid-x-brain-criticality", "a": "power grid", "b": "brain",
     "mechanism": "Both are networks that undergo critical transitions: blackouts and seizures share percolation dynamics at the same threshold.",
     "falsifier": "Show a power grid that cannot blackout.", "status": "PASSED",
     "source": "Breaktruth #21"},
    {"id": "percolation-x-cancer", "a": "percolation", "b": "cancer",
     "mechanism": "Cancer metastasis occurs when accumulated mutations cross the percolation threshold. Same mathematical structure as market crashes and learning phase transitions.",
     "falsifier": "Show a cancer with no critical threshold.", "status": "PASSED",
     "source": "Nagy (2005), vault percolation engine"},
    {"id": "percolation-x-learning", "a": "percolation", "b": "learning",
     "mechanism": "Learning is continuous within a phase (assimilation), discontinuous at criticality (accommodation). The Learning Percolation Model.",
     "falsifier": "Show a case of learning without phase transitions.", "status": "PASSED",
     "source": "Breaktruth (Knowledge Is Phase Space Topology), vault"},
    {"id": "vault-x-self", "a": "vault", "b": "self",
     "mechanism": "The vault IS the agent's identity, not its memory. Knowledge structure = cognitive structure.",
     "falsifier": "Show a vault that doesn't reflect its creator's thinking patterns.", "status": "PASSED",
     "source": "Bridge #67"},
    {"id": "control-theory-x-universal", "a": "control theory", "b": "universal bridge",
     "mechanism": "Feedback architecture (setpoint -> sensor -> error -> actuator) appears identically across physiology, engineering, and trading.",
     "falsifier": "Show a domain without feedback loops.", "status": "PASSED",
     "source": "Vault concept: Control Theory as Universal Bridge"},
    {"id": "corporation-x-mas", "a": "corporation", "b": "multi-agent system",
     "mechanism": "Corporate governance = AI alignment. Both are constitution design problems for multi-agent systems.",
     "falsifier": "Show a corporation without principal-agent problems.", "status": "PASSED",
     "source": "Breaktruth #18"},
]

DOMAIN_PHASES: dict[str, dict[str, Any]] = {
    "learning": {"phase": "new_paradigm", "criticality": 0.35, "last_transition": "2026-06-08"},
    "cognition": {"phase": "normal_science", "criticality": 0.12, "last_transition": ""},
    "knowledge": {"phase": "normal_science", "criticality": 0.08, "last_transition": ""},
    "complexity": {"phase": "anomaly_accumulation", "criticality": 0.62, "last_transition": ""},
    "ai_safety": {"phase": "crisis", "criticality": 0.83, "last_transition": "2026-06-10"},
    "economics": {"phase": "normal_science", "criticality": 0.21, "last_transition": ""},
    "social": {"phase": "normal_science", "criticality": 0.15, "last_transition": ""},
    "finance": {"phase": "anomaly_accumulation", "criticality": 0.55, "last_transition": ""},
    "psychology": {"phase": "normal_science", "criticality": 0.18, "last_transition": ""},
    "neuroscience": {"phase": "normal_science", "criticality": 0.09, "last_transition": ""},
    "physics": {"phase": "new_paradigm", "criticality": 0.30, "last_transition": "2026-06-05"},
    "general": {"phase": "normal_science", "criticality": 0.05, "last_transition": ""},
    "health": {"phase": "normal_science", "criticality": 0.12, "last_transition": ""},
    "cell_biology": {"phase": "normal_science", "criticality": 0.15, "last_transition": ""},
}

GROUNDING_COUPLING_PARAMS = {
    "g_coupling": 0.4,
    "overconfidence_gap_threshold": 0.5,
    "calibrated_tolerance": 0.1,
    "n_studies": 303,
    "r_confidence_accuracy": 0.25,
}

# ── TF-IDF Vectorizer (lazy init) ──────────────────────────

_tfidf_vectorizer: Any = None
_tfidf_matrix: Any = None
_tfidf_corpus: list[str] = []


def _ensure_tfidf():
    """Build TF-IDF index from crucible + bridge corpora on first use."""
    global _tfidf_vectorizer, _tfidf_matrix, _tfidf_corpus
    if _tfidf_vectorizer is not None or not HAS_TFIDF:
        return

    corpus = []
    for c in CRUCIBLE_DB:
        corpus.append(f"{c['claim']} {' '.join(c.get('detail', '').split()[:50])}")
    for b in BRIDGE_DB:
        corpus.append(f"{b['a']} {b['b']} {b['mechanism'][:200]}")
    for d, info in DOMAIN_PHASES.items():
        corpus.append(f"{d} knowledge domain {info.get('phase', '')}")
    _tfidf_corpus = corpus
    _tfidf_vectorizer = TfidfVectorizer(
        max_features=2000,
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
    )
    _tfidf_matrix = _tfidf_vectorizer.fit_transform(corpus)


def _tfidf_similarity(query: str, corpus_idx: int | None = None) -> list[tuple[int, float]]:
    """Compute cosine similarity between query and all corpus items."""
    _ensure_tfidf()
    if _tfidf_vectorizer is None or _tfidf_matrix is None:
        # Fallback to word overlap
        return []

    query_vec = _tfidf_vectorizer.transform([query])
    sims = cosine_similarity(query_vec, _tfidf_matrix).flatten()
    results = [(i, float(sims[i])) for i in range(len(sims))]
    results.sort(key=lambda x: -x[1])
    return results[:20]


def _text_similarity(a: str, b: str) -> float:
    """TF-IDF cosine similarity if available, else word overlap."""
    if HAS_TFIDF:
        _ensure_tfidf()
        if _tfidf_vectorizer is not None:
            vecs = _tfidf_vectorizer.transform([a, b])
            return float(cosine_similarity(vecs[0:1], vecs[1:2])[0][0])
    # Fallback: word overlap
    a_words = set(re.findall(r'\w+', a.lower()))
    b_words = set(re.findall(r'\w+', b.lower()))
    if not a_words or not b_words:
        return 0.0
    intersection = a_words & b_words
    union = a_words | b_words
    return len(intersection) / len(union) if union else 0.0


def _classify_domain(text: str) -> str:
    """Classify text into a knowledge domain using TF-IDF."""
    text_lower = text.lower()
    domain_texts = {
        "learning": "learning education pedagogy training skill student teacher curriculum phase transition piaget kuhn cognition cognitive development",
        "cognition": "cognition thinking reasoning mental model cognitive bias heuristic decision metacognition attention memory",
        "knowledge": "knowledge epistemology belief truth justification evidence falsification paradigm vault",
        "complexity": "complexity emergence self-organization network scale-free power law criticality tipping point percolation",
        "ai_safety": "alignment safety reward hacking goodhart herding model collapse ai risk calibration grounding confidence llm accuracy hallucination overconfidence",
        "economics": "economy market resource value token incentive game theory cooperation trust",
        "finance": "finance trading stock portfolio risk volatility asset return drawdown market microstructure",
        "psychology": "psychology behavior personality emotion motivation stress trauma attachment cognitive",
        "neuroscience": "neuroscience brain neuron synapse plasticity cortex hippocampus neural",
        "physics": "physics quantum relativity thermodynamics entropy force energy field wave particle",
        "social": "society culture group community norm institution collective coordination political",
        "health": "health longevity disease medicine therapy diagnosis clinical treatment",
        "cell_biology": "cell biology gene dna protein metabolism mitochondria signaling pathway",
    }
    scores: dict[str, float] = {}
    for domain, keywords in domain_texts.items():
        sim = _text_similarity(text_lower, keywords)
        if sim > 0:
            scores[domain] = sim
    if scores:
        return max(scores, key=scores.get)
    return "general"


# ── Vault Sync ──────────────────────────────────────────────

DEFAULT_VAULT_PATHS = [
    os.environ.get("OBSIDIAN_VAULT", ""),
    os.path.expanduser("~/Obsidian Vault"),
    os.path.expanduser("~/personal-knowledge-backup"),
]


def find_vault() -> str | None:
    """Find the Obsidian vault directory."""
    for p in DEFAULT_VAULT_PATHS:
        path = Path(p)
        if path.exists():
            return str(path)
    # Try to find by looking for AGENTS.md
    for p in [Path.home() / "Obsidian Vault", Path.home() / "personal-knowledge-backup"]:
        if p.exists() and (p / "AGENTS.md").exists():
            return str(p)
    return None


def sync_vault(vault_path: str | None = None) -> dict:
    """Scan vault for crucible data, bridges, and percolation info."""
    path = vault_path or find_vault()
    if not path or not Path(path).exists():
        return {"status": "no_vault", "crucible_found": 0, "bridges_found": 0}
    
    root = Path(path)
    result = {"status": "ok", "vault_path": str(root), "crucible_found": 0, "bridges_found": 0}
    
    # Find crucible/replication references
    crucible_files = []
    for pattern in ["*Crucible*", "*crucible*", "*Replication*", "*Ledger*"]:
        crucible_files.extend(list(root.rglob(pattern)))
    result["crucible_found"] = len(crucible_files)
    
    # Find bridge files
    bridge_files = []
    for pattern in ["*Bridge*", "*bridge*", "*Why_*"]:
        bridge_files.extend(list(root.rglob(pattern)))
    result["bridges_found"] = len(bridge_files)
    
    # Find percolation data
    percolation_paths = [
        root / ".percolation.json",
        root / "data" / ".percolation.json",
    ]
    for pp in percolation_paths:
        if pp.exists():
            try:
                data = json.loads(pp.read_text(encoding="utf-8"))
                result["percolation"] = {
                    "domains": len(data.get("domains", {})),
                    "phases": len(data.get("phases", [])),
                    "events": len(data.get("events", [])),
                }
                # Update domain phases from live data
                for did, d in data.get("domains", {}).items():
                    name = d.get("name", did)
                    slug = name.lower().replace(" ", "_")
                    if slug in DOMAIN_PHASES:
                        DOMAIN_PHASES[slug]["phase"] = d.get("phase", DOMAIN_PHASES[slug]["phase"])
                        DOMAIN_PHASES[slug]["criticality"] = d.get("criticality", DOMAIN_PHASES[slug]["criticality"])
                result["percolation_updated"] = True
            except Exception:
                pass
    
    # Count total concept files
    concepts_dir = root / "04 Resources" / "Concepts"
    if concepts_dir.exists():
        concept_files = list(concepts_dir.rglob("*.md"))
        result["total_concepts"] = len(concept_files)
    
    # Count publications
    pub_dir = root / "04 Resources" / "Publications"
    if pub_dir.exists():
        result["total_publications"] = len(list(pub_dir.rglob("*.md")))
    
    return result


# ── Core Engine ─────────────────────────────────────────────

def find_crucible(claim: str, threshold: float = 0.1) -> list[dict]:
    """Find crucible results matching this claim using TF-IDF."""
    results = []
    for c in CRUCIBLE_DB:
        sim = _text_similarity(claim, c.get("claim", ""))
        if sim >= threshold:
            results.append({**c, "similarity": round(sim, 3)})
    results.sort(key=lambda x: -x.get("similarity", 0))
    return results[:5]


def find_bridges(concept: str, top_n: int = 3) -> list[dict]:
    """Find relevant bridges for a concept."""
    results = []
    for b in BRIDGE_DB:
        sim_a = _text_similarity(concept, b.get("a", ""))
        sim_b = _text_similarity(concept, b.get("b", ""))
        sim = max(sim_a, sim_b)
        if sim >= 0.1:
            results.append({**b, "similarity": round(sim, 3), "match_domain": b["a"] if sim_a >= sim_b else b["b"]})
    results.sort(key=lambda x: -x.get("similarity", 0))
    return results[:top_n]


def find_bridge_between(a: str, b: str) -> list[dict]:
    """Find bridges connecting two specific concepts."""
    results = []
    for bridge in BRIDGE_DB:
        sim_aa = _text_similarity(a, bridge.get("a", ""))
        sim_ab = _text_similarity(a, bridge.get("b", ""))
        sim_ba = _text_similarity(b, bridge.get("a", ""))
        sim_bb = _text_similarity(b, bridge.get("b", ""))
        score1 = (sim_aa + sim_bb) / 2
        score2 = (sim_ab + sim_ba) / 2
        score = max(score1, score2)
        if score >= 0.15:
            results.append({**bridge, "similarity": round(score, 3)})
    results.sort(key=lambda x: -x.get("similarity", 0))
    return results[:3]


def score_grounding(claim: str, domain: str = "") -> dict:
    """Score how grounded a claim is using Grounding-Coupling Law."""
    dom = domain or _classify_domain(claim)
    params = GROUNDING_COUPLING_PARAMS
    crucible_hits = find_crucible(claim, threshold=0.15)

    base_grounding = params.get("g_coupling", 0.4)

    has_falsifier = "not" in claim.lower() or "if" in claim.lower()
    has_specific_source = bool(re.search(r'\b(202[0-9]|study|paper|experiment|test|data)\b', claim.lower()))
    is_empirical = bool(re.search(r'\b(r=|p=|n=|correlation|effect|coefficient)\b', claim.lower()))

    if crucible_hits:
        hit = crucible_hits[0]
        if hit.get("status") == "PASSED":
            base_grounding = min(1.0, base_grounding + 0.4)
        elif hit.get("status") == "FAILED":
            base_grounding = max(0.1, base_grounding - 0.2)

    if has_falsifier:
        base_grounding = min(1.0, base_grounding + 0.15)
    if has_specific_source:
        base_grounding = min(1.0, base_grounding + 0.1)
    if is_empirical:
        base_grounding = min(1.0, base_grounding + 0.2)

    overconfidence_gap = params.get("g_coupling", 0.4) * (1.0 - base_grounding)

    return {
        "score": round(base_grounding, 2),
        "domain": dom,
        "overconfidence_gap": round(overconfidence_gap, 2),
        "is_calibrated": overconfidence_gap < params.get("calibrated_tolerance", 0.1),
        "has_crucible_evidence": len(crucible_hits) > 0,
        "crucible_best": crucible_hits[0] if crucible_hits else None,
        "breakdown": {
            "base_coupling": params.get("g_coupling", 0.4),
            "crucible_adjustment": 0.4 if (crucible_hits and crucible_hits[0].get("status") == "PASSED") else (-0.2 if crucible_hits else 0),
            "falsifier_bonus": 0.15 if has_falsifier else 0,
            "source_bonus": 0.1 if has_specific_source else 0,
            "empirical_bonus": 0.2 if is_empirical else 0,
        },
    }


def check_percolation(text: str) -> dict:
    """Check percolation phase for the domain of this text."""
    dom = _classify_domain(text)
    phase_info = DOMAIN_PHASES.get(dom, {"phase": "unknown", "criticality": 0.0})

    phase_emoji = {
        "normal_science": "📘", "anomaly_accumulation": "⚠️",
        "crisis": "🔥", "revolution": "🌀", "new_paradigm": "✨",
    }.get(phase_info.get("phase", ""), "❓")
    phase_label = {
        "normal_science": "Stable - continuous learning",
        "anomaly_accumulation": "Tension building",
        "crisis": "Critical - phase transition imminent",
        "revolution": "Active transition",
        "new_paradigm": "Settled into new framework",
    }.get(phase_info.get("phase", ""), "Unknown")

    return {
        "domain": dom,
        "phase": phase_info.get("phase", "unknown"),
        "phase_label": phase_label,
        "emoji": phase_emoji,
        "criticality": phase_info.get("criticality", 0.0),
        "last_transition": phase_info.get("last_transition", ""),
    }


# ── Epistemic Label ────────────────────────────────────────

def generate_epistemic_label(text: str) -> dict:
    """Generate a complete epistemic label for any text."""
    domain = _classify_domain(text)
    grounding = score_grounding(text, domain)
    crucible = find_crucible(text)
    bridges = find_bridges(text)
    percolation = check_percolation(text)

    if grounding.get("is_calibrated") and grounding.get("score", 0) > 0.6:
        calibration = "calibrated"
    elif grounding.get("overconfidence_gap", 0) > 0.5:
        calibration = "overconfident"
    elif grounding.get("score", 0) < 0.3:
        calibration = "uncertain"
    else:
        calibration = "speculative"

    label_parts = [
        f"🧪 EPISTEMIC LABEL — v1.0",
        f"{'━' * 40}",
        f"Claim: {text[:80]}",
        f"Domain: {domain}",
        f"Status:",
    ]

    if crucible:
        c = crucible[0]
        label_parts.append(f"  ◉ CRUCIBLE: {c.get('status', 'NOT_TESTED')} (n={c.get('n', '?')})")
        label_parts.append(f"    {c.get('detail', '')[:100]}")
    else:
        label_parts.append(f"  ○ NOT_IN_CRUCIBLE")

    label_parts.append(f"Grounding: {grounding.get('score', 0):.0%}")
    label_parts.append(f"Overconfidence gap: {grounding.get('overconfidence_gap', 0):.0%}")
    label_parts.append(f"Calibration: {calibration}")
    label_parts.append(f"Phase: {percolation.get('emoji', '')} {percolation.get('phase_label', '')} (criticality {percolation.get('criticality', 0):.0%})")

    if bridges:
        label_parts.append(f"Bridges:")
        for b in bridges[:2]:
            label_parts.append(f"  ↳ {b.get('id', '')}: {b.get('mechanism', '')[:80]}")

    label_parts.append(f"Rule: Certainty is cheap and internal; truth is expensive and external.")

    return {
        "label": "\n".join(label_parts),
        "domain": domain,
        "grounding": grounding,
        "crucible": crucible,
        "bridges": bridges,
        "percolation": percolation,
        "calibration": calibration,
        "text": text[:200],
    }


# ── Reports ─────────────────────────────────────────────────

def generate_report_json() -> dict:
    """Generate a complete JSON report of the epistemic engine state."""
    domains_status = {}
    for did, info in sorted(DOMAIN_PHASES.items()):
        domains_status[did] = {
            "phase": info.get("phase", "unknown"),
            "criticality": info.get("criticality", 0),
            "last_transition": info.get("last_transition", ""),
        }

    passed = sum(1 for c in CRUCIBLE_DB if c.get("status") == "PASSED")
    failed = sum(1 for c in CRUCIBLE_DB if c.get("status") == "FAILED")

    return {
        "engine": "epistemic-engine",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "grounding_coupling_law": {
            "g": GROUNDING_COUPLING_PARAMS.get("g_coupling", 0.4),
            "r_confidence_accuracy": GROUNDING_COUPLING_PARAMS.get("r_confidence_accuracy", 0.25),
            "n_studies": GROUNDING_COUPLING_PARAMS.get("n_studies", 303),
            "overconfidence_gap_threshold": GROUNDING_COUPLING_PARAMS.get("overconfidence_gap_threshold", 0.5),
        },
        "crucible": {
            "total": len(CRUCIBLE_DB),
            "passed": passed,
            "failed": failed,
        },
        "bridges": {
            "total": len(BRIDGE_DB),
        },
        "domains": {
            "total": len(DOMAIN_PHASES),
            "details": domains_status,
        },
        "has_tfidf": HAS_TFIDF,
    }


def generate_report_html() -> str:
    """Generate a standalone HTML dashboard."""
    report = generate_report_json()
    
    rows = ""
    for did, info in sorted(DOMAIN_PHASES.items()):
        crit = info.get("criticality", 0) * 100
        phase = info.get("phase", "unknown")
        emoji = {"normal_science": "📘", "anomaly_accumulation": "⚠️",
                 "crisis": "🔥", "revolution": "🌀", "new_paradigm": "✨"}.get(phase, "❓")
        bar = "█" * int(crit // 8) + "░" * (12 - int(crit // 8))
        rows += f"<tr><td>{emoji}</td><td>{did}</td><td>{phase}</td><td><code>[{bar}]</code></td><td>{crit:.0f}%</td></tr>\n"
    
    crucible_rows = ""
    for c in CRUCIBLE_DB:
        badge = "✅ PASSED" if c.get("status") == "PASSED" else "❌ FAILED"
        crucible_rows += f"<tr><td>{badge}</td><td>{c.get('claim', '')[:60]}</td><td>n={c.get('n', '?')}</td><td>{c.get('detail', '')[:80]}</td></tr>\n"
    
    bridge_rows = ""
    for b in BRIDGE_DB:
        badge = "✅" if b.get("status") == "PASSED" else "❌"
        bridge_rows += f"<tr><td>{badge}</td><td>{b.get('a', '')}</td><td>↔</td><td>{b.get('b', '')}</td><td>{b.get('mechanism', '')[:60]}</td></tr>\n"

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Epistemic Engine Report</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2em auto; padding: 0 1em; background: #0d1117; color: #c9d1d9; }}
  h1, h2, h3 {{ color: #58a6ff; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
  th, td {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid #30363d; }}
  th {{ background: #161b22; color: #8b949e; text-transform: uppercase; font-size: 0.8em; }}
  code {{ background: #161b22; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; }}
  .badge-pass {{ background: #1b3325; color: #3fb950; }}
  .badge-fail {{ background: #3d1f1f; color: #f85149; }}
  .stats {{ display: flex; gap: 1em; flex-wrap: wrap; }}
  .stat-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1em; flex: 1; min-width: 140px; }}
  .stat-num {{ font-size: 2em; font-weight: bold; color: #58a6ff; }}
  .stat-label {{ font-size: 0.8em; color: #8b949e; margin-top: 4px; }}
  .footer {{ margin-top: 2em; font-size: 0.8em; color: #484f58; text-align: center; }}
</style></head>
<body>
  <h1>🧪 Epistemic Engine Report</h1>
  <p>Generated: {report['timestamp']} | TF-IDF: {'✅' if HAS_TFIDF else '⚠️ (fallback)'}</p>

  <div class="stats">
    <div class="stat-card"><div class="stat-num">{report['crucible']['total']}</div><div class="stat-label">Crucible Claims</div></div>
    <div class="stat-card"><div class="stat-num">{report['bridges']['total']}</div><div class="stat-label">Bridges</div></div>
    <div class="stat-card"><div class="stat-num">{report['domains']['total']}</div><div class="stat-label">Domains Tracked</div></div>
    <div class="stat-card"><div class="stat-num">{report['grounding_coupling_law']['g']}</div><div class="stat-label">Grounding Coupling g</div></div>
    <div class="stat-card"><div class="stat-num">{report['grounding_coupling_law']['r_confidence_accuracy']}</div><div class="stat-label">r(conf, acc)</div></div>
  </div>

  <h2>⚖️ Crucible Results</h2>
  <table><tr><th>Status</th><th>Claim</th><th>n</th><th>Detail</th></tr>{crucible_rows}</table>

  <h2>🌉 Bridges</h2>
  <table><tr><th></th><th>Domain A</th><th></th><th>Domain B</th><th>Mechanism</th></tr>{bridge_rows}</table>

  <h2>🌋 Domain Phases</h2>
  <table><tr><th></th><th>Domain</th><th>Phase</th><th>Criticality</th><th></th></tr>{rows}</table>

  <h2>📋 Grounding-Coupling Law</h2>
  <p><strong>Self-consistency is not truth; only external grounding couples them.</strong></p>
  <p>A system builds confidence from internal consistency (consensus or precision). That confidence tracks accuracy only in proportion to its external-grounding coupling <em>g</em>. As <em>g</em> falls, confidence and accuracy decouple: an overconfidence gap opens, pumped by internal effort rather than by truth.</p>
  <p><em>Certainty is cheap and internal; truth is expensive and external.</em></p>

  <div class="footer"><p>Vault knowledge distilled into one engine. Fork at github.com/DanceNitra/epistemic-engine</p></div>
</body></html>"""


# ── CLI Commands ────────────────────────────────────────────

def cmd_claim(args):
    text = args.text
    print(f"\n📋 CLAIM: {text}\n")

    crucible = find_crucible(text)
    if crucible:
        for c in crucible[:3]:
            status = "✅" if c.get("status") == "PASSED" else "❌"
            print(f"{status} CRUCIBLE: {c.get('status', '?')} (n={c.get('n', '?')}, sim={c.get('similarity', 0):.0%})")
            print(f"   {c.get('detail', '')[:120]}")
    else:
        print("○ NOT_TESTED — no crucible match found")

    grounding = score_grounding(text)
    print(f"\n📊 GROUNDING: {grounding.get('score', 0):.0%}")
    print(f"   Overconfidence gap: {grounding.get('overconfidence_gap', 0):.0%}")
    print(f"   Domain: {grounding.get('domain', '?')}")
    if grounding.get("breakdown"):
        print(f"   Breakdown: {grounding['breakdown']}")

    bridges = find_bridges(text)
    if bridges:
        print(f"\n🌉 NEAREST BRIDGES:")
        for b in bridges[:3]:
            print(f"   {b.get('id', '?')} ({b.get('match_domain', '')})")
            print(f"   {b.get('mechanism', '')[:100]}")

    percolation = check_percolation(text)
    print(f"\n🌋 PERCOLATION:")
    print(f"   Domain: {percolation.get('domain', '?')}")
    print(f"   Phase: {percolation.get('emoji', '')} {percolation.get('phase_label', '')}")
    print(f"   Criticality: {percolation.get('criticality', 0):.0%}")

    # JSON output
    if getattr(args, "json_output", None):
        print("\n--- JSON ---")
        print(json.dumps({
            "claim": text,
            "crucible": crucible[:2],
            "grounding": grounding,
            "bridges": bridges[:2],
            "percolation": percolation,
        }, indent=2))


def cmd_bridge(args):
    a, b = args.a, args.b
    print(f"\n🌉 BRIDGE: {a} ↔ {b}\n")

    bridges = find_bridge_between(a, b)
    if bridges:
        for br in bridges:
            status = "✅" if br.get("status") == "PASSED" else "❌"
            print(f"{status} {br.get('id', '?')}")
            print(f"   {br.get('mechanism', '')[:200]}")
            print(f"   Falsifier: {br.get('falsifier', '')}")
            print(f"   Source: {br.get('source', '')}")
            print()
    else:
        print("No direct bridge found.")
        print("Try broader terms or check 'engine.py list-bridges'.")


def cmd_label(args):
    label = generate_epistemic_label(args.text)
    print(f"\n{label.get('label', '')}")


def cmd_percolation(args):
    text = args.text
    p = check_percolation(text)
    print(f"\n🌋 PERCOLATION STATUS")
    print(f"{p.get('emoji', '')} Domain: {p.get('domain', '?')}")
    print(f"   Phase: {p.get('phase_label', '')}")
    print(f"   Criticality: {p.get('criticality', 0):.0%}")
    if p.get("last_transition"):
        print(f"   Last transition: {p['last_transition']}")


def cmd_bridges(args):
    text = args.text
    bridges = find_bridges(text, top_n=10)
    print(f"\n🌉 BRIDGES for '{text}':")
    for b in bridges:
        status = "✅" if b.get("status") == "PASSED" else "❌"
        print(f"  {status} {b.get('a', '')} ↔ {b.get('b', '')} (sim={b.get('similarity', 0):.0%})")


def cmd_status(args):
    vault_info = sync_vault()
    
    print(f"\n🧪 EPISTEMIC ENGINE — Status\n")
    print(f"Crucible entries: {len(CRUCIBLE_DB)}")
    print(f"Bridges: {len(BRIDGE_DB)}")
    print(f"Domains tracked: {len(DOMAIN_PHASES)}")
    
    passed = sum(1 for c in CRUCIBLE_DB if c.get("status") == "PASSED")
    failed = sum(1 for c in CRUCIBLE_DB if c.get("status") == "FAILED")
    print(f"Crucible: {passed} PASSED, {failed} FAILED")
    
    domains_by_phase: dict[str, int] = {}
    for d, info in DOMAIN_PHASES.items():
        p = info.get("phase", "unknown")
        domains_by_phase[p] = domains_by_phase.get(p, 0) + 1
    print(f"Phases: {', '.join(f'{k}={v}' for k, v in domains_by_phase.items())}")
    
    print(f"\n📡 Matching: {'TF-IDF (scikit-learn)' if HAS_TFIDF else 'Word Overlap (fallback)'}")
    print(f"Grounding-Coupling Law active | g={GROUNDING_COUPLING_PARAMS.get('g_coupling', 0.4)}")
    print(f"r(confidence, accuracy) = {GROUNDING_COUPLING_PARAMS.get('r_confidence_accuracy', 0.25)} | n={GROUNDING_COUPLING_PARAMS.get('n_studies', 303)}")
    
    if vault_info.get("status") == "ok":
        print(f"\n📂 Vault sync: {vault_info.get('vault_path', '?')}")
        if "total_concepts" in vault_info:
            print(f"   Concepts: {vault_info['total_concepts']}")
        if "percolation" in vault_info:
            p = vault_info["percolation"]
            print(f"   Live percolation: {p.get('domains', 0)} domains, {p.get('phases', 0)} transitions")
    else:
        print(f"\n📂 Vault: NOT FOUND (run 'sync-vault --vault-path PATH')")
    
    print(f"\nKnowledge is free. Grounding is expensive.")


def cmd_sync_vault(args):
    vault_path = args.vault_path or None
    result = sync_vault(vault_path)
    print(f"\n📂 VAULT SYNC\n")
    if result.get("status") == "no_vault":
        print("No vault found. Specify with --vault-path or set OBSIDIAN_VAULT env.")
        print(f"Searched: {', '.join(DEFAULT_VAULT_PATHS)}")
    else:
        print(f"Path: {result.get('vault_path', '?')}")
        if "total_concepts" in result:
            print(f"Total concepts: {result['total_concepts']}")
        if "total_publications" in result:
            print(f"Total publications: {result['total_publications']}")
        print(f"Crucible references found: {result.get('crucible_found', 0)}")
        print(f"Bridge references found: {result.get('bridges_found', 0)}")
        if "percolation" in result:
            p = result["percolation"]
            print(f"Percolation data: {p.get('domains', 0)} domains, {p.get('phases', 0)} transitions")
        if result.get("percolation_updated"):
            print(f"⚠️  Domain phases updated from live percolation data")


def cmd_report(args):
    if getattr(args, "json_output", None) or not (getattr(args, "html", None)):
        report = generate_report_json()
        print(json.dumps(report, indent=2))
    if getattr(args, "html", None):
        html = generate_report_html()
        output = args.html
        if output == "-":
            print(html)
        elif output:
            Path(output).write_text(html, encoding="utf-8")
            print(f"HTML report written to {output}")
        else:
            print(html)


# ── Main ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="🧪 Epistemic Engine — evaluate any claim against vault epistemology"
    )
    sub = parser.add_subparsers(dest="command")

    p_claim = sub.add_parser("claim", help="Evaluate a claim")
    p_claim.add_argument("text", nargs="+")
    p_claim.add_argument("--json", dest="json_output", action="store_true", help="JSON output")

    p_bridge = sub.add_parser("bridge", help="Find bridge between two concepts")
    p_bridge.add_argument("a", nargs="+")
    p_bridge.add_argument("b", nargs="+")

    p_label = sub.add_parser("label", help="Get epistemic label for text")
    p_label.add_argument("text", nargs="+")

    p_perc = sub.add_parser("percolation", help="Check percolation phase")
    p_perc.add_argument("text", nargs="+")

    p_brs = sub.add_parser("bridges", help="List bridges for a domain")
    p_brs.add_argument("text", nargs="+")

    sub.add_parser("status", help="Engine status")

    p_sync = sub.add_parser("sync-vault", help="Scan vault for epistemic data")
    p_sync.add_argument("--vault-path", help="Path to Obsidian vault")

    p_report = sub.add_parser("report", help="Generate report")
    p_report.add_argument("--json", dest="json_output", action="store_true", help="JSON output")
    p_report.add_argument("--html", nargs="?", const="-", help="HTML report file (omit for stdout)")

    sub.add_parser("list-bridges", help="List all bridges")

    args = parser.parse_args()

    if not args.command or args.command == "status":
        cmd_status(args)
    elif args.command == "list-bridges":
        for b in BRIDGE_DB:
            status = "✅" if b.get("status") == "PASSED" else "❌"
            print(f"  {status} {b.get('a', '')} ↔ {b.get('b', '')}")
            print(f"     {b.get('mechanism', '')[:100]}\n")
    elif args.command == "claim":
        args.text = " ".join(args.text)
        cmd_claim(args)
    elif args.command == "bridge":
        args.a = " ".join(args.a)
        args.b = " ".join(args.b)
        cmd_bridge(args)
    elif args.command == "label":
        args.text = " ".join(args.text)
        cmd_label(args)
    elif args.command == "percolation":
        args.text = " ".join(args.text)
        cmd_percolation(args)
    elif args.command == "bridges":
        args.text = " ".join(args.text)
        cmd_bridges(args)
    elif args.command == "sync-vault":
        cmd_sync_vault(args)
    elif args.command == "report":
        cmd_report(args)


if __name__ == "__main__":
    main()