import OCKIndividuationMSpaceComposition.SymmetryOrientationFiberPrincipalC2
import OCKIndividuationMSpaceComposition.SymmetryAxisCoaxisTorsorAction

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# Equivariant bridge from presentations to coorientations

There are two local ways to display the same primitive distinction: an
orientation presentation (which endpoint is written first), and a coaxis of
the generated two-point axis (which endpoint is called positive).  This file
proves that they are the same two-element torsor, with endpoint reversal on
one side corresponding exactly to coaxis reversal on the other.

The equivalence is constructed from the already proved two-element
classifications.  It therefore adds no orientation, coaxis, or C₂ premise and
does not identify either local torsor with an orientation of the ambient
carrier.
-/

noncomputable def orientationToAxisCoaxis {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier)
    (presentation : OrientationFiber base) :
    AxisCoaxis base.toFixedPointFreeInvolution base.axisFirst := by
  classical
  exact if presentation = orientationBase base then
    baseAxisCoaxis base.toFixedPointFreeInvolution base.axisFirst else
    reverseAxisCoaxis (baseAxisCoaxis base.toFixedPointFreeInvolution
      base.axisFirst)

@[simp] theorem orientationToAxisCoaxis_base {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier) :
    orientationToAxisCoaxis base (orientationBase base) =
      baseAxisCoaxis base.toFixedPointFreeInvolution base.axisFirst := by
  simp [orientationToAxisCoaxis]

@[simp] theorem orientationToAxisCoaxis_partner {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier) :
    orientationToAxisCoaxis base (orientationPartner base) =
      reverseAxisCoaxis (baseAxisCoaxis base.toFixedPointFreeInvolution
        base.axisFirst) := by
  have partner_ne_base : orientationPartner base ≠ orientationBase base :=
    (orientationBase_ne_partner base).symm
  simp [orientationToAxisCoaxis, partner_ne_base]

noncomputable def axisCoaxisToOrientation {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier)
    (coaxis : AxisCoaxis base.toFixedPointFreeInvolution base.axisFirst) :
    OrientationFiber base := by
  classical
  exact if coaxis = baseAxisCoaxis base.toFixedPointFreeInvolution
      base.axisFirst then orientationBase base else orientationPartner base

@[simp] theorem axisCoaxisToOrientation_base {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier) :
    axisCoaxisToOrientation base
        (baseAxisCoaxis base.toFixedPointFreeInvolution base.axisFirst) =
      orientationBase base := by
  simp [axisCoaxisToOrientation]

@[simp] theorem axisCoaxisToOrientation_reverse_base
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier) :
    axisCoaxisToOrientation base
        (reverseAxisCoaxis (baseAxisCoaxis base.toFixedPointFreeInvolution
          base.axisFirst)) = orientationPartner base := by
  have reverse_ne_base :
      reverseAxisCoaxis (baseAxisCoaxis base.toFixedPointFreeInvolution
        base.axisFirst) ≠ baseAxisCoaxis base.toFixedPointFreeInvolution
          base.axisFirst := by
    simpa [coaxisSwap] using
      (coaxisSwap_ne_self
        (baseAxisCoaxis base.toFixedPointFreeInvolution base.axisFirst))
  simp [axisCoaxisToOrientation, reverse_ne_base]

theorem reverse_baseAxisCoaxis_twice {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier) :
    reverseAxisCoaxis (reverseAxisCoaxis
        (baseAxisCoaxis base.toFixedPointFreeInvolution base.axisFirst)) =
      baseAxisCoaxis base.toFixedPointFreeInvolution base.axisFirst := by
  apply axisCoaxis_ext_positive
  ext point
  exact reverseAxisCoaxis_twice
    (baseAxisCoaxis base.toFixedPointFreeInvolution base.axisFirst) point

/-! ## The two local torsors are equivalent -/

noncomputable def orientationFiberAxisCoaxisEquiv
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier) :
    OrientationFiber base ≃
      AxisCoaxis base.toFixedPointFreeInvolution base.axisFirst where
  toFun := orientationToAxisCoaxis base
  invFun := axisCoaxisToOrientation base
  left_inv := by
    intro presentation
    rcases orientationFiber_eq_base_or_partner base presentation with
      rfl | rfl <;> simp
  right_inv := by
    intro coaxis
    rcases axisCoaxis_eq_base_or_reverse_base
      base.toFixedPointFreeInvolution base.axisFirst coaxis with
      base_case | reverse_case
    · subst coaxis
      simp
    · subst coaxis
      simp

theorem orientationFiberAxisCoaxisEquiv_intertwines_reverse
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier)
    (presentation : OrientationFiber base) :
    orientationFiberAxisCoaxisEquiv base
        (orientationReverse base presentation) =
      coaxisSwap (orientationFiberAxisCoaxisEquiv base presentation) := by
  rcases orientationFiber_eq_base_or_partner base presentation with
    rfl | rfl <;>
      simp [orientationFiberAxisCoaxisEquiv, coaxisSwap,
        reverse_baseAxisCoaxis_twice]

theorem orientationFiberAxisCoaxisEquiv_intertwines_c2
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier)
    (bit : Bool) (presentation : OrientationFiber base) :
    orientationFiberAxisCoaxisEquiv base
        (orientationC2Action base bit presentation) =
      coaxisC2Action bit
        (orientationFiberAxisCoaxisEquiv base presentation) := by
  cases bit
  · rfl
  · exact orientationFiberAxisCoaxisEquiv_intertwines_reverse base presentation

/-! ## Compact semantic bridge -/

theorem orientationFiber_axisCoaxis_equivariant_principal_c2_spine
    {Carrier : Type uCarrier} (base : PrimitiveDistinction Carrier) :
    Nonempty
        (OrientationFiber base ≃
          AxisCoaxis base.toFixedPointFreeInvolution base.axisFirst) ∧
      (∀ presentation : OrientationFiber base,
        orientationFiberAxisCoaxisEquiv base
            (orientationReverse base presentation) =
          coaxisSwap (orientationFiberAxisCoaxisEquiv base presentation)) ∧
      (∀ (bit : Bool) (presentation : OrientationFiber base),
        orientationFiberAxisCoaxisEquiv base
            (orientationC2Action base bit presentation) =
          coaxisC2Action bit
            (orientationFiberAxisCoaxisEquiv base presentation)) := by
  exact ⟨⟨orientationFiberAxisCoaxisEquiv base⟩,
    orientationFiberAxisCoaxisEquiv_intertwines_reverse base,
    orientationFiberAxisCoaxisEquiv_intertwines_c2 base⟩

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
