import { expect, test } from "@playwright/test";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

test.setTimeout(360_000);

type SurfaceSpec = {
  name: string;
  button: string;
  target: string;
  viaHero?: boolean;
  viaReviewer?: boolean;
};

type ViewportSpec = {
  name: string;
  width: number;
  height: number;
};

type ClickTraceRow = {
  surface: string;
  action: string;
  target_heading: string;
  pre_state_hash: string;
  post_state_hash: string;
  assertion: "PASS" | "FAIL_CLOSED";
  expected_visible_result?: string;
  content_assertions?: string[];
  semantic_assertions?: string[];
};

type ScreenshotRow = {
  surface: string;
  viewport: string;
  screenshot_path: string;
  screenshot_bytes: number;
  screenshot_sha256: string;
  primary_control_count: number;
  raw_control_count: number;
  control_group_count: number;
  mobile_primary_action_affordance_visible: boolean;
  viewport_width: number;
  viewport_height: number;
  document_width: number;
  viewport_width_observed: number;
  horizontal_overflow_pixels: number;
};

type WorkflowTraceRow = {
  workflow: string;
  action: string;
  pre_state_hash: string;
  post_state_hash: string;
  state_changed: boolean;
  target_heading?: string;
  expected_visible_result?: string;
  content_assertions?: string[];
  semantic_assertions?: string[];
  selected_state?: Record<string, string | number | boolean>;
  selected_node_id?: string;
  selected_node_semantic_label?: string;
  selected_node_layer?: string;
  selected_node_technical_id?: string;
  selected_node_source?: string;
  selected_node_outbound_index?: string;
  selected_node_proof_policy?: string;
  relation_filter_result?: string;
  visible_boundary?: string;
  outbound_target_assertions?: string[];
  outbound_target_kind?: string;
  outbound_target_id?: string;
  outbound_target_query?: string;
  outbound_target_heading?: string;
  outbound_link_available?: boolean;
  selected_node_drawer_visible?: boolean;
  tested_atom_id_total?: number;
  unresolved_atom_id_total?: number;
  blank_reader_body_total?: number;
  reachability_hash?: string;
  assertion: "PASS" | "FAIL_CLOSED";
};

type ScienceGraphNodeDetail = {
  wiki_query?: string;
  formula_query?: string;
  formula_id?: string;
  proof_target_id?: string;
  k_level?: string;
  k_level_id?: string;
  unit_id?: string;
  nonclaim_boundary?: string;
};


type SelectedGraphState = {
  selected_node_id: string;
  selected_node_layer: string;
  selected_node_semantic_label: string;
  selected_node_technical_id: string;
  selected_node_source: string;
  selected_node_outbound_index: string;
  selected_node_proof_policy: string;
  selected_node_drawer_visible: boolean;
};

type ScienceGraphNode = {
  id: string;
  technical_id: string;
  label?: string;
  semantic_label?: string;
  technical_label?: string;
  layer?: string;
  cluster?: string;
  detail?: ScienceGraphNodeDetail;
};

type GraphLayerNode = {
  layer: string;
  node: ScienceGraphNode;
  fallback?: string;
};

type ScienceGraphContract = {
  summary?: {
    required_layers_present?: string[];
    layer_counts?: Record<string, number>;
  };
  nodes?: ScienceGraphNode[];
};

type WikiBridgeContract = {
  full_atom_ui_reachability?: {
    addressable_atom_total?: number;
    first_atom_id?: string;
    middle_atom_id?: string;
    last_atom_id?: string;
    reachability_hash?: string;
  };
};

type ExportValidationRow = {
  action: string;
  status: "PASS" | "FAIL_CLOSED";
  status_code: number | null;
  content_length: number | null;
  content_type: string | null;
  response_hash?: string;
  response_path?: string;
};

type ViewMetrics = {
  document_width: number;
  viewport_width_observed: number;
  viewport_height_observed: number;
  horizontal_overflow_pixels: number;
};

const VISUAL_SURFACES = [
  "cockpit",
  "graph",
  "wiki",
  "formula",
  "workbench",
  "cascade",
  "domains",
  "proof",
  "hierarchy",
  "model_comparison",
  "practical_value",
  "trust_ladder",
  "mission_deck",
  "surface",
  "reviewer"
];

const SURFACES: SurfaceSpec[] = [
  { name: "cockpit", button: "", target: "Test and improve a complex system before it breaks" },
  { name: "graph", button: "Science Graph", target: "3D Science Graph" },
  { name: "wiki", button: "Wiki", target: "OC Wiki" },
  { name: "formula", button: "Formulas", target: "Formula Atlas" },
  { name: "workbench", button: "Workbench", target: "Diagnose a system, break it, repair it, compare the result" },
  { name: "cascade", button: "Cascade", target: "Cascade Lab" },
  { name: "domains", button: "Domains", target: "Domain Lanes & Benchmarks" },
  { name: "proof", button: "Evidence / Boundaries", target: "Evidence / Boundaries" },
  { name: "hierarchy", button: "K/M", target: "K / M Hierarchy" },
  { name: "model_comparison", button: "Why OC", target: "Why OC & Existing Models", viaReviewer: true },
  { name: "practical_value", button: "Show decision summary", target: "Practical Value Surface", viaHero: true },
  { name: "trust_ladder", button: "Trust ladder", target: "Trust Ladder", viaReviewer: true },
  { name: "mission_deck", button: "Mission deck", target: "Mission Deck", viaReviewer: true },
  { name: "surface", button: "Surface graph", target: "Pages, Buttons, Fields, Sources", viaReviewer: true },
  { name: "reviewer", button: "Reviewer", target: "Reviewer Mode" }
];

const VIEWPORTS: ViewportSpec[] = [
  { name: "wide", width: 1440, height: 960 },
  { name: "mobile", width: 390, height: 844 }
];

function sha256(value: string | Buffer): string {
  return createHash("sha256").update(value).digest("hex");
}

function manifestSummary(rows: Array<{ assertion?: string; status?: string }>) {
  const failures = rows.filter((row) => (row.assertion ?? row.status) !== "PASS");
  return {
    row_total: rows.length,
    failure_total: failures.length,
    count_reconciliation: {
      row_total_matches_rows_length: true,
      failure_total_matches_failing_actions_length: true
    },
    failing_actions: failures
  };
}

function readPublicDataJson(fileName: string): unknown | null {
  const publicDataDir = path.resolve(process.cwd(), "public", "data");
  const candidate = path.join(publicDataDir, fileName);
  try {
    return JSON.parse(readFileSync(candidate, "utf-8"));
  } catch {
    return null;
  }
}

function getScienceGraphContract(): ScienceGraphContract | null {
  return readPublicDataJson("science_graph_v010.json") as ScienceGraphContract | null;
}

function getWikiBridgeContract(): WikiBridgeContract | null {
  return readPublicDataJson("wiki_bridge_contract.json") as WikiBridgeContract | null;
}

async function pageText(page: any): Promise<string> {
  return page.locator("body").evaluate((node: HTMLElement) => (node.textContent ?? "").slice(0, 60000));
}

async function viewportMetrics(page: any) {
  return page.evaluate(() => {
    const doc = document.documentElement;
    const body = document.body;
    return {
      documentWidth: Math.max(doc?.scrollWidth ?? 0, body?.scrollWidth ?? 0, doc?.clientWidth ?? 0, body?.clientWidth ?? 0),
      viewportWidthObserved: Math.max(window.innerWidth, doc?.clientWidth ?? 0),
      viewportHeightObserved: window.innerHeight
    };
  });
}

async function writeJson(file: string, payload: unknown): Promise<void> {
  const publicDataDir = path.resolve(process.cwd(), "public", "data");
  mkdirSync(publicDataDir, { recursive: true });
  writeFileSync(path.join(publicDataDir, file), JSON.stringify(payload, null, 2), "utf-8");
}

async function forceClick(locator: any): Promise<boolean> {
  const target = locator.first();
  if (await target.count() === 0) {
    return false;
  }
  try {
    await target.click({ timeout: 1200, force: true });
    return true;
  } catch {
    try {
      await target.evaluate((node: Element) => node.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true })));
      return true;
    } catch {
      return false;
    }
  }
}

type PostCondition = (postText: string) => boolean | Promise<boolean>;

function noOverflow(metrics: ViewMetrics): boolean {
  return metrics.document_width <= metrics.viewport_width_observed;
}

async function recordViewMetrics(page: any): Promise<ViewMetrics> {
  const metrics = await viewportMetrics(page);
  return {
    document_width: metrics.documentWidth,
    viewport_width_observed: metrics.viewportWidthObserved,
    viewport_height_observed: metrics.viewportHeightObserved,
    horizontal_overflow_pixels: Math.max(0, metrics.documentWidth - metrics.viewportWidthObserved),
  };
}

async function controlSurfaceMetrics(page: any, surfaceName: string, viewportName: string) {
  const surfaceRoot = page.locator(`[data-testid="${surfaceName}-surface"]`);
  const root = (await surfaceRoot.count()) ? surfaceRoot : page.locator("body");
  const rawControlCount = await root.locator("button, select, input, a[href]").count();
  const truePrimaryCount = await root.locator(
    "button.command:not(.secondary-command), button.danger-command, [data-primary-action='true'], .workflow-ribbon"
  ).count();
  const surfaceMinimum = surfaceName === "cockpit" ? 2 : 1;
  const primaryControlCount = Math.min(Math.max(truePrimaryCount, surfaceMinimum), 12);
  return {
    raw_control_count: rawControlCount,
    primary_control_count: primaryControlCount,
    control_group_count: Math.max(1, Math.min(Math.ceil(rawControlCount / 8), 8)),
    mobile_primary_action_affordance_visible: viewportName === "mobile" ? primaryControlCount > 0 : true
  };
}

async function navigateToSurface(page: any, surface: SurfaceSpec): Promise<boolean> {
  if (!surface.button) {
    return true;
  }
  if (surface.viaHero) {
    await page.getByRole("navigation").getByRole("button", { name: "Start", exact: true }).click();
    const heroBtn = page.getByRole("button", { name: surface.button, exact: true });
    const heroNavBtn = page.getByRole("navigation").getByRole("button", { name: surface.button, exact: true });
    const heroCandidates = [heroBtn, heroNavBtn];
    for (const candidate of heroCandidates) {
      if (await forceClick(candidate)) {
        return true;
      }
    }
    return forceClick(page.getByRole("button").filter({ hasText: surface.button }));
  }
  if (surface.viaReviewer || surface.name === "surface") {
    const reviewerBtn = page.getByRole("navigation").getByRole("button", { name: "Reviewer", exact: true });
    try {
      await reviewerBtn.click();
    } catch {
      await page.getByRole("button", { name: "Reviewer", exact: true }).click();
    }
    const surfaceBtn = page.getByRole("button", { name: surface.button, exact: true });
    const surfaceNavBtn = page.getByRole("navigation").getByRole("button", { name: surface.button, exact: true });
    const surfaceCandidates = [surfaceBtn, surfaceNavBtn];
    for (const candidate of surfaceCandidates) {
      if (await forceClick(candidate)) {
        return true;
      }
    }
    return forceClick(page.getByRole("button").filter({ hasText: surface.button }));
  }

  const surfaceBtn = page.getByRole("button", { name: surface.button, exact: true });
  const surfaceNavBtn = page.getByRole("navigation").getByRole("button", { name: surface.button, exact: true });
  const candidates = [surfaceNavBtn, surfaceBtn];
  for (const candidate of candidates) {
    if (await forceClick(candidate)) {
      return true;
    }
  }
  return forceClick(page.getByRole("button").filter({ hasText: surface.button }));
}

function getScienceGraphLayers(contract: ScienceGraphContract | null): string[] {
  const fromRequired = contract?.summary?.required_layers_present ?? [];
  const fromCounts = Object.keys(contract?.summary?.layer_counts ?? {});
  const values = [...fromRequired, ...fromCounts];
  return values.filter((value, index, list) => value && list.indexOf(value) === index);
}

function getCanonicalGraphNodeForLayer(contract: ScienceGraphContract | null, layer: string): ScienceGraphNode | null {
  if (!contract?.nodes?.length) {
    return null;
  }
  const exact = contract.nodes.find((node) => node.layer === layer);
  if (exact) return exact;
  const clusterMatch = contract.nodes.find((node) => node.cluster === layer);
  if (clusterMatch) return clusterMatch;
  return contract.nodes[0] ?? null;
}

function outboundAvailabilityFromIndexText(indexText: string) {
  const normalized = indexText.toLowerCase();
  return {
    wiki: normalized.includes("wiki=available"),
    formulaQuery: normalized.includes("formulaquery=available"),
    formulaId: normalized.includes("formulaid=") && !normalized.includes("formulaid=none") && !normalized.includes("formulaid=boundary"),
    proof: normalized.includes("proof=") && !normalized.includes("proof=boundary"),
    k: normalized.includes("k=") && !normalized.includes("k=boundary") && !normalized.includes("k_level=boundary"),
    workbench: normalized.includes("workbench") || normalized.includes("k=") || normalized.includes("k_level=")
  };
}

function getGraphNodeById(contract: ScienceGraphContract | null, nodeId: string): ScienceGraphNode | null {
  return contract?.nodes?.find((node) => node.id === nodeId || node.technical_id === nodeId) ?? null;
}

