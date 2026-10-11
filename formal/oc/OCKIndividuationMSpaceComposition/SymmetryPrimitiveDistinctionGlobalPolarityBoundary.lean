import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionC2Boundary

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# The exact ambient boundary for a Boolean polarity

The generated two-point axis carries a base-relative Boolean polarity.  It is
tempting to extend that polarity to the whole carrier while requiring the
canonical ambient pair-swap to negate it everywhere.  This module isolates
the precise missing premise: such an ambient Boolean anti-invariant exists
exactly when the distinguished pair covers the carrier.

The result is an observable-level boundary, not a definition of a global
polarity.  On a carrier with an extra fixed point, Boolean negation at that
point is impossible.  Under exact coverage, the displayed first endpoint
supplies a concrete polarity and the endpoint cases prove anti-invariance.
No global action, intrinsic dimension, or canonical orientation is inferred.
-/

def PairSwapBoolAntiInvariant
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (polarity : Carrier → Bool) : Prop :=
  ∀ point,
    polarity (distinction.pairSwap point) = Bool.not (polarity point)

noncomputable def pairSwapPolarity
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) : Carrier → Bool := by
  classical
  exact fun point => if point = distinction.first then false else true

theorem pairSwapPolarity_antiInvariant_of_covers
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier) :
    PairSwapBoolAntiInvariant distinction
      (pairSwapPolarity distinction) := by
  intro point
  rcases covers point with first | second
  · subst point
    rw [distinction.pairSwap_first]
    simp [pairSwapPolarity, Ne.symm distinction.separated]
  · subst point
    rw [distinction.pairSwap_second]
    simp [pairSwapPolarity, Ne.symm distinction.separated]

theorem covers_of_pairSwapBoolAntiInvariant
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    {polarity : Carrier → Bool}
    (antiInvariant : PairSwapBoolAntiInvariant distinction polarity) :
    distinction.CoversCarrier := by
  intro point
  by_contra outside
  have notFirst : point ≠ distinction.first := by
    intro equal
    exact outside (Or.inl equal)
  have notSecond : point ≠ distinction.second := by
    intro equal
    exact outside (Or.inr equal)
  have fixed : distinction.pairSwap point = point :=
    distinction.pairSwap_outside point notFirst notSecond
  have impossible : polarity point = Bool.not (polarity point) := by
    calc
      polarity point = polarity (distinction.pairSwap point) :=
        congrArg polarity fixed.symm
      _ = Bool.not (polarity point) := antiInvariant point
  cases value : polarity point <;> simp [value] at impossible

theorem exists_pairSwapBoolAntiInvariant_iff_coversCarrier
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    (∃ polarity : Carrier → Bool,
      PairSwapBoolAntiInvariant distinction polarity) ↔
      distinction.CoversCarrier := by
  constructor
  · rintro ⟨polarity, antiInvariant⟩
    exact covers_of_pairSwapBoolAntiInvariant distinction antiInvariant
  · intro covers
    exact ⟨pairSwapPolarity distinction,
      pairSwapPolarity_antiInvariant_of_covers distinction covers⟩

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
