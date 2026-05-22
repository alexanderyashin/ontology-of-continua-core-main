import Lake
open Lake DSL

package "oc_continuous_replay_full_closure" where

@[default_target]
lean_lib «OCContinuousReplay» where
  roots := #[`OCContinuousReplay]
