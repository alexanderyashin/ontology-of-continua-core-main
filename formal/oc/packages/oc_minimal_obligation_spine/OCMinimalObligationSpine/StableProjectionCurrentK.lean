import OCMinimalObligationSpine.CurrentK
import OCMinimalObligationSpine.StableProjectionWorldModel

namespace OCMinimalObligationSpine

open UnifiedEntityProjection

/-!
# CurrentK adapter for the stable-projection core

This module is intentionally downstream of both `CurrentK` and the generic
stable-projection theorem family.  Keeping the adapter separate prevents the
generic world-model facet from depending circularly on the particular current
representation record that it conceptually precedes.
-/

/-- Attach the generic causal-trajectory projection family to a declared K. -/
def currentKTrajectoryProjectionFamily (K : CurrentK) :
    ProjectionFamily K.State Nat (fun _ => K.Receiver -> K.Effect) :=
  trajectoryProjectionFamily K.receiverEffect K.stateTransition

theorem current_k_trajectory_projections_are_shift_stable
    (K : CurrentK) :
    (currentKTrajectoryProjectionFamily K).DynamicsCommute
      K.stateTransition shiftCausalTrajectory := by
  exact trajectory_projection_dynamics_commute
    K.receiverEffect K.stateTransition

/-
Exact declared K semantics force its encoder to refine the stable projection
family.  They still do not imply that the family separates all K states.
-/
theorem exact_current_k_encoder_refines_stable_projection_family
    (K : CurrentK)
    (exactSemantics : HasExactDeclaredSemantics K)
    {left right : K.State}
    (collision : K.encode left = K.encode right) :
    (currentKTrajectoryProjectionFamily K).signature left =
      (currentKTrajectoryProjectionFamily K).signature right := by
  exact exact_causal_dynamic_encoder_refines_trajectory_signature
    exactSemantics.1 exactSemantics.2 collision

end OCMinimalObligationSpine
