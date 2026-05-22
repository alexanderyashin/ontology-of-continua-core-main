import Lake
open Lake DSL

package "oc_full_k_hierarchy_evidence_closure" where

@[default_target]
lean_lib «OCFullK» where
  roots := #[`OCFullK]