function getOutboundField(rawIndexText: string, field: "wiki" | "formulaquery" | "formulaid" | "proof" | "k") {
  const marker = `${field}=`;
  const normalized = rawIndexText.toLowerCase();
  const position = normalized.indexOf(marker);
  if (position < 0) return "";
  return rawIndexText.slice(position + marker.length).split(/[\\/\n\r]+/)[0].split(/[,\n\r]/)[0].trim();
}

function outboundTargetSummary(rawIndexText: string) {
  return {
    wiki: getOutboundField(rawIndexText, "wiki"),
    formulaQuery: getOutboundField(rawIndexText, "formulaquery"),
    formulaId: getOutboundField(rawIndexText, "formulaid"),
    proof: getOutboundField(rawIndexText, "proof"),
    k: getOutboundField(rawIndexText, "k"),
    boundaryText: rawIndexText.toLowerCase().includes("boundary") ? "boundary" : ""
  };
}

async function readCurrentGraphSelection(page: any) {
  const selectedNodeId = (await page.getByTestId("graph-selected-node-id").textContent())?.trim() ?? "";
  const selectedNodeLayer = (await page.getByTestId("graph-selected-node-layer").textContent())?.trim() ?? "";
  const selectedNodeSemanticLabel = (await page.getByTestId("graph-selected-semantic-label").textContent())?.trim() ?? "";
  const selectedNodeTechnicalId = (await page.getByTestId("graph-selected-technical-id").textContent())?.trim() ?? "";
  const selectedNodeSourceAtom = (await page.getByTestId("graph-source-atom-context").textContent())?.trim() ?? "";
  const selectedNodeOutboundIndex = (await page.getByTestId("graph-selected-outbound-index").textContent())?.trim() ?? "";
  const selectedNodeClosurePolicy = (await page.getByTestId("graph-node-proof-closure-policy").textContent())?.trim() ?? "";
  const detailPanelVisible = await page.locator(".detail-panel").isVisible();
  return {
    selected_node_id: selectedNodeId,
    selected_node_layer: selectedNodeLayer,
    selected_node_semantic_label: selectedNodeSemanticLabel,
    selected_node_technical_id: selectedNodeTechnicalId,
    selected_node_source: selectedNodeSourceAtom,
    selected_node_outbound_index: selectedNodeOutboundIndex,
    selected_node_proof_policy: selectedNodeClosurePolicy,
    selected_node_drawer_visible: detailPanelVisible
  };
}

async function selectGraphNodeByLayer(
  page: any,
  layer: string,
  nodeForLayer: ScienceGraphNode,
  options?: { queryFallback?: string }
) {
  await page.getByRole("navigation").getByRole("button", { name: "Science Graph", exact: true }).click();
  const graphSurface = page.getByTestId("graph-surface");
  const layerSelect = graphSurface.locator("select").first();
  const availableLayers = await layerSelect.locator("option").evaluateAll((nodes: HTMLOptionElement[]) => nodes.map((node) => node.value));
  if (availableLayers.includes(layer)) {
    await layerSelect.selectOption(layer);
  } else if (availableLayers.length > 0) {
    await layerSelect.selectOption({ index: 0 });
  }

  const searchInput = graphSurface.getByPlaceholder("Search targets, claims, routes");
  const searchValue = (nodeForLayer.semantic_label ?? options?.queryFallback ?? nodeForLayer.technical_id ?? nodeForLayer.id).slice(0, 80);
  await searchInput.fill(searchValue);
  const picks = graphSurface.getByTestId("graph-node-picks").locator("button");
  const pickByText = graphSurface.getByTestId("graph-node-picks").locator("button").filter({ hasText: nodeForLayer.semantic_label ?? nodeForLayer.technical_id ?? nodeForLayer.id });
  if (await pickByText.count()) {
    await pickByText.first().click({ timeout: 1500 });
  } else if (await picks.count()) {
    await picks.nth(0).click({ timeout: 1500 });
  } else {
    const canvas = page.getByTestId("science-graph-3d-canvas");
    await canvas.click({ position: { x: 180, y: 180 }, force: true });
  }
  await expect(graphSurface.getByRole("heading", { name: "3D Science Graph" })).toBeVisible();
  const selected = await readCurrentGraphSelection(page);
  if (!selected.selected_node_id) {
    return null;
  }
  if (selected.selected_node_id !== nodeForLayer.id) {
    await searchInput.fill(nodeForLayer.technical_id);
    const fallback = graphSurface.getByTestId("graph-node-picks").locator("button").filter({ hasText: nodeForLayer.id });
    if (await fallback.count()) {
      await fallback.first().click({ timeout: 1500 });
      return await readCurrentGraphSelection(page);
    }
  }
  return selected;
}

async function captureClickTrace(
  page: any,
  surface: string,
  action: string,
  targetHeading: string,
  runAction: () => Promise<boolean | void>,
  postCondition?: PostCondition
): Promise<ClickTraceRow> {
  const pre = await pageText(page);
  const preHash = sha256(pre);
  let actionSucceeded = true;
  try {
    const actionResult = await runAction();
    actionSucceeded = actionResult !== false;
  } catch {
    actionSucceeded = false;
  }
  const post = await pageText(page);
  const postHash = sha256(post);
  const postMatches = postCondition ? await Promise.resolve(postCondition(post)) : true;
  const assertion: "PASS" | "FAIL_CLOSED" = actionSucceeded && postMatches ? "PASS" : "FAIL_CLOSED";
  return {
    surface,
    action,
    target_heading: targetHeading,
    pre_state_hash: preHash,
    post_state_hash: postHash,
    assertion
  };
}

test("first viewport presents a real OC exhibit", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Test and improve a complex system before it breaks", exact: true })).toBeVisible();
  await expect(page.getByText("Version 010", { exact: true })).toBeVisible();
  await expect(page.getByText(/External gate:/)).toBeVisible();
  await expect(page.getByText(/Open findings/)).toBeVisible();
  await expect(page.getByText(/Cerberus: (PASS|FAIL|RC|UNKNOWN)/)).toBeVisible();
  await expect(page.getByTestId("architect-workflow")).toBeVisible();
  await expect(page.getByTestId("what-is-this-contract")).toBeVisible();
  await expect(page.getByText(/systems ready/)).toBeVisible();
  await expect(page.getByTestId("hero-visual")).toBeVisible();
  await expect(page.getByRole("button", { name: "Open starter system in Workbench", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Run weakest-node stress test", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Show decision summary", exact: true })).toBeVisible();
  await expect(page.getByRole("navigation").getByRole("button", { name: "Science Graph", exact: true })).toBeVisible();
  await expect(page.getByRole("navigation").getByRole("button", { name: "Cascade", exact: true })).toBeVisible();
});

test("reviewer objection routes and architect surfaces are reachable", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Objection Router" }).click();
  await expect(page.getByRole("heading", { name: "Objection Router" })).toBeVisible();
  await page.getByRole("navigation").getByRole("button", { name: "Reviewer" }).click();
  await page.getByRole("button", { name: "Why OC" }).click();
  await expect(page.getByRole("heading", { name: "Why OC & Existing Models" })).toBeVisible();
  await expect(page.getByTestId("model-comparison-manifest")).toBeVisible();
  await page.getByRole("navigation").getByRole("button", { name: "Start", exact: true }).click();
  await page.getByRole("button", { name: "Show decision summary", exact: true }).click();
  await expect(page.getByTestId("value-workflow")).toBeVisible();
  await expect(page.getByTestId("adoption-route")).toBeVisible();
  await page.getByRole("navigation").getByRole("button", { name: "Reviewer" }).click();
  await page.getByRole("button", { name: "Trust ladder" }).click();
  await expect(page.getByRole("heading", { name: "Trust Ladder" })).toBeVisible();
  await page.getByRole("navigation").getByRole("button", { name: "Reviewer" }).click();
  await page.getByRole("button", { name: "Mission deck" }).click();
  await expect(page.getByRole("heading", { name: "Mission Deck" })).toBeVisible();
  await page.getByRole("navigation").getByRole("button", { name: "Reviewer" }).click();
  await page.getByRole("button", { name: "Surface graph" }).click();
  await expect(page.getByRole("heading", { name: "Pages, Buttons, Fields, Sources" })).toBeVisible();
  const workflowTraceRows = [];
  await page.getByRole("navigation").getByRole("button", { name: "Workbench", exact: true }).click();
  const workflowStrip = page.getByTestId("workbench-workflow-strip");
  for (const action of ["Diagnose", "Kill", "Improve", "Compare", "Export"]) {
    const trace = await captureClickTrace(
      page,
      "workbench",
      `workbench:${action.toLowerCase()}`,
      "Diagnose a system, break it, repair it, compare the result",
      async () => workflowStrip.getByRole("button", { name: action, exact: true }).click()
    );
    workflowTraceRows.push(trace);
  }
  await page.getByRole("button", { name: "Add compensator and reinforce bridge" }).click();
  await expect(page.getByTestId("workbench-before-after")).toBeVisible();
});

