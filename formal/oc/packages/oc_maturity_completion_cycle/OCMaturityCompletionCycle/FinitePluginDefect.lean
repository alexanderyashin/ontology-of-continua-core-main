import OCMaturityCompletionCycle.VerifiedDynamicsCapabilities

/-!
# Finite plug-in coupling-heterogeneity defect for empirical testing

The adapter supplies training-only finite conditional PMFs.  The formal target
is a weighted total-variation heterogeneity between a local-signature mixture
and laws additionally indexed by an independently measured coupling
coordinate.  It is not the `qChi` prediction defect, which is defined by the
separate Bernoulli bridge.  No asymptotic consistency or held-out improvement
is asserted here.

For C-MAPSS-like adapters the intended binding is:

* `Group`: engine/unit or prospectively frozen fold group;
* `LocalSignature`: training-only local state/transition signature;
* `Coupling`: independently measured operating-condition/coupling coordinate;
* `NextState × BoundaryOut`: next transition class and frozen outcome channel;
* `trainingCutDigest`: immutable evidence cutoff for every supplied PMF.
-/

namespace OCMaturityCompletionCycle

universe uGroup uSignature uCoupling uNextState uBoundaryOut

/-- Population-level finite conditional-law object targeted by the estimator. -/
structure FinitePopulationTransitionOutputLaw
    (Group : Type uGroup)
    (LocalSignature : Type uSignature)
    (Coupling : Type uCoupling)
    (NextState : Type uNextState)
    (BoundaryOut : Type uBoundaryOut)
    [Fintype Group]
    [Fintype LocalSignature]
    [Fintype Coupling]
    [Fintype NextState]
    [Fintype BoundaryOut] where
  eligible : Group → LocalSignature → Bool
  signatureWeight : Group → FiniteProbabilityMass LocalSignature
  localLaw : Group → LocalSignature →
    FiniteProbabilityMass (NextState × BoundaryOut)
  coupledLaw : Group → LocalSignature → Coupling →
    FiniteProbabilityMass (NextState × BoundaryOut)
  couplingWeight : Group → LocalSignature → FiniteProbabilityMass Coupling
  local_is_coupling_mixture : ∀ group signature outcome,
    (localLaw group signature).mass outcome =
      ∑ coupling,
        (couplingWeight group signature).mass coupling *
          (coupledLaw group signature coupling).mass outcome

/-- Exact finite defect for one independent group. -/
def groupCouplingHeterogeneityDefect
    {Group : Type uGroup}
    {LocalSignature : Type uSignature}
    {Coupling : Type uCoupling}
    {NextState : Type uNextState}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype Group]
    [Fintype LocalSignature]
    [Fintype Coupling]
    [Fintype NextState]
    [Fintype BoundaryOut]
    (target : FinitePopulationTransitionOutputLaw Group LocalSignature Coupling
      NextState BoundaryOut)
    (group : Group) : ℚ :=
  ∑ signature,
    if target.eligible group signature then
      (target.signatureWeight group).mass signature *
        ∑ coupling,
          (target.couplingWeight group signature).mass coupling *
            finiteTotalVariation
              (target.localLaw group signature)
              (target.coupledLaw group signature coupling)
    else 0

theorem groupCouplingHeterogeneityDefect_nonnegative
    {Group : Type uGroup}
    {LocalSignature : Type uSignature}
    {Coupling : Type uCoupling}
    {NextState : Type uNextState}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype Group]
    [Fintype LocalSignature]
    [Fintype Coupling]
    [Fintype NextState]
    [Fintype BoundaryOut]
    (target : FinitePopulationTransitionOutputLaw Group LocalSignature Coupling
      NextState BoundaryOut)
    (group : Group) :
    0 ≤ groupCouplingHeterogeneityDefect target group := by
  apply Finset.sum_nonneg
  intro signature _
  split
  · exact mul_nonneg
      ((target.signatureWeight group).nonnegative signature) (by
        apply Finset.sum_nonneg
        intro coupling _
        exact mul_nonneg
          ((target.couplingWeight group signature).nonnegative coupling)
          (finiteTotalVariation_nonnegative _ _))
  · exact le_rfl

/--
Training-only plug-in estimate.  PMFs and eligibility are computed outside Lean
from the frozen training cut; the counts and digest make the estimator map
auditable without pretending that provenance proves statistical validity.
-/
structure TrainingOnlyTransitionOutputPlugin
    (Group : Type uGroup)
    (LocalSignature : Type uSignature)
    (Coupling : Type uCoupling)
    (NextState : Type uNextState)
    (BoundaryOut : Type uBoundaryOut)
    [Fintype Group]
    [Fintype LocalSignature]
    [Fintype Coupling]
    [Fintype NextState]
    [Fintype BoundaryOut] where
  estimatedTarget : FinitePopulationTransitionOutputLaw Group LocalSignature
    Coupling NextState BoundaryOut
  localSampleCount : Group → LocalSignature → Nat
  coupledSampleCount : Group → LocalSignature → Coupling → Nat
  trainingCutDigest : String
  estimatorVersion : String

