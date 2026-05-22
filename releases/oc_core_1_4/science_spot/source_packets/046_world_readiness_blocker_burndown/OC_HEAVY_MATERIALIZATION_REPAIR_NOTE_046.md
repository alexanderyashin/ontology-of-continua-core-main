# OC 046 Heavy Materialization Repair Note

## What Was Tried

The explicit FULL materialization route was run as required. It failed before closure because the deferred manifest included `SURFACE__SCIENTIFIC_RELEASE_READINESS_MODEL_LATEST_JSON`, while the derivation registry marks that surface as `autoderive_enabled=false`. A direct enabled-surface retry then reached the long `build_t1_factory_v1.py` frontier producer and was stopped after a no-output runtime stall, so it is not counted as full downstream proof closure.

## Repair Applied

`run_logion_system_autoderive_v1.ps1` now builds an all-surface map and skips target ids that are present but disabled, emitting `LOGION_SYSTEM_AUTODERIVE_TARGET_SKIPPED_DISABLED` instead of failing as if the surface id did not exist.

## Current Honest Status

| Item | Status | Meaning |
| --- | --- | --- |
| Disabled surface mismatch | repaired | Future runs distinguish disabled known surfaces from genuinely missing ids. |
| Impacted surface files | 25 existing / 0 missing | 046 verifies all impacted paths exist before release packet validation. |
| Stale tuple/feedback consumers | 21 | Still a runtime materialization pressure signal, not a theory blocker. |
| Long frontier pass | runtime-window limitation | Requires a dedicated later run if owner wants full heavy frontier propagation, but 046 world-readiness boundaries remain no-send for external gates. |

Disabled impacted surface ids: none detected.