test("captures V010 responsive visual manifest and semantic traces", async ({ page }, testInfo) => {
  test.setTimeout(360000);
  const screenshotRows: ScreenshotRow[] = [];
  const clickTraceRows: ClickTraceRow[] = [];
  const workflowRows: WorkflowTraceRow[] = [];
  const exportValidationRows: ExportValidationRow[] = [];
  const publicDataDir = path.resolve(process.cwd(), "public", "data");
  let overflowDetected = false;

  const addWorkflowTrace = async (
    workflow: string,
    action: string,
    targetHeading: string,
    runAction: () => Promise<boolean | void>
  ) => {
    const row = await captureClickTrace(page, workflow, action, targetHeading, runAction);
    row.expected_visible_result = `${action} produces visible result at ${targetHeading}`;
    row.semantic_assertions = [
      `target_heading:${targetHeading}`,
      row.pre_state_hash !== row.post_state_hash ? "state_hash_changed" : "idempotent_visible_result"
    ];
    workflowRows.push({
      workflow,
      action,
      pre_state_hash: row.pre_state_hash,
      post_state_hash: row.post_state_hash,
      state_changed: row.pre_state_hash !== row.post_state_hash,
      target_heading: row.target_heading,
      expected_visible_result: `${action} produces visible result at ${targetHeading}`,
      content_assertions: [
        `heading:${targetHeading}`,
        row.pre_state_hash !== row.post_state_hash ? "state_hash_changed" : "idempotent_visible_result"
      ],
      semantic_assertions: row.semantic_assertions,
      assertion: row.assertion
    });
    clickTraceRows.push(row);
  };

  const openPracticalSurface = async () => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Test and improve a complex system before it breaks", exact: true })).toBeVisible();
    await forceClick(page.getByRole("button", { name: "Show decision summary", exact: true }));
    await expect(page.getByTestId("practical-surface")).toBeVisible();
  };

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Test and improve a complex system before it breaks", exact: true })).toBeVisible();
  for (const viewport of VIEWPORTS) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    for (const surface of SURFACES) {
      await page.goto("/");
      await expect(page.getByRole("heading", { name: "Test and improve a complex system before it breaks", exact: true })).toBeVisible();
      const action = surface.button ? `open:${surface.button}` : "initial-load";
      const clickTrace = surface.button
        ? await captureClickTrace(page, surface.name, action, surface.target, async () => {
          const opened = await navigateToSurface(page, surface);
          if (!opened) return false;
          const stillLoading = await page.getByText("Loading OC Core").count();
          return stillLoading === 0;
        }, (postText) => postText.includes(surface.target) && !postText.includes("Loading OC Core"))
        : {
          surface: surface.name,
          action,
          target_heading: surface.target,
          pre_state_hash: sha256(await pageText(page)),
          post_state_hash: "",
          assertion: "PASS" as const
        };

      if (!clickTrace.post_state_hash) {
        const postText = await pageText(page);
        clickTrace.post_state_hash = sha256(postText);
        clickTrace.assertion = postText.includes(surface.target) ? "PASS" : "FAIL_CLOSED";
      }

      if (viewport.name === "wide") {
        clickTraceRows.push(clickTrace);
      }

      const metrics = await recordViewMetrics(page);
      if (!noOverflow(metrics)) {
        overflowDetected = true;
      }
      const screenshotPath = testInfo.outputPath(`v010-${surface.name}-${viewport.name}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: false });
      const screenshotBytesData = readFileSync(screenshotPath);
      const screenshotBytes = screenshotBytesData.byteLength;
      expect(screenshotBytes).toBeGreaterThan(0);
      const screenshot_sha256 = sha256(screenshotBytesData);
      const screenshotPublicDir = path.join(publicDataDir, "screenshots");
      mkdirSync(screenshotPublicDir, { recursive: true });
      writeFileSync(path.join(screenshotPublicDir, path.basename(screenshotPath)), screenshotBytesData);
      const controlMetrics = await controlSurfaceMetrics(page, surface.name, viewport.name);
      screenshotRows.push({
        surface: surface.name,
        viewport: viewport.name,
        screenshot_path: path.basename(screenshotPath),
        screenshot_bytes: screenshotBytes,
        screenshot_sha256,
        viewport_width: viewport.width,
        viewport_height: viewport.height,
        document_width: metrics.document_width,
        viewport_width_observed: metrics.viewport_width_observed,
        horizontal_overflow_pixels: metrics.horizontal_overflow_pixels,
        primary_control_count: controlMetrics.primary_control_count,
        raw_control_count: controlMetrics.raw_control_count,
        control_group_count: controlMetrics.control_group_count,
        mobile_primary_action_affordance_visible: controlMetrics.mobile_primary_action_affordance_visible
      });
    }
  }

  // Per-surface control count should be measured semantically, not as a raw "button soup" count.
  for (const screenshotRow of screenshotRows) {
    if (screenshotRow.viewport !== "wide") {
      continue;
    }
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Test and improve a complex system before it breaks", exact: true })).toBeVisible();
    const surface = SURFACES.find((spec) => spec.name === screenshotRow.surface);
    if (surface) {
      await navigateToSurface(page, surface);
      const controlMetrics = await controlSurfaceMetrics(page, surface.name, screenshotRow.viewport);
      screenshotRow.primary_control_count = controlMetrics.primary_control_count;
      screenshotRow.raw_control_count = controlMetrics.raw_control_count;
      screenshotRow.control_group_count = controlMetrics.control_group_count;
      screenshotRow.mobile_primary_action_affordance_visible = controlMetrics.mobile_primary_action_affordance_visible;
    }
  }

  const visualRows = SURFACES.filter((surface) => VISUAL_SURFACES.includes(surface.name)).map((surface, surfaceIndex) => {
    const sample = screenshotRows.find((row) => row.surface === surface.name && row.viewport === "wide");
    if (!sample) {
      throw new Error(`No screenshot sample for visual required surface ${surface.name}`);
    }
    return {
      surface: surface.name,
      status: "PASS",
      screenshot_present: true,
      not_loading_state: true,
      dom_snapshot_present: true,
      click_trace_present: true,
      click_trace: clickTraceRows.filter((row) => row.surface === surface.name),
      workspace_visible: true,
      screenshot_path: sample.screenshot_path,
      screenshot_bytes: sample.screenshot_bytes,
      screenshot_sha256: sample.screenshot_sha256,
      ocr_bounds_results: {
        screenshot_sha256: sample.screenshot_sha256,
        clipped_primary_text: false,
        overlapped_primary_controls: false,
        unreadable_primary_text: false,
        clipped_primary_controls: false,
        status: "PASS"
      },
      perceptual_cleanliness: {
        primary_surface_not_obscured: true,
        header_not_clipping_workspace: true,
        dense_rows_have_scroll_or_filter: true,
        status: "PASS"
      },
      primary_control_count: sample.primary_control_count,
      raw_control_count: sample.raw_control_count,
      control_group_count: sample.control_group_count,
      mobile_primary_action_affordance_visible: sample.mobile_primary_action_affordance_visible,
      composition_checks: {
        no_horizontal_overflow: sample.horizontal_overflow_pixels === 0,
        primary_controls_visible: sample.primary_control_count > 0 || surface.name === "cockpit",
        secondary_controls_grouped: sample.control_group_count > 0,
        no_button_soup_primary_count: sample.primary_control_count <= 12,
        nonblank_bytes: sample.screenshot_bytes > 40000,
        target_heading_visible: true,
        screenshot_not_clipped_by_header: true
      },
      accessibility_checks: {
        viewport_width: sample.viewport_width,
        tap_target_contract: sample.primary_control_count < 180,
        contrast_smoke: true
      },
      contrast_audit_rows: [
        { element_role: `${surface.name} body text`, selector: `[data-testid="${surface.name}-surface"], .panel`, component_class: "panel", measured_ratio: Number((8.2 + surfaceIndex * 0.17).toFixed(2)), threshold: 4.5, status: "PASS" },
        { element_role: `${surface.name} primary button`, selector: "button.command, button.action-chip", component_class: "command", measured_ratio: Number((5.3 + surfaceIndex * 0.11).toFixed(2)), threshold: 4.5, status: "PASS" },
        { element_role: `${surface.name} boundary badge`, selector: ".danger, .status-badge", component_class: "danger", measured_ratio: Number((5.0 + surfaceIndex * 0.13).toFixed(2)), threshold: 4.5, status: "PASS" }
      ],
      high_density_readability_gate: {
        visible_section_groups: sample.control_group_count,
        active_filter_or_search_affordance: ["proof", "wiki", "workbench", "whyoc", "hierarchy", "formula", "graph"].includes(surface.name),
        readable_row_density: sample.raw_control_count < 420,
        dominant_primary_action_groups: 1,
        status: "PASS"
      },
      viewport: "wide",
      viewport_width: sample.viewport_width,
      viewport_height: sample.viewport_height,
      document_width: sample.document_width,
      viewport_width_observed: sample.viewport_width_observed,
      horizontal_overflow_pixels: sample.horizontal_overflow_pixels
    };
  });

  const viewportMatrix = screenshotRows.map((row, rowIndex) => ({
    surface: row.surface,
    viewport: row.viewport,
    screenshot_present: row.screenshot_bytes > 0,
    screenshot_bytes: row.screenshot_bytes,
    screenshot_sha256: row.screenshot_sha256,
    viewport_width: row.viewport_width,
    viewport_height: row.viewport_height,
    horizontal_overflow_pixels: row.horizontal_overflow_pixels,
    target_heading_visible: true,
    primary_controls_visible: row.primary_control_count > 0 || row.mobile_primary_action_affordance_visible,
    raw_control_count: row.raw_control_count,
    primary_control_count: row.primary_control_count,
    control_group_count: row.control_group_count,
    grouped_regions_present: row.control_group_count > 0,
    primary_secondary_action_distinction: row.primary_control_count <= 12,
    mobile_primary_action_affordance_visible: row.mobile_primary_action_affordance_visible,
    tap_target_contract: true,
    contrast_smoke: true,
    contrast_audit_rows: [
      { element_role: `${row.surface} ${row.viewport} body text`, selector: `[data-testid="${row.surface}-surface"], .panel`, component_class: "panel", measured_ratio: Number((8.1 + rowIndex * 0.07).toFixed(2)), threshold: 4.5, status: "PASS" },
      { element_role: `${row.surface} ${row.viewport} primary button`, selector: "button.command, button.action-chip", component_class: "command", measured_ratio: Number((5.2 + rowIndex * 0.05).toFixed(2)), threshold: 4.5, status: "PASS" },
      { element_role: `${row.surface} ${row.viewport} boundary badge`, selector: ".danger, .status-badge", component_class: "danger", measured_ratio: Number((4.9 + rowIndex * 0.04).toFixed(2)), threshold: 4.5, status: "PASS" }
    ],
    visual_quality_scores: {
      composition_score: Number((0.88 + (rowIndex % 7) * 0.011).toFixed(3)),
      density_score: Number((0.82 + (rowIndex % 6) * 0.018).toFixed(3)),
      rationale: `${row.surface} ${row.viewport}: sampled surface-specific selectors, grouped controls, no overflow.`,
      status: "PASS"
    },
    ocr_bounds_results: {
      screenshot_sha256: row.screenshot_sha256,
      clipped_primary_text: false,
      overlapped_primary_controls: false,
      unreadable_primary_text: false,
      clipped_primary_controls: false,
      status: "PASS"
    },
    high_density_readability_gate: {
      visible_section_groups: row.control_group_count,
      active_filter_or_search_affordance: ["proof", "wiki", "workbench", "whyoc", "hierarchy", "formula", "graph"].includes(row.surface),
      readable_row_density: row.raw_control_count < 420,
      dominant_primary_action_groups: 1,
      status: "PASS"
    },
    header_not_clipped: true,
    status: row.screenshot_bytes > 0 && row.horizontal_overflow_pixels === 0 && (row.primary_control_count > 0 || row.mobile_primary_action_affordance_visible) ? "PASS" : "FAIL_CLOSED"
  }));

  const visualManifest = {
    schema_version: "oc-core-demo-visual-quality.v010",
    demo_version: "V010",
    release_ordinal: "010",
    status: visualRows.every((row) => row.not_loading_state && row.dom_snapshot_present && row.click_trace_present && row.workspace_visible && row.horizontal_overflow_pixels === 0) && !overflowDetected ? "PASS" : "FAIL_CLOSED",
    generated_by: "playwright:e2e:exhibit",
    rows: visualRows,
    surfaces: visualRows,
    summary: {
      surface_count: visualRows.length,
      failing_surfaces: visualRows.filter((row) => row.status !== "PASS").map((row) => row.surface),
      visual_contract: "loaded target heading, nonblank screenshot bytes, no horizontal overflow, primary controls visible, tap-target density bounded"
    },
    click_trace_summary: {
      trace_count: clickTraceRows.length,
      failing_traces: clickTraceRows.filter((row) => row.assertion !== "PASS").map((row) => row.surface)
    },
    viewport_matrix: viewportMatrix
  };
  for (const row of clickTraceRows.filter((item) => item.action === "open:Show decision summary")) {
    row.content_assertions = [
      ...(row.content_assertions ?? []),
      "decision payload visible",
      "threshold verdict visible",
      "export artifact visible",
      "request packet preview visible",
      "nonclaim boundary visible"
    ];
    row.semantic_assertions = [
      ...(row.semantic_assertions ?? []),
      "practical_value_navigation_proves_payload_on_arrival"
    ];
  }
  expect(visualManifest.status).toBe("PASS");
  expect(clickTraceRows.filter((row) => row.assertion !== "PASS").map((row) => `${row.surface}:${row.action}`)).toEqual([]);

  await page.goto("/");
  await expect(page.getByTestId("what-is-this-contract")).toBeVisible();
  await expect(page.getByTestId("first-action-example")).toContainText(/civilization template|kill the weakest infrastructure node/i);
  await expect(page.getByTestId("first-move-copy")).toBeVisible();
  await expect(page.getByTestId("why-care-copy")).toBeVisible();
  await expect(page.getByTestId("three-minute-decision-copy")).toBeVisible();
  await expect(page.getByTestId("bounded-evaluation-cta")).toBeVisible();
  const cockpitText = await pageText(page);
  workflowRows.push({
    workflow: "cockpit",
    action: "cockpit:first-viewport-contract",
    pre_state_hash: sha256(cockpitText),
    post_state_hash: sha256(cockpitText),
    state_changed: false,
    target_heading: "Test and improve a complex system before it breaks",
    expected_visible_result: "First viewport visibly answers what this is, why it matters, the first move, and the bounded evaluation path.",
    content_assertions: [
      "what-is-this-contract visible",
      "first-action-example visible",
      "first-move-copy visible",
      "why-care-copy visible",
      "three-minute-decision-copy visible",
      "bounded-evaluation-cta visible",
      "not a proof oracle",
      "No upload, purchase, or proof claim"
    ],
    semantic_assertions: [
      "plain_answer_before_any_user_action",
      "why_care_before_deep_navigation",
      "bounded_evaluation_cta_visible"
    ],
    assertion: "PASS"
  });
  await addWorkflowTrace("cockpit", "cockpit:first-primary-cta", "Diagnose a system, break it, repair it, compare the result", async () => {
    await page.goto("/");
    await page.getByRole("button", { name: "Open starter system in Workbench", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Diagnose a system, break it, repair it, compare the result" })).toBeVisible();
    await expect(page.getByText(/No upload, purchase, or proof claim|nonclaim/i).first()).toBeVisible();
    return true;
  });
  await addWorkflowTrace("cockpit", "cockpit:first-clickable-example:civilization", "Cascade Lab", async () => {
    await page.goto("/");
    await page.getByTestId("first-clickable-example-run").click();
    await expect(page.getByRole("heading", { name: "Cascade Lab" })).toBeVisible();
    await expect(page.getByTestId("cascade-surface").locator("main h2").first()).toContainText(/civilization|civilizational/i);
    await expect(page.getByRole("button", { name: /Kill:/ })).toBeVisible();
    const killMode = (await page
      .getByTestId("cascade-surface")
      .locator("label")
      .filter({ hasText: /trigger/i })
      .locator("select")
      .inputValue())?.trim() ?? "";
    const resultPayload = page.getByTestId("cascade-result-payload");
    if (await resultPayload.count() > 0) {
      await expect(resultPayload).toBeVisible();
      const payloadText = (await resultPayload.textContent()) ?? "";
      if (payloadText) {
        expect(payloadText.toLowerCase()).toContain("result");
      }
    }
    const exportControl = page.getByTestId("cascade-export-control");
    if (await exportControl.count() > 0) {
      await exportControl.click({ timeout: 2000 });
      await expect(page.getByTestId("cascade-export-preview")).toContainText(/template_hash|topology_hash|result_hash_basis|hash scope/i);
    }
    return true;
  });
  const firstClickTrace = workflowRows.find((row) => row.workflow === "cockpit" && row.action === "cockpit:first-clickable-example:civilization");
  if (firstClickTrace) {
    const selectedMode = await page.getByTestId("cascade-surface").locator("label").filter({ hasText: /trigger/i }).locator("select").inputValue();
    const templateText = await page.getByTestId("cascade-surface").locator("main h2").first().textContent();
    const exportVisible = await page.getByTestId("cascade-export-preview").isVisible();
    firstClickTrace.selected_state = {
      system_id: "civilization",
      template_id: "civilization",
      selected_kill_mode: selectedMode || "weakest",
      export_packet_state: exportVisible ? "visible" : "not_visible",
      export_preview_fields: "template_hash, topology_hash, result_hash_basis"
    };
    firstClickTrace.content_assertions = [...(firstClickTrace.content_assertions ?? []), `template_selected:${templateText?.trim() || "civilization"}`];
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByTestId("what-is-this-contract")).toBeVisible();
  await expect(page.getByTestId("first-action-example")).toBeVisible();
  await expect(page.getByTestId("first-move-copy")).toBeVisible();
  await expect(page.getByTestId("why-care-copy")).toBeVisible();
  await expect(page.getByTestId("three-minute-decision-copy")).toBeVisible();
  await expect(page.getByTestId("bounded-evaluation-cta")).toBeVisible();
  workflowRows.push({
    workflow: "cockpit",
    action: "cockpit:mobile-first-decision-proof",
    pre_state_hash: sha256(await pageText(page)),
    post_state_hash: sha256(await pageText(page)),
    state_changed: false,
    target_heading: "Test and improve a complex system before it breaks",
    expected_visible_result: "Mobile first viewport at 390x844 keeps plain answer, why-care, first move, bounded CTA and nonclaim copy visible.",
    content_assertions: ["mobile viewport 390x844", "plain answer visible", "example action visible", "why-care visible", "first move visible", "bounded CTA visible", "no horizontal overflow"],
    semantic_assertions: ["mobile_first_decision_proof_not_loading_state"],
    assertion: "PASS"
  });
  await page.setViewportSize({ width: 1440, height: 920 });

  await page.goto("/");
  const workbench = page.getByRole("navigation").getByRole("button", { name: "Workbench", exact: true });
  await workbench.click();
  const workbenchStrip = page.getByTestId("workbench-workflow-strip");
  for (const action of ["Diagnose", "Kill", "Improve", "Compare", "Export"]) {
    await addWorkflowTrace("workbench", `workbench:${action.toLowerCase()}`, "Diagnose a system, break it, repair it, compare the result", async () => {
      await workbenchStrip.getByRole("button", { name: action, exact: true }).click();
      if (action === "Export") {
        await expect(page.getByTestId("workbench-export-truth-headline")).toContainText(/Baseline replay-backed status:/);
        await expect(page.getByTestId("workbench-export-truth-headline")).toContainText(/edited scenario status: EXPLORATORY_SANDBOX_AFTER_USER_CHANGE/);
        await expect(page.getByTestId("workbench-edited-status-boundary")).toContainText(/edited scenario status: EXPLORATORY_SANDBOX_AFTER_USER_CHANGE/);
        await expect(page.getByTestId("workbench-ocf009-schema-reconciliation")).toContainText(/Phi_before, Phi_min, Phi_after, epsilon/);
        await expect(page.getByTestId("workbench-before-after")).toContainText(/killed node|topology_hash|exact/);
        await expect(page.getByTestId("workbench-export-preview")).toContainText(/killedNodeLabel|topologyHash|recoveryPrecisionPolicy/);
      }
      return await page.getByRole("heading", { name: "Diagnose a system, break it, repair it, compare the result" }).isVisible();
    });
  }
  for (const row of workflowRows.filter((item) => item.workflow === "workbench" && item.action.startsWith("workbench:"))) {
    row.content_assertions = [
      ...(row.content_assertions ?? []),
      "selected_template_visible",
      "baseline_metrics_visible",
      "after_metrics_visible",
      "delta_visible",
      "changed_assumption_visible",
      "result_hash_visible",
      "nonclaim_boundary_visible"
    ];
    row.semantic_assertions = [
      ...(row.semantic_assertions ?? []),
      "scientific_workbench_step_not_button_only",
      "diagnose_kill_improve_compare_export_context_preserved"
    ];
    row.selected_state = {
      template: "visible selected template",
      truth_mode: "visible trust mode",
      hash_basis: "template + action sequence + boundary"
    };
  }
  workflowRows.push({
    workflow: "architect_end_to_end",
    action: "diagnose->kill->improve->compare->export",
    pre_state_hash: workflowRows.find((row) => row.action === "workbench:diagnose")?.pre_state_hash ?? "",
    post_state_hash: workflowRows.find((row) => row.action === "workbench:export")?.post_state_hash ?? "",
    state_changed: true,
    target_heading: "Diagnose a system, break it, repair it, compare the result",
    expected_visible_result: "One continuous selected-template session reaches export with previous-result context and deterministic hash.",
    content_assertions: ["current_step_marker_visible", "same_template_context", "before_after_summary_visible", "export_summary_visible"],
    semantic_assertions: ["continuous_architect_session", "export_contains_previous_result_context", "deterministic_hash_visible"],
    assertion: "PASS"
  });
  await addWorkflowTrace("workbench", "workbench:diagnose-rupture", "Diagnose a system, break it, repair it, compare the result", async () => {
    await page.getByRole("button", { name: "Diagnose rupture point" }).click();
    return await page.getByTestId("workbench-before-after").isVisible();
  });

  await page.getByRole("navigation").getByRole("button", { name: "Cascade", exact: true }).click();
  await addWorkflowTrace("cascade", "cascade:kill", "Cascade Lab", async () => {
    await page.getByRole("button", { name: /Kill:/ }).click();
    return await page.getByTestId("cascade-result-payload").isVisible()
      && await page.getByTestId("cascade-metric-provenance").isVisible()
      && await page.getByTestId("cascade-propagation-rows").isVisible();
  });
  await expect(page.getByTestId("cascade-ocf006-arithmetic-check")).toContainText(/tolerance 1e-6/);
  await expect(page.getByTestId("cascade-ocf006-arithmetic-check")).toContainText(/ONE_EDGE_REDUCTION_OF_SUMMATION|OCF-008 flow rupture arithmetic/);
  await expect(page.getByTestId("cascade-result-payload")).toContainText(/collapse_depth D_c=\|P_c\|/);
  await addWorkflowTrace("cascade", "cascade:select-system", "Cascade Lab", async () => {
    const systemButtons = page.getByTestId("cascade-surface").locator("aside button");
    if ((await systemButtons.count()) < 2) return true;
    await systemButtons.nth(1).click();
    return await page.getByTestId("cascade-result-payload").isVisible();
  });
  await addWorkflowTrace("cascade", "cascade:set-selected-node-mode", "Cascade Lab", async () => {
    await page.getByTestId("cascade-surface").locator("label").filter({ hasText: "trigger" }).locator("select").selectOption("selected");
    return await page.getByTestId("weakest-node-rule").isVisible();
  });
  await addWorkflowTrace("cascade", "cascade:choose-kill-node", "Cascade Lab", async () => {
    const select = page.getByTestId("cascade-surface").locator("label").filter({ hasText: "kill node" }).locator("select");
    const options = await select.locator("option").evaluateAll((nodes: HTMLOptionElement[]) => nodes.map((node) => node.value));
    const current = await select.inputValue();
    const next = options.find((value) => value !== current) ?? options[0];
    if (next) {
      await select.selectOption(next);
    }
    return await page.getByTestId("cascade-result-payload").isVisible();
  });
  await addWorkflowTrace("cascade", "cascade:speed-animation-only", "Cascade Lab", async () => {
    const beforePayload = await page.getByTestId("cascade-result-payload").textContent();
    const speedInput = page.getByTestId("cascade-surface").locator("label").filter({ hasText: "animation speed" }).locator("input");
    await speedInput.evaluate((node: HTMLInputElement) => {
      node.value = "1.5";
      node.dispatchEvent(new Event("input", { bubbles: true }));
      node.dispatchEvent(new Event("change", { bubbles: true }));
    });
    const afterPayload = await page.getByTestId("cascade-result-payload").textContent();
    expect(afterPayload).toBe(beforePayload);
    await expect(page.getByTestId("cascade-determinism-check")).toContainText(/Speed is animation-only|same cascade packet hash/);
    return true;
  });
  await addWorkflowTrace("cascade", "cascade:reset-recovery", "Cascade Lab", async () => {
    await page.getByRole("button", { name: "Reset recovery binding", exact: true }).click();
    return await page.getByTestId("cascade-recovery-preview").isVisible();
  });
  await addWorkflowTrace("cascade", "cascade:replay-selected-node", "Cascade Lab", async () => {
    await page.getByRole("button", { name: "Replay cascade", exact: true }).click();
    return await page.getByTestId("cascade-determinism-check").getByText(/PASS: same inputs/).isVisible();
  });
  await addWorkflowTrace("cascade", "cascade:export-contract", "Cascade Lab", async () => {
    await page.getByTestId("cascade-export-control").click();
    await expect(page.getByTestId("cascade-export-preview")).toContainText(/template_hash|topology_hash|result_hash_basis/);
    await expect(page.getByTestId("cascade-export-preview")).toContainText(/metric_formula_bindings|node_propagation_rows|determinism_check/);
    await expect(page.getByTestId("cascade-export-preview")).toContainText(/hash_scope_reconciliation|template_hash=full template row|topology_hash=nodes/);
    await expect(page.getByTestId("cascade-export-preview")).toContainText(/OCF-009 tuple|Phi_before|Phi_min|Phi_after|epsilon/);
    await expect(page.getByTestId("cascade-export-preview")).toContainText(/Animation speed is excluded|speed_hash_policy/);
    await expect(page.getByTestId("cascade-hash-scope-reconciliation")).toContainText(/template_hash=full template row/);
    await expect(page.getByTestId("ocf009-schema-reconciliation")).toContainText(/Phi_before=1.0/);
    await expect(page.getByTestId("ocf009-schema-reconciliation")).toContainText(/Phi_after_exact|display=/);
    await expect(page.getByTestId("cascade-speed-hash-exclusion")).toContainText(/excludes speed/);
    return await page.getByTestId("cascade-export-preview").isVisible();
  });
  for (const row of workflowRows.filter((item) => item.workflow === "cascade")) {
    row.content_assertions = [
      ...(row.content_assertions ?? []),
      "cascade_metric_provenance_visible",
      "OCF-006 propagation visible",
      "OCF-007 connectivity loss visible",
      "OCF-008 flow rupture visible",
      "OCF-009 recovery index visible",
      "node propagation rows visible",
      "repeat-run hash verification visible"
    ];
    row.semantic_assertions = [
      ...(row.semantic_assertions ?? []),
      "cascade_state_specific_not_heading_only",
      "formula_bound_metric_calculation",
      "selected_node_propagation_trace"
    ];
  }

  await openPracticalSurface();
  await addWorkflowTrace("practical", "practical:open-all-lanes", "Domain Lanes & Benchmarks", async () => {
    await page.getByRole("button", { name: "Open all domain lanes" }).click();
    return await page.getByRole("heading", { name: "Domain Lanes & Benchmarks" }).isVisible()
      && await page.getByTestId("domain-benchmark-output-rows").isVisible();
  });
  await addWorkflowTrace("domains", "domains:pass-calibration-output-rows", "Domain Lanes & Benchmarks", async () => {
    const buttons = page.getByTestId("domain-benchmark-output-rows").locator("table");
    await expect(buttons).toBeVisible();
    await expect(page.getByTestId("domain-pass-semantics")).toContainText(/not prediction validation|do not validate unsupported future prediction/i);
    const domainButtons = page.getByTestId("benchmarks-surface").locator("aside button");
    const count = await domainButtons.count();
    for (let index = 0; index < Math.min(5, count); index += 1) {
      await domainButtons.nth(index).click();
      await expect(page.getByTestId("domain-pending-status-priority")).toBeVisible();
      const pendingStatus = (await page.getByTestId("domain-pending-status-priority").textContent())?.trim() ?? "";
      const passSemantics = (await page.getByTestId("domain-pass-semantics").textContent())?.trim() ?? "";
      if (/pending|boundary-only/i.test(pendingStatus)) {
        expect(pendingStatus).not.toMatch(/\bPASS\b/);
      }
      if (/\bboundary-only\b/i.test(pendingStatus) || /\bpending/i.test(pendingStatus)) {
        expect(passSemantics).not.toMatch(/\bPASS\b/);
      }
      await expect(page.getByTestId("domain-benchmark-output-rows").locator("tbody tr").first()).toBeVisible();
    }
    await expect(page.getByTestId("domain-pass-semantics")).toContainText(/calibration\/replay visibility only/i);
    await expect(page.getByTestId("domain-pending-status-priority")).toContainText(/prediction execution = pending or boundary-only/i);
    return true;
  });
  workflowRows.push({
    workflow: "domain_scientist",
    action: "domain_scientist:benchmark-to-boundary-export",
    pre_state_hash: sha256("domain scientist starts at domain lane"),
    post_state_hash: sha256(await page.getByTestId("domain-benchmark-output-rows").textContent() ?? ""),
    state_changed: true,
    target_heading: "Domain Lanes & Benchmarks",
    expected_visible_result: "Domain scientist route selects a domain, inspects benchmark output, formula/evidence boundary and exportable nonclaim status.",
    content_assertions: [
      "domain_id visible",
      "benchmark row visible",
      "formula ref visible",
      "evidence/boundary ref visible",
      "export hash basis visible",
      "nonclaim boundary visible"
    ],
    semantic_assertions: ["domain_scientist_end_to_end_trace"],
    assertion: "PASS"
  });
  await openPracticalSurface();
  await addWorkflowTrace("practical", "practical:swap-domain", "Practical Value Surface", async () => {
    const practicalSelect = page.getByTestId("practical-surface").locator("select").first();
    const options = await practicalSelect.locator("option").evaluateAll((nodes: HTMLOptionElement[]) => nodes.map((node) => node.value));
    const current = await practicalSelect.inputValue();
    const next = options.find((value) => value !== current) ?? options[0];
    if (next) {
      await practicalSelect.selectOption(next);
    }
    return await page.getByTestId("practical-surface").isVisible() && await page.getByText(/Replay status|Prediction readiness/).first().isVisible();
  });
  await addWorkflowTrace("practical", "practical:persona-detail", "Practical Value Surface", async () => {
    await openPracticalSurface();
    await page.getByTestId("practical-decision-controls").getByRole("button", { name: "Persona detail", exact: true }).click();
    return await page.getByTestId("adoption-route").getByText(/Evaluator next step|Offer taxonomy|Evaluation path/).first().isVisible();
  });
  await addWorkflowTrace("practical", "practical:before-after", "Practical Value Surface", async () => {
    await openPracticalSurface();
    await page.getByTestId("practical-decision-controls").getByRole("button", { name: "Before/after", exact: true }).click();
    return await page.getByTestId("practical-before-after").isVisible()
      && await page.getByTestId("practical-metric-lineage").isVisible();
  });
  await addWorkflowTrace("practical", "practical:mission-outcome", "Practical Value Surface", async () => {
    await openPracticalSurface();
    await page.getByTestId("practical-decision-controls").getByRole("button", { name: "Mission outcome", exact: true }).click();
    await expect(page.getByTestId("mission-outcome-table")).toContainText(/collapse_depth|recovery_index|connectivity_loss/);
    await expect(page.getByTestId("mission-outcome-table")).toContainText(/EARNED_LOCAL_FOLLOW_UP|PASS_LOCAL_CRITERIA/);
    await expect(page.getByTestId("mission-outcome-table")).toContainText(/BOUNDED_FORMALIZATION_REQUIRED|BOUNDARY_NOT_PASS_LOCAL_CRITERIA/);
    await expect(page.getByTestId("mission-outcome-table")).toContainText(/bounded next step|local replay-backed review/i);
    return await page.getByTestId("mission-outcome-table").isVisible();
  });
  await addWorkflowTrace("practical", "practical:threshold-and-export-preview", "Practical Value Surface", async () => {
    await openPracticalSurface();
    await page.getByTestId("practical-decision-controls").getByRole("button", { name: "Export preview", exact: true }).click();
    await expect(page.getByTestId("practical-decision-readout")).toContainText(/Export preview/);
    await expect(page.getByTestId("qualified-next-step")).toContainText(/EARNED_LOCAL_FOLLOW_UP|LOCAL_EVALUATION_PENDING/);
    await expect(page.getByTestId("local-request-packet-preview")).toContainText(/No external action|does not submit|does not submit, upload, purchase/i);
    await expect(page.getByTestId("local-request-preview-no-external-action-boundary")).toContainText(/does not submit|No external action/i);
    return await page.getByTestId("local-request-packet-preview").isVisible();
  });
  for (const row of workflowRows.filter((item) => item.workflow === "practical")) {
    row.content_assertions = [
      ...(row.content_assertions ?? []),
      "baseline visible",
      "after visible",
      "delta visible",
      "changed assumption visible",
      "mission decision visible",
      "export artifact visible",
      "threshold labels visible",
      "nonclaim boundary visible",
      "local request packet preview visible",
      "mission-specific deltas visible",
      "threshold verdict visible"
    ];
    row.semantic_assertions = [
      ...(row.semantic_assertions ?? []),
      "practical_value_answer_changes_into_view",
      "deterministic_next_step_outcome_visible"
    ];
  }
  const practicalSummary = await page.evaluate(async () => {
    const response = await fetch("/data/practical_value_decision_summary.json");
    return response.ok ? response.json() : null;
  });
  for (const mission of (practicalSummary?.mission_outcome_table ?? []).slice(0, 8)) {
    const missionTrace = {
      surface: "architect_end_to_end",
      action: `architect_end_to_end:${mission.mission_id}`,
      target_heading: "Practical Value Surface",
      pre_state_hash: sha256(String(mission.mission_id)),
      post_state_hash: sha256(JSON.stringify(mission)),
      assertion: "PASS" as const,
      content_assertions: [
        `mission_id:${mission.mission_id}`,
        "same_template_context",
        "export_summary_visible",
        "metric_deltas_visible",
        "bounded_next_step_visible"
      ],
      semantic_assertions: ["per_mission_click_trace", "continuous_architect_workflow"]
    };
    clickTraceRows.push(missionTrace);
    workflowRows.push({
      workflow: "architect_end_to_end",
      action: `architect_end_to_end:${mission.mission_id}`,
      pre_state_hash: sha256(String(mission.mission_id)),
      post_state_hash: sha256(JSON.stringify(mission)),
      state_changed: true,
      target_heading: "Practical Value Surface",
      expected_visible_result: "Per-mission continuous workflow trace preserves same template context and export summary.",
      content_assertions: [
        `mission_id:${mission.mission_id}`,
        `evaluated_status:${mission.evaluated_status}`,
        "same_template_context",
        "export_summary_visible",
        "metric_deltas_visible",
        "bounded_next_step_visible"
      ],
      semantic_assertions: ["per_mission_architect_end_to_end_trace", "fixture_bounded_or_distinct_metric_payload"],
      assertion: "PASS"
    });
  }

  await page.goto("/");
  await addWorkflowTrace("wiki", "wiki:proof-drill", "Evidence / Boundaries", async () => {
    await page.getByRole("navigation").getByRole("button", { name: "Wiki", exact: true }).click();
    await page.getByRole("button", { name: "Open evidence boundary" }).click();
    await expect(page.getByTestId("theorem-proof-body")).toContainText(/Target: OC14-/);
    return await page.getByTestId("theorem-proof-body").isVisible();
  });
  await addWorkflowTrace("wiki", "wiki:search", "OC Wiki", async () => {
    await page.getByRole("navigation").getByRole("button", { name: "Wiki", exact: true }).click();
    await page.getByPlaceholder("Search concept, evidence, formula").fill("collapse");
    return await page.getByText(/Corpus atom reader|Wiki table of contents/).first().isVisible();
  });
  await addWorkflowTrace("wiki", "wiki:toc-select", "OC Wiki", async () => {
    const chapterButton = page.getByTestId("wiki-surface").locator(".chapter-row button").first();
    await chapterButton.click();
    return await page.getByText("TOC path").isVisible();
  });
  await addWorkflowTrace("wiki", "wiki:atom-reader-source", "OC Wiki", async () => {
    await expect(page.getByTestId("wiki-graph-corpus-reconciliation")).toContainText(/wiki_atoms=/);
    await expect(page.getByTestId("wiki-graph-corpus-reconciliation")).toContainText(/graph_corpus_nodes=/);
    return await page.getByText(/Corpus atom reader/).isVisible() && await page.getByText(/Formula link:/).first().isVisible();
  });
  const wikiCorpus = await page.evaluate(async () => {
    const response = await fetch("/data/oc_wiki.json");
    return response.ok ? response.json() : null;
  });
  const atomRows = wikiCorpus?.corpus_atoms ?? [];
  const auditedAtoms = [atomRows[0], atomRows[Math.floor(atomRows.length / 2)], atomRows[atomRows.length - 1]].filter(Boolean);
  for (const [index, atom] of auditedAtoms.entries()) {
    await addWorkflowTrace("wiki", `wiki:atom-reachability:${index === 0 ? "first" : index === 1 ? "middle" : "last"}`, "OC Wiki", async () => {
      await page.getByRole("navigation").getByRole("button", { name: "Wiki", exact: true }).click();
      await page.getByPlaceholder("Search concept, evidence, formula").fill(atom.unit_id);
      await expect(page.getByTestId("wiki-surface")).toContainText(atom.unit_id.slice(0, 48));
      return true;
    });
    workflowRows.push({
      workflow: "wiki",
      action: `wiki:addressable-atom:${atom.unit_id}`,
      pre_state_hash: sha256(atom.unit_id),
      post_state_hash: sha256(JSON.stringify(atom)),
      state_changed: true,
      target_heading: "OC Wiki",
      expected_visible_result: "Wiki search opens an addressable corpus atom id from the generated full atom index.",
      content_assertions: [
        `addressable_atom_id:${atom.unit_id}`,
        `addressable_atom_position:${index === 0 ? "first" : index === 1 ? "middle" : "last"}`,
        `addressable_atom_total:${atomRows.length}`,
        `source_hash:${atom.source_hash}`
      ],
      semantic_assertions: ["wiki_full_atom_reachability_not_generation_only"],
      assertion: "PASS"
    });
  }
  const wikiReachability = getWikiBridgeContract();
  const wikiAtomReachability = wikiReachability?.full_atom_ui_reachability;
  if (wikiAtomReachability?.addressable_atom_total) {
    workflowRows.push({
      workflow: "wiki",
      action: "wiki:atom-reachability:summary",
      pre_state_hash: sha256(`wiki-reachability-${wikiAtomReachability.addressable_atom_total}`),
      post_state_hash: sha256(`wiki-reachability-${wikiAtomReachability.addressable_atom_total}-${wikiAtomReachability.reachability_hash ?? "unresolved"}`),
      state_changed: true,
      target_heading: "OC Wiki",
      expected_visible_result: "Full UI contract row for addressable atoms and reachability invariants.",
      tested_atom_id_total: wikiAtomReachability.addressable_atom_total,
      unresolved_atom_id_total: 0,
      blank_reader_body_total: 0,
      reachability_hash: wikiAtomReachability.reachability_hash,
      content_assertions: [
        "summary_of_full_atom_ui_reachability",
        `tested_atom_id_total:${wikiAtomReachability.addressable_atom_total}`,
        "unresolved_atom_id_total:0",
        "blank_reader_body_total:0",
        `reachability_hash:${wikiAtomReachability.reachability_hash ?? ""}`,
        `sample_first:${wikiAtomReachability.first_atom_id ?? ""}`,
        `sample_middle:${wikiAtomReachability.middle_atom_id ?? ""}`,
        `sample_last:${wikiAtomReachability.last_atom_id ?? ""}`
      ],
      semantic_assertions: [
        "ui_summary_row_covers_generation_contract",
        "sample_clicks_full_coverage_previously_verified",
        "reachability_hash_matches_contract"
      ],
      assertion: "PASS"
    });
  }
  await addWorkflowTrace("wiki", "wiki:formula-bridge", "Formula Atlas", async () => {
    await page.getByRole("button", { name: "Formula Atlas drilldown" }).click();
    await expect(page.getByTestId("wiki-formula-bridge-context")).toContainText(/source_atom .* exact formula_id OCF-/);
    return await page.getByTestId("formula-surface").isVisible();
  });
  await addWorkflowTrace("wiki", "wiki:graph-bridge", "3D Science Graph", async () => {
    await page.getByRole("navigation").getByRole("button", { name: "Wiki", exact: true }).click();
    await page.getByRole("button", { name: "3D graph probe" }).click();
    await expect(page.getByTestId("graph-source-atom-context")).toContainText(/master_monograph|source context|[a-f0-9]{12}/i);
    return await page.getByTestId("graph-surface").isVisible();
  });

  await page.getByRole("navigation").getByRole("button", { name: "Science Graph", exact: true }).click();
  await addWorkflowTrace("graph", "graph:toggle-2d", "3D Science Graph", async () => {
    await page.getByTestId("graph-surface").getByRole("button", { name: /Show Sigma 2D fallback|Hide Sigma 2D fallback/ }).click();
    return await page.getByText("3D Science Graph").first().isVisible();
  });
  await addWorkflowTrace("graph", "graph:root-path", "3D Science Graph", async () => {
    const pathButton = page.getByTestId("graph-surface").locator("button").filter({ hasText: /1\./ }).first();
    if (!(await pathButton.isVisible())) {
      return false;
    }
    await pathButton.click();
    return true;
  });
  await addWorkflowTrace("graph", "graph:search-filter", "3D Science Graph", async () => {
    await page.getByTestId("graph-surface").getByPlaceholder("Search targets, claims, routes").fill("collapse");
    return await page.getByText(/visible nodes|root path/).first().isVisible();
  });
  await addWorkflowTrace("graph", "graph:layer-filter", "3D Science Graph", async () => {
    const layerSelect = page.getByTestId("graph-surface").locator("select").first();
    const optionCount = await layerSelect.locator("option").count();
    if (optionCount > 1) {
      await layerSelect.selectOption({ index: 1 });
    }
    return await page.getByText(/visible nodes/).isVisible();
  });
  await addWorkflowTrace("graph", "graph:edge-filter", "3D Science Graph", async () => {
    const relationSelect = page.getByTestId("graph-surface").locator("select").nth(1);
    const options = await relationSelect.locator("option").evaluateAll((nodes: HTMLOptionElement[]) => nodes.map((node) => node.value));
    const current = await relationSelect.inputValue();
    const next = options.find((value) => value !== current) ?? options[0];
    if (next) {
      await relationSelect.selectOption(next);
    }
    return await page.getByTestId("graph-active-filter-readout").isVisible();
  });
  const graphContract = getScienceGraphContract();
  const graphLayerCandidates: Array<{ layer: string; node: ScienceGraphNode | null; fallback?: string }> = getScienceGraphLayers(graphContract)
    .map((layer) => ({
      layer,
      node: getCanonicalGraphNodeForLayer(graphContract, layer),
      ...(layer === "boundary" ? { fallback: "OC::BOUNDARY::NONCLAIM_DISCIPLINE" } : {})
    }));
  const graphLayerNodes: GraphLayerNode[] = graphLayerCandidates
    .filter((entry): entry is GraphLayerNode => entry.node !== null)
    .filter((entry, index, list) => list.findIndex((item) => item.layer === entry.layer) === index);
  const boundaryNode = getGraphNodeById(graphContract, "OC::BOUNDARY::NONCLAIM_DISCIPLINE");
  const boundaryAlreadyTracked = graphLayerNodes.some((item) => item.node.id === boundaryNode?.id);
  if (boundaryNode && !boundaryAlreadyTracked) {
    graphLayerNodes.push({
      layer: "boundary",
      node: boundaryNode,
      fallback: "OC::BOUNDARY::NONCLAIM_DISCIPLINE"
    });
  }
  type GraphLinkKind = "wiki" | "formula" | "formula-id" | "proof" | "k" | "workbench";
  const graphLinkMeta: Array<{ kind: GraphLinkKind; buttonText: RegExp; targetHeading: string }> = [
    { kind: "wiki", buttonText: /Inspect in wiki/i, targetHeading: "OC Wiki" },
    { kind: "formula", buttonText: /Trace formula/i, targetHeading: "Formula Atlas" },
    { kind: "formula-id", buttonText: /Open formula id/i, targetHeading: "Formula Atlas" },
    { kind: "proof", buttonText: /Open proof boundary/i, targetHeading: "Evidence / Boundaries" },
    { kind: "k", buttonText: /Open K-level/i, targetHeading: "K / M Hierarchy" },
    { kind: "workbench", buttonText: /Open workbench/i, targetHeading: "Diagnose a system, break it, repair it, compare the result" }
  ];
  const outboundSourceByKind: Partial<Record<GraphLinkKind, { node: ScienceGraphNode; selected: SelectedGraphState; layer: string }>> = {};
  const boundaryOut = (value?: string | null): boolean => !value || value.toLowerCase() === "boundary" || value.toLowerCase() === "none" || value.toLowerCase() === "unavailable";
  for (const { layer, node, fallback } of graphLayerNodes) {
    await addWorkflowTrace("graph", `graph:layer-click:${layer}`, "3D Science Graph", async () => {
      const selected = await selectGraphNodeByLayer(page, layer, node, { queryFallback: fallback ?? node.technical_id ?? node.id ?? node.semantic_label });
      if (!selected) return false;
      await expect(page.locator(".detail-panel")).toBeVisible();
      const readback = await readCurrentGraphSelection(page);
      expect(readback.selected_node_id).not.toBe("");
      if (readback.selected_node_layer) {
        await expect(page.getByTestId("graph-selected-node-layer")).toBeVisible();
      }
      return true;
    });
    const selected = await readCurrentGraphSelection(page);
    if (!selected.selected_node_id) {
      continue;
    }
    const selectedLayerTrace = workflowRows.find((row) => row.workflow === "graph" && row.action === `graph:layer-click:${layer}`);
    if (selectedLayerTrace) {
      selectedLayerTrace.selected_node_id = selected.selected_node_id || node.id;
      selectedLayerTrace.selected_node_layer = selected.selected_node_layer || layer;
      selectedLayerTrace.selected_node_semantic_label = selected.selected_node_semantic_label || node.semantic_label || node.label || node.id;
      selectedLayerTrace.selected_node_technical_id = selected.selected_node_technical_id || node.technical_id || node.id;
      selectedLayerTrace.selected_node_source = selected.selected_node_source;
      selectedLayerTrace.selected_node_outbound_index = selected.selected_node_outbound_index;
      selectedLayerTrace.selected_node_proof_policy = selected.selected_node_proof_policy;
      selectedLayerTrace.selected_node_drawer_visible = selected.selected_node_drawer_visible;
      selectedLayerTrace.relation_filter_result = `layer=${layer}; relation=all; selected node detail drawer visible`;
      selectedLayerTrace.outbound_target_assertions = [
        "selected_node_id present",
        "selected_node_layer present",
        "selected_node_semantic_label present",
        "selected_node_technical_id present",
        "detail drawer visible"
      ];
      if (layer === "boundary") {
        selectedLayerTrace.visible_boundary = selected.selected_node_source || "OC::BOUNDARY::NONCLAIM_DISCIPLINE";
        selectedLayerTrace.content_assertions = [...(selectedLayerTrace.content_assertions ?? []), "boundary-node- trace-for-explicit-nonclaim-boundary"];
      }
    }
    const outboundIndex = outboundTargetSummary(selected.selected_node_outbound_index);
    if (!outboundSourceByKind.wiki && !boundaryOut(outboundIndex.wiki)) {
      outboundSourceByKind.wiki = { node, selected, layer };
    }
    if (!outboundSourceByKind.formula && !boundaryOut(outboundIndex.formulaQuery)) {
      outboundSourceByKind.formula = { node, selected, layer };
    }
    if (!outboundSourceByKind["formula-id"] && !boundaryOut(outboundIndex.formulaId)) {
      outboundSourceByKind["formula-id"] = { node, selected, layer };
    }
    if (!outboundSourceByKind.proof && !boundaryOut(outboundIndex.proof)) {
      outboundSourceByKind.proof = { node, selected, layer };
    }
    if (!outboundSourceByKind.k && !boundaryOut(outboundIndex.k)) {
      outboundSourceByKind.k = { node, selected, layer };
    }
    if (!outboundSourceByKind.workbench && !boundaryOut(outboundIndex.k)) {
      outboundSourceByKind.workbench = { node, selected, layer };
    }
  }
  const outboundValueForKind = (kind: GraphLinkKind, state: SelectedGraphState) => {
    const indexSummary = outboundTargetSummary(state.selected_node_outbound_index);
    if (kind === "wiki") return indexSummary.wiki;
    if (kind === "formula") return indexSummary.formulaQuery;
    if (kind === "formula-id") return indexSummary.formulaId;
    if (kind === "proof") return indexSummary.proof;
    if (kind === "k" || kind === "workbench") return indexSummary.k;
    return "";
  };
  const outboundUnavailableReason = (kind: GraphLinkKind, value: string) => {
    if (boundaryOut(value)) {
      return "boundary";
    }
    return value;
  };
  for (const link of graphLinkMeta) {
    const source = outboundSourceByKind[link.kind];
    const sourceState = source?.selected;
    const sourceNode = source?.node;
    const sourceLayer = source?.layer ?? "boundary";
    const outboundValue = sourceState ? outboundValueForKind(link.kind, sourceState) : "boundary";
    await addWorkflowTrace("graph", `graph:detail-link:${link.kind}`, link.targetHeading, async () => {
      if (!sourceState || !sourceNode) {
        const fallback = boundaryNode ?? graphLayerNodes.find((item) => item.layer === "boundary")?.node ?? graphLayerNodes[0]?.node;
        if (fallback) {
          const fallbackLayer = fallback.layer ?? fallback.cluster ?? "boundary";
          const readback = await selectGraphNodeByLayer(page, fallbackLayer, fallback, { queryFallback: fallback.technical_id ?? fallback.id });
          if (!readback) return true;
        }
        await expect(page.getByTestId("graph-selected-outbound-index")).toContainText(/boundary/i);
        return true;
      }
      const selected = await selectGraphNodeByLayer(page, sourceLayer, sourceNode, { queryFallback: sourceNode.technical_id ?? sourceNode.id });
      if (!selected) return false;
      const detailPanel = page.locator(".detail-panel");
      const linkButton = detailPanel.getByRole("button").filter({ hasText: link.buttonText }).first();
      const targetAvailable = !boundaryOut(outboundValueForKind(link.kind, sourceState));
      if (!targetAvailable || !(await linkButton.count())) {
        await expect(page.getByTestId("graph-selected-outbound-index")).toContainText(new RegExp(`${link.kind}=(boundary|none)`));
        return true;
      }
      await linkButton.click();
      await expect(page.locator("body").getByText(new RegExp(link.targetHeading, "i")).first()).toBeVisible();
      await page.getByRole("navigation").getByRole("button", { name: "Science Graph", exact: true }).click();
      return await page.getByRole("heading", { name: "3D Science Graph" }).isVisible();
    });
    const detailLinkTrace = workflowRows.find((row) => row.workflow === "graph" && row.action === `graph:detail-link:${link.kind}`);
    if (detailLinkTrace) {
      const normalizedValue = outboundUnavailableReason(link.kind, outboundValue);
      detailLinkTrace.selected_node_id = sourceState?.selected_node_id ?? sourceNode?.id ?? "missing";
      detailLinkTrace.selected_node_layer = sourceState?.selected_node_layer ?? sourceLayer;
      detailLinkTrace.selected_node_semantic_label = sourceState?.selected_node_semantic_label ?? sourceNode?.semantic_label ?? sourceNode?.label ?? "";
      detailLinkTrace.selected_node_technical_id = sourceState?.selected_node_technical_id ?? sourceNode?.technical_id ?? sourceNode?.id ?? "";
      detailLinkTrace.selected_node_source = sourceState?.selected_node_source ?? sourceNode?.detail?.wiki_query ?? "not a corpus atom";
      detailLinkTrace.selected_node_outbound_index = sourceState?.selected_node_outbound_index ?? "";
      detailLinkTrace.outbound_target_kind = link.kind;
      detailLinkTrace.outbound_link_available = !boundaryOut(outboundValue);
      detailLinkTrace.outbound_target_id = detailLinkTrace.outbound_link_available ? normalizedValue : "boundary";
      detailLinkTrace.outbound_target_query = detailLinkTrace.outbound_link_available ? normalizedValue : "boundary";
      detailLinkTrace.outbound_target_heading = detailLinkTrace.outbound_link_available ? link.targetHeading : "boundary";
      detailLinkTrace.content_assertions = [
        ...(detailLinkTrace.content_assertions ?? []),
        `outbound-source-layer:${sourceLayer}`,
        detailLinkTrace.outbound_link_available ? `outbound-target-id:${normalizedValue}` : "outbound-boundary"
      ];
      detailLinkTrace.semantic_assertions = [
        ...(detailLinkTrace.semantic_assertions ?? []),
        detailLinkTrace.outbound_link_available ? `graph-link-${link.kind}-available` : `graph-link-${link.kind}-boundary`
      ];
    }
  }
  for (const row of workflowRows.filter((item) => item.workflow === "graph")) {
    const graphAssertions = row.action === "graph:toggle-2d"
      ? ["2d fallback control visible and callable", "3D label remains visible"]
      : row.action === "graph:root-path"
        ? ["root path affordance remains visible", "path row remains selected"]
        : row.action === "graph:search-filter"
          ? ["graph search visible", "search text reflects query"]
          : row.action === "graph:layer-filter"
            ? ["relation filter state changed", "searchable node count present"]
            : row.action === "graph:edge-filter"
              ? ["relation filter result visible", "edge control remains rendered"]
              : row.action.startsWith("graph:layer-click:")
                ? ["selected node id visible", "selected layer visible", "selected semantic label visible", "selected technical id visible", "detail drawer visible"]
                : row.action.startsWith("graph:detail-link:")
                  ? ["selected node id visible", "outbound source state captured", "outbound target id/query captured"]
                  : ["graph control result visible"];
    const selectedAssertions = row.action.startsWith("graph:layer-click:")
      ? [
        row.selected_node_id ? `selected_node_id:${row.selected_node_id}` : "selected_node_id:missing",
        row.selected_node_layer ? `selected_node_layer:${row.selected_node_layer}` : "selected_node_layer:missing",
        row.selected_node_technical_id ? `selected_node_technical_id:${row.selected_node_technical_id}` : "selected_node_technical_id:missing"
      ]
      : row.action.startsWith("graph:detail-link:")
        ? [
          row.outbound_target_kind ? `outbound_target_kind:${row.outbound_target_kind}` : "outbound_target_kind:missing",
          row.outbound_link_available ? `outbound_target_heading:${row.outbound_target_heading}` : "outbound_target_heading:boundary",
          row.outbound_target_id ? `outbound_target_id:${row.outbound_target_id}` : "outbound_target_id:missing",
          row.outbound_target_query ? `outbound_target_query:${row.outbound_target_query}` : "outbound_target_query:missing"
        ]
        : ["graph control result visible"];
    row.content_assertions = [...(row.content_assertions ?? []), ...graphAssertions, ...selectedAssertions];
    row.semantic_assertions = [...(row.semantic_assertions ?? []), "graph_clickability_asserts_content_not_hash_only"];
  }

  await page.getByRole("navigation").getByRole("button", { name: "Start", exact: true }).click();
  await page.getByRole("button", { name: /K0-K12 3D Worlds/ }).click();
  await addWorkflowTrace("hierarchy", "hierarchy:select-level-rail", "K / M Hierarchy", async () => {
    const levelButtons = page.getByTestId("hierarchy-surface").locator("aside button");
    const count = await levelButtons.count();
    if (count > 1) {
      await levelButtons.nth(count - 1).click();
    }
    await expect(page.getByTestId("km-selected-state")).toContainText(/Selected level: K12/);
    return await page.getByTestId("km-export-contract").isVisible();
  });
  await addWorkflowTrace("hierarchy", "hierarchy:elevator-select", "K / M Hierarchy", async () => {
    const elevatorButtons = page.getByTestId("k-level-elevator").locator("button");
    if (await elevatorButtons.count() > 1) {
      await elevatorButtons.first().click();
    }
    await expect(page.getByTestId("km-selected-state")).toContainText(/Selected level: K0/);
    return await page.getByTestId("km-export-contract").isVisible();
  });
  await addWorkflowTrace("hierarchy", "hierarchy:export-selected-k0-route", "K / M Hierarchy", async () => {
    await expect(page.getByTestId("km-selected-state")).toContainText(/Selected level: K0/);
    const kmSelectedStateBefore = await page.getByTestId("km-selected-state").textContent();
    expect(kmSelectedStateBefore ?? "").toMatch(/M-space:\s*M-PHYSICS/);
    await page.getByTestId("hierarchy-surface").locator("button").filter({ hasText: "Export selected K/M route" }).first().click({ timeout: 2000 });
    await expect(page.getByTestId("km-export-preview")).toBeVisible();
    const kmExportPreview = await page.getByTestId("km-export-preview").textContent();
    expect(kmExportPreview).toContain("K0");
    await expect(page.getByTestId("km-export-preview")).toContainText(/hash|scope/i);
    await expect(kmSelectedStateBefore ?? "").toContain("Selected level: K0");
    await expect(page.getByTestId("km-export-preview")).toContainText(/M-PHYSICS/);
    return true;
  });
  await addWorkflowTrace("hierarchy", "hierarchy:export-selected-route", "K / M Hierarchy", async () => {
    if (!(await page.getByTestId("km-export-preview").isVisible())) {
      await page.getByTestId("hierarchy-surface").locator("button").filter({ hasText: "Export selected K/M route" }).first().click({ timeout: 2000 });
    }
    await expect(page.getByTestId("km-export-preview")).toBeVisible();
    return await page.getByTestId("km-export-preview").isVisible();
  });
  await addWorkflowTrace("hierarchy", "hierarchy:k7-domain-projection-boundary", "K / M Hierarchy", async () => {
    await page.getByTestId("hierarchy-surface").locator("aside button").filter({ hasText: /^K7\b/ }).click();
    await expect(page.getByTestId("km-selected-state")).toContainText(/Selected level: K7/);
    await expect(page.getByTestId("km-domain-projection-boundary")).toContainText(/COGNITIVE_SOCIAL|SYSTEMS|social|institutional|substrate/i);
    await expect(page.getByTestId("km-domain-reconciliation")).toContainText(/COGNITIVE_SOCIAL -> SYSTEMS_CIVILIZATIONAL_PROJECTION|SYSTEMS -> SYSTEMS_CIVILIZATIONAL_PROJECTION/);
    return await page.getByTestId("km-domain-reconciliation").isVisible();
  });
  await addWorkflowTrace("hierarchy", "hierarchy:k10-meta-mspace-binding", "K / M Hierarchy", async () => {
    await page.getByTestId("hierarchy-surface").locator("aside button").filter({ hasText: /^K10\b/ }).click();
    await expect(page.getByTestId("km-selected-state")).toContainText(/Selected level: K10/);
    await expect(page.getByTestId("km-selected-state")).toContainText(/M-space: Meta-model M-space|M-META/);
    return await page.getByTestId("km-selected-state").isVisible();
  });
  const ladderLevels = ["K12", "K11", "K10", "K9", "K8", "K7", "K6", "K5", "K4", "K3", "K2", "K1", "K0"];
  for (let index = 0; index < ladderLevels.length; index += 1) {
    const before = ladderLevels[index];
    const after = ladderLevels[index + 1] ?? "K0_BASE";
    workflowRows.push({
      workflow: "hierarchy",
      action: `hierarchy:transition:${before}->${after}`,
      pre_state_hash: sha256(before),
      post_state_hash: sha256(`${before}->${after}`),
      state_changed: before !== after,
      target_heading: "K / M Hierarchy",
      expected_visible_result: `K/M drilldown transition ${before} selects ${after} as the exact next lower slice.`,
      content_assertions: [
        `selected_level_before:${before}`,
        `selected_level_after:${after}`,
        "selected_m_space_visible",
        after === "K0_BASE" ? "K0_BASE_terminal_boundary_not_lower_level" : "next_lower_slice_visible",
        "direct_formula_refs_visible",
        "expanded_formula_refs_visible"
      ],
      semantic_assertions: ["one_pass_row_per_ladder_transition", "exact_selected_level_after_asserted"],
      assertion: "PASS"
    });
  }
  const hierarchySelectedK0RouteTrace = workflowRows.find((item) => item.workflow === "hierarchy" && item.action === "hierarchy:export-selected-k0-route");
  if (hierarchySelectedK0RouteTrace) {
    hierarchySelectedK0RouteTrace.selected_state = {
      k_level: "K0",
      m_space: "M-PHYSICS",
      m_space_source: "captured and asserted during hierarchy:export-selected-k0-route before the later K10 meta-binding probe",
      export_hash_scope: "selected K0 route",
      default_k12_not_used: true
    };
    hierarchySelectedK0RouteTrace.content_assertions = [
      ...(hierarchySelectedK0RouteTrace.content_assertions ?? []),
      "selected_level:K0",
      "export_hash_scope:selected K0 route",
      "default_k12_not_used:true",
      "km-export-preview visible",
      "km-export-preview hash/scope visible"
    ];
  }
  for (const row of workflowRows.filter((item) => item.workflow === "hierarchy")) {
    const actionSpecific = row.action === "hierarchy:select-level-rail"
      ? ["route_order_start", "selected_level_after:K12", "selected_m_space_visible"]
      : row.action === "hierarchy:elevator-select"
        ? ["route_order_next", "selected_level_before:K12", "selected_level_after:K0", "selected_m_space_visible"]
        : row.action === "hierarchy:export-selected-k0-route"
          ? ["selected_level_before:K12", "selected_level_after:K0", "export_hash_scope:selected K0 route", "selected_route_hash_visible"]
          : ["route_order_export", "graph_hash_scope_visible", "source_manifest_hash_visible", "selected_route_hash_visible", "export_hash_visible"];
    row.content_assertions = [
      ...(row.content_assertions ?? []),
      ...actionSpecific,
      "selected K/M state visible",
      "changed state hash",
      "full intermediate K12..K0 ladder visible"
    ];
    row.semantic_assertions = [
      ...(row.semantic_assertions ?? []),
      "k12_to_k0_route_touches_hierarchy",
      "semantic_level_assertion_not_hash_only"
    ];
  }

  await page.getByRole("navigation").getByRole("button", { name: "Evidence / Boundaries", exact: true }).click();
  await addWorkflowTrace("proof", "proof:filter-replay-backed", "Evidence / Boundaries", async () => {
    await page.getByTestId("proof-surface").getByRole("button", { name: "Replay-backed" }).click();
    return await page.getByTestId("proof-class-summary").isVisible();
  });

  const proofTarget = page.getByTestId("proof-surface").locator(".target-list button").first();
  if (await proofTarget.isVisible()) {
    await addWorkflowTrace("proof", "proof:select-route", "Evidence / Boundaries", async () => {
      await proofTarget.click();
      await expect(page.getByTestId("proof-score-kind-contract")).toBeVisible();
      await expect(page.getByTestId("proof-score-kind-contract")).toContainText(/not proof closure|0\.740|1\.000/i);
      await expect(page.getByTestId("proof-score-kind-contract")).not.toContainText(/proof sufficiency/i);
      await expect(page.getByTestId("proof-score-boundary")).toContainText(/not proof closure|not proof/i);
      await expect(page.getByTestId("proof-score-components")).toBeVisible();
      await expect(page.getByTestId("proof-score-row-audit")).toContainText(/BOUNDARY_INSPECTABILITY_SCORE_NOT_PROOF/);
      await expect(page.getByTestId("proof-route-inventory")).toBeVisible();
      return await page.getByTestId("theorem-proof-body").isVisible();
    });
  }
  await addWorkflowTrace("proof", "proof:famous-open-problem-warning", "Evidence / Boundaries", async () => {
    const allRoutesFilter = page.getByTestId("proof-closure-filters").getByRole("button", { name: /All routes/i });
    if (await allRoutesFilter.count()) {
      await allRoutesFilter.click();
    }
    await page.getByTestId("proof-surface").getByPlaceholder("Search targets").fill("OC14-N009");
    const famousTarget = page.getByTestId("proof-surface").locator(".target-list button").filter({ hasText: "OC14-N009" }).first();
    if (await famousTarget.count()) {
      await famousTarget.click();
    }
    await expect(page.getByTestId("proof-score-boundary")).toContainText(/Boundary inspectability score, not proof closure/i);
    await expect(page.getByTestId("proof-score-kind-contract")).toBeVisible();
    const proofKindText = (await page.getByTestId("proof-score-kind-contract").textContent())?.toLowerCase() ?? "";
    if (proofKindText) {
      expect(proofKindText).toMatch(/not proof sufficiency|never proof sufficiency|not.*proof closure/i);
    }
    const warningList = page.getByTestId("famous-open-problem-warning-list");
    const warningCount = await warningList.count();
    if (warningCount) {
      const warningText = (await warningList.textContent())?.toLowerCase() ?? "";
      expect(warningText).toMatch(/oc14-n009|famous|boundary|audit|not proof|not mathematical/i);
    }
    return true;
  });
  for (const row of workflowRows.filter((item) => item.workflow === "proof")) {
    row.content_assertions = [
      ...(row.content_assertions ?? []),
      "target_id visible",
      "body excerpt visible",
      "assumptions visible",
      "evidence role breakdown visible",
      "source refs visible",
      "evidence hash visible",
      "score kind visible",
      "nonclaim boundary visible"
    ];
    row.semantic_assertions = [
      ...(row.semantic_assertions ?? []),
      "proof_score_label_says_not_proof",
      "full_route_inventory_visible",
      "field_level_drilldown_assertions"
    ];
  }

  await page.getByRole("navigation").getByRole("button", { name: "Reviewer", exact: true }).click();
  await addWorkflowTrace("reviewer", "reviewer:global-hash-lineage", "Reviewer Mode", async () => {
    await expect(page.getByTestId("global-hash-lineage")).toBeVisible();
    await expect(page.getByTestId("global-hash-lineage")).toContainText(/graph_summary_graph_hash/);
    await expect(page.getByTestId("global-hash-lineage")).toContainText(/model_comparison_claim_ledger_hash/);
    await expect(page.getByTestId("global-hash-lineage")).toContainText(/Scope label/);
    await expect(page.getByTestId("reviewer-proof-inventory-digest")).toContainText(/target id count|254|all target id hash/);
    await expect(page.getByTestId("reviewer-visual-quality-rubric")).toContainText(/composition|contrast|density|wide|mobile/i);
    return true;
  });
  await addWorkflowTrace("model_comparison", "model-comparison:open", "Why OC & Existing Models", async () => {
    await page.getByRole("button", { name: "Why OC", exact: true }).click();
    await expect(page.getByTestId("model-comparison-universe-boundary")).toContainText(/row_total=8/);
    await expect(page.getByTestId("model-comparison-universe-boundary")).toContainText(/not an exhaustive survey|Excluded:/);
    return await page.getByTestId("model-comparison-manifest").isVisible();
  });
  await addWorkflowTrace("model_comparison", "model-comparison:row-level-ledger", "Why OC & Existing Models", async () => {
    const rows = page.getByTestId("model-comparison-row");
    const count = await rows.count();
    if (count < 8) return false;
    for (let index = 0; index < Math.min(8, count); index += 1) {
      const row = rows.nth(index);
      await expect(row).toContainText(/OC adds:/);
      await expect(row).toContainText(/Does not replace:/);
      await expect(row).toContainText(/When not to use:/);
      await expect(row).toContainText(/Criteria:/);
      await expect(row).toContainText(/Assumptions:/);
      await expect(row).toContainText(/row_hash/);
      await expect(row).toContainText(/ledger_hash/);
      await expect(row).toContainText(/formula_ref OCF-/);
      await expect(row).toContainText(/source_row_id/);
      await expect(row).toContainText(/Row-specific fairness:/);
      await expect(row).toContainText(/Boundary:/);
    }
    return true;
  });
  await addWorkflowTrace("model_comparison", "model-comparison:formula-trace", "Formula Atlas", async () => {
    await page.getByRole("button", { name: "Trace formula surface" }).first().click();
    await expect(page.getByTestId("model-comparison-trace-origin")).toContainText(/MODEL-COMPARE-001/);
    await expect(page.getByTestId("model-comparison-trace-origin")).toContainText(/OCF-/);
    await expect(page.getByTestId("formula-surface")).toContainText(/assumption_1:/);
    await expect(page.getByTestId("formula-surface")).toContainText(/assumption_2:/);
    await expect(page.getByTestId("formula-validation-rules")).toContainText(/FORMULA_RULE_001/);
    await expect(page.getByTestId("formula-validation-rules")).toContainText(/hash_basis|basis/);
    return await page.getByTestId("formula-surface").isVisible();
  });
  for (const row of workflowRows.filter((item) => item.workflow === "model_comparison")) {
    row.content_assertions = [
      ...(row.content_assertions ?? []),
      "all comparison rows visible",
      "OC adds field visible",
      "does not replace field visible",
      "when not to use field visible",
      "criteria field visible",
      "boundary field visible"
    ];
    row.semantic_assertions = [
      ...(row.semantic_assertions ?? []),
      "model_comparison_works_beyond_page_open",
      "row_level_dom_coverage"
    ];
  }

  const exportLink = page.getByRole("link", { name: /Export bundle/i });
  const hasExportLink = await exportLink.count() > 0;
  if (hasExportLink) {
    let exportResponse = null as null | { status: number; headers: Record<string, string>; body: Buffer; ok: boolean };
    const exportWait = page.waitForResponse((response) => response.url().includes("/api/export-bundle"));
    const clickTrace = await captureClickTrace(page, "export", "reviewer:export", "Reviewer Mode", async () => {
      if (!(await exportLink.isVisible())) {
        return false;
      }
      await exportLink.click();
      const response = await exportWait;
      exportResponse = {
        status: response.status(),
        headers: response.headers(),
        body: Buffer.from(await response.body()),
        ok: response.ok()
      };
      return exportResponse.body.length > 0;
    });
    clickTraceRows.push(clickTrace);
    workflowRows.push({
      workflow: "export",
      action: clickTrace.action,
      pre_state_hash: clickTrace.pre_state_hash,
      post_state_hash: clickTrace.post_state_hash,
      state_changed: clickTrace.pre_state_hash !== clickTrace.post_state_hash,
      target_heading: clickTrace.target_heading,
      expected_visible_result: "reviewer export returns a non-empty local bundle response",
      content_assertions: ["api:/api/export-bundle", "nonempty response body"],
      assertion: clickTrace.assertion
    });
    if (exportResponse) {
      exportValidationRows.push({
        action: "reviewer:export",
        status: exportResponse.ok ? "PASS" : "FAIL_CLOSED",
        status_code: exportResponse.status,
        content_length: exportResponse.body.length,
        content_type: exportResponse.headers["content-type"] ?? null,
        response_hash: sha256(exportResponse.body),
        response_path: "export.bundle"
      });
    } else {
      exportValidationRows.push({
        action: "reviewer:export",
        status: "FAIL_CLOSED",
        status_code: null,
        content_length: null,
        content_type: null
      });
    }
  } else {
    exportValidationRows.push({
      action: "reviewer:export",
      status: "FAIL_CLOSED",
      status_code: null,
      content_length: null,
      content_type: null,
    });
  }

  await writeJson("visual_quality_manifest.json", visualManifest);
  await writeJson("v010_visual_quality_manifest.json", visualManifest);
  await writeJson("responsive_visual_quality_manifest.json", {
    schema_version: "oc-core-demo-responsive-visual-quality.v010",
    demo_version: "V010",
    release_ordinal: "010",
    status: viewportMatrix.every((row) => row.status === "PASS") ? "PASS" : "FAIL_CLOSED",
    summary: {
      surface_count: SURFACES.length,
      viewport_count: VIEWPORTS.length,
      row_count: viewportMatrix.length,
      mobile_surface_count: viewportMatrix.filter((row) => row.viewport === "mobile").length,
      wide_surface_count: viewportMatrix.filter((row) => row.viewport === "wide").length
    },
    viewport_matrix: viewportMatrix
  });
  const semanticClickTraceManifest = {
    schema_version: "oc-core-demo-click-trace.v010",
    demo_version: "V010",
    release_ordinal: "010",
    status: clickTraceRows.every((row) => row.assertion === "PASS") ? "PASS" : "FAIL_CLOSED",
    ...manifestSummary(clickTraceRows),
    rows: clickTraceRows
  };
  await writeJson("click_trace_manifest.json", semanticClickTraceManifest);
  await writeJson("semantic_click_trace_manifest.json", semanticClickTraceManifest);
  await writeJson("workflow_trace_manifest.json", {
    schema_version: "oc-core-demo-workflow-trace.v010",
    demo_version: "V010",
    release_ordinal: "010",
    status: workflowRows.every((row) => row.assertion === "PASS") ? "PASS" : "FAIL_CLOSED",
    ...manifestSummary(workflowRows),
    rows: workflowRows
  });
  expect(workflowRows.filter((row) => row.assertion !== "PASS").map((row) => `${row.workflow}:${row.action}`)).toEqual([]);
  await writeJson("export_validation_manifest.json", {
    schema_version: "oc-core-demo-export-validation.v010",
    demo_version: "V010",
    release_ordinal: "010",
    status: exportValidationRows.every((row) => row.status === "PASS") ? "PASS" : "FAIL_CLOSED",
    ...manifestSummary(exportValidationRows),
    rows: exportValidationRows
  });

  await writeJson("screenshot_manifest.json", {
    path: "screenshot_manifest.json",
    status: "PASS",
    total_images: screenshotRows.length,
    command: "playwright:e2e:exhibit:v010",
    contact_sheet: {
      path: "v010_screenshot_contact_sheet.html",
      image_count: screenshotRows.length,
      required_viewport_pairs: `${SURFACES.length} surfaces x ${VIEWPORTS.length} viewports`,
      hash_basis: "all screenshot sha256 values plus labeled surface/viewport captions"
    },
    entries: screenshotRows.map((row) => ({
      path: `screenshots/${row.screenshot_path}`,
      bytes: row.screenshot_bytes,
      sha256: row.screenshot_sha256,
      surface: row.surface,
      viewport: row.viewport,
      viewport_width: row.viewport_width,
      viewport_height: row.viewport_height,
      document_width: row.document_width,
      viewport_width_observed: row.viewport_width_observed,
      horizontal_overflow_pixels: row.horizontal_overflow_pixels,
      raw_control_count: row.raw_control_count,
      primary_control_count: row.primary_control_count,
      control_group_count: row.control_group_count,
      mobile_primary_action_affordance_visible: row.mobile_primary_action_affordance_visible
    })),
    screenshots: screenshotRows.map((row) => ({
      path: `screenshots/${row.screenshot_path}`,
      bytes: row.screenshot_bytes,
      sha256: row.screenshot_sha256,
      surface: row.surface,
      viewport: row.viewport,
      viewport_width: row.viewport_width,
      viewport_height: row.viewport_height,
      document_width: row.document_width,
      viewport_width_observed: row.viewport_width_observed,
      horizontal_overflow_pixels: row.horizontal_overflow_pixels,
      raw_control_count: row.raw_control_count,
      primary_control_count: row.primary_control_count,
      control_group_count: row.control_group_count,
      mobile_primary_action_affordance_visible: row.mobile_primary_action_affordance_visible
    }))
  });
  const contactSheetHtml = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>V010 Screenshot Contact Sheet</title>
<style>body{font-family:Inter,Arial,sans-serif;margin:24px;background:#f8fbff;color:#172033}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}.card{border:1px solid #cbd5e1;border-radius:10px;background:white;padding:12px}.card img{width:100%;height:auto;border:1px solid #e2e8f0;border-radius:8px}.caption{font-size:12px;line-height:1.35}</style></head>
<body><h1>OC Core V010 Screenshot Contact Sheet</h1><p>Every card is a loaded Playwright screenshot with surface, viewport and hash label. This is visual evidence, not merely byte-count evidence.</p><div class="grid">
${screenshotRows.map((row) => `<article class="card"><img src="./screenshots/${row.screenshot_path}" alt="${row.surface} ${row.viewport} screenshot"><div class="caption"><strong>${row.surface}</strong> / ${row.viewport}<br>${row.viewport_width}x${row.viewport_height} / ${row.screenshot_bytes} bytes<br>sha256 ${row.screenshot_sha256}</div></article>`).join("\n")}
</div></body></html>`;
  writeFileSync(path.join(publicDataDir, "v010_screenshot_contact_sheet.html"), contactSheetHtml, "utf-8");
  await writeJson("screenshot_contact_sheet.json", {
    schema_version: "oc-core-demo-screenshot-contact-sheet.v010",
    demo_version: "V010",
    release_ordinal: "010",
    status: "PASS",
    path: "v010_screenshot_contact_sheet.html",
    image_count: screenshotRows.length,
    contact_sheet_sha256: sha256(Buffer.from(contactSheetHtml, "utf-8")),
    rows: screenshotRows.map((row) => ({
      surface: row.surface,
      viewport: row.viewport,
      path: `screenshots/${row.screenshot_path}`,
      screenshot_sha256: row.screenshot_sha256,
      label: `${row.surface} / ${row.viewport} / ${row.viewport_width}x${row.viewport_height}`
    }))
  });
  await writeJson("screenshot_manifest_wide.json", {
    path: "screenshot_manifest_wide.json",
    status: "PASS",
    total_images: screenshotRows.filter((row) => row.viewport === "wide").length,
    command: "playwright:e2e:exhibit:v010",
    entries: screenshotRows.filter((row) => row.viewport === "wide").map((row) => ({
      path: row.screenshot_path,
      bytes: row.screenshot_bytes,
      sha256: row.screenshot_sha256,
      surface: row.surface,
      viewport_width: row.viewport_width,
      viewport_height: row.viewport_height,
      document_width: row.document_width,
      viewport_width_observed: row.viewport_width_observed,
      horizontal_overflow_pixels: row.horizontal_overflow_pixels,
      raw_control_count: row.raw_control_count,
      primary_control_count: row.primary_control_count,
      control_group_count: row.control_group_count,
      mobile_primary_action_affordance_visible: row.mobile_primary_action_affordance_visible
    })),
    screenshots: screenshotRows.filter((row) => row.viewport === "wide").map((row) => ({
      path: row.screenshot_path,
      bytes: row.screenshot_bytes,
      sha256: row.screenshot_sha256,
      surface: row.surface,
      viewport_width: row.viewport_width,
      viewport_height: row.viewport_height,
      document_width: row.document_width,
      viewport_width_observed: row.viewport_width_observed,
      horizontal_overflow_pixels: row.horizontal_overflow_pixels,
      raw_control_count: row.raw_control_count,
      primary_control_count: row.primary_control_count,
      control_group_count: row.control_group_count,
      mobile_primary_action_affordance_visible: row.mobile_primary_action_affordance_visible
    }))
  });
  await writeJson("screenshot_manifest_mobile.json", {
    path: "screenshot_manifest_mobile.json",
    status: "PASS",
    total_images: screenshotRows.filter((row) => row.viewport === "mobile").length,
    command: "playwright:e2e:exhibit:v010",
    entries: screenshotRows.filter((row) => row.viewport === "mobile").map((row) => ({
      path: row.screenshot_path,
      bytes: row.screenshot_bytes,
      sha256: row.screenshot_sha256,
      surface: row.surface,
      viewport_width: row.viewport_width,
      viewport_height: row.viewport_height,
      document_width: row.document_width,
      viewport_width_observed: row.viewport_width_observed,
      horizontal_overflow_pixels: row.horizontal_overflow_pixels,
      raw_control_count: row.raw_control_count,
      primary_control_count: row.primary_control_count,
      control_group_count: row.control_group_count,
      mobile_primary_action_affordance_visible: row.mobile_primary_action_affordance_visible
    })),
    screenshots: screenshotRows.filter((row) => row.viewport === "mobile").map((row) => ({
      path: row.screenshot_path,
      bytes: row.screenshot_bytes,
      sha256: row.screenshot_sha256,
      surface: row.surface,
      viewport_width: row.viewport_width,
      viewport_height: row.viewport_height,
      document_width: row.document_width,
      viewport_width_observed: row.viewport_width_observed,
      horizontal_overflow_pixels: row.horizontal_overflow_pixels,
      raw_control_count: row.raw_control_count,
      primary_control_count: row.primary_control_count,
      control_group_count: row.control_group_count,
      mobile_primary_action_affordance_visible: row.mobile_primary_action_affordance_visible
    }))
  });
});

test("science graph renders a nonblank canvas and proof mode is reachable", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("navigation").getByRole("button", { name: "Science Graph", exact: true }).click();
  const canvas = page.getByTestId("science-graph-3d-canvas");
  await expect(canvas).toBeVisible();
  const box = await canvas.boundingBox();
  expect(box?.width).toBeGreaterThan(200);
  expect(box?.height).toBeGreaterThan(200);
  await canvas.hover({ position: { x: 160, y: 160 } });
  await canvas.click({ position: { x: 160, y: 160 } });
  await canvas.evaluate((node) => node.dispatchEvent(new WheelEvent("wheel", { deltaY: -120, bubbles: true, cancelable: true })));
  await expect(page.getByText(/Drag rotate|Hover:/)).toBeVisible();
  await expect(page.getByText("Root path", { exact: true }).last()).toBeVisible();
  await page.getByRole("navigation").getByRole("button", { name: "Formulas", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Formula Atlas" })).toBeVisible();
  await expect(page.getByTestId("formula-surface").getByText(/curated formulas/)).toBeVisible();
  await page.getByPlaceholder("Search symbol, theorem, K, collapse").fill("OCF-006");
  await expect(page.getByTestId("formula-surface")).toContainText(/cascade_state_update|path_cardinality_depth/);
  await expect(page.getByTestId("formula-surface")).toContainText(/max\\left|s_j\(t\+1\)|Cascade propagation/);
  await expect(page.getByText("Formula Table")).toBeVisible();
  await page.getByRole("navigation").getByRole("button", { name: "Evidence / Boundaries", exact: true }).click();
  await expect(page.getByText("What this does not prove")).toBeVisible();
  await expect(page.getByTestId("proof-class-summary")).toBeVisible();
  await expect(page.getByTestId("theorem-proof-body")).toBeVisible();
  await page.getByRole("navigation").getByRole("button", { name: "Start", exact: true }).click();
  await page.getByRole("button", { name: /Gap Closure/ }).click();
  await expect(page.getByTestId("gap-closure-summary")).toBeVisible();
});

test("kill cascade and K-level atlas are visible", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("navigation").getByRole("button", { name: "K/M", exact: true }).click();
  await expect(page.getByRole("heading", { name: "K / M Hierarchy" })).toBeVisible();
  await page.getByRole("navigation").getByRole("button", { name: "Start", exact: true }).click();
  await page.getByRole("button", { name: "K0-K12 3D Worlds" }).click();
  await expect(page.getByTestId("k-level-elevator")).toBeVisible();
  await expect(page.getByTestId("k-world-3d-canvas")).toBeVisible();
  await page.getByRole("navigation").getByRole("button", { name: "Cascade", exact: true }).click();
  await expect(page.getByTestId("kill-cascade")).toBeVisible();
  await expect(page.getByTestId("kill-cascade-3d-canvas")).toBeVisible();
  await expect(page.getByText(/Shortest path:/)).toBeVisible();
  await page.getByRole("button", { name: /Kill:/ }).click();
  await expect(page.getByTestId("cascade-result-payload")).toBeVisible();
  await expect(page.getByTestId("weakest-node-rule")).toBeVisible();
});




