import Lake
open Lake DSL

package "oc_sequential_evidence_packet_closure" where

@[default_target]
lean_lib «OCSequential» where
  roots := #[`OCSequential]
