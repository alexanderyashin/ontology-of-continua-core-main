export type Concept = {
  id: string;
  title: string;
  short: string;
  learning_goal: string;
  visual_metaphor: string;
  color: string;
  try_it: string;
  nonclaim: string;
};

export type JourneyStep = {
  id: string;
  title: string;
  concept?: string;
  simulation?: string;
  view?: string;
  k_level_id?: string;
  concept_id?: string;
  minutes: number;
};

export type WorkbenchLink = {
  k_level_id: string;
  concept_id?: string;
  system_id?: string;
  relation?: string;
};

export type WorkbenchConfig = {
  default_system_id?: string;
  default_k_level_id?: string;
  default_concept_id?: string;
  hierarchy_links?: WorkbenchLink[];
};

export type KAxis = {
  axis_id: string;
  title: string;
  direction: string;
  default_value: number;
  k_levels: string[];
  domain_ids: string[];
  claim_status: string;
  interpretation: string;
  nonclaim_boundary: string;
  axis_hash?: string;
  source_status?: string;
  closure_basis?: string;
  min?: number;
  max?: number;
  step?: number;
};

export type MSpace = {
  m_space_id: string;
  semantic_name: string;
  scope: string;
  functions: string[];
  parent_domain: string;
  k_level_bindings: string[];
  domain_bindings: string[];
  operators: string[];
  supported_axes: string[];
  boundary_text: string;
  source_hash?: string;
};

export type SystemTemplate = {
  template_id: string;
  title: string;
  truth_mode: "REPLAY_BACKED" | "EXPLORATORY_SANDBOX" | string;
  fallback_truth_mode: "REPLAY_BACKED" | "EXPLORATORY_SANDBOX" | string;
  k_levels: string[];
  m_spaces: string[];
  nodes: SystemModel["nodes"];
  edges: SystemModel["edges"];
  allowed_axis_ids: string[];
  allowed_axes?: KAxis[];
  editable_actions: string[];
  default_intervention?: Record<string, unknown>;
  assumptions: string[];
  nonclaim_boundary: string;
  template_hash?: string;
};

export type Journey = {
  id: string;
  title: string;
  audience: string;
  promise: string;
  steps: JourneyStep[];
};

export type SimulationSpec = {
  id: string;
  title: string;
  source_title: string;
  concept: string;
  visual_type: string;
  purpose: string;
  output_interpretation: string;
  parameters: Record<string, { type: "number" | "integer" | "string"; default: number | string; min?: number; max?: number }>;
  limits: string[];
  evidence_refs: string[];
};

export type GraphNode = {
  id: string;
  technical_id?: string;
  label: string;
  semantic_label?: string;
  technical_label?: string;
  route: string;
  demo_class: string;
  demo_spec_id: string;
  evidence_class: string;
  statement_excerpt: string;
  quality_flags: string[];
  source_hash?: string;
  layer?: string;
  cluster: string;
  x: number;
  y: number;
  z?: number;
  size: number;
  detail?: {
    proof_target_id?: string;
    proof_route_id?: string;
    wiki_query?: string;
    formula_query?: string;
    nonclaim_boundary?: string;
    rationale?: string;
    node_type?: string;
    k_level?: string;
    k_level_id?: string;
    m_level_id?: string;
    system_id?: string;
    domain_id?: string;
    simulation_id?: string;
    formula_id?: string;
    formula_text?: string;
    unit_id?: string;
    document_id?: string;
    chapter_id?: string;
    replay_status?: string;
    validation_status?: string;
  };
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  relation: string;
  edge_type?: string;
  evidence_ref?: string;
  weight?: number;
};

