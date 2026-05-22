import Lake
open Lake DSL

package "oc_empirical_crown_domain_closure" where

@[default_target]
lean_lib «OCEmpirical» where
  roots := #[`OCEmpirical]
