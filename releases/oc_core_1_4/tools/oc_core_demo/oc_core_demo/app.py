from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import streamlit as st

try:
    from oc_core_demo.core import (
        SCHEMA_VERSION,
        explain_spec,
        export_release_context,
        list_cases,
        list_specs,
        load_public_graph,
        run_spec_safe,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from oc_core_demo.core import (
        SCHEMA_VERSION,
        explain_spec,
        export_release_context,
        list_cases,
        list_specs,
        load_public_graph,
        run_spec_safe,
    )


THEME_CSS = """
<style>
.stApp { background: #f7f9fc; color: #18212f; }
.block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1280px; }
h1, h2, h3 { letter-spacing: 0; color: #172033; }
[data-testid="stSidebar"] { background: #edf2f7; }
.oc-panel { border: 1px solid #d8e1ea; background: #ffffff; border-radius: 8px; padding: 1rem; margin: 0.65rem 0; }
.oc-panel strong { color: #153e75; }
.oc-muted { color: #5c6b7a; }
.oc-badge { display: inline-block; border: 1px solid #9bb8d8; border-radius: 999px; padding: 0.12rem 0.55rem; color: #153e75; background: #e8f2ff; font-size: 0.78rem; margin-right: 0.3rem; }
.oc-pass { border-color: #72b7a1; color: #0f624f; background: #e8f7f2; }
.oc-fail { border-color: #d19090; color: #8a2525; background: #fff0f0; }
.oc-warning { border-left: 3px solid #d99a38; padding-left: 0.85rem; }
div[data-testid="stMetric"] { background: #ffffff; border: 1px solid #d8e1ea; padding: 0.65rem; border-radius: 8px; }
button[kind="primary"] { border-radius: 8px; }
</style>
"""

PAGES = [
    "Dashboard",
    "Case Workspace",
    "Model Lab",
    "Decision Calculators",
    "Science Graph",
    "Proof & Limits",
    "JSON Interface",
    "Release Package",
]


def _download(label: str, payload: dict[str, Any], file_name: str) -> None:
    st.download_button(
        label,
        data=json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2),
        file_name=file_name,
        mime="application/json",
    )


def _full_spec(spec_id: str) -> dict[str, Any]:
    return explain_spec(spec_id)["spec"]


def _specs_for(window_id: str) -> list[dict[str, Any]]:
    return [spec for spec in list_specs() if spec["window_id"] == window_id]


