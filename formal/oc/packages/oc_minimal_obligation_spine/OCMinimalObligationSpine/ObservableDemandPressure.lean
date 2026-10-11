import OCMinimalObligationSpine.IrreduciblePressure

namespace OCMinimalObligationSpine

open UnifiedEntityProjection

universe uReceiver uEffect uRepairCandidate

/--
An executable receiver-side rule fixed before looking at any representation,
repair, lift, or proposed K successor.

`acceptsMergedEffects step receiver leftEffect rightEffect = false` means that
the two source-level receiver effects are not allowed to remain merged for this
declared receiver and step.  The rule has no access to `State`, `Carrier`,
`encode`, repair candidates, lift candidates, or axis-birth vocabulary, so it
cannot make demand true merely because a desired K transition exists.
-/
structure ObservableReceiverConstraint
    (Receiver : Type uReceiver)
    (Effect : Type uEffect) where
  acceptsMergedEffects : Nat -> Receiver -> Effect -> Effect -> Bool

/-- The left source-level receiver effect certified by a distinction. -/
def observedLeftEffect
    {K : CurrentK}
    (d : TrajectoryDistinction K) : K.Effect :=
  K.receiverEffect
    (evolveState K.stateTransition d.step d.left)
    d.receiver

/-- The right source-level receiver effect certified by a distinction. -/
def observedRightEffect
    {K : CurrentK}
    (d : TrajectoryDistinction K) : K.Effect :=
  K.receiverEffect
    (evolveState K.stateTransition d.step d.right)
    d.receiver

/--
Observable demand evidence: a frozen receiver constraint rejects merging the
two actually observed source-level effects.  This predicate mentions neither
the current encoder nor any proposed successor.
-/
def ReceiverConstraintFalsified
    {K : CurrentK}
    (constraint : ObservableReceiverConstraint K.Receiver K.Effect)
    (d : TrajectoryDistinction K) : Prop :=
  constraint.acceptsMergedEffects
      d.step d.receiver (observedLeftEffect d) (observedRightEffect d) =
    false

/--
The non-circular active-demand policy induced by one frozen executable
receiver constraint.
-/
def activeDemandFromReceiverConstraint
    {K : CurrentK}
    (constraint : ObservableReceiverConstraint K.Receiver K.Effect) :
    ActiveDemand K :=
  fun d => ReceiverConstraintFalsified constraint d

theorem receiverConstraintFalsified_activates_demand
    {K : CurrentK}
    (constraint : ObservableReceiverConstraint K.Receiver K.Effect)
    (d : TrajectoryDistinction K)
    (falsified : ReceiverConstraintFalsified constraint d) :
    activeDemandFromReceiverConstraint constraint d :=
  falsified

/--
Even a certified source-level effect difference is inactive when the frozen
receiver rule explicitly accepts merging that effect pair.  Thus bare
difference is not demand.
-/
theorem receiverConstraintAccepts_deactivates_demand
    {K : CurrentK}
    (constraint : ObservableReceiverConstraint K.Receiver K.Effect)
    (d : TrajectoryDistinction K)
    (accepted :
      constraint.acceptsMergedEffects
          d.step d.receiver (observedLeftEffect d) (observedRightEffect d) =
        true) :
    Not (activeDemandFromReceiverConstraint constraint d) := by
  simp only
    [activeDemandFromReceiverConstraint, ReceiverConstraintFalsified, accepted,
      Bool.true_eq_false, not_false_eq_true]

/-- An accepted merge blocks pressure before any repair or M-space reasoning. -/
theorem receiverConstraintAccepts_blocks_pressure
    {K : CurrentK}
    (search : RepairSearchClass.{uRepairCandidate} K)
    (constraint : ObservableReceiverConstraint K.Receiver K.Effect)
    (d : TrajectoryDistinction K)
    (accepted :
      constraint.acceptsMergedEffects
          d.step d.receiver (observedLeftEffect d) (observedRightEffect d) =
        true) :
    Not
      (IrreduciblePressureWithin
        search (activeDemandFromReceiverConstraint constraint) d) := by
  intro pressure
  exact (receiverConstraintAccepts_deactivates_demand
    constraint d accepted) pressure.1

