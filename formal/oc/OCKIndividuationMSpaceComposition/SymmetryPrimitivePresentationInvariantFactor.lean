import OCKIndividuationMSpaceComposition.SymmetryPrimitivePresentationOrientationQuotient

namespace OCKIndividuationMSpaceComposition

universe uCarrier uObservable

namespace PrimitiveDistinction

/-!
# The invariant layer of the primitive-presentation quotient

The preceding file derives the unordered-support quotient and the free
two-element orientation fibre.  This file proves its universal property at
the level of observables: reversal invariance is exactly the condition for an
observable on ordered presentations to descend to unordered support.  Thus
the quotient is not merely a convenient data structure; it is the maximal
information that survives loss of orientation.

Conversely, a single reversal-sensitive value is a formal obstruction to any
factor through the quotient.  No canonical orientation is selected and no
global carrier action is introduced.
-/

def PresentationReversalInvariant
    {Carrier : Type uCarrier} {Observable : Type uObservable}
    (observable : PrimitiveDistinction Carrier → Observable) : Prop :=
  ∀ presentation,
    observable presentation.reverseLabels = observable presentation

theorem presentationInvariant_on_sameUnorderedSupport
    {Carrier : Type uCarrier} {Observable : Type uObservable}
    (observable : PrimitiveDistinction Carrier → Observable)
    (invariant : PresentationReversalInvariant observable)
    {first second : PrimitiveDistinction Carrier}
    (same : SameUnorderedSupport first second) :
    observable first = observable second := by
  rcases (sameUnorderedSupport_iff_eq_or_reverse first second).1 same with
    equal | reversed
  · exact equal ▸ rfl
  · subst second
    exact (invariant first).symm

def presentationInvariantFactor
    {Carrier : Type uCarrier} {Observable : Type uObservable}
    (observable : PrimitiveDistinction Carrier → Observable)
    (invariant : PresentationReversalInvariant observable) :
    UnorderedDistinction Carrier → Observable :=
  Quotient.lift observable (by
    intro first second same
    exact presentationInvariant_on_sameUnorderedSupport
      observable invariant same)

@[simp] theorem presentationInvariantFactor_spec
    {Carrier : Type uCarrier} {Observable : Type uObservable}
    (observable : PrimitiveDistinction Carrier → Observable)
    (invariant : PresentationReversalInvariant observable)
    (presentation : PrimitiveDistinction Carrier) :
    presentationInvariantFactor observable invariant
      (unorderedClass presentation) = observable presentation :=
  rfl

theorem presentationInvariant_factors_through_unorderedClass
    {Carrier : Type uCarrier} {Observable : Type uObservable}
    (observable : PrimitiveDistinction Carrier → Observable)
    (invariant : PresentationReversalInvariant observable) :
    ∃ factor : UnorderedDistinction Carrier → Observable,
      ∀ presentation,
        factor (unorderedClass presentation) = observable presentation :=
  ⟨presentationInvariantFactor observable invariant,
    presentationInvariantFactor_spec observable invariant⟩

theorem presentationInvariant_iff_unorderedClass_factor
    {Carrier : Type uCarrier} {Observable : Type uObservable}
    (observable : PrimitiveDistinction Carrier → Observable) :
    PresentationReversalInvariant observable ↔
      ∃ factor : UnorderedDistinction Carrier → Observable,
        ∀ presentation,
          factor (unorderedClass presentation) = observable presentation := by
  constructor
  · intro invariant
    exact presentationInvariant_factors_through_unorderedClass
      observable invariant
  · rintro ⟨factor, specification⟩ presentation
    calc
      observable presentation.reverseLabels =
          factor (unorderedClass presentation.reverseLabels) :=
        (specification presentation.reverseLabels).symm
      _ = factor (unorderedClass presentation) :=
        congrArg factor (reverseLabels_preserves_unorderedClass presentation)
      _ = observable presentation := specification presentation

theorem unorderedClass_factor_unique
    {Carrier : Type uCarrier} {Observable : Type uObservable}
    (observable : PrimitiveDistinction Carrier → Observable)
    {factor₁ factor₂ : UnorderedDistinction Carrier → Observable}
    (spec₁ : ∀ presentation,
      factor₁ (unorderedClass presentation) = observable presentation)
    (spec₂ : ∀ presentation,
      factor₂ (unorderedClass presentation) = observable presentation) :
    factor₁ = factor₂ := by
  funext quotientClass
  refine Quotient.inductionOn quotientClass ?_
  intro presentation
  calc
    factor₁ (unorderedClass presentation) = observable presentation :=
      spec₁ presentation
    _ = factor₂ (unorderedClass presentation) := (spec₂ presentation).symm

def PresentationSymmetryBreakingWitness
    {Carrier : Type uCarrier} {Observable : Type uObservable}
    (observable : PrimitiveDistinction Carrier → Observable)
    (presentation : PrimitiveDistinction Carrier) : Prop :=
  observable presentation.reverseLabels ≠ observable presentation

theorem presentation_symmetry_breaking_forbids_unorderedClass_factor
    {Carrier : Type uCarrier} {Observable : Type uObservable}
    (observable : PrimitiveDistinction Carrier → Observable)
    (presentation : PrimitiveDistinction Carrier)
    (breaking : PresentationSymmetryBreakingWitness observable presentation) :
    ¬ ∃ factor : UnorderedDistinction Carrier → Observable,
        ∀ candidate,
          factor (unorderedClass candidate) = observable candidate := by
  rintro ⟨factor, specification⟩
  apply breaking
  calc
    observable presentation.reverseLabels =
        factor (unorderedClass presentation.reverseLabels) :=
      (specification presentation.reverseLabels).symm
    _ = factor (unorderedClass presentation) :=
      congrArg factor (reverseLabels_preserves_unorderedClass presentation)
    _ = observable presentation := specification presentation

theorem reverseLabels_ne_self
    {Carrier : Type uCarrier}
    (presentation : PrimitiveDistinction Carrier) :
    presentation.reverseLabels ≠ presentation := by
  intro equality
  apply presentation.separated
  exact (congrArg PrimitiveDistinction.first equality).symm

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
