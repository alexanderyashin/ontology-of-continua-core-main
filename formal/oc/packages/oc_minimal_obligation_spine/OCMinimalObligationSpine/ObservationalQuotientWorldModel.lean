import OCMinimalObligationSpine.StableProjectionWorldModel

namespace OCMinimalObligationSpine

open UnifiedEntityProjection

universe uSource uReceiver uEffect

variable
  {Source : Type uSource}
  {Receiver : Type uReceiver}
  {Effect : Type uEffect}

/-!
# Canonical observational quotient world model

`StableProjectionWorldModel` deliberately leaves joint separation as a
domain-supplied hypothesis when its entity type is fixed in advance.  This
module closes the corresponding mathematical existence question without
pretending that unobservable raw-state differences can be reconstructed.

For any deterministic transition and typed receiver-effect interface, identify
two source states exactly when every finite-step receiver effect agrees.  The
resulting quotient is the canonical observational state space.  Its complete
trajectory projections:

* jointly separate quotient states by construction;
* commute with the induced quotient dynamics;
* preserve the present receiver effects at step zero; and
* form a causally and dynamically exact minimal encoder of the source process.

This is a theorem about the observational quotient induced by a declared
interface.  It does not assert that a chosen physical observation interface is
complete for an inaccessible raw ontology.
-/

/-- Equality of all finite-step receiver effects. -/
def trajectoryObservationalSetoid
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) : Setoid Source where
  r left right :=
    causalTrajectorySignature effect transition left =
      causalTrajectorySignature effect transition right
  iseqv := {
    refl := fun _ => rfl
    symm := fun equality => equality.symm
    trans := fun leftMiddle middleRight => leftMiddle.trans middleRight
  }

/-- The source process modulo complete causal-trajectory indistinguishability. -/
abbrev ObservationalState
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :=
  Quotient (trajectoryObservationalSetoid effect transition)

/-- Canonical projection from raw source states to observational states. -/
def observationalQuotient
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :
    Source -> ObservationalState effect transition :=
  Quotient.mk (trajectoryObservationalSetoid effect transition)

/-- The complete trajectory signature is well-defined on quotient states. -/
def observationalTrajectorySignature
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :
    ObservationalState effect transition -> Nat -> Receiver -> Effect :=
  Quotient.lift
    (causalTrajectorySignature effect transition)
    (fun _ _ sameTrajectory => sameTrajectory)

/-- Each finite step is one projection of the observational state. -/
def observationalProjectionFamily
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :
    ProjectionFamily
      (ObservationalState effect transition)
      Nat
      (fun _ => Receiver -> Effect) where
  project step state :=
    observationalTrajectorySignature effect transition state step

theorem observational_projection_signature_eq_trajectory_signature
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source)
    (state : ObservationalState effect transition) :
    (observationalProjectionFamily effect transition).signature state =
      observationalTrajectorySignature effect transition state := by
  rfl

/--
The quotient projections jointly separate observational states.  No
raw-state injectivity premise is required because precisely the
trajectory-indistinguishable states have been identified.
-/
theorem observational_projection_family_jointly_separates
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :
    (observationalProjectionFamily effect transition).JointlySeparates := by
  intro left right
  refine Quotient.inductionOn₂ left right ?_
  intro leftSource rightSource
  intro representativeSignaturesEqual
  apply Quotient.sound
  exact representativeSignaturesEqual

/--
Complete trajectory equality is preserved by one source transition, so the
source transition descends to the observational quotient.
-/
theorem trajectory_observational_equivalence_is_transition_invariant
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source)
    {left right : Source}
    (sameTrajectory :
      causalTrajectorySignature effect transition left =
        causalTrajectorySignature effect transition right) :
    causalTrajectorySignature effect transition (transition left) =
      causalTrajectorySignature effect transition (transition right) := by
  calc
    causalTrajectorySignature effect transition (transition left) =
        shiftCausalTrajectory
          (causalTrajectorySignature effect transition left) :=
      causal_trajectory_signature_has_closed_dynamics
        effect transition left
    _ = shiftCausalTrajectory
          (causalTrajectorySignature effect transition right) := by
      rw [sameTrajectory]
    _ = causalTrajectorySignature effect transition (transition right) :=
      (causal_trajectory_signature_has_closed_dynamics
        effect transition right).symm

