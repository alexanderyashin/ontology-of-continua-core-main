import Lake
open Lake DSL

package "oc_evidence_operationalization" where

@[default_target]
lean_lib «OCOperational» where
  roots := #[`OCOperational]
