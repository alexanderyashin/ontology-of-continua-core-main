import OCMinimalObligationSpine.ObservableDemandPressure
import OCMinimalObligationSpine.ObservableTransitionSelection
import OCMinimalObligationSpine.StableProjectionCurrentK

namespace OCMinimalObligationSpine

open UnifiedEntityProjection

universe
  uLiftCarrier uLiftCandidate uRepairCandidate uObservation

/-!
# Scoped exact successor

This module composes the already proved pressure, M-space, ranking, strict
successor, and stable-projection layers.  It closes only a scoped
representational theorem:

* a frozen observable receiver constraint rejects a declared merge;
* the current encoder collides on that distinction;
* every admissible architecture-preserving repair in the declared repair scope
  fails;
* a declared M-space witness exists and candidate rank is observation-bound;
* every candidate admitted by the lift constraints has exact declared
  receiver-effect and deterministic-transition semantics.

The conclusion is an exact, rank-minimal strict successor in that declared
scope.  It is not a physical K-level realization, raw-state reconstruction
theorem, empirical validation, or collapse theorem.
-/

/--
One selected lift is simultaneously a strict representational successor and an
exact realization of its declared receiver-effect and deterministic-transition
semantics.

Exactness is deliberately separate from strictness: resolving one distinction
does not by itself prove that the selected representation is scientifically
adequate for every declared receiver and transition.
-/
structure ExactStrictSuccessorCertificate
    (K : CurrentK)
    (candidate : LiftCandidate.{uLiftCarrier} K) where
  strictSuccessor : StrictSuccessorCertificate K candidate
  exactSemantics : HasExactDeclaredSemantics candidate.toCurrentK

/-- An exact strict successor is a strict edge in the encoder-kernel order. -/
theorem ExactStrictSuccessorCertificate.kernel_strictly_refines_current
    {K : CurrentK}
    {candidate : LiftCandidate.{uLiftCarrier} K}
    (certificate : ExactStrictSuccessorCertificate K candidate) :
    EncoderKernelStrictlyRefines candidate.encode K.encode :=
  certificate.strictSuccessor.kernel_strictly_refines_current

/--
The selected successor's causal-trajectory projections commute with its
declared transition.  This stability follows from the generic CurrentK adapter;
it does not assert joint separation of raw states.
-/
theorem ExactStrictSuccessorCertificate.trajectory_projections_are_shift_stable
    {K : CurrentK}
    {candidate : LiftCandidate.{uLiftCarrier} K}
    (certificate : ExactStrictSuccessorCertificate K candidate) :
    (currentKTrajectoryProjectionFamily candidate.toCurrentK).DynamicsCommute
      candidate.toCurrentK.stateTransition shiftCausalTrajectory := by
  cases certificate
  exact current_k_trajectory_projections_are_shift_stable candidate.toCurrentK

/--
Exact declared semantics makes every collision of the selected encoder a
collision of the complete causal-trajectory projection signature.

This is refinement of the stable projection family, not injectivity of that
family on raw states.
-/
theorem ExactStrictSuccessorCertificate.encoder_refines_stable_projection_family
    {K : CurrentK}
    {candidate : LiftCandidate.{uLiftCarrier} K}
    (certificate : ExactStrictSuccessorCertificate K candidate)
    {left right : K.State}
    (collision : candidate.encode left = candidate.encode right) :
    (currentKTrajectoryProjectionFamily candidate.toCurrentK).signature left =
      (currentKTrajectoryProjectionFamily candidate.toCurrentK).signature
        right := by
  exact exact_current_k_encoder_refines_stable_projection_family
    candidate.toCurrentK certificate.exactSemantics collision

/-- Auditable proposition produced by the general scoped exact-successor route. -/
def ScopedExactRankedSuccessorEvidence
    {K : CurrentK}
    (repairSearch : RepairSearchClass.{uRepairCandidate} K)
    (activeDemand : ActiveDemand K)
    (d : TrajectoryDistinction K)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (rank : TransitionRank liftSearch) : Prop :=
  IrreduciblePressureWithin repairSearch activeDemand d /\
    Exists fun argmin : NatRankedMSpaceArgmin liftSearch d rank =>
      Nonempty
          (ExactStrictSuccessorCertificate K
            (liftSearch.lift argmin.minimizer.1)) /\
        EncoderKernelStrictlyRefines
          (liftSearch.lift argmin.minimizer.1).encode K.encode

