import Lake
open Lake DSL

package "oc_k3_cognition_empirical_upgrade" where

@[default_target]
lean_lib «OCCognition» where
  roots := #[`OCCognition]