/-- Computable training defect exposed to the empirical adapter. -/
def trainingPluginCouplingHeterogeneityDefect
    {Group : Type uGroup}
    {LocalSignature : Type uSignature}
    {Coupling : Type uCoupling}
    {NextState : Type uNextState}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype Group]
    [Fintype LocalSignature]
    [Fintype Coupling]
    [Fintype NextState]
    [Fintype BoundaryOut]
    (estimate : TrainingOnlyTransitionOutputPlugin Group LocalSignature Coupling
      NextState BoundaryOut)
    (group : Group) : ℚ :=
  groupCouplingHeterogeneityDefect estimate.estimatedTarget group

/-- The plug-in constructor evaluates exactly the declared finite target. -/
theorem trainingPluginCouplingHeterogeneityDefect_is_targetEvaluation
    {Group : Type uGroup}
    {LocalSignature : Type uSignature}
    {Coupling : Type uCoupling}
    {NextState : Type uNextState}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype Group]
    [Fintype LocalSignature]
    [Fintype Coupling]
    [Fintype NextState]
    [Fintype BoundaryOut]
    (estimate : TrainingOnlyTransitionOutputPlugin Group LocalSignature Coupling
      NextState BoundaryOut)
    (group : Group) :
    trainingPluginCouplingHeterogeneityDefect estimate group =
      groupCouplingHeterogeneityDefect estimate.estimatedTarget group := rfl

/--
Optional strong target: every strict defect ordering respects held-out risk.
This is stronger than, and must not be identified with, a positive Spearman or
top-versus-bottom preregistered test.
-/
def StrongPairwiseTrainingDefectRanksHeldOutRisk
    {Group : Type uGroup}
    {LocalSignature : Type uSignature}
    {Coupling : Type uCoupling}
    {NextState : Type uNextState}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype Group]
    [Fintype LocalSignature]
    [Fintype Coupling]
    [Fintype NextState]
    [Fintype BoundaryOut]
    (estimate : TrainingOnlyTransitionOutputPlugin Group LocalSignature Coupling
      NextState BoundaryOut)
    (heldOutRisk : Group → ℚ) : Prop :=
  ∀ left right,
    trainingPluginCouplingHeterogeneityDefect estimate left <
        trainingPluginCouplingHeterogeneityDefect estimate right →
      heldOutRisk left ≤ heldOutRisk right

/-- Concrete falsifier for the frozen ranking prediction. -/
def StrongPairwiseTrainingDefectRankingFalsified
    {Group : Type uGroup}
    {LocalSignature : Type uSignature}
    {Coupling : Type uCoupling}
    {NextState : Type uNextState}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype Group]
    [Fintype LocalSignature]
    [Fintype Coupling]
    [Fintype NextState]
    [Fintype BoundaryOut]
    (estimate : TrainingOnlyTransitionOutputPlugin Group LocalSignature Coupling
      NextState BoundaryOut)
    (heldOutRisk : Group → ℚ) : Prop :=
  ∃ left right,
    trainingPluginCouplingHeterogeneityDefect estimate left <
        trainingPluginCouplingHeterogeneityDefect estimate right ∧
      heldOutRisk right < heldOutRisk left

theorem strongPairwiseTrainingDefectRankingFalsified_refutes_prediction
    {Group : Type uGroup}
    {LocalSignature : Type uSignature}
    {Coupling : Type uCoupling}
    {NextState : Type uNextState}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype Group]
    [Fintype LocalSignature]
    [Fintype Coupling]
    [Fintype NextState]
    [Fintype BoundaryOut]
    (estimate : TrainingOnlyTransitionOutputPlugin Group LocalSignature Coupling
      NextState BoundaryOut)
    (heldOutRisk : Group → ℚ)
    (falsified : StrongPairwiseTrainingDefectRankingFalsified estimate heldOutRisk) :
    ¬ StrongPairwiseTrainingDefectRanksHeldOutRisk estimate heldOutRisk := by
  intro prediction
  rcases falsified with ⟨left, right, defectOrder, reverseRisk⟩
  exact (not_le_of_gt reverseRisk) (prediction left right defectOrder)

end OCMaturityCompletionCycle
