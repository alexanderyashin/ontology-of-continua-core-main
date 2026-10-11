import OCKIndividuationMSpaceComposition.ContextIndexedSymmetry
import OCKIndividuationMSpaceComposition.SymmetryFoundationsCore
import OCKIndividuationMSpaceComposition.SymmetryInvariantQuotient

namespace OCKIndividuationMSpaceComposition

universe uState uObservable uEvidence

/-!
# Context-indexed OC symmetries as the two-point symmetry core

`ContextIndexedSymmetry` already gives a typed local stabilizer: a state
equivalence must preserve transition, observation, evidence and
admissibility.  This bridge adds the extra hypotheses needed for the
distinction/axis kernel: involutivity and fixed-point freeness.  It then
reuses the core results without identifying a context-local symmetry with a
universal OC symmetry.

The bridge is intentionally conditional.  A local automorphism that is not
involutive or has fixed points does not enter the two-point axis model merely
because it has been called a symmetry.
-/

/-- A local mechanics symmetry that is exactly a free involution. -/
structure InvolutiveLocalSymmetry
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    (mechanics : LocalMechanics State Observable Evidence)
    extends LocalSymmetry mechanics where
  involutive : ∀ state, stateEquiv (stateEquiv state) = state
  fixedPointFree : ∀ state, stateEquiv state ≠ state

/-- Forget the extra mechanics surfaces and expose the core action. -/
def involutiveLocalSymmetryAction
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (symmetry : InvolutiveLocalSymmetry mechanics) :
    FixedPointFreeInvolution State where
  action := symmetry.stateEquiv
  involutive := symmetry.involutive
  fixedPointFree := symmetry.fixedPointFree

/-- The local observation is invariant on every generated axis. -/
theorem local_symmetry_observation_is_invariant
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (symmetry : InvolutiveLocalSymmetry mechanics) :
    InvariantObservable (involutiveLocalSymmetryAction symmetry)
      mechanics.observation :=
  symmetry.observation_eq

/-- The local evidence label is invariant on every generated axis. -/
theorem local_symmetry_evidence_is_invariant
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (symmetry : InvolutiveLocalSymmetry mechanics) :
    InvariantObservable (involutiveLocalSymmetryAction symmetry)
      mechanics.evidence :=
  symmetry.evidence_eq

/-- Admissibility is an axis-invariant state predicate. -/
theorem local_symmetry_admissibility_is_axis_invariant
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (symmetry : InvolutiveLocalSymmetry mechanics) :
    AxisInvariant (involutiveLocalSymmetryAction symmetry)
      mechanics.admissible :=
  symmetry.admissible_iff

/-- The local action preserves the canonical axis class. -/
theorem local_symmetry_preserves_axis_class
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (symmetry : InvolutiveLocalSymmetry mechanics) (state : State) :
    axisClass (involutiveLocalSymmetryAction symmetry)
        (symmetry.stateEquiv state) =
      axisClass (involutiveLocalSymmetryAction symmetry) state :=
  action_preserves_axis_class (involutiveLocalSymmetryAction symmetry) state

/-- Observation factorization and local stabilizer invariance coincide. -/
theorem local_observation_factors_iff_invariant
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (symmetry : InvolutiveLocalSymmetry mechanics) :
    InvariantObservable (involutiveLocalSymmetryAction symmetry)
        mechanics.observation ↔
      ∃ factor : AxisQuotient (involutiveLocalSymmetryAction symmetry) →
          Observable,
        ∀ state,
          factor (axisClass (involutiveLocalSymmetryAction symmetry) state) =
            mechanics.observation state :=
  invariant_observable_iff_axis_quotient_factor
    (involutiveLocalSymmetryAction symmetry) mechanics.observation

end OCKIndividuationMSpaceComposition
