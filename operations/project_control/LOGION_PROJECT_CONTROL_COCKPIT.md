# Logion Project Control Cockpit

- Portfolio state: `LOGION_PROJECT_CONTROL_ACTIVE`
- OC133 release state: `OC_CORE_1_3_3_EXTERNAL_REVIEW_READY_NO_SEND`
- External-review ready no-send: `true`
- Full science program: `OC_FULL_SCIENCE_PROGRAM_RUNNING`
- All-domain blockers: `2`
- Cerberus critical/high: `0` / `0`
- Journal packages: `8`
- Dirty tree governed/current: `true` / `true`
- Delta Queue significant/trigger: `false` / `false`
- Process coherence: `PASS` critical/high=`0`
- External LLM budget/day: `2000000`
- Host compute: `allowed`
- Budget action: `REQUEST_EXTRA_LLM_BUDGET`

## Workstreams

- `OC133_RELEASE_FOREGROUND` state=`OC_CORE_1_3_3_EXTERNAL_REVIEW_READY_NO_SEND` priority=`1` release_owner=`true`
- `OC_FULL_SCIENCE_BACKGROUND` state=`OC_FULL_SCIENCE_PROGRAM_RUNNING` priority=`2` release_owner=`false`
- `ESTRA_TOOLKIT` state=`AVAILABLE_ISOLATED_NOT_OC133_RELEASE_OWNER` priority=`3` release_owner=`false`
- `EA2O` state=`AVAILABLE_ISOLATED_NOT_OC133_RELEASE_OWNER` priority=`4` release_owner=`false`
- `OTHER_WORKSTREAMS` state=`AVAILABLE_ISOLATED_NOT_OC133_RELEASE_OWNER` priority=`5` release_owner=`false`

## Locks

- `OC133_RELEASE_ARTIFACT_LOCK` owner=`OC133_RELEASE_FOREGROUND` background_release_write=`false`
- `OC_FULL_SCIENCE_BACKGROUND_LOCK` owner=`OC_FULL_SCIENCE_BACKGROUND` background_release_write=`false`
- `NON_OC_WORKSTREAM_ISOLATION_LOCK` owner=`ESTRA_TOOLKIT_EA2O_OTHER` background_release_write=`false`

Controller hash: `f7aac4cd0a464d9f51a975beb24b544b51cf4672909dd4241665ceef8817ebaa`