/-- Auditable proposition produced by the completely enumerated finite route. -/
def FiniteScopedExactRankedSuccessorEvidence
    {K : CurrentK}
    (repairSearch : RepairSearchClass.{uRepairCandidate} K)
    (activeDemand : ActiveDemand K)
    (d : TrajectoryDistinction K)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (declaredLifts : FiniteDeclaredMSpace liftSearch d)
    (rank : TransitionRank liftSearch) : Prop :=
  IrreduciblePressureWithin repairSearch activeDemand d /\
    Exists fun argmin : FiniteMSpaceArgmin declaredLifts rank =>
      Nonempty
          (ExactStrictSuccessorCertificate K
            (liftSearch.lift argmin.minimizer.1)) /\
        EncoderKernelStrictlyRefines
          (liftSearch.lift argmin.minimizer.1).encode K.encode

/--
Scoped end-to-end theorem for the positive route.

The repair declaration proves exhaustion only inside `repairSearch`; the
M-space witness proves non-emptiness only inside `liftSearch`; and
`exactOfConstraints` is an explicit scientific contract rather than a
consequence of resolving one distinction.
-/
theorem observable_exact_ranked_strict_successor_of_scoped_evidence
    {K : CurrentK}
    (repairSearch : RepairSearchClass.{uRepairCandidate} K)
    (constraint : ObservableReceiverConstraint K.Receiver K.Effect)
    (d : TrajectoryDistinction K)
    (declaredRepairs : FiniteDeclaredRepairSearch repairSearch)
    (constraintFalsified : ReceiverConstraintFalsified constraint d)
    (currentCollision : K.encode d.left = K.encode d.right)
    (everyListedCandidateFails :
      forall candidate,
        candidate ∈ declaredRepairs.candidates ->
          repairSearch.architecturePreserving candidate ->
            repairSearch.admissible candidate ->
              Not (Resolves (repairSearch.repair candidate) d))
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    {Observation : Type uObservation}
    (ranking :
      ObservableTransitionRanking liftSearch.Candidate Observation)
    (witness : ObservableMSpaceWitness liftSearch d ranking)
    (exactOfConstraints :
      forall candidate,
        liftSearch.constraints candidate ->
          HasExactDeclaredSemantics
            (liftSearch.lift candidate).toCurrentK) :
    ScopedExactRankedSuccessorEvidence
      repairSearch (activeDemandFromReceiverConstraint constraint) d
      liftSearch ranking.toTransitionRank := by
  let pressure :
      IrreduciblePressureWithin repairSearch
        (activeDemandFromReceiverConstraint constraint) d :=
    irreduciblePressureWithin_of_finite_observable_replay
      repairSearch constraint d declaredRepairs constraintFalsified
      currentCollision everyListedCandidateFails
  obtain ⟨argmin, ⟨strictSuccessor⟩⟩ :=
    observable_ranked_strict_successor_exists
      pressure liftSearch ranking witness
  let certificate :
      ExactStrictSuccessorCertificate K
        (liftSearch.lift argmin.minimizer.1) :=
    {
      strictSuccessor := strictSuccessor
      exactSemantics :=
        exactOfConstraints argmin.minimizer.1 argmin.minimizer.2.1
    }
  exact
    ⟨pressure, argmin, ⟨certificate⟩,
      certificate.kernel_strictly_refines_current⟩

/--
Finite executable-search corollary.