def _node_rows(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for node in nodes:
        statement = " ".join(str(node.get("statement", "")).split())
        rows.append(
            {
                "id": node.get("id", ""),
                "label": node.get("label", ""),
                "route": node.get("route", ""),
                "demo_class": node.get("demo_class", ""),
                "evidence_class": node.get("evidence_class", ""),
                "statement_excerpt": statement[:220] + ("..." if len(statement) > 220 else ""),
            }
        )
    return rows


def _param_controls(spec: dict[str, Any], overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    overrides = overrides or {}
    params: dict[str, Any] = {}
    for key, block in spec["parameters"].items():
        default = overrides.get(key, block.get("default"))
        label = key.replace("_", " ")
        help_text = block.get("description") or f"default {block.get('default')}"
        if block["type"] == "integer":
            params[key] = st.slider(label, int(block.get("min", 0)), int(block.get("max", 100)), int(default), help=help_text)
        elif block["type"] == "number":
            params[key] = st.slider(label, float(block.get("min", 0.0)), float(block.get("max", 1.0)), float(default), help=help_text)
        else:
            height = 120 if key == "case_text" else 80
            params[key] = st.text_area(label, str(default), height=height, help=help_text)
    return params


def _score_metrics(body: dict[str, Any]) -> None:
    metric_keys = [
        ("risk_score", "Risk"),
        ("sufficiency_score", "Evidence"),
        ("readiness_score", "Readiness"),
        ("score", "Score"),
        ("final_coherence", "Final coherence"),
        ("final_health", "Final health"),
    ]
    found = [(key, label) for key, label in metric_keys if key in body]
    if not found:
        return
    cols = st.columns(min(4, len(found)))
    for column, (key, label) in zip(cols, found):
        column.metric(label, body[key])


def _show_result(result: dict[str, Any], *, compact_json: bool = True) -> None:
    status = result.get("status", "PASS")
    badge_class = "oc-pass" if status == "PASS" else "oc-fail"
    st.markdown(
        f"<div class='oc-panel'><span class='oc-badge {badge_class}'>{status}</span>"
        f"<span class='oc-muted'>schema {result.get('schema_version', SCHEMA_VERSION)} | hash "
        f"<code>{result.get('result_hash', '')[:18]}</code></span></div>",
        unsafe_allow_html=True,
    )
    body = result.get("result", {})
    if isinstance(body, dict):
        _score_metrics(body)
        if body.get("risk_band") or body.get("band") or body.get("outcome") or body.get("final_band"):
            st.markdown(
                "<div class='oc-panel oc-warning'><strong>Reading</strong><br>"
                f"{body.get('risk_band') or body.get('band') or body.get('outcome') or body.get('final_band')}</div>",
                unsafe_allow_html=True,
            )
        if body.get("series"):
            key = "coherence" if "coherence" in body["series"][0] else "health"
            st.line_chart({row["step"]: row[key] for row in body["series"]})
        if body.get("history"):
            st.line_chart({row["step"]: row["active_total"] for row in body["history"]})
        if body.get("components"):
            st.bar_chart(body["components"])
        if body.get("nodes"):
            st.dataframe(body["nodes"], use_container_width=True, hide_index=True)
        if body.get("edges"):
            with st.expander("Graph edges"):
                st.dataframe(body["edges"], use_container_width=True, hide_index=True)
        if body.get("trace"):
            st.dataframe(body["trace"], use_container_width=True, hide_index=True)
        if body.get("warnings"):
            for warning in body["warnings"]:
                st.caption(warning)
    if compact_json:
        with st.expander("Result JSON"):
            st.json(result)
    else:
        st.json(result)
    _download("Export JSON", result, "oc_core_demo_result.json")


def _dashboard(graph: dict[str, Any], specs: list[dict[str, Any]]) -> None:
    payload = export_release_context()
    cols = st.columns(4)
    cols[0].metric("Targets", payload["target_total"])
    cols[1].metric("Graph nodes", payload["graph_node_total"])
    cols[2].metric("Specs", payload["spec_total"])
    cols[3].metric("External actions", payload["external_actions"])

    st.markdown(
        "<div class='oc-panel'><strong>Reviewer start</strong><br>"
        "<span class='oc-muted'>Run a bounded case diagnostic, then inspect the graph or proof boundary behind the result.</span></div>",
        unsafe_allow_html=True,
    )
    cases = list_cases()
    case = cases[0]
    spec = _full_spec("case_diagnostic")
    params = _param_controls(spec, case["params"])
    if st.button("Run dashboard case", type="primary"):
        _show_result(run_spec_safe("case_diagnostic", params))

    st.subheader("Available windows")
    rows = [{"spec_id": spec["spec_id"], "window": spec["window_id"], "class": spec["demo_class"], "purpose": spec["purpose"]} for spec in specs]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="OC Core 1.4 Demonstrator", layout="wide")
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    page = st.sidebar.radio("Window", PAGES)
    graph = load_public_graph()
    specs = list_specs()

    st.title("OC Core 1.4 Demonstrator")
    st.caption("V001 public science companion with deterministic local JSON output and explicit proof boundaries.")

    if page == "Dashboard":
        _dashboard(graph, specs)

    elif page == "Case Workspace":
        st.subheader("Case Workspace")
        cases = list_cases()
        selected = st.selectbox("Example case", [case["case_id"] for case in cases])
        case = next(row for row in cases if row["case_id"] == selected)
        st.markdown(f"<div class='oc-panel'><strong>{case['title']}</strong><br><span class='oc-muted'>{case['case_text']}</span></div>", unsafe_allow_html=True)
        spec = _full_spec("case_diagnostic")
        params = _param_controls(spec, case["params"])
        if st.button("Analyze case", type="primary"):
            _show_result(run_spec_safe("case_diagnostic", params))

    elif page == "Model Lab":
        st.subheader("Model Lab")
        choices = _specs_for("model_lab")
        spec_id = st.selectbox("Model", [spec["spec_id"] for spec in choices])
        spec = _full_spec(spec_id)
        st.markdown(f"<div class='oc-panel'><strong>{spec['title']}</strong><br><span class='oc-muted'>{spec['purpose']}</span></div>", unsafe_allow_html=True)
        params = _param_controls(spec)
        if st.button("Run model", type="primary"):
            _show_result(run_spec_safe(spec_id, params))

    elif page == "Decision Calculators":
        st.subheader("Decision Calculators")
        choices = _specs_for("decision_calculators")
        spec_id = st.selectbox("Calculator", [spec["spec_id"] for spec in choices])
        spec = _full_spec(spec_id)
        st.markdown(f"<div class='oc-panel'><strong>{spec['title']}</strong><br><span class='oc-muted'>{spec['output_interpretation']}</span></div>", unsafe_allow_html=True)
        params = _param_controls(spec)
        if st.button("Calculate", type="primary"):
            _show_result(run_spec_safe(spec_id, params))

    elif page == "Science Graph":
        st.subheader("Science Graph")
        nodes = graph.get("nodes", [])
        demo_classes = sorted({node.get("demo_class", "") for node in nodes if node.get("demo_class")})
        left, right = st.columns([2, 1])
        search = left.text_input("Search node text", "")
        demo_class = right.selectbox("Demo class", ["ALL"] + demo_classes)
        rows = [
            node
            for node in nodes
            if (demo_class == "ALL" or node.get("demo_class") == demo_class)
            and (not search or search.lower() in json.dumps(node, ensure_ascii=False).lower())
        ]
        st.metric("Matching nodes", len(rows))
        st.dataframe(_node_rows(rows[:300]), use_container_width=True, hide_index=True)
        selected = st.selectbox("Inspect node", [node["id"] for node in rows[:300]] or ["OC14-N001"])
        radius = st.slider("Neighborhood radius", 1, 3, 1)
        if st.button("Inspect neighborhood", type="primary"):
            _show_result(run_spec_safe("graph_neighborhood", {"node": selected, "radius": radius}))

    elif page == "Proof & Limits":
        st.subheader("Proof & Limits")
        targets = [node for node in graph.get("nodes", []) if str(node.get("id", "")).startswith("OC14-N")]
        search = st.text_input("Find target", "connected")
        matching = [node for node in targets if not search or search.lower() in json.dumps(node, ensure_ascii=False).lower()]
        st.metric("Matching targets", len(matching))
        st.dataframe(_node_rows(matching[:200]), use_container_width=True, hide_index=True)
        target = st.selectbox("Target", [node["id"] for node in matching[:250]] or ["OC14-N001"])
        if st.button("Replay public route", type="primary"):
            _show_result(run_spec_safe("proof_trace_replay", {"target": target}))
        st.markdown(
            "<div class='oc-panel oc-warning'><strong>Boundary</strong><br>"
            "<span class='oc-muted'>Route replay is public evidence structure only. It is not external peer review and not a proof engine.</span></div>",
            unsafe_allow_html=True,
        )

    elif page == "JSON Interface":
        st.subheader("JSON Interface")
        commands = [
            "python -m oc_core_demo list",
            "python -m oc_core_demo cases",
            "python -m oc_core_demo analyze-case --params examples/case_params.json",
            "python -m oc_core_demo run transformation_risk_calculator --params examples/transform_risk_params.json",
            "python -m oc_core_demo graph --node OC14-N001 --radius 2",
            "python -m oc_core_demo explain case_diagnostic --json",
            "python -m oc_core_demo export",
        ]
        for command in commands:
            st.code(command)
        with st.expander("Case schema excerpt"):
            st.json({"case_schema": _full_spec("case_diagnostic")["parameters"], "example_specs": specs[:4]})

    else:
        st.subheader("Release Package")
        payload = export_release_context()
        cols = st.columns(4)
        cols[0].metric("Graph nodes", payload["graph_node_total"])
        cols[1].metric("Targets", payload["target_total"])
        cols[2].metric("Specs", payload["spec_total"])
        cols[3].metric("External actions", payload["external_actions"])
        st.markdown(
            "<div class='oc-panel'><strong>Release boundary</strong><br>"
            "<span class='oc-muted'>Local review artifact only. GitHub, Zenodo, journal submission, outreach and commercial claims remain outside this app.</span></div>",
            unsafe_allow_html=True,
        )
        _show_result(payload, compact_json=False)


if __name__ == "__main__":
    main()
