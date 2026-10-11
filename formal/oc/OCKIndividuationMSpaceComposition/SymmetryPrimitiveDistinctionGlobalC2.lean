import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionC2Boundary
import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionCommutation
import Mathlib.Data.Fintype.Card
import Mathlib.Tactic

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# Exact global C₂ boundary for a primitive distinction

The primitive pair always derives a local two-point axis and its C₂
automorphism algebra.  This file closes the remaining finite global boundary:
the ambient carrier has the same two-point algebra exactly when the displayed
pair covers it.  No global action is introduced by definition; the finite
cardinality criterion and the classification of arbitrary ambient permutations
are proved from coverage and endpoint separation.
-/

/-! ## Coverage is exactly the finite two-point condition -/

noncomputable def carrierAxisEquiv
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier) :
    Carrier ≃ distinction.Axis := by
  classical
  let toAxis : Carrier → distinction.Axis := fun point =>
    ⟨point, by
      rcases covers point with first | second
      · exact Or.inl first
      · exact Or.inr second⟩
  exact Equiv.ofBijective toAxis
    ⟨by
      intro first second equality
      exact congrArg Subtype.val equality,
      by
        intro point
        refine ⟨point.1, ?_⟩
        apply Subtype.ext
        rfl⟩

theorem coversCarrier_iff_card_eq_two
    {Carrier : Type uCarrier} [Fintype Carrier]
    (distinction : PrimitiveDistinction Carrier) :
    distinction.CoversCarrier ↔ Fintype.card Carrier = 2 := by
  constructor
  · intro covers
    calc
      Fintype.card Carrier = Fintype.card distinction.Axis :=
        Fintype.card_congr (carrierAxisEquiv distinction covers)
      _ = 2 := distinction.axis_card_eq_two
  · intro cardEq point
    classical
    let pair : Finset Carrier :=
      insert distinction.first (singleton distinction.second)
    have pairSubset :
        pair ⊆
          (Finset.univ : Finset Carrier) := by
      simp [pair]
    have pairCard :
        pair.card = 2 := by
      simp [pair, distinction.separated]
    have univCard : (Finset.univ : Finset Carrier).card = 2 := by
      simpa using cardEq
    have pairEqUniv :
        pair = Finset.univ :=
      Finset.eq_of_subset_of_card_le pairSubset (by
        simpa [pairCard, univCard])
    have pointMember : point ∈
        pair := by
      rw [pairEqUniv]
      exact Finset.mem_univ point
    simpa [pair] using pointMember

/-! ## Every ambient permutation is one of the two C₂ elements -/

theorem carrierAutomorphism_eq_identity_or_pairSwap
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier)
    (transform : Equiv.Perm Carrier) :
    transform = Equiv.refl Carrier ∨
      transform = pairSwapEquiv distinction := by
  rcases covers (transform distinction.first) with mapsFirst | mapsSecond
  · left
    apply Equiv.ext
    intro point
    rcases covers point with pointFirst | pointSecond
    · subst point
      simpa using mapsFirst
    · subst point
      have mapsSecond' : transform distinction.second = distinction.second := by
        rcases covers (transform distinction.second) with imageFirst | imageSecond
        · exfalso
          have equalImages :
              transform distinction.second = transform distinction.first :=
            imageFirst.trans mapsFirst.symm
          have equalPoints : distinction.second = distinction.first :=
            transform.injective equalImages
          exact distinction.separated equalPoints.symm
        · exact imageSecond
      simpa using mapsSecond'
  · right
    apply Equiv.ext
    intro point
    rcases covers point with pointFirst | pointSecond
    · subst point
      change transform distinction.first = distinction.pairSwap distinction.first
      rw [distinction.pairSwap_first]
      exact mapsSecond
    · subst point
      have mapsSecond' : transform distinction.second = distinction.first := by
        rcases covers (transform distinction.second) with imageFirst | imageSecond
        · exact imageFirst
        · exfalso
          have equalImages :
              transform distinction.second = transform distinction.first :=
            imageSecond.trans mapsSecond.symm
          have equalPoints : distinction.second = distinction.first :=
            transform.injective equalImages
          exact distinction.separated equalPoints.symm
      change transform distinction.second = distinction.pairSwap distinction.second
      rw [distinction.pairSwap_second]
      exact mapsSecond'

/-! ## A derived global parity coordinate -/

noncomputable def carrierAutomorphismParity
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (transform : Equiv.Perm Carrier) : Bool :=
  by
    classical
    exact if transform distinction.first = distinction.first then false else true

@[simp] theorem carrierAutomorphismParity_identity
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    carrierAutomorphismParity distinction (Equiv.refl Carrier) = false := by
  simp [carrierAutomorphismParity]

@[simp] theorem carrierAutomorphismParity_pairSwap
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    carrierAutomorphismParity distinction (pairSwapEquiv distinction) = true := by
  classical
  unfold carrierAutomorphismParity
  change (if distinction.pairSwap distinction.first = distinction.first
    then false else true) = true
  rw [distinction.pairSwap_first]
  simp [Ne.symm distinction.separated]

noncomputable def carrierAutomorphismEquivBool
    {Carrier : Type uCarrier} [Fintype Carrier]
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier) :
    Equiv.Perm Carrier ≃ Bool where
  toFun := carrierAutomorphismParity distinction
  invFun := fun parity =>
    if parity then pairSwapEquiv distinction else Equiv.refl Carrier
  left_inv := by
    intro transform
    rcases distinction.carrierAutomorphism_eq_identity_or_pairSwap covers transform with
      identity | swap
    · subst transform
      rw [carrierAutomorphismParity_identity distinction]
      rfl
    · subst transform
      rw [carrierAutomorphismParity_pairSwap distinction]
      rfl
  right_inv := by
    intro parity
    cases parity
    · simpa using carrierAutomorphismParity_identity distinction
    · simpa using carrierAutomorphismParity_pairSwap distinction

theorem global_c2_spine
    {Carrier : Type uCarrier} [Fintype Carrier]
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier) :
    Fintype.card Carrier = 2 ∧
      (∀ point : Carrier,
        distinction.pairSwap (distinction.pairSwap point) = point) ∧
      (∀ point : Carrier,
        distinction.pairSwap point ≠ point) ∧
      Nonempty (Equiv.Perm Carrier ≃ Bool) := by
  exact ⟨(distinction.coversCarrier_iff_card_eq_two).mp covers,
    distinction.pairSwap_involutive,
    (distinction.pairSwap_fixedPointFree_iff_coversCarrier).mpr covers,
    ⟨distinction.carrierAutomorphismEquivBool covers⟩⟩

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