export type ScienceGraph = {
  summary: {
    node_total: number;
    edge_total: number;
    target_total: number;
    k_level_total?: number;
    domain_total?: number;
    theorem_total?: number;
    formula_node_total?: number;
    corpus_atom_node_total?: number;
    cluster_counts: Record<string, number>;
    layer_counts?: Record<string, number>;
    relation_counts: Record<string, number>;
    root_node_id?: string;
    graph_hash?: string;
  };
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export type ProofRoute = {
  target_id: string;
  label: string;
  status: string;
  demo_class: string;
  demo_spec_id: string;
  evidence_class: string;
  ui_route: string;
  statement_excerpt: string;
  quality_flags: string[];
  source_target_id?: string;
  closure_status?: string;
  closure_basis?: string;
  closure_evidence_hash?: string;
  nonclaim_boundary?: string;
  closure_source_refs?: string[];
  rationale: string;
  non_simulated_reason: string;
  trace: string[];
};

export type TrustLadderEntry = {
  id?: string;
  rung_id?: string;
  title: string;
  summary?: string;
  rationale?: string;
  status?: string;
  basis?: string;
  evidence?: string;
  surface_links?: Array<Record<string, string>>;
};

export type WhyOCComparisonModel = {
  id?: string;
  comparison_id?: string;
  model_id?: string;
  title?: string;
  model_title?: string;
  compared_model?: string;
  compared_model_id?: string;
  domain?: string;
  model_kind?: string;
  strengths?: string[];
  limitations?: string[];
  native_strength?: string;
  oc_adds?: string;
  does_not_replace?: string;
  nonreplacement_text?: string;
  concrete_decision?: string;
  native_preferable_case?: string;
  decision_rubric?: Record<string, string>;
  when_not_to_use?: string;
  comparison_axes?: string[];
  comparison_criteria?: string[];
  comparison_assumptions?: string[];
  formula_refs?: string[];
  baseline_evidence?: string[];
  claim_status?: string;
  trust_status?: string;
  when_to_use?: string;
  nonclaim_boundary?: string;
  surface_links?: Array<Record<string, string>>;
};

export type KLevelExample = {
  k_level?: string;
  k_level_id?: string;
  title?: string;
  objective?: string;
  route?: string;
  proof_target?: string;
  expected_mode?: string;
  formula_query?: string;
  graph_query?: string;
  workbench_k_level?: string;
  nonclaim_boundary?: string;
};

export type PracticalValueSurface = {
  headline?: string;
  claims?: string[];
  use_cases?: string[];
  proof_link_targets?: string[];
};

export type PracticalValueCard = {
  card_id: string;
  title: string;
  audience: string;
  value_statement: string;
  practical_value: string;
  linked_routes?: string[];
  linked_missions?: string[];
  linked_rungs?: string[];
  linked_comparison_rows?: string[];
  surfaces?: Array<Record<string, string>>;
};

export type MissionDeckCard = {
  id: string;
  title: string;
  status?: string;
  objective?: string;
  action_label?: string;
  action_view?: string;
  action_query?: string;
  template_id?: string;
  target_system_id?: string;
  stage_sequence?: string[];
  claim_status?: string;
  nonclaim_boundary?: string;
  steps?: Array<Record<string, string | number | string[]>>;
};

export type ReviewerObjectionRoute = {
  id: string;
  title: string;
  audience: string;
  severity: string;
  promise: string;
  steps: Array<Record<string, string | number | string[]>>;
  links_to_real_surfaces: Array<Record<string, string>>;
  nonclaim_boundary: string;
};

export type SystemFlowRow = {
  flow_id?: string;
  system_id: string;
  source: string;
  target: string;
  flow_channel?: string;
  flow_direction?: string;
  weight?: number;
  k_level?: string;
  k_levels?: string[];
  claim_status?: string;
  source_status?: string;
  nonclaim_boundary?: string;
  flow_hash?: string;
  [key: string]: unknown;
};

export type SystemCycleRow = {
  cycle_id?: string;
  system_id: string;
  title?: string;
  nodes?: string[];
  cycle_kind?: string;
  direction?: string;
  claim_status?: string;
  source_status?: string;
  nonclaim_boundary?: string;
  cycle_hash?: string;
  k_level?: string;
  k_levels?: string[];
  [key: string]: unknown;
};

export type ThresholdRow = {
  threshold_id?: string;
  system_id: string;
  node_id?: string;
  title?: string;
  axis_id?: string;
  threshold_type?: string;
  value?: number;
  k_levels?: string[];
  claim_status?: string;
  source_status?: string;
  interpretation?: string;
  nonclaim_boundary?: string;
  threshold_hash?: string;
  k_level?: string;
  [key: string]: unknown;
};

export type CompensatorRow = {
  compensator_id?: string;
  system_id: string;
  node_id?: string;
  title?: string;
  mode?: string;
  default_delta?: number;
  claim_status?: string;
  source_status?: string;
  nonclaim_boundary?: string;
  compensator_hash?: string;
  k_level?: string;
  k_levels?: string[];
  [key: string]: unknown;
};

export type CerberusReviewFinding = {
  head?: string;
  head_id?: string;
  severity?: string;
  status?: string;
  finding_summary?: string;
  finding_id?: string;
  source_refs?: string[];
  nonclaim_boundary?: string;
};

export type CerberusReviewSummary = {
  unresolved_total?: number;
  unresolved_minor_total?: number;
  unresolved_medium_plus_total?: number;
  baseline_finding_total?: number;
  heads_present?: string[];
  findings_by_head?: Record<string, number>;
  headline?: string;
  finding_count?: number;
  findings?: CerberusReviewFinding[];
};

export type CerberusReviewPayload = {
  status?: string;
  summary?: CerberusReviewSummary;
  review_hash?: string;
  review_summary?: string;
  source_file?: string;
  failure_reason_codes?: string[];
};

export type CorpusCompletenessReport = {
  schema_version?: string;
  demo_version?: string;
  release_ordinal?: string;
  scope?: string;
  counts?: {
    available_pass_units?: number;
    generated_atoms?: number;
    coverage_ratio?: number;
    bounded_exclusions?: number;
    status_breakdown?: Record<string, number>;
  };
  bounded_exclusions?: string[];
  report_hash?: string;
};

export type ProofBodyIndex = {
  schema_version?: string;
  demo_version?: string;
  release_ordinal?: string;
  route_total?: number;
  proof_closed_total_excluding_obligations?: number;
  boundary_or_obligation_total?: number;
  status_counts?: Record<string, number>;
  proof_carrying_hash_lineage?: Record<string, unknown>;
  evidence_score_summary?: Record<string, unknown>;
  full_route_inventory_contract?: Record<string, unknown>;
  rows?: Array<{
    target_id?: string;
    closure_status?: string;
    evidence_score?: number;
    raw_weighted_score?: number;
    capped_score?: number;
    evidence_score_label?: string;
    score_kind?: string;
    score_cap?: number;
    score_component_basis?: Record<string, number>;
    score_not_proof_warning?: string;
    proof_class?: string;
    evidence_hash?: string;
    source_refs?: string[];
    proof_carrying_hash_basis?: string[];
    elevated_boundary_warning?: string;
    famous_open_problem_name?: string;
    open_problem_boundary_required?: boolean;
  }>;
  nonclaim_boundary?: string;
  index_hash?: string;
};

export type PracticalValueDecisionDeliverable = {
  value_id: string;
  decision_improved: string;
  three_minute_action?: string;
  export_preview?: string;
  safe_cta?: string;
};

export type PracticalValueDecisionSummary = {
  schema_version?: string;
  demo_version?: string;
  release_ordinal?: string;
  buyer_fit_workflow?: string[];
  bounded_cta?: string;
  buyer_personas?: Array<{ persona: string; value_metric: string; thresholds?: Record<string, string> }>;
  before_after_panel?: {
    baseline?: Record<string, number>;
    after_improvement?: Record<string, number>;
    delta?: Record<string, number>;
    metric_formula_bindings?: Array<Record<string, unknown>>;
    changed_assumption?: string;
    export_hash_basis?: string;
    interpretation?: string;
  };
  evaluation_thresholds?: Record<string, Record<string, string>>;
  mission_outcome_table?: Array<{
    mission_id: string;
    mission_name: string;
    target_user: string;
    expected_local_decision: string;
    primary_metric: string;
    export_artifact: string;
    route_or_surface: string;
    evaluated_status?: string;
    metric_deltas?: Record<string, number>;
    threshold_verdict?: string;
    bounded_next_step?: string;
    export_hash?: string;
    content_delta_assertions?: string[];
  }>;
  local_success_criterion?: string;
  deterministic_next_step_outcome?: {
    status?: string;
    basis?: string[];
    outcome_hash?: string;
    safe_cta?: string;
  };
  local_request_packet_preview?: {
    status?: string;
    request_type?: string;
    selected_surface?: string;
    included_fields?: string[];
    explicit_non_action?: string;
    request_hash?: string;
    next_step_rule?: string;
  };
  mission_total?: number;
  deliverable_total?: number;
  deliverables?: PracticalValueDecisionDeliverable[];
  mission_ids?: string[];
  nonclaim_boundary?: string;
  summary_hash?: string;
};

export type Atlas = {
  schema_version: string;
  demo_version?: string;
  release_ordinal?: string;
  release_label?: string;
  edition?: "public" | "private";
  title: string;
  generated_from?: Record<string, number>;
  source_status?: { generated_from: Record<string, number> };
  build_policy?: Record<string, unknown>;
  concepts: Concept[];
  journeys: Journey[];
  simulations?: SimulationSpec[];
  simulation_worlds?: SimulationWorld[];
  k_level_worlds?: KLevelWorld[];
  system_zoo?: SystemModel[];
  graph: ScienceGraph;
  proof_routes: ProofRoute[];
  glossary?: Array<{ term: string; definition: string; concept_id?: string }>;
  wiki?: OCWiki;
  k_levels?: KLevel[];
  domain_benchmarks?: DomainBenchmark[];
  science_graph?: ScienceGraph;
  science_graph_v010?: ScienceGraph;
  science_graph_v009?: ScienceGraph;
  science_graph_v007?: ScienceGraph;
  graph_v007?: ScienceGraph;
  science_graph_v006?: ScienceGraph;
  system_workbench?: WorkbenchConfig;
  system_workbench_schema?: Record<string, unknown>;
  didactic_routes?: Journey[];
  reviewer_objection_routes?: ReviewerObjectionRoute[];
  route_action_manifest?: Array<Record<string, unknown>>;
  k_axes?: KAxis[];
  m_spaces?: MSpace[];
  system_templates?: SystemTemplate[];
  k_level_example_atlas?: KLevelExample[] | Record<string, KLevelExample[]>;
  demonstrator_surface_graph?: {
    summary?: Record<string, number>;
    surfaces?: Array<Record<string, any>>;
    controls?: Array<Record<string, any>>;
    routes?: Array<Record<string, any>>;
    nodes?: Array<Record<string, any>>;
    edges?: Array<Record<string, any>>;
    prebuild_gate?: Record<string, any>;
    surface_graph_hash?: string;
  };
  persona_user_story_map?: Record<string, unknown>;
  formula_formalization_obligations?: Record<string, unknown>;
  system_architect_missions?: MissionDeckCard[];
  practical_value?: PracticalValueSurface;
  practical_value_decision_summary?: PracticalValueDecisionSummary;
  practical_value_cards?: PracticalValueCard[];
  model_comparison_matrix?: WhyOCComparisonModel[];
  system_flows?: SystemFlowRow[];
  system_cycles?: SystemCycleRow[];
  thresholds?: ThresholdRow[];
  compensators?: CompensatorRow[];
  collapse_paths?: Array<Record<string, unknown>>;
  entity_link_index?: Record<string, unknown>;
  formula_atlas?: FormulaRow[];
  corpus_completeness_report?: CorpusCompletenessReport;
  corpus_index?: CorpusAtom[];
  proof_body_index?: ProofBodyIndex;
  research_gaps?: ResearchGap[];
  research_gap_summary?: ResearchGapSummary;
  closure_ledger?: ClosureLedgerRow[];
  proof_placeholder_closure_ledger?: ProofPlaceholderClosureLedger;
  evidence_roles?: Array<{ id: string; title: string; definition: string }>;
  reviewer_mode?: { checklist: string[]; external_actions: number };
  why_oc?: {
    title?: string;
    mission_text?: string;
    comparisons?: WhyOCComparisonModel[];
    trust_ladder?: TrustLadderEntry[];
  };
  mission_deck?: MissionDeckCard[];
  trust_ladder?: TrustLadderEntry[] | { title?: string; entries?: TrustLadderEntry[] };
  science_graph_v008?: ScienceGraph;
  cerberus_review?: CerberusReviewPayload;
  determinism_hash?: string;
};

export type WikiChapter = {
  id: string;
  document_id?: string;
  order: number;
  title: string;
  sections: Array<{ heading: string; paragraphs: string[] }>;
  claim_trace: string[];
  residual_uncertainties: string[];
  atom_count?: number;
};

export type OCWiki = {
  glossary: Array<{ term: string; definition: string }>;
  postulates: Array<{ id: string; title: string; statement: string; test: string }>;
  operators: Array<{ id: string; title: string; effect: string }>;
  chapters: WikiChapter[];
  corpus_summary?: { atom_count: number; documents: Record<string, number>; chapter_count: number; full_corpus_mode: string };
  corpus_atoms?: CorpusAtom[];
  formulas: FormulaRow[];
};

export type CorpusAtom = {
  unit_id: string;
  source_unit_id: string;
  document_id: string;
  chapter_id: string;
  chapter_title: string;
  section_id: string;
  title?: string;
  text: string;
  search_text: string;
  source_hash: string;
  target_pdf_filename: string;
  formula_query: string;
  proof_query: string;
};

export type FormulaRow = {
  ordinal?: number;
  formula_id: string;
  formula_text: string;
  formula?: string;
  status: string;
  title?: string;
  formula_title?: string;
  semantic_title?: string;
  domain?: string;
  interpretation?: string;
  quality_status?: string;
  formula_class?: string;
  symbol_refs: string[];
  operator_meanings?: Array<{ symbol: string; meaning: string }>;
  operator_glossary?: Array<{ symbol: string; meaning: string }>;
  operators?: Array<{ symbol: string; meaning: string }>;
  operator_summary?: string;
  consequences?: string[];
  chart_spec?: {
    chart_id?: string;
    kind?: string;
    x_axis?: string;
    y_axis?: string;
    threshold?: number;
    points?: Array<{ x: number; y: number }>;
    nonclaim_boundary?: string;
  };
  diagnostic_chart?: FormulaRow["chart_spec"];
  source_unit_id?: string;
  source_view_id?: string;
  source_atom_id?: string;
  source_link?: string;
  source_link_label?: string;
  source_hash?: string;
  source_refs?: string[];
  formula_source_refs?: string[];
  source_boundary?: string;
  boundary?: string;
  nonclaim_boundary?: string;
  assumptions?: string[];
  assumption_bodies?: Array<{ assumption_id: string; text: string; text_hash?: string; status?: string }>;
  validation_rules?: string[];
  validation_rule_bodies?: Array<{ rule_id: string; rule_text: string; status: string; hash_basis?: string[] }>;
  typed_symbol_signatures?: Array<{ symbol: string; type?: string; role?: string; meaning?: string }>;
  symbol_table?: Array<{ symbol: string; type?: string; role?: string; domain?: string; range?: string; default_value?: number | null; source_boundary?: string }>;
  dimension_checks?: {
    status?: string;
    dimension_vector?: Record<string, string>;
    operation_checks?: Array<{ operation: string; operand_dimension: string; status: string; explanation: string }>;
    denominator_terms?: string[];
    nonclaim_boundary?: string;
  };
  formula_role_contract?: {
    status?: string;
    formula_family_id?: string;
    required_visible_roles?: string[];
    nonclaim_boundary?: string;
  };
  formula_subderivations?: Array<{
    formula_role_id: string;
    formula_subtype: string;
    canonical_expression: string;
    symbols?: string[];
    input_fields?: string[];
    output_fields?: string[];
    meaning?: string;
  }>;
  denominator_guards?: Array<{ guard: string; status: string; failure_behavior: string }>;
  dimensional_consistency_status?: string;
  ui_probe_contract?: { probe_id?: string; surface?: string; workbench_binding?: string; expected_visible_result?: string; deterministic?: boolean };
  formula_boundary_mapping?: { status?: string; target_route?: string; nonclaim_boundary?: string };
  render_mode?: "katex" | "plain";
  katex_ready?: boolean;
};

export type KLevel = {
  level_id: string;
  meaning: string;
  semantic_summary: string;
  domain_projections: string[];
  domain_projection_boundary?: string;
  terminal_status: string;
  model_boundary_status: string;
  theorem_admissibility_status: string;
  quantitative_prediction_readiness: string;
  preserved_invariants: string;
  confidence?: number;
  confidence_basis: string;
  applicability_bounds: string[];
  simulation_status: string;
  simulation_summary: Record<string, boolean>;
  artifact_sha256?: string;
  model_hash?: string;
  closure_status?: string;
  closure_basis?: string;
  proof_refs?: string[];
  source_refs?: string[];
  lower_dependencies?: string[];
  top_down_constraints?: string[];
  nonclaim_boundary?: string;
  scenario_matrix: Array<Record<string, unknown>>;
};

export type DomainBenchmark = {
  domain_id: string;
  title: string;
  source_status: string;
  prediction_status: string;
  promotion_state: string;
  closure_status?: string;
  closure_basis?: string;
  replay_status?: string;
  validation_status?: string;
  replay_hashes?: string[];
  claim_level?: string;
  closure_program_status?: string;
  pass_semantics?: string;
  prediction_boundary?: string;
  pass_does_not_mean?: string;
  claim_display_policy?: string;
  source_refs?: string[];
  measurable_outputs: string[];
  nonclaim_boundary: string;
  theorem_to_observable_map: string[];
  benchmark_dataset_manifest: Array<Record<string, string>>;
  case_total: number;
  held_out_case_total?: number;
  benchmark_pending_execution_total?: number;
  benchmark_executed_prediction_total?: number;
  raw_claim_level?: string;
  benchmark_cases: Array<Record<string, string>>;
};

export type SimulationWorld = {
  id: string;
  world_id?: string;
  title: string;
  type: string;
  purpose: string;
  default_params: Record<string, number | string>;
  assumptions: string[];
  source_status: string;
};

export type KLevelWorld = {
  world_id: string;
  level_id: string;
  title: string;
  meaning: string;
  semantic_summary: string;
  nodes: Array<{ id: string; label: string; role: string; x: number; y: number; z: number; health: number }>;
  links: Array<{ source: string; target: string; relation: string; weight: number }>;
  kill_options: string[];
  replay_status: string;
  closure_status: string;
  artifact_sha256?: string;
  nonclaim_boundary: string;
  world_hash: string;
};

export type SystemModel = {
  id: string;
  title: string;
  k_levels: string[];
  critical_nodes: string[];
  dependencies: Array<[string, string]>;
  nodes?: Array<{ id: string; label: string; role: string; x: number; y: number; z: number; vulnerability: number; resilience: number; recovery_capacity: number; health: number }>;
  edges?: Array<{ id: string; source: string; target: string; weight: number; flow_channel: string }>;
  weakest_node?: string;
  model_hash?: string;
  kill_default: string;
  what_it_shows: string;
  nonclaim: string;
};

export type ResearchGap = {
  gap_id: string;
  kind: string;
  title: string;
  status: string;
  missing_evidence: string;
  requested_action: string;
  source_ref: string;
  severity: string;
};

export type ResearchGapSummary = {
  open_count: number;
  closure_rows: number;
  closed_count: number;
  counts_by_status: Record<string, number>;
  proof_placeholder_rows_closed: number;
  nonclaim_boundary: string;
};

export type ClosureLedgerRow = {
  gap_id: string;
  kind: string;
  title: string;
  closure_status: string;
  closure_basis: string;
  source_refs: string[];
  evidence_hash: string;
  closed_at_build: string;
  nonclaim_boundary: string;
};

export type ProofPlaceholderClosureLedger = {
  schema_version: string;
  demo_version: string;
  release_ordinal: string;
  status: string;
  placeholder_rows_closed: number;
  open_placeholder_rows: number;
  ledger_hash?: string;
  rows: Array<Record<string, string>>;
};
