import OCKIndividuationMSpaceComposition.FiniteAliasChallengeRisk
import OCKIndividuationMSpaceComposition.OC14SemanticKernel
import OCKIndividuationMSpaceComposition.NestedPredictiveInformationRisk

namespace OCKIndividuationMSpaceComposition

/-!
# Blackwell and Bayes correspondence for finite OC alias challenges

This module identifies the mature decision-theoretic core of M8/M9 exactly.
A deterministic OC observation refinement induces a Blackwell garbling between
the corresponding degenerate probability channels.  A two-world collision
challenge is a binary decision problem with exact deterministic Bayes risk
`1/2`; an origin-time observation which separates the same worlds has risk
zero.  Consequently the exact information value on this declared challenge is
`1/2`.

These are correspondence theorems, not novelty claims.  Their purpose is to
make the operational interpretation of the finite collision law precise.
-/

universe uWorld uCoarse uFine uOutcome

/-- A channel `coarse` is a Blackwell garbling of `fine` when a Markov kernel
post-processes every fine observation law into the coarse law. -/
def PMFBlackwellGarbling
    {World : Type uWorld} {Fine : Type uFine} {Coarse : Type uCoarse}
    (fine : StochasticObservationChannel World Fine)
    (coarse : StochasticObservationChannel World Coarse) : Prop :=
  ∃ garble : Fine → PMF Coarse,
    ∀ world, (fine.observe world).bind garble = coarse.observe world

/-- Every finite or infinite deterministic OC refinement is exactly a
degenerate Blackwell garbling: forget the extra coordinate after observing it.
-/
theorem observation_refinement_is_deterministic_blackwell_garbling
    {World : Type uWorld} {Coarse : Type uCoarse} {Fine : Type uFine}
    (coarse : World → Coarse) (fine : World → Fine)
    (refines : ObservationRefines coarse fine) :
    PMFBlackwellGarbling
      (deterministicObservationChannel fine)
      (deterministicObservationChannel coarse) := by
  rcases refines with ⟨forget, recovers⟩
  refine ⟨fun information => PMF.pure (forget information), ?_⟩
  intro world
  simp [deterministicObservationChannel, recovers]

/-- Equal-weight zero-one risk for the explicit two-world decision problem. -/
noncomputable def twoWorldChallengeRisk
    {World : Type uWorld} {Observation : Type*} {Outcome : Type uOutcome}
    [DecidableEq Outcome]
    (observe : World → Observation) (target : World → Outcome)
    (first second : World) (predict : Observation → Outcome) : ℝ :=
  ((FiniteZeroOneError (predict (observe first)) (target first) : ℝ) +
    (FiniteZeroOneError (predict (observe second)) (target second) : ℝ)) / 2

/-- An aliased pair with different targets imposes risk at least `1/2` on every
deterministic observation-only decision rule. -/
theorem aliased_two_world_challenge_risk_ge_half
    {World : Type uWorld} {Observation : Type*} {Outcome : Type uOutcome}
    [DecidableEq Outcome]
    (observe : World → Observation) (target : World → Outcome)
    (first second : World)
    (aliases : observe first = observe second)
    (different : target first ≠ target second)
    (predict : Observation → Outcome) :
    (1 : ℝ) / 2 ≤
      twoWorldChallengeRisk observe target first second predict := by
  let pair : ObservationCollisionPair observe target :=
    ⟨(first, second), by
      refine ⟨?_, aliases, different⟩
      intro same
      exact different (congrArg target same)⟩
  have lower := collision_pair_endpoint_error_count_ge_one
    observe target predict pair
  unfold twoWorldChallengeRisk
  have lowerReal :
      (1 : ℝ) ≤
        (FiniteZeroOneError (predict (observe first)) (target first) : ℝ) +
          (FiniteZeroOneError (predict (observe second)) (target second) : ℝ) := by
    exact_mod_cast lower
  linarith

/-- The lower bound is sharp for every declared aliased pair: predicting the
first target on the shared observation makes exactly one endpoint wrong. -/
theorem aliased_two_world_challenge_half_is_attainable
    {World : Type uWorld} {Observation : Type*} {Outcome : Type uOutcome}
    [DecidableEq Observation] [DecidableEq Outcome] [Inhabited Outcome]
    (observe : World → Observation) (target : World → Outcome)
    (first second : World)
    (aliases : observe first = observe second)
    (different : target first ≠ target second) :
    ∃ predict : Observation → Outcome,
      twoWorldChallengeRisk observe target first second predict = (1 : ℝ) / 2 := by
  let predict : Observation → Outcome := fun observation =>
    if observation = observe first then target first else default
  refine ⟨predict, ?_⟩
  have secondAliasesFirst : observe second = observe first := aliases.symm
  simp [twoWorldChallengeRisk, FiniteZeroOneError, predict,
    secondAliasesFirst, different]

