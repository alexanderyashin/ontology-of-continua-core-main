import OCKIndividuationMSpaceComposition.SymmetryGlobalC2NormalizedDecomposition
import OCKIndividuationMSpaceComposition.SymmetryGlobalC2OddQuotientExactness

namespace OCKIndividuationMSpaceComposition

universe uCarrier uValue

namespace PrimitiveDistinction

/-!
# Quotient bridge for the normalized global layers

The normalized decomposition separates the orientation-free and
orientation-sensitive information.  Under exact coverage, the even half
always descends to the pair quotient.  The odd half descends only when it is
identically zero: characteristic-zero turns the general M21 2-torsion
criterion into an exact zero criterion.
-/

theorem carrierInvariantHalf_factors_through_globalPairQuotient
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier)
    [Field Value] [CharZero Value]
    (observable : Carrier → Value) :
    ∃ factor : AxisQuotient
        (distinction.pairSwapGlobalInvolution covers) → Value,
      ∀ point,
        factor (axisClass (distinction.pairSwapGlobalInvolution covers) point) =
          distinction.carrierInvariantHalf observable point :=
  (distinction.carrierInvariant_iff_globalPairQuotient_factor_of_covers
    covers (distinction.carrierInvariantHalf observable)).mp
    (distinction.carrierInvariantHalf_invariant observable)

theorem carrierAntiInvariantHalf_factor_through_globalPairQuotient_iff_zero
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier)
    [Field Value] [CharZero Value]
    (observable : Carrier → Value) :
    (∃ factor : AxisQuotient
        (distinction.pairSwapGlobalInvolution covers) → Value,
      ∀ point,
        factor (axisClass (distinction.pairSwapGlobalInvolution covers) point) =
          distinction.carrierAntiInvariantHalf observable point) ↔
      ∀ point, distinction.carrierAntiInvariantHalf observable point = 0 := by
  constructor
  · intro factorization point
    have torsion :
        2 • distinction.carrierAntiInvariantHalf observable point = 0 :=
      (distinction.carrierAntiInvariant_factor_through_globalPairQuotient_iff_two_torsion
        covers (distinction.carrierAntiInvariantHalf observable)
        (distinction.carrierAntiInvariantHalf_antiInvariant observable)).mp
        factorization point
    have doubled :
        (2 : Value) * distinction.carrierAntiInvariantHalf observable point = 0 := by
      simpa [two_nsmul] using torsion
    exact (mul_eq_zero.mp doubled).resolve_left (by norm_num)
  · intro zero
    apply (distinction.carrierAntiInvariant_factor_through_globalPairQuotient_iff_two_torsion
      covers (distinction.carrierAntiInvariantHalf observable)
      (distinction.carrierAntiInvariantHalf_antiInvariant observable)).mpr
    intro point
    rw [zero point]
    simp

theorem carrierAntiInvariantHalf_eq_zero_iff_carrierInvariant
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [Field Value] [CharZero Value]
    (observable : Carrier → Value) :
    (∀ point, distinction.carrierAntiInvariantHalf observable point = 0) ↔
      CarrierInvariant distinction observable := by
  constructor
  · intro zero point
    have half_zero :
        (observable point - observable (distinction.pairSwap point)) / 2 = 0 :=
      zero point
    have diff_zero :
        observable point - observable (distinction.pairSwap point) = 0 := by
      have multiplied :=
        (div_eq_iff (by norm_num : (2 : Value) ≠ 0)).mp half_zero
      simpa using multiplied
    exact (sub_eq_zero.mp diff_zero).symm
  · intro invariant point
    change (observable point - observable (distinction.pairSwap point)) / 2 = 0
    rw [sub_eq_zero.mpr (invariant point).symm, zero_div]

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
