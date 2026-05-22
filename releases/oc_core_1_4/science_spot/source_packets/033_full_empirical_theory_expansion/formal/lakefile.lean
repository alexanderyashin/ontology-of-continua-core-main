import Lake
open Lake DSL

package "oc_full_empirical_theory_expansion" where

@[default_target]
lean_lib «OCFullEmpirical» where
  roots := #[`OCFullEmpirical]
