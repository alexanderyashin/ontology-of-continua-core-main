import OCKIndividuationMSpaceComposition.SymmetryGlobalC2InvariantDecomposition
import OCKIndividuationMSpaceComposition.SymmetryInvariantQuotient

namespace OCKIndividuationMSpaceComposition

universe uCarrier uValue

namespace PrimitiveDistinction

/-!
# Quotient semantics of the globally covered derived C₂

When the primitive pair covers the ambient carrier, its canonical swap is a
genuine fixed-point-free involution.  The generic quotient theorem can then
be instantiated without replacing the primitive construction by an assumed
action: an ambient observable factors through the orbit quotient exactly when
it is invariant under the derived pair swap.

In particular, the orbit-sum layer constructed in the preceding module is an
orientation-free observable on that quotient.  The quotient forgets polarity,
while the contrast layer remains the orientation-sensitive component.  This
is a semantic factorization result, not a claim that every ambient carrier is
globally two-point or that every observable is invariant.
-/

theorem carrierInvariant_iff_globalPairQuotient_factor_of_covers
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier)
    [Zero Value]
    (observable : Carrier → Value) :
    CarrierInvariant distinction observable ↔
      ∃ factor : AxisQuotient
          (distinction.pairSwapGlobalInvolution covers) → Value,
        ∀ point,
          factor (axisClass (distinction.pairSwapGlobalInvolution covers) point) =
            observable point := by
  constructor
  · intro invariant
    apply invariant_observable_factors_through_axis_quotient
      (distinction.pairSwapGlobalInvolution covers) observable
    intro point
    change observable (distinction.pairSwap point) = observable point
    exact invariant point
  · rintro ⟨factor, specification⟩
    have generic :
        InvariantObservable (distinction.pairSwapGlobalInvolution covers)
          observable :=
      (invariant_observable_iff_axis_quotient_factor
        (distinction.pairSwapGlobalInvolution covers) observable).mpr
        ⟨factor, specification⟩
    intro point
    exact generic point

theorem carrierInvariantPart_factors_through_globalPairQuotient
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier)
    [AddCommMonoid Value]
    (observable : Carrier → Value) :
    ∃ factor : AxisQuotient
          (distinction.pairSwapGlobalInvolution covers) → Value,
        ∀ point,
          factor (axisClass (distinction.pairSwapGlobalInvolution covers) point) =
            distinction.carrierInvariantPart observable point :=
  (distinction.carrierInvariant_iff_globalPairQuotient_factor_of_covers
    covers (distinction.carrierInvariantPart observable)).mp
    (distinction.carrierInvariantPart_invariant observable)

theorem globalPairQuotient_factor_unique
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier)
    [Zero Value]
    (observable : Carrier → Value)
    {factor₁ factor₂ : AxisQuotient
        (distinction.pairSwapGlobalInvolution covers) → Value}
    (spec₁ : ∀ point,
      factor₁ (axisClass (distinction.pairSwapGlobalInvolution covers) point) =
        observable point)
    (spec₂ : ∀ point,
      factor₂ (axisClass (distinction.pairSwapGlobalInvolution covers) point) =
        observable point) :
    factor₁ = factor₂ :=
  axis_quotient_factor_unique
    (distinction.pairSwapGlobalInvolution covers) observable spec₁ spec₂

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