/-- Exact Bayes statement: the aliased two-world challenge has an attained
optimal deterministic risk of `1/2` over the unrestricted predictor class. -/
theorem aliased_two_world_challenge_exact_bayes_risk
    {World : Type uWorld} {Observation : Type*} {Outcome : Type uOutcome}
    [DecidableEq Observation] [DecidableEq Outcome] [Inhabited Outcome]
    (observe : World → Observation) (target : World → Outcome)
    (first second : World)
    (aliases : observe first = observe second)
    (different : target first ≠ target second) :
    ∃ witness : OptimalRiskWitness
        (twoWorldChallengeRisk observe target first second)
        (Set.univ : Set (Observation → Outcome)),
      witness.value = (1 : ℝ) / 2 := by
  rcases aliased_two_world_challenge_half_is_attainable
    observe target first second aliases different with ⟨predict, attains⟩
  let witness : OptimalRiskWitness
      (twoWorldChallengeRisk observe target first second)
      (Set.univ : Set (Observation → Outcome)) :=
    { predictor := predict
      predictor_admissible := Set.mem_univ predict
      optimal := by
        intro candidate _candidateAdmissible
        rw [attains]
        exact aliased_two_world_challenge_risk_ge_half
          observe target first second aliases different candidate }
  exact ⟨witness, attains⟩

/-- A genuinely separating origin observation supports zero risk on the same
two-world challenge. -/
theorem separated_two_world_challenge_zero_is_attainable
    {World : Type uWorld} {Observation : Type*} {Outcome : Type uOutcome}
    [DecidableEq Observation] [DecidableEq Outcome]
    (observe : World → Observation) (target : World → Outcome)
    (first second : World)
    (separates : observe first ≠ observe second) :
    ∃ predict : Observation → Outcome,
      twoWorldChallengeRisk observe target first second predict = 0 := by
  rcases separated_origin_information_supports_two_world_exact_prediction
    observe target first second separates with ⟨predict, firstCorrect, secondCorrect⟩
  refine ⟨predict, ?_⟩
  simp [twoWorldChallengeRisk, FiniteZeroOneError, firstCorrect, secondCorrect]

/-- **Exact finite value-of-information theorem.** On a task-relevant raw
alias pair, any admitted origin observation which separates the pair reduces
the attained deterministic Bayes risk from `1/2` to `0`, hence has exact gross
value `1/2` for this declared challenge. -/
theorem separated_origin_information_has_exact_half_challenge_value
    {World : Type uWorld} {Raw : Type uCoarse} {Information : Type uFine}
    {Outcome : Type uOutcome}
    [DecidableEq Raw] [DecidableEq Information] [DecidableEq Outcome]
    [Inhabited Outcome]
    (raw : World → Raw) (information : World → Information)
    (target : World → Outcome) (first second : World)
    (rawAliases : raw first = raw second)
    (informationSeparates : information first ≠ information second)
    (different : target first ≠ target second) :
    ∃ rawWitness : OptimalRiskWitness
        (twoWorldChallengeRisk raw target first second)
        (Set.univ : Set (Raw → Outcome)),
      ∃ informationPredict : Information → Outcome,
        rawWitness.value = (1 : ℝ) / 2 ∧
        twoWorldChallengeRisk information target first second informationPredict = 0 ∧
        rawWitness.value -
          twoWorldChallengeRisk information target first second informationPredict =
            (1 : ℝ) / 2 := by
  rcases aliased_two_world_challenge_exact_bayes_risk
    raw target first second rawAliases different with ⟨rawWitness, rawHalf⟩
  rcases separated_two_world_challenge_zero_is_attainable
    information target first second informationSeparates with
    ⟨informationPredict, informationZero⟩
  refine ⟨rawWitness, informationPredict, rawHalf, informationZero, ?_⟩
  rw [rawHalf, informationZero]
  norm_num

end OCKIndividuationMSpaceComposition
