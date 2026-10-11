import OCKIndividuationMSpaceComposition.ConstraintGeneratedObject

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe
  uMechanism uIntervention uOutcome
  uOccurrence uExperiment uExperimentOutcome uView uTarget uTime

/-!
# Strongest relative universalization

This module states the strongest domain-neutral consequences of the enriched
constraint-generated model.  Every positive result remains relative to a typed
causal, boundary, provenance, scale and experiment contract.  The final
theorems record strict limits on any absolute strengthening.
-/

/--
Universal property of the generated carrier: membership is equivalent to
membership in every dependency-closed carrier containing the root.
-/
theorem generatedKernel_universal_iff
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {root mechanism : Mechanism} :
    GeneratedKernel model root mechanism ↔
      ∀ carrier : Mechanism → Prop,
        carrier root →
        DependencyClosed model carrier →
        carrier mechanism := by
  constructor
  · intro generated carrier containsRoot closed
    exact generatedKernel_is_least_closed containsRoot closed generated
  · intro universal
    exact universal (GeneratedKernel model root)
      (generatedKernel_contains_root model root)
      (generatedKernel_is_dependencyClosed model root)

/-- Every admissible identity lies between the forced and allowed bounds. -/
theorem admissibleIdentityRelation_bounds
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    {evidence : BinaryRelation Occurrence}
    {law : Occurrence → Experiment → ExperimentOutcome}
    {relation : BinaryRelation Occurrence}
    (candidate : AdmissibleIdentityRelation evidence law relation) :
    RelationRefines (ForcedIdentity evidence) relation ∧
      RelationRefines relation (AllowedIdentity law) := by
  constructor
  · intro left right forced
    exact EquivalenceGenerated.minimal
      candidate.containsEvidence candidate.reflexive candidate.symmetric
        candidate.transitive forced
  · exact candidate.experimentSound

/-- An admissible identity exists exactly when the interval is consistent. -/
theorem admissibleIdentity_exists_iff
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    (evidence : BinaryRelation Occurrence)
    (law : Occurrence → Experiment → ExperimentOutcome) :
    (∃ relation, AdmissibleIdentityRelation evidence law relation) ↔
      RelationRefines (ForcedIdentity evidence) (AllowedIdentity law) := by
  constructor
  · rintro ⟨relation, candidate⟩
    have bounds := admissibleIdentityRelation_bounds candidate
    intro left right forced
    exact bounds.2 (bounds.1 forced)
  · intro safe
    exact ⟨ForcedIdentity evidence,
      forcedIdentityCandidate evidence law safe⟩

/-- Converged bounds imply existence and uniqueness of operational identity. -/
theorem converged_identity_bounds_exist_unique
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    (evidence : BinaryRelation Occurrence)
    (law : Occurrence → Experiment → ExperimentOutcome)
    (convergence : ForcedIdentity evidence = AllowedIdentity law) :
    ∃! relation, AdmissibleIdentityRelation evidence law relation := by
  refine ⟨ForcedIdentity evidence, ?_, ?_⟩
  · exact forcedIdentityCandidate evidence law (by
      intro left right forced
      rw [← convergence]
      exact forced)
  · intro relation candidate
    exact converged_identity_bounds_force_unique_relation
      convergence candidate

/-- Unique admissible identity forces the two interval endpoints to meet. -/
theorem unique_admissible_identity_implies_converged_bounds
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    (evidence : BinaryRelation Occurrence)
    (law : Occurrence → Experiment → ExperimentOutcome)
    (unique : ∃! relation,
      AdmissibleIdentityRelation evidence law relation) :
    ForcedIdentity evidence = AllowedIdentity law := by
  rcases unique with ⟨relation, candidate, uniqueness⟩
  have bounds := admissibleIdentityRelation_bounds candidate
  have safe :
      RelationRefines (ForcedIdentity evidence) (AllowedIdentity law) := by
    intro left right forced
    exact bounds.2 (bounds.1 forced)
  have forcedCandidate :=
    forcedIdentityCandidate evidence law safe
  have allowedCandidate :=
    allowedIdentityCandidate evidence law safe
  have forcedEq : ForcedIdentity evidence = relation :=
    uniqueness (ForcedIdentity evidence) forcedCandidate
  have allowedEq : AllowedIdentity law = relation :=
    uniqueness (AllowedIdentity law) allowedCandidate
  exact forcedEq.trans allowedEq.symm

