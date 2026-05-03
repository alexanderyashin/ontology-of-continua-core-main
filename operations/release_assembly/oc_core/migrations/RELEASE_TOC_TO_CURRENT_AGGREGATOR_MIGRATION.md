# Release TOC to Current Aggregator Migration

Status: `APPLIED`

The previous concrete release table of contents was a version-bound planning artifact. The canonical source is now:

- common source: `operations/release_assembly/oc_core/current_release_aggregator/OC_CORE_CURRENT_RELEASE_AGGREGATOR.json`
- versioned instance pattern: `releases/{release_id}/editorial/release_assembly/OC_CORE_RELEASE_INSTANCE_{version}.json`

Rule: common assembly inputs may not embed a concrete release version or public-record metadata. Concrete release numbers are assigned only by the release instance builder.
