import Lake
open Lake DSL

package "oc_universal_metamodel" where

@[default_target]
lean_lib «OCUniversal» where
  roots := #[`OCUniversal]
