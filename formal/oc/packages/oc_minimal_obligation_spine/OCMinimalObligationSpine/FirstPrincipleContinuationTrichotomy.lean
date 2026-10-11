import OCMinimalObligationSpine.ScopedExactSuccessor

namespace OCMinimalObligationSpine

open UnifiedEntityProjection

universe uLiftCarrier uLiftCandidate uRepairCandidate

/-!
# Scoped formal content of the OC contradiction-driven first principle

The programmatic first principle says that a causally insufficient
representation must be repaired or refined inside frozen admissible classes,
or exact continuation in those classes fails.  This module states and proves
that precise representational claim.

The theorem does not call the refinement a physical axis birth and does not
call scoped continuation failure a physical collapse.  Those transfers still
require the independent packages in `PhysicalAdmissibility` and
`PhysicalLiftCollapse`.
-/

/--
Exact continuation inside the declared representational scope means that
either an admissible architecture-preserving same-K repair exists or an
admissible resolving lift exists.
-/
def ExactContinuationWithin
    {K : CurrentK}
    (repairSearch : RepairSearchClass.{uRepairCandidate} K)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K) : Prop :=
  BoundedExactContinuation
    (RepairableWithin repairSearch d)
    (AvailableLiftWithin liftSearch d)

/--
The existing generic notion of bounded representational collapse, specialized
to the declared same-K repair and lift classes.
-/
def BoundedRepresentationalCollapseWithin
    {K : CurrentK}
    (repairSearch : RepairSearchClass.{uRepairCandidate} K)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K) : Prop :=
  BoundedRepresentationalCollapse
    (RepairableWithin repairSearch d)
    (AvailableLiftWithin liftSearch d)

theorem boundedRepresentationalCollapseWithin_iff_no_exactContinuation
    {K : CurrentK}
    (repairSearch : RepairSearchClass.{uRepairCandidate} K)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K) :
    BoundedRepresentationalCollapseWithin repairSearch liftSearch d ↔
      Not (ExactContinuationWithin repairSearch liftSearch d) := by
  rfl

theorem not_exactContinuationWithin_iff_no_repair_and_no_lift
    {K : CurrentK}
    (repairSearch : RepairSearchClass.{uRepairCandidate} K)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K) :
    Not (ExactContinuationWithin repairSearch liftSearch d) ↔
      Not (RepairableWithin repairSearch d) ∧
        Not (AvailableLiftWithin liftSearch d) := by
  constructor
  · intro noContinuation
    constructor
    · intro repair
      exact noContinuation (Or.inl repair)
    · intro lift
      exact noContinuation (Or.inr lift)
  · intro noRoutes continuation
    cases continuation with
    | inl repair => exact noRoutes.1 repair
    | inr lift => exact noRoutes.2 lift

/--
The three mutually meaningful scoped outcomes:

1. a same-K repair exists;
2. an exact natural-rank-minimal strict successor exists; or
3. neither repair nor lift supplies exact continuation in the frozen classes.

The second branch contains an actual certificate, not merely an available
candidate or an untyped dimension label.
-/
def ScopedExactContinuationTrichotomy
    {K : CurrentK}
    (repairSearch : RepairSearchClass.{uRepairCandidate} K)
    (d : TrajectoryDistinction K)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (rank : TransitionRank liftSearch) : Prop :=
  RepairableWithin repairSearch d ∨
    (Exists fun argmin : NatRankedMSpaceArgmin liftSearch d rank =>
      Nonempty
        (ExactStrictSuccessorCertificate K
          (liftSearch.lift argmin.minimizer.1))) ∨
    BoundedRepresentationalCollapseWithin repairSearch liftSearch d

/--
Formal first-principle theorem for one frozen representational scope.

Premises:

* the receiver distinction is an active demand;
* current K does not express it;
* same-K repairs and lifts are explicitly typed search classes;
* lift burden is a natural-number rank; and
* every candidate satisfying the declared lift constraints has exact declared
  receiver-effect and dynamic semantics.

Conclusion: repair, exact ranked strict refinement, or scoped failure of exact
continuation.  The proof uses classical route selection; it is not an
executable completeness test for an infinite candidate class.
-/
theorem scoped_first_principle_exact_continuation_trichotomy
    {K : CurrentK}
    (repairSearch : RepairSearchClass.{uRepairCandidate} K)
    (activeDemand : ActiveDemand K)
    (d : TrajectoryDistinction K)
    (demandIsActive : activeDemand d)
    (notExpressed : Not (Expresses K d))
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (rank : TransitionRank liftSearch)
    (exactOfConstraints :
      forall candidate,
        liftSearch.constraints candidate ->
          HasExactDeclaredSemantics
            (liftSearch.lift candidate).toCurrentK) :
    ScopedExactContinuationTrichotomy
      repairSearch d liftSearch rank := by
  classical
  by_cases repairable : RepairableWithin repairSearch d
  · exact Or.inl repairable
  · right
    by_cases available : AvailableLiftWithin liftSearch d
    · left
      let pressure :
          IrreduciblePressureWithin repairSearch activeDemand d :=
        irreduciblePressureWithin_intro
          repairSearch activeDemand d demandIsActive notExpressed repairable
      obtain ⟨argmin⟩ :=
        natRanked_mSpace_argmin_exists liftSearch d rank available
      obtain ⟨strictSuccessor⟩ :=
        strictSuccessorCertificate_of_pressure_natRankedArgmin
          pressure liftSearch argmin
      refine ⟨argmin, ?_⟩
      exact
        ⟨{
          strictSuccessor := strictSuccessor
          exactSemantics :=
            exactOfConstraints
              argmin.minimizer.1
              argmin.minimizer.2.1
        }⟩
    · right
      exact
        no_repair_and_no_lift_force_bounded_representational_collapse
          repairable available

/--
The exact-successor branch inherits both strict kernel refinement and stable
causal-trajectory projections from its certificate.
-/
theorem first_principle_refinement_branch_properties
    {K : CurrentK}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {d : TrajectoryDistinction K}
    {rank : TransitionRank liftSearch}
    (argmin : NatRankedMSpaceArgmin liftSearch d rank)
    (certificate :
      ExactStrictSuccessorCertificate K
        (liftSearch.lift argmin.minimizer.1)) :
    EncoderKernelStrictlyRefines
        (liftSearch.lift argmin.minimizer.1).encode K.encode ∧
      (currentKTrajectoryProjectionFamily
        (liftSearch.lift argmin.minimizer.1).toCurrentK).DynamicsCommute
        (liftSearch.lift argmin.minimizer.1).toCurrentK.stateTransition
        shiftCausalTrajectory := by
  exact
    ⟨certificate.kernel_strictly_refines_current,
      certificate.trajectory_projections_are_shift_stable⟩

end OCMinimalObligationSpine
