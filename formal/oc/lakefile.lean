import Lake
open Lake DSL
package oc_qualified_edition where
  version := v!"0.1.0"
  moreLeanArgs := #["-j", "1"]
require mathlib from "vendor/mathlib"
require oc_minimal_obligation_spine from "packages/oc_minimal_obligation_spine"
require oc_projection_causality_identity from "packages/oc_projection_causality_identity"
require oc_maturity_completion_cycle from "packages/oc_maturity_completion_cycle"
lean_lib OCKIndividuationMSpaceComposition where
  roots := #[`OCKIndividuationMSpaceComposition]
lean_lib OCScientificExtensions where
  srcDir := "packages/oc_scientific_extensions"
lean_lib OCQualifiedEdition where
  roots := #[`OCQualifiedEdition]