/-- Exact classification of uniqueness in the bare identity interval. -/
theorem admissibleIdentity_unique_iff
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    (evidence : BinaryRelation Occurrence)
    (law : Occurrence → Experiment → ExperimentOutcome) :
    (∃! relation, AdmissibleIdentityRelation evidence law relation) ↔
      ForcedIdentity evidence = AllowedIdentity law := by
  constructor
  · exact unique_admissible_identity_implies_converged_bounds evidence law
  · exact converged_identity_bounds_exist_unique evidence law

/-!
## Quotient representation and descent
-/

/-- The quotient lift is the unique function agreeing with `f` on tokens. -/
theorem operationalToken_lift_unique
    {Occurrence : Type uOccurrence}
    {Target : Type uTarget}
    {evidence : BinaryRelation Occurrence}
    (f : Occurrence → Target)
    (respectsEvidence : ∀ ⦃left right⦄,
      evidence left right → f left = f right) :
    ∃! lifted : OperationalToken evidence → Target,
      ∀ occurrence,
        lifted (operationalTokenOf evidence occurrence) = f occurrence := by
  have respectsForced : ∀ ⦃left right⦄,
      ForcedIdentity evidence left right → f left = f right := by
    intro left right forced
    exact EquivalenceGenerated.minimal
      (target := fun source target => f source = f target)
      (by
        intro source target edge
        exact respectsEvidence edge)
      (by intro occurrence; rfl)
      (by
        intro first second equal
        exact equal.symm)
      (by
        intro first second third firstSecond secondThird
        exact firstSecond.trans secondThird)
      forced
  let lifted : OperationalToken evidence → Target :=
    Quotient.lift f (by
      intro left right related
      exact respectsForced related)
  apply ExistsUnique.intro lifted
  · intro occurrence
    rfl
  · intro other commutes
    funext token
    obtain ⟨occurrence, rfl⟩ := Quotient.exists_rep token
    simpa [lifted, operationalTokenOf] using commutes occurrence

/-- A map descends through a surjective projection exactly when it preserves fibers. -/
theorem projection_descent_iff
    {Occurrence : Type uOccurrence}
    {View : Type uView}
    (projection : Occurrence → View)
    (surjective : Function.Surjective projection)
    (transform : Occurrence → Occurrence) :
    (∃ induced : View → View,
      ∀ occurrence,
        induced (projection occurrence) = projection (transform occurrence)) ↔
      ∀ ⦃left right⦄,
        projection left = projection right →
          projection (transform left) = projection (transform right) := by
  constructor
  · rintro ⟨induced, commutes⟩ left right sameView
    rw [← commutes left, ← commutes right, sameView]
  · intro preserves
    let choosePreimage : View → Occurrence :=
      fun view => Classical.choose (surjective view)
    refine ⟨fun view => projection (transform (choosePreimage view)), ?_⟩
    intro occurrence
    apply preserves
    exact Classical.choose_spec (surjective (projection occurrence))

/-- The induced map through a surjective projection is unique. -/
theorem projection_descent_unique
    {Occurrence : Type uOccurrence}
    {View : Type uView}
    (projection : Occurrence → View)
    (surjective : Function.Surjective projection)
    (transform : Occurrence → Occurrence)
    {first second : View → View}
    (firstCommutes : ∀ occurrence,
      first (projection occurrence) = projection (transform occurrence))
    (secondCommutes : ∀ occurrence,
      second (projection occurrence) = projection (transform occurrence)) :
    first = second := by
  funext view
  rcases surjective view with ⟨occurrence, rfl⟩
  exact (firstCommutes occurrence).trans (secondCommutes occurrence).symm

/-!
## Strict no-go results
-/

/-- A collision in a projection rules out exact recovery by a left inverse. -/
theorem projection_collision_no_leftInverse
    {Occurrence : Type uOccurrence}
    {View : Type uView}
    {projection : Occurrence → View}
    {left right : Occurrence}
    (different : left ≠ right)
    (collision : projection left = projection right) :
    ¬ ∃ recover : View → Occurrence,
      Function.LeftInverse recover projection := by
  rintro ⟨recover, leftInverse⟩
  apply different
  rw [← leftInverse left, ← leftInverse right, collision]

