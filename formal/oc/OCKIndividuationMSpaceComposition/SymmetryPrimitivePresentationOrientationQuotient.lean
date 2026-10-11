import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionCommutation
import OCKIndividuationMSpaceComposition.SymmetryOrientationPresentationInvolution

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# The orientation quotient of a primitive distinction

An ordered pair is a presentation of an unordered distinction.  This file
turns that sentence into a quotient and proves the exact two-element fibre:
two presentations have the same support precisely when one is the other or
its endpoint reversal.  The resulting free involution lives on the space of
presentations of one unordered pair; it is not silently promoted to an action
on an arbitrary ambient carrier.

No C₂ action, torsor, coordinate, topology or dimension is assumed here.  The
only input is endpoint separation and the previously defined endpoint swap.
-/

/-! ## Unordered-support equivalence -/

theorem sameUnorderedSupport_refl
    {Carrier : Type uCarrier} (presentation : PrimitiveDistinction Carrier) :
    SameUnorderedSupport presentation presentation := by
  exact Or.inl ⟨rfl, rfl⟩

theorem sameUnorderedSupport_symm
    {Carrier : Type uCarrier}
    {left right : PrimitiveDistinction Carrier}
    (same : SameUnorderedSupport left right) :
    SameUnorderedSupport right left := by
  rcases same with ⟨firstEq, secondEq⟩ | ⟨firstEq, secondEq⟩
  · exact Or.inl ⟨firstEq.symm, secondEq.symm⟩
  · exact Or.inr ⟨secondEq.symm, firstEq.symm⟩

theorem sameUnorderedSupport_trans
    {Carrier : Type uCarrier}
    {first second third : PrimitiveDistinction Carrier}
    (firstSecond : SameUnorderedSupport first second)
    (secondThird : SameUnorderedSupport second third) :
    SameUnorderedSupport first third := by
  rcases firstSecond with ⟨firstFirst, secondSecond⟩ |
    ⟨firstSecond, secondFirst⟩
  · rcases secondThird with ⟨secondFirstThird, secondSecondThird⟩ |
      ⟨secondSecondThird, secondFirstThird⟩
    · exact Or.inl ⟨firstFirst.trans secondFirstThird,
        secondSecond.trans secondSecondThird⟩
    · exact Or.inr ⟨firstFirst.trans secondSecondThird,
        secondSecond.trans secondFirstThird⟩
  · rcases secondThird with ⟨secondFirstThird, secondSecondThird⟩ |
      ⟨secondSecondThird, secondFirstThird⟩
    · exact Or.inr ⟨firstSecond.trans secondSecondThird,
        secondFirst.trans secondFirstThird⟩
    · exact Or.inl ⟨firstSecond.trans secondFirstThird,
        secondFirst.trans secondSecondThird⟩

def primitiveDistinctionSetoid (Carrier : Type uCarrier) :
    Setoid (PrimitiveDistinction Carrier) where
  r := SameUnorderedSupport
  iseqv := {
    refl := sameUnorderedSupport_refl
    symm := sameUnorderedSupport_symm
    trans := sameUnorderedSupport_trans }

def UnorderedDistinction (Carrier : Type uCarrier) :=
  Quotient (primitiveDistinctionSetoid Carrier)

def unorderedClass {Carrier : Type uCarrier}
    (presentation : PrimitiveDistinction Carrier) :
    UnorderedDistinction Carrier :=
  Quotient.mk (primitiveDistinctionSetoid Carrier) presentation

theorem unorderedClass_eq_iff_sameUnorderedSupport
    {Carrier : Type uCarrier}
    (left right : PrimitiveDistinction Carrier) :
    unorderedClass left = unorderedClass right ↔
      SameUnorderedSupport left right := by
  constructor
  · intro equality
    exact Quotient.exact (s := primitiveDistinctionSetoid Carrier) equality
  · intro same
    exact Quotient.sound (s := primitiveDistinctionSetoid Carrier) same

/-! ## Exact classification of an orientation fibre -/

theorem sameUnorderedSupport_iff_eq_or_reverse
    {Carrier : Type uCarrier}
    (first second : PrimitiveDistinction Carrier) :
    SameUnorderedSupport first second ↔
      second = first ∨ second = first.reverseLabels := by
  constructor
  · intro same
    rcases same with ⟨firstEq, secondEq⟩ | ⟨firstEq, secondEq⟩
    · apply Or.inl
      cases first with
      | mk leftFirst leftSecond leftSeparated =>
        cases second with
        | mk rightFirst rightSecond rightSeparated =>
          simp_all
    · apply Or.inr
      cases first with
      | mk leftFirst leftSecond leftSeparated =>
        cases second with
        | mk rightFirst rightSecond rightSeparated =>
          simp_all [reverseLabels]
  · intro alternatives
    rcases alternatives with same | reversed
    · cases same
      exact sameUnorderedSupport_refl _
    · cases reversed
      exact Or.inr ⟨rfl, rfl⟩

theorem reverseLabels_sameUnorderedSupport
    {Carrier : Type uCarrier}
    (presentation : PrimitiveDistinction Carrier) :
    SameUnorderedSupport presentation.reverseLabels presentation := by
  exact Or.inr ⟨rfl, rfl⟩

theorem reverseLabels_preserves_unorderedClass
    {Carrier : Type uCarrier}
    (presentation : PrimitiveDistinction Carrier) :
    unorderedClass presentation.reverseLabels = unorderedClass presentation :=
  (unorderedClass_eq_iff_sameUnorderedSupport _ _).2
    (reverseLabels_sameUnorderedSupport presentation)

