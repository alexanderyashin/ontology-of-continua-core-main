import OCKIndividuationMSpaceComposition.FiniteObservationLearning
import OCKIndividuationMSpaceComposition.ContextRiskDecomposition

namespace OCKIndividuationMSpaceComposition

universe uWorld uObservation uAction uVocabulary uContext uOperation uEvidence

/-!
# Task-conditioned optics: finite OC kernel

This is the first bounded bridge for the adaptive-optics programme.  It does
not assert a universal ontology or a universal granularity law.  An optic is a
typed observation/representation contract; a task supplies the target and
loss; and an oracle risk certificate supplies the explicit decision-theoretic
premise needed for a refinement theorem.
-/

structure TaskConditionedOptic (World : Type uWorld) where
  Observation : Type uObservation
  Vocabulary : Type uVocabulary
  Context : Type uContext
  Operation : Type uOperation
  Evidence : Type uEvidence
  observe : World → Observation
  represent : Observation → Vocabulary
  context : World → Context
  horizon : Nat
  admissibleOperation : Operation → Prop
  provenance : Evidence

structure OpticRefinement
    {World : Type uWorld} (coarse fine : TaskConditionedOptic World) where
  coarsen : fine.Observation → coarse.Observation
  commutes : ∀ world,
    coarse.observe world = coarsen (fine.observe world)

structure TaskContract {World : Type uWorld} (optic : TaskConditionedOptic World) where
  Action : Type uAction
  target : World → Action
  loss : Action → Action → ℝ
  horizon : Nat
  interpretation : Prop

/- A risk function is intentionally supplied by the domain adapter.  This
  keeps Brier, MAE, log loss and control loss as task losses, not OC
  primitives. -/
structure OracleDecisionCertificate
    {Observation Action : Type*}
    (risk : (Observation → Action) → ℝ) where
  rule : Observation → Action
  value : ℝ
  value_eq : value = risk rule
  optimal : ∀ decision, value ≤ risk decision

/-- A refinement cannot worsen oracle risk when the fine decision class can
simulate every coarse decision and both risk functions agree under that
simulation.  The theorem is deliberately certificate-based: it does not
smuggle in a distribution, a learner or a causal interpretation. -/
theorem oracle_risk_monotone_of_optic_refinement
    {World : Type uWorld} {coarse fine : TaskConditionedOptic World}
    (refinement : OpticRefinement coarse fine)
    {Action : Type*}
    (coarseRisk : (coarse.Observation → Action) → ℝ)
    (fineRisk : (fine.Observation → Action) → ℝ)
    (coarseOracle : OracleDecisionCertificate coarseRisk)
    (fineOracle : OracleDecisionCertificate fineRisk)
    (simulation : ∀ decision,
      fineRisk (decision ∘ refinement.coarsen) = coarseRisk decision) :
    fineOracle.value ≤ coarseOracle.value := by
  calc
    fineOracle.value ≤ fineRisk (coarseOracle.rule ∘ refinement.coarsen) :=
      fineOracle.optimal (coarseOracle.rule ∘ refinement.coarsen)
    _ = coarseRisk coarseOracle.rule := simulation coarseOracle.rule
    _ = coarseOracle.value := coarseOracle.value_eq.symm

/-- The target signature is the coarsest exact task-sufficient quotient in the
finite kernel: every exact observation factors through equality of target
signatures.  This is the OC naming/adapter surface for the existing
observation-sufficiency theorem, not a new claim about causal state. -/
theorem task_signature_is_coarsest_sufficient
    {World Outcome Observation : Type*}
    (target : World → Outcome)
    (observe : World → Observation)
    (sufficient : ∀ left right,
      observe left = observe right → target left = target right) :
    (∀ left right, target left = target right → target left = target right) ∧
      IsObservationRefinement target observe := by
  constructor
  · exact target_signature_is_observation_sufficient target
  · exact every_sufficient_observation_refines_target_signature
      observe target sufficient

/-! A concrete finite-sample countermodel: the oracle fine optic is strictly
better, while a learned finite-sample refinement is strictly worse.  The two
triples are intentionally separate so the theorem cannot be misread as a
contradiction to oracle monotonicity. -/
theorem finite_sample_refinement_nonmonotone_countermodel :
    ∃ (truthOracle coarseOracle fineOracle truthLearned coarseLearned fineLearned : ℝ),
      SquaredPredictionRisk truthOracle fineOracle <
        SquaredPredictionRisk truthOracle coarseOracle ∧
      SquaredPredictionRisk truthLearned coarseLearned <
        SquaredPredictionRisk truthLearned fineLearned ∧
      ContextSignalEnergy coarseLearned fineLearned > 0 ∧
      inner ℝ (truthLearned - fineLearned)
          (fineLearned - coarseLearned) <
        -(ContextSignalEnergy coarseLearned fineLearned / 2) := by
  refine ⟨0, 1, 0, 0, 0, 1, ?_⟩
  norm_num [SquaredPredictionRisk, ContextSignalEnergy]

end OCKIndividuationMSpaceComposition