/-- Classical equivalence identity collapses two alleged fission children. -/
theorem equivalence_collapses_fission
    {Occurrence : Type uOccurrence}
    {identity : BinaryRelation Occurrence}
    (symmetric : Symmetric identity)
    (transitive : Transitive identity)
    {parent firstChild secondChild : Occurrence}
    (firstContinuation : identity parent firstChild)
    (secondContinuation : identity parent secondChild) :
    identity firstChild secondChild :=
  transitive (symmetric firstContinuation) secondContinuation

/-- Hence distinct children cannot both retain one classical identity token. -/
theorem distinct_fission_children_not_both_identical
    {Occurrence : Type uOccurrence}
    {identity : BinaryRelation Occurrence}
    (symmetric : Symmetric identity)
    (transitive : Transitive identity)
    {parent firstChild secondChild : Occurrence}
    (childrenSeparated : ¬ identity firstChild secondChild) :
    ¬ (identity parent firstChild ∧ identity parent secondChild) := by
  rintro ⟨firstContinuation, secondContinuation⟩
  exact childrenSeparated
    (equivalence_collapses_fission symmetric transitive
      firstContinuation secondContinuation)

/--
An evidence-invariant successor selector must choose a fixed point of every
evidence-preserving symmetry that fixes the parent.
-/
theorem invariant_selector_is_fixed
    {Occurrence : Type uOccurrence}
    (successor : Occurrence → Occurrence)
    (symmetry : Occurrence → Occurrence)
    (equivariant : ∀ occurrence,
      successor (symmetry occurrence) = symmetry (successor occurrence))
    {parent : Occurrence}
    (fixesParent : symmetry parent = parent) :
    symmetry (successor parent) = successor parent := by
  rw [← equivariant parent, fixesParent]

/-- A fixed-point-free branch symmetry forbids an invariant successor choice. -/
theorem no_invariant_selector_without_fixed_successor
    {Occurrence : Type uOccurrence}
    (candidate : Occurrence → Prop)
    (symmetry : Occurrence → Occurrence)
    {parent : Occurrence}
    (fixesParent : symmetry parent = parent)
    (noCandidateFixed : ∀ occurrence,
      candidate occurrence → symmetry occurrence ≠ occurrence) :
    ¬ ∃ successor : Occurrence → Occurrence,
      candidate (successor parent) ∧
      ∀ occurrence,
        successor (symmetry occurrence) = symmetry (successor occurrence) := by
  rintro ⟨successor, isCandidate, equivariant⟩
  exact noCandidateFixed (successor parent) isCandidate
    (invariant_selector_is_fixed successor symmetry equivariant fixesParent)

/-- A fixed-point-free Boolean symmetry cannot have a unique invariant selector. -/
theorem no_unique_bool_selector_invariant_under_swap
    (selected : Bool → Prop)
    (invariant : ∀ value, selected value ↔ selected (!value)) :
    ¬ ∃! value, selected value := by
  rintro ⟨chosen, chosenSelected, unique⟩
  have swappedSelected : selected (!chosen) :=
    (invariant chosen).mp chosenSelected
  have impossible : (!chosen) = chosen :=
    unique (!chosen) swappedSelected
  cases chosen <;> simp at impossible

/-!
## A bare finite carrier cannot select a nontrivial invariant scale
-/

inductive BareThree
  | first
  | second
  | third
  deriving DecidableEq

def swapFirstSecond : BareThree → BareThree
  | .first => .second
  | .second => .first
  | .third => .third

theorem swapFirstSecond_involution :
    Function.Involutive swapFirstSecond := by
  intro value
  cases value <;> rfl

theorem no_swap_invariant_root :
    ¬ ∃ root : BareThree, swapFirstSecond root = root ∧ root ≠ .third := by
  rintro ⟨root, fixed, notThird⟩
  cases root <;> simp [swapFirstSecond] at fixed notThird

end OCKIndividuationMSpaceComposition
