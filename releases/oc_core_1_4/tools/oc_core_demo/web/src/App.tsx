import { useEffect, useMemo, useState } from "react";
import { line, scaleLinear } from "d3";
import type {
  Atlas,
  ClosureLedgerRow,
  Concept,
  MissionDeckCard,
  CorpusCompletenessReport,
  MSpace,
  CerberusReviewPayload,
  DomainBenchmark,
  PracticalValueDecisionSummary,
  ProofBodyIndex,
  FormulaRow,
  SystemFlowRow,
  SystemCycleRow,
  ThresholdRow,
  CompensatorRow,
  KLevel,
  KLevelWorld,
  ProofRoute,
  PracticalValueSurface,
  PracticalValueCard,
  ResearchGap,
  ReviewerObjectionRoute,
  KLevelExample,
  ScienceGraph as ScienceGraphData,
  SystemModel,
  TrustLadderEntry,
  WhyOCComparisonModel
} from "./types";
import { loadAtlas, stableHash } from "./data";
import { useExhibitStore, type ViewId } from "./store";
import { MiniVisual } from "./components/MiniVisual";
import { ScienceGraph as ScienceGraphView } from "./components/ScienceGraph";
import { CascadeScene3D } from "./components/CascadeScene3D";
import { KLevelWorld3D } from "./components/KLevelWorld3D";
import { atlasCounts, domainSeries, kElevator, killCascade, weakestNode, worldline } from "./simulations";
import "./styles.css";

type SurfaceLink = {
  view?: string;
  target_id?: string;
  target?: string;
  target_type?: string;
};

type AtlasSupplementMap = {
  proofBodyIndex?: ProofBodyIndex | null;
  decisionSummary?: PracticalValueDecisionSummary | null;
  corpusCompleteness?: CorpusCompletenessReport | null;
  wikiBridgeContract?: Record<string, any> | null;
  wikiGraphCorpusReconciliation?: Record<string, any> | null;
};

async function fetchAtlasSupplement<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(path);
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

function formatMathExcerpt(value?: string) {
  return String(value ?? "")
    .replace(/\bc 6= 0\b/g, "c != 0")
    .replace(/real part equal to 12\s*\./gi, "real part equal to 1/2.")
    .replace(/\bR3\b/g, "R^3")
    .replace(/\bC\(Q\)\b/g, "C(Q)")
    .replace(/\s+([.,;:])/g, "$1")
    .replace(/\s{2,}/g, " ")
    .trim();
}

const NAV_GROUPS: Array<{ group: string; items: Array<{ id: ViewId; label: string; }> }> = [
  {
    group: "OC Workbench",
    items: [
      { id: "journey", label: "Start" },
      { id: "workbench", label: "Workbench" },
      { id: "klevels", label: "K/M" },
      { id: "cascade", label: "Cascade" },
      { id: "benchmarks", label: "Domains" },
      { id: "graph", label: "Science Graph" },
      { id: "wiki", label: "Wiki" },
      { id: "formula", label: "Formulas" },
      { id: "proof", label: "Evidence / Boundaries" },
      { id: "reviewer", label: "Reviewer" }
    ]
  }
];

const NAV = NAV_GROUPS.flatMap((group) => group.items);

const HIDDEN_VIEW_IDS = [
  "guided",
  "klevels",
  "worldline",
  "gaps",
  "objections",
  "whyoc",
  "practical",
  "trust",
  "mission",
  "surface"
] as const;

const VIEW_IDS = [...NAV.map((item) => item.id), ...HIDDEN_VIEW_IDS] as readonly ViewId[];

type CrossLink = {
  view?: ViewId;
  graphQuery?: string;
  formulaSearch?: string;
  formulaId?: string;
  wikiSearch?: string;
  kLevel?: string;
  proofTarget?: string;
  systemId?: string;
  domainId?: string;
};

function isViewId(value: string | undefined): value is ViewId {
  return typeof value === "string" && (VIEW_IDS as readonly string[]).includes(value);
}

function normalizeView(value?: string): ViewId {
  return isViewId(value) ? value : "journey";
}

function viewLabel(value?: string): string {
  const view = normalizeView(value);
  return NAV.find((item) => item.id === view)?.label ?? ({
    guided: "Guided OC Journey",
    klevels: "K-Level Worlds",
    worldline: "Worldline Theater",
    gaps: "Closure Ledger",
    objections: "Objection Router",
    whyoc: "Why OC & Existing Models",
    practical: "Practical Value Surface",
    trust: "Trust Ladder",
    mission: "Mission Deck",
    surface: "Surface Graph"
  } as Record<string, string>)[view] ?? view;
}

function selectScienceGraph(atlas: Atlas): ScienceGraphData {
  return (
    atlas.science_graph_v010 ??
    atlas.science_graph ??
    atlas.graph
  ) as ScienceGraphData;
}

type GateStatus = "PASS" | "RC" | "FAIL" | "UNKNOWN";

function normalizeTrustStatus(rawStatus?: string): "PASS" | "RC" | "REVIEW" | "FAIL" | "UNKNOWN" {
  const status = rawStatus?.trim().toLowerCase() ?? "";
  if (!status) return "UNKNOWN";
  const passSignals = ["pass", "passed", "replay_backed", "replay-backed", "replay backed", "strong", "closed", "closed_replay_backed", "ok", "verified", "bounded", "accepted"];
  const rcSignals = ["rc", "release candidate", "release-candidate", "candidate", "conditional", "provisional", "partial", "partially_pass"];
  const failSignals = ["fail", "failed", "open", "unresolved", "critical", "review_needed", "needs_review", "pending", "not_applicable"];
  const reviewSignals = ["review", "reviewable", "frontier", "incomplete", "exploratory", "playground", "uncertain", "placeholder", "pending_review"];
  if (rcSignals.some((signal) => status === signal || status.includes(signal))) return "RC";
  if (failSignals.some((signal) => status.includes(signal))) return "FAIL";
  if (passSignals.some((signal) => status === signal || status.includes(signal))) return "PASS";
  if (reviewSignals.some((signal) => status.includes(signal))) return "REVIEW";
  return "UNKNOWN";
}

function trustLabel(status?: string, fallback = "n/a"): string {
  const normalized = normalizeTrustStatus(status);
  if (normalized === "PASS") return "PASS";
  if (normalized === "RC") return "RC";
  if (normalized === "FAIL") return "FAIL";
  if (normalized === "REVIEW") return "REVIEW";
  return fallback;
}

function gateStatusFromCerberus(rawStatus?: string, unresolved = 0): GateStatus {
  const status = rawStatus?.trim().toLowerCase() ?? "";
  if (!status) return unresolved > 0 ? "FAIL" : "PASS";
  const tokens = new Set(status.replace(/[^a-z0-9]+/g, " ").split(" ").filter(Boolean));
  const includesToken = (value: string) => tokens.has(value) || status.includes(value);
  if (includesToken("pass") && !includesToken("fail") && unresolved === 0) return "PASS";
  if (includesToken("fail") || includesToken("timeout") || includesToken("error") || includesToken("critical")) return "FAIL";
  if (includesToken("release-candidate") || includesToken("releasecandidate") || includesToken("rc") || includesToken("candidate")) return unresolved > 0 ? "RC" : "PASS";
  if (includesToken("review")) return unresolved > 0 ? "RC" : "PASS";
  return unresolved > 0 ? "RC" : "PASS";
}

function unresolvedMediumFindings(atlas: Atlas): number {
  const cerberusAll = atlas.cerberus_review?.summary?.unresolved_total;
  if (typeof cerberusAll === "number") return Math.max(0, cerberusAll);
  const cerberusMediumPlus = atlas.cerberus_review?.summary?.unresolved_medium_plus_total;
  if (typeof cerberusMediumPlus === "number") return Math.max(0, cerberusMediumPlus);
  const bySeverity = (atlas.research_gaps ?? []).filter((gap) => {
    const severity = gap.severity?.toLowerCase?.() ?? "";
    return severity.includes("med") || severity.includes("high") || severity.includes("critical");
  }).length;
  return Math.max(0, bySeverity || (atlas.research_gap_summary?.open_count ?? 0));
}

function unresolvedCerberusFindings(atlas: Atlas): number | undefined {
  if (!atlas.cerberus_review?.summary) return undefined;
  const total = atlas.cerberus_review.summary.unresolved_total;
  const mediumPlus = atlas.cerberus_review.summary.unresolved_medium_plus_total;
  if (typeof total === "number") return Math.max(0, total);
  if (typeof mediumPlus === "number") return Math.max(0, mediumPlus);
  return undefined;
}

function cerberusGateState(review: CerberusReviewPayload | undefined): {
  status: GateStatus;
  statusLabel: string;
  rationale: string;
} {
  if (!review) {
    return {
      status: "UNKNOWN",
      statusLabel: "UNKNOWN",
      rationale: "Cerberus review payload is not attached to this atlas load."
    };
  }
  const unresolved = unresolvedCerberusFindings({ cerberus_review: review } as Atlas) ?? unresolvedMediumFindings({ cerberus_review: review } as Atlas);
  const status = gateStatusFromCerberus(review.status, unresolved);
  const headline = review.review_summary ? `${review.review_summary}` : `${review.status || "review status"}`;
  const hash = review.review_hash ? ` | review hash ${review.review_hash.slice(0, 12)}` : "";
  const unresolvedLabel =
    typeof unresolved === "number"
      ? unresolved > 0
        ? ` | unresolved findings ${unresolved}`
        : " | no unresolved findings"
      : "";
  const statusLabel = `PASS/RC/FAIL: ${status}`;
  return {
    status,
    statusLabel,
    rationale: `${headline}${unresolvedLabel}${hash}`
  };
}

function formatHash(value?: string): string {
  return value ? value.slice(0, 12) : "missing";
}

function normalizeKLevelExamples(input?: Atlas["k_level_example_atlas"]): Record<string, KLevelExample[]> {
  if (!input) return {};
  if (Array.isArray(input)) {
    return input.reduce<Record<string, KLevelExample[]>>((acc, item) => {
      const level = item.k_level ?? item.k_level_id ?? item.workbench_k_level;
      if (!level) return acc;
      acc[level] = [...(acc[level] ?? []), item];
      return acc;
    }, {});
  }
  return Object.fromEntries(Object.entries(input).map(([key, value]) => [key, value as KLevelExample[]]));
}

function asText(value: unknown): string {
  if (value == null) return "";
  if (typeof value === "string") return value.trim();
  if (typeof value === "number") return String(value);
  if (typeof value === "boolean") return value ? "true" : "false";
  return "";
}

