# OC Core 1.4 Public Demonstrator

This directory contains the public-safe source and static data for the OC Core 1.4 Demonstrator.

The demonstrator is included as a release-facing inspection tool. It exposes the public system workbench, science graph, formula atlas, wiki, proof/evidence routes, and reviewer data produced by the current V010 demonstrator pipeline.

## Public Boundary

- Demo version in data: `V010`.
- Cerberus status in included public data: `PASS`.
- Private portable packages, desktop shortcut state, local runtime paths, owner-machine data, review-machine internals, and private provenance are not included.
- Public data is static and sanitized; unsupported science remains represented as a boundary or formalization obligation.

## Useful Paths

- `web/`: React/Vite web application source.
- `web/public/data/`: public generated atlas, graph, formula, wiki, workbench, proof, and manifest data.
- `oc_core_demo/`: Python CLI/engine source retained for inspection and deterministic reviewer tools.
- `schemas/`: public JSON schemas used by the demonstrator.

To run the web app from this source tree, install the web dependencies in `web/` and use the package scripts there. The public release package itself is source/data only; it does not include private runtime bundles or desktop launcher state.
