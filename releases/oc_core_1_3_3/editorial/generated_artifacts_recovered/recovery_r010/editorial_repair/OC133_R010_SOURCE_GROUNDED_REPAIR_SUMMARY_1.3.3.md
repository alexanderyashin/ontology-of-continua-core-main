# OC Core 1.3.3 r010 Source-Grounded Repair Summary

Status: `PASS`
Artifact hash: `64e29948788b215ce54e6db2d681a7cab16c525245e085dc4e44f2f19eb43e84`

## Fields

- `status`: PASS
- `source_grounded_repair_status`: REPAIR_REQUIRED
- `release_id`: oc_core_1_3_3
- `version`: 1.3.3
- `source_revision`: recovery_r009
- `service_status`: DONE
- `queue_status`: DONE
- `common_llm_service_status`: PASS
- `repair_record_total`: 24
- `accepted_candidate_total`: 8
- `accepted_candidate_promoted_total`: 0
- `accepted_repair_blocker_total`: 0
- `unresolved_repair_record_total`: 24
- `source_grounded_repair_loop_status`: PASS
- `accepted_repair_promotion_status`: PASS
- `local_editorial_capability_boundary_status`: LOCAL_EDITORIAL_CAPABILITY_EXHAUSTED
- `repair_queue_status`: DONE
- `repair_queue_done_status`: PASS
- `repair_queue_packet_total`: 24
- `repair_queue_packet_done_total`: 24
- `repair_ollama_invocation_total`: 24
- `ollama_invocation_total`: 24
- `unmanaged_ollama_call_total`: 0
- `service_ledger_ref`: logion_local/runtime/observability/logion_llm/LOGION_LLM_SERVICE_LEDGER.ndjson
- `v_model_lowest_checked_level`: L10
- `v_model_flow`: L10_source_grounded_repair_suggestions_without_public_promotion
- `model_sequence`: ['qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b', 'qwen2.5-coder:3b']
- `cadence_sequence`: ['cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound', 'cheap_model_requested_or_profile_bound']
- `blocker_class_counts`: {'fabrication_risk': 8, 'forbidden_public_term': 3, 'missing_anchor': 15, 'reader_quality_blocker': 2, 'weak_example': 12, 'weak_formal_anchor': 13, 'weak_limitation': 3}
- `capability_boundary`: Local Ollama generated bounded repair suggestions, but unresolved source-grounding blockers remain; no generated repair text is promoted into public PDFs.