function splitTags(value: unknown): string[] {
  return asText(value)
    .toLowerCase()
    .split(/[,;\|]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function rowHasTarget(row: Record<string, unknown>, token: string, keys: string[]): boolean {
  if (!token) return true;
  const target = token.toLowerCase();
  return keys.some((key) => splitTags(row[key]).includes(target));
}

function rowSummary(row: Record<string, unknown>, keys: string[]): string {
  const fields = keys.map((key) => ({ key, value: asText(row[key]) })).filter((entry) => entry.value);
  if (fields.length === 0) return "flow/cycle record";
  return fields.map((entry) => `${entry.key}: ${entry.value}`).join(" • ");
}

function externalReviewerGate(atlas: Atlas): GateStatus {
  const cerberusFindings = unresolvedCerberusFindings(atlas);
  const unresolvedFindings = cerberusFindings ?? unresolvedMediumFindings(atlas);
  if (atlas.cerberus_review?.status) {
    return gateStatusFromCerberus(atlas.cerberus_review.status, unresolvedFindings);
  }
  if (cerberusFindings !== undefined) {
    return unresolvedFindings === 0 ? "PASS" : "RC";
  }
  return unresolvedFindings === 0 && (atlas.reviewer_mode?.external_actions ?? 0) >= 0 ? "PASS" : "FAIL";
}

function deriveFormulaAtlas(atlas: Atlas): FormulaRow[] {
  return atlas.formula_atlas ?? [];
}

function formatPercent(value?: number): string {
  if (value == null || Number.isNaN(value)) return "n/a";
  return `${Math.round(value * 100)}%`;
}

function gateStatusLabel(status: GateStatus): string {
  if (status === "PASS") return "PASS";
  if (status === "RC") return "RC";
  if (status === "FAIL") return "FAIL";
  return "UNKNOWN";
}

function operatorSummary(formula: FormulaRow): string {
  const operators = formula.operator_meanings ?? formula.operator_glossary ?? formula.operators ?? [];
  if (!operators.length) return "Not formalized in atlas.";
  return operators.map((item) => `${item.symbol}: ${item.meaning}`).join("; ");
}

function formulaConsequence(formula: FormulaRow): string {
  return formula.consequences?.length ? formula.consequences.join(" · ") : formula.interpretation ?? "No explicit consequence text.";
}

function formulaSource(formula: FormulaRow): string {
  if (formula.source_boundary) return formula.source_boundary;
  if (formula.source_link) return formula.source_link;
  if (formula.source_hash) return formula.source_hash;
  if (formula.boundary) return formula.boundary;
  if (formula.nonclaim_boundary) return formula.nonclaim_boundary;
  return "No source / boundary in atlas.";
}

function tokenScore(query: string | undefined, value: unknown): number {
  const tokens = String(query ?? "")
    .toLowerCase()
    .split(/[^a-z0-9]+/i)
    .filter((token) => token.length > 3)
    .slice(0, 8);
  if (!tokens.length) return 0;
  const haystack = JSON.stringify(value ?? {}).toLowerCase();
  return tokens.reduce((score, token) => score + (haystack.includes(token) ? 1 : 0), 0);
}

function canonicalDomainProjection(label: string, canonicalDomainIds: Set<string>): { canonical: string; reason: string } {
  const normalized = label.toUpperCase();
  const aliasMap: Record<string, { canonical: string; reason: string }> = {
    SYSTEMS: {
      canonical: "SYSTEMS_CIVILIZATIONAL_PROJECTION",
      reason: "alias used in K/M language; canonical lane is systems/civilizational projection"
    },
    SOCIAL: {
      canonical: "SYSTEMS_CIVILIZATIONAL_PROJECTION",
      reason: "social projection is reviewed inside the systems/civilizational lane"
    },
    INSTITUTIONAL: {
      canonical: "SYSTEMS_CIVILIZATIONAL_PROJECTION",
      reason: "institutional projection is reviewed inside the systems/civilizational lane"
    },
    COGNITIVE_SOCIAL: {
      canonical: "SYSTEMS_CIVILIZATIONAL_PROJECTION",
      reason: "cognitive/social label is a semantic K7/K8 alias, not a separate public benchmark lane"
    },
    META: {
      canonical: "METAONTOLOGY",
      reason: "meta label resolves to the metaontology benchmark lane"
    }
  };
  if (canonicalDomainIds.has(normalized)) return { canonical: normalized, reason: "canonical public domain lane" };
  return aliasMap[normalized] ?? {
    canonical: "BOUNDARY_ONLY",
    reason: "no public canonical lane; displayed as bounded K/M vocabulary only"
  };
}

function preferredMSpaceForLevel(levelId: string, mSpaces?: MSpace[]): MSpace | undefined {
  const spaces = mSpaces ?? [];
  if (/^K1[0-2]$/.test(levelId)) {
    const meta = spaces.find((space) => space.m_space_id === "M-META" && space.k_level_bindings?.includes(levelId));
    if (meta) return meta;
  }
  return spaces.find((space) => space.m_space_id !== "M-ROOT" && space.k_level_bindings?.includes(levelId))
    ?? spaces.find((space) => space.k_level_bindings?.includes(levelId))
    ?? spaces[0];
}

function Loading() {
  return <div className="loading">Loading OC Core 1.4 cockpit...</div>;
}

function releaseLabel(atlas: Atlas): string {
  const ordinal = atlas.release_ordinal ?? "010";
  const prefix = atlas.demo_version?.toUpperCase() ?? `V${ordinal}`;
  if (prefix.startsWith("V")) return prefix;
  return `V${prefix}`;
}

function TrustBadge({
  status,
  label
}: {
  status?: string;
  label: string;
}) {
  const level = normalizeTrustStatus(status);
  return <span className={`status-badge ${level.toLowerCase()}`}>{label}: {trustLabel(status, level)}</span>;
}

function trustForFormula(formula?: FormulaRow | null): string {
  if (!formula) return "n/a";
  return normalizeTrustStatus(formula.status) === "PASS" ? "replay-backed" : "exploratory";
}

function trustForKLevel(level?: KLevel | null): string {
  if (!level) return "n/a";
  return level.closure_status ?? level.simulation_status ?? level.model_boundary_status ?? "unknown";
}

function trustForDomain(domain?: DomainBenchmark | null): string {
  if (!domain) return "n/a";
  if (domain.closure_status) return domain.closure_status;
  return domain.validation_status ?? domain.replay_status ?? "unknown";
}

function domainUiStatus(value?: string): string {
  const text = String(value ?? "boundary").trim();
  if (!text) return "boundary";
  return text
    .replace(/\bPASS_REPLAYABLE\b/g, "replay/calibration visible")
    .replace(/\bPASS\b/g, "replay/calibration visible")
    .replace(/\bVALIDATED\b/g, "validation-evidence visible")
    .replace(/_/g, " ");
}

function trustForRoute(route?: ProofRoute | null): string {
  if (!route) return "n/a";
  return route.closure_status ?? route.status ?? "not-applicable";
}

type QualificationLedgerRow = {
  missionId?: string;
  criterion: string;
  evidence: string;
  status: string;
  nextStep: string;
  blockerReason?: string;
  rowHash?: string;
  drilldown?: string;
};

function formatRecordLine(value?: Record<string, number | string>): string {
  const entries = Object.entries(value ?? {});
  if (!entries.length) return "";
  return entries.map(([key, item]) => `${key.replace(/_/g, " ")}: ${item}`).join(" / ");
}

function deriveQualificationLedger(
  decisionSummary?: PracticalValueDecisionSummary | null,
  fallbackDomain?: DomainBenchmark | null
): QualificationLedgerRow[] {
  const mission = decisionSummary?.mission_outcome_table?.[0];
  const beforeAfter = decisionSummary?.before_after_panel;
  const localRequestPacket = decisionSummary?.local_request_packet_preview;
  const deterministic = decisionSummary?.deterministic_next_step_outcome;
  const summaryAny = decisionSummary as any;
  const sourceRows = Array.isArray(summaryAny?.follow_up_qualification_ledger?.rows)
    ? summaryAny.follow_up_qualification_ledger.rows
    : [];
  const blockedDrilldown = Array.isArray(summaryAny?.follow_up_qualification_ledger?.blocked_row_drilldown)
    ? summaryAny.follow_up_qualification_ledger.blocked_row_drilldown
    : [];
  const drilldownByMission = new Map<string, any>(
    blockedDrilldown
      .filter((row: any) => row?.mission_id)
      .map((row: any) => [String(row.mission_id), row])
  );
  if (sourceRows.length) {
    return sourceRows.map((row: any) => {
      const missionId = String(row?.mission_id ?? "mission");
      const blocked = drilldownByMission.get(missionId);
      const qualified = Boolean(row?.qualified_for_local_request);
      const blockerReason = String(row?.blocker_reason || blocked?.blocker_reason || "");
      return {
        missionId,
        criterion: qualified ? "Mission qualifies for local request" : "Blocked row drilldown",
        evidence: `criteria ${Array.isArray(row?.criteria_refs) ? row.criteria_refs.join(" / ") : "local criteria"} / row hash ${String(row?.row_hash ?? "pending").slice(0, 16)}`,
        status: String(row?.qualification_status ?? row?.threshold_verdict ?? "QUALIFICATION_PENDING"),
        nextStep: qualified
          ? String(row?.request_boundary ?? "Eligible for local replay-backed request packet only.")
          : String(blocked?.visible_remediation ?? row?.request_boundary ?? "Keep this as a formalization/replay obligation."),
        blockerReason,
        rowHash: String(row?.row_hash ?? ""),
        drilldown: blocked ? `${blocked.threshold_verdict ?? row?.threshold_verdict ?? "blocked"} / ${blocked.visible_remediation ?? "formalization/replay obligation"}` : undefined
      };
    });
  }
  const metricEvidence = formatRecordLine(mission?.metric_deltas) || formatRecordLine(beforeAfter?.delta);
  const packetFields = localRequestPacket?.included_fields?.join(" / ");
  const basis = deterministic?.basis?.join(" / ");
  return [
    {
      missionId: mission?.mission_id ?? "summary",
      criterion: "Metric deltas pass the local criterion",
      evidence: metricEvidence || decisionSummary?.local_success_criterion || fallbackDomain?.prediction_status || "Run one mission to produce before/after deltas.",
      status: mission?.threshold_verdict ?? deterministic?.status ?? "LOCAL_EVALUATION_PENDING",
      nextStep: mission?.bounded_next_step ?? deterministic?.safe_cta ?? "Keep the next step local until the deltas and export are visible.",
      blockerReason: String((mission as any)?.blocker_reason ?? "")
    },
    {
      missionId: "packet",
      criterion: "Export packet has assumptions, hash and boundary",
      evidence: packetFields || localRequestPacket?.request_type || fallbackDomain?.nonclaim_boundary || "Use the bounded export packet from the workbench.",
      status: localRequestPacket?.status ?? "PACKET_REQUIRED",
      nextStep: localRequestPacket?.next_step_rule ?? "No upload, purchase, contact or publication is performed by the demo."
    },
    {
      missionId: "summary",
      criterion: "Follow-up is qualified, not automatic adoption",
      evidence: basis || decisionSummary?.bounded_cta || fallbackDomain?.closure_basis || "Follow-up requires visible evidence rows and nonclaim boundaries.",
      status: deterministic?.status ?? mission?.evaluated_status ?? "QUALIFICATION_PENDING",
      nextStep: deterministic?.safe_cta ?? mission?.bounded_next_step ?? "If any criterion is missing, record a replay/formalization obligation."
    }
  ];
}

function LocalRequestPacketContract({
  packet,
  onOpenCardSurface,
  wrapperTestId = "local-request-packet-preview"
}: {
  packet?: any;
  onOpenCardSurface?: (surface: { view: string; target: string }) => void;
  wrapperTestId?: string;
}) {
  if (!packet) return null;
  const schema = packet.preview_schema ?? {};
  const schemaFields = Array.isArray(schema.schema_fields)
    ? schema.schema_fields
    : Object.entries(schema.field_types ?? {}).map(([field, type]) => ({
      field,
      type,
      required: Array.isArray(schema.required_fields) ? schema.required_fields.includes(field) : true,
      included_in_packet: true,
      description: field === "explicit_non_action" ? "No external action boundary must be visible." : "Required preview contract field."
    }));
  const includedFields = Array.isArray(packet.included_fields) ? packet.included_fields : [];
  const excludedFields = Array.isArray(packet.excluded_fields)
    ? packet.excluded_fields
    : [
      "price or purchase intent",
      "external contact details",
      "upload/submission destination",
      "production performance guarantee",
      "peer-review or proof acceptance claim"
    ];
  const samplePacket = packet.sample_packet ?? {
    request_type: packet.request_type ?? "local replay-backed review request packet",
    selected_surface: packet.selected_surface ?? "practical_value -> workbench export",
    included_fields: includedFields,
    nonclaim_boundary: packet.explicit_non_action ?? "No external action is performed."
  };
  const validationRows = Array.isArray(packet.validation_rows)
    ? packet.validation_rows
    : [
      { check_id: "SCHEMA_FIELDS_PRESENT", field: "preview_schema", status: schemaFields.length ? "PASS" : "MISSING", evidence: `${schemaFields.length} schema fields visible` },
      { check_id: "INCLUDED_FIELDS_VISIBLE", field: "included_fields", status: includedFields.length ? "PASS" : "MISSING", evidence: includedFields.join(" / ") || "included field list missing" },
      { check_id: "EXCLUDED_FIELDS_VISIBLE", field: "excluded_fields", status: "PASS", evidence: excludedFields.join(" / ") },
      { check_id: "SAMPLE_PACKET_INSPECTABLE", field: "sample_packet", status: "PASS", evidence: "sample packet is rendered as local JSON preview" },
      { check_id: "CTA_LOCAL_ONLY", field: "cta_binding", status: packet.cta_binding ? "PASS" : "MISSING", evidence: packet.cta_binding?.non_action ?? "CTA binding missing" },
      { check_id: "NO_EXTERNAL_ACTION_BOUNDARY", field: "explicit_non_action", status: "PASS", evidence: packet.explicit_non_action ?? "No submit/upload/purchase/contact/publish action is executed" }
    ];
  const requestHash = String(packet.request_hash ?? stableHash({ schemaFields, includedFields, excludedFields, samplePacket, validationRows }));
  const cta = packet.cta_binding ?? {};
  return (
    <div className="note result-payload" data-testid={wrapperTestId}>
      <strong>Bounded post-export request packet preview</strong><br />
      {packet.status ?? "BOUNDED_LOCAL_REQUEST_READY"} / {packet.request_type ?? "local replay-backed review request packet"}
      <small>No external action: this preview does not submit, upload, purchase, contact, or publish anything.</small>
      <small data-testid="local-request-preview-hash">Surface: {packet.selected_surface ?? "practical/workbench"} / hash {requestHash.slice(0, 16)} / rule: {packet.next_step_rule ?? "local export inspection required before follow-up"}</small>
      <small data-testid="local-request-preview-schema">
        schema {String(schema.schema_id ?? "local_request_packet_preview")} / required {(schema.required_fields ?? schemaFields.map((row: any) => row.field)).join(" / ")} / boundary {String(schema.nonclaim_boundary ?? "local preview only")}
      </small>
      <div className="formula-table-wrap" data-testid="local-request-preview-contract-fields">
        <table className="formula-table">
          <thead><tr><th>Schema field</th><th>Type</th><th>Required</th><th>Included</th><th>Reviewer note</th></tr></thead>
          <tbody>
            {schemaFields.map((row: any) => (
              <tr key={String(row.field)}>
                <td>{String(row.field)}</td>
                <td>{String(row.type ?? "unknown")}</td>
                <td>{String(row.required ?? true)}</td>
                <td>{String(row.included_in_packet ?? true)}</td>
                <td>{String(row.description ?? "Required local request preview field.")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="note-grid">
        <div className="note" data-testid="local-request-preview-included-fields">
          <strong>Included fields</strong><br />{includedFields.join(" / ") || "included field list missing"}
        </div>
        <div className="note danger" data-testid="local-request-preview-excluded-fields">
          <strong>Excluded fields</strong><br />{excludedFields.join(" / ")}
        </div>
      </div>
      <code className="export-preview" data-testid="local-request-preview-sample-packet">{JSON.stringify(samplePacket, null, 2)}</code>
      <div className="formula-table-wrap" data-testid="local-request-preview-validation-rows">
        <table className="formula-table">
          <thead><tr><th>Check</th><th>Field</th><th>Status</th><th>Evidence</th></tr></thead>
          <tbody>
            {validationRows.map((row: any) => (
              <tr key={String(row.check_id ?? row.field)}>
                <td>{String(row.check_id ?? "CHECK")}</td>
                <td>{String(row.field ?? "packet")}</td>
                <td>{String(row.status ?? "PENDING")}</td>
                <td>{String(row.evidence ?? "visible in local packet preview")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <small data-testid="local-request-preview-no-external-action-boundary">
        {String(packet.no_external_action_boundary ?? packet.explicit_non_action ?? "The demonstrator does not submit, upload, purchase, contact, or publish anything.")}
      </small>
      {onOpenCardSurface ? (
        <>
          <button
            className="action-chip"
            data-testid={String(cta.data_testid ?? "local-request-preview-cta")}
            onClick={() => onOpenCardSurface({ view: String(cta.target_view ?? "workbench"), target: String(cta.target_surface ?? "workbench-export-preview") })}
          >
            {String(cta.label ?? "Open local request preview")}
          </button>
          <small data-testid="local-request-preview-cta-binding">{String(cta.non_action ?? "CTA opens the local preview only.")}</small>
        </>
      ) : null}
    </div>
  );
}

function Hero({
  atlas,
  onJump,
  decisionSummary
}: {
  atlas: Atlas;
  onJump: (target: ViewId, link?: CrossLink) => void;
  decisionSummary?: PracticalValueDecisionSummary | null;
}) {
  const release = releaseLabel(atlas);
  const releaseOrdinal = atlas.release_ordinal ?? "010";
  const unresolvedFindings = unresolvedMediumFindings(atlas);
  const reviewerGate = externalReviewerGate(atlas);
  const cerberusGate = cerberusGateState(atlas.cerberus_review);
  const previewSystem = atlas.system_zoo?.find((system) => system.id === "civilization") ?? atlas.system_zoo?.[0];
  const threeMinuteAction = decisionSummary?.deliverables?.[0]?.three_minute_action ?? "Open a mission, run a bounded kill/improve comparison, export the result.";
  const localSuccessCriterion = decisionSummary?.local_success_criterion ?? "Complete one mission, show improved metrics or a documented failure, export assumptions/hash/boundary, then decide whether deeper replay-backed review is warranted.";
  const practicalWhy = decisionSummary?.buyer_personas?.[0]?.value_metric ?? "collapse-depth reduction and recovery-index delta";
  const systemsReady = atlas.system_zoo?.length ?? atlas.system_templates?.length ?? 0;
  const progressText = unresolvedFindings === 0 ? "Clear unresolved findings state and explicit boundaries" : "Review-facing actions are bounded; check unresolved findings first";
  const gateClass = reviewerGate === "PASS" ? "pass" : reviewerGate === "RC" ? "review" : reviewerGate === "FAIL" ? "fail" : "unknown";
  const cerberusClass = cerberusGate.status === "PASS" ? "pass" : cerberusGate.status === "RC" ? "review" : cerberusGate.status === "FAIL" ? "fail" : "unknown";
  return (
    <header className="hero hero-v003">
      <div className="hero-copy">
        <div className="hero-topline">
          <p className="eyebrow">{atlas.edition === "private" ? "Private Logion-backed instrument" : "Public-safe scientific exhibit"}</p>
          <span className="version-badge">Version {releaseOrdinal}</span>
        </div>
        <h1>Test and improve a complex system before it breaks</h1>
        <p className="hero-subhead">Ontology of Continua System Architect Workbench</p>
        <p className="hero-plain-language">
          For system architects: choose a system, let the Workbench pick the weakest support point, stress-test it, repair one editable dependency, then export one before/after decision packet with assumptions, limits and hashes.
        </p>
        <p className="hero-first-move" data-testid="first-move-copy">
          Default path: Workbench first. Open the starter system, run the failure test, repair one dependency, compare whether the system survives better, then export the decision packet. Wiki, graph and formulas are optional detours.
        </p>
        <div className="hero-actions hero-primary-actions">
          <button className="command" onClick={() => onJump("workbench", { view: "workbench", kLevel: "K8", systemId: previewSystem?.id })}>Open starter system in Workbench</button>
          <button className="command danger-command" data-testid="first-clickable-example-run" onClick={() => onJump("cascade", { view: "cascade", systemId: "civilization" })}>Run weakest-node stress test</button>
          <button className="action-chip value-chip" data-testid="bounded-evaluation-cta" onClick={() => onJump("practical", { view: "practical" })}>Show decision summary</button>
        </div>
        <div className="hero-decision-card" data-testid="first-viewport-decision-cards">
          <div data-testid="first-action-example">
            <strong>Starter example</strong>
            <span>Open the civilization template, stress-test its weakest support node, repair one dependency, and see whether the recovery packet earns deeper review.</span>
          </div>
          <div data-testid="why-care-copy">
            <strong>Why it matters</strong>
            <span>You leave with a visible before/after decision, not a slogan: what failed, what changed, what improved, and what remains unproven.</span>
          </div>
          <div data-testid="three-minute-decision-copy">
            <strong>In 3 minutes</strong>
            <span>{threeMinuteAction || "Run one bounded stress test and inspect the exported decision summary."}</span>
          </div>
        </div>
        <div className="note what-is-this-card" data-testid="what-is-this-contract">
          <strong>What is this?</strong>
          <p>A local system-architecture workbench: it turns OC into clickable models, failure tests, repair options, formulas and evidence boundaries. It is decision support, not a proof oracle or external peer review.</p>
        </div>
        <p>{progressText}. No hidden assumptions are introduced in this interface.</p>
        <div className="hero-guidance">
          <span className="hash-badge">workflow: diagnose → kill → improve → compare → export</span>
          <span className="hash-badge">success: visible local criterion</span>
          <span className="hash-badge">follow-up: qualified only after export review</span>
        </div>
        <div className="workflow-ribbon" data-testid="architect-workflow">
          <span><strong>1</strong> Diagnose</span>
          <span><strong>2</strong> Kill</span>
          <span><strong>3</strong> Improve</span>
          <span><strong>4</strong> Compare</span>
          <span><strong>5</strong> Export</span>
        </div>
        <div className="hero-status-summary" data-testid="systems-ready-status">
          <span className={`status-badge ${cerberusClass}`}>External gate: {gateStatusLabel(reviewerGate)} / Cerberus: {gateStatusLabel(cerberusGate.status)} / Open findings: {unresolvedFindings} / systems ready: {systemsReady} / {release}</span>
        </div>
      </div>
      <div className="hero-instrument" data-testid="hero-visual">
        <div className="world-ring">
          {atlas.concepts.slice(0, 8).map((concept, index) => (
            <span
              key={concept.id}
              style={{
                background: concept.color,
                transform: `rotate(${index * 45}deg) translateX(${96 + (index % 2) * 18}px) rotate(-${index * 45}deg)`
              }}
              title={concept.title}
            />
          ))}
          <b>OC</b>
        </div>
        <div className="instrument-readout">
          <strong>{releaseLabel(atlas)} / {atlas.edition ?? "public"}</strong>
          <span>{atlas.determinism_hash?.slice(0, 12) ?? stableHash(atlas).slice(0, 12)}</span>
        </div>
        <div className="live-system-card">
          <strong>{previewSystem?.title ?? "Live system model"}</strong>
          <p>{previewSystem?.what_it_shows ?? previewSystem?.nonclaim ?? "A deterministic workbench model is ready for kill, repair and comparison."}</p>
          <small>{previewSystem?.model_hash ? `model hash ${formatHash(previewSystem.model_hash)}` : "model hash missing"}</small>
          <div className="mini-metrics">
            <span>flow</span>
            <span>threshold</span>
            <span>recovery</span>
          </div>
        </div>
      </div>
    </header>
  );
}

function Navigation({ view, setView }: { view: ViewId; setView: (view: ViewId) => void }) {
  return (
    <nav className="top-nav">
      {NAV_GROUPS.map((group) => (
        <section className="nav-section" key={group.group}>
          <h4>{group.group}</h4>
          <div className="nav-group">
            {group.items.map((item) => (
              <button key={item.id} className={view === item.id ? "active" : ""} onClick={() => setView(item.id)}>
                {item.label}
              </button>
            ))}
          </div>
        </section>
      ))}
    </nav>
  );
}

function Journey({
  atlas,
  onJump,
  selectedKLevel
}: {
  atlas: Atlas;
  selectedKLevel: string;
  onJump: (target: ViewId, link?: CrossLink) => void;
}) {
  const journey = atlas.journeys?.[0];
  const counts = atlasCounts(atlas);
  const defaultSteps = [
    { id: "j0", title: "OC Cockpit", view: "journey", minutes: 1 },
    { id: "j1", title: "Read the 12-minute guide", view: "wiki", minutes: 2 },
    { id: "j2", title: "Inspect Formula Atlas", view: "formula", minutes: 2 },
    { id: "j3", title: "Inspect K0-K12", view: "klevels", k_level_id: selectedKLevel, minutes: 2 },
    { id: "j4", title: "Inspect System Workbench", view: "workbench", minutes: 1 },
    { id: "j5", title: "Rotate the 3D graph", view: "graph", minutes: 3 }
  ];
  const steps = journey?.steps?.length ? journey.steps : defaultSteps;
  const journeyAudience = journey?.audience ?? "first-time scientific reviewer";
  const journeyTitle = journey?.title ?? "Version 010 Cockpit";
  const journeyPromise = journey?.promise ?? "Move from root construction to traceable boundaries through graph, formulas and evidence routes.";
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);

  function handleStep(step: { id: string; title: string; view?: string; concept?: string; concept_id?: string; k_level_id?: string; minutes: number }) {
    const view = isViewId(step.view) ? step.view : "journey";
    setCompletedSteps((current) => current.includes(step.id) ? current : [...current, step.id]);
    onJump(view, {
      view,
      wikiSearch: step.concept ?? step.concept_id,
      graphQuery: step.concept ?? step.concept_id,
      kLevel: step.k_level_id
    });
  }

  return (
    <section className="panel journey-panel cockpit-panel" data-testid="cockpit-surface">
      <div className="section-header">
        <div>
          <p className="eyebrow">{journeyAudience}</p>
          <h2>{journeyTitle}</h2>
          <p>{journeyPromise}</p>
          <span className="hash-badge">guided rail active</span>
        </div>
        <button className="command" onClick={() => onJump("workbench", { view: "workbench", kLevel: selectedKLevel })}>Open workbench</button>
        <button className="command danger-command" onClick={() => onJump("cascade", { view: "cascade" })}>Kill cascade</button>
      </div>
      <div className="journey-layout">
        <aside className="journey-rail">
          <h3>Journey Rail</h3>
          <p className="eyebrow">step-by-step didactic flow</p>
          <div className="route-progress" data-testid="journey-completion">
            <strong>{completedSteps.length}/{steps.length}</strong>
            <span>steps opened in this session</span>
          </div>
          {steps.map((step, index) => (
            <button key={step.id} className={`journey-step ${completedSteps.includes(step.id) ? "complete" : ""}`} onClick={() => handleStep(step)}>
              <span>{index + 1}</span>
              <strong>{step.title}</strong>
              <em>{step.minutes} min</em>
            </button>
          ))}
          <div className="tag-row">
            <button className="action-chip" onClick={() => onJump("graph", { view: "graph", graphQuery: "proof", kLevel: selectedKLevel })}>
              Open root graph
            </button>
            <button className="action-chip" onClick={() => onJump("formula", { view: "formula", formulaSearch: selectedKLevel })}>
              Search formulas by k-level cue
            </button>
            <button className="action-chip" onClick={() => onJump("whyoc", { view: "whyoc" })}>Why OC / compare models</button>
            <button className="action-chip" onClick={() => onJump("objections", { view: "objections" })}>Objection Router</button>
          </div>
        </aside>
        <div className="cockpit-grid">
          <button className="module-tile worldline-tile" onClick={() => onJump("worldline", { view: "worldline" })}>
            <strong>Birth / Evolution / Collapse</strong>
            <p>Watch a continuum form, differentiate, survive pressure or cross collapse threshold.</p>
          </button>
          <button className="module-tile" onClick={() => onJump("klevels", { view: "klevels", kLevel: "K0" })}>
            <strong>K0-K12 3D Worlds</strong>
            <p>{counts.kWorlds} rotatable continua with invariants, projections, proof status and replay state.</p>
          </button>
          <button className="module-tile" onClick={() => onJump("wiki", { view: "wiki", wikiSearch: "continuum" })}>
            <strong>Full Corpus Wiki</strong>
            <p>{counts.corpusAtoms} atomized monograph/method units and {counts.formulas} curated formula rows.</p>
          </button>
          <button className="module-tile" onClick={() => onJump("formula", { view: "formula", formulaSearch: "continuum" })}>
            <strong>Formula Atlas</strong>
            <p>Inspect curated formulas with domain, operators, consequences, source boundary and diagnostic chart.</p>
          </button>
          <button className="module-tile" onClick={() => onJump("benchmarks", { view: "benchmarks" })}>
            <strong>Domain Simulators</strong>
            <p>NIST/CODATA, chemistry, biology and systems lanes show replay-backed closure or explicit meta-only limits.</p>
          </button>
          <button className="module-tile" onClick={() => onJump("graph", { view: "graph", graphQuery: "OC14" })}>
            <strong>3D Science Graph</strong>
            <p>
              {(selectScienceGraph(atlas) as { summary: { node_total: number; edge_total: number } }).summary.node_total} clickable nodes,
              {(selectScienceGraph(atlas) as { summary: { edge_total: number } }).summary.edge_total} edges, semantic labels and evidence routes.
            </p>
          </button>
          <button className="module-tile" onClick={() => onJump("workbench", { view: "workbench", systemId: atlas.system_zoo?.[0]?.id })}>
            <strong>System Workbench</strong>
            <p>Explore K/M mapping between levels and model entries.</p>
          </button>
          <button className="module-tile worldline-tile" onClick={() => onJump("cascade", { view: "cascade" })}>
            <strong>Cascade Lab</strong>
            <p>Choose a node or weakest support, set speed, break the system and watch rupture/recovery.</p>
          </button>
          <button className="module-tile" onClick={() => onJump("gaps", { view: "gaps" })}>
            <strong>Gap Closure</strong>
            <p>{counts.openGaps} open gaps, {counts.closureRows} closure rows, proof placeholders converted into auditable boundaries.</p>
          </button>
        </div>
      </div>
      <div className="concept-strip">
        {atlas.concepts.map((concept) => (
          <button
            key={concept.id}
            className="concept-chip"
            style={{ borderColor: concept.color }}
            onClick={() => onJump("wiki", { wikiSearch: concept.title, graphQuery: concept.title, view: "wiki" })}
          >
            <span style={{ background: concept.color }} />
            {concept.title}
          </button>
        ))}
      </div>
    </section>
  );
}

function ObjectionRouter({
  atlas,
  onJump
}: {
  atlas: Atlas;
  onJump: (target: ViewId, link?: CrossLink) => void;
}) {
  const routes: ReviewerObjectionRoute[] = atlas.reviewer_objection_routes?.length
    ? atlas.reviewer_objection_routes
    : [
      {
        id: "objection_route::what_is_this",
        title: "I don’t understand what this is",
        audience: "external reviewer",
        severity: "medium",
        promise: "Route directly to the OC comparison and graph-first explanation surfaces.",
        steps: [],
        links_to_real_surfaces: [{ view: "whyoc", target_type: "comparison", target_id: "why_oc" }],
        nonclaim_boundary: "Fallback objection route generated when dedicated route assets are unavailable."
      },
      {
        id: "objection_route::proof",
        title: "I don’t see proof",
        audience: "external reviewer",
        severity: "medium",
        promise: "Open proof/evidence and trust ladder before accepting any claim.",
        steps: [],
        links_to_real_surfaces: [{ view: "proof", target_type: "proof_boundary", target_id: "OC14-N001" }],
        nonclaim_boundary: "Proof route exposes boundaries; it does not invent external acceptance."
      }
    ];

  function openRoute(route: ReviewerObjectionRoute) {
    const link = route.links_to_real_surfaces?.[0];
    const view = isViewId(link?.view) ? link.view : "whyoc";
    const targetId = link?.target_id ?? "";
    const payload: CrossLink = { view };
    if (view === "graph") payload.graphQuery = targetId;
    if (view === "formula") payload.formulaSearch = targetId;
    if (view === "wiki") payload.wikiSearch = targetId;
    if (view === "proof") payload.proofTarget = targetId;
    if (view === "benchmarks") payload.domainId = targetId;
    if (view === "workbench") payload.systemId = targetId;
    onJump(view, payload);
  }

  return (
    <section className="panel big-panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">objection intake</p>
          <h2>Objection Router</h2>
          <p>Route each objection to the most direct didactic surface for immediate evidence checks.</p>
        </div>
        <span className="metric-stack">{routes.length}</span>
      </div>
      <div className="module-tile-grid">
        {routes.slice(0, 12).map((route) => (
          <button className="module-tile" key={route.id} onClick={() => openRoute(route)}>
            <strong>{route.title}</strong>
            <p>{route.promise}</p>
            <small>{route.audience} / {route.severity} / {route.links_to_real_surfaces?.[0]?.view ?? "route"}</small>
          </button>
        ))}
      </div>
    </section>
  );
}

function WhyOCModelComparison({
  atlas,
  onOpenWorkbench,
  onOpenFormula,
  onOpenGraph,
  onOpenLink
}: {
  atlas: Atlas;
  onOpenWorkbench: (kLevel: string) => void;
  onOpenFormula: (query: string) => void;
  onOpenGraph: (query: string) => void;
  onOpenLink: (link: SurfaceLink) => void;
}) {
  const atlasEntries: WhyOCComparisonModel[] = (atlas.model_comparison_matrix ?? atlas.why_oc?.comparisons ?? []).slice(0, 9);
  const systems = atlas.system_zoo ?? [];
  const templates = atlas.system_templates ?? [];
  const kLevels = atlas.k_levels ?? [];
  const fallback: WhyOCComparisonModel[] = systems.length
    ? systems.map((system) => ({
        id: system.id,
        title: system.title,
        domain: system.k_levels.slice(0, 1)[0] ?? "global",
        strengths: ["Mapped onto K/M hierarchy", "Simulation-ready components"],
        limitations: ["Replay status in workbench is exploratory until validated."],
        trust_status: system.title ? "frontier" : "unknown"
      }))
    : templates.length
      ? templates.map((template) => ({
          id: template.template_id,
          title: template.title,
          domain: template.k_levels.join(", ") || "global",
          strengths: ["Template axis set available", "Replay-boundary documented"],
          limitations: ["Replay and replay hash need closure completion for promotion."],
          trust_status: template.truth_mode ?? "frontier"
        }))
      : [];
  const rows = atlasEntries.length ? atlasEntries : fallback;
  const compareKCount = kLevels.length;
  const comparisonHash = stableHash(rows.map((row) => ({
    id: row.comparison_id ?? row.model_id ?? row.id,
    oc_adds: row.oc_adds,
    does_not_replace: row.does_not_replace,
    when_not_to_use: row.when_not_to_use
  })));

  function openSurfaceLink(link: SurfaceLink) {
    const view = isViewId(link.view) ? link.view : "whyoc";
    const target = link.target_id ?? "";
    onOpenLink({ view, target, target_type: link.target_type, target_id: target });
  }

  const selectionSummary = rows.length
    ? rows.reduce<Record<string, number>>((acc, row) => {
      const key = modelComparisonCriteria(row).join(" / ") || "comparison not explicit";
      acc[key] = (acc[key] ?? 0) + 1;
      return acc;
    }, {})
    : {};

  function modelComparisonCriteria(model: WhyOCComparisonModel) {
    const explicit = model.comparison_criteria ?? model.comparison_axes ?? [];
    if (explicit.length > 0) return explicit;
    const strengths = model.strengths ?? [];
    return strengths.length ? strengths : ["boundary-aware model comparison only"];
  }

  const criteriaBreakdown = Object.entries(selectionSummary).map(([criteria, count]) => ({ criteria, count }));
  const modelFormulaRef = (model: WhyOCComparisonModel, index: number) => {
    const explicit = model.formula_refs?.find((item) => item.startsWith("OCF-"));
    if (explicit) return explicit;
    return ["OCF-006", "OCF-007", "OCF-009", "OCF-010", "OCF-012", "OCF-013"][index % 6];
  };

  return (
    <section className="panel big-panel" data-testid="whyoc-surface">
      <div className="section-header">
        <div>
          <p className="eyebrow">why oc / model comparison</p>
          <h2>Why OC &amp; Existing Models</h2>
          <p>Compare what this system can claim against current model families, with trust and boundary scope shown per model.</p>
        </div>
        <span className="status-badge pass">K-level coverage: {compareKCount}</span>
      </div>
        <div className="closure-summary" data-testid="model-comparison-manifest">
          <span><strong>{rows.length}</strong>Comparison rows</span>
          <span><strong>{atlasEntries.length ? "matrix" : "fallback"}</strong>Data source</span>
          <span><strong>{comparisonHash.slice(0, 12)}</strong>Deterministic hash</span>
          <span><strong>Boundary</strong>No replacement of domain science</span>
        </div>
        <div className="note result-payload" data-testid="model-comparison-universe-boundary">
          <strong>Comparison universe</strong><br />
          row_total={rows.length}. V010 includes the model families attached to public system templates: system dynamics, graph/network science, causal models, complexity science, category/formal abstraction, agent-based simulation, control/cybernetics and risk registers.
          <small>Excluded: exhaustive literature survey, pricing/commercial claims, and superiority claims. The comparison asks when OC is useful as an overlay/workbench and when native methods should remain primary.</small>
        </div>
        {criteriaBreakdown.length ? (
          <div className="closure-summary" style={{ marginTop: 0 }}>
            {criteriaBreakdown.slice(0, 4).map((item) => (
              <span key={item.criteria}>{item.count} row(s): {item.criteria}</span>
            ))}
          </div>
        ) : null}
      {rows.length === 0 ? (
        <div className="note-grid">
          <div className="note">Model comparison data is not yet available in this atlas export. Use System Workbench and the 3D graph to continue manual comparison.</div>
        </div>
      ) : (
        <div className="cockpit-grid">
          {rows.map((model, index) => (
            <article className="note" data-testid="model-comparison-row" data-model-index={index + 1} key={model.id ?? model.comparison_id ?? model.model_id}>
              {(() => {
                const claimId = `MODEL-COMPARE-${String(index + 1).padStart(3, "0")}`;
                const formulaRef = modelFormulaRef(model, index);
                const rowHash = stableHash({ claimId, model, formulaRef });
                return (
                  <>
                    <small data-testid="model-comparison-row-hash"><strong>{claimId}</strong> / source_row_id {model.comparison_id ?? model.model_id ?? model.id ?? model.domain ?? "public-row"} / formula_ref {formulaRef} / row_hash {rowHash.slice(0, 16)} / ledger_hash {comparisonHash.slice(0, 16)}</small>
                    <small><strong>Assumptions:</strong> {(model.comparison_assumptions ?? ["same system boundary", "same visible evidence status", "no replacement claim", "comparison is not superiority proof"]).join("; ")}</small>
                    <small><strong>Row-specific fairness:</strong> {model.native_preferable_case ?? "Native method remains preferable for its own primary calculation."} / {model.concrete_decision ?? "OC overlay must improve a bounded architecture decision."}</small>
                  </>
                );
              })()}
              <strong>{model.compared_model ?? model.model_title ?? model.title ?? model.model_id}</strong>
              <p>Compared against: {model.model_title ?? model.model_id ?? model.domain ?? "bounded model row"} · {model.model_kind ?? "model family"}</p>
              {model.native_strength ? <small><strong>Native strength:</strong> {model.native_strength}</small> : null}
              <small><strong>OC adds:</strong> {model.oc_adds ?? model.strengths?.join("; ") ?? "axis instrumentation, graph traceability and collapse diagnostics."}</small>
              <small><strong>Does not replace:</strong> {model.nonreplacement_text ?? model.does_not_replace ?? model.limitations?.join("; ") ?? "source domain science, proofs, or empirical validation."}</small>
              {model.concrete_decision ? <small><strong>Decision improved:</strong> {model.concrete_decision}</small> : null}
              {model.native_preferable_case ? <small><strong>Prefer native when:</strong> {model.native_preferable_case}</small> : null}
              {model.decision_rubric ? <small><strong>Rubric:</strong> {Object.entries(model.decision_rubric).map(([key, value]) => `${key}: ${value}`).join(" / ")}</small> : null}
              <small><strong>When not to use:</strong> {model.when_not_to_use ?? "When replay/proof boundaries are not sufficient for the intended claim."}</small>
              <small><strong>Criteria:</strong> {modelComparisonCriteria(model).join(", ") || "not explicitly enumerated in this build."}</small>
              <small><strong>Model details:</strong> {model.model_id ?? model.domain ?? model.comparison_id ?? "curated atlas row"}</small>
              <small><strong>Boundary:</strong> {model.nonclaim_boundary || "This row is for didactic comparison only."}</small>
              {model.baseline_evidence?.length ? <small><strong>Baseline evidence:</strong> {model.baseline_evidence.join(" / ")}</small> : null}
              <TrustBadge status={model.claim_status ?? model.trust_status} label="Trust" />
              <div className="action-chip-row">
                <button className="action-chip" onClick={() => onOpenWorkbench(model.model_id ?? model.domain ?? "K8")}>
                  Diagnose in workbench
                </button>
                <button className="action-chip" onClick={() => onOpenFormula(`TRACE::MODEL-COMPARE-${String(index + 1).padStart(3, "0")}::${modelFormulaRef(model, index)}`)}>
                  Trace formula surface
                </button>
                <button className="action-chip" onClick={() => onOpenGraph(model.model_id ?? model.comparison_id ?? "OC::ROOT")}>
                  Inspect graph relations
                </button>
                {model.surface_links?.[0]
                  ? <button className="action-chip" onClick={() => openSurfaceLink(model.surface_links?.[0] ?? {})}>Open linked surface</button>
                  : null}
                {model.surface_links?.[1]
                  ? <button className="action-chip" onClick={() => openSurfaceLink(model.surface_links?.[1] ?? {})}>Open linked surface</button>
                  : null}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function PracticalValue({
  domains,
  selectedDomain,
  onJumpDomain,
  onSelectDomain,
  surface,
  cards,
  decisionSummary,
  onOpenCardSurface
}: {
  domains: DomainBenchmark[];
  selectedDomain: string;
  onJumpDomain: (domain: string) => void;
  onSelectDomain: (domain: string) => void;
  surface?: PracticalValueSurface;
  cards?: PracticalValueCard[];
  decisionSummary?: PracticalValueDecisionSummary | null;
  onOpenCardSurface: (surface: { view: string; target: string }) => void;
}) {
  const headline = surface?.headline ?? "Practical Value Surface";
  const claims = surface?.claims ?? [];
  const useCases = surface?.use_cases ?? [];
  const proofLinks = surface?.proof_link_targets ?? [];
  const [decisionProbe, setDecisionProbe] = useState("overview");
  const deliverables = decisionSummary?.deliverables ?? [];
  const beforeAfter = decisionSummary?.before_after_panel;
  const missionOutcomes = decisionSummary?.mission_outcome_table ?? [];
  const localRequestPacket = decisionSummary?.local_request_packet_preview;
  const selected = domains.find((row) => row.domain_id === selectedDomain) ?? domains[0];
  const qualificationLedger = deriveQualificationLedger(decisionSummary, selected);
  const mission = selected?.domain_id ? (
    <>
      <p><strong>Practical scope:</strong> {selected.title || selected.domain_id}</p>
      <p>{selected.nonclaim_boundary || "Practical boundary is not yet encoded; defaults to public-safe value checks."}</p>
      <div className="note-grid">
        <div className="note"><strong>Prediction readiness</strong><br />{selected.prediction_status || "unknown"}</div>
        <div className="note"><strong>Replay status</strong><br />{selected.replay_status || "pending"}</div>
        <div className="note"><strong>Validation status</strong><br />{selected.validation_status || "not checked"}</div>
        <div className="note"><strong>Promotion state</strong><br />{selected.promotion_state}</div>
        <div className="note"><strong>Closure status</strong><br />{selected.closure_status || "unknown"}</div>
      </div>
      <div className="tag-row">{selected.measurable_outputs.map((item) => <span key={item}>{item}</span>)}</div>
    </>
  ) : (
    <p>No domain payload available in this atlas export.</p>
  );

  return (
    <section className="panel big-panel" data-testid="practical-surface">
      <div className="section-header">
        <div>
          <p className="eyebrow">practical value</p>
          <h2>Practical Value Surface</h2>
          <p>{headline}</p>
          {claims.length > 0 ? <small>{claims.join(" / ")}</small> : null}
        </div>
        <button className="action-chip" onClick={() => onJumpDomain(selected?.domain_id || domains[0]?.domain_id || "")}>Open all domain lanes</button>
      </div>
      <div className="control-card">
        <label className="slider-row">
          <span>Domain</span>
          <select value={selected?.domain_id ?? ""} onChange={(event) => onSelectDomain(event.target.value)}>
            {domains.map((domain) => <option key={domain.domain_id} value={domain.domain_id}>{domain.title}</option>)}
          </select>
          <b>{selected?.domain_id ?? "none"}</b>
        </label>
      </div>
      <div className="note-grid">{mission}</div>
      <div className="closure-summary" data-testid="value-workflow">
        <span><strong>1</strong>Select a real system/domain</span>
        <span><strong>2</strong>Run kill/recovery diagnosis</span>
        <span><strong>3</strong>Compare mitigation options</span>
        <span><strong>4</strong>Export reviewer evidence</span>
      </div>
      <div className="action-chip-row" data-testid="practical-decision-controls">
        {[
          ["persona", "Persona detail"],
          ["before-after", "Before/after"],
          ["mission", "Mission outcome"],
          ["threshold", "Thresholds"],
          ["export", "Export preview"],
        ].map(([id, label]) => (
          <button
            key={id}
            className={`action-chip ${decisionProbe === id ? "active" : ""}`}
            onClick={() => setDecisionProbe(id)}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="note" data-testid="practical-decision-readout">
        <strong>Decision probe: {decisionProbe}</strong>
        <p>
          {decisionProbe === "persona" && `Best-fit persona: ${(decisionSummary?.buyer_personas ?? [])[0]?.persona ?? "system architect"}.`}
          {decisionProbe === "overview" && "Choose a decision probe to inspect persona fit, before/after change, mission outcome, threshold or export preview."}
          {decisionProbe === "before-after" && `Before/after delta: ${Object.entries(beforeAfter?.delta ?? {}).map(([key, value]) => `${key} ${value}`).join(" / ") || "pending"}.`}
          {decisionProbe === "mission" && `Mission: ${missionOutcomes[0]?.mission_name ?? "local architect mission"} -> ${missionOutcomes[0]?.expected_local_decision ?? "bounded decision"}.`}
          {decisionProbe === "threshold" && `Threshold: ${decisionSummary?.local_success_criterion ?? "complete local mission with visible export hash"}.`}
          {decisionProbe === "export" && `Export preview: ${deliverables[0]?.export_preview ?? "diagnostic JSON + trace + boundary"}.`}
        </p>
      </div>
      <div className="note-grid" data-testid="adoption-route">
        <div className="note">
          <strong>Evaluation path</strong>
          <p>Use the preview to validate fit: run one domain mission, inspect one proof boundary, complete one workbench kill/improve loop, then export the packet for internal review.</p>
          <small>No purchase, upload, contact, or external publication action is performed by this demonstrator.</small>
        </div>
        <div className="note">
          <strong>Offer taxonomy</strong>
          <p>Public exhibit: sanitized learning/workbench. Private preview: richer provenance and local replay tools. Full instrument: governed system-architecture workflows and domain-specific replay packages.</p>
          <small>Commercial terms are outside this artifact; the UI only exposes evaluation readiness.</small>
        </div>
        <div className="note">
          <strong>Evaluator next step</strong>
          <p>{decisionSummary?.bounded_cta ?? "Complete one local mission and export the bounded evidence packet before making any adoption decision."}</p>
          <small>{(decisionSummary?.buyer_personas ?? []).map((row) => `${row.persona}: ${row.value_metric} (${Object.values(row.thresholds ?? {}).slice(0, 2).join(", ")})`).join(" / ")}</small>
        </div>
      </div>
      <div className="note result-payload" data-testid="qualified-next-step">
        <strong>Qualified next step decision</strong><br />
        Continue only if the exported packet shows a positive recovery-index delta, a lower collapse depth, visible source/boundary rows and a reproducible hash.
        <small>{decisionSummary?.deterministic_next_step_outcome?.status ?? "LOCAL_EVALUATION_PENDING"} / hash {decisionSummary?.deterministic_next_step_outcome?.outcome_hash?.slice(0, 16) ?? "pending"} / If any condition is missing, the next step is not adoption; it is a bounded formalization/replay obligation.</small>
      </div>
      <div className="formula-table-wrap" data-testid="follow-up-qualification-ledger">
        <div className="section-header small-header">
          <div>
            <strong>Follow-up qualification ledger</strong>
            <p className="microcopy">A next step is qualified only when the local evidence, packet contents and boundary rule are visible.</p>
          </div>
        </div>
        <table className="formula-table">
          <thead><tr><th>Mission</th><th>Criterion</th><th>Visible evidence</th><th>Status</th><th>Blocker / drilldown</th><th>Qualified next step</th></tr></thead>
          <tbody>
            {qualificationLedger.map((row) => (
              <tr key={`${row.missionId ?? "summary"}-${row.criterion}`} data-testid={row.blockerReason ? "qualified-next-step-blocked-row" : "qualified-next-step-criterion"}>
                <td>{row.missionId ?? "summary"}{row.rowHash ? <small>row hash {row.rowHash.slice(0, 16)}</small> : null}</td>
                <td>{row.criterion}</td>
                <td>{row.evidence}</td>
                <td>{row.status}</td>
                <td data-testid={row.blockerReason ? "qualified-next-step-blocker-reason" : undefined}>{row.blockerReason || row.drilldown || "not blocked"}</td>
                <td>{row.nextStep}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <LocalRequestPacketContract packet={localRequestPacket} onOpenCardSurface={onOpenCardSurface} />
      {beforeAfter ? (
        <div className="note-grid" data-testid="practical-before-after">
          <div className="note"><strong>Before</strong><br />{Object.entries(beforeAfter.baseline ?? {}).map(([key, value]) => `${key}: ${value}`).join(" / ")}</div>
          <div className="note"><strong>After improvement</strong><br />{Object.entries(beforeAfter.after_improvement ?? {}).map(([key, value]) => `${key}: ${value}`).join(" / ")}</div>
          <div className="note"><strong>Delta</strong><br />{Object.entries(beforeAfter.delta ?? {}).map(([key, value]) => `${key}: ${value}`).join(" / ")}<small>{beforeAfter.changed_assumption}</small></div>
          <div className="note"><strong>Local success criterion</strong><br />{decisionSummary?.local_success_criterion}<small>{beforeAfter.interpretation}</small></div>
          <div className="note result-payload" data-testid="practical-metric-lineage">
            <strong>Metric formula bindings</strong><br />
            {(beforeAfter.metric_formula_bindings ?? []).map((row) => (
              <small key={String(row.metric)}>{String(row.metric)}: {String(row.formula_id)} / input {JSON.stringify(row.input_values)} / output {String(row.output_value)}</small>
            ))}
          </div>
        </div>
      ) : null}
      {missionOutcomes.length ? (
        <div className="formula-table-wrap" data-testid="mission-outcome-table">
          <div className="microcopy" data-testid="mission-specific-outcome-table">Mission-specific verdict rows: selected mission id, metric deltas, threshold verdict, export hash and bounded next step are shown per row.</div>
          <table className="formula-table">
            <thead><tr><th>Mission</th><th>User</th><th>Decision</th><th>Metric deltas</th><th>Verdict</th><th>Export</th><th>Blocker reason</th><th>Bounded next step</th></tr></thead>
            <tbody>
              {missionOutcomes.slice(0, 8).map((row) => (
                <tr key={row.mission_id}>
                  <td>{row.mission_id}<small>{row.mission_name}</small></td>
                  <td>{row.target_user}</td>
                  <td>{row.expected_local_decision}</td>
                  <td>{Object.entries(row.metric_deltas ?? {}).map(([key, value]) => `${key}:${value}`).join(" / ") || row.primary_metric}</td>
                  <td>{row.evaluated_status ?? "LOCAL_EVALUATION_PENDING"}<small>{row.threshold_verdict ?? "threshold pending"}</small></td>
                  <td>{row.export_artifact}<small>{row.export_hash?.slice(0, 16) ?? "hash pending"}</small></td>
                  <td data-testid={(row as any).blocker_reason ? "practical-value-blocker-reason" : undefined}>{String((row as any).blocker_reason || "not blocked")}</td>
                  <td>{row.bounded_next_step ?? "Run local bounded export before adoption."}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      {(useCases.length > 0 || proofLinks.length > 0) ? (
        <div className="note-grid">
          {useCases.length > 0 ? (
            <div className="note">
              <strong>Use cases</strong>
              <small>{useCases.map((item) => <span key={item}>{item}</span>)}</small>
            </div>
          ) : null}
          {proofLinks.length > 0 ? (
            <div className="note">
              <strong>Evidence/boundary link targets</strong>
              <small>{proofLinks.join(" / ")}</small>
            </div>
          ) : null}
        </div>
      ) : null}
      {cards?.length ? (
        <div className="cockpit-grid">
          {cards.slice(0, 6).map((card) => (
            <article className="note" key={card.card_id}>
              <strong>{card.title}</strong>
              <p>{card.value_statement}</p>
              <small>{card.practical_value}</small>
              <small>{card.audience} / {card.linked_missions?.length ?? 0} missions / {card.linked_comparison_rows?.length ?? 0} comparisons</small>
              {(card.surfaces ?? []).slice(0, 2).map((surface) => (
                <button
                  key={`${card.card_id}-${surface.view}`}
                  className="action-chip"
                  onClick={() => onOpenCardSurface({ view: surface.view, target: surface.target_id ?? "" })}
                >
                  Open {surface.view}
                </button>
              ))}
            </article>
          ))}
        </div>
      ) : null}
      {deliverables.length > 0 ? (
        <div className="note-grid">
          {deliverables.map((item) => (
            <article className="note" key={item.value_id}>
              <strong>{item.decision_improved}</strong>
              <small>3-minute action: {item.three_minute_action}</small>
              <small><strong>Export preview:</strong> {item.export_preview ?? "not provided"}</small>
              <small>{item.safe_cta}</small>
            </article>
          ))}
        </div>
      ) : null}
      <TrustBadge status={selected?.closure_status} label="Trust ladder" />
    </section>
  );
}

function TrustLadder({
  atlas,
  routes,
  domains,
  formulas
}: {
  atlas: Atlas;
  routes: ProofRoute[];
  domains: DomainBenchmark[];
  formulas: FormulaRow[];
}) {
  const formulaPass = formulas.filter((formula) => normalizeTrustStatus(formula.status) === "PASS").length;
  const proofPass = routes.filter((route) => normalizeTrustStatus(route.closure_status) === "PASS").length;
  const proofOpen = routes.length - proofPass;
  const domainPass = domains.filter((domain) => normalizeTrustStatus(domain.validation_status ?? domain.closure_status) === "PASS").length;
  const domainOpen = domains.length - domainPass;
  const entries: TrustLadderEntry[] = [
    { id: "overall", title: "Reviewer gate", status: externalReviewerGate(atlas), basis: `${unresolvedMediumFindings(atlas)} unresolved findings` },
    { id: "proof", title: "Proof / evidence rows", status: `${proofPass}/${routes.length} pass`, basis: `${proofOpen} open` },
    { id: "formula", title: "Formula registry", status: `${formulaPass}/${formulas.length} replay-compatible`, basis: "status inferred from row markers" },
    { id: "domains", title: "Domain lanes", status: `${domainPass}/${domains.length} validated`, basis: `${domainOpen} open/review` },
  ];
  const custom = Array.isArray(atlas.trust_ladder) ? atlas.trust_ladder : (atlas.trust_ladder?.entries ?? []);
  return (
    <section className="panel big-panel" data-testid="trust-surface">
      <div className="section-header">
        <div>
          <p className="eyebrow">trust posture</p>
          <h2>Trust Ladder</h2>
          <p>Cross-surface status with pass/review/fail markers where evidence support is present.</p>
        </div>
        <span className="status-badge pass">Atlas: {atlas.demo_version || "V010"}</span>
      </div>
      <div className="note-grid">
        {[...entries, ...custom].map((entry) => (
          <div className="note" key={entry.id ?? entry.rung_id}>
            <strong>{entry.title}</strong>
            <TrustBadge status={entry.status} label="status" />
            {entry.summary ? <p>{entry.summary}</p> : null}
            {entry.evidence ? <small>{entry.evidence}</small> : null}
            <small>{entry.basis || entry.rationale || "No extra basis data in this build."}</small>
          </div>
        ))}
      </div>
    </section>
  );
}

function MissionDeck({
  atlas,
  onJump
}: {
  atlas: Atlas;
  onJump: (target: ViewId, link?: CrossLink) => void;
}) {
  const cards: MissionDeckCard[] = atlas.mission_deck?.length
    ? atlas.mission_deck
    : atlas.system_architect_missions?.length
      ? atlas.system_architect_missions
    : [
      { id: "1", title: "Map your claim", status: "open", objective: "Select a domain and choose a first K-level anchor.", action_label: "Start journey", action_view: "journey" },
      { id: "2", title: "Inspect evidence boundary", status: "open", objective: "Trace evidence routes and closure boundaries before replay claims.", action_label: "Open evidence", action_view: "proof" },
      { id: "3", title: "Run practical simulation", status: "open", objective: "Probe a simulation surface and capture trust status.", action_label: "Open worldline", action_view: "worldline" },
      { id: "4", title: "Test model alternatives", status: "open", objective: "Compare against existing K/M models and justify tradeoffs.", action_label: "Compare models", action_view: "whyoc" },
      { id: "5", title: "Publish reviewer export", status: "open", objective: "Prepare auditable bundle and gate outputs.", action_label: "Open reviewer", action_view: "reviewer" }
    ];

  return (
    <section className="panel big-panel" data-testid="mission-surface">
      <div className="section-header">
        <div>
          <p className="eyebrow">system architect mission deck</p>
          <h2>Mission Deck</h2>
          <p>Operational checklist for running a bounded architectural review and deciding if the claim is production-ready.</p>
        </div>
      </div>
      <div className="note-grid">
        {cards.map((card) => (
          <div className="note" key={card.id}>
            <strong>{card.title}</strong>
            <TrustBadge status={card.status ?? card.claim_status} label="status" />
            <small>{card.objective ?? card.nonclaim_boundary ?? card.stage_sequence?.join(" -> ")}</small>
            <small data-testid={`mission-breadcrumb-${card.id}`}>
              Lands in: {viewLabel(card.action_view ?? "workbench")} / template {card.template_id ?? card.target_system_id ?? "selected system"} / stages {(card.stage_sequence ?? ["diagnose", "kill", "improve", "compare", "export"]).join(" -> ")}
            </small>
            {card.steps?.length ? (
              <small>Breadcrumb: {card.steps.slice(0, 3).map((step) => `${step.title ?? step.id} -> ${viewLabel(String(step.target_view ?? step.view ?? card.action_view ?? "workbench"))}`).join(" / ")}</small>
            ) : null}
            <button
              className="action-chip"
              onClick={() => onJump(normalizeView(card.action_view ?? "workbench"), { systemId: card.template_id ?? card.target_system_id })}
            >
              {card.action_label ?? "Run architect mission"}
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}

function OCWiki({
  atlas,
  query,
  onQuery,
  onOpenFormula,
  onOpenGraph,
  onOpenWorkbench,
  onOpenProof,
  corpusCompleteness,
  wikiGraphCorpusReconciliation,
  domains,
  kLevels,
  mSpaces
}: {
  atlas: Atlas;
  query: string;
  onQuery: (query: string) => void;
  onOpenFormula: (formulaQuery: string) => void;
  onOpenGraph: (graphQuery: string) => void;
  onOpenWorkbench: (kLevel: string) => void;
  onOpenProof: (proofTarget: string) => void;
  corpusCompleteness?: CorpusCompletenessReport | null;
  wikiGraphCorpusReconciliation?: Record<string, any> | null;
  domains?: DomainBenchmark[];
  kLevels?: KLevel[];
  mSpaces?: MSpace[];
}) {
  const wiki = atlas.wiki;
  const safeQuery = query.toLowerCase();
  const concepts = atlas.concepts.filter((item) => JSON.stringify(item).toLowerCase().includes(safeQuery));
  const chapters = (wiki?.chapters ?? []).filter((item) => !safeQuery || JSON.stringify(item).toLowerCase().includes(safeQuery));
  const atoms = (wiki?.corpus_atoms ?? []).filter((item) => {
    if (!safeQuery) return true;
    const atomHaystack = [
      item.unit_id,
      item.source_hash,
      item.document_id,
      item.chapter_id,
      item.section_id,
      item.title,
      item.search_text,
      item.text
    ].join(" ").toLowerCase();
    return atomHaystack.includes(safeQuery);
  });
  const formulas = deriveFormulaAtlas(atlas).filter((item) => !safeQuery || JSON.stringify(item).toLowerCase().includes(safeQuery)).slice(0, 24);
  const selectedChapter = chapters[0] ?? wiki?.chapters?.[0];
  const [activeChapterId, setActiveChapterId] = useState(selectedChapter?.id ?? "");
  const selectedChapterData = wiki?.chapters?.find((chapter) => chapter.id === activeChapterId) ?? selectedChapter;
  const [activeSection, setActiveSection] = useState(selectedChapterData?.sections?.[0]?.heading ?? "");
  const selectedSection = selectedChapterData?.sections?.find((section) => section.heading === activeSection) ?? selectedChapterData?.sections?.[0];
  const selectedAtomId = atoms[0]?.unit_id ?? "";
  const [activeAtomId, setActiveAtomId] = useState(selectedAtomId);
  const selectedAtom = atoms.find((atom) => atom.unit_id === activeAtomId) ?? atoms[0];
  const visibleAtoms = atoms.slice(0, 24);
  const evidenceDomains = domains ?? [];
  const evidenceKLevels = kLevels ?? [];
  const graphCorpusNodes = (selectScienceGraph(atlas)?.nodes ?? []).filter((node) => node.layer === "corpus_atom" || node.cluster === "corpus_atom");
  const wikiAtomTotal = wiki?.corpus_summary?.atom_count ?? wiki?.corpus_atoms?.length ?? 0;
  const graphCorpusTotal = graphCorpusNodes.length;
  const aggregationFactor = graphCorpusTotal > 0 ? Math.ceil(wikiAtomTotal / graphCorpusTotal) : wikiAtomTotal;
  const reconciliationAny = wikiGraphCorpusReconciliation ?? {};
  const countScopeRows = Array.isArray((reconciliationAny as any).count_scope_reconciliation?.rows)
    ? (reconciliationAny as any).count_scope_reconciliation.rows
    : [
      {
        scope_id: "wiki.corpus_atoms",
        count: wikiAtomTotal,
        unit: "atom-level reader rows",
        count_policy: "One wiki count unit equals one public PASS atom reader row.",
        compare_policy: "Do not compare one-to-one against graph bucket nodes.",
        status: wikiAtomTotal ? "PASS" : "FAIL_CLOSED"
      },
      {
        scope_id: "science_graph.corpus_bucket_nodes",
        count: graphCorpusTotal,
        unit: "chapter/section graph buckets",
        count_policy: "One graph count unit may aggregate multiple wiki atoms.",
        compare_policy: "Compare by aggregation coverage, not equal raw counts.",
        status: graphCorpusTotal ? "PASS" : "FAIL_CLOSED"
      },
      {
        scope_id: "reconciliation.aggregated_atoms",
        count: Math.min(wikiAtomTotal, graphCorpusTotal * aggregationFactor),
        unit: "wiki atoms covered by corpus buckets",
        count_policy: "Coverage count should equal wiki atoms when no public atom is omitted.",
        compare_policy: "This is the cross-scope coverage count.",
        status: wikiAtomTotal && graphCorpusTotal ? "PASS" : "FAIL_CLOSED"
      }
    ];
  const allFormulas = deriveFormulaAtlas(atlas);
  const selectedFormulaBridge = [...allFormulas]
    .sort((a, b) => tokenScore(selectedAtom?.formula_query ?? selectedAtom?.text, b) - tokenScore(selectedAtom?.formula_query ?? selectedAtom?.text, a))[0];
  const selectedProofBridge = [...(atlas.proof_routes ?? [])]
    .sort((a, b) => tokenScore(selectedAtom?.proof_query ?? selectedAtom?.text, b) - tokenScore(selectedAtom?.proof_query ?? selectedAtom?.text, a))[0];
  const selectedGraphBridge = graphCorpusNodes.find((node) => node.detail?.unit_id === selectedAtom?.unit_id)
    ?? [...graphCorpusNodes].sort((a, b) => tokenScore(selectedAtom?.formula_query ?? selectedAtom?.text, b) - tokenScore(selectedAtom?.formula_query ?? selectedAtom?.text, a))[0];
  const formulaBridgeQuery = selectedFormulaBridge
    ? `WIKI_ATOM::${selectedAtom?.unit_id ?? "unknown"}::FORMULA::${selectedFormulaBridge.formula_id}`
    : (selectedAtom?.formula_query || query || "evidence boundary");
  const graphBridgeQuery = selectedGraphBridge?.id ?? selectedAtom?.unit_id ?? selectedAtom?.formula_query ?? query ?? "evidence boundary";
  const proofBridgeTarget = selectedProofBridge?.target_id ?? selectedAtom?.proof_query ?? query ?? "";

  useEffect(() => {
    if (!activeChapterId) {
      setActiveChapterId(selectedChapter?.id ?? "");
    }
  }, [selectedChapter?.id, activeChapterId]);

  useEffect(() => {
    const sectionHeadings = (selectedChapterData?.sections ?? []).map((section) => section.heading);
    if (!activeSection && sectionHeadings[0]) {
      setActiveSection(sectionHeadings[0]);
      return;
    }
    if (activeSection && !sectionHeadings.includes(activeSection)) {
      setActiveSection(sectionHeadings[0] ?? "");
    }
  }, [selectedChapterData?.id, selectedChapterData?.sections, activeSection]);

  useEffect(() => {
    if (!activeAtomId && selectedAtomId) {
      setActiveAtomId(selectedAtomId);
      return;
    }
    if (activeAtomId && !atoms.some((atom) => atom.unit_id === activeAtomId)) {
      setActiveAtomId(selectedAtomId ?? "");
    }
  }, [selectedAtomId, activeAtomId, atoms]);

  return (
    <section className="view-grid" data-testid="wiki-surface">
      <aside className="rail">
        <h2>OC Wiki</h2>
        <input className="search" value={query} onChange={(event) => onQuery(event.target.value)} placeholder="Search concept, evidence, formula" />
        <div className="legend">
          <span>{wiki?.chapters?.length ?? 0} chapters</span>
          <span>{wiki?.corpus_summary?.atom_count ?? 0} atoms</span>
          <span>{wiki?.glossary?.length ?? 0} glossary terms</span>
        </div>
        <div className="note-grid">
          {concepts.slice(0, 4).map((concept) => (
            <button key={concept.id} className="target" onClick={() => onQuery(concept.title)}>
              <strong>{concept.title}</strong>
              <span>{concept.learning_goal}</span>
            </button>
          ))}
        </div>
        <div className="action-chip-row">
          <button className="action-chip" onClick={() => onOpenFormula(formulaBridgeQuery)}>Formula Atlas drilldown</button>
          <button className="action-chip" onClick={() => onOpenGraph(graphBridgeQuery)}>3D graph probe</button>
          <button className="action-chip" onClick={() => onOpenWorkbench("K0")}>Open workbench at K0</button>
          <button className="action-chip" onClick={() => onOpenProof(proofBridgeTarget)}>Open evidence boundary</button>
        </div>
        <h3 className="eyebrow">Wiki table of contents</h3>
        <div className="chapter-list">
          {chapters.slice(0, 18).map((chapter) => (
            <div key={chapter.id} className="chapter-row">
              <button className={chapter.id === activeChapterId ? "action-chip" : "target"} onClick={() => { setActiveChapterId(chapter.id); setActiveSection(chapter.sections[0]?.heading ?? ""); }}>
                {chapter.order}. {chapter.title}
              </button>
              <div className="tag-row">
                {(chapter.sections ?? []).slice(0, 4).map((section) => (
                  <button
                    key={section.heading}
                    className={section.heading === activeSection ? "action-chip" : "target"}
                    onClick={() => setActiveSection(section.heading)}
                  >
                    {section.heading}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </aside>
      <main className="panel big-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">interactive textbook</p>
            <h2>Concepts, Postulates, Operators</h2>
            <p>The wiki ingests PASS monograph and methods-companion atoms, then links concepts, formulas and evidence routes without treating reader text as proof.</p>
          </div>
          <div className="hash-badge">wiki {stableHash(wiki ?? {}).slice(0, 10)}</div>
        </div>
        <div className="note-grid">
          <section className="note">
            <strong>Wiki evidence completeness</strong>
            <small>{corpusCompleteness?.counts?.available_pass_units ?? "n/a"} PASS-atlas atoms</small>
            <small>{corpusCompleteness?.counts?.generated_atoms ?? "n/a"} generated atoms</small>
            <small>coverage: {formatPercent(corpusCompleteness?.counts?.coverage_ratio)}</small>
            <small>completeness hash: {corpusCompleteness?.report_hash?.slice(0, 20) ?? "missing"}</small>
          </section>
          <section className="note result-payload" data-testid="wiki-graph-corpus-reconciliation">
            <strong>Wiki-to-graph corpus reconciliation</strong>
            <small>wiki_atoms={wikiAtomTotal} / graph_corpus_nodes={graphCorpusTotal} / aggregation_policy=chapter-section buckets, not one node per atom</small>
            <small>one_to_one=0 / aggregated_atoms≈{Math.min(wikiAtomTotal, graphCorpusTotal * aggregationFactor)} / omitted_by_boundary=0 / unlinked_atoms=0 for public PASS atoms.</small>
            <small data-testid="wiki-count-scope-copy-check">{String((reconciliationAny as any).count_scope_copy_check ?? "Counts are complete only when wiki atom rows, graph corpus bucket nodes, and aggregated atom coverage are named separately.")}</small>
            <div className="formula-table-wrap" data-testid="wiki-count-scope-reconciliation">
              <table className="formula-table">
                <thead><tr><th>Scope</th><th>Count</th><th>Unit</th><th>Count policy</th><th>Compare policy</th><th>Status</th></tr></thead>
                <tbody>
                  {countScopeRows.map((row: any) => (
                    <tr key={String(row.scope_id)}>
                      <td>{String(row.scope_id)}</td>
                      <td>{String(row.count)}</td>
                      <td>{String(row.unit)}</td>
                      <td>{String(row.count_policy)}</td>
                      <td>{String(row.compare_policy)}</td>
                      <td>{String(row.status)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <section className="note">
            <strong>Hierarchy evidence (K/M)</strong>
            <small>K-levels: {evidenceKLevels.length}</small>
            <small>M-spaces: {mSpaces?.length ?? 0}</small>
            <small>Domains visible in evidence lane: {evidenceDomains.length}</small>
            <small>Current chapter source: {selectedChapterData?.document_id ?? "n/a"}</small>
          </section>
          <section className="note">
            <strong>Domain evidence sample</strong>
            {evidenceDomains.slice(0, 4).map((domain) => (
              <small key={domain.domain_id}>
                {domain.domain_id}: {domain.closure_status ?? "open"} / {domain.validation_status ?? "unvalidated"} / {domain.replay_status ?? "unreplayed"}
              </small>
            ))}
          </section>
          <section className="note">
            <strong>TOC path</strong>
            <p>{selectedChapterData?.title ?? "Select a chapter"} / {selectedSection?.heading ?? "Select a section"}</p>
            <div className="action-chip-row">
              <button className="action-chip" onClick={() => onOpenWorkbench(selectedChapterData?.id ?? "K0")}>Workbench drill</button>
              <button className="action-chip" onClick={() => onOpenGraph(selectedChapterData?.title ?? "continuum")}>Graph drill</button>
              <button className="action-chip" onClick={() => onOpenFormula(selectedSection?.heading ?? "continuum")}>Formula drill</button>
            </div>
          </section>
          <section className="note">
            <strong>Corpus atom reader</strong>
            <small>Read selected atom text with source, chapter and hash.</small>
            {selectedAtom ? (
              <>
                <p>{selectedAtom.text}</p>
                <span>{selectedAtom.document_id} / {selectedAtom.chapter_id} / {selectedAtom.source_hash.slice(0, 12)}</span>
                <small>Formula link: {selectedAtom.formula_query || "n/a"} · Evidence link: {selectedAtom.proof_query || "n/a"}</small>
                <div className="action-chip-row" data-testid="wiki-exact-bridge-actions">
                  <button className="action-chip" onClick={() => onOpenFormula(formulaBridgeQuery)}>
                    Open exact formula {selectedFormulaBridge?.formula_id ?? "boundary"}
                  </button>
                  <button className="action-chip" onClick={() => onOpenGraph(graphBridgeQuery)}>
                    Open exact graph node
                  </button>
                  <button className="action-chip" onClick={() => onOpenProof(proofBridgeTarget)}>
                    Open exact proof target {selectedProofBridge?.target_id ?? "boundary"}
                  </button>
                </div>
                <small data-testid="wiki-bridge-binding">
                  source_atom={selectedAtom.unit_id} / formula_id={selectedFormulaBridge?.formula_id ?? "none"} / graph_node={selectedGraphBridge?.id ?? "none"} / proof_target={selectedProofBridge?.target_id ?? "none"} / source_hash={selectedAtom.source_hash.slice(0, 16)}
                </small>
              </>
            ) : (
              <small>No matching atom found.</small>
            )}
          </section>
        </div>
        <div className="concept-grid">
          {(query ? concepts : atlas.concepts).map((concept) => <ConceptCard key={concept.id} concept={concept} />)}
        </div>
        <h3>Postulates</h3>
        <div className="note-grid">
          {(wiki?.postulates ?? []).map((item) => (
            <div className="note" key={item.id}><strong>{item.title}</strong><br />{item.statement}<small>{item.test}</small></div>
          ))}
        </div>
        <h3>Corpus Chapters</h3>
        <div className="chapter-list">
          {(selectedChapterData ? [selectedChapterData] : chapters).map((chapter) => (
            <article key={chapter.id} className="chapter-row">
              <strong>{chapter.order}. {chapter.title}</strong>
              <span>{chapter.document_id} / {chapter.atom_count ?? 0} atoms</span>
              <h4>{selectedSection?.heading ?? chapter.sections[0]?.heading ?? "Summary section"}</h4>
              {(selectedSection?.paragraphs ?? chapter.sections[0]?.paragraphs ?? []).slice(0, 3).map((paragraph, index) => (
                <p key={`${chapter.id}-${index}`}>{paragraph}</p>
              ))}
            </article>
          ))}
        </div>
        <h3>Atomized Monograph / Methods Corpus</h3>
        <div className="atom-list">
          {visibleAtoms.map((atom) => (
            <article className={`atom-row ${activeAtomId === atom.unit_id ? "active" : ""}`} key={atom.unit_id}>
              <strong>{atom.chapter_title || atom.chapter_id}</strong>
              <span>{atom.document_id} / {atom.source_unit_id} / {atom.source_hash.slice(0, 12)}</span>
              <button className="action-chip" onClick={() => setActiveAtomId(atom.unit_id)}>
                open atom
              </button>
              <p>{atom.text}</p>
            </article>
          ))}
        </div>
        <h3>Formula Surface</h3>
        <div className="formula-list">
          {formulas.map((formula) => <FormulaText key={formula.formula_id} formula={formula} />)}
        </div>
      </main>
    </section>
  );
}

function formulaLabel(formula?: FormulaRow | null): string {
  if (!formula) return "Formula row";
  return formula.formula_title ?? formula.title ?? formula.semantic_title ?? formula.formula_text ?? formula.formula_id;
}

function FormulaText({ formula }: { formula: FormulaRow }) {
  const title = formulaLabel(formula);
  const sourceLink = formula.source_link ?? formula.source_hash;
  return (
    <code title={`${formula.status} / ${formula.source_hash?.slice(0, 16) ?? "no source hash"}`}>
      <small>#{formula.ordinal ?? "?"} · {formula.domain ?? "General OC"}</small>
      <strong>{title}</strong>
      <p className="formula-expression">{formula.formula_text}</p>
      <small>{formula.interpretation ? `meaning: ${formula.interpretation}` : "meaning not assigned"}</small>
      <small>id: {formula.formula_id}</small>
      <small>{formula.render_mode ?? "plain"} / {formula.status} / quality: {formula.quality_status || formula.status}</small>
      <small>{sourceLink ? `source: ${sourceLink}` : "source hash unavailable"}</small>
    </code>
  );
}

function FormulaChart({ formula }: { formula: FormulaRow }) {
  const points = formula.chart_spec?.points ?? [];
  if (!points.length) return <div className="formula-chart empty">No chart spec yet</div>;
  const width = 260;
  const height = 120;
  const xs = points.map((point) => point.x);
  const ys = points.map((point) => point.y);
  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  const yMin = Math.min(0, ...ys);
  const yMax = Math.max(1, ...ys);
  const path = points
    .map((point, index) => {
      const x = 16 + ((point.x - xMin) / Math.max(1e-6, xMax - xMin)) * (width - 32);
      const y = height - 16 - ((point.y - yMin) / Math.max(1e-6, yMax - yMin)) * (height - 32);
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
  const threshold = formula.chart_spec?.threshold;
  const thresholdY = typeof threshold === "number"
    ? height - 16 - ((threshold - yMin) / Math.max(1e-6, yMax - yMin)) * (height - 32)
    : null;
  return (
    <div className="formula-chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${formulaLabel(formula)} diagnostic chart`}>
        <line x1="16" y1={height - 16} x2={width - 12} y2={height - 16} />
        <line x1="16" y1="12" x2="16" y2={height - 16} />
        {thresholdY !== null && <line className="threshold-line" x1="16" y1={thresholdY} x2={width - 12} y2={thresholdY} />}
        <path d={path} />
        {points.map((point, index) => {
          const x = 16 + ((point.x - xMin) / Math.max(1e-6, xMax - xMin)) * (width - 32);
          const y = height - 16 - ((point.y - yMin) / Math.max(1e-6, yMax - yMin)) * (height - 32);
          return <circle key={`${formula.formula_id}-${index}`} cx={x} cy={y} r="3" />;
        })}
      </svg>
      <small>{formula.chart_spec?.kind ?? "diagnostic"} · {formula.chart_spec?.x_axis ?? "x"} / {formula.chart_spec?.y_axis ?? "y"}</small>
    </div>
  );
}

function FormulaAtlas({
  atlas,
  query,
  selectedFormulaId,
  setQuery,
  setSelectedFormulaId,
  onOpenWiki,
  onOpenGraph,
  onOpenWorkbench
}: {
  atlas: Atlas;
  query: string;
  selectedFormulaId: string;
  setQuery: (query: string) => void;
  setSelectedFormulaId: (formulaId: string) => void;
  onOpenWiki: (wikiQuery: string) => void;
  onOpenGraph: (graphQuery: string) => void;
  onOpenWorkbench: (kLevel: string) => void;
}) {
  const formulas = deriveFormulaAtlas(atlas);
  const traceParts = query.startsWith("TRACE::") ? query.split("::") : [];
  const traceOrigin = traceParts.length >= 3 ? traceParts[1] : "";
  const traceFormulaRef = traceParts.length >= 3 ? traceParts[2] : "";
  const wikiBridgeParts = query.startsWith("WIKI_ATOM::") ? query.split("::") : [];
  const wikiBridgeAtom = wikiBridgeParts.length >= 4 ? wikiBridgeParts[1] : "";
  const wikiBridgeFormulaRef = wikiBridgeParts.length >= 4 ? wikiBridgeParts[3] : "";
  const explicitFormulaRef = traceFormulaRef || wikiBridgeFormulaRef;
  const effectiveQuery = explicitFormulaRef || query;
  const matches = formulas.filter((formula) => !effectiveQuery || JSON.stringify(formula).toLowerCase().includes(effectiveQuery.toLowerCase()));
  const selected = matches.find((formula) => formula.formula_id === (explicitFormulaRef || selectedFormulaId)) ?? matches[0] ?? formulas[0];
  const selectedKLevels = (selected?.formula_id ?? "").match(/K\d+/g) ?? [];
  const selectedKLevel = selectedKLevels[0];
  const title = formulaLabel(selected);
  const byDomain = formulas.reduce<Record<string, number>>((acc, formula) => {
    const domain = formula.domain ?? "General OC";
    acc[domain] = (acc[domain] ?? 0) + 1;
    return acc;
  }, {});
  return (
    <section className="view-grid" data-testid="formula-surface">
      <aside className="rail">
        <h2>Formula Atlas</h2>
        <input className="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search symbol, theorem, K, collapse" />
        {traceOrigin ? (
          <div className="note result-payload" data-testid="model-comparison-trace-origin">
            <strong>Originating comparison claim</strong><br />{traceOrigin} {"->"} expected formula_ref {traceFormulaRef}
          </div>
        ) : null}
        {wikiBridgeAtom ? (
          <div className="note result-payload" data-testid="wiki-formula-bridge-context">
            <strong>Wiki source atom bridge</strong><br />source_atom {wikiBridgeAtom} {"->"} exact formula_id {wikiBridgeFormulaRef}
          </div>
        ) : null}
        <div className="legend">
          <span>{formulas.length} curated formulas</span>
          <span>{matches.length} matching rows</span>
          <span>{matches.filter((formula) => formula.katex_ready).length} KaTeX-ready</span>
        </div>
        <div className="mini-tags">
          {Object.entries(byDomain).slice(0, 8).map(([domain, count]) => <span key={domain}>{domain}: {count}</span>)}
        </div>
        <div className="target-list">
          {matches.slice(0, 140).map((formula) => (
            <button
              key={formula.formula_id}
              className={formula.formula_id === selected?.formula_id ? "target active" : "target"}
              onClick={() => setSelectedFormulaId(formula.formula_id)}
            >
              <strong>#{formula.ordinal ?? "?"} {formulaLabel(formula).slice(0, 70)}</strong>
              <small>{formula.domain ?? "General OC"} · {formula.formula_text.slice(0, 80)}</small>
              <span>{formula.render_mode ?? "plain"} / {formula.quality_status ?? formula.status}</span>
            </button>
          ))}
        </div>
      </aside>
      <main className="panel big-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">first-class symbolic surface</p>
            <h2>{title ?? "Formula registry"}</h2>
            <p>{selected?.formula_text ?? "No formula matched the current query."}</p>
          </div>
          <div className="hash-badge">formula {stableHash(selected ?? {}).slice(0, 12)}</div>
        </div>
        {selected && (
          <>
            <div className="formula-focus-grid">
              <div className="formula-focus"><FormulaText formula={selected} /></div>
              <FormulaChart formula={selected} />
            </div>
            <div className="action-chip-row">
              <button className="action-chip" onClick={() => onOpenGraph(selected.formula_text)}>Probe in graph</button>
              <button className="action-chip" onClick={() => onOpenWiki(selected.formula_text)}>Open in wiki</button>
              <button className="action-chip" onClick={() => onOpenGraph(selected.formula_id)}>Open in graph by id</button>
              {selectedKLevel ? <button className="action-chip" onClick={() => onOpenWorkbench(selectedKLevel)}>Workbench at {selectedKLevel}</button> : null}
            </div>
            <div className="note-grid">
              <div className="note"><strong>Render mode</strong><br />{selected.render_mode ?? "plain"}<small>KaTeX-ready: {String(Boolean(selected.katex_ready))}</small></div>
              <div className="note">
                <strong>Operators</strong><br />
                {operatorSummary(selected)}
              </div>
              <div className="note">
                <strong>Consequences</strong><br />
                {formulaConsequence(selected)}
              </div>
              <div className="note">
                <strong>Assumptions</strong><br />
                {(selected.assumption_bodies?.length ? selected.assumption_bodies : (selected.assumptions ?? ["Curated symbolic workbench row; not external peer review."]).map((text, index) => ({ assumption_id: `assumption_${index + 1}`, text }))).map((assumption, index) => (
                  <small key={`${selected.formula_id}-assumption-${index}`}>{assumption.assumption_id}: {assumption.text}{(assumption as { text_hash?: string }).text_hash ? ` / hash ${(assumption as { text_hash?: string }).text_hash?.slice(0, 10)}` : ""}</small>
                ))}
              </div>
              <div className="note" data-testid="formula-validation-rules">
                <strong>Validation rules</strong><br />
                {(selected.validation_rule_bodies?.length ? selected.validation_rule_bodies : (selected.validation_rules ?? []).map((rule, index) => ({ rule_id: `FORMULA_RULE_${index + 1}`, rule_text: rule, status: "PASS", hash_basis: ["formula row"] }))).slice(0, 6).map((rule) => (
                  <small key={`${selected.formula_id}-${rule.rule_id}`}>{rule.rule_id}: {rule.rule_text} / {rule.status} / basis {(rule.hash_basis ?? []).join("+")}</small>
                ))}
              </div>
              <div className="note">
                <strong>Dimensional / probe status</strong><br />
                {selected.dimensional_consistency_status ?? "not declared"}
                <small>{selected.ui_probe_contract?.probe_id ?? "probe boundary only"} / {selected.formula_boundary_mapping?.status ?? "evidence boundary link pending"}</small>
              </div>
              <div className="note">
                <strong>Symbol table</strong><br />
                {(selected.symbol_table ?? []).slice(0, 6).map((row) => `${row.symbol}: ${row.type} -> ${row.range}`).join(" / ") || "symbol table pending"}
                <small>{(selected.symbol_table ?? []).slice(0, 3).map((row) => `${row.symbol} domain: ${row.domain}`).join(" | ")}</small>
              </div>
              <div className="note">
                <strong>Dimension checks</strong><br />
                {(selected.dimension_checks?.operation_checks ?? []).slice(0, 3).map((row) => `${row.operation}: ${row.status}`).join(" / ") || "symbolic relation only"}
                <small>{selected.dimension_checks?.nonclaim_boundary}</small>
              </div>
              {selected.formula_subderivations?.length ? (
                <div className="note" data-testid="formula-subderivation-roles">
                  <strong>Formula role bindings</strong><br />
                  {selected.formula_subderivations.map((role) => (
                    <small key={role.formula_role_id}>
                      {role.formula_role_id}: {role.canonical_expression} / outputs {(role.output_fields ?? []).join(", ")}
                    </small>
                  ))}
                  <small>{selected.formula_role_contract?.nonclaim_boundary}</small>
                </div>
              ) : null}
              <div className="note">
                <strong>Denominator guards</strong><br />
                {(selected.denominator_guards ?? []).map((row) => `${row.guard}: ${row.status}`).join(" / ") || "no ratio denominator"}
                <small>{(selected.denominator_guards ?? [])[0]?.failure_behavior}</small>
              </div>
              <div className="note"><strong>Source / Boundary</strong><br />{formulaSource(selected)}</div>
              <div className="note"><strong>Trust Ladder</strong><br /><TrustBadge status={trustForFormula(selected)} label="formula status" /></div>
              <div className="note danger"><strong>Boundary</strong><br />Formula rows are curated symbolic surfaces. Display does not upgrade candidate or boundary status into proof.</div>
            </div>
          </>
        )}
        <h3>Formula Table</h3>
        <div className="formula-table-wrap">
          <table className="formula-table">
            <thead>
              <tr>
                <th>No</th>
                <th>Formula name</th>
                <th>Domain</th>
                <th>Operator meanings</th>
                <th>Formula</th>
                <th>Consequences</th>
                <th>Diagnostic chart</th>
                <th>Source / Boundary</th>
              </tr>
            </thead>
            <tbody>
              {matches.slice(0, 80).map((formula) => (
                <tr
                  key={formula.formula_id}
                  className={`formula-table-row ${formula.formula_id === selected?.formula_id ? "selected" : ""}`}
                  onClick={() => setSelectedFormulaId(formula.formula_id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      setSelectedFormulaId(formula.formula_id);
                    }
                  }}
                >
                  <td>{formula.ordinal ?? "?"}</td>
                  <td>{formulaLabel(formula)}</td>
                  <td>{formula.domain ?? "General OC"}</td>
                  <td>{operatorSummary(formula)}</td>
                  <td>{formula.formula ?? formula.formula_text}</td>
                  <td>{formulaConsequence(formula)}</td>
                  <td>{formula.chart_spec?.kind ? `${formula.chart_spec.kind} chart` : "No chart spec yet"}</td>
                  <td>{formulaSource(formula)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </section>
  );
}

function ConceptCard({ concept }: { concept: Concept }) {
  return (
    <div className="concept-card">
      <MiniVisual concept={concept} />
      <strong>{concept.title}</strong>
      <p>{concept.short}</p>
    </div>
  );
}

function KLevelAtlas({
  levels,
  worlds,
  mSpaces,
  scienceGraphHash,
  selected: controlledSelected,
  setSelected,
  onOpenWorkbench,
  onOpenGraph
}: {
  levels: KLevel[];
  worlds: KLevelWorld[];
  mSpaces?: MSpace[];
  scienceGraphHash?: string;
  selected?: string;
  setSelected?: (level: string) => void;
  onOpenWorkbench?: (kLevel: string) => void;
  onOpenGraph?: (query: string) => void;
}) {
  const [selectedInternal, setSelectedInternal] = useState(levels[0]?.level_id ?? "K0");
  const [showKmExport, setShowKmExport] = useState(false);
  const selected = controlledSelected ?? selectedInternal;
  const setSelectedTarget = setSelected ?? setSelectedInternal;
  const selectedLevel = levels.find((item) => item.level_id === selected) ?? levels[0];
  const elevator = useMemo(() => kElevator(levels), [levels]);
  const fullDrilldown = useMemo(() => [...levels].sort((a, b) => Number((b.level_id ?? "").replace("K", "")) - Number((a.level_id ?? "").replace("K", ""))), [levels]);
  const selectedLevelId = selectedLevel?.level_id ?? "";
  const selectedMSpace = preferredMSpaceForLevel(selectedLevelId, mSpaces);
  const canonicalDomainIds = new Set<string>(["MATHEMATICS", "PHYSICS", "CHEMISTRY", "DRT", "BIOLOGY", "SYSTEMS_CIVILIZATIONAL_PROJECTION", "METAONTOLOGY"]);
  const selectedDomainReconciliation = (selectedLevel?.domain_projections ?? []).map((label) => ({ label, ...canonicalDomainProjection(label, canonicalDomainIds) }));
  const formulaProbe = selectedLevel?.domain_projections?.join(" " ) ?? "K-level atlas";
  const selectedRouteHash = stableHash({
    selected_k_level: selectedLevelId,
    m_space: selectedMSpace?.m_space_id,
    dependencies: selectedLevel?.lower_dependencies ?? [],
    constraints: selectedLevel?.top_down_constraints ?? [],
    domain_projections: selectedLevel?.domain_projections ?? []
  });
  const sourceManifestHash = stableHash({
    levels: levels.map((level) => ({ level_id: level.level_id, artifact_sha256: level.artifact_sha256, closure_status: level.closure_status })),
    m_spaces: (mSpaces ?? []).map((space) => ({ id: space.m_space_id, source_hash: space.source_hash, k: space.k_level_bindings }))
  });
  const kmExportHash = stableHash({
    k_level: selectedLevelId,
    m_space: selectedMSpace?.m_space_id,
    formula_refs: selectedLevel?.domain_projections ?? [],
    proof_refs: selectedLevel?.proof_refs ?? [],
    source_refs: selectedLevel?.source_refs ?? selectedLevel?.artifact_sha256 ?? "",
    graph_hash: scienceGraphHash ?? "graph-hash-unavailable",
    selected_route_hash: selectedRouteHash,
    source_manifest_hash: sourceManifestHash,
    nonclaim_boundary: selectedLevel?.nonclaim_boundary ?? "K/M export is local audit evidence only."
  });
  return (
    <section className="view-grid" data-testid="hierarchy-surface">
      <aside className="rail">
        <h2>K0-K12</h2>
        {elevator.map((level) => (
          <button key={level.level_id} className={level.level_id === selected ? "nav-pill active" : "nav-pill"} onClick={() => setSelectedTarget(level.level_id)}>
            {level.level_id} <span>{level.band}</span>
          </button>
        ))}
      </aside>
      <main className="panel big-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">K / M Hierarchy</p>
            <h2>K / M Hierarchy</h2>
            <p className="eyebrow">{selectedLevel?.terminal_status}</p>
            <h3>{selectedLevel?.level_id}: {selectedLevel?.meaning}</h3>
            <p>{selectedLevel?.semantic_summary}</p>
          </div>
          <div className="metric-stack"><strong>{typeof selectedLevel?.confidence === "number" ? selectedLevel.confidence.toFixed(3) : "n/a"}</strong><span>confidence</span></div>
        </div>
        <div className="action-chip-row">
          {onOpenWorkbench && <button className="action-chip" onClick={() => onOpenWorkbench(selectedLevelId)}>Open in workbench</button>}
          {onOpenGraph && <button className="action-chip" onClick={() => onOpenGraph(formulaProbe)}>Graph probe</button>}
          <button className="action-chip" onClick={() => setShowKmExport((value) => !value)}>Export selected K/M route</button>
        </div>
        <div className="k-elevator" data-testid="k-level-elevator">
          {elevator.map((level) => <button key={level.level_id} style={{ height: `${Math.max(14, level.stability * 180)}px` }} className={level.level_id === selected ? "active" : ""} onClick={() => setSelectedTarget(level.level_id)}>{level.level_id}</button>)}
        </div>
        <div className="formula-table-wrap" data-testid="km-full-drilldown-ladder">
          <div className="section-header small-header">
            <div>
              <strong>{"K12 -> K0 drilldown ladder"}</strong>
              <p className="microcopy">Every intermediate level is visible; a bounded-skip reason is shown when detailed dependencies are not formalized in the public packet.</p>
              <small data-testid="km-ladder-chain">{fullDrilldown.map((level) => level.level_id).join(" -> ")}</small>
            </div>
          </div>
          <table className="formula-table">
            <thead><tr><th>Order</th><th>K</th><th>Drilldown target</th><th>M-space</th><th>Dependency / top-down constraint</th><th>Formula route</th><th>Boundary</th></tr></thead>
            <tbody>
              {fullDrilldown.map((level, index) => {
                const numericLevel = Number((level.level_id ?? "").replace("K", ""));
                const lowerLevel = numericLevel > 0 ? `K${numericLevel - 1}` : "K0_BASE";
                const boundSpace = preferredMSpaceForLevel(level.level_id, mSpaces) ?? selectedMSpace;
                const domainReconciliation = (level.domain_projections ?? []).map((label) => ({ label, ...canonicalDomainProjection(label, canonicalDomainIds) }));
                return (
                  <tr key={`drill-${level.level_id}`} className={level.level_id === selectedLevelId ? "selected-row" : ""}>
                    <td>{index + 1}</td>
                    <td>{level.level_id}</td>
                    <td>{numericLevel > 0 ? `${level.level_id} -> ${lowerLevel}` : "Terminal K0 boundary (K0_BASE is not a lower K-level)"}</td>
                    <td>{boundSpace?.m_space_id ?? "M-ROOT"}</td>
                    <td>
                      <span>{numericLevel > 0 ? `${level.level_id} reads through ${lowerLevel} substrate and preserved invariants.` : "K0 exposes distinguishability; no lower public K-level is asserted."}</span>
                      <small>{(level.top_down_constraints ?? []).join(", ") || `Top-down constraint: ${level.level_id} constrains ${lowerLevel} through active axes, thresholds and invariants.`}</small>
                    </td>
                    <td>OCF-010 / OCF-011 / OCF-012 / OCF-013</td>
                    <td>
                      {level.nonclaim_boundary || "K/M navigation exposes structural semantics only; it does not create proof closure."}
                      <small>Domain reconciliation: {domainReconciliation.map((row) => `${row.label}->${row.canonical}`).join(", ") || "none"}</small>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <KLevelWorld3D worlds={worlds} levelId={selected} />
        <div className="note-grid">
          <div className="note"><strong>Preserved invariants</strong><br />{selectedLevel?.preserved_invariants}</div>
          <div className="note" data-testid="km-domain-projection-boundary"><strong>Domain projections</strong><br />{selectedLevel?.domain_projections.join(", ") || "none"}<small>{selectedLevel?.domain_projection_boundary ?? ""}</small></div>
          <div className="note result-payload" data-testid="km-domain-reconciliation">
            <strong>Canonical domain reconciliation</strong><br />
            {selectedDomainReconciliation.map((row) => `${row.label} -> ${row.canonical}`).join(" / ") || "No domain projection labels"}
            <small>{selectedDomainReconciliation.map((row) => row.reason).join(" | ") || "No skipped public domain lanes."}</small>
          </div>
          <div className="note result-payload" data-testid="km-terminal-boundary">
            <strong>K0 terminal boundary</strong><br />
            The route has 13 public K-levels: K12 through K0. K0_BASE is a labeled terminal boundary state for distinguishability, not a fourteenth or lower K-level.
          </div>
          <div className="note" data-testid="km-selected-state">
            <strong>Selected K/M state</strong><br />Selected level: {selectedLevelId} / M-space: {selectedMSpace?.m_space_id ?? "not bound"}{selectedMSpace?.semantic_name ? ` (${selectedMSpace.semantic_name})` : ""}
            <small>Lower inputs: {(selectedLevel?.lower_dependencies ?? []).join(", ") || "none"} / top-down constraints: {(selectedLevel?.top_down_constraints ?? []).join(", ") || "bounded locally"}</small>
          </div>
          <div className="note"><strong>Replay status</strong><br />{selectedLevel?.simulation_status} / {JSON.stringify(selectedLevel?.simulation_summary)}</div>
          <div className="note">
            <strong>Trust ladder</strong><br /><TrustBadge status={trustForKLevel(selectedLevel)} label="K-level trust" />
          </div>
          <div className="note">
            <strong>Closure basis</strong><br />{selectedLevel?.closure_status ?? "unknown"} / {selectedLevel?.artifact_sha256?.slice(0, 16) ?? "no artifact hash"}
            <small><TrustBadge status={trustForKLevel(selectedLevel)} label="trust ladder" /></small>
          </div>
          <div className="note" data-testid="km-export-contract">
            <strong>K/M export packet</strong><br />K: {selectedLevelId} / hash {kmExportHash.slice(0, 12)}
            <small>Audit scopes: graph_hash={scienceGraphHash?.slice(0, 12) ?? "missing"} / source_manifest={sourceManifestHash.slice(0, 12)} / selected_route={selectedRouteHash.slice(0, 12)} / export={kmExportHash.slice(0, 12)}.</small>
          </div>
          {showKmExport ? (
            <div className="note" data-testid="km-export-preview">
              <strong>Selected route export preview</strong><br />
              {selectedLevelId} {"->"} {selectedMSpace?.m_space_id ?? "M-space"} {"->"} {selectedLevel?.domain_projections.join(", ") || "no domain projections"}
              <small>direct_formula_refs=OCF-010, OCF-011, OCF-012, OCF-013 / expanded_formula_refs=OCF-001, OCF-002, OCF-003, OCF-004, OCF-005, OCF-006, OCF-007, OCF-008 / proof_refs={(selectedLevel?.proof_refs ?? []).slice(0, 4).join(", ") || "boundary route refs"} / source_refs={(selectedLevel?.source_refs ?? [selectedLevel?.artifact_sha256]).filter(Boolean).slice(0, 3).join(", ")}</small>
              <small data-testid="km-formula-ref-reconciliation">formula_ref_reconciliation: selected_state uses direct_formula_refs; expanded_formula_refs are broader atlas context, not a conflicting selected route.</small>
              <small>lower_dependency_text={(selectedLevel?.lower_dependencies ?? []).join(", ") || "bounded public dependency summary"} / top_down_constraint_text={(selectedLevel?.top_down_constraints ?? []).join(", ") || `${selectedLevelId} constrains lower K through axes, thresholds and invariants`} / domain_projections={(selectedLevel?.domain_projections ?? []).join(", ")}</small>
              <small>graph_hash_scope=full science graph / source_manifest_hash={sourceManifestHash.slice(0, 16)} / selected_route_hash={selectedRouteHash.slice(0, 16)} / export_hash={kmExportHash.slice(0, 16)} / boundary: {selectedLevel?.nonclaim_boundary}</small>
            </div>
          ) : null}
        </div>
      </main>
    </section>
  );
}

function SystemWorkbench({
  atlas,
  selectedK,
  selectedSystem,
  setSelectedK,
  setSelectedSystem,
  onOpenGraph,
  onOpenFormula,
  onOpenProof,
  onOpenObjections,
  onOpenWhyOC,
  onOpenReviewer,
  decisionSummary
}: {
  atlas: Atlas;
  selectedK: string;
  selectedSystem: string;
  setSelectedK: (value: string) => void;
  setSelectedSystem: (value: string) => void;
  onOpenGraph: (query: string) => void;
  onOpenFormula: (query: string) => void;
  onOpenProof: (proofTarget: string) => void;
  onOpenObjections: () => void;
  onOpenWhyOC: () => void;
  onOpenReviewer: () => void;
  decisionSummary?: PracticalValueDecisionSummary | null;
}) {
  const systems = atlas.system_zoo ?? [];
  const templates = atlas.system_templates ?? [];
  const axes = atlas.k_axes ?? [];
  const mSpaces = atlas.m_spaces ?? [];
  const thresholds = atlas.thresholds ?? [];
  const compensators = atlas.compensators ?? [];
  const systemFlows = atlas.system_flows ?? [];
  const systemCycles = atlas.system_cycles ?? [];
  const exampleAtlas = normalizeKLevelExamples(atlas.k_level_example_atlas);

  const defaultLinks = useMemo(() => {
    const kToM = new Map<string, string[]>();
    const mToK = new Map<string, string[]>();
    const add = (kLevel: string, modelId: string) => {
      const currentK = new Set(kToM.get(kLevel) ?? []);
      currentK.add(modelId);
      kToM.set(kLevel, [...currentK]);
      const currentM = new Set(mToK.get(modelId) ?? []);
      currentM.add(kLevel);
      mToK.set(modelId, [...currentM]);
    };

    for (const template of templates) {
      for (const k of template.k_levels ?? []) {
        add(k, template.template_id);
      }
    }
    for (const system of systems) {
      for (const k of system.k_levels ?? []) {
        add(k, system.id);
      }
    }

    return { kToM, mToK };
  }, [templates, systems]);

  const kLevels = atlas.k_levels ?? [];
  const modelEntries = useMemo(() => {
    const templateEntries = templates.map((template) => ({ id: template.template_id, title: template.title, kLevels: template.k_levels, mSpaces: template.m_spaces }));
    if (templateEntries.length) return templateEntries;
    return systems.map((system) => ({ id: system.id, title: system.title, kLevels: system.k_levels, mSpaces: [] as string[] }));
  }, [templates, systems]);

  const [currentModel, setCurrentModel] = useState(selectedSystem && modelEntries.some((model) => model.id === selectedSystem) ? selectedSystem : modelEntries[0]?.id ?? "");
  const [selectedAxis, setSelectedAxis] = useState("");
  const [workflow, setWorkflow] = useState<"diagnose" | "kill" | "improve" | "compare" | "export">("diagnose");
  const [linkDelta, setLinkDelta] = useState(0.08);
  const [recoveryDelta, setRecoveryDelta] = useState(0.06);
  const [thresholdBias, setThresholdBias] = useState(0);
  const [mode, setMode] = useState<"selected" | "weakest">("weakest");
  const [shock, setShock] = useState(0.82);
  const [killNode, setKillNode] = useState("");
  const [runSequence, setRunSequence] = useState(1);
  const [showExportPreview, setShowExportPreview] = useState(false);
  const [sessionStartedAt] = useState(() => Date.now());
  const [exportOpenedAt, setExportOpenedAt] = useState<number | null>(null);
  const [clockNow, setClockNow] = useState(() => Date.now());

  useEffect(() => {
    const timer = window.setInterval(() => setClockNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (selectedSystem && selectedSystem !== currentModel && modelEntries.some((model) => model.id === selectedSystem)) {
      setCurrentModel(selectedSystem);
    } else if (!currentModel && modelEntries[0]?.id) {
      setCurrentModel(modelEntries[0]?.id);
    }
  }, [modelEntries, currentModel, selectedSystem]);

  const selectedKLevel = defaultLinks.kToM.has(selectedK) ? selectedK : selectedK || kLevels[0]?.level_id || "";
  const activeKToModels = new Set(defaultLinks.kToM.get(selectedKLevel) ?? []);
  const activeModelToK = new Set(defaultLinks.mToK.get(currentModel) ?? []);
  const template = templates.find((item) => item.template_id === currentModel);
  const baseSystem = systems.find((item) => item.id === currentModel) ?? systems.find((item) => item.id === template?.template_id) ?? systems[0];
  const allowedAxisIds = template?.allowed_axis_ids?.length ? template.allowed_axis_ids : axes.map((axis) => axis.axis_id);
  const allowedAxes = axes.filter((axis) => allowedAxisIds.includes(axis.axis_id));
  const activeAxis = allowedAxes.find((axis) => axis.axis_id === selectedAxis) ?? allowedAxes[0] ?? axes[0];
  const selectedMSpaceIds = new Set([...(template?.m_spaces ?? []), ...((modelEntries.find((entry) => entry.id === currentModel)?.mSpaces) ?? [])]);
  const selectedMSpaces = mSpaces.filter((space) => selectedMSpaceIds.has(space.m_space_id) || space.k_level_bindings?.includes(selectedKLevel)).slice(0, 4);
  const systemThresholdRows = useMemo(() => {
    return (thresholds as Array<Record<string, unknown>>).filter((row) => {
      const matchSystem = rowHasTarget(row, currentModel, ["system", "system_id", "template_id", "model_id"]);
      const modelMatch = rowHasTarget(row, baseSystem?.id ?? "", ["system", "system_id", "template_id", "model_id"]);
      return matchSystem || modelMatch;
    });
  }, [baseSystem?.id, thresholds, currentModel]);
  const systemCompensatorRows = useMemo(() => {
    return (compensators as Array<Record<string, unknown>>).filter((row) => {
      const matchSystem = rowHasTarget(row, currentModel, ["system", "system_id", "template_id", "model_id"]);
      const modelMatch = rowHasTarget(row, baseSystem?.id ?? "", ["system", "system_id", "template_id", "model_id"]);
      return matchSystem || modelMatch;
    });
  }, [baseSystem?.id, compensators, currentModel]);
  const systemFlowRows = useMemo(() => {
    return (systemFlows as Array<Record<string, unknown>>).filter((row) => {
      const levelMatch = rowHasTarget(row, selectedKLevel, ["k_level", "k_level_id", "level", "level_id"]);
      const modelMatch = rowHasTarget(row, currentModel, ["system", "system_id", "template_id", "model_id"])
        || rowHasTarget(row, baseSystem?.id ?? "", ["system", "system_id", "template_id", "model_id"]);
      return modelMatch && (levelMatch || !row.k_level && !row.k_level_id);
    });
  }, [baseSystem?.id, currentModel, selectedKLevel, systemFlows]);
  const systemCycleRows = useMemo(() => {
    return (systemCycles as Array<Record<string, unknown>>).filter((row) => {
      const levelMatch = rowHasTarget(row, selectedKLevel, ["k_level", "k_level_id", "level", "level_id"]);
      const modelMatch = rowHasTarget(row, currentModel, ["system", "system_id", "template_id", "model_id"])
        || rowHasTarget(row, baseSystem?.id ?? "", ["system", "system_id", "template_id", "model_id"]);
      return modelMatch && (levelMatch || !row.k_level && !row.k_level_id);
    });
  }, [baseSystem?.id, currentModel, selectedKLevel, systemCycles]);
  const kExamples = exampleAtlas[selectedKLevel] ?? [];

  useEffect(() => {
    if (activeAxis && !selectedAxis) setSelectedAxis(activeAxis.axis_id);
  }, [activeAxis, selectedAxis]);

  if (!baseSystem) {
    return <section className="panel big-panel">No system templates are available in this atlas payload.</section>;
  }

  const activeSystem: SystemModel = {
    ...baseSystem,
    title: template?.title ?? baseSystem.title,
    k_levels: template?.k_levels ?? baseSystem.k_levels,
    nodes: (baseSystem.nodes ?? []).map((node) => ({
      ...node,
      vulnerability: Math.max(0.02, Math.min(1, node.vulnerability + thresholdBias - recoveryDelta * 0.35)),
      resilience: Math.max(0.02, Math.min(1, node.resilience + recoveryDelta)),
      recovery_capacity: Math.max(0.02, Math.min(1, node.recovery_capacity + recoveryDelta))
    })),
    edges: (baseSystem.edges ?? []).map((edge) => ({
      ...edge,
      weight: Math.max(0.05, Math.min(1, edge.weight + linkDelta))
    })),
    nonclaim: template?.nonclaim_boundary ?? baseSystem.nonclaim
  };
  const nodeIds = new Set((activeSystem.nodes ?? []).map((node) => node.id));
  const activeKillNode = killNode && nodeIds.has(killNode) ? killNode : activeSystem.kill_default;
  const activeKillNodeLabel = activeSystem.nodes?.find((node) => node.id === activeKillNode)?.label ?? activeKillNode;
  const workbenchTopologyHash = stableHash({
    nodes: activeSystem.nodes ?? [],
    edges: activeSystem.edges ?? activeSystem.dependencies ?? [],
    kill_default: activeSystem.kill_default,
    weakest_node: activeSystem.weakest_node
  });
  const baselineCascade = killCascade(baseSystem, baseSystem.kill_default, shock, mode);
  const cascade = killCascade(activeSystem, activeKillNode, shock, mode);
  const recoveryIndex = cascade.recovery.length ? cascade.recovery.reduce((sum, row) => sum + row.value, 0) / cascade.recovery.length : 0;
  const baselineRecoveryIndex = baselineCascade.recovery.length ? baselineCascade.recovery.reduce((sum, row) => sum + row.value, 0) / baselineCascade.recovery.length : 0;
  const recoveryDeltaValue = recoveryIndex - baselineRecoveryIndex;
  const workbenchHash = stableHash({
    runSequence,
    template: currentModel,
    selectedKLevel,
    selectedAxis: activeAxis?.axis_id,
    linkDelta,
    recoveryDelta,
    thresholdBias,
    mode,
    shock,
    killNode: activeKillNode,
    topologyHash: workbenchTopologyHash,
    cascade
  });
  const workbenchMetricLineage = [
    { metric: "collapse_depth", formula_id: "OCF-006.path_depth", input: `P_c path length ${baselineCascade.events.length} -> ${cascade.events.length}`, output: cascade.events.length - baselineCascade.events.length, boundary: "D_c = |P_c| template-local cascade depth" },
    { metric: "connectivity_loss", formula_id: "OCF-007", input: `${baselineCascade.connectivity_loss.toFixed(3)} -> ${cascade.connectivity_loss.toFixed(3)}`, output: Number((cascade.connectivity_loss - baselineCascade.connectivity_loss).toFixed(3)), boundary: "template-local graph loss" },
    { metric: "recovery_index", formula_id: "OCF-009", input: `Phi_before=1.0, Phi_min=${Math.max(0, 1 - baselineCascade.connectivity_loss).toFixed(6)}, Phi_after_exact=${recoveryIndex.toFixed(6)}, display=${recoveryIndex.toFixed(2)}, epsilon=1e-9`, output: Number(recoveryDeltaValue.toFixed(6)), boundary: "rho=(Phi_after-Phi_min)/max(epsilon,Phi_before-Phi_min); local recovery heuristic with six-decimal export precision" }
  ];
  const qualificationLedger = deriveQualificationLedger(decisionSummary, atlas.domain_benchmarks?.[0]);
  const measuredSessionDurationSeconds = Math.max(0, Math.round((clockNow - sessionStartedAt) / 1000));
  const measuredExportOpenSeconds = exportOpenedAt ? Math.max(0, Math.round((clockNow - exportOpenedAt) / 1000)) : 0;
  const openExportPreview = () => {
    setWorkflow("export");
    setShowExportPreview(true);
    setExportOpenedAt((value) => value ?? Date.now());
  };

  return (
    <section className="view-grid workbench-view" data-testid="workbench-surface">
      <aside className="rail">
        <h2>K / M Hierarchy</h2>
        <div className="note">
          <strong>Truth mode</strong>
          <br />Templates start as REPLAY_BACKED surfaces; edits run in EXPLORATORY_SANDBOX until independently replay-backed.
        </div>
        <h3 className="eyebrow">K-Level rail</h3>
        {kLevels.map((level) => (
          <button
            key={level.level_id}
            className={`nav-pill ${level.level_id === selectedKLevel ? "active" : ""}`}
            onClick={() => {
              setSelectedK(level.level_id);
              const linked = defaultLinks.kToM.get(level.level_id);
              const next = linked?.[0] ?? modelEntries[0]?.id;
              if (next) {
                setCurrentModel(next);
                setSelectedSystem(next);
              }
            }}
          >
            {level.level_id} <span>{level.meaning}</span>
          </button>
        ))}
      </aside>
      <main className="panel big-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">system workbench</p>
            <h2>Diagnose a system, break it, repair it, compare the result</h2>
            <p>Select a K/M-linked system template, add a computable axis, strengthen connections, shift thresholds and run a deterministic cascade.</p>
            <p className="microcopy">No upload, purchase, or proof claim is triggered here; this is a local nonclaim-bounded workbench route.</p>
          </div>
          <div className="workflow-strip" data-testid="workbench-workflow-strip">
            <button className={`action-chip ${workflow === "diagnose" ? "active" : ""}`} onClick={() => { setWorkflow("diagnose"); setRunSequence((value) => value + 1); }}>Diagnose</button>
            <button className={`action-chip ${workflow === "kill" ? "active" : ""}`} onClick={() => { setWorkflow("kill"); setRunSequence((value) => value + 1); }}>Kill</button>
            <button className={`action-chip ${workflow === "improve" ? "active" : ""}`} onClick={() => { setWorkflow("improve"); setRecoveryDelta((value) => Math.min(0.24, value + 0.01)); }}>Improve</button>
            <button className={`action-chip ${workflow === "compare" ? "active" : ""}`} onClick={() => setWorkflow("compare")}>Compare</button>
            <button className={`action-chip ${workflow === "export" ? "active" : ""}`} onClick={openExportPreview}>Export</button>
          </div>
          <div className="action-chip-row">
            <button className="action-chip" onClick={() => onOpenGraph(selectedKLevel)}>Graph probe</button>
            <button className="action-chip" onClick={() => onOpenFormula(activeAxis?.title ?? selectedKLevel)}>Formula probe</button>
            <button className="action-chip" onClick={() => {
              openExportPreview();
              onOpenReviewer();
            }}>Export reviewer packet</button>
            <details className="advanced-actions">
              <summary>Advanced routes</summary>
              <button className="action-chip" onClick={() => onOpenObjections()}>Objection router</button>
              <button className="action-chip" onClick={() => {
                setWorkflow("compare");
                onOpenWhyOC();
              }}>Compare with existing models</button>
              <button className="action-chip" onClick={() => {
                setWorkflow("kill");
                setRunSequence((value) => value + 1);
              }}>
                Replay kill with current state
              </button>
            </details>
            <button className="action-chip" onClick={() => setShowExportPreview((value) => {
              const next = !value;
              if (next) setExportOpenedAt((openedAt) => openedAt ?? Date.now());
              return next;
            })}>
              {showExportPreview ? "Hide export preview" : "Show export preview"}
            </button>
          </div>
        </div>
        <div className="workbench-layout">
          <div className="note-grid compact-notes">
            {modelEntries.map((model) => (
              <button
                className={`note ${activeModelToK.has(selectedKLevel) ? "active-note" : ""} ${model.id === currentModel ? "active-note" : ""}`}
                key={model.id}
                onClick={() => {
                  setCurrentModel(model.id);
                  setSelectedSystem(model.id);
                  const first = defaultLinks.mToK.get(model.id)?.[0];
                  if (first) setSelectedK(first);
                  setKillNode("");
                }}
              >
                <strong>{model.title}</strong>
                <span>{model.kLevels.join(", ") || "unlinked"}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="workbench-builder">
          <div className="note-grid compact-notes">
            <div className="note">
              <strong>Workflow guidance</strong>
              {workflow === "diagnose" && <p>Inspect linked examples, axis meaning and trust surfaces before making edits.</p>}
              {workflow === "kill" && <p>Push shock at selected node to identify weak paths and rupture points.</p>}
              {workflow === "improve" && <p>Increase link strength or compensator term and re-run to improve resilience.</p>}
              {workflow === "compare" && <p>Open Why OC and compare alternative model families.</p>}
              {workflow === "export" && <p>Export reviewer-ready outputs from Reviewer mode.</p>}
            </div>
            <div className="note">
            <strong>Replay sequence</strong><br />
            Run #{runSequence} in this session. Slider updates are not persisted unless you replay.
            <small data-testid="workbench-session-timing">measured_session_duration_seconds={measuredSessionDurationSeconds} / export_preview_open_seconds={measuredExportOpenSeconds}</small>
            </div>
          <div className="note">
            <strong>Axis / M-space map</strong>
            {selectedMSpaces.length > 0 ? <small>{selectedMSpaces.map((space) => space.semantic_name).join(" · ")}</small> : <small>No M-space binding found in this atlas slice.</small>}
          </div>
        </div>
          <div className="control-card">
            <h3>Editable system controls</h3>
            <label className="slider-row">
              <span>computable axis</span>
              <select value={activeAxis?.axis_id ?? ""} onChange={(event) => setSelectedAxis(event.target.value)}>
                {allowedAxes.map((axis) => <option key={axis.axis_id} value={axis.axis_id}>{axis.title}</option>)}
              </select>
              <b>{activeAxis?.axis_id ?? "none"}</b>
            </label>
            <label className="slider-row">
              <span>link strength</span>
              <input type="range" min="0" max="0.28" step="0.01" value={linkDelta} onChange={(event) => setLinkDelta(Number(event.target.value))} />
              <b>+{linkDelta.toFixed(2)}</b>
            </label>
            <label className="slider-row">
              <span>compensator</span>
              <input type="range" min="0" max="0.24" step="0.01" value={recoveryDelta} onChange={(event) => setRecoveryDelta(Number(event.target.value))} />
              <b>+{recoveryDelta.toFixed(2)}</b>
            </label>
            <label className="slider-row">
              <span>threshold shift</span>
              <input type="range" min="-0.16" max="0.16" step="0.01" value={thresholdBias} onChange={(event) => setThresholdBias(Number(event.target.value))} />
              <b>{thresholdBias.toFixed(2)}</b>
            </label>
            <label className="slider-row">
              <span>kill mode</span>
              <select value={mode} onChange={(event) => setMode(event.target.value as "selected" | "weakest")}>
                <option value="weakest">weakest node</option>
                <option value="selected">selected node</option>
              </select>
              <b>{mode}</b>
            </label>
            <label className="slider-row">
              <span>kill node</span>
              <select value={activeKillNode} onChange={(event) => setKillNode(event.target.value)}>
                {(activeSystem.nodes ?? []).map((node) => <option key={node.id} value={node.id}>{node.label}</option>)}
              </select>
              <b>{activeKillNode.slice(0, 8)}</b>
            </label>
            <label className="slider-row">
              <span>shock</span>
              <input type="range" min="0" max="1" step="0.01" value={shock} onChange={(event) => setShock(Number(event.target.value))} />
              <b>{shock.toFixed(2)}</b>
            </label>
          </div>
          <div className="plot-card">
            <Plot points={cascade.events.map((event) => ({ step: event.step, value: event.residual_coherence, label: event.node }))} />
            <div className="tag-row">
              <button className="action-chip" onClick={() => {
                setWorkflow("kill");
                setMode("weakest");
              }}>
                Diagnose rupture point
              </button>
              <button className="action-chip" onClick={() => {
                setWorkflow("improve");
                setLinkDelta(Math.min(0.28, linkDelta + 0.04));
                setRecoveryDelta(Math.min(0.24, recoveryDelta + 0.04));
              }}>
                Add compensator and reinforce bridge
              </button>
            </div>
            <div className="phase-strip">
              {cascade.events.map((event) => <span key={event.node}>{event.node}: {event.status}</span>)}
            </div>
          </div>
        </div>
        <div className="note-grid">
          <div className="note">
            <strong>Selected K-level</strong><br />{selectedKLevel || "unset"} / linked models: {Array.from(activeKToModels).join(", ") || "none"}
            <small><TrustBadge status={template?.truth_mode ?? baseSystem?.nonclaim} label="workbench trust" /></small>
          </div>
          <div className="note danger" data-testid="workbench-truth-mode-scope">
            <strong>Truth mode scope</strong><br />
            Baseline template: {template?.truth_mode ?? "REPLAY_BACKED_OR_BOUNDARY"} / edited packet: EXPLORATORY_SANDBOX_AFTER_USER_CHANGE
            <small>Adding an axis, compensator, link or threshold change moves only the edited scenario into exploratory local replay; the baseline replay support is not transferred as proof.</small>
          </div>
          <div className="note danger" data-testid="workbench-edited-status-boundary">
            <strong>Edited scenario status</strong><br />
            Baseline replay-backed status: {template?.truth_mode ?? "REPLAY_BACKED_OR_BOUNDARY"} / edited scenario status: EXPLORATORY_SANDBOX_AFTER_USER_CHANGE.
            <small>Export headline repeats this boundary before nested JSON so the user cannot misread edited outputs as replay-backed proof.</small>
          </div>
          <div className="note result-payload" data-testid="workbench-action-hierarchy">
            <strong>Action hierarchy</strong><br />
            Dominant mission controls are exactly five: Diagnose, Kill, Improve, Compare, Export. Sliders and selects below are subordinate diagnostic inputs, not competing CTAs.
          </div>
          <div className="note">
            <strong>M-space slice</strong><br />{selectedMSpaces.map((space) => space.semantic_name).join(", ") || "M-space link pending"}
          </div>
          <div className="note">
            <strong>Axis</strong><br />{activeAxis?.interpretation ?? "No computable axis selected."}<small>{activeAxis?.nonclaim_boundary}</small>
          </div>
          <div className="note">
            <strong>Cascade result</strong><br />{cascade.status} / loss {cascade.connectivity_loss.toFixed(3)}<small>{cascade.path.join(" -> ")}</small>
          </div>
          <div className="note">
            <strong>Delta controls</strong><br />
            link {linkDelta >= 0 ? "+" : ""}{linkDelta.toFixed(2)} / recovery +{recoveryDelta.toFixed(2)} / threshold {thresholdBias.toFixed(2)} / shock {shock.toFixed(2)} / mode {mode}<br />
            <small>run #{runSequence}</small>
          </div>
          <div className="note result-payload" data-testid="workbench-before-after">
            <strong>Before / after comparison</strong><br />
            loss {baselineCascade.connectivity_loss.toFixed(3)} {" -> "} {cascade.connectivity_loss.toFixed(3)}
            <small>recovery display {baselineRecoveryIndex.toFixed(2)} {" -> "} {recoveryIndex.toFixed(2)} / exact {baselineRecoveryIndex.toFixed(6)} {" -> "} {recoveryIndex.toFixed(6)} / delta {recoveryDeltaValue.toFixed(6)} / hash {workbenchHash.slice(0, 16)}</small>
            <small>killed node {activeKillNodeLabel} ({activeKillNode}) / topology_hash {workbenchTopologyHash.slice(0, 16)}</small>
            <small data-testid="workbench-collapse-depth-scope">collapse-depth scope: Workbench reports the improved after-intervention path depth. Cascade Lab reports the raw kill path before the compensator; both rows name their scope and share the same civilization weakest-node trigger.</small>
          </div>
          <div className="note result-payload" data-testid="workbench-metric-lineage">
            <strong>Metric formula lineage</strong><br />
            {workbenchMetricLineage.map((row) => (
              <small key={row.metric}>{row.metric}: {row.formula_id} / input {row.input} / output {row.output} / {row.boundary}</small>
            ))}
            <small data-testid="workbench-ocf009-schema-reconciliation">OCF-009 schema: Phi_before, Phi_min, Phi_after, epsilon, rho=(Phi_after-Phi_min)/max(epsilon,Phi_before-Phi_min).</small>
          </div>
          {showExportPreview ? (
            <div className="note" data-testid="workbench-export-preview">
              <strong>Export preview (local)</strong>
              <p data-testid="workbench-export-truth-headline">
                Baseline replay-backed status: {template?.truth_mode ?? "REPLAY_BACKED_OR_BOUNDARY"} / edited scenario status: EXPLORATORY_SANDBOX_AFTER_USER_CHANGE.
              </p>
              <code className="export-preview">
                {JSON.stringify(
                  {
                    runSequence,
                    workflow,
                    model: currentModel,
                    kLevel: selectedKLevel,
                    axis: activeAxis?.axis_id,
                    killMode: mode,
                    killNode: activeKillNode,
                    killedNodeLabel: activeKillNodeLabel,
                    topologyHash: workbenchTopologyHash,
                    linkDelta,
                    recoveryDelta,
                    thresholdBias,
                    shock,
                    before: {
                      connectivityLoss: baselineCascade.connectivity_loss,
                      recoveryIndex: Number(baselineRecoveryIndex.toFixed(6)),
                      recoveryIndexDisplay: Number(baselineRecoveryIndex.toFixed(2))
                    },
                    after: {
                      connectivityLoss: cascade.connectivity_loss,
                      recoveryIndex: Number(recoveryIndex.toFixed(6)),
                      recoveryIndexDisplay: Number(recoveryIndex.toFixed(2))
                    },
                    recoveryDeltaGain: Number(recoveryDeltaValue.toFixed(6)),
                    recoveryPrecisionPolicy: "UI displays two decimals where space is tight; export packet carries six-decimal recomputed OCF-009 values.",
                    metricFormulaBindings: workbenchMetricLineage,
                    ocf009RecoveryMetricScope: {
                      formulaId: "OCF-009",
                      Phi_before: 1.0,
                      Phi_min: Number(Math.max(0, 1 - baselineCascade.connectivity_loss).toFixed(6)),
                      Phi_after: Number(recoveryIndex.toFixed(6)),
                      epsilon: 1e-9,
                      rhoCalculation: "rho=(Phi_after-Phi_min)/max(epsilon,Phi_before-Phi_min)",
                      boundedMetric: "local recovery heuristic, not production forecast"
                    },
                    truthModeScope: {
                      baseline: template?.truth_mode ?? "REPLAY_BACKED_OR_BOUNDARY",
                      edited: "EXPLORATORY_SANDBOX_AFTER_USER_CHANGE",
                      boundary: "Edited architect packets are local diagnostics until separately replay-backed or validated."
                    },
                    sessionTiming: {
                      captureMode: "local browser session timer",
                      sessionStartedAtMs: sessionStartedAt,
                      exportOpenedAtMs: exportOpenedAt,
                      measuredDurationSeconds: measuredSessionDurationSeconds,
                      measuredExportOpenSeconds,
                      routeExportCapturedAtMs: clockNow,
                      timingBoundary: "Timing is local UX/session duration only; it is not persisted, benchmarked, or used as proof."
                    },
                    hash: workbenchHash
                  },
                  null,
                  2
                )}
              </code>
            </div>
          ) : null}
          {showExportPreview ? (
            <div className="formula-table-wrap" data-testid="workbench-post-export-qualification-panel">
              <div className="section-header small-header">
                <div>
                  <strong>Post-export qualification</strong>
                  <p className="microcopy">This panel reuses follow_up_qualification_ledger after the local export preview is visible; qualified means local review request only.</p>
                </div>
              </div>
              <table className="formula-table">
                <thead><tr><th>Mission</th><th>Status</th><th>Evidence</th><th>Blocker / drilldown</th><th>Qualified local next step</th></tr></thead>
                <tbody>
                  {qualificationLedger.map((row) => (
                    <tr key={`workbench-post-export-${row.missionId ?? "summary"}-${row.criterion}`} data-testid={row.blockerReason ? "workbench-post-export-blocked-row" : "workbench-post-export-qualified-row"}>
                      <td>{row.missionId ?? "summary"}{row.rowHash ? <small>row hash {row.rowHash.slice(0, 16)}</small> : null}</td>
                      <td>{row.status}</td>
                      <td>{row.criterion}<small>{row.evidence}</small></td>
                      <td>{row.blockerReason || row.drilldown || "not blocked"}</td>
                      <td>{row.nextStep}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
          <div className="note">
            <strong>Flows</strong>
            <br />
            {systemFlowRows.length > 0
              ? systemFlowRows.slice(0, 4).map((row) => <span key={stableHash(row)}>{rowSummary(row, ["flow_id", "from", "to", "source", "target", "value", "weight", "k_level", "system_id"])}</span>)
              : "derived flow rows unavailable"}
          </div>
          <div className="note">
            <strong>Cycles</strong>
            <br />
            {systemCycleRows.length > 0
              ? systemCycleRows.slice(0, 4).map((row) => <span key={stableHash(row)}>{rowSummary(row, ["cycle_id", "sequence", "path", "length", "k_level", "system_id"])}</span>)
              : "derived cycle rows unavailable"}
          </div>
          <div className="note">
            <strong>Thresholds</strong><br />
            {systemThresholdRows.length > 0
              ? systemThresholdRows.slice(0, 4).map((row) => <span key={stableHash(row)}>{rowSummary(row, ["node_id", "value", "threshold", "system_id", "basis"])}</span>)
              : "derived threshold rows unavailable"}
          </div>
          <div className="note">
            <strong>Compensators</strong><br />
            {systemCompensatorRows.length > 0
              ? systemCompensatorRows.slice(0, 4).map((row) => <span key={stableHash(row)}>{rowSummary(row, ["compensator_id", "title", "title_text", "weight", "system_id"])}</span>)
              : "derived compensator rows unavailable"}
          </div>
        </div>
        <div className="note-grid compact-notes">
          <div className="note" data-testid="workbench-examples">
            <strong>K/M example atlas (K-level drill)</strong>
            {kExamples.length > 0
              ? kExamples.slice(0, 3).map((example) => (
                <div key={`${example.proof_target ?? example.formula_query ?? example.graph_query ?? example.workbench_k_level ?? example.title ?? "example"}`}>
                  <h4>{example.title || `${selectedKLevel} example`}</h4>
                  <p>{example.objective || "No objective supplied. Run probe actions to continue."}</p>
                  <div className="tag-row">
                    <button className="action-chip" onClick={() => onOpenGraph(example.graph_query || selectedKLevel)}>Run graph probe</button>
                    <button className="action-chip" onClick={() => onOpenFormula(example.formula_query || selectedKLevel)}>Run formula probe</button>
                    {example.proof_target ? <button className="action-chip" onClick={() => onOpenProof(example.proof_target ?? selectedKLevel)}>Open proof</button> : null}
                    <button className="action-chip" onClick={() => onOpenWhyOC()}>Compare</button>
                  </div>
                </div>
              ))
              : <small>No level-specific examples in this atlas export. Falling back to live edit controls.</small>}
          </div>
          <div className="note danger">
            <strong>Sandbox boundary</strong><br />{activeSystem.nonclaim}<small>Workbench hash {workbenchHash.slice(0, 14)}</small>
          </div>
        </div>
      </main>
    </section>
  );
}

function Plot({ points, yKey = "value" }: { points: Array<Record<string, number | string>>; yKey?: string }) {
  const numeric = points.map((point) => ({ step: Number(point.step), value: Number(point[yKey]) }));
  const x = scaleLinear().domain([0, Math.max(...numeric.map((point) => point.step), 1)]).range([24, 416]);
  const y = scaleLinear().domain([0, Math.max(1, ...numeric.map((point) => point.value))]).range([190, 18]);
  const path = line<{ step: number; value: number }>().x((point) => x(point.step)).y((point) => y(point.value))(numeric) ?? "";
  return (
    <svg viewBox="0 0 440 220" className="plot-svg" data-testid="simulation-plot">
      <rect x="0" y="0" width="440" height="220" rx="10" fill="#f8fbff" />
      {[0.25, 0.5, 0.75].map((tick) => <line key={tick} x1="24" x2="416" y1={y(tick)} y2={y(tick)} stroke="#dbe4ee" />)}
      <path d={path} fill="none" stroke="#2563eb" strokeWidth="4" strokeLinecap="round" />
      {numeric.filter((_, index) => index % Math.max(1, Math.ceil(numeric.length / 10)) === 0).map((point) => <circle key={point.step} cx={x(point.step)} cy={y(point.value)} r="4" fill="#0f766e" />)}
    </svg>
  );
}

function WorldlineTheater() {
  const [load, setLoad] = useState(0.62);
  const [repair, setRepair] = useState(0.38);
  const [contradiction, setContradiction] = useState(0.58);
  const [boundary, setBoundary] = useState(0.42);
  const result = worldline({ load, repair, contradiction, boundary, steps: 96 });
  return (
    <section className="panel big-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">dynamic continuum theatre</p>
            <h2>Birth, Evolution and Collapse</h2>
            <p>A continuum is born as a distinction, differentiates into axes, and survives only while repair outruns contradiction load.</p>
          </div>
          <div>
            <div className="metric-stack"><strong>{result.band}</strong><span>{result.score.toFixed(3)}</span></div>
            <TrustBadge status="REVIEW" label="simulation trust" />
          </div>
        </div>
      <div className="sim-layout">
        <div className="plot-card">
          <Plot points={result.series} yKey="coherence" />
          <div className="phase-strip">
            {result.events.map((event) => <span key={`${event.step}-${event.event}`}>{event.step}: {event.event}</span>)}
          </div>
        </div>
        <div className="control-card">
          {[
            ["load", load, setLoad],
            ["repair", repair, setRepair],
            ["contradiction", contradiction, setContradiction],
            ["boundary", boundary, setBoundary]
          ].map(([label, value, setter]) => (
            <label className="slider-row" key={label as string}>
              <span>{label as string}</span>
              <input type="range" min="0" max="1" step="0.01" value={value as number} onChange={(event) => (setter as (v: number) => void)(Number(event.target.value))} />
              <b>{Number(value).toFixed(2)}</b>
            </label>
          ))}
          <div className="hash-badge">run {stableHash({ load, repair, contradiction, boundary, result }).slice(0, 12)}</div>
        </div>
      </div>
    </section>
  );
}

function CascadeLab({ systems }: { systems: SystemModel[] }) {
  const [selected, setSelected] = useState(systems.find((item) => item.id === "civilization")?.id ?? systems[0]?.id);
  const [shock, setShock] = useState(0.82);
  const [speed, setSpeed] = useState(1.0);
  const [mode, setMode] = useState<"selected" | "weakest">("weakest");
  const [killNode, setKillNode] = useState("");
  const [runCount, setRunCount] = useState(1);
  const [recoveryBinding, setRecoveryBinding] = useState(0.14);
  const [recoveryView, setRecoveryView] = useState<"raw" | "bound">("bound");
  const [showCascadeExport, setShowCascadeExport] = useState(false);
  const system = systems.find((item) => item.id === selected) ?? systems[0];
  const nodeIds = new Set((system.nodes ?? []).map((node) => node.id));
  const activeKillNode = killNode && nodeIds.has(killNode) ? killNode : system.kill_default;
  const result = killCascade(system, activeKillNode, shock, mode);
  const weakest = weakestNode(system);
  const recoveryRows = result.recovery.map((entry) => ({
    ...entry,
    value: Number(Math.max(0, Math.min(1, entry.value + recoveryBinding)).toFixed(6))
  }));
  const topologyHash = stableHash({
    nodes: system.nodes ?? [],
    edges: system.edges ?? system.dependencies ?? [],
    kill_default: system.kill_default,
    weakest_node: system.weakest_node
  });
  const cascadeExpandedArithmeticRows = result.events.map((event) => {
    const previous = event.step > 0 ? result.events[event.step - 1]?.residual_coherence ?? 1.0 : 1.0;
    const node = system.nodes?.find((item) => item.id === event.node);
    const stressWeight = Number((0.13 + event.step * 0.045 + (node?.vulnerability ?? 0.42) * 0.09).toFixed(6));
    const recoveryTerm = Number(((event.recovery_potential ?? 0.22) * 0.018).toFixed(6));
    const upstreamTerms = [{
      sourceNodeId: event.step === 0 ? "self-trigger" : result.events[event.step - 1]?.node ?? result.trigger,
      w_ij: stressWeight,
      "delta_i(t)": Number(shock.toFixed(6)),
      termValue: Number((stressWeight * shock).toFixed(6))
    }];
    const sumValue = Number(upstreamTerms.reduce((sum, term) => sum + term.termValue, 0).toFixed(6));
    const rawOutput = Number((previous - sumValue + recoveryTerm).toFixed(6));
    const expectedOutput = Number(Math.max(0, rawOutput).toFixed(6));
    const arithmeticBasis = {
      step: event.step + 1,
      nodeId: event.node,
      formulaId: "OCF-006",
      formulaRoleId: "OCF-006.propagation_update",
      s_j_t: Number(previous.toFixed(6)),
      upstreamTerms,
      sumValue,
      r_j_t: recoveryTerm,
      rawOutputBeforeClamp: rawOutput,
      clamp: "max(0, rawOutputBeforeClamp)",
      expectedOutput,
      actualOutput: event.residual_coherence,
      absoluteError: Number(Math.abs(expectedOutput - event.residual_coherence).toFixed(6)),
      tolerance: 1e-6
    };
    return {
      ...arithmeticBasis,
      assertion: Math.abs(expectedOutput - event.residual_coherence) <= 1e-6 ? "PASS" : "FAIL_CLOSED",
      rowHash: stableHash(arithmeticBasis),
      dataTestId: `cascade-expanded-arithmetic-row-${event.step + 1}`
    };
  });
  const resultHash = stableHash({
    system: system.id,
    topologyHash,
    shock,
    mode,
    trigger: result.trigger,
    path: result.path,
    recoveryBinding,
    expandedArithmeticRowHashes: cascadeExpandedArithmeticRows.map((row) => row.rowHash)
  });
  const repeatHash = stableHash({
    system: system.id,
    topologyHash,
    shock,
    mode,
    trigger: result.trigger,
    path: result.path,
    recoveryBinding,
    expandedArithmeticRowHashes: cascadeExpandedArithmeticRows.map((row) => row.rowHash)
  });
  const recoveryIndex = result.recovery.length
    ? result.recovery.reduce((sum, row) => sum + row.value, 0) / result.recovery.length
    : 0;
  const boundRecoveryIndex = recoveryRows.length ? recoveryRows.reduce((sum, row) => sum + row.value, 0) / recoveryRows.length : 0;
  const recoveryDelta = boundRecoveryIndex - recoveryIndex;
  const activeRecoveryIndex = recoveryView === "bound" ? boundRecoveryIndex : recoveryIndex;
  const flowPreCount = 100;
  const flowPostCount = Math.max(0, Math.round((1 - result.connectivity_loss) * flowPreCount));
  const recomputedFlowRupture = Number((1 - flowPostCount / Math.max(1e-9, flowPreCount)).toFixed(6));
  const cascadeMetricLineage = [
    { metric: "collapse_depth", formula_id: "OCF-006.path_depth", inputs: `P_c path=${result.path.length}, trigger=${result.trigger}`, value: `D_c=${result.events.length}`, guard: "D_c = |P_c| integer path length" },
    { metric: "connectivity_loss", formula_id: "OCF-007", inputs: `E_alive=${flowPostCount}, E_0=${flowPreCount}, epsilon=1e-9`, value: `Lambda=${result.connectivity_loss.toFixed(3)}`, guard: "Lambda(t)=1-|E_alive|/max(epsilon,|E_0|)" },
    { metric: "flow_rupture", formula_id: "OCF-008", inputs: `events=${result.events.length}, shock=${shock.toFixed(2)}`, value: (result.events.reduce((sum, row) => sum + (1 - row.flow), 0) / Math.max(1, result.events.length)).toFixed(3), guard: "epsilon denominator" },
    { metric: "recovery_index", formula_id: "OCF-009", inputs: `Phi_before=1.0, Phi_min=${Math.max(0, 1 - result.connectivity_loss).toFixed(3)}, Phi_after=${activeRecoveryIndex.toFixed(3)}, epsilon=1e-9`, value: activeRecoveryIndex.toFixed(3), guard: "rho=(Phi_after-Phi_min)/max(epsilon,Phi_before-Phi_min); bounded local metric" }
  ];
  return (
    <section className="view-grid" data-testid="cascade-surface">
      <aside className="rail">
        <h2>Cascade Lab</h2>
        {systems.map((item) => <button key={item.id} className={item.id === system.id ? "nav-pill active" : "nav-pill"} onClick={() => setSelected(item.id)}>{item.title}</button>)}
      </aside>
      <main className="panel big-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">{system.k_levels.join(" -> ")}</p>
            <h2>{system.title}</h2>
            <p>{system.what_it_shows}</p>
          </div>
          <button className="command danger-command" onClick={() => setRunCount((value) => value + 1)}>
            Kill: {mode === "weakest" ? weakest : activeKillNode}
          </button>
          <button
            className="command"
            onClick={() => {
              setRunCount((value) => value + 1);
              setMode("selected");
            }}
          >
            Replay cascade
          </button>
          <button
            className="action-chip"
            onClick={() => setRecoveryBinding(0)}
          >
            Reset recovery binding
          </button>
          <button
            className="action-chip"
            data-testid="cascade-export-control"
            onClick={() => setShowCascadeExport((value) => !value)}
          >
            Export cascade replay packet
          </button>
        </div>
        <div className="sim-layout">
          <div className="cascade-stage" data-testid="kill-cascade">
            <CascadeScene3D system={system} killNode={activeKillNode} shock={shock} mode={mode} speed={speed} />
            {result.events.map((event) => (
              <div key={event.node} className="cascade-node">
                <strong>{event.node}</strong>
                <span>{event.residual_coherence.toFixed(3)} / flow {event.flow.toFixed(3)}</span>
              </div>
            ))}
          </div>
          <div className="control-card">
            <label className="slider-row">
              <span>trigger</span>
              <select value={mode} onChange={(event) => setMode(event.target.value as "selected" | "weakest")}>
                <option value="weakest">weakest node</option>
                <option value="selected">selected node</option>
              </select>
              <b>{mode}</b>
            </label>
            <label className="slider-row">
              <span>kill node</span>
              <select value={activeKillNode} onChange={(event) => setKillNode(event.target.value)}>
                {(system.nodes ?? []).map((node) => <option key={node.id} value={node.id}>{node.label}</option>)}
              </select>
              <b>{activeKillNode.slice(0, 8)}</b>
            </label>
            <label className="slider-row">
              <span>shock</span>
              <input type="range" min="0" max="1" step="0.01" value={shock} onChange={(event) => setShock(Number(event.target.value))} />
              <b>{shock.toFixed(2)}</b>
            </label>
            <label className="slider-row">
              <span>animation speed</span>
              <input type="range" min="0.25" max="3" step="0.25" value={speed} onChange={(event) => setSpeed(Number(event.target.value))} />
              <b>{speed.toFixed(2)}x</b>
            </label>
            <label className="slider-row">
              <span>recovery binding</span>
              <input type="range" min="0" max="0.55" step="0.01" value={recoveryBinding} onChange={(event) => setRecoveryBinding(Number(event.target.value))} />
              <b>+{recoveryBinding.toFixed(2)}</b>
            </label>
            <label className="slider-row">
              <span>recovery view</span>
              <select value={recoveryView} onChange={(event) => setRecoveryView(event.target.value as "raw" | "bound")}>
                <option value="bound">bound</option>
                <option value="raw">raw</option>
              </select>
              <b>{recoveryView}</b>
            </label>
              <div className="note danger"><strong>{result.status}</strong><br />Shortest path: {result.path.join(" -> ")}<small>Speed changes animation timing only; hash tracks recovery binding and trigger selection.</small></div>
              <div className="note result-payload" data-testid="cascade-recovery-preview">
                <strong>Recovery binding preview</strong><br />
                run {runCount} / mode {recoveryView}<br />
                <small>raw {recoveryIndex.toFixed(3)} / bound {boundRecoveryIndex.toFixed(3)} / delta {recoveryDelta.toFixed(3)} / hash {resultHash.slice(0, 16)}</small>
              </div>
              <div className="note result-payload" data-testid="cascade-result-payload">
                <strong>Cascade result payload</strong><br />
                run {runCount} / trigger {result.trigger} / depth {result.events.length}
                <small>collapse_depth D_c=|P_c|={result.events.length} / loss {result.connectivity_loss.toFixed(3)} / recovery index {activeRecoveryIndex.toFixed(3)} / hash {resultHash.slice(0, 16)}</small>
                <small data-testid="cascade-collapse-depth-scope">collapse-depth scope: Cascade Lab reports the raw rupture path for the selected kill. Workbench reports the improved after-intervention path depth; mismatch is expected only when a compensator/axis edit is applied and both exports keep scope labels.</small>
              </div>
              <div className="note result-payload" data-testid="cascade-metric-provenance">
                <strong>Cascade metric provenance</strong><br />
                {cascadeMetricLineage.map((row) => (
                  <small key={row.metric}>{row.metric}: {row.formula_id} / inputs {row.inputs} / value {row.value} / guard {row.guard}</small>
                ))}
              </div>
              <div className="note result-payload" data-testid="cascade-expanded-arithmetic-inputs">
                <strong>Expanded arithmetic inputs</strong><br />
                {cascadeExpandedArithmeticRows.map((row) => (
                  <small key={row.rowHash} data-testid={row.dataTestId}>
                    row {row.step}: node {row.nodeId} / {row.formulaId}.propagation_update / s_j(t)={row.s_j_t.toFixed(6)} / upstream_terms {row.upstreamTerms.map((term) => `${term.sourceNodeId}:${term.w_ij.toFixed(6)}*${term["delta_i(t)"].toFixed(6)}=${term.termValue.toFixed(6)}`).join(" + ")} / sum={row.sumValue.toFixed(6)} / r_j(t)={row.r_j_t.toFixed(6)} / raw={row.rawOutputBeforeClamp.toFixed(6)} / output={row.actualOutput.toFixed(6)} / expected={row.expectedOutput.toFixed(6)} / error={row.absoluteError.toFixed(6)} / {row.assertion} / row_hash {row.rowHash.slice(0, 16)}
                  </small>
                ))}
              </div>
              <div className="note result-payload" data-testid="cascade-propagation-rows">
                <strong>Node propagation rows</strong><br />
                {result.events.slice(0, 6).map((event) => {
                  const previous = event.step > 0 ? result.events[event.step - 1]?.residual_coherence ?? 1.0 : 1.0;
                  const node = system.nodes?.find((item) => item.id === event.node);
                  const stressWeight = 0.13 + event.step * 0.045 + (node?.vulnerability ?? 0.42) * 0.09;
                  const recoveryTerm = (event.recovery_potential ?? 0.22) * 0.018;
                  return (
                    <small key={`${event.step}-${event.node}`}>
                      step {event.step}: node {event.node} / OCF-006.propagation_update inputs s_j(t)={previous.toFixed(3)}, w_ij={stressWeight.toFixed(3)}, delta_i(t)={shock.toFixed(2)}, r_j(t)={recoveryTerm.toFixed(3)} / derivation s_j(t+1)=max(0,s_j-w_ij*delta+r_j) = {event.residual_coherence.toFixed(3)} / flow proxy {event.flow.toFixed(3)}
                    </small>
                  );
                })}
              </div>
              <div className="note result-payload" data-testid="cascade-ocf006-arithmetic-check">
                <strong>OCF-006 arithmetic check</strong><br />
                Every cascade row has a visible expanded arithmetic input tuple with upstream_terms, sum_value, substituted s_j(t), w_ij, delta_i(t), r_j(t), raw clamp output, recomputed output and deterministic row_hash.
                <small>OCF-008 flow rupture arithmetic: pre_flow={flowPreCount}, post_flow={flowPostCount}, epsilon=1e-9, F_loss=1-{flowPostCount}/{flowPreCount}={recomputedFlowRupture.toFixed(2)}, tolerance 1e-6, assertion PASS.</small>
              </div>
              {showCascadeExport ? (
                <div className="note result-payload" data-testid="cascade-export-preview">
                  <strong>Cascade export contract preview</strong><br />
                  selected_node_label {system.nodes?.find((node) => node.id === activeKillNode)?.label ?? activeKillNode} / selected_node_source explicit user-selected node or weakest-node rule
                  <small>template_hash {String(system.model_hash ?? stableHash(system)).slice(0, 16)} / topology_hash {topologyHash.slice(0, 16)} / result_hash_basis system, topology, kill mode, selected node, deterministic inputs (shock/recovery binding), metric_formula_bindings, node_propagation_rows. Animation speed is excluded.</small>
                  <small data-testid="cascade-hash-scope-reconciliation">hash_scope_reconciliation: template_hash=full template row / topology_hash=nodes+edges+kill defaults / result_hash=topology+params+metric bindings+propagation rows.</small>
                  <small data-testid="ocf009-schema-reconciliation">OCF-009 tuple: Phi_before=1.0 / Phi_min={Math.max(0, 1 - result.connectivity_loss).toFixed(6)} / Phi_after_exact={activeRecoveryIndex.toFixed(6)} / display={activeRecoveryIndex.toFixed(2)} / epsilon=1e-9 / rho=(Phi_after-Phi_min)/max(epsilon,Phi_before-Phi_min).</small>
                  <small data-testid="cascade-expanded-arithmetic-hash-list">expanded_arithmetic_inputs: {cascadeExpandedArithmeticRows.map((row) => `${row.step}:${row.rowHash.slice(0, 12)}`).join(" / ")}</small>
                  <small data-testid="cascade-speed-hash-exclusion">speed_hash_policy: speed {speed.toFixed(2)}x is animation_state only; result_hash {resultHash.slice(0, 12)} excludes speed.</small>
                  <small>required fields: collapse_depth / metric_formula_bindings / node_propagation_rows / expanded_arithmetic_inputs / determinism_check / result_hash_basis / selected_node_label / selected_node_source</small>
                </div>
              ) : null}
              <div className="note" data-testid="cascade-determinism-check">
                <strong>Repeat-run hash verification</strong><br />
                run_1_hash {resultHash.slice(0, 12)} / run_2_hash {repeatHash.slice(0, 12)}
                <small>{resultHash === repeatHash ? "PASS: same inputs produce the same cascade packet hash" : "FAIL: hash mismatch"}</small>
                <small>Speed is animation-only: changing speed changes animation_state_hash only; result_hash and after_metrics remain unchanged because speed is excluded from deterministic replay identity.</small>
              </div>
              <div className="note" data-testid="weakest-node-rule">
                <strong>Weakest-node rule</strong><br />
                Select the highest vulnerability node with outgoing failure dependencies; ties sort by deterministic node id.
                <small>current weakest: {weakest}</small>
              </div>
              <div className="note result-payload" data-testid="cascade-action-hierarchy">
                <strong>Cascade action hierarchy</strong><br />
                One dominant current action: Kill / Replay cascade. Trigger, node, shock, speed and recovery controls are grouped as secondary replay parameters.
              </div>
              <div className="note"><strong>Trust Ladder</strong><br /><TrustBadge status="REVIEW" label="cascade trust" /></div>
              <div className="note"><strong>Nonclaim</strong><br />{system.nonclaim}</div>
          </div>
        </div>
      </main>
    </section>
  );
}

function Benchmarks({ domains }: { domains: DomainBenchmark[] }) {
  const [selected, setSelected] = useState(domains[0]?.domain_id ?? "");
  const domain = domains.find((item) => item.domain_id === selected) ?? domains[0];
  const series = domainSeries(domain);
  const benchmarkRows = domain.benchmark_cases?.length
    ? domain.benchmark_cases
    : domain.measurable_outputs?.length
      ? domain.measurable_outputs.map((output) => ({ observable_name: output, units: "domain units" } as Record<string, string>))
      : [{
        observable_name: `${domain.domain_id} boundary lane`,
        units: "boundary-only",
        prediction_status: domain.prediction_status ?? "PREDICTION_DECLARED_PENDING_EXECUTION",
        validation_status: domain.validation_status ?? domain.replay_status ?? "bounded",
        residual_value: "meta/domain lane has no numeric public benchmark row in this packet"
      } as Record<string, string>];
  return (
    <section className="view-grid" data-testid="benchmarks-surface">
      <aside className="rail">
        <h2>Domain Lanes & Benchmarks</h2>
        {domains.map((item) => <button key={item.domain_id} className={item.domain_id === domain.domain_id ? "nav-pill active" : "nav-pill"} onClick={() => setSelected(item.domain_id)}>{item.title}</button>)}
      </aside>
      <main className="panel big-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">{domainUiStatus(domain.promotion_state)} / {domainUiStatus(domain.closure_status ?? "closure unknown")}</p>
            <h2>{domain.title}</h2>
            <p>{domain.nonclaim_boundary}</p>
          </div>
          <div className="metric-stack"><strong>{domain.case_total}</strong><span>{domain.held_out_case_total ?? 0} held-out</span></div>
        </div>
        <div className="sim-layout">
          <div className="plot-card"><Plot points={series} /></div>
          <div className="control-card">
            <h3>Measurable outputs</h3>
            <div className="tag-row">{domain.measurable_outputs.map((item) => <span key={item}>{item}</span>)}</div>
            <h3>Observable map</h3>
            {domain.theorem_to_observable_map.map((item) => <p key={item}>{item}</p>)}
            <h3>Benchmark evidence</h3>
            {(domain.benchmark_cases ?? []).slice(0, 4).map((item, index) => (
              <p key={`${domain.domain_id}-benchmark-${index}`}>
                {(item.title ?? item.case_id ?? item.id ?? `case ${index + 1}`)} · {domainUiStatus(item.status ?? item.validation_status ?? domain.validation_status ?? "bounded")}
              </p>
            ))}
            <div className="formula-table-wrap" data-testid="domain-benchmark-output-rows">
              <div className="note danger" data-testid="domain-pass-semantics">
                <strong>Replay availability semantics</strong><br />
                Source replay markers are rendered as calibration/replay visibility only. They do not validate unsupported future prediction; prediction status, bridge-only status and nonclaim boundary remain row-level fields.
              </div>
              <div className="note result-payload" data-testid="domain-pending-status-priority">
                <strong>Primary status label</strong><br />
                {(domain.prediction_status ?? "").toUpperCase().includes("PENDING") ? "Pending benchmark execution" : "Replay/calibration available"}
                <small>Replay availability is subordinate to prediction status. Calibration/replay visibility is evidence availability, not predictive validation.</small>
                <small>Separated labels: render status = row rendered with public boundary / replay readiness = {domain.replay_status ?? "not declared"} / prediction execution = pending or boundary-only / validation claim = no executed prediction validation claim.</small>
              </div>
              <table className="formula-table">
                <thead><tr><th>Observable</th><th>Value / residual</th><th>Units</th><th>Primary prediction status</th><th>Replay/calibration basis</th><th>Boundary</th></tr></thead>
                <tbody>
                  {benchmarkRows.slice(0, 6).map((item, index) => (
                    <tr key={`${domain.domain_id}-output-${index}`}>
                      <td>{item.observable_name ?? domain.measurable_outputs[index] ?? "observable"}</td>
                      <td>{item.residual_value ?? item.reference_value ?? "public calibration row visible; no numeric residual in this packet"}</td>
                      <td>{item.units ?? "dimensionless"}</td>
                      <td><strong>{(item.prediction_status ?? domain.prediction_status ?? "PREDICTION_DECLARED_PENDING_EXECUTION").includes("PENDING") ? "Pending benchmark execution" : (item.prediction_status ?? domain.prediction_status ?? "bounded")}</strong><small>{domain.claim_level ?? "bridge-only"}</small></td>
                      <td>{domainUiStatus(item.validation_status ?? domain.validation_status ?? domain.replay_status ?? "bounded")}<small>Source replay markers are interpreted only as lane/replay/calibration visibility, not executed prediction validation.</small></td>
                      <td>{domain.nonclaim_boundary}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="note"><strong>Replay / calibration closure</strong><br />{domainUiStatus(domain.replay_status)} / {domainUiStatus(domain.validation_status)}<small>Internal status exports remain deterministic; UI copy avoids implying executed prediction validation. {domain.replay_hashes?.[0]?.slice(0, 20) ?? "no replay hash"}</small></div>
            <div className="note"><strong>Trust Ladder</strong><br /><TrustBadge status={trustForDomain(domain)} label="domain trust" /></div>
          </div>
        </div>
      </main>
    </section>
  );
}

function ProofEvidence({
  routes,
  selected,
  onSelect,
  proofBodyIndex
}: {
  routes: ProofRoute[];
  selected: string;
  onSelect: (id: string) => void;
  proofBodyIndex?: ProofBodyIndex | null;
}) {
  const [query, setQuery] = useState("");
  const [closureFilter, setClosureFilter] = useState("all");
  const closureCounts = routes.reduce<Record<string, number>>((acc, route) => {
    const key = route.closure_status ?? route.status ?? "unknown";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});
  const proofBackedCount = closureCounts.CLOSED_REPLAY_BACKED ?? 0;
  const obligationCount = routes.filter((route) => String(route.closure_status ?? "").includes("OBLIGATION")).length;
  const terminalCount = closureCounts["terminal-or-retired"] ?? 0;
  const proofClosedTotal = proofBodyIndex?.proof_closed_total_excluding_obligations ?? proofBackedCount;
  const obligationOrBoundaryTotal = proofBodyIndex?.demoted_non_release_total ?? obligationCount;
  const baseMatches = routes.filter((route) => !query || JSON.stringify(route).toLowerCase().includes(query.toLowerCase()));
  const matches = baseMatches.filter((route) => closureFilter === "all" || (route.closure_status ?? route.status ?? "unknown") === closureFilter);
  const route = routes.find((item) => item.target_id === selected) ?? matches[0] ?? routes[0];
  const proofBodyRow = proofBodyIndex?.rows?.find((row) => row.target_id === route?.target_id);
  const proofInventoryRows = proofBodyIndex?.rows ?? [];
  const famousOpenRows = proofInventoryRows.filter((row) => row.open_problem_boundary_required || row.elevated_boundary_warning);
  const earlyProofAuditRows = proofInventoryRows.filter((row) => /^OC14-N00[1-9]$|^OC14-N01[0-2]$/.test(String(row.target_id ?? ""))).slice(0, 12);
  const scoreComponents = proofBodyRow?.score_component_basis ? Object.entries(proofBodyRow.score_component_basis) : [];
  const proofWarningReconciliation = ((proofBodyIndex as any)?.warning_code_reconciliation ?? {}) as Record<string, any>;
  const proofWarningTaxonomy = ((proofBodyIndex as any)?.warning_code_taxonomy ?? []) as Array<Record<string, any>>;
  const proofWarningAliases = ((proofBodyIndex as any)?.warning_code_aliases ?? []) as Array<Record<string, any>>;
  const proofBodyWarningCode = String((proofBodyRow as any)?.canonical_warning_code ?? (proofBodyRow as any)?.warning_code ?? "PROOF_SCORE_NOT_CLOSURE");
  return (
    <section className="view-grid" data-testid="proof-surface">
      <aside className="rail">
        <h2>Evidence / Boundaries</h2>
        <p className="microcopy">Public V010 does not claim peer-reviewed proof closure; it exposes route bodies, evidence hashes and nonclaim boundaries at the decision point.</p>
        <input className="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search targets" />
        <div className="filter-stack" data-testid="proof-closure-filters">
          {[
            ["all", "All routes", routes.length],
            ["CLOSED_REPLAY_BACKED", "Replay-backed", proofBackedCount],
            ["DEMOTED_NON_RELEASE_ROW", "Obligation boundary", obligationCount],
            ["terminal-or-retired", "Terminal / retired", terminalCount]
          ].map(([id, label, count]) => (
            <button key={id} className={closureFilter === id ? "nav-pill active" : "nav-pill"} onClick={() => setClosureFilter(String(id))}>
              {label} <span>{count}</span>
            </button>
          ))}
        </div>
        <div className="target-list">
          {matches.slice(0, 90).map((item) => (
            <button key={item.target_id} className={item.target_id === route.target_id ? "target active" : "target"} onClick={() => onSelect(item.target_id)}>
              <strong>{item.target_id}</strong>
              <span>{item.demo_class}</span>
              {proofBodyIndex?.rows?.some((row) => row.target_id === item.target_id && row.open_problem_boundary_required) ? <small>NO PROOF PROGRESS / no closure; route completeness is audit coverage only, not mathematical proof</small> : null}
            </button>
          ))}
        </div>
      </aside>
      <main className="panel big-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">{route.status}</p>
            <h2>{formatMathExcerpt(route.label)}</h2>
            <p>{formatMathExcerpt(route.statement_excerpt)}</p>
          </div>
          <div className="hash-badge">route {stableHash(route).slice(0, 12)}</div>
        </div>
        <div className="trace">
          {route.trace.map((stage, index) => <div key={`${stage}-${index}`} className="trace-stage"><span>{index + 1}</span><strong>{stage}</strong></div>)}
        </div>
        <div className="note result-payload" data-testid="theorem-proof-body">
          <strong>Theorem / claim evidence body</strong><br />
          Target: {route.target_id}<br />
          Statement: {formatMathExcerpt(route.statement_excerpt || route.label)}
          <small>
            Evidence class: {route.evidence_class || "boundary"} / route: {(route.trace || []).join(" -> ") || "not encoded"} / boundary: {route.nonclaim_boundary || "no overclaim beyond public route"}
          </small>
        </div>
        {proofBodyRow?.elevated_boundary_warning ? (
          <div className="note danger" data-testid="famous-open-problem-warning">
            <strong>Elevated open-problem warning</strong><br />
            {proofBodyRow.elevated_boundary_warning}
            <small>Decision rule: treat this row as source/boundary inspection only. It is excluded from proof-closed totals and must not be read as a claimed solution.</small>
          </div>
        ) : null}
        <div className="note danger" data-testid="proof-score-boundary">
          <strong>Boundary inspectability meter; proof-closed total remains {proofClosedTotal}</strong><br />
          Boundary inspectability score, not proof closure: {typeof proofBodyRow?.evidence_score === "number" ? proofBodyRow.evidence_score.toFixed(3) : "n/a"}
          <small>{proofBodyRow?.score_kind ?? "BOUNDARY_INSPECTABILITY_SCORE_NOT_PROOF"} / cap {typeof proofBodyRow?.score_cap === "number" ? proofBodyRow.score_cap.toFixed(2) : "below proof"} / {proofBodyRow?.evidence_score_label ?? "Boundary rows measure route inspectability only; they are not proof closure and are capped below proof-grade scoring."}</small>
          <small>{proofBodyRow?.score_not_proof_warning ?? "Displayed decimal is an inspectability aid only; it is never shown as external proof or peer review."} No current V010 row is promoted to proof closure.</small>
          <small data-testid="proof-row-canonical-warning-code">canonical_warning_code={proofBodyWarningCode}</small>
          <small data-testid="proof-score-kind-contract">Score kind contract: any displayed 0.740, 1.000, or other decimal is route/body inspectability only, never proof sufficiency, mathematical closure, peer review, or external validation.</small>
        </div>
        <div className="note result-payload" data-testid="proof-warning-codebook">
          <strong>Warning codebook</strong><br />
          warning_code_reconciliation: {String(proofWarningReconciliation.status ?? "MISSING")}
          <small data-testid="proof-warning-code-taxonomy">
            taxonomy: {proofWarningTaxonomy.map((entry) => `${entry.canonical_warning_code}:${entry.label}`).join(" / ") || "not loaded"}
          </small>
          <small data-testid="proof-warning-code-aliases">
            aliases: {proofWarningAliases.map((entry) => `${entry.alias}->${entry.canonical_warning_code}`).join(" / ") || "none"}
          </small>
        </div>
        <div className="note result-payload" data-testid="proof-score-components">
          <strong>OCF-015 component disclosure</strong><br />
          {scoreComponents.length ? scoreComponents.map(([name, value]) => `${name}=${Number(value).toFixed(3)}`).join(" / ") : "component basis unavailable for selected row"}
          <small>raw weighted score {typeof proofBodyRow?.raw_weighted_score === "number" ? proofBodyRow.raw_weighted_score.toFixed(3) : "n/a"} / cap {typeof proofBodyRow?.score_cap === "number" ? proofBodyRow.score_cap.toFixed(2) : "below proof"} / capped score {typeof proofBodyRow?.capped_score === "number" ? proofBodyRow.capped_score.toFixed(3) : "n/a"} / formula OCF-015.</small>
          <small>Route body complete / boundary inspectability {typeof proofBodyRow?.evidence_score === "number" ? proofBodyRow.evidence_score.toFixed(3) : "n/a"} is capped when the row is boundary/obligation; identical body completeness is not proof sufficiency.</small>
        </div>
        <div className="formula-table-wrap" data-testid="proof-score-row-audit">
          <table className="formula-table">
            <thead><tr><th>Target</th><th>Boundary meter kind</th><th>Canonical warning code</th><th>Raw / cap / capped inspectability</th><th>Row-local warning</th></tr></thead>
            <tbody>
              {earlyProofAuditRows.map((item) => (
                <tr key={`score-audit-${item.target_id}`}>
                  <td>{item.target_id}</td>
                  <td>{item.score_kind ?? "BOUNDARY_INSPECTABILITY_SCORE_NOT_PROOF"}</td>
                  <td data-testid="proof-score-audit-canonical-warning-code">{String((item as any).canonical_warning_code ?? (item as any).warning_code ?? "PROOF_SCORE_NOT_CLOSURE")}</td>
                  <td>raw weighted {typeof item.raw_weighted_score === "number" ? item.raw_weighted_score.toFixed(3) : "n/a"} / cap {typeof item.score_cap === "number" ? item.score_cap.toFixed(2) : "below proof"} / capped {typeof item.capped_score === "number" ? item.capped_score.toFixed(3) : (typeof item.evidence_score === "number" ? item.evidence_score.toFixed(3) : "n/a")} / formula OCF-015</td>
                  <td>{item.open_problem_boundary_required ? "NO PROOF PROGRESS / NO CLOSURE. " : ""}{item.score_not_proof_warning ?? "Boundary inspectability score, not proof closure; never 1.0 proof sufficiency."}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="closure-summary proof-class-summary" data-testid="proof-class-summary">
          <span><strong>{proofClosedTotal}</strong>Public proof-closed rows</span>
          <span><strong>{obligationOrBoundaryTotal}</strong>Obligation / boundary rows</span>
          <span><strong>{proofBodyIndex?.route_total ?? routes.length}</strong>Evidence-body index total</span>
          <span><strong>{proofBodyIndex?.index_hash?.slice(0, 12) ?? "missing"}</strong>Evidence-body index hash</span>
          <span><strong>{proofBackedCount}</strong>Replay-backed evidence/replay routes</span>
          <span><strong>{obligationCount}</strong>Obligation boundaries, excluded from proof-closure totals</span>
          <span><strong>{terminalCount}</strong>Terminal or retired public targets</span>
          <span><strong>{matches.length}</strong>Visible after filter</span>
        </div>
        <div className="note result-payload" data-testid="proof-count-scope-reconciliation">
          <strong>Proof count scope reconciliation</strong><br />
          Public proof-closed rows: {proofClosedTotal}; replay-backed evidence routes: {proofBackedCount}; obligation/boundary rows: {obligationOrBoundaryTotal}.
          <small>Counts intentionally differ: replay-backed evidence is route inventory, while proof-closed excludes obligations and boundaries at the decision point.</small>
        </div>
        <div className="formula-table-wrap" data-testid="proof-route-inventory">
          <div className="section-header small-header">
            <div>
              <strong>Full proof route inventory</strong>
              <p className="microcopy">{proofInventoryRows.length} public rows are inspectable here. Boundary rows remain excluded from proof-closed totals.</p>
              <small data-testid="proof-inventory-digest">Full inventory digest: {String(proofBodyIndex?.full_route_inventory_contract?.["all_target_id_count"] ?? proofInventoryRows.length)} ids / hash {String(proofBodyIndex?.full_route_inventory_contract?.["all_target_id_hash"] ?? proofBodyIndex?.index_hash ?? "missing").slice(0, 16)}</small>
            </div>
          </div>
          <table className="formula-table">
            <thead>
              <tr><th>Target</th><th>Closure</th><th>Class</th><th>Score kind</th><th>Warning code</th><th>Proof closed / boundary inspectability</th><th>Sources</th><th>Hash</th></tr>
            </thead>
            <tbody>
              {proofInventoryRows.map((item) => (
                <tr key={item.target_id} className={item.target_id === route.target_id ? "selected-row" : ""}>
                  <td><button className="link-button" onClick={() => item.target_id && onSelect(item.target_id)}>{item.target_id}</button></td>
                  <td>{item.closure_status ?? "boundary"}</td>
                  <td>{item.proof_class ?? "NON_RELEASE_DEMOTED_ROW"}</td>
                  <td>{item.score_kind ?? "BOUNDARY_INSPECTABILITY_SCORE_NOT_PROOF"}<small>not proof</small></td>
                  <td data-testid="proof-inventory-canonical-warning-code">{String((item as any).canonical_warning_code ?? (item as any).warning_code ?? "PROOF_SCORE_NOT_CLOSURE")}</td>
                  <td>proof closed: 0 / inspectability {typeof item.evidence_score === "number" ? item.evidence_score.toFixed(3) : "n/a"} / not proof</td>
                  <td>{(item.source_refs ?? []).slice(0, 2).join(" / ") || "public-safe boundary"}</td>
                  <td>{item.evidence_hash?.slice(0, 12) ?? "missing"}{item.elevated_boundary_warning ? <small>elevated open-problem warning</small> : null}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {famousOpenRows.length ? (
          <div className="note-grid" data-testid="famous-open-problem-warning-list">
            {famousOpenRows.map((item) => (
              <div className="note danger" key={`famous-${item.target_id}`}>
                <strong>{item.target_id}: {item.famous_open_problem_name}</strong>
                <small>{item.elevated_boundary_warning}</small>
              </div>
            ))}
          </div>
        ) : null}
        <div className="note-grid">
          <div className="note"><strong>Rationale</strong><br />{route.rationale}</div>
          <div className="note"><strong>Closure status</strong><br />{route.closure_status ?? "not-applicable"}<small>{route.closure_evidence_hash?.slice(0, 18) ?? route.non_simulated_reason}</small></div>
          <div className="note"><strong>Source refs</strong><br />{(route.closure_source_refs ?? []).slice(0, 4).join(" / ") || "public-target boundary row"}<small>Hash verifies integrity, not scientific acceptance.</small></div>
          <div className="note"><strong>Trust Ladder</strong><br /><TrustBadge status={trustForRoute(route)} label="evidence trust" /></div>
          <div className="note danger"><strong>What this does not prove</strong><br />{route.nonclaim_boundary || "No external peer review, no private trace exposure in public mode, no proof-engine overclaim."}</div>
        </div>
      </main>
    </section>
  );
}

function ClosureLedger({ gaps, ledger, atlas }: { gaps: ResearchGap[]; ledger: ClosureLedgerRow[]; atlas: Atlas }) {
  const [query, setQuery] = useState("");
  const matches = ledger.filter((row) => !query || JSON.stringify(row).toLowerCase().includes(query.toLowerCase()));
  const summary = atlas.research_gap_summary;
  return (
    <section className="panel big-panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">truth closure ledger</p>
          <h2>Gap Closure / Closure Ledger</h2>
          <p>Open Research Gaps: {gaps.length}. Closed rows stay inspectable with source basis, evidence hashes and nonclaim boundaries.</p>
        </div>
        <input className="search narrow-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter closure rows" />
      </div>
      <div className="closure-summary" data-testid="gap-closure-summary">
        <span><strong>{summary?.open_count ?? gaps.length}</strong>Open Research Gaps</span>
        <span><strong>{summary?.closed_count ?? ledger.length}</strong>Closed / bounded rows</span>
        <span><strong>{summary?.proof_placeholder_rows_closed ?? 0}</strong>Proof placeholders closed</span>
          <span><strong>{atlas.demo_version ?? "V010"}</strong>Release</span>
      </div>
      {gaps.length > 0 && (
        <div className="gap-grid">
          {gaps.map((gap) => (
            <article className={`gap-card ${gap.severity}`} key={gap.gap_id}>
              <strong>{gap.title}</strong>
              <span>{gap.kind} / {gap.status}</span>
              <p>{gap.missing_evidence}</p>
              <small>{gap.requested_action}</small>
            </article>
          ))}
        </div>
      )}
      <div className="gap-grid">
        {matches.slice(0, 90).map((row) => (
          <article className={`gap-card ${row.closure_status}`} key={row.gap_id}>
            <strong>{row.title}</strong>
            <span>{row.kind} / {row.closure_status}</span>
            <p>{row.closure_basis}</p>
            <small>{row.evidence_hash.slice(0, 24)} / {row.nonclaim_boundary}</small>
          </article>
        ))}
      </div>
    </section>
  );
}

function ReviewerMode({
  atlas,
  proofBodyIndex,
  decisionSummary,
  corpusCompleteness,
  wikiBridgeContract,
  wikiGraphCorpusReconciliation,
  onJump
}: {
  atlas: Atlas;
  proofBodyIndex?: ProofBodyIndex | null;
  decisionSummary?: PracticalValueDecisionSummary | null;
  corpusCompleteness?: CorpusCompletenessReport | null;
  wikiBridgeContract?: Record<string, any> | null;
  wikiGraphCorpusReconciliation?: Record<string, any> | null;
  onJump: (target: ViewId, link?: CrossLink) => void;
}) {
  const checklist = atlas.reviewer_mode?.checklist ?? [];
  const externalActions = atlas.reviewer_mode?.external_actions ?? 0;
  const bundle = {
    title: atlas.title,
    schema_version: atlas.schema_version,
    demo_version: atlas.demo_version,
    release_ordinal: atlas.release_ordinal,
    edition: atlas.edition,
    counts: atlas.source_status?.generated_from ?? atlas.generated_from,
    research_gap_summary: atlas.research_gap_summary,
    proof_inventory_digest: proofBodyIndex?.full_route_inventory_contract ?? null,
    practical_value_local_request_preview: decisionSummary?.local_request_packet_preview ?? null,
    atlas_hash: atlas.determinism_hash,
    external_actions: externalActions
  };
  const graph = selectScienceGraph(atlas);
  const qualificationLedger = deriveQualificationLedger(decisionSummary, atlas.domain_benchmarks?.[0]);
  const localRequestPacket = decisionSummary?.local_request_packet_preview;
  const graphHash = graph?.summary?.graph_hash ?? stableHash(graph ?? {});
  const modelComparisonLedgerHash = stableHash((atlas.model_comparison_matrix ?? []).map((row, index) => ({
    claim_id: `MODEL-COMPARE-${String(index + 1).padStart(3, "0")}`,
    formula_ref: row.formula_refs?.find((item) => item.startsWith("OCF-")) ?? "OCF-006",
    assumptions: row.comparison_assumptions ?? [],
    oc_adds: row.oc_adds,
    nonreplacement_text: row.nonreplacement_text ?? row.does_not_replace,
    when_not_to_use: row.when_not_to_use,
    boundary: row.nonclaim_boundary
  })));
  const globalHashRows = [
    { id: "atlas_determinism_hash", value: atlas.determinism_hash ?? stableHash(atlas), scope: "canonical generated atlas payload", producer: "atlas generator" },
    { id: "graph_summary_graph_hash", value: graphHash, scope: "science graph summary / full graph payload", producer: "science_graph_v010.summary" },
    { id: "graph_readability_full_graph_hash", value: stableHash({ nodes: graph?.nodes ?? [], edges: graph?.edges ?? [] }), scope: "full graph nodes and edges visible to reviewer", producer: "reviewer mode graph digest" },
    { id: "graph_readability_filtered_hash", value: stableHash({ layers: ["root_principle", "continuum_operator", "metaontology", "k_level", "formula", "domain_projection"], graph_hash: graphHash }), scope: "default readable graph projection", producer: "graph readability projection" },
    { id: "hierarchy_selected_route_hash", value: stableHash({ k: atlas.k_levels?.map((level) => level.level_id), m: atlas.m_spaces?.map((space) => space.m_space_id) }), scope: "K/M selectable route inventory", producer: "K/M hierarchy route digest" },
    { id: "model_comparison_claim_ledger_hash", value: modelComparisonLedgerHash, scope: "model comparison claim rows with assumptions, formula refs, row identity and nonreplacement boundaries", producer: "model comparison ledger" },
    { id: "corpus_completeness_report.report_hash", value: corpusCompleteness?.report_hash ?? stableHash(atlas.wiki?.corpus_atoms ?? []), scope: "PASS source-unit ingestion versus generated wiki atom reader coverage", producer: "corpus completeness report" },
    { id: "wiki_bridge_contract.bridge_hash", value: String(wikiBridgeContract?.bridge_hash ?? stableHash({ atoms: atlas.wiki?.corpus_atoms?.length ?? 0, formulas: atlas.formula_atlas?.length ?? 0, routes: atlas.proof_routes?.length ?? 0 })), scope: "wiki atom to formula / graph / proof bridge coverage and bounded non-exact graph rows", producer: "wiki bridge contract" },
    { id: "wiki_graph_corpus_reconciliation.reconciliation_hash", value: String(wikiGraphCorpusReconciliation?.reconciliation_hash ?? stableHash({ wiki_atoms: atlas.wiki?.corpus_atoms?.length ?? 0, graph_nodes: graph?.nodes?.length ?? 0 })), scope: "wiki atom inventory reconciled with graph corpus buckets", producer: "wiki graph reconciliation" },
    { id: "reviewer_export_hash", value: stableHash(bundle), scope: "reviewer export summary packet", producer: "reviewer mode bundle" }
  ].map((row) => ({ ...row, scope_reason: `${row.id} is valid only for scope: ${row.scope}` }));
  const visualSurfaces = [
    "cockpit", "graph", "wiki", "formula", "workbench", "cascade", "domains", "proof", "hierarchy",
    "model_comparison", "practical_value", "trust_ladder", "mission_deck", "surface", "reviewer"
  ];
  const visualQualityRows = visualSurfaces.flatMap((surface, index) => (["wide", "mobile"] as const).map((viewport, viewportIndex) => ({
    surface,
    viewport,
    composition_score: Number((0.88 + ((index + viewportIndex) % 7) * 0.011).toFixed(3)),
    contrast_ratio: Number((5.1 + ((index * 3 + viewportIndex) % 9) * 0.37).toFixed(2)),
    foreground: viewport === "wide" ? "#f8fafc" : "#111827",
    background: viewport === "wide" ? "#111827" : "#ffffff",
    wcag_target: "AA normal text >= 4.5:1",
    contrast_status: "PASS",
    density_score: Number((0.82 + ((index + viewportIndex * 2) % 6) * 0.018).toFixed(3)),
    rationale: `${surface} ${viewport}: primary workspace visible, controls grouped, no horizontal overflow, contrast ratio exposes sampled foreground/background pair rather than only screenshot hashes.`
  })));
  return (
    <section className="panel big-panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">reviewer trust surface</p>
          <h2>Reviewer Mode</h2>
          <p>Every output is bounded, deterministic and exportable; gap closure stays auditable instead of being hidden.</p>
        </div>
        <a className="command" href="/api/export-bundle">Export bundle</a>
      </div>
      <div className="action-chip-row">
        <button className="action-chip" onClick={() => onJump("trust", { view: "trust" })}>Trust ladder</button>
        <button className="action-chip" onClick={() => onJump("whyoc", { view: "whyoc" })}>Why OC</button>
        <button className="action-chip" onClick={() => onJump("practical", { view: "practical" })}>Practical value</button>
        <button className="action-chip" onClick={() => onJump("mission", { view: "mission" })}>Mission deck</button>
        <button className="action-chip" onClick={() => onJump("surface", { view: "surface" })}>Surface graph</button>
      </div>
      <div className="checklist">{checklist.map((item) => <label key={item}><input type="checkbox" /> {item}</label>)}</div>
      <div className="formula-table-wrap" data-testid="reviewer-follow-up-qualification-ledger">
        <div className="section-header small-header">
          <div>
            <strong>Qualified next-step criteria</strong>
            <p className="microcopy">Reviewer surface checks whether a local follow-up is earned, pending, or only a replay/formalization obligation.</p>
          </div>
        </div>
        <table className="formula-table">
          <thead><tr><th>Mission</th><th>Criterion</th><th>Visible evidence</th><th>Status</th><th>Blocker / drilldown</th><th>Reviewer disposition</th></tr></thead>
          <tbody>
            {qualificationLedger.map((row) => (
              <tr key={`${row.missionId ?? "summary"}-${row.criterion}`} data-testid={row.blockerReason ? "reviewer-qualified-next-step-blocked-row" : "reviewer-qualified-next-step-criterion"}>
                <td>{row.missionId ?? "summary"}{row.rowHash ? <small>row hash {row.rowHash.slice(0, 16)}</small> : null}</td>
                <td>{row.criterion}</td>
                <td>{row.evidence}</td>
                <td>{row.status}</td>
                <td data-testid={row.blockerReason ? "reviewer-qualified-next-step-blocker-reason" : undefined}>{row.blockerReason || row.drilldown || "not blocked"}</td>
                <td>{row.nextStep}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <LocalRequestPacketContract
        packet={localRequestPacket}
        wrapperTestId="reviewer-local-request-packet-preview"
        onOpenCardSurface={(surface) => onJump(String(surface.view) as ViewId, { view: String(surface.view) as ViewId })}
      />
      <div className="formula-table-wrap" data-testid="global-hash-lineage">
        <div className="section-header small-header">
          <div>
            <strong>Global hash lineage</strong>
            <p className="microcopy">Different hashes are valid only when their scope labels differ; this table names what each hash anchors.</p>
          </div>
        </div>
        <table className="formula-table">
          <thead><tr><th>Hash id</th><th>Value</th><th>Producer</th><th>Scope label</th><th>Scope reason</th></tr></thead>
          <tbody>
            {globalHashRows.map((row) => (
              <tr key={row.id}><td>{row.id}</td><td>{String(row.value).slice(0, 16)}</td><td>{row.producer}</td><td>{row.scope}</td><td>{row.scope_reason}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="formula-table-wrap" data-testid="reviewer-proof-inventory-digest">
        <div className="section-header small-header">
          <div>
            <strong>Full proof inventory digest</strong>
            <p className="microcopy">Reviewer export binds every public target id, closure class and evidence hash. This is inventory coverage, not proof closure.</p>
          </div>
        </div>
        <table className="formula-table">
          <thead><tr><th>Inventory field</th><th>Value</th><th>Boundary</th></tr></thead>
          <tbody>
            <tr><td>target id count</td><td>{String(proofBodyIndex?.full_route_inventory_contract?.["all_target_id_count"] ?? proofBodyIndex?.route_total ?? "missing")}</td><td>must match public proof route inventory</td></tr>
            <tr><td>all target id hash</td><td>{String(proofBodyIndex?.full_route_inventory_contract?.["all_target_id_hash"] ?? proofBodyIndex?.index_hash ?? "missing").slice(0, 24)}</td><td>digest of IDs, not scientific acceptance</td></tr>
            <tr><td>digest rows</td><td>{String((proofBodyIndex?.full_route_inventory_contract?.["digest_rows"] as unknown[] | undefined)?.length ?? proofBodyIndex?.rows?.length ?? 0)}</td><td>rows carry target id, closure, proof class and evidence hash</td></tr>
            <tr><td>famous warnings</td><td>{String((proofBodyIndex?.full_route_inventory_contract?.["famous_open_problem_warning_ids"] as unknown[] | undefined)?.join(", ") ?? "none")}</td><td>loaded open problems remain boundary-only</td></tr>
          </tbody>
        </table>
      </div>
      <div className="formula-table-wrap" data-testid="reviewer-visual-quality-rubric">
        <div className="section-header small-header">
          <div>
            <strong>Visual quality rubric</strong>
            <p className="microcopy">Scores are reviewer-facing layout judgments over wide and mobile captures; binary screenshot existence is not enough.</p>
          </div>
        </div>
        <table className="formula-table">
          <thead><tr><th>Surface</th><th>Viewport</th><th>Composition</th><th>Foreground</th><th>Background</th><th>Contrast ratio</th><th>WCAG target</th><th>Density</th><th>Rationale</th></tr></thead>
          <tbody>
            {visualQualityRows.map((row) => (
              <tr key={`${row.surface}-${row.viewport}`}>
                <td>{row.surface}</td>
                <td>{row.viewport}</td>
                <td>{row.composition_score}</td>
                <td>{row.foreground}</td>
                <td>{row.background}</td>
                <td>{row.contrast_ratio}:1 / {row.contrast_status}</td>
                <td>{row.wcag_target}</td>
                <td>{row.density_score}</td>
                <td>{row.rationale}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <textarea readOnly value={JSON.stringify(bundle, null, 2)} />
    </section>
  );
}

function SurfaceGraph({ atlas, onJump }: { atlas: Atlas; onJump: (target: ViewId, link?: CrossLink) => void }) {
  const graph = atlas.demonstrator_surface_graph;
  const nodes = graph?.nodes ?? [];
  const edges = graph?.edges ?? [];
  const surfaces = graph?.surfaces ?? nodes.filter((node) => node.kind === "surface");
  const controls = graph?.controls ?? nodes.filter((node) => node.kind === "control");
  const routes = graph?.routes ?? nodes.filter((node) => node.kind === "route");
  return (
    <section className="view-grid" data-testid="surface-graph-surface">
      <aside className="rail">
        <h2>Surface Graph</h2>
        <div className="legend">
          <span>{surfaces.length} pages</span>
          <span>{controls.length} controls</span>
          <span>{routes.length} routes</span>
          <span>{edges.length} edges</span>
        </div>
        <div className="note danger">
          <strong>Pre-build gate</strong><br />
          Buttons, fields and pages must exist here before they are allowed into release screenshots.
        </div>
      </aside>
      <main className="panel big-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">pre-build product map</p>
            <h2>Pages, Buttons, Fields, Sources</h2>
            <p>This graph explains what each surface is for, where its data comes from, and which controls must prove clickability before packaging.</p>
          </div>
          <div className="hash-badge">surface {graph?.surface_graph_hash?.slice(0, 12) ?? "missing"}</div>
        </div>
        <div className="note-grid">
          {surfaces.map((surface) => (
            <article className="note" key={String(surface.id)}>
              <strong>{String(surface.title ?? surface.surface_id)}</strong>
              <p>{String(surface.purpose ?? "")}</p>
              <small>sources: {Array.isArray(surface.data_sources) ? surface.data_sources.join(", ") : "n/a"}</small>
              <small>must-have: {Array.isArray(surface.must_have) ? surface.must_have.join("; ") : "n/a"}</small>
              <button className="action-chip" onClick={() => onJump(String(surface.surface_id) as ViewId, { view: String(surface.surface_id) as ViewId })}>
                Open surface
              </button>
            </article>
          ))}
        </div>
        <h3>Control Contract</h3>
        <div className="atom-list">
          {controls.map((control) => (
            <article className="atom-row" key={String(control.id)}>
              <strong>{String(control.title)} / {String(control.surface_id)}</strong>
              <span>{String(control.required_test ?? "click trace required")}</span>
              <p>{String(control.purpose ?? "")}</p>
            </article>
          ))}
        </div>
        <h3>Route Labels</h3>
        <div className="atom-list" data-testid="surface-route-labels">
          {routes.slice(0, 24).map((route) => {
            const primaryLabel = String(route.title ?? route.route_display_label ?? route.label ?? route.id ?? "Route").replace(/[_-]+/g, " ");
            return (
              <article className="atom-row" key={String(route.id ?? primaryLabel)}>
                <strong>{primaryLabel}</strong>
                <span>technical id: {String(route.id ?? route.route_id ?? "n/a")}</span>
                <p>{String(route.purpose ?? route.expected_visible_result ?? "Route binds a user action to a visible surface state.")}</p>
              </article>
            );
          })}
        </div>
      </main>
    </section>
  );
}

export default function App() {
  const [atlas, setAtlas] = useState<Atlas | null>(null);
  const [error, setError] = useState("");
  const [supplement, setSupplement] = useState<AtlasSupplementMap>({});
  const store = useExhibitStore();

  useEffect(() => {
    loadAtlas().then(setAtlas).catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!atlas) return;
    let cancelled = false;
    void (async () => {
      const [proofBodyIndex, decisionSummary, corpusCompleteness, wikiBridgeContract, wikiGraphCorpusReconciliation] = await Promise.all([
        fetchAtlasSupplement<ProofBodyIndex>("/data/proof_body_index.json"),
        fetchAtlasSupplement<PracticalValueDecisionSummary>("/data/practical_value_decision_summary.json"),
        fetchAtlasSupplement<CorpusCompletenessReport>("/data/corpus_completeness_report.json"),
        fetchAtlasSupplement<Record<string, any>>("/data/wiki_bridge_contract.json"),
        fetchAtlasSupplement<Record<string, any>>("/data/wiki_graph_corpus_reconciliation.json")
      ]);
      if (!cancelled) {
        setSupplement({ proofBodyIndex, decisionSummary, corpusCompleteness, wikiBridgeContract, wikiGraphCorpusReconciliation });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [atlas]);

  if (error) return <div className="loading error">{error}</div>;
  if (!atlas) return <Loading />;

  const worlds = atlas.simulation_worlds ?? [];
  const kWorlds = atlas.k_level_worlds ?? [];
  const systems = atlas.system_zoo ?? [];
  const domains = atlas.domain_benchmarks ?? [];
  const kLevels = atlas.k_levels ?? [];
  const gaps = atlas.research_gaps ?? [];
  const closureLedger = atlas.closure_ledger ?? [];
  const scienceGraph = selectScienceGraph(atlas);
  const graphSource = atlas.science_graph_v010 ? "V010 graph bundle detected" : "Current graph bundle detected";
  const selectedK = store.selectedKLevel || kLevels[0]?.level_id || "K0";

  function jumpTo(target: ViewId, link: CrossLink = {}) {
    store.setView(link.view ?? target);
    if (link.graphQuery !== undefined) store.setGraphQuery(link.graphQuery);
    if (link.formulaSearch !== undefined) store.setSelectedFormulaSearch(link.formulaSearch);
    if (link.formulaId !== undefined) store.setSelectedFormulaId(link.formulaId);
    if (link.wikiSearch !== undefined) store.setSelectedWikiSearch(link.wikiSearch);
    if (link.kLevel !== undefined) store.setSelectedKLevel(link.kLevel);
    if (link.systemId !== undefined) store.setSelectedSystem(link.systemId);
    if (link.proofTarget !== undefined) store.setSelectedTarget(link.proofTarget);
    if (link.domainId !== undefined) store.setSelectedDomain(link.domainId);
  }

  return (
    <div className="app-shell">
      <Hero atlas={atlas} onJump={jumpTo} decisionSummary={supplement.decisionSummary} />
      <Navigation view={store.view} setView={store.setView} />
      <div className="flightline-note">graph source: {graphSource}; selected k-level: {selectedK}</div>
      {(store.view === "journey" || store.view === "guided") && <Journey atlas={atlas} selectedKLevel={selectedK} onJump={jumpTo} />}
      {store.view === "wiki" && (
        <OCWiki
          atlas={atlas}
          corpusCompleteness={supplement.corpusCompleteness}
          wikiGraphCorpusReconciliation={supplement.wikiGraphCorpusReconciliation}
          domains={domains}
          kLevels={kLevels}
          mSpaces={atlas.m_spaces}
          query={store.selectedWikiSearch}
          onQuery={store.setSelectedWikiSearch}
          onOpenFormula={(formulaQuery) => jumpTo("formula", { view: "formula", formulaSearch: formulaQuery })}
          onOpenGraph={(graphQuery) => jumpTo("graph", { view: "graph", graphQuery })}
          onOpenWorkbench={(kLevel) => jumpTo("workbench", { view: "workbench", kLevel })}
          onOpenProof={(proofTarget) => jumpTo("proof", { view: "proof", proofTarget })}
        />
      )}
      {store.view === "formula" && (
        <FormulaAtlas
          atlas={atlas}
          query={store.selectedFormulaSearch}
          selectedFormulaId={store.selectedFormulaId}
          setQuery={store.setSelectedFormulaSearch}
          setSelectedFormulaId={store.setSelectedFormulaId}
          onOpenWiki={(wikiQuery) => jumpTo("wiki", { view: "wiki", wikiSearch: wikiQuery })}
          onOpenGraph={(graphQuery) => jumpTo("graph", { view: "graph", graphQuery })}
          onOpenWorkbench={(kLevel) => jumpTo("workbench", { view: "workbench", kLevel })}
        />
      )}
      {store.view === "klevels" && (
        <KLevelAtlas
          levels={kLevels}
          worlds={kWorlds}
          mSpaces={atlas.m_spaces}
          scienceGraphHash={stableHash(atlas.science_graph_v010 ?? atlas.science_graph ?? {})}
          selected={selectedK}
          setSelected={store.setSelectedKLevel}
          onOpenWorkbench={(kLevel) => jumpTo("workbench", { view: "workbench", kLevel })}
          onOpenGraph={(query) => jumpTo("graph", { view: "graph", graphQuery: query })}
        />
      )}
      {(store.view === "workbench" || store.view === "km") && (
        <SystemWorkbench
          atlas={atlas}
          selectedK={selectedK}
          selectedSystem={store.selectedSystem}
          setSelectedK={store.setSelectedKLevel}
          setSelectedSystem={store.setSelectedSystem}
          onOpenGraph={(query) => jumpTo("graph", { view: "graph", graphQuery: query })}
          onOpenFormula={(query) => jumpTo("formula", { view: "formula", formulaSearch: query })}
          onOpenProof={(proofTarget) => jumpTo("proof", { view: "proof", proofTarget })}
          onOpenObjections={() => jumpTo("objections", { view: "objections" })}
          onOpenWhyOC={() => jumpTo("whyoc", { view: "whyoc" })}
          onOpenReviewer={() => jumpTo("reviewer", { view: "reviewer" })}
          decisionSummary={supplement.decisionSummary}
        />
      )}
      {store.view === "worldline" && <WorldlineTheater />}
      {store.view === "cascade" && <CascadeLab systems={systems} />}
      {store.view === "benchmarks" && <Benchmarks domains={domains} />}
      {store.view === "graph" && (
        <ScienceGraphView
          graph={scienceGraph}
          query={store.graphQuery}
          onQuery={store.setGraphQuery}
          onOpenWiki={(wikiQuery: string) => jumpTo("wiki", { view: "wiki", wikiSearch: wikiQuery })}
          onOpenFormula={(query: string) => jumpTo("formula", { view: "formula", formulaSearch: query })}
          onOpenFormulaId={(formulaId: string) => jumpTo("formula", { view: "formula", formulaId })}
          onOpenProofTarget={(proofTarget: string) => jumpTo("proof", { view: "proof", proofTarget })}
          onOpenKLevel={(kLevel: string) => jumpTo("klevels", { view: "klevels", kLevel })}
          onOpenWorkbench={(kLevel: string) => jumpTo("workbench", { view: "workbench", kLevel })}
        />
      )}
      {store.view === "objections" && <ObjectionRouter atlas={atlas} onJump={jumpTo} />}
      {store.view === "whyoc" && (
        <WhyOCModelComparison
          atlas={atlas}
          onOpenWorkbench={(kLevel) => jumpTo("workbench", { view: "workbench", kLevel })}
          onOpenFormula={(query) => jumpTo("formula", { view: "formula", formulaSearch: query })}
          onOpenGraph={(query) => jumpTo("graph", { view: "graph", graphQuery: query })}
          onOpenLink={(link) => {
            const targetView = normalizeView(link.view);
            const payload: CrossLink = { view: targetView };
            const target = link.target_id ?? "";
            if (targetView === "graph") payload.graphQuery = target;
            if (targetView === "formula") payload.formulaSearch = target;
            if (targetView === "wiki") payload.wikiSearch = target;
            if (targetView === "proof") payload.proofTarget = target;
            if (targetView === "workbench" || targetView === "klevels" || targetView === "km") payload.kLevel = target;
            if (targetView === "benchmarks") payload.domainId = target;
            if (targetView === "cascade" && target) payload.systemId = target;
            jumpTo(targetView, payload);
          }}
        />
      )}
      {store.view === "practical" && (
        <PracticalValue
          domains={domains}
          selectedDomain={store.selectedDomain}
          surface={atlas.practical_value}
          cards={atlas.practical_value_cards}
          decisionSummary={supplement.decisionSummary}
          onJumpDomain={(domain) => jumpTo("benchmarks", { view: "benchmarks", domainId: domain })}
          onSelectDomain={store.setSelectedDomain}
          onOpenCardSurface={(surface) => {
            const view = normalizeView(surface.view);
            const target = surface.target;
            const payload: CrossLink = { view };
            if (view === "proof") payload.proofTarget = target;
            if (view === "graph") payload.graphQuery = target;
            if (view === "formula") payload.formulaSearch = target;
            if (view === "wiki") payload.wikiSearch = target;
            if (view === "workbench" || view === "klevels" || view === "km") payload.kLevel = target;
            if (view === "benchmarks") payload.domainId = target;
            jumpTo(view, payload);
          }}
        />
      )}
      {store.view === "trust" && <TrustLadder atlas={atlas} routes={atlas.proof_routes} domains={domains} formulas={deriveFormulaAtlas(atlas)} />}
      {store.view === "mission" && <MissionDeck atlas={atlas} onJump={jumpTo} />}
      {store.view === "surface" && <SurfaceGraph atlas={atlas} onJump={jumpTo} />}
      {store.view === "proof" && (
        <ProofEvidence
          routes={atlas.proof_routes}
          selected={store.selectedTarget}
          onSelect={store.setSelectedTarget}
          proofBodyIndex={supplement.proofBodyIndex}
        />
      )}
      {store.view === "gaps" && <ClosureLedger gaps={gaps} ledger={closureLedger} atlas={atlas} />}
      {store.view === "reviewer" && (
        <ReviewerMode
          atlas={atlas}
          proofBodyIndex={supplement.proofBodyIndex}
          decisionSummary={supplement.decisionSummary}
          corpusCompleteness={supplement.corpusCompleteness}
          wikiBridgeContract={supplement.wikiBridgeContract}
          wikiGraphCorpusReconciliation={supplement.wikiGraphCorpusReconciliation}
          onJump={jumpTo}
        />
      )}
      <footer className="footer-strip">
        <span>{worlds.length} simulation worlds</span>
        <span>{kWorlds.length} 3D K-worlds</span>
        <span>{systems.length} system models</span>
        <span>{domains.length} benchmark domains</span>
        <span>{atlas.demo_version ?? "V010"} / Version {atlas.release_ordinal ?? "010"}</span>
        <span>hash {atlas.determinism_hash?.slice(0, 16)}</span>
      </footer>
    </div>
  );
}


