import Lake
open Lake DSL

package "oc_rolling_empirical_upgrade_execution" where

@[default_target]
lean_lib «OCRolling» where
  roots := #[`OCRolling]
