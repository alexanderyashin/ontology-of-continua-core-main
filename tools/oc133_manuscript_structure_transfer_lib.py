from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE_ID = "oc_core_1_3_3"
VERSION = "1.3.3"
EDITORIAL = ROOT / "releases" / RELEASE_ID / "editorial"
STRUCTURE_DIR = EDITORIAL / "master_manuscript_structure"
LEGACY_L2_MD = EDITORIAL / "MASTER_MANUSCRIPT_L2_CHAPTER_STRUCTURE_1_3_3.md"
RECOVERED_MASTER_JSON = EDITORIAL / "MASTER_MANUSCRIPT_STRUCTURE_1_3_3.json"

EXPECTED_L1_TOTAL = 20
EXPECTED_L2_TOTAL = 164
MAX_DEPTH = 10
COMPANION_MIN_DEPTH = 2
EXPECTED_STRUCTURE_FILE_TOTAL = 2 + ((MAX_DEPTH - 1) * 4) + 2 + 2

LEVEL_NAMES = {
    1: "top_level_block",
    2: "chapter",
    3: "section",
    4: "subsection",
    5: "subsubsection",
    6: "paragraph_group",
    7: "argument_move",
    8: "evidence_proof_example_slot",
    9: "transition_claim_support_slot",
    10: "paragraph_slot",
}

L3_TEMPLATES = [
    ("Purpose and Reader Task", "purpose_and_reader_task"),
    ("Core Material and Definitions", "core_material_and_definitions"),
    ("Evidence and Corpus Anchors", "evidence_and_corpus_anchors"),
    ("Boundary and Forward Transition", "boundary_and_forward_transition"),
]

DEEPER_CHAIN = {
    4: "Scope and Inclusion Rules",
    5: "Required Subclaim Coverage",
    6: "Paragraph Group Draft Slot",
    7: "Argument Move Draft Slot",
    8: "Evidence, Proof, or Example Draft Slot",
    9: "Claim-Support Transition Draft Slot",
    10: "Paragraph Draft Slot",
}

STOPWORDS = {
    "and",
    "the",
    "with",
    "from",
    "into",
    "that",
    "this",
    "core",
    "what",
    "does",
    "not",
    "claim",
    "claims",
    "release",
    "chapter",
    "section",
}

UNSAFE_TITLE_PATTERNS = [
    re.compile(r"^import:", re.I),
    re.compile(r"\.(?:tex|md|json|pdf|zip|ndjson)\b", re.I),
    re.compile(r"\b(?:route|payload|manifest|release[-_ ]machine|control[-_ ]plane)\b", re.I),
]

STANDARD_ANCHORS = [
    {
        "id": "NATURE_REPORTING_REPRODUCIBILITY",
        "url": "https://www.nature.com/ncomms/editorial-policies/reporting-standards",
        "expectation": "reporting, reproducibility, data, code, material, and protocol availability are planned before manuscript prose",
    },
    {
        "id": "ICMJE_RECOMMENDATIONS",
        "url": "https://www.icmje.org/recommendations/",
        "expectation": "authorship, contribution, accountability, manuscript preparation, and publication responsibility are explicit",
    },
    {
        "id": "TOP_GUIDELINES",
        "url": "https://incentivizingopen.org/projects2/transparency-and-openness-promotion-top-guidelines/",
        "expectation": "transparency, openness, preregisterable claims, data/code/material availability, and analytic reproducibility are structurally represented",
    },
    {
        "id": "LOGION_TOE_GRADE_POSITIVE_GATE",
        "url": "internal://logion/scientific-editorial-standard",
        "expectation": "the structure must positively plan claim, model, proof, evidence, falsifier, limits, reviewer response, reproducibility, and synthesis routes",
    },
]

STANDARD_SOURCE_URLS = {
    "NATURE_REPORTING_REPRODUCIBILITY": "https://www.nature.com/ncomms/editorial-policies/reporting-standards",
    "ICMJE_RECOMMENDATIONS": "https://www.icmje.org/recommendations/",
    "TOP_GUIDELINES": "https://incentivizingopen.org/projects2/transparency-and-openness-promotion-top-guidelines/",
    "LOGION_TOE_GRADE_POSITIVE_GATE": "internal://logion/scientific-editorial-standard",
}

STANDARD_SOURCE_REQUIREMENTS = [
    {
        "id": "NATURE_REPORTING_REQUIREMENTS",
        "source_id": "NATURE_REPORTING_REPRODUCIBILITY",
        "source_section": "Reporting requirements",
        "source_url": STANDARD_SOURCE_URLS["NATURE_REPORTING_REPRODUCIBILITY"],
        "requirement": "Plan transparent reporting and reproducibility obligations before manuscript prose is drafted.",
    },
    {
        "id": "NATURE_DATA_AVAILABILITY",
        "source_id": "NATURE_REPORTING_REPRODUCIBILITY",
        "source_section": "Availability of data",
        "source_url": STANDARD_SOURCE_URLS["NATURE_REPORTING_REPRODUCIBILITY"],
        "requirement": "Plan a data availability route that exposes the minimum dataset needed to interpret, verify, and extend claims.",
    },
    {
        "id": "NATURE_CODE_ALGORITHM_AVAILABILITY",
        "source_id": "NATURE_REPORTING_REPRODUCIBILITY",
        "source_section": "Availability and peer review of computer code and algorithm",
        "source_url": STANDARD_SOURCE_URLS["NATURE_REPORTING_REPRODUCIBILITY"],
        "requirement": "Plan code, algorithm, and replay availability for computational results central to claims.",
    },
    {
        "id": "NATURE_PROTOCOLS_MATERIALS",
        "source_id": "NATURE_REPORTING_REPRODUCIBILITY",
        "source_section": "Availability of materials / Experimental protocols",
        "source_url": STANDARD_SOURCE_URLS["NATURE_REPORTING_REPRODUCIBILITY"],
        "requirement": "Plan material, protocol, source, and artifact traceability where results require them.",
    },
    {
        "id": "ICMJE_AUTHOR_CONTRIBUTOR_ACCOUNTABILITY",
        "source_id": "ICMJE_RECOMMENDATIONS",
        "source_section": "II.A Defining the Role of Authors and Contributors",
        "source_url": STANDARD_SOURCE_URLS["ICMJE_RECOMMENDATIONS"],
        "requirement": "Plan authorship, instrument, method, contribution, and accountability statements explicitly.",
    },
    {
        "id": "ICMJE_MANUSCRIPT_PREPARATION",
        "source_id": "ICMJE_RECOMMENDATIONS",
        "source_section": "IV.A Preparing a Manuscript for Submission to a Medical Journal",
        "source_url": STANDARD_SOURCE_URLS["ICMJE_RECOMMENDATIONS"],
        "requirement": "Plan manuscript sections so a reviewer can find purpose, method, results/evidence, limits, references, and disclosures.",
    },
    {
        "id": "ICMJE_AI_USE_BOUNDARY",
        "source_id": "ICMJE_RECOMMENDATIONS",
        "source_section": "V. Use of Artificial Intelligence in Publishing",
        "source_url": STANDARD_SOURCE_URLS["ICMJE_RECOMMENDATIONS"],
        "requirement": "Plan explicit AI assistance boundaries and keep responsibility with accountable humans.",
    },
    {
        "id": "ICMJE_VERSION_CORRECTION_RESPONSIBILITY",
        "source_id": "ICMJE_RECOMMENDATIONS",
        "source_section": "III.A Corrections and Version Control",
        "source_url": STANDARD_SOURCE_URLS["ICMJE_RECOMMENDATIONS"],
        "requirement": "Plan version, correction, and incident lessons as part of publication governance.",
    },
    {
        "id": "TOP_TRANSPARENCY_POLICY_SET",
        "source_id": "TOP_GUIDELINES",
        "source_section": "8 policy recommendations / Disclosure, Requirement, Verification",
        "source_url": STANDARD_SOURCE_URLS["TOP_GUIDELINES"],
        "requirement": "Plan transparency criteria at verification level, not merely disclosure level.",
    },
    {
        "id": "TOP_DATA_CODE_MATERIALS_DESIGN_REPLICATION",
        "source_id": "TOP_GUIDELINES",
        "source_section": "TOP modular standards",
        "source_url": STANDARD_SOURCE_URLS["TOP_GUIDELINES"],
        "requirement": "Plan citation, data, code, materials, design/analysis, preregistration, analysis-plan, and replication/replay slots.",
    },
    {
        "id": "LOGION_CLAIM_MODEL_PROOF_EVIDENCE_ROUTE",
        "source_id": "LOGION_TOE_GRADE_POSITIVE_GATE",
        "source_section": "Internal TOE-grade positive gate",
        "source_url": STANDARD_SOURCE_URLS["LOGION_TOE_GRADE_POSITIVE_GATE"],
        "requirement": "Every TOE-relevant theme must have a planned path through claim, model, proof, evidence, falsifier, limits, and synthesis.",
    },
    {
        "id": "LOGION_CORPUS_COMPLETENESS_AND_FILL_HOOKS",
        "source_id": "LOGION_TOE_GRADE_POSITIVE_GATE",
        "source_section": "Internal corpus and fill-control gate",
        "source_url": STANDARD_SOURCE_URLS["LOGION_TOE_GRADE_POSITIVE_GATE"],
        "requirement": "Every terminal branch must expose later fill-control hooks and corpus-coverage obligations without assessing fill in this phase.",
    },
]

