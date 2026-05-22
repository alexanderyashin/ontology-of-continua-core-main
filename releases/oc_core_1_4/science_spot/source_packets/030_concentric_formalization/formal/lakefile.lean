import Lake
open Lake DSL

package "oc_concentric_formalization" where

@[default_target]
lean_lib «OCConcentric» where
  roots := #[`OCConcentric]
