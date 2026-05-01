# Physics/Chemistry Official Batch Factory

Verdict: `BLOCKED_ACQUISITION_READY_NO_SEND`
Grand TOE support allowed: `false`
Open blockers: `9`

| Domain | Candidate N | Eligible N | Minimum N | Gate valid | Status |
| --- | ---: | ---: | ---: | --- | --- |
| `physics` | `44` | `0` | `20` | `false` | `BLOCKED_ACQUISITION_READY_NO_SEND` |
| `chemistry` | `12` | `0` | `20` | `false` | `BLOCKED_ACQUISITION_READY_NO_SEND` |

No-send locks are active. Candidate packs in this directory must not be registered while blocked.

Physics acquisition packet:
- `validation/heldout/grand_science/physics_chemistry/official_batch/OC133_PHYSICS_OFFICIAL_BATCH_ACQUISITION_PACKET.json`

## Missing Official Snapshots

### Physics
- `physics_nist_constants_pre_target_lock_manifest_v1` -> `validation/_raw/physics_nist_constants_pre_target_lock_manifest_v1.json`
- `physics_nist_asd_hydrogen_balmer_lines_v1` -> `validation/_raw/physics_nist_asd_hydrogen_balmer_lines_v1.tsv`

### Chemistry
- `chemistry_pubchem_20_compound_properties_v1` -> `validation/_raw/chemistry_pubchem_20_compound_properties_v1.json`
- `chemistry_nist_webbook_water_gas_thermo_v1` -> `validation/_raw/chemistry_nist_webbook_water_gas_thermo_v1.html`
- `chemistry_nist_webbook_water_ir_spectrum_v1` -> `validation/_raw/chemistry_nist_webbook_water_ir_spectrum_v1.html`
- `chemistry_nist_kinetics_water_v1` -> `validation/_raw/chemistry_nist_kinetics_water_v1.html`

## Open Blockers
- `SOURCE_SEPARATION_MODE_NOT_ALLOWED::official_snapshot_replay`
- `PRE_TARGET_LOCK_REQUIRED`
- `TARGET_HIDDEN_UNTIL_SCORING_REQUIRED`
- `SOURCE_SEPARATION_NOT_DECLARED_BEFORE_SCORING`
- `SOURCE_SEPARATION_ATTESTATION_REQUIRED`
- `SOURCE_SEPARATION_MODE_NOT_ALLOWED`
- `GRAND_TOE_SUPPORT_NOT_ALLOWED`
- `N_BELOW_MINIMUM::chemistry::12/20`
- `N_BELOW_MINIMUM::20`
