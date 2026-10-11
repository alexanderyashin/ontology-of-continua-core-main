import OCKIndividuationMSpaceComposition.SymmetryPrimitiveRestrictedNaturality

namespace OCKIndividuationMSpaceComposition

universe uCarrier

/-!
# The exact admissible class for a primitive pair swap

M45 supplied a sufficient restricted-naturality premise: a relabelling may
fix or exchange the two distinguished endpoints.  This layer makes the
premise algebraic and proves that it is exact.  The admissible relabellings
contain the identity, are closed under equivalence composition and inverse,
and are precisely the relabellings that commute with the canonical pair
transposition.  No pairing or ordering of the complement is selected.
-/

namespace PrimitiveDistinction

variable {Carrier : Type uCarrier}

/-- The explicit class of relabellings that preserve the unordered support of
a primitive distinction. -/
def pairSupportPreservingClass
    (distinction : PrimitiveDistinction Carrier) : Set (Carrier ≃ Carrier) :=
  {relabel | PreservesPairSupport distinction relabel}

/-- The identity relabelling preserves the distinguished support. -/
theorem preservesPairSupport_refl
    (distinction : PrimitiveDistinction Carrier) :
    PreservesPairSupport distinction (Equiv.refl Carrier) := by
  exact Or.inl ⟨rfl, rfl⟩

/-- The support-preserving class is closed under equivalence composition. -/
theorem preservesPairSupport_trans
    (distinction : PrimitiveDistinction Carrier)
    (left right : Carrier ≃ Carrier)
    (left_preserves : PreservesPairSupport distinction left)
    (right_preserves : PreservesPairSupport distinction right) :
    PreservesPairSupport distinction (left.trans right) := by
  rcases left_preserves with left_fixed | left_swapped
  · rcases right_preserves with right_fixed | right_swapped
    · exact Or.inl ⟨by simp [Equiv.trans_apply, left_fixed.1, right_fixed.1],
        by simp [Equiv.trans_apply, left_fixed.2, right_fixed.2]⟩
    · exact Or.inr ⟨by simp [Equiv.trans_apply, left_fixed.1, right_swapped.1],
        by simp [Equiv.trans_apply, left_fixed.2, right_swapped.2]⟩
  · rcases right_preserves with right_fixed | right_swapped
    · exact Or.inr ⟨by simp [Equiv.trans_apply, left_swapped.1, right_fixed.2],
        by simp [Equiv.trans_apply, left_swapped.2, right_fixed.1]⟩
    · exact Or.inl ⟨by simp [Equiv.trans_apply, left_swapped.1, right_swapped.2],
        by simp [Equiv.trans_apply, left_swapped.2, right_swapped.1]⟩

/-- The support-preserving class is closed under inverse relabelling. -/
theorem preservesPairSupport_symm
    (distinction : PrimitiveDistinction Carrier)
    (relabel : Carrier ≃ Carrier)
    (preserves : PreservesPairSupport distinction relabel) :
    PreservesPairSupport distinction relabel.symm := by
  rcases preserves with fixed | swapped
  · exact Or.inl ⟨by
      calc
        relabel.symm distinction.first =
            relabel.symm (relabel distinction.first) := by rw [fixed.1]
        _ = distinction.first := relabel.symm_apply_apply _,
      by
      calc
        relabel.symm distinction.second =
            relabel.symm (relabel distinction.second) := by rw [fixed.2]
        _ = distinction.second := relabel.symm_apply_apply _⟩
  · exact Or.inr ⟨by
      calc
        relabel.symm distinction.first =
            relabel.symm (relabel distinction.second) := by rw [swapped.2]
        _ = distinction.second := relabel.symm_apply_apply _,
      by
      calc
        relabel.symm distinction.second =
            relabel.symm (relabel distinction.first) := by rw [swapped.1]
        _ = distinction.first := relabel.symm_apply_apply _⟩

/-- The canonical transposition commutes with a relabelling exactly when the
relabelling preserves the unordered support of the primitive pair. -/
theorem preservesPairSupport_iff_pairSwap_commutes
    (distinction : PrimitiveDistinction Carrier)
    (relabel : Carrier ≃ Carrier) :
    PreservesPairSupport distinction relabel ↔
      Function.Commute distinction.pairSwap relabel := by
  constructor
  · exact distinction.pairSwap_commutes_of_preservesPairSupport relabel
  · intro commute
    have commuteAtFirst := commute distinction.first
    by_cases firstImage : relabel distinction.first = distinction.first
    · have secondImage : relabel distinction.second = distinction.second := by
        have h := commuteAtFirst
        simp only [firstImage, distinction.pairSwap_first] at h
        exact h.symm
      exact Or.inl ⟨firstImage, secondImage⟩
    · by_cases firstImageSecond : relabel distinction.first = distinction.second
      · have secondImage : relabel distinction.second = distinction.first := by
          have h := commuteAtFirst
          simp only [firstImageSecond, distinction.pairSwap_second,
            distinction.pairSwap_first] at h
          exact h.symm
        exact Or.inr ⟨firstImageSecond, secondImage⟩
      · have outside := distinction.pairSwap_outside (relabel distinction.first)
          firstImage firstImageSecond
        have equalImages : relabel distinction.first = relabel distinction.second := by
          have h := commuteAtFirst
          simp only [outside, distinction.pairSwap_first] at h
          exact h
        exact False.elim (distinction.separated (relabel.injective equalImages))

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