/-- The deterministic transition induced on observational quotient states. -/
def observationalTransition
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :
    ObservationalState effect transition ->
      ObservationalState effect transition :=
  Quotient.lift
    (fun source =>
      observationalQuotient effect transition (transition source))
    (fun _ _ sameTrajectory =>
      Quotient.sound
        (trajectory_observational_equivalence_is_transition_invariant
          effect transition sameTrajectory))

/-- Quotient dynamics shift the complete trajectory projections by one step. -/
theorem observational_projection_dynamics_commute
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :
    (observationalProjectionFamily effect transition).DynamicsCommute
      (observationalTransition effect transition)
      shiftCausalTrajectory := by
  intro state
  refine Quotient.inductionOn state ?_
  intro source
  exact causal_trajectory_signature_has_closed_dynamics
    effect transition source

/--
The canonical quotient therefore supplies the realization package that was
only hypothetical for an arbitrary preselected entity type.
-/
def canonicalObservationalWorldModel
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :
    WorldModelRealizationHypothesis
      (ObservationalState effect transition)
      Nat
      (fun _ => Receiver -> Effect)
      (observationalProjectionFamily effect transition)
      (observationalTransition effect transition)
      shiftCausalTrajectory where
  jointlySeparates :=
    observational_projection_family_jointly_separates effect transition
  dynamicsCommute :=
    observational_projection_dynamics_commute effect transition

/-- Step zero of the quotient trajectory recovers every present effect. -/
theorem observational_quotient_preserves_receiver_effects
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :
    PreservesTypedReceiverEffects effect
      (observationalQuotient effect transition)
      (fun state receiver =>
        observationalTrajectorySignature effect transition state 0 receiver) := by
  intro source receiver
  rfl

/-- The source transition is represented exactly by the quotient transition. -/
theorem observational_quotient_has_closed_dynamics
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :
    PreservesTypedDeterministicDynamics transition
      (observationalQuotient effect transition)
      (observationalTransition effect transition) := by
  intro source
  rfl

/--
No causally exact encoder may identify more source pairs than the canonical
observational quotient: equality of complete trajectories is exactly quotient
equality.  A nonminimal exact encoder may still identify fewer pairs.
-/
theorem observational_quotient_is_causally_minimal
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :
    IsCausalDynamicallyMinimalEncoder effect transition
      (observationalQuotient effect transition) := by
  intro left right sameTrajectory
  exact Quotient.sound sameTrajectory

/--
Publication-facing closure theorem for the mathematical world-model core:
every deterministic typed observation process has a stable, jointly
separating, causally minimal observational quotient.
-/
structure CanonicalObservationalWorldModelCertificate
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) : Prop where
  jointlySeparates :
    (observationalProjectionFamily effect transition).JointlySeparates
  dynamicsCommute :
    (observationalProjectionFamily effect transition).DynamicsCommute
      (observationalTransition effect transition)
      shiftCausalTrajectory
  preservesEffects :
    PreservesTypedReceiverEffects effect
      (observationalQuotient effect transition)
      (fun state receiver =>
        observationalTrajectorySignature effect transition state 0 receiver)
  closedDynamics :
    PreservesTypedDeterministicDynamics transition
      (observationalQuotient effect transition)
      (observationalTransition effect transition)
  causallyMinimal :
    IsCausalDynamicallyMinimalEncoder effect transition
      (observationalQuotient effect transition)

theorem canonical_observational_world_model_certificate
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :
    CanonicalObservationalWorldModelCertificate effect transition where
  jointlySeparates :=
    observational_projection_family_jointly_separates effect transition
  dynamicsCommute :=
    observational_projection_dynamics_commute effect transition
  preservesEffects :=
    observational_quotient_preserves_receiver_effects effect transition
  closedDynamics :=
    observational_quotient_has_closed_dynamics effect transition
  causallyMinimal :=
    observational_quotient_is_causally_minimal effect transition

end OCMinimalObligationSpine
