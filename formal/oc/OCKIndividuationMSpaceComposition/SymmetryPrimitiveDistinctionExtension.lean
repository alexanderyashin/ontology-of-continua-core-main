import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinction

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# Extending a primitive distinction beyond its generated axis

The primitive pair already generates a canonical local C₂ axis.  A global free
involution on a larger carrier needs exactly more pairing data on the
complement.  This module proves both directions without treating that data as
implicit.
-/

/-- Points not contained in the generated two-point axis. -/
def Outside {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :=
  { point : Carrier // point ≠ distinction.first ∧ point ≠ distinction.second }

/-- The complement is empty exactly when the primitive pair covers the whole
carrier. -/
theorem outside_not_nonempty_iff_coversCarrier {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    ¬ Nonempty distinction.Outside ↔ distinction.CoversCarrier := by
  constructor
  · intro noOutside point
    by_cases first : point = distinction.first
    · exact Or.inl first
    · by_cases second : point = distinction.second
      · exact Or.inr second
      · exact (noOutside ⟨⟨point, first, second⟩⟩).elim
  · intro covers outside
    rcases outside with ⟨point, notFirst, notSecond⟩
    rcases covers point with first | second
    · exact notFirst first
    · exact notSecond second

/-- Extend the distinguished transposition by an explicitly supplied free
involution on the complement. -/
noncomputable def extendedSwap {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (outsideSymmetry : FixedPointFreeInvolution distinction.Outside)
    (point : Carrier) : Carrier := by
  classical
  exact if first : point = distinction.first then distinction.second
    else if second : point = distinction.second then distinction.first
    else (outsideSymmetry.action ⟨point, first, second⟩).1

@[simp] theorem extendedSwap_first {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (outsideSymmetry : FixedPointFreeInvolution distinction.Outside) :
    distinction.extendedSwap outsideSymmetry distinction.first =
      distinction.second := by
  simp [extendedSwap]

@[simp] theorem extendedSwap_second {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (outsideSymmetry : FixedPointFreeInvolution distinction.Outside) :
    distinction.extendedSwap outsideSymmetry distinction.second =
      distinction.first := by
  simp [extendedSwap, Ne.symm distinction.separated]

theorem extendedSwap_outside {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (outsideSymmetry : FixedPointFreeInvolution distinction.Outside)
    (point : Carrier) (notFirst : point ≠ distinction.first)
    (notSecond : point ≠ distinction.second) :
    distinction.extendedSwap outsideSymmetry point =
      (outsideSymmetry.action ⟨point, notFirst, notSecond⟩).1 := by
  simp [extendedSwap, notFirst, notSecond]

/-- The extended swap is involutive on the whole carrier. -/
theorem extendedSwap_involutive {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (outsideSymmetry : FixedPointFreeInvolution distinction.Outside)
    (point : Carrier) :
    distinction.extendedSwap outsideSymmetry
        (distinction.extendedSwap outsideSymmetry point) = point := by
  classical
  by_cases first : point = distinction.first
  · subst point
    simp
  · by_cases second : point = distinction.second
    · subst point
      simp
    · let outsidePoint : distinction.Outside := ⟨point, first, second⟩
      have imageNotFirst :
          (outsideSymmetry.action outsidePoint).1 ≠ distinction.first :=
        (outsideSymmetry.action outsidePoint).property.1
      have imageNotSecond :
          (outsideSymmetry.action outsidePoint).1 ≠ distinction.second :=
        (outsideSymmetry.action outsidePoint).property.2
      have involutive := congrArg Subtype.val
        (outsideSymmetry.involutive outsidePoint)
      simpa [extendedSwap, first, second, outsidePoint, imageNotFirst,
        imageNotSecond] using involutive

/-- The extended swap is fixed-point-free on the whole carrier. -/
theorem extendedSwap_fixedPointFree {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (outsideSymmetry : FixedPointFreeInvolution distinction.Outside)
    (point : Carrier) :
    distinction.extendedSwap outsideSymmetry point ≠ point := by
  classical
  by_cases first : point = distinction.first
  · subst point
    rw [extendedSwap_first]
    exact Ne.symm distinction.separated
  · by_cases second : point = distinction.second
    · subst point
      rw [extendedSwap_second]
      exact distinction.separated
    · intro fixed
      let outsidePoint : distinction.Outside := ⟨point, first, second⟩
      apply outsideSymmetry.fixedPointFree outsidePoint
      apply Subtype.ext
      simpa [extendedSwap, first, second, outsidePoint] using fixed

/-- Complement pairing is sufficient for a global free involution extending
the primitive swap. -/
noncomputable def extendToFixedPointFreeInvolution {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (outsideSymmetry : FixedPointFreeInvolution distinction.Outside) :
    FixedPointFreeInvolution Carrier where
  action :=
    { toFun := distinction.extendedSwap outsideSymmetry
      invFun := distinction.extendedSwap outsideSymmetry
      left_inv := distinction.extendedSwap_involutive outsideSymmetry
      right_inv := distinction.extendedSwap_involutive outsideSymmetry }
  involutive := distinction.extendedSwap_involutive outsideSymmetry
  fixedPointFree := distinction.extendedSwap_fixedPointFree outsideSymmetry

/-- An involution exchanging the first endpoint necessarily exchanges the
second endpoint back. -/
theorem globalSwap_second {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (symmetry : FixedPointFreeInvolution Carrier)
    (swapsFirst : symmetry.action distinction.first = distinction.second) :
    symmetry.action distinction.second = distinction.first := by
  rw [← swapsFirst]
  exact symmetry.involutive distinction.first

/-- A global involution exchanging the distinguished pair preserves its
complement. -/
theorem globalSwap_preserves_outside {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (symmetry : FixedPointFreeInvolution Carrier)
    (swapsFirst : symmetry.action distinction.first = distinction.second)
    (point : distinction.Outside) :
    symmetry.action point.1 ≠ distinction.first ∧
      symmetry.action point.1 ≠ distinction.second := by
  constructor
  · intro imageFirst
    apply point.property.2
    calc
      point.1 = symmetry.action (symmetry.action point.1) :=
        (symmetry.involutive point.1).symm
      _ = symmetry.action distinction.first := congrArg symmetry.action imageFirst
      _ = distinction.second := swapsFirst
  · intro imageSecond
    apply point.property.1
    calc
      point.1 = symmetry.action (symmetry.action point.1) :=
        (symmetry.involutive point.1).symm
      _ = symmetry.action distinction.second := congrArg symmetry.action imageSecond
      _ = distinction.first := distinction.globalSwap_second symmetry swapsFirst

/-- Complement pairing is also necessary: every global free involution that
exchanges the primitive endpoints restricts to a free involution outside the
generated axis. -/
noncomputable def restrictGlobalToOutside {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (symmetry : FixedPointFreeInvolution Carrier)
    (swapsFirst : symmetry.action distinction.first = distinction.second) :
    FixedPointFreeInvolution distinction.Outside where
  action :=
    { toFun := fun point =>
        ⟨symmetry.action point.1,
          distinction.globalSwap_preserves_outside symmetry swapsFirst point⟩
      invFun := fun point =>
        ⟨symmetry.action point.1,
          distinction.globalSwap_preserves_outside symmetry swapsFirst point⟩
      left_inv := by
        intro point
        apply Subtype.ext
        exact symmetry.involutive point.1
      right_inv := by
        intro point
        apply Subtype.ext
        exact symmetry.involutive point.1 }
  involutive := by
    intro point
    apply Subtype.ext
    exact symmetry.involutive point.1
  fixedPointFree := by
    intro point equality
    exact symmetry.fixedPointFree point.1 (congrArg Subtype.val equality)

/-- Exact extension criterion.  A global fixed-point-free involution which
exchanges the primitive endpoints exists if and only if the complement itself
admits a fixed-point-free involution.  This identifies the minimal additional
structure without hiding it inside a stronger distinction interface. -/
theorem globalFreeExtension_exists_iff_outsidePairing
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier) :
    (∃ symmetry : FixedPointFreeInvolution Carrier,
        symmetry.action distinction.first = distinction.second) ↔
      Nonempty (FixedPointFreeInvolution distinction.Outside) := by
  constructor
  · rintro ⟨symmetry, swapsFirst⟩
    exact ⟨distinction.restrictGlobalToOutside symmetry swapsFirst⟩
  · rintro ⟨outsideSymmetry⟩
    refine ⟨distinction.extendToFixedPointFreeInvolution outsideSymmetry, ?_⟩
    exact distinction.extendedSwap_first outsideSymmetry

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
