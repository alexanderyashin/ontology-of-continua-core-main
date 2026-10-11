import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinction
import OCKIndividuationMSpaceComposition.SymmetryAxisCoaxisTorsor
import OCKIndividuationMSpaceComposition.SymmetrySignRepresentation

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# The axis of the axis

The primitive distinction already produces a two-point axis and its canonical
swap.  Applying the generic orbit construction once more at a chosen endpoint
therefore produces an ``axis of the axis``.  This module proves that the
second construction is only a presentation change: it is canonically
equivalent to the original generated axis, and the induced odd sign/coaxis
coordinate is exactly the previously derived polarity.

The result makes the ``difference is an axis of the axis`` intuition precise
without adding a new symmetry hypothesis.  The only non-canonical datum is
the base endpoint used to call one sign negative; exchanging that base applies
Boolean negation.
-/

abbrev AxisOfAxis {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :=
  axis distinction.toFixedPointFreeInvolution distinction.axisFirst

/-- Every point of the primitive axis gives a point of its second-order axis.
    The proof is derived from the two endpoint cases, not assumed. -/
def axisOfAxisPoint {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (point : distinction.Axis) : distinction.AxisOfAxis :=
  ⟨point, by
    rcases distinction.axis_cases point with first | second
    · exact Or.inl first
    · right
      rw [second]
      exact distinction.axisSwap_first.symm⟩

/-- Forgetting the second-order membership proof is the inverse map. -/
noncomputable def axisOfAxisEquiv {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    distinction.Axis ≃ distinction.AxisOfAxis where
  toFun := distinction.axisOfAxisPoint
  invFun := Subtype.val
  left_inv := by
    intro point
    rfl
  right_inv := by
    intro point
    apply Subtype.ext
    rfl

/-- The second-order swap is transported from the primitive swap. -/
theorem axisOfAxisPoint_swap {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (point : distinction.Axis) :
    distinction.axisOfAxisPoint (distinction.axisSwap point) =
      OCKIndividuationMSpaceComposition.axisSwap
        distinction.toFixedPointFreeInvolution
        distinction.axisFirst (distinction.axisOfAxisPoint point) := by
  apply Subtype.ext
  rfl

/-- The canonical coaxis on the axis of the axis. -/
noncomputable def primitiveAxisOfAxisCoaxis {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    AxisCoaxis distinction.toFixedPointFreeInvolution distinction.axisFirst :=
  baseAxisCoaxis distinction.toFixedPointFreeInvolution distinction.axisFirst

/-- The canonical sign pairing on the axis of the axis. -/
noncomputable def primitiveAxisOfAxisSignPairing {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    AxisSignPairing distinction.toFixedPointFreeInvolution distinction.axisFirst :=
  baseAxisSignPairing distinction.toFixedPointFreeInvolution distinction.axisFirst

/-! ## The coaxis/sign is exactly the primitive polarity -/

theorem primitiveAxisOfAxisCoaxis_positive_iff_polarity_false
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (point : distinction.Axis) :
    distinction.axisOfAxisPoint point ∈
        (distinction.primitiveAxisOfAxisCoaxis).positive ↔
      distinction.generatedPolarity point = false := by
  rcases distinction.axis_cases point with first | second
  · subst point
    constructor
    · intro _
      exact distinction.generatedPolarity_first
    · intro _
      change (distinction.axisOfAxisPoint distinction.axisFirst).1 =
        distinction.axisFirst
      rfl
  · subst point
    constructor
    · intro membership
      have equal : distinction.axisSecond = distinction.axisFirst := by
        change (distinction.axisOfAxisPoint distinction.axisSecond).1 =
          distinction.axisFirst at membership
        exact membership
      exact (distinction.axisFirst_ne_axisSecond equal.symm).elim
    · intro polarity
      rw [distinction.generatedPolarity_second] at polarity
      cases polarity

theorem primitiveAxisOfAxisSign_agrees_with_polarity
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (point : distinction.Axis) :
    (distinction.primitiveAxisOfAxisSignPairing).sign
        (distinction.axisOfAxisPoint point) =
      distinction.generatedPolarity point := by
  classical
  rcases distinction.axis_cases point with first | second
  · subst point
    simp [axisOfAxisPoint, primitiveAxisOfAxisSignPairing]
  · subst point
    rw [distinction.generatedPolarity_second]
    change (if distinction.axisSecond = distinction.axisFirst then false else true) = true
    have distinct : distinction.axisSecond ≠ distinction.axisFirst :=
      Ne.symm distinction.axisFirst_ne_axisSecond
    simp [distinct]

/-- The two possible coorientations of the second-order axis are exactly the
    base choice and its reversal. -/
theorem primitiveAxisOfAxisCoaxis_eq_base_or_reverse
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (coaxis : AxisCoaxis distinction.toFixedPointFreeInvolution
      distinction.axisFirst) :
    coaxis = distinction.primitiveAxisOfAxisCoaxis ∨
      coaxis = reverseAxisCoaxis distinction.primitiveAxisOfAxisCoaxis := by
  exact axisCoaxis_eq_base_or_reverse_base
    distinction.toFixedPointFreeInvolution distinction.axisFirst coaxis

/-! ## One compact bridge theorem -/

theorem primitiveDistinction_axis_of_axis_spine
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    Nonempty (distinction.Axis ≃ distinction.AxisOfAxis) ∧
      (∀ point : distinction.Axis,
        distinction.axisOfAxisPoint (distinction.axisSwap point) =
          OCKIndividuationMSpaceComposition.axisSwap
            distinction.toFixedPointFreeInvolution
            distinction.axisFirst (distinction.axisOfAxisPoint point)) ∧
      (∀ point : distinction.Axis,
        (distinction.primitiveAxisOfAxisSignPairing).sign
            (distinction.axisOfAxisPoint point) =
          distinction.generatedPolarity point) ∧
      Nonempty
        (AxisCoaxis distinction.toFixedPointFreeInvolution
          distinction.axisFirst ≃ Bool) := by
  refine ⟨⟨distinction.axisOfAxisEquiv⟩, ?_, ?_, ?_⟩
  · intro point
    exact distinction.axisOfAxisPoint_swap point
  · intro point
    exact distinction.primitiveAxisOfAxisSign_agrees_with_polarity point
  · exact ⟨axisCoaxisEquivBool distinction.toFixedPointFreeInvolution
      distinction.axisFirst⟩

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