/--
A finite declaration of the complete same-K repair scope used by a replay.
Completeness is explicit: a short list without this proof cannot certify repair
exhaustion.
-/
structure FiniteDeclaredRepairSearch
    {K : CurrentK}
    (search : RepairSearchClass.{uRepairCandidate} K) where
  candidates : List search.Candidate
  complete : forall candidate : search.Candidate, candidate ∈ candidates

/--
Failure of every admissible architecture-preserving member of a complete
finite declaration proves absence of a repair in exactly that declared scope.
-/
theorem no_repair_of_complete_finite_declared_failures
    {K : CurrentK}
    (search : RepairSearchClass.{uRepairCandidate} K)
    (d : TrajectoryDistinction K)
    (declared : FiniteDeclaredRepairSearch search)
    (everyListedCandidateFails :
      forall candidate,
        candidate ∈ declared.candidates ->
          search.architecturePreserving candidate ->
            search.admissible candidate ->
              Not (Resolves (search.repair candidate) d)) :
    Not (RepairableWithin search d) := by
  apply exhaustive_scoped_no_repair search d
  intro candidate preservesArchitecture isAdmissible
  exact everyListedCandidateFails
    candidate (declared.complete candidate) preservesArchitecture isAdmissible

/--
Minimal non-circular pressure realization theorem.

Pressure follows from three independent evidence channels:

1. a frozen receiver constraint is falsified by source-level effects;
2. the current encoder collides on the demanded states;
3. every admissible architecture-preserving repair in the declared scope
   fails.

This proves scoped representational pressure only.  It does not construct a
lift, a physical axis, a domain law, or an empirical K transition.
-/
theorem irreduciblePressureWithin_of_observable_demand_collision_and_exhausted_repairs
    {K : CurrentK}
    (search : RepairSearchClass.{uRepairCandidate} K)
    (constraint : ObservableReceiverConstraint K.Receiver K.Effect)
    (d : TrajectoryDistinction K)
    (constraintFalsified : ReceiverConstraintFalsified constraint d)
    (currentCollision : K.encode d.left = K.encode d.right)
    (everyCandidateFails :
      forall candidate,
        search.architecturePreserving candidate ->
          search.admissible candidate ->
            Not (Resolves (search.repair candidate) d)) :
    IrreduciblePressureWithin
      search (activeDemandFromReceiverConstraint constraint) d := by
  apply irreduciblePressureWithin_intro
  · exact constraintFalsified
  · intro currentExpresses
    exact currentExpresses currentCollision
  · exact exhaustive_scoped_no_repair search d everyCandidateFails

/--
Finite-replay form of the same theorem.  The declared candidate list and its
completeness proof make the exhaustion boundary inspectable.
-/
theorem irreduciblePressureWithin_of_finite_observable_replay
    {K : CurrentK}
    (search : RepairSearchClass.{uRepairCandidate} K)
    (constraint : ObservableReceiverConstraint K.Receiver K.Effect)
    (d : TrajectoryDistinction K)
    (declared : FiniteDeclaredRepairSearch search)
    (constraintFalsified : ReceiverConstraintFalsified constraint d)
    (currentCollision : K.encode d.left = K.encode d.right)
    (everyListedCandidateFails :
      forall candidate,
        candidate ∈ declared.candidates ->
          search.architecturePreserving candidate ->
            search.admissible candidate ->
              Not (Resolves (search.repair candidate) d)) :
    IrreduciblePressureWithin
      search (activeDemandFromReceiverConstraint constraint) d := by
  apply irreduciblePressureWithin_intro
  · exact constraintFalsified
  · intro currentExpresses
    exact currentExpresses currentCollision
  · exact no_repair_of_complete_finite_declared_failures
      search d declared everyListedCandidateFails

end OCMinimalObligationSpine
