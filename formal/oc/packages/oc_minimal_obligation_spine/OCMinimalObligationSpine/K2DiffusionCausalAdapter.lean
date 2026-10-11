import OCMinimalObligationSpine.StableProjectionCurrentK

namespace OCMinimalObligationSpine.K2DiffusionCausalAdapter

open UnifiedEntityProjection

/-!
# Bounded K2 diffusion causal adapter

This module is a mathematical domain realization of the CurrentK and stable
causal-projection interfaces.  It is not empirical validation of diffusion or
of OC.  The old representation exposes one variance snapshot

    s(t,D,b) = 2 * D * t + b.

Two exact parameter states collide at the present snapshot but produce
different receiver effects after one declared time step.  Therefore the old
snapshot encoding cannot have exact receiver-effect semantics and closed
encoded dynamics simultaneously.  The theorem does not imply that a richer K
must use a new carrier: a same-carrier encoder may retain more information.
-/

structure DiffusionState where
  time : Nat
  diffusivity : Nat
  varianceFloor : Nat
deriving DecidableEq, Repr

def advance (state : DiffusionState) : DiffusionState :=
  { state with time := state.time + 1 }

def varianceEffect (state : DiffusionState) : Nat :=
  2 * state.diffusivity * state.time + state.varianceFloor

def snapshotVarianceK : CurrentK where
  State := DiffusionState
  Receiver := Unit
  Effect := Nat
  Carrier := Nat
  stateTransition := advance
  receiverEffect := fun state _ => varianceEffect state
  encode := varianceEffect
  carrierTransition := id
  decodeReceiverEffect := fun carrier _ => carrier

def earlyFast : DiffusionState := ⟨1, 2, 0⟩
def lateSlow : DiffusionState := ⟨2, 1, 0⟩

/-- Both declared states expose the same present variance `s = 4`. -/
theorem present_snapshot_collision :
    snapshotVarianceK.encode earlyFast =
      snapshotVarianceK.encode lateSlow := by
  change (4 : Nat) = 4
  rfl

/-- One time step later their declared receiver effects are `8` and `6`. -/
theorem next_step_receiver_effects_differ :
    snapshotVarianceK.receiverEffect
        (evolveState snapshotVarianceK.stateTransition 1 earlyFast) () ≠
      snapshotVarianceK.receiverEffect
        (evolveState snapshotVarianceK.stateTransition 1 lateSlow) () := by
  change (8 : Nat) ≠ 6
  decide

def futureVarianceDistinction : TrajectoryDistinction snapshotVarianceK where
  left := earlyFast
  right := lateSlow
  step := 1
  receiver := ()
  effect_ne := next_step_receiver_effects_differ

theorem present_snapshot_does_not_express_future_variance :
    Not (Expresses snapshotVarianceK futureVarianceDistinction) := by
  intro separation
  exact separation present_snapshot_collision

/-- The collision is an exact domain instance of the generic CurrentK no-go. -/
theorem present_snapshot_refutes_exact_closed_semantics :
    Not (HasExactDeclaredSemantics snapshotVarianceK) := by
  exact unexpressed_distinction_refutes_exact_declared_semantics
    snapshotVarianceK futureVarianceDistinction
    present_snapshot_does_not_express_future_variance

/-- The complete trajectory projection family itself remains shift-stable. -/
theorem complete_diffusion_trajectory_family_is_shift_stable :
    (currentKTrajectoryProjectionFamily snapshotVarianceK).DynamicsCommute
      snapshotVarianceK.stateTransition shiftCausalTrajectory := by
  exact current_k_trajectory_projections_are_shift_stable snapshotVarianceK

/--
Public/release boundary for the Spot-On real-data replay.

The replay is allowed to close a scoped domain witness only when the selected
dataset is admitted, the endpoint was predeclared, a matched transition stratum
is nonempty, the present-only baseline is rejected at the declared five-sigma
gate, and the structural K2 adapter theorem above is available.  The conclusion
is deliberately scoped to the domain witness; it is not a universal OC
validation or an external all-dataset biological theorem.
-/
structure SpotOnScopedK2EmpiricalWitness : Type where
  selectedDatasetAdmitted : Prop
  singlePredeclaredEndpoint : Prop
  matchedTransitionStratumNonempty : Prop
  presentOnlyBaselineRejectedAtFiveSigma : Prop
  structuralK2AdapterAvailable : Prop
  datasetProof : selectedDatasetAdmitted
  endpointProof : singlePredeclaredEndpoint
  stratumProof : matchedTransitionStratumNonempty
  fiveSigmaProof : presentOnlyBaselineRejectedAtFiveSigma
  adapterProof : structuralK2AdapterAvailable

def SpotOnScopedK2EmpiricalWitness.scopedDomainWitnessClosed
    (witness : SpotOnScopedK2EmpiricalWitness) : Prop :=
  witness.selectedDatasetAdmitted ∧
    witness.singlePredeclaredEndpoint ∧
    witness.matchedTransitionStratumNonempty ∧
    witness.presentOnlyBaselineRejectedAtFiveSigma ∧
    witness.structuralK2AdapterAvailable ∧
    Not (HasExactDeclaredSemantics snapshotVarianceK)

theorem spoton_scoped_k2_empirical_witness_closed
    (witness : SpotOnScopedK2EmpiricalWitness) :
    witness.scopedDomainWitnessClosed := by
  exact ⟨witness.datasetProof,
    witness.endpointProof,
    witness.stratumProof,
    witness.fiveSigmaProof,
    witness.adapterProof,
    present_snapshot_refutes_exact_closed_semantics⟩

end OCMinimalObligationSpine.K2DiffusionCausalAdapter
