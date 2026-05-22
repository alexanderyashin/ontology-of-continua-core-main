import Lake
open Lake DSL

package "oc_k2_biology_empirical_upgrade" where

@[default_target]
lean_lib «OCBiology» where
  roots := #[`OCBiology]
