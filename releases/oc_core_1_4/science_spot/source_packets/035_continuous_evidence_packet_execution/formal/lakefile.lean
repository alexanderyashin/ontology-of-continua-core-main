import Lake
open Lake DSL

package "oc_continuous_evidence_packet_execution" where

@[default_target]
lean_lib «OCContinuous» where
  roots := #[`OCContinuous]