STANDARD_DERIVED_POSITIVE_CRITERIA = [
    {
        "id": "CRITERION_REPRODUCIBILITY_ARCHITECTURE",
        "criterion": "The structure must reserve explicit reporting, reproducibility, replay, and verification architecture.",
        "source_requirement_ids": ["NATURE_REPORTING_REQUIREMENTS", "TOP_TRANSPARENCY_POLICY_SET"],
        "required_title_keywords": ["methodology", "reproducibility", "replay", "verification", "artifact", "traceability"],
    },
    {
        "id": "CRITERION_DATA_EVIDENCE_AVAILABILITY",
        "criterion": "The structure must reserve data/evidence availability and minimum-evidence interpretation routes.",
        "source_requirement_ids": ["NATURE_DATA_AVAILABILITY", "TOP_DATA_CODE_MATERIALS_DESIGN_REPLICATION"],
        "required_title_keywords": ["data availability", "evidence", "validation", "target-blind", "held-out", "ledger"],
    },
    {
        "id": "CRITERION_CODE_ALGORITHM_REPLAY",
        "criterion": "The structure must reserve code, algorithm, finite-model, simulation, and replay obligations.",
        "source_requirement_ids": ["NATURE_CODE_ALGORITHM_AVAILABILITY", "TOP_DATA_CODE_MATERIALS_DESIGN_REPLICATION"],
        "required_title_keywords": ["code availability", "software", "finite model", "simulations", "replay", "lean"],
    },
    {
        "id": "CRITERION_PROTOCOL_MATERIAL_TRACEABILITY",
        "criterion": "The structure must reserve protocol, source, artifact, and corpus traceability.",
        "source_requirement_ids": ["NATURE_PROTOCOLS_MATERIALS", "LOGION_CORPUS_COMPLETENESS_AND_FILL_HOOKS"],
        "required_title_keywords": ["protocol", "source", "artifact", "corpus ledger", "traceability", "checksums"],
    },
    {
        "id": "CRITERION_AUTHOR_INSTRUMENT_METHOD_ACCOUNTABILITY",
        "criterion": "The structure must distinguish author, instrument, method, contribution, and accountability.",
        "source_requirement_ids": ["ICMJE_AUTHOR_CONTRIBUTOR_ACCOUNTABILITY", "ICMJE_AI_USE_BOUNDARY"],
        "required_title_keywords": ["author", "instrument", "method", "contribution", "ai", "accountability"],
    },
    {
        "id": "CRITERION_MANUSCRIPT_READER_NAVIGATION",
        "criterion": "The structure must make the reader path and manuscript preparation logic explicit.",
        "source_requirement_ids": ["ICMJE_MANUSCRIPT_PREPARATION", "NATURE_REPORTING_REQUIREMENTS"],
        "required_title_keywords": ["reader", "abstract", "table of contents", "reading paths", "didactic", "worked examples"],
    },
    {
        "id": "CRITERION_CLAIM_TRACEABILITY",
        "criterion": "The structure must route every promoted claim through model, proof/data evidence, boundary, and synthesis.",
        "source_requirement_ids": ["LOGION_CLAIM_MODEL_PROOF_EVIDENCE_ROUTE", "TOP_TRANSPARENCY_POLICY_SET"],
        "required_title_keywords": ["claim", "model", "proof", "evidence", "limits", "synthesis"],
    },
    {
        "id": "CRITERION_FALSIFICATION_NEGATIVE_CONTROL",
        "criterion": "The structure must reserve falsifier, negative control, counterexample, demotion, and failure-mode slots.",
        "source_requirement_ids": ["LOGION_CLAIM_MODEL_PROOF_EVIDENCE_ROUTE", "TOP_DATA_CODE_MATERIALS_DESIGN_REPLICATION"],
        "required_title_keywords": ["falsifier", "negative controls", "counterexample", "demotion", "failure modes"],
    },
    {
        "id": "CRITERION_PRIOR_ART_NOVELTY_POSITIONING",
        "criterion": "The structure must reserve prior-art, comparator, novelty, non-equivalence, and residual-delta positioning.",
        "source_requirement_ids": ["ICMJE_MANUSCRIPT_PREPARATION", "LOGION_CLAIM_MODEL_PROOF_EVIDENCE_ROUTE"],
        "required_title_keywords": ["prior art", "comparator", "novelty", "non-equivalence", "residual-delta"],
    },
    {
        "id": "CRITERION_VERSION_INCIDENT_RELEASE_GOVERNANCE",
        "criterion": "The structure must reserve version, correction, incident, known-error, citation, and external-use governance.",
        "source_requirement_ids": ["ICMJE_VERSION_CORRECTION_RESPONSIBILITY", "LOGION_CORPUS_COMPLETENESS_AND_FILL_HOOKS"],
        "required_title_keywords": ["versioning", "release governance", "incident", "known-error", "citation", "external use"],
    },
]

L1_BURDEN_MAP = {
    1: "publication identity, frontmatter, attribution, and reader navigability",
    2: "claim boundary, audience contract, and release-vs-full-science separation",
    3: "problem statement and motivation for the theory",
    4: "prior-art comparator context and scientific positioning inputs",
    5: "method, evidence architecture, falsification, and traceability standards",
    6: "mathematical and conceptual prerequisites",
    7: "core formal model and foundational limits",
    8: "dynamic, boundary, identity, and k-level semantics",
    9: "theorem spine, proof dependencies, and closure boundaries",
    10: "formalization and executable semantic evidence",
    11: "empirical, computational, and target-blind evidence lanes",
    12: "domain projection and phenomenon coverage map",
    13: "falsification, limits, demotion rules, and failure modes",
    14: "novelty, non-equivalence, and response to reframing attacks",
    15: "didactic atlas, examples, figures, and reader tracks",
    16: "adversarial review protocol and closure evidence",
    17: "reproducibility, software, data, and source-to-artifact traceability",
    18: "release governance, citation, journal extraction, and external-use boundaries",
    19: "synthesis, contribution, open program, and future release relation",
    20: "appendices, full ledgers, glossary, bibliography, index, and corpus ledger",
}

SCIENTIFIC_ARC_REQUIREMENTS = [
    ("identity", ["title", "identity", "citation", "author", "instrument", "method"]),
    ("scope", ["scope", "claims", "does not claim", "boundary", "promotion", "demotion"]),
    ("problem", ["problem", "motivation", "continuum", "liveness", "identity", "boundaries"]),
    ("prior_art", ["prior art", "comparator", "systems theory", "autopoiesis", "dynamical", "category"]),
    ("method", ["methodology", "standard", "evidence architecture", "negative controls"]),
    ("formal_model", ["formal foundation", "tuple", "well-formed", "lawful", "continuumness"]),
    ("dynamics", ["dynamics", "operators", "identity", "k-level", "rebirth", "demotion"]),
    ("proof", ["theorem", "proof", "dependency", "minimality", "counterexample"]),
    ("formalization", ["formalization", "lean", "finite model", "machine-checked", "witness"]),
    ("empirical_evidence", ["empirical", "computational", "evidence", "target-blind", "held-out"]),
    ("domain_projection", ["domain projection", "phenomenon", "coverage", "model cards"]),
    ("falsification", ["falsification", "falsifier", "failure modes", "unsupported", "risks"]),
    ("novelty", ["novelty", "non-equivalence", "overlap", "residual-delta", "positioning"]),
    ("didactics", ["didactic", "worked examples", "visual", "reader tracks", "figure"]),
    ("review", ["adversarial review", "reviewer", "cerberus", "objections", "response"]),
    ("reproducibility", ["reproducibility", "data", "software", "checksums", "replay"]),
    ("governance", ["release governance", "journal", "metadata", "owner approval", "external use"]),
    ("synthesis", ["synthesis", "contribution", "research roadmap", "future releases"]),
    ("backmatter", ["back matter", "appendix", "glossary", "bibliography", "index", "corpus ledger"]),
]

TOE_ROUTE_REQUIREMENTS = [
    ("claim", ["claim", "claims", "claim classes", "claim promotion"]),
    ("model", ["model", "tuple", "formal foundation", "well-formed continua"]),
    ("proof", ["proof", "theorem", "dependency graph", "minimality"]),
    ("evidence", ["evidence", "validation", "target-blind", "held-out"]),
    ("falsifier", ["falsifier", "falsification", "counterexample"]),
    ("limits", ["limits", "does not claim", "failure modes", "research-only"]),
    ("synthesis", ["synthesis", "what 1.3.3 establishes", "scientific contribution"]),
]

LEVEL_PURPOSES = {
    2: "chapters define the complete scientific reading architecture under frozen L1 blocks",
    3: "sections define repeatable internal obligations for every chapter before any prose is written",
    4: "subsections constrain each section into inclusion rules and scientific boundaries",
    5: "subsubsections enumerate required subclaim coverage inside each boundary",
    6: "paragraph groups reserve coherent local development units without writing prose",
    7: "argument moves reserve the rhetorical and evidential moves each paragraph group must perform",
    8: "evidence, proof, or example slots bind each argument move to future support material",
    9: "transition and claim-support slots make every support relation explicit before drafting",
    10: "paragraph slots define the final fill map for prose generation without containing prose",
}

