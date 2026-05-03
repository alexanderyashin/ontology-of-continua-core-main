# OC Core 1.3.3 Source Intake Audit

Status: `PASS`
Artifact hash: `409d2b1afd4a736ad60351daff490f62013d685c786fbc98450420b9479dbdc2`

## Policy

- `accepted_language`: English/public-release-safe source routes only
- `reject_non_english_titles`: True
- `reject_only_non_english_source_paths`: True
- `reject_import_routes_as_science_nodes`: True
- `reject_placeholders`: True
- `reject_structural_route_only_nodes`: True
- `note`: Rejected rows remain in L10b forensic evidence but are not allowed into L10c assembly.

## Summary

- `total_l10b_rows`: 9612
- `covered_by_current_total`: 5
- `raw_recovered_candidate_total`: 9607
- `accepted_recovered_candidate_total`: 4730
- `rejected_recovered_candidate_total`: 4877
- `accepted_bad_row_total`: 0

## Rejection Reasons

- `import_route_not_science_node`: 1518
- `non_english_cyrillic_title`: 1606
- `only_non_english_source_paths`: 4326
- `placeholder_or_template_title`: 2
- `structural_route_only_no_science_heading`: 1518
