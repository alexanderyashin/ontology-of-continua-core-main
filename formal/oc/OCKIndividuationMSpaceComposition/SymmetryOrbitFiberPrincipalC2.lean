import OCKIndividuationMSpaceComposition.SymmetryFreeInvolutionNormalizedDecomposition
import Mathlib.Tactic

namespace OCKIndividuationMSpaceComposition

universe uCarrier

/-!
# Principal C₂ structure on every free-involution orbit fibre

`SymmetryFiniteFreeInvolutionOrbitRank` proves that a finite orbit fibre has
two points.  Here the two points are upgraded to the actual principal action:
the involution restricts to the fibre, its non-trivial Boolean element is free,
and every target point is reached by a unique Boolean element.  This is the
torsor statement needed by the symmetry programme, with no global orientation
choice and no additional C₂ axiom.
-/

namespace FixedPointFreeInvolution

variable {Carrier : Type uCarrier}

/-! ## The involution restricted to a quotient fibre -/

def axisFiberSwap
    (symmetry : FixedPointFreeInvolution Carrier)
    (quotientPoint : AxisQuotient symmetry) :
    AxisFiber symmetry quotientPoint ≃ AxisFiber symmetry quotientPoint where
  toFun := fun point =>
    ⟨symmetry.action point.1, by
      calc
        axisClass symmetry (symmetry.action point.1) =
            axisClass symmetry point.1 :=
          action_preserves_axis_class symmetry point.1
        _ = quotientPoint := point.2⟩
  invFun := fun point =>
    ⟨symmetry.action point.1, by
      calc
        axisClass symmetry (symmetry.action point.1) =
            axisClass symmetry point.1 :=
          action_preserves_axis_class symmetry point.1
        _ = quotientPoint := point.2⟩
  left_inv := by
    intro point
    apply Subtype.ext
    exact symmetry.involutive point.1
  right_inv := by
    intro point
    apply Subtype.ext
    exact symmetry.involutive point.1

theorem axisFiberSwap_involutive
    (symmetry : FixedPointFreeInvolution Carrier)
    (quotientPoint : AxisQuotient symmetry)
    (point : AxisFiber symmetry quotientPoint) :
    axisFiberSwap symmetry quotientPoint
        (axisFiberSwap symmetry quotientPoint point) = point := by
  apply Subtype.ext
  exact symmetry.involutive point.1

theorem axisFiberSwap_fixedPointFree
    (symmetry : FixedPointFreeInvolution Carrier)
    (quotientPoint : AxisQuotient symmetry)
    (point : AxisFiber symmetry quotientPoint) :
    axisFiberSwap symmetry quotientPoint point ≠ point := by
  intro equality
  apply symmetry.fixedPointFree point.1
  exact congrArg Subtype.val equality

/-! ## The explicit Boolean action -/

def axisFiberC2Action
    (symmetry : FixedPointFreeInvolution Carrier)
    (quotientPoint : AxisQuotient symmetry)
    (bit : Bool) (point : AxisFiber symmetry quotientPoint) :
    AxisFiber symmetry quotientPoint :=
  if bit then axisFiberSwap symmetry quotientPoint point else point

theorem axisFiberC2Action_false
    (symmetry : FixedPointFreeInvolution Carrier)
    (quotientPoint : AxisQuotient symmetry)
    (point : AxisFiber symmetry quotientPoint) :
    axisFiberC2Action symmetry quotientPoint false point = point := by
  rfl

theorem axisFiberC2Action_true
    (symmetry : FixedPointFreeInvolution Carrier)
    (quotientPoint : AxisQuotient symmetry)
    (point : AxisFiber symmetry quotientPoint) :
    axisFiberC2Action symmetry quotientPoint true point =
      axisFiberSwap symmetry quotientPoint point := by
  rfl

theorem axisFiberC2Action_xor
    (symmetry : FixedPointFreeInvolution Carrier)
    (quotientPoint : AxisQuotient symmetry)
    (first second : Bool) (point : AxisFiber symmetry quotientPoint) :
    axisFiberC2Action symmetry quotientPoint (first ^^ second) point =
      axisFiberC2Action symmetry quotientPoint first
        (axisFiberC2Action symmetry quotientPoint second point) := by
  cases first <;> cases second <;>
    simp [axisFiberC2Action, axisFiberSwap_involutive]