Both the repair scope and the M-space fiber are explicitly and completely
enumerated.  The conclusion therefore uses `FiniteMSpaceArgmin`; no execution
claim is made for an infinite candidate class.
-/
theorem finite_observable_exact_ranked_strict_successor_of_scoped_replay
    {K : CurrentK}
    (repairSearch : RepairSearchClass.{uRepairCandidate} K)
    (constraint : ObservableReceiverConstraint K.Receiver K.Effect)
    (d : TrajectoryDistinction K)
    (declaredRepairs : FiniteDeclaredRepairSearch repairSearch)
    (constraintFalsified : ReceiverConstraintFalsified constraint d)
    (currentCollision : K.encode d.left = K.encode d.right)
    (everyListedCandidateFails :
      forall candidate,
        candidate ∈ declaredRepairs.candidates ->
          repairSearch.architecturePreserving candidate ->
            repairSearch.admissible candidate ->
              Not (Resolves (repairSearch.repair candidate) d))
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    {Observation : Type uObservation}
    (ranking :
      ObservableTransitionRanking liftSearch.Candidate Observation)
    (declaredLifts : FiniteDeclaredMSpace liftSearch d)
    (witness : ObservableMSpaceWitness liftSearch d ranking)
    (exactOfConstraints :
      forall candidate,
        liftSearch.constraints candidate ->
          HasExactDeclaredSemantics
            (liftSearch.lift candidate).toCurrentK) :
    FiniteScopedExactRankedSuccessorEvidence
      repairSearch (activeDemandFromReceiverConstraint constraint) d
      liftSearch declaredLifts ranking.toTransitionRank := by
  let pressure :
      IrreduciblePressureWithin repairSearch
        (activeDemandFromReceiverConstraint constraint) d :=
    irreduciblePressureWithin_of_finite_observable_replay
      repairSearch constraint d declaredRepairs constraintFalsified
      currentCollision everyListedCandidateFails
  obtain ⟨argmin⟩ :=
    finite_observable_mSpace_argmin_exists_of_witness
      liftSearch d ranking declaredLifts witness
  obtain ⟨strictSuccessor⟩ :=
    strictSuccessorCertificate_of_pressure_finiteArgmin
      pressure liftSearch argmin
  let certificate :
      ExactStrictSuccessorCertificate K
        (liftSearch.lift argmin.minimizer.1) :=
    {
      strictSuccessor := strictSuccessor
      exactSemantics :=
        exactOfConstraints argmin.minimizer.1 argmin.minimizer.2.1
    }
  exact
    ⟨pressure, argmin, ⟨certificate⟩,
      certificate.kernel_strictly_refines_current⟩

/--
Fail-closed routing theorem for one declared lift scope.

The same observable pressure evidence routes either to an exact rank-minimal
strict successor when the M-space fiber is inhabited, or to the scoped fact
that no admissible resolving lift is available.  The negative branch contains
no physical-collapse or universal no-lift wording.  The case split is
classical; it is not an executable completeness test for an infinite lift
class.
-/
theorem scoped_evidence_routes_to_exact_ranked_successor_or_no_available_lift
    {K : CurrentK}
    (repairSearch : RepairSearchClass.{uRepairCandidate} K)
    (constraint : ObservableReceiverConstraint K.Receiver K.Effect)
    (d : TrajectoryDistinction K)
    (declaredRepairs : FiniteDeclaredRepairSearch repairSearch)
    (constraintFalsified : ReceiverConstraintFalsified constraint d)
    (currentCollision : K.encode d.left = K.encode d.right)
    (everyListedCandidateFails :
      forall candidate,
        candidate ∈ declaredRepairs.candidates ->
          repairSearch.architecturePreserving candidate ->
            repairSearch.admissible candidate ->
              Not (Resolves (repairSearch.repair candidate) d))
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    {Observation : Type uObservation}
    (ranking :
      ObservableTransitionRanking liftSearch.Candidate Observation)
    (exactOfConstraints :
      forall candidate,
        liftSearch.constraints candidate ->
          HasExactDeclaredSemantics
            (liftSearch.lift candidate).toCurrentK) :
    ScopedExactRankedSuccessorEvidence
        repairSearch (activeDemandFromReceiverConstraint constraint) d
        liftSearch ranking.toTransitionRank \/
      Not (AvailableLiftWithin liftSearch d) := by
  classical
  let pressure :
      IrreduciblePressureWithin repairSearch
        (activeDemandFromReceiverConstraint constraint) d :=
    irreduciblePressureWithin_of_finite_observable_replay
      repairSearch constraint d declaredRepairs constraintFalsified
      currentCollision everyListedCandidateFails
  by_cases available : AvailableLiftWithin liftSearch d
  · left
    obtain ⟨argmin⟩ :=
      natRanked_mSpace_argmin_exists
        liftSearch d ranking.toTransitionRank available
    obtain ⟨strictSuccessor⟩ :=
      strictSuccessorCertificate_of_pressure_natRankedArgmin
        pressure liftSearch argmin
    let certificate :
        ExactStrictSuccessorCertificate K
          (liftSearch.lift argmin.minimizer.1) :=
      {
        strictSuccessor := strictSuccessor
        exactSemantics :=
          exactOfConstraints argmin.minimizer.1 argmin.minimizer.2.1
      }
    exact
      ⟨pressure, argmin, ⟨certificate⟩,
        certificate.kernel_strictly_refines_current⟩
  · exact Or.inr available

end OCMinimalObligationSpine