LEVEL_STRUCTURE_RATIONALE = {
    2: [
        "L2 fixes the chapter architecture because the manuscript must first prove that every frozen L1 burden has enough reader-facing scientific capacity.",
        "The sequence separates identity, boundaries, problem, prior art, method, model, proof, evidence, limits, novelty, review, reproducibility, governance, and synthesis so reviewers can audit each obligation independently.",
        "The 164 chapter nodes are deliberate: they reserve all currently required monograph-scale functions without turning machine routes or evidence dumps into chapters.",
    ],
    3: [
        "L3 gives every chapter the same minimum section duties: reader task, core material, evidence/corpus anchor, and transition boundary.",
        "This prevents later drafting from producing chapters that explain content but forget why the reader needs it, what evidence supports it, or how it connects forward.",
    ],
    4: [
        "L4 makes inclusion rules explicit beneath each section so later content cannot sprawl or skip scientific boundaries.",
        "This level is intentionally still structural: it decides what belongs under each section before prose exists.",
    ],
    5: [
        "L5 reserves subclaim coverage so claim/evidence gaps can be detected before writing.",
        "A TOE-grade manuscript needs subclaim granularity because broad chapter headings alone cannot prove scientific completeness.",
    ],
    6: [
        "L6 groups future paragraphs into coherent local units that can later be filled, reviewed, and maturity-scored.",
        "This prevents prose generation from flattening proofs, evidence, limits, and didactics into unreviewable long passages.",
    ],
    7: [
        "L7 reserves argument moves so every paragraph group has an explicit rhetorical and evidential job.",
        "This level supports later editorial review for narrative continuity, not only factual correctness.",
    ],
    8: [
        "L8 binds argument moves to support classes: proof, evidence, example, negative control, limitation, or planned future work.",
        "This is the first level where unsupported claims become structurally visible before prose drafting.",
    ],
    9: [
        "L9 makes transitions and claim-support relations explicit so the manuscript cannot merely list facts without showing why they support the next claim.",
        "This level directly addresses the known failure mode of disconnected appendices or glued deltas.",
    ],
    10: [
        "L10 creates paragraph slots for later manuscript filling while still forbidding final prose in this phase.",
        "This is the handoff point to fill-control: every terminal slot has a future maturity hook and inherited structure remains locked.",
    ],
}

LEVEL_NEXT_EXPECTATIONS = {
    2: "L3 must give every chapter purpose, core material, evidence anchors, and transition boundaries",
    3: "L4 must state inclusion rules under each section without collapsing inherited sections",
    4: "L5 must map each subsection to required subclaims and avoid unsupported broad claims",
    5: "L6 must create paragraph-group slots that can later hold coherent manuscript prose",
    6: "L7 must define argument moves for each paragraph group before evidence is attached",
    7: "L8 must assign evidence, proof, example, or explicit future-work support slots",
    8: "L9 must define how each support slot transitions into claim support or limitation",
    9: "L10 must provide paragraph slots and fill-control hooks for later maturity tracking",
    10: "the next phase must assess fill maturity and source coverage without altering frozen structure",
}

LEVEL_REJECTED_ALTERNATIVES = {
    2: [
        "IMRAD-only article structure: rejected because OC 1.3.3 is a monograph-scale theory artifact, not a single empirical article.",
        "Appendix-first evidence dump: rejected because readers need identity, scope, problem, method, model, proof, evidence, limits, and synthesis in order.",
        "Internal build-order outline: rejected because public scientific reading order must not mirror operational build machinery.",
    ],
    3: [
        "Freeform chapter-specific sections: rejected because every chapter needs comparable purpose, material, evidence, and transition obligations.",
        "Raw corpus import headings: rejected because recovered sources are evidence for structure, not reader-facing structure by themselves.",
    ],
    4: [
        "Immediate prose outline: rejected because inclusion rules must be fixed before drafting.",
    ],
    5: [
        "Single generic subclaim bucket: rejected because later fill-control needs explicit subclaim slots.",
    ],
    6: [
        "Paragraph-level drafting now: rejected because this phase is cartography only.",
    ],
    7: [
        "Reviewer-response-only argument flow: rejected because the manuscript must teach and prove, not only defend.",
    ],
    8: [
        "Evidence-only slots: rejected because formal proof, examples, negative controls, and limitations are all required support classes.",
    ],
    9: [
        "Implicit transitions: rejected because claim-support gaps were a known release failure class.",
    ],
    10: [
        "Final prose paragraphs: rejected because L10 is paragraph-slot structure, not final manuscript text.",
    ],
}


@dataclass(frozen=True)
class OutlineNode:
    node_id: str
    parent_id: str | None
    level: int
    order_path: list[int]
    outline_number: str
    title: str
    level_name: str
    status: str
    source: str
    provenance: list[dict[str, Any]]

    def to_json(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "level_name": self.level_name,
            "node_id": self.node_id,
            "order_path": self.order_path,
            "outline_number": self.outline_number,
            "parent_id": self.parent_id,
            "provenance": self.provenance,
            "source": self.source,
            "status": self.status,
            "title": self.title,
        }


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).rstrip() + "\n"


def write_text_if_changed(path: Path, text: str) -> bool:
    normalized = text.rstrip() + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8", errors="replace") == normalized:
        return False
    path.write_text(normalized, encoding="utf-8", newline="\n")
    return True


def node_id(level: int, order_path: list[int]) -> str:
    return f"OC133-MS-L{level:02d}-" + "-".join(f"{part:03d}" for part in order_path)


def outline_number(order_path: list[int]) -> str:
    return ".".join(str(part) for part in order_path)


def sort_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(nodes, key=lambda node: tuple(node["order_path"]))


def nodes_hash(nodes: list[dict[str, Any]]) -> str:
    return sha256_text(stable_json(sort_nodes(nodes)))


def artifact_paths(depth: int) -> tuple[Path, Path]:
    stem = f"MASTER_MANUSCRIPT_STRUCTURE_L{depth:02d}_1_3_3"
    return STRUCTURE_DIR / f"{stem}.json", STRUCTURE_DIR / f"{stem}.md"


def companion_paths(depth: int) -> tuple[Path, Path]:
    stem = f"MASTER_MANUSCRIPT_STRUCTURE_L{depth:02d}_COMPANION_1_3_3"
    return STRUCTURE_DIR / f"{stem}.json", STRUCTURE_DIR / f"{stem}.md"


def standards_source_map_paths() -> tuple[Path, Path]:
    stem = "MASTER_MANUSCRIPT_STRUCTURE_STANDARDS_SOURCE_MAP_1_3_3"
    return STRUCTURE_DIR / f"{stem}.json", STRUCTURE_DIR / f"{stem}.md"


def index_paths() -> tuple[Path, Path]:
    return (
        STRUCTURE_DIR / "MASTER_MANUSCRIPT_STRUCTURE_CASCADE_INDEX_1_3_3.json",
        STRUCTURE_DIR / "MASTER_MANUSCRIPT_STRUCTURE_CASCADE_INDEX_1_3_3.md",
    )


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def parse_l1_l2_source(path: Path = LEGACY_L2_MD) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not path.exists():
        raise FileNotFoundError(path)
    l1: list[dict[str, Any]] = []
    l2: list[dict[str, Any]] = []
    current_l1: int | None = None
    l1_re = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$")
    l2_re = re.compile(r"^###\s+(\d+)\.(\d+)\s+(.+?)\s*$")
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if match := l1_re.match(line):
            current_l1 = int(match.group(1))
            l1.append(
                {
                    "index": current_l1,
                    "title": match.group(2).strip(),
                    "line": line_number,
                    "path": relative(path),
                }
            )
            continue
        if match := l2_re.match(line):
            parent = int(match.group(1))
            if current_l1 is not None and parent != current_l1:
                raise ValueError(f"L2 parent mismatch on line {line_number}: {line}")
            l2.append(
                {
                    "parent_index": parent,
                    "index": int(match.group(2)),
                    "title": match.group(3).strip(),
                    "line": line_number,
                    "path": relative(path),
                }
            )
    return l1, l2


def unsafe_reader_title(title: str) -> bool:
    return any(pattern.search(title) for pattern in UNSAFE_TITLE_PATTERNS)


def tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[A-Za-z0-9]+", text.lower())
        if len(token) >= 4 and token not in STOPWORDS
    }


def load_recovered_nodes() -> list[dict[str, Any]]:
    if not RECOVERED_MASTER_JSON.exists():
        return []
    data = json.loads(RECOVERED_MASTER_JSON.read_text(encoding="utf-8"))
    nodes: list[dict[str, Any]] = []
    for node in data.get("nodes", []):
        title = str(node.get("title", "")).strip()
        if not title or unsafe_reader_title(title):
            continue
        nodes.append(node)
    return nodes