/-! ## The two-element orientation fibre -/

def OrientationFiber {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier) :=
  {presentation : PrimitiveDistinction Carrier //
    SameUnorderedSupport presentation base}

def orientationBase {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier) : OrientationFiber base :=
  ⟨base, sameUnorderedSupport_refl base⟩

def orientationPartner {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier) : OrientationFiber base :=
  ⟨base.reverseLabels, reverseLabels_sameUnorderedSupport base⟩

theorem orientationBase_ne_partner
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier) :
    orientationBase base ≠ orientationPartner base := by
  intro equality
  apply base.separated
  have endpointEquality := congrArg
    (fun presentation : OrientationFiber base => presentation.1.first) equality
  exact endpointEquality

theorem orientationFiber_eq_base_or_partner
    {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier) (presentation : OrientationFiber base) :
    presentation = orientationBase base ∨
      presentation = orientationPartner base := by
  rcases (sameUnorderedSupport_iff_eq_or_reverse presentation.1 base).1
    presentation.2 with same | reversed
  · apply Or.inl
    apply Subtype.ext
    exact same.symm
  · apply Or.inr
    apply Subtype.ext
    have reversedApplied := congrArg
      (fun p : PrimitiveDistinction Carrier => p.reverseLabels) reversed
    simpa using reversedApplied.symm

def orientationReverse {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier) :
    OrientationFiber base → OrientationFiber base :=
  fun presentation =>
    ⟨presentation.1.reverseLabels, by
      rcases presentation.2 with same | same
      · exact Or.inr ⟨same.2, same.1⟩
      · exact Or.inl ⟨same.2, same.1⟩⟩

@[simp] theorem orientationReverse_base
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier) :
    orientationReverse base (orientationBase base) = orientationPartner base := by
  apply Subtype.ext
  rfl

@[simp] theorem orientationReverse_partner
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier) :
    orientationReverse base (orientationPartner base) = orientationBase base := by
  apply Subtype.ext
  simpa using reverseLabels_involutive base

theorem orientationReverse_involutive
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier)
    (presentation : OrientationFiber base) :
    orientationReverse base (orientationReverse base presentation) = presentation := by
  rcases orientationFiber_eq_base_or_partner base presentation with rfl | rfl
  · simp
  · simp

theorem orientationReverse_fixedPointFree
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier)
    (presentation : OrientationFiber base) :
    orientationReverse base presentation ≠ presentation := by
  rcases orientationFiber_eq_base_or_partner base presentation with rfl | rfl
  · simpa using (orientationBase_ne_partner base).symm
  · simpa using orientationBase_ne_partner base

noncomputable def orientationFiberInvolution
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier) :
    FixedPointFreeInvolution (OrientationFiber base) where
  action := {
    toFun := orientationReverse base
    invFun := orientationReverse base
    left_inv := orientationReverse_involutive base
    right_inv := orientationReverse_involutive base }
  involutive := orientationReverse_involutive base
  fixedPointFree := orientationReverse_fixedPointFree base

theorem orientationFiber_pairTransitive
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier)
    (left right : OrientationFiber base) :
    right = left ∨ right = orientationReverse base left := by
  rcases orientationFiber_eq_base_or_partner base left with rfl | rfl
  · rcases orientationFiber_eq_base_or_partner base right with rfl | rfl
    · exact Or.inl rfl
    · exact Or.inr rfl
  · rcases orientationFiber_eq_base_or_partner base right with rfl | rfl
    · exact Or.inr (by simp)
    · exact Or.inl rfl

noncomputable def orientationFiberTorsor
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier) :
    R3C2OrientationTorsorInterface (OrientationFiber base) Unit Unit where
  reverse := orientationReverse base
  reverseInvolutive := orientationReverse_involutive base
  reverseFree := orientationReverse_fixedPointFree base
  pairTransitive := orientationFiber_pairTransitive base
  axisOf := fun _ => ()
  identityOf := fun _ => ()

noncomputable def orientationFiberEquivFin2
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier) :
    OrientationFiber base ≃ Fin 2 := by
  classical
  let equivalence : OrientationFiber base ≃ Fin 2 :=
    { toFun := fun presentation =>
        if presentation = orientationBase base then 0 else 1
      invFun := fun index => if index = 0 then orientationBase base else
        orientationPartner base
      left_inv := by
        intro presentation
        rcases orientationFiber_eq_base_or_partner base presentation with rfl | rfl
        · simp
        · have partnerNeBase : orientationPartner base ≠ orientationBase base :=
            (orientationBase_ne_partner base).symm
          simp [partnerNeBase]
      right_inv := by
        intro index
        fin_cases index
        · simp
        · have partnerNeBase : orientationPartner base ≠ orientationBase base :=
            (orientationBase_ne_partner base).symm
          simp [partnerNeBase] }
  exact equivalence

noncomputable instance orientationFiberFintype
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier) :
    Fintype (OrientationFiber base) :=
  Fintype.ofEquiv (Fin 2) (orientationFiberEquivFin2 base).symm

theorem orientationFiber_has_exact_two_elements
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier) :
    Fintype.card (OrientationFiber base) = 2 := by
  exact Fintype.card_congr (orientationFiberEquivFin2 base)

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
