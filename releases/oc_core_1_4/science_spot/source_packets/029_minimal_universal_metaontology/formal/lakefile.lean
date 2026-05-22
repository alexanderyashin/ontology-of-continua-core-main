import Lake
open Lake DSL

package "oc_minimal_metaontology" where

@[default_target]
lean_lib «OCMinimal» where
  roots := #[`OCMinimal]
