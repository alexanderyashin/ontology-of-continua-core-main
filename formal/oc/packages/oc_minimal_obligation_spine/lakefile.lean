-- Modified for the portable OC release preview: local dependency paths and explicit OC audit roots.
-- Original recipe SHA256: df74ab2b39460b85f39e39fe865ffaec2b762c8ac56140b2163564014426f9de
import Lake
open Lake DSL

package «oc_minimal_obligation_spine» where
  version := v!"0.1.0"

require mathlib from "../../vendor/mathlib"

lean_lib OCMinimalObligationSpine where
  roots := #[`OCMinimalObligationSpine]
