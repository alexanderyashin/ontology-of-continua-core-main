-- Modified for the portable OC release preview: local dependency paths and explicit OC audit roots.
-- Original recipe SHA256: d2c8d1a560938beee0a136ecbd41790231630fd457739b08c9b3cc843898c72f
import Lake
open Lake DSL

package «oc_projection_causality_identity» where
  version := v!"0.1.0"

require mathlib from "../../vendor/mathlib"
require oc_minimal_obligation_spine from "../oc_minimal_obligation_spine"

lean_lib OCProjectionCausalityIdentity where
  roots := #[
    `OCProjectionCausalityIdentity,
    `OCProjectionCausalityIdentityAudit,
    `OCProjectionCausalityIdentitySignatures
  ]