theorem axisFiberC2Action_transitive
    (symmetry : FixedPointFreeInvolution Carrier)
    (quotientPoint : AxisQuotient symmetry)
    (first second : AxisFiber symmetry quotientPoint) :
    ∃ bit : Bool,
      axisFiberC2Action symmetry quotientPoint bit first = second := by
  have sameClass : sameAxis symmetry first.1 second.1 :=
    (axisClass_eq_iff_sameAxis symmetry first.1 second.1).1
      (first.2.trans second.2.symm)
  rcases sameClass with same | partner
  · refine ⟨false, ?_⟩
    change first = second
    apply Subtype.ext
    exact same.symm
  · refine ⟨true, ?_⟩
    apply Subtype.ext
    change symmetry.action first.1 = second.1
    exact partner.symm

theorem axisFiberC2Action_free
    (symmetry : FixedPointFreeInvolution Carrier)
    (quotientPoint : AxisQuotient symmetry)
    (bit : Bool) (point : AxisFiber symmetry quotientPoint)
    (fixed : axisFiberC2Action symmetry quotientPoint bit point = point) :
    bit = false := by
  cases bit
  · rfl
  · exfalso
    exact axisFiberSwap_fixedPointFree symmetry quotientPoint point
      (by simpa [axisFiberC2Action] using fixed)

theorem axisFiberC2Action_unique
    (symmetry : FixedPointFreeInvolution Carrier)
    (quotientPoint : AxisQuotient symmetry)
    (first second : AxisFiber symmetry quotientPoint) :
    ∃! bit : Bool,
      axisFiberC2Action symmetry quotientPoint bit first = second := by
  rcases axisFiberC2Action_transitive symmetry quotientPoint first second with
    ⟨bit, reaches⟩
  refine ⟨bit, reaches, ?_⟩
  intro other otherReaches
  cases bit with
  | false =>
    cases other with
    | false => rfl
    | true =>
      exfalso
      apply axisFiberSwap_fixedPointFree symmetry quotientPoint first
      have swapToSecond :
          axisFiberSwap symmetry quotientPoint first = second := by
        simpa [axisFiberC2Action] using otherReaches
      have secondToFirst : second = first := by
        simpa [axisFiberC2Action] using reaches.symm
      exact swapToSecond.trans secondToFirst
  | true =>
    cases other with
    | false =>
      exfalso
      apply axisFiberSwap_fixedPointFree symmetry quotientPoint first
      have swapToSecond :
          axisFiberSwap symmetry quotientPoint first = second := by
        simpa [axisFiberC2Action] using reaches
      have secondToFirst : second = first := by
        have firstToSecond : first = second := by
          simpa [axisFiberC2Action] using otherReaches
        exact firstToSecond.symm
      exact swapToSecond.trans secondToFirst
    | true => rfl

/-! ## Cardinality for arbitrary (not only displayed) quotient points -/

theorem axisFiber_card_eq_two_of_quotient
    (symmetry : FixedPointFreeInvolution Carrier)
    [Fintype Carrier] (quotientPoint : AxisQuotient symmetry) :
    Fintype.card (AxisFiber symmetry quotientPoint) = 2 := by
  refine Quotient.inductionOn quotientPoint ?_
  intro representative
  exact axisFiber_card_eq_two symmetry representative

theorem axisFiber_principal_c2_spine
    (symmetry : FixedPointFreeInvolution Carrier)
    (quotientPoint : AxisQuotient symmetry) :
    (∀ (first second : AxisFiber symmetry quotientPoint),
      ∃ bit : Bool,
        axisFiberC2Action symmetry quotientPoint bit first = second) ∧
    (∀ (bit : Bool) (point : AxisFiber symmetry quotientPoint)
      (_fixed : axisFiberC2Action symmetry quotientPoint bit point = point),
      bit = false) ∧
    (∀ (first second : AxisFiber symmetry quotientPoint),
      ∃! bit : Bool,
        axisFiberC2Action symmetry quotientPoint bit first = second) := by
  exact ⟨axisFiberC2Action_transitive symmetry quotientPoint,
    fun bit point fixed => axisFiberC2Action_free symmetry quotientPoint
      bit point fixed,
    axisFiberC2Action_unique symmetry quotientPoint⟩

end FixedPointFreeInvolution

end OCKIndividuationMSpaceComposition