def provenance_candidates(chapter_title: str, l1_title: str, recovered_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chapter_tokens = tokens(chapter_title) | tokens(l1_title)
    if not chapter_tokens:
        return []
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for node in recovered_nodes:
        title = str(node.get("title", ""))
        score = len(chapter_tokens & tokens(title))
        if score <= 0:
            continue
        scored.append((score, title.lower(), node))
    scored.sort(key=lambda item: (-item[0], item[1]))
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for score, _, node in scored:
        title = str(node.get("title", "")).strip()
        if title.lower() in seen:
            continue
        seen.add(title.lower())
        provenance = node.get("provenance") or []
        first = provenance[0] if provenance else {}
        candidates.append(
            {
                "commit": first.get("commit"),
                "line": first.get("line"),
                "node_id": node.get("node_id"),
                "path": first.get("path"),
                "role": node.get("role"),
                "score": score,
                "title": title,
            }
        )
        if len(candidates) == 3:
            break
    return candidates


def title_corpus(nodes: list[dict[str, Any]]) -> str:
    return " | ".join(str(node.get("title", "")).lower() for node in nodes)


def requirement_present(corpus: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in corpus for keyword in keywords)


def build_requirement_coverage(nodes: list[dict[str, Any]], requirements: list[tuple[str, list[str]]]) -> list[dict[str, Any]]:
    corpus = title_corpus(nodes)
    coverage: list[dict[str, Any]] = []
    for requirement_id, keywords in requirements:
        matched = [keyword for keyword in keywords if keyword.lower() in corpus]
        coverage.append(
            {
                "requirement_id": requirement_id,
                "status": "PLANNED_IN_STRUCTURE" if matched else "MISSING_FROM_STRUCTURE",
                "matched_keywords": matched,
                "required_keyword_set": keywords,
            }
        )
    return coverage


def standards_source_map_without_hash(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "artifact_hash"}


def build_standards_source_map_payload() -> dict[str, Any]:
    sources = []
    for anchor in STANDARD_ANCHORS:
        source_id = anchor["id"]
        sources.append(
            {
                "id": source_id,
                "url": STANDARD_SOURCE_URLS[source_id],
                "kind": "internal_standard" if source_id.startswith("LOGION_") else "external_public_standard",
                "expectation": anchor["expectation"],
                "requirement_ids": [
                    item["id"]
                    for item in STANDARD_SOURCE_REQUIREMENTS
                    if item["source_id"] == source_id
                ],
            }
        )
    payload: dict[str, Any] = {
        "artifact_kind": "MASTER_MANUSCRIPT_STRUCTURE_STANDARDS_SOURCE_MAP",
        "body_prose_included": False,
        "version": VERSION,
        "release_id": RELEASE_ID,
        "status": "ACTIVE_STRUCTURE_STANDARD_SOURCE_MAP",
        "scope": "OC Core 1.3.3 manuscript-structure cascade companions L02-L10",
        "source_policy": {
            "external_sources_are_standard_anchors": True,
            "internal_logion_standard_is_not_external_citation": True,
            "criterion_objects_required_before_100_scores": True,
            "structure_only_no_fill_assessment": True,
        },
        "sources": sources,
        "requirements": STANDARD_SOURCE_REQUIREMENTS,
        "positive_criteria": STANDARD_DERIVED_POSITIVE_CRITERIA,
    }
    payload["artifact_hash"] = sha256_text(stable_json(standards_source_map_without_hash(payload)))
    return payload


def validate_standards_source_map_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected_ids = set(STANDARD_SOURCE_URLS)
    actual_ids = {source.get("id") for source in payload.get("sources", [])}
    if actual_ids != expected_ids:
        failures.append("standard_source_id_set_mismatch")
    for source in payload.get("sources", []):
        source_id = source.get("id")
        if source.get("url") != STANDARD_SOURCE_URLS.get(str(source_id), ""):
            failures.append(f"standard_source_url_mismatch::{source_id}")
        if not source.get("requirement_ids"):
            failures.append(f"standard_source_without_requirements::{source_id}")
    requirement_ids = {item.get("id") for item in payload.get("requirements", [])}
    for criterion in payload.get("positive_criteria", []):
        if not criterion.get("source_requirement_ids"):
            failures.append(f"criterion_without_source_requirements::{criterion.get('id')}")
        for requirement_id in criterion.get("source_requirement_ids", []):
            if requirement_id not in requirement_ids:
                failures.append(f"criterion_unknown_source_requirement::{criterion.get('id')}::{requirement_id}")
        if not criterion.get("required_title_keywords"):
            failures.append(f"criterion_without_keywords::{criterion.get('id')}")
    if payload.get("body_prose_included") is not False:
        failures.append("source_map_body_prose_flag_mismatch")
    expected_hash = sha256_text(stable_json(standards_source_map_without_hash(payload)))
    if payload.get("artifact_hash") != expected_hash:
        failures.append("source_map_hash_mismatch")
    return failures


def criterion_coverage(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    corpus = title_corpus(nodes)
    requirements_by_id = {item["id"]: item for item in STANDARD_SOURCE_REQUIREMENTS}
    coverage: list[dict[str, Any]] = []
    for criterion in STANDARD_DERIVED_POSITIVE_CRITERIA:
        matched_keywords = [
            keyword
            for keyword in criterion["required_title_keywords"]
            if keyword.lower() in corpus
        ]
        source_refs = [requirements_by_id[requirement_id] for requirement_id in criterion["source_requirement_ids"]]
        coverage.append(
            {
                "criterion_id": criterion["id"],
                "criterion": criterion["criterion"],
                "status": "PLANNED_IN_STRUCTURE" if matched_keywords else "MISSING_FROM_STRUCTURE",
                "matched_keywords": matched_keywords,
                "required_title_keywords": criterion["required_title_keywords"],
                "source_requirement_ids": criterion["source_requirement_ids"],
                "exact_standard_source_refs": source_refs,
            }
        )
    return coverage


def sequence_audit(combined_nodes: list[dict[str, Any]]) -> dict[str, Any]:
    l1_nodes = [node for node in sort_nodes(combined_nodes) if int(node["level"]) == 1]
    actual_titles = [str(node["title"]) for node in l1_nodes]
    expected_titles = [
        "Front Matter And Publication Identity",
        "Orientation, Scope, And Claim Boundaries",
        "Problem, Motivation, And Scientific Context",
        "Prior Art And Comparator Landscape",
        "Methodology And Evidence Architecture",
        "Mathematical And Conceptual Preliminaries",
        "OC Core Formal Foundation",
        "Dynamics, Boundaries, Identity, And K-Levels",
        "Theorem Spine And Proof Closure",
        "Formalization And Executable Semantics",
        "Empirical And Computational Evidence",
        "Domain Projections And Phenomenon Coverage",
        "Falsification, Limits, And Failure Modes",
        "Novelty, Non-Equivalence, And Scientific Positioning",
        "Didactic Atlas And Worked Examples",
        "Adversarial Review And Reviewer Response",
        "Reproducibility, Data, Software, And Artifact Traceability",
        "Release Governance And Journal Extraction Map",
        "Synthesis And Research Program",
        "Back Matter",
    ]
    return {
        "status": "PASS" if actual_titles == expected_titles else "FAIL",
        "expected_sequence_logic": (
            "identity -> scope -> problem -> prior art -> method -> preliminaries -> model -> dynamics -> "
            "proof -> formalization -> evidence -> domains -> limits -> novelty -> didactics -> review -> "
            "reproducibility -> governance -> synthesis -> back matter"
        ),
        "expected_l1_titles": expected_titles,
        "actual_l1_titles": actual_titles,
    }


def next_level_contract(depth: int) -> dict[str, Any]:
    if depth < MAX_DEPTH:
        next_depth = depth + 1
        must_add = LEVEL_NEXT_EXPECTATIONS[depth]
    else:
        next_depth = None
        must_add = LEVEL_NEXT_EXPECTATIONS[depth]
    return {
        "current_depth": f"L{depth:02d}",
        "next_depth": f"L{next_depth:02d}" if next_depth else "FILL_CONTROL_PHASE_AFTER_STRUCTURE_APPROVAL",
        "must_preserve": [
            "all inherited_locked_nodes exactly as inherited from parent",
            "all parent hashes and combined node order",
            "L1 approved frozen titles and ordering",
            "structure-only status until owner approval",
        ],
        "must_add": must_add,
        "must_not_change": [
            "delete inherited nodes",
            "rename inherited nodes",
            "reorder inherited nodes",
            "collapse two inherited nodes into one",
            "insert manuscript prose, release payloads, or publication metadata",
            "assess fill maturity before the fill-control phase",
        ],
        "verification_commands": [
            "python tools\\oc133_manuscript_structure_orchestrator.py --check",
            "python tools\\oc133_manuscript_structure_standards_auditor.py --check",
        ],
    }


def coverage_score(coverage: list[dict[str, Any]]) -> int:
    if not coverage:
        return 0
    planned = sum(1 for item in coverage if item.get("status") == "PLANNED_IN_STRUCTURE")
    return int(round((planned / len(coverage)) * 100))


def l1_burden_coverage(combined_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    l1_nodes = [node for node in combined_nodes if int(node["level"]) == 1]
    by_index = {int(node["order_path"][0]): node for node in l1_nodes}
    coverage: list[dict[str, Any]] = []
    for index in range(1, EXPECTED_L1_TOTAL + 1):
        node = by_index.get(index)
        coverage.append(
            {
                "l1_index": index,
                "node_id": node.get("node_id") if node else "",
                "status": "PLANNED_IN_STRUCTURE" if node else "MISSING_FROM_STRUCTURE",
                "title": node.get("title") if node else "",
                "intended_scientific_burden": L1_BURDEN_MAP[index],
            }
        )
    return coverage


def parent_child_coverage(payload: dict[str, Any]) -> dict[str, Any]:
    depth = int(payload["depth"])
    if depth <= 1:
        return {"status": "NOT_APPLICABLE", "missing_parent_child_links": []}
    own = payload["own_expansion_nodes"]
    inherited_ids = {node["node_id"] for node in payload["inherited_locked_nodes"]}
    missing = [
        node["node_id"]
        for node in own
        if node.get("parent_id") is not None and node.get("parent_id") not in inherited_ids
    ]
    return {
        "status": "PASS" if not missing else "FAIL",
        "missing_parent_child_links": missing,
    }


def expected_visual_policy(node: dict[str, Any]) -> str:
    title = str(node.get("title", "")).lower()
    if any(word in title for word in ["visual", "atlas", "map", "figure", "table", "boundary", "tuple", "k-level", "projection"]):
        return "FIGURE_OR_TABLE_EXPECTED"
    if any(word in title for word in ["theorem", "proof", "dependency", "finite", "lean", "evidence", "reproducibility", "checksums"]):
        return "TABLE_OR_TRACE_EXPECTED"
    return "VISUAL_OPTIONAL_BUT_READER_AID_RECOMMENDED"


def node_expectation(node: dict[str, Any]) -> dict[str, Any]:
    level = int(node["level"])
    title = str(node["title"])
    return {
        "node_id": node["node_id"],
        "outline_number": node["outline_number"],
        "title": title,
        "level": level,
        "level_name": node["level_name"],
        "target_reader_task": f"understand the {node['level_name']} role of '{title}' in the complete OC 1.3.3 theory map",
        "required_links": {
            "prior_art": "required where the node states novelty, comparator, positioning, or external scientific context",
            "formal_claim": "required where the node states model, theorem, proof, identity, boundary, k-level, or formal semantics content",
            "evidence_or_replay": "required where the node states empirical, computational, simulation, validation, or reproducibility content",
            "limit_or_falsifier": "required where the node states claim boundary, failure mode, demotion, risk, unsupported claim, or research-only content",
        },
        "expected_figures_tables": expected_visual_policy(node),
        "future_fill_control_hook": {
            "allowed_maturity_values": ["complete", "partial", "planned", "missing"],
            "current_fill_maturity_status": "not_assessed_this_phase",
            "fill_assessment_phase": "NEXT_STEP_AFTER_STRUCTURE_APPROVAL",
        },
    }


def build_node_expectation_index(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [node_expectation(node) for node in sort_nodes(payload["own_expansion_nodes"])]


def companion_payload_without_hash(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "artifact_hash"}


def build_companion_payload(payload: dict[str, Any]) -> dict[str, Any]:
    depth = int(payload["depth"])
    if depth < COMPANION_MIN_DEPTH:
        raise ValueError("Companion payloads are defined for L02-L10 only")

    combined_nodes = payload["combined_nodes"]
    arc_coverage = build_requirement_coverage(combined_nodes, SCIENTIFIC_ARC_REQUIREMENTS)
    toe_coverage = build_requirement_coverage(combined_nodes, TOE_ROUTE_REQUIREMENTS)
    standard_criteria = criterion_coverage(combined_nodes)
    sequence = sequence_audit(combined_nodes)
    standards_map = build_standards_source_map_payload()
    standards_json_path, standards_md_path = standards_source_map_paths()
    l1_coverage = l1_burden_coverage(combined_nodes)
    parent_child = parent_child_coverage(payload)
    own_total = int(payload["node_counts"]["own_expansion"])
    inherited_total = int(payload["node_counts"]["inherited_locked"])
    combined_total = int(payload["node_counts"]["combined"])
    node_expectations = build_node_expectation_index(payload)
    unresolved = [
        item
        for item in [parent_child]
        if item.get("status") == "FAIL"
    ]
    structure_score = 100 if payload["status"] == "DRAFT_STRUCTURE_ONLY" and own_total > 0 and inherited_total > 0 else 0
    reader_path_score = 100 if node_expectations and all(item["target_reader_task"] for item in node_expectations) else 0
    standard_score = coverage_score(
        [
            {
                "status": item["status"],
            }
            for item in standard_criteria
        ]
    )
    sequence_score = 100 if sequence["status"] == "PASS" else 0
    companion: dict[str, Any] = {
        "artifact_kind": "MASTER_MANUSCRIPT_STRUCTURE_LEVEL_COMPANION",
        "body_prose_included": False,
        "version": VERSION,
        "release_id": RELEASE_ID,
        "depth": depth,
        "depth_label": payload["depth_label"],
        "structure_scope": payload["structure_scope"],
        "status": "DRAFT_STRUCTURE_REVIEW_COMPANION",
        "structure_artifact": payload["written_artifacts"],
        "structure_artifact_hash": payload["artifact_hash"],
        "structure_combined_hash": payload["combined_hash"],
        "parent_artifact_hash": payload["parent_artifact_hash"],
        "standards_source_map": {
            "artifact_hash": standards_map["artifact_hash"],
            "json": relative(standards_json_path),
            "markdown": relative(standards_md_path),
        },
        "standard_anchors": STANDARD_ANCHORS,
        "standard_source_requirements": STANDARD_SOURCE_REQUIREMENTS,
        "standard_derived_positive_criteria": standard_criteria,
        "level_purpose": LEVEL_PURPOSES[depth],
        "level_specific_rationale": LEVEL_STRUCTURE_RATIONALE[depth],
        "why_this_structure_order_is_correct": [
            "It preserves every approved/frozen parent node before adding the current level.",
            "It follows the required scientific reading path: identity, scope, problem, prior art, method, model, proof, evidence, limits, novelty, didactics, review, reproducibility, governance, synthesis, and back matter.",
            "It is structure-only, so manuscript prose cannot bypass later fill-control and editorial gates.",
        ],
        "sequence_audit": sequence,
        "rejected_alternatives": LEVEL_REJECTED_ALTERNATIVES[depth],
        "required_scientific_arc_coverage": arc_coverage,
        "toe_route_coverage": toe_coverage,
        "l1_scientific_burden_coverage": l1_coverage,
        "next_level_expectations": LEVEL_NEXT_EXPECTATIONS[depth],
        "next_level_contract": next_level_contract(depth),
        "node_expectation_index": node_expectations,
        "quantitative_checks": {
            "inherited_locked_node_total": inherited_total,
            "own_expansion_node_total": own_total,
            "combined_node_total": combined_total,
            "scientific_arc_requirement_total": len(arc_coverage),
            "scientific_arc_planned_total": sum(1 for item in arc_coverage if item["status"] == "PLANNED_IN_STRUCTURE"),
            "toe_route_requirement_total": len(toe_coverage),
            "toe_route_planned_total": sum(1 for item in toe_coverage if item["status"] == "PLANNED_IN_STRUCTURE"),
            "standard_criterion_total": len(standard_criteria),
            "standard_criterion_planned_total": sum(1 for item in standard_criteria if item["status"] == "PLANNED_IN_STRUCTURE"),
            "l1_burden_total": len(l1_coverage),
            "l1_burden_planned_total": sum(1 for item in l1_coverage if item["status"] == "PLANNED_IN_STRUCTURE"),
            "node_expectation_total": len(node_expectations),
            "unresolved_structure_question_total": len(unresolved),
        },
        "review_gate_outputs": {
            "structure_completeness_score": structure_score,
            "scientific_arc_coverage_score": coverage_score(arc_coverage),
            "reader_path_coverage_score": reader_path_score,
            "toe_target_coverage_score": coverage_score(toe_coverage),
            "standards_criterion_coverage_score": standard_score,
            "sequence_order_score": sequence_score,
            "unresolved_structure_question_total": len(unresolved),
            "review_verdict": (
                "PASS"
                if not unresolved
                and structure_score == 100
                and coverage_score(arc_coverage) == 100
                and coverage_score(toe_coverage) == 100
                and standard_score == 100
                and sequence_score == 100
                else "FAIL"
            ),
        },
        "unresolved_draft_questions": unresolved,
        "approval_policy": {
            "owner_approval_required_before_freeze": True,
            "current_level_freeze_status": "NOT_FROZEN_DRAFT_ONLY",
            "allowed_now": "revise structure; do not generate prose or release artifacts",
        },
    }
    companion["artifact_hash"] = sha256_text(stable_json(companion_payload_without_hash(companion)))
    return companion


def validate_companion_payload(companion: dict[str, Any], structure_payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    depth = int(companion["depth"])
    if depth < COMPANION_MIN_DEPTH or depth > MAX_DEPTH:
        failures.append("companion_depth_out_of_range")
    if companion.get("structure_artifact_hash") != structure_payload.get("artifact_hash"):
        failures.append("structure_artifact_hash_mismatch")
    if companion.get("structure_combined_hash") != structure_payload.get("combined_hash"):
        failures.append("structure_combined_hash_mismatch")
    if companion.get("body_prose_included") is not False:
        failures.append("body_prose_flag_mismatch")
    standards_map = build_standards_source_map_payload()
    standards_ref = companion.get("standards_source_map", {})
    if standards_ref.get("artifact_hash") != standards_map["artifact_hash"]:
        failures.append("standards_source_map_hash_mismatch")
    if {anchor.get("id") for anchor in companion.get("standard_anchors", [])} != set(STANDARD_SOURCE_URLS):
        failures.append("standard_anchor_id_set_mismatch")
    if len(companion.get("standard_source_requirements", [])) != len(STANDARD_SOURCE_REQUIREMENTS):
        failures.append("standard_source_requirement_total_mismatch")
    criteria = companion.get("standard_derived_positive_criteria", [])
    if len(criteria) != len(STANDARD_DERIVED_POSITIVE_CRITERIA):
        failures.append("standard_criteria_total_mismatch")
    requirement_ids = {item["id"] for item in STANDARD_SOURCE_REQUIREMENTS}
    for criterion in criteria:
        criterion_id = criterion.get("criterion_id", "")
        if not criterion.get("source_requirement_ids"):
            failures.append(f"criterion_without_source_requirements::{criterion_id}")
        if not criterion.get("exact_standard_source_refs"):
            failures.append(f"criterion_without_exact_source_refs::{criterion_id}")
        for requirement_id in criterion.get("source_requirement_ids", []):
            if requirement_id not in requirement_ids:
                failures.append(f"criterion_unknown_requirement::{criterion_id}::{requirement_id}")
        if criterion.get("status") != "PLANNED_IN_STRUCTURE":
            failures.append(f"criterion_not_planned::{criterion_id}")
    if companion.get("sequence_audit", {}).get("status") != "PASS":
        failures.append("sequence_audit_not_pass")
    contract = companion.get("next_level_contract", {})
    for key in ["must_preserve", "must_add", "must_not_change", "verification_commands"]:
        if not contract.get(key):
            failures.append(f"next_level_contract_missing::{key}")
    expected_total = structure_payload["node_counts"]["own_expansion"]
    if companion["quantitative_checks"]["node_expectation_total"] != expected_total:
        failures.append("node_expectation_total_mismatch")
    if companion["quantitative_checks"].get("standard_criterion_total") != len(STANDARD_DERIVED_POSITIVE_CRITERIA):
        failures.append("standard_criterion_total_mismatch")
    if companion["quantitative_checks"].get("standard_criterion_planned_total") != len(STANDARD_DERIVED_POSITIVE_CRITERIA):
        failures.append("standard_criterion_planned_total_mismatch")
    gate = companion.get("review_gate_outputs", {})
    for key in [
        "structure_completeness_score",
        "scientific_arc_coverage_score",
        "reader_path_coverage_score",
        "toe_target_coverage_score",
        "standards_criterion_coverage_score",
        "sequence_order_score",
    ]:
        if int(gate.get(key, 0)) < 100:
            failures.append(f"{key}_below_100")
    if int(gate.get("unresolved_structure_question_total", 0)) != 0:
        failures.append("unresolved_structure_questions_present")
    if gate.get("review_verdict") != "PASS":
        failures.append("review_verdict_not_pass")
    return failures


def build_level_catalog() -> dict[int, list[dict[str, Any]]]:
    l1_items, l2_items = parse_l1_l2_source()
    if len(l1_items) != EXPECTED_L1_TOTAL:
        raise ValueError(f"Expected {EXPECTED_L1_TOTAL} L1 blocks, found {len(l1_items)}")
    if len(l2_items) != EXPECTED_L2_TOTAL:
        raise ValueError(f"Expected {EXPECTED_L2_TOTAL} L2 chapters, found {len(l2_items)}")

    recovered_nodes = load_recovered_nodes()
    catalog: dict[int, list[OutlineNode]] = {level: [] for level in range(1, MAX_DEPTH + 1)}
    l1_by_index = {item["index"]: item for item in l1_items}

    for l1 in l1_items:
        path = [l1["index"]]
        catalog[1].append(
            OutlineNode(
                node_id=node_id(1, path),
                parent_id=None,
                level=1,
                order_path=path,
                outline_number=outline_number(path),
                title=l1["title"],
                level_name=LEVEL_NAMES[1],
                status="APPROVED_FROZEN_BY_OWNER",
                source="owner_approved_l1_structure",
                provenance=[{"kind": "owner_approved_l1", "line": l1["line"], "path": l1["path"]}],
            )
        )

    for l2 in l2_items:
        l1 = l1_by_index[l2["parent_index"]]
        path2 = [l2["parent_index"], l2["index"]]
        l2_id = node_id(2, path2)
        catalog[2].append(
            OutlineNode(
                node_id=l2_id,
                parent_id=node_id(1, [l2["parent_index"]]),
                level=2,
                order_path=path2,
                outline_number=outline_number(path2),
                title=l2["title"],
                level_name=LEVEL_NAMES[2],
                status="DRAFT_STRUCTURE_ONLY",
                source="owner_approved_l2_source_demoted_to_draft_cascade",
                provenance=[{"kind": "owner_approved_l2_source", "line": l2["line"], "path": l2["path"]}],
            )
        )
        candidates = provenance_candidates(l2["title"], l1["title"], recovered_nodes)
        for l3_index, (title, source_key) in enumerate(L3_TEMPLATES, start=1):
            path3 = [*path2, l3_index]
            l3_id = node_id(3, path3)
            catalog[3].append(
                OutlineNode(
                    node_id=l3_id,
                    parent_id=l2_id,
                    level=3,
                    order_path=path3,
                    outline_number=outline_number(path3),
                    title=title,
                    level_name=LEVEL_NAMES[3],
                    status="DRAFT_STRUCTURE_ONLY",
                    source=f"deterministic_l3_template::{source_key}",
                    provenance=[
                        {"kind": "template", "chapter": l2["title"], "template": source_key},
                        {"candidates": candidates, "kind": "recovered_corpus_candidates"},
                    ],
                )
            )
            parent_id = l3_id
            parent_path = path3
            for level in range(4, MAX_DEPTH + 1):
                current_path = [*parent_path, 1]
                current_id = node_id(level, current_path)
                catalog[level].append(
                    OutlineNode(
                        node_id=current_id,
                        parent_id=parent_id,
                        level=level,
                        order_path=current_path,
                        outline_number=outline_number(current_path),
                        title=DEEPER_CHAIN[level],
                        level_name=LEVEL_NAMES[level],
                        status="DRAFT_SLOT",
                        source=f"deterministic_l{level}_draft_slot_template",
                        provenance=[{"kind": "template", "parent_level": level - 1, "parent_node_id": parent_id}],
                    )
                )
                parent_id = current_id
                parent_path = current_path

    return {level: [node.to_json() for node in sorted(nodes, key=lambda item: item.order_path)] for level, nodes in catalog.items()}


def payload_without_hash(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "artifact_hash"}


def build_level_payload(depth: int, parent_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if depth < 1 or depth > MAX_DEPTH:
        raise ValueError(f"Depth out of range: {depth}")
    catalog = build_level_catalog()
    own_expansion = catalog[depth]
    if depth == 1:
        inherited_locked_nodes: list[dict[str, Any]] = []
        parent_artifact = None
        parent_artifact_hash = None
        parent_combined_hash = None
        status = "APPROVED_FROZEN_BY_OWNER"
    else:
        if parent_payload is None:
            raise ValueError(f"L{depth:02d} transfer requires parent L{depth - 1:02d} payload")
        if int(parent_payload["depth"]) != depth - 1:
            raise ValueError(f"Parent depth mismatch for L{depth:02d}")
        inherited_locked_nodes = parent_payload["combined_nodes"]
        parent_json_path, _ = artifact_paths(depth - 1)
        parent_artifact = relative(parent_json_path)
        parent_artifact_hash = parent_payload["artifact_hash"]
        parent_combined_hash = parent_payload["combined_hash"]
        status = "DRAFT_STRUCTURE_ONLY"

    combined_nodes = sort_nodes([*inherited_locked_nodes, *own_expansion])
    own_node_ids = {node["node_id"] for node in own_expansion}
    inherited_node_ids = {node["node_id"] for node in inherited_locked_nodes}
    if inherited_node_ids & own_node_ids:
        overlap = sorted(inherited_node_ids & own_node_ids)[:5]
        raise ValueError(f"L{depth:02d} own expansion overlaps inherited nodes: {overlap}")
    inherited_lookup = set(inherited_node_ids)
    for node in own_expansion:
        if node["parent_id"] is not None and node["parent_id"] not in inherited_lookup:
            raise ValueError(f"L{depth:02d} node {node['node_id']} has missing parent {node['parent_id']}")
        if unsafe_reader_title(str(node["title"])):
            raise ValueError(f"L{depth:02d} unsafe title in {node['node_id']}: {node['title']}")

    json_path, md_path = artifact_paths(depth)
    payload: dict[str, Any] = {
        "artifact_kind": "MASTER_MANUSCRIPT_LEVEL_STRUCTURE",
        "body_prose_included": False,
        "combined_hash": nodes_hash(combined_nodes),
        "combined_nodes": combined_nodes,
        "depth": depth,
        "depth_label": f"L{depth:02d}",
        "depth_semantics": {str(key): value for key, value in LEVEL_NAMES.items()},
        "inherited_locked_hash": nodes_hash(inherited_locked_nodes),
        "inherited_locked_nodes": inherited_locked_nodes,
        "node_counts": {
            "combined": len(combined_nodes),
            "inherited_locked": len(inherited_locked_nodes),
            "own_expansion": len(own_expansion),
        },
        "own_expansion_hash": nodes_hash(own_expansion),
        "own_expansion_nodes": own_expansion,
        "parent_artifact": parent_artifact,
        "parent_artifact_hash": parent_artifact_hash,
        "parent_combined_hash": parent_combined_hash,
        "release_id": RELEASE_ID,
        "status": status,
        "structure_scope": f"L01-L{depth:02d}" if depth > 1 else "L01",
        "version": VERSION,
        "written_artifacts": {"json": relative(json_path), "markdown": relative(md_path)},
    }
    payload["artifact_hash"] = sha256_text(stable_json(payload_without_hash(payload)))
    return payload


def validate_level_payload(payload: dict[str, Any], parent_payload: dict[str, Any] | None = None) -> list[str]:
    failures: list[str] = []
    depth = int(payload["depth"])
    if depth == 1:
        if payload["node_counts"]["own_expansion"] != EXPECTED_L1_TOTAL:
            failures.append("l1_total_mismatch")
        if payload["inherited_locked_nodes"]:
            failures.append("l1_has_inherited_nodes")
        if payload["status"] != "APPROVED_FROZEN_BY_OWNER":
            failures.append("l1_status_not_approved_frozen")
    else:
        if parent_payload is None:
            failures.append("missing_parent_payload")
        else:
            if payload["inherited_locked_nodes"] != parent_payload["combined_nodes"]:
                failures.append("inherited_locked_nodes_not_equal_parent_combined_nodes")
            if payload["parent_artifact_hash"] != parent_payload["artifact_hash"]:
                failures.append("parent_artifact_hash_mismatch")
            if payload["parent_combined_hash"] != parent_payload["combined_hash"]:
                failures.append("parent_combined_hash_mismatch")
        if payload["status"] != "DRAFT_STRUCTURE_ONLY":
            failures.append("draft_status_mismatch")
    if depth == 2 and payload["node_counts"]["own_expansion"] != EXPECTED_L2_TOTAL:
        failures.append("l2_total_mismatch")
    for node in payload["own_expansion_nodes"]:
        if int(node["level"]) != depth:
            failures.append(f"own_expansion_wrong_level::{node['node_id']}")
        if unsafe_reader_title(str(node["title"])):
            failures.append(f"unsafe_reader_title::{node['node_id']}")
    return failures


def render_node_list(nodes: list[dict[str, Any]], *, root_indent: int = 0) -> list[str]:
    lines: list[str] = []
    for node in sort_nodes(nodes):
        indent = "  " * max(0, int(node["level"]) - 1 + root_indent)
        status = str(node["status"])
        if status == "APPROVED_FROZEN_BY_OWNER":
            suffix = " [APPROVED_FROZEN]"
        elif status == "DRAFT_SLOT":
            suffix = " [DRAFT_SLOT]"
        else:
            suffix = " [DRAFT]"
        lines.append(f"{indent}- {node['outline_number']} {node['title']}{suffix}")
    return lines


def render_level_markdown(payload: dict[str, Any]) -> str:
    depth = int(payload["depth"])
    lines = [
        f"# OC Core 1.3.3 Master Manuscript Structure {payload['structure_scope']}",
        "",
        f"Status: {payload['status']}",
        f"Version: {payload['version']}",
        f"Depth: {payload['depth_label']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        f"Parent artifact hash: `{payload['parent_artifact_hash'] or 'NONE'}`",
        f"Parent combined hash: `{payload['parent_combined_hash'] or 'NONE'}`",
        f"Inherited locked hash: `{payload['inherited_locked_hash']}`",
        f"Own expansion hash: `{payload['own_expansion_hash']}`",
        f"Combined hash: `{payload['combined_hash']}`",
        "",
        "Structure-only artifact. It contains headings, draft slots, hashes, and provenance only.",
        "",
        "## Level Semantics",
        "",
    ]
    for level in range(1, depth + 1):
        lines.append(f"- L{level:02d}: {LEVEL_NAMES[level]}")
    lines.extend(["", "## Inherited Locked Structure", ""])
    if payload["inherited_locked_nodes"]:
        lines.extend(render_node_list(payload["inherited_locked_nodes"]))
    else:
        lines.append("None.")
    lines.extend(["", "## Own Draft Expansion", ""])
    lines.extend(render_node_list(payload["own_expansion_nodes"]))
    lines.extend(["", "## Combined Outline", ""])
    lines.extend(render_node_list(payload["combined_nodes"]))
    return "\n".join(lines) + "\n"


def render_standards_source_map_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Manuscript Structure Standards Source Map",
        "",
        f"Status: {payload['status']}",
        f"Version: {payload['version']}",
        f"Artifact hash: `{payload['artifact_hash']}`",
        "",
        "Structure-standard source map only. It records the standards used by L02-L10 companions; it is not manuscript prose.",
        "",
        "## Sources",
        "",
    ]
    for source in payload["sources"]:
        lines.append(f"- {source['id']}: {source['expectation']} ({source['url']})")
    lines.extend(["", "## Requirements", ""])
    for item in payload["requirements"]:
        lines.append(
            f"- {item['id']} [{item['source_id']} / {item['source_section']}]: "
            f"{item['requirement']} ({item['source_url']})"
        )
    lines.extend(["", "## Positive Criteria", ""])
    for item in payload["positive_criteria"]:
        lines.append(
            f"- {item['id']}: {item['criterion']} "
            f"(sources: {', '.join(item['source_requirement_ids'])})"
        )
    return "\n".join(lines) + "\n"


def render_companion_markdown(companion: dict[str, Any]) -> str:
    gate = companion["review_gate_outputs"]
    checks = companion["quantitative_checks"]
    lines = [
        f"# OC Core 1.3.3 Master Manuscript Structure {companion['structure_scope']} Companion",
        "",
        f"Status: {companion['status']}",
        f"Version: {companion['version']}",
        f"Depth: {companion['depth_label']}",
        f"Artifact hash: `{companion['artifact_hash']}`",
        f"Structure artifact hash: `{companion['structure_artifact_hash']}`",
        f"Structure combined hash: `{companion['structure_combined_hash']}`",
        f"Parent artifact hash: `{companion['parent_artifact_hash'] or 'NONE'}`",
        "",
        "Structure-review companion only. It records scientific cartography rationale and gates; it is not manuscript prose.",
        "",
        "## Purpose",
        "",
        companion["level_purpose"],
        "",
        "## Standard Anchors",
        "",
    ]
    source_ref = companion["standards_source_map"]
    lines.extend(
        [
            f"Standards source map: `{source_ref['artifact_hash']}` "
            f"({source_ref['markdown']}; {source_ref['json']})",
            "",
        ]
    )
    for anchor in companion["standard_anchors"]:
        lines.append(f"- {anchor['id']}: {anchor['expectation']} ({anchor['url']})")
    lines.extend(["", "## Standard-Derived Positive Criteria", ""])
    for item in companion["standard_derived_positive_criteria"]:
        lines.append(
            f"- {item['criterion_id']}: {item['status']} - {item['criterion']} "
            f"(sources: {', '.join(item['source_requirement_ids'])}; "
            f"matched: {', '.join(item['matched_keywords']) if item['matched_keywords'] else 'NONE'})"
        )
    lines.extend(["", "## Level-Specific Rationale", ""])
    for item in companion["level_specific_rationale"]:
        lines.append(f"- {item}")
    sequence = companion["sequence_audit"]
    lines.extend(["", "## Sequence Audit", ""])
    lines.append(f"Status: {sequence['status']}")
    lines.append(f"Logic: {sequence['expected_sequence_logic']}")
    lines.extend(["", "## Why This Structure And Order", ""])
    for item in companion["why_this_structure_order_is_correct"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Rejected Alternatives", ""])
    for item in companion["rejected_alternatives"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Required Scientific Arc Coverage", ""])
    for item in companion["required_scientific_arc_coverage"]:
        lines.append(
            f"- {item['requirement_id']}: {item['status']} "
            f"(matched: {', '.join(item['matched_keywords']) if item['matched_keywords'] else 'NONE'})"
        )
    lines.extend(["", "## TOE Route Coverage", ""])
    for item in companion["toe_route_coverage"]:
        lines.append(
            f"- {item['requirement_id']}: {item['status']} "
            f"(matched: {', '.join(item['matched_keywords']) if item['matched_keywords'] else 'NONE'})"
        )
    lines.extend(["", "## L1 Burden Coverage", ""])
    for item in companion["l1_scientific_burden_coverage"]:
        lines.append(
            f"- L1.{item['l1_index']} {item['title']}: {item['status']} - "
            f"{item['intended_scientific_burden']}"
        )
    lines.extend(["", "## Next-Level Expectations", "", companion["next_level_expectations"], ""])
    contract = companion["next_level_contract"]
    lines.extend(["## Next-Level Contract", ""])
    lines.append(f"- current_depth: {contract['current_depth']}")
    lines.append(f"- next_depth: {contract['next_depth']}")
    for field in ["must_preserve", "must_not_change", "verification_commands"]:
        lines.append(f"- {field}:")
        for item in contract[field]:
            lines.append(f"  - {item}")
    lines.append(f"- must_add: {contract['must_add']}")
    lines.append("")
    lines.extend(["## Quantitative Checks", ""])
    for key in sorted(checks.keys()):
        lines.append(f"- {key}: {checks[key]}")
    lines.extend(["", "## Review Gate Outputs", ""])
    for key in sorted(gate.keys()):
        lines.append(f"- {key}: {gate[key]}")
    lines.extend(["", "## Node Expectation Index", ""])
    for item in companion["node_expectation_index"]:
        lines.append(
            f"- {item['outline_number']} {item['title']} [{item['level_name']}]: "
            f"{item['expected_figures_tables']}; fill={item['future_fill_control_hook']['current_fill_maturity_status']}"
        )
    lines.extend(["", "## Unresolved Draft Questions", ""])
    if companion["unresolved_draft_questions"]:
        for item in companion["unresolved_draft_questions"]:
            lines.append(f"- {item}")
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


def read_payload(depth: int) -> dict[str, Any]:
    json_path, _ = artifact_paths(depth)
    if not json_path.exists():
        raise FileNotFoundError(json_path)
    return json.loads(json_path.read_text(encoding="utf-8"))


def expected_level_files(depth: int, parent_payload: dict[str, Any] | None = None) -> dict[Path, str]:
    payload = build_level_payload(depth, parent_payload)
    failures = validate_level_payload(payload, parent_payload)
    if failures:
        raise RuntimeError(f"L{depth:02d} payload validation failed: {failures}")
    json_path, md_path = artifact_paths(depth)
    files = {json_path: stable_json(payload), md_path: render_level_markdown(payload)}
    if depth >= COMPANION_MIN_DEPTH:
        companion = build_companion_payload(payload)
        companion_failures = validate_companion_payload(companion, payload)
        if companion_failures:
            raise RuntimeError(f"L{depth:02d} companion validation failed: {companion_failures}")
        companion_json_path, companion_md_path = companion_paths(depth)
        files[companion_json_path] = stable_json(companion)
        files[companion_md_path] = render_companion_markdown(companion)
    return files


def expected_standards_source_map_files() -> dict[Path, str]:
    payload = build_standards_source_map_payload()
    failures = validate_standards_source_map_payload(payload)
    if failures:
        raise RuntimeError(f"Standards source map validation failed: {failures}")
    json_path, md_path = standards_source_map_paths()
    return {json_path: stable_json(payload), md_path: render_standards_source_map_markdown(payload)}


def check_files(files: dict[Path, str]) -> dict[str, Any]:
    missing: list[str] = []
    changed: list[str] = []
    for path, text in files.items():
        rel = relative(path)
        if not path.exists():
            missing.append(rel)
            continue
        if path.read_text(encoding="utf-8", errors="replace") != text:
            changed.append(rel)
    return {"changed": changed, "missing": missing, "state": "PASS" if not missing and not changed else "FAIL"}


def write_files(files: dict[Path, str]) -> list[str]:
    changed: list[str] = []
    for path, text in files.items():
        if write_text_if_changed(path, text):
            changed.append(relative(path))
    return changed


def run_l1(write: bool) -> dict[str, Any]:
    files = expected_level_files(1, None)
    if write:
        result = {"changed": write_files(files), "missing": [], "state": "PASS"}
    else:
        result = check_files(files)
    result["depth"] = 1
    result["script_role"] = "l1_base"
    return result


def run_standards_source_map(write: bool) -> dict[str, Any]:
    files = expected_standards_source_map_files()
    if write:
        result = {"changed": write_files(files), "missing": [], "state": "PASS"}
    else:
        result = check_files(files)
    result["script_role"] = "standards_source_map"
    return result


def run_transfer(depth: int, write: bool) -> dict[str, Any]:
    if depth < 2 or depth > MAX_DEPTH:
        raise ValueError(f"Transfer depth out of range: {depth}")
    parent_payload = read_payload(depth - 1)
    files = expected_level_files(depth, parent_payload)
    if write:
        result = {"changed": write_files(files), "missing": [], "state": "PASS"}
    else:
        result = check_files(files)
    result["depth"] = depth
    result["script_role"] = f"transfer_l{depth - 1:02d}_to_l{depth:02d}"
    return result


def all_payloads_from_disk() -> list[dict[str, Any]]:
    return [read_payload(depth) for depth in range(1, MAX_DEPTH + 1)]


def build_index_payload(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    standards_map = build_standards_source_map_payload()
    standards_json_path, standards_md_path = standards_source_map_paths()
    entries = []
    for payload in payloads:
        companion_ref: dict[str, Any] | None = None
        if int(payload["depth"]) >= COMPANION_MIN_DEPTH:
            companion = build_companion_payload(payload)
            companion_json_path, companion_md_path = companion_paths(int(payload["depth"]))
            companion_ref = {
                "artifact_hash": companion["artifact_hash"],
                "json": relative(companion_json_path),
                "markdown": relative(companion_md_path),
                "review_verdict": companion["review_gate_outputs"]["review_verdict"],
                "scores": {
                    "structure_completeness_score": companion["review_gate_outputs"]["structure_completeness_score"],
                    "scientific_arc_coverage_score": companion["review_gate_outputs"]["scientific_arc_coverage_score"],
                    "reader_path_coverage_score": companion["review_gate_outputs"]["reader_path_coverage_score"],
                    "toe_target_coverage_score": companion["review_gate_outputs"]["toe_target_coverage_score"],
                    "standards_criterion_coverage_score": companion["review_gate_outputs"]["standards_criterion_coverage_score"],
                    "sequence_order_score": companion["review_gate_outputs"]["sequence_order_score"],
                    "unresolved_structure_question_total": companion["review_gate_outputs"]["unresolved_structure_question_total"],
                },
            }
        entries.append(
            {
                "artifact_hash": payload["artifact_hash"],
                "companion": companion_ref,
                "combined_hash": payload["combined_hash"],
                "depth": payload["depth"],
                "inherited_locked_hash": payload["inherited_locked_hash"],
                "node_counts": payload["node_counts"],
                "own_expansion_hash": payload["own_expansion_hash"],
                "parent_artifact_hash": payload["parent_artifact_hash"],
                "paths": payload["written_artifacts"],
                "status": payload["status"],
                "structure_scope": payload["structure_scope"],
            }
        )
    index_payload = {
        "artifact_kind": "MASTER_MANUSCRIPT_STRUCTURE_CASCADE_INDEX",
        "body_prose_included": False,
        "cascade_depth_total": MAX_DEPTH,
        "entries": entries,
        "release_id": RELEASE_ID,
        "standards_source_map": {
            "artifact_hash": standards_map["artifact_hash"],
            "json": relative(standards_json_path),
            "markdown": relative(standards_md_path),
        },
        "structure_policy": {
            "batch_draft_cadence": True,
            "companion_required_for_l2_to_l10": True,
            "l1_status": "APPROVED_FROZEN_BY_OWNER",
            "l2_to_l10_status": "DRAFT_STRUCTURE_ONLY",
            "lower_levels_must_preserve_inherited_locked_nodes": True,
            "lower_levels_split_inherited_and_own_expansion": True,
            "source_backed_positive_criteria_required": True,
        },
        "version": VERSION,
    }
    index_payload["artifact_hash"] = sha256_text(stable_json(index_payload))
    return index_payload


def render_index_markdown(index_payload: dict[str, Any]) -> str:
    lines = [
        "# OC Core 1.3.3 Master Manuscript Structure Cascade Index",
        "",
        f"Version: {index_payload['version']}",
        f"Artifact hash: `{index_payload['artifact_hash']}`",
        "",
        "This index records the separate L1-L10 structure documents.",
        "Each lower level has a locked inherited part and its own draft expansion.",
        f"Standards source map: `{index_payload['standards_source_map']['artifact_hash']}` "
        f"({index_payload['standards_source_map']['markdown']})",
        "",
        "## Artifacts",
        "",
        "| Scope | Status | Inherited | Own | Combined | Parent artifact hash | Artifact hash | Companion review |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for entry in index_payload["entries"]:
        counts = entry["node_counts"]
        companion = entry.get("companion") or {}
        companion_note = "NONE"
        if companion:
            scores = companion["scores"]
            companion_note = (
                companion["review_verdict"] +
                " arc=" + str(scores["scientific_arc_coverage_score"]) +
                " toe=" + str(scores["toe_target_coverage_score"]) +
                " standards=" + str(scores["standards_criterion_coverage_score"])
            )
        lines.append(
            f"| {entry['structure_scope']} | {entry['status']} | {counts['inherited_locked']} | "
            f"{counts['own_expansion']} | {counts['combined']} | "
            f"`{entry['parent_artifact_hash'] or 'NONE'}` | `{entry['artifact_hash']}` | {companion_note} |"
        )
    return "\n".join(lines) + "\n"


def expected_index_files() -> dict[Path, str]:
    payloads = all_payloads_from_disk()
    failures = validate_cascade_payloads(payloads)
    if failures:
        raise RuntimeError(f"Cascade validation failed before index build: {failures}")
    index_payload = build_index_payload(payloads)
    json_path, md_path = index_paths()
    return {json_path: stable_json(index_payload), md_path: render_index_markdown(index_payload)}


def validate_cascade_payloads(payloads: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    if len(payloads) != MAX_DEPTH:
        failures.append("depth_total_mismatch")
        return failures
    for expected_depth, payload in enumerate(payloads, start=1):
        if int(payload["depth"]) != expected_depth:
            failures.append(f"depth_order_mismatch::{expected_depth}")
        parent = payloads[expected_depth - 2] if expected_depth > 1 else None
        failures.extend(f"L{expected_depth:02d}::{failure}" for failure in validate_level_payload(payload, parent))
        if expected_depth >= COMPANION_MIN_DEPTH:
            companion = build_companion_payload(payload)
            failures.extend(
                f"L{expected_depth:02d}_COMPANION::{failure}"
                for failure in validate_companion_payload(companion, payload)
            )
    if payloads[0]["node_counts"]["own_expansion"] != EXPECTED_L1_TOTAL:
        failures.append("l1_total_mismatch")
    if payloads[1]["node_counts"]["own_expansion"] != EXPECTED_L2_TOTAL:
        failures.append("l2_total_mismatch")
    l3_total = payloads[2]["node_counts"]["own_expansion"]
    if payloads[9]["node_counts"]["own_expansion"] != l3_total:
        failures.append("l10_paragraph_slot_total_mismatch")
    return failures


def run_index(write: bool) -> dict[str, Any]:
    files = expected_index_files()
    if write:
        result = {"changed": write_files(files), "missing": [], "state": "PASS"}
    else:
        result = check_files(files)
    result["script_role"] = "cascade_index"
    return result


def run_transfer_cli(depth: int, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Transfer OC133 manuscript structure L{depth - 1:02d} to L{depth:02d}.")
    parser.add_argument("--write", action="store_true", help="Write this transfer output if changed.")
    parser.add_argument("--check", action="store_true", help="Check this transfer output without writing.")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = run_transfer(depth, write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1


def main_l1(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build/check OC133 manuscript structure L01 base.")
    parser.add_argument("--write", action="store_true", help="Write L01 output if changed.")
    parser.add_argument("--check", action="store_true", help="Check L01 output without writing.")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        args.check = True
    result = run_l1(write=args.write)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["state"] == "PASS" else 1
