import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionCommutation

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# Exact commutation boundary for primitive pair reversals

For two primitive distinctions there are only two ways for their canonical
transpositions to commute: their endpoint supports are disjoint, or the two
transpositions are the same unordered pair.  The second case is compatibility
without a new direction.  Therefore a commuting family can be faithful only
after equal unordered supports have been quotiented out; for pairwise distinct
reversals, disjointness is not merely sufficient but necessary.

This is a boundary theorem, not a stronger global OC claim.  It does not say
that every family of distinctions is commuting, nor that every ambient point
is covered by a family.
-/

private theorem not_commute_shared_first_first
    {Carrier : Type uCarrier}
    (left right : PrimitiveDistinction Carrier)
    (firstEqual : left.first = right.first)
    (secondNe : left.second ≠ right.second) :
    ¬ Function.Commute left.pairSwap right.pairSwap := by
  intro commute
  have rightAtLeftFirst : right.pairSwap left.first = right.second := by
    rw [firstEqual]
    exact right.pairSwap_first
  have leftFixRightSecond : left.pairSwap right.second = right.second :=
    left.pairSwap_outside right.second
      (by
        intro equality
        apply right.separated
        exact firstEqual.symm.trans equality.symm)
      secondNe.symm
  have rightFixLeftSecond : right.pairSwap left.second = left.second :=
    right.pairSwap_outside left.second
      (by
        intro equality
        apply left.separated
        exact firstEqual.trans equality.symm)
      secondNe
  have atFirst := commute left.first
  rw [rightAtLeftFirst, leftFixRightSecond,
    left.pairSwap_first, rightFixLeftSecond] at atFirst
  exact secondNe.symm atFirst

private theorem not_commute_shared_first_second
    {Carrier : Type uCarrier}
    (left right : PrimitiveDistinction Carrier)
    (firstEqual : left.first = right.second)
    (secondNe : left.second ≠ right.first) :
    ¬ Function.Commute left.pairSwap right.pairSwap := by
  intro commute
  have rightAtLeftFirst : right.pairSwap left.first = right.first := by
    rw [firstEqual]
    exact right.pairSwap_second
  have leftFixRightFirst : left.pairSwap right.first = right.first :=
    left.pairSwap_outside right.first
      (by
        intro equality
        apply right.separated
        exact equality.trans firstEqual)
      (by
        exact secondNe.symm)
  have rightFixLeftSecond : right.pairSwap left.second = left.second :=
    right.pairSwap_outside left.second
      secondNe (by
        intro equality
        apply left.separated
        exact firstEqual.trans equality.symm)
  have atFirst := commute left.first
  rw [rightAtLeftFirst, leftFixRightFirst,
    left.pairSwap_first, rightFixLeftSecond] at atFirst
  exact secondNe.symm atFirst

private theorem not_commute_shared_second_first
    {Carrier : Type uCarrier}
    (left right : PrimitiveDistinction Carrier)
    (secondEqual : left.second = right.first)
    (firstNe : left.first ≠ right.second) :
    ¬ Function.Commute left.pairSwap right.pairSwap := by
  intro commute
  have rightAtLeftSecond : right.pairSwap left.second = right.second := by
    rw [secondEqual]
    exact right.pairSwap_first
  have leftFixRightSecond : left.pairSwap right.second = right.second :=
    left.pairSwap_outside right.second
      (by
        exact firstNe.symm)
      (by
        intro equality
        apply right.separated
        exact secondEqual.symm.trans equality.symm)
  have rightFixLeftFirst : right.pairSwap left.first = left.first :=
    right.pairSwap_outside left.first
      (by
        intro equality
        apply left.separated
        exact equality.trans secondEqual.symm)
      firstNe
  have atSecond := commute left.second
  rw [rightAtLeftSecond, leftFixRightSecond,
    left.pairSwap_second, rightFixLeftFirst] at atSecond
  exact firstNe.symm atSecond

private theorem not_commute_shared_second_second
    {Carrier : Type uCarrier}
    (left right : PrimitiveDistinction Carrier)
    (secondEqual : left.second = right.second)
    (firstNe : left.first ≠ right.first) :
    ¬ Function.Commute left.pairSwap right.pairSwap := by
  intro commute
  have rightAtLeftSecond : right.pairSwap left.second = right.first := by
    rw [secondEqual]
    exact right.pairSwap_second
  have leftFixRightFirst : left.pairSwap right.first = right.first :=
    left.pairSwap_outside right.first
      (by
        exact firstNe.symm)
      (by
        intro equality
        apply right.separated
        exact equality.trans secondEqual)
  have rightFixLeftFirst : right.pairSwap left.first = left.first :=
    right.pairSwap_outside left.first
      firstNe (by
        intro equality
        apply left.separated
        exact equality.trans secondEqual.symm)
  have atSecond := commute left.second
  rw [rightAtLeftSecond, leftFixRightFirst,
    left.pairSwap_second, rightFixLeftFirst] at atSecond
  exact firstNe.symm atSecond

/-- Commuting primitive pair swaps have disjoint supports or are the same
unordered pair.  The latter alternative is precisely the duplicate-direction
case and does not provide a faithful new coordinate. -/
theorem commute_iff_supportsDisjoint_or_sameUnorderedSupport
    {Carrier : Type uCarrier}
    (left right : PrimitiveDistinction Carrier) :
    Function.Commute left.pairSwap right.pairSwap ↔
      SupportsDisjoint left right ∨ SameUnorderedSupport left right := by
  constructor
  · intro commute
    by_cases firstFirst : left.first = right.first
    · by_cases secondSecond : left.second = right.second
      · exact Or.inr (Or.inl ⟨firstFirst, secondSecond⟩)
      · exact (not_commute_shared_first_first left right firstFirst
          secondSecond commute).elim
    · by_cases firstSecond : left.first = right.second
      · by_cases secondFirst : left.second = right.first
        · exact Or.inr (Or.inr ⟨firstSecond, secondFirst⟩)
        · exact (not_commute_shared_first_second left right firstSecond
            secondFirst commute).elim
      · by_cases secondFirst : left.second = right.first
        · by_cases secondSecond : left.second = right.second
          · exact (right.separated
              (secondFirst.symm.trans secondSecond)).elim
          · exact (not_commute_shared_second_first left right secondFirst
              firstSecond commute).elim
        · by_cases secondSecond : left.second = right.second
          · exact (not_commute_shared_second_second left right secondSecond
              firstFirst commute).elim
          · exact Or.inl ⟨firstFirst, firstSecond, secondFirst, secondSecond⟩
  · intro disjointOrSame
    rcases disjointOrSame with disjoint | same
    · exact pairSwap_commute_of_supportsDisjoint left right disjoint
    · have equal : left.pairSwap = right.pairSwap :=
        pairSwap_eq_of_sameUnorderedSupport left right same
      intro point
      rw [equal]

/-- If two primitive reversals commute and are not equal as transformations,
their endpoint supports must be disjoint.  This is the exact finite boundary
needed before counting faithful independent directions. -/
theorem commute_and_pairSwap_ne_implies_supportsDisjoint
    {Carrier : Type uCarrier}
    (left right : PrimitiveDistinction Carrier)
    (commute : Function.Commute left.pairSwap right.pairSwap)
    (distinct : left.pairSwap ≠ right.pairSwap) :
    SupportsDisjoint left right := by
  rcases (commute_iff_supportsDisjoint_or_sameUnorderedSupport left right).mp
      commute with disjoint | same
  · exact disjoint
  · exact (distinct (pairSwap_eq_of_sameUnorderedSupport left right same)).elim

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
