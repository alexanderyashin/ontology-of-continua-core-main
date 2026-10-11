import OCKIndividuationMSpaceComposition.SymmetryGlobalC2OddBoundary
import OCKIndividuationMSpaceComposition.SymmetryGlobalC2InvariantQuotient

namespace OCKIndividuationMSpaceComposition

universe uCarrier uValue

namespace PrimitiveDistinction

/-!
# Quotient obstruction for the odd layer

The derived pair swap has two distinct semantic components.  The invariant
component descends to the orbit quotient, while the anti-invariant component
can descend only when its values are 2-torsion.  This file isolates that
obstruction as a theorem rather than silently treating the odd layer as an
orientation-free observable.

The result is deliberately conditional: a nonzero contrast excludes quotient
factorization only after a no-2-torsion premise (or a direct non-2-torsion
witness).  In a value type with 2-torsion, the weaker conclusion is the exact
forced equation `2 • contrast = 0`.
-/

/-- Quotient factorization of the contrast forces every contrast value to be
2-torsion.  The proof combines quotient invariance with anti-invariance of the
derived pair swap, so it does not assume an extra global action. -/
theorem carrierAntiInvariant_factor_through_globalPairQuotient_forces_two_torsion
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier)
    [AddCommGroup Value]
    (observable : Carrier → Value)
    {factor : AxisQuotient
        (distinction.pairSwapGlobalInvolution covers) → Value}
    (specification : ∀ point,
      factor (axisClass (distinction.pairSwapGlobalInvolution covers) point) =
        distinction.carrierAntiInvariantPart observable point)
    (point : Carrier) :
    2 • distinction.carrierAntiInvariantPart observable point = 0 := by
  have invariant :
      CarrierInvariant distinction
        (distinction.carrierAntiInvariantPart observable) := by
    apply (distinction.carrierInvariant_iff_globalPairQuotient_factor_of_covers
      covers (distinction.carrierAntiInvariantPart observable)).mpr
    exact ⟨factor, specification⟩
  have same :
      distinction.carrierAntiInvariantPart observable
          (distinction.pairSwap point) =
        distinction.carrierAntiInvariantPart observable point :=
    invariant point
  have opposite :
      distinction.carrierAntiInvariantPart observable
          (distinction.pairSwap point) =
        - distinction.carrierAntiInvariantPart observable point :=
    distinction.carrierAntiInvariantPart_antiInvariant observable point
  calc
    2 • distinction.carrierAntiInvariantPart observable point =
        distinction.carrierAntiInvariantPart observable point +
          distinction.carrierAntiInvariantPart observable point := by
      rw [two_nsmul]
    _ = distinction.carrierAntiInvariantPart observable point +
          distinction.carrierAntiInvariantPart observable
            (distinction.pairSwap point) := by
      congr 1
      exact same.symm
    _ = distinction.carrierAntiInvariantPart observable point +
          (- distinction.carrierAntiInvariantPart observable point) := by
      rw [opposite]
    _ = 0 := add_neg_cancel _

/-- A witnessed non-2-torsion contrast cannot descend to the global pair
quotient.  This is the exact odd/equivariant obstruction, with no claim that
nonzero alone is sufficient in a value type with 2-torsion. -/
theorem carrierAntiInvariantPart_not_factor_through_globalPairQuotient_of_two_nsmul_ne_zero
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier)
    [AddCommGroup Value]
    (observable : Carrier → Value)
    (point : Carrier)
    (nonTorsion :
      2 • distinction.carrierAntiInvariantPart observable point ≠ 0) :
    ¬ ∃ factor : AxisQuotient
          (distinction.pairSwapGlobalInvolution covers) → Value,
        ∀ point,
          factor (axisClass (distinction.pairSwapGlobalInvolution covers) point) =
            distinction.carrierAntiInvariantPart observable point := by
  rintro ⟨factor, specification⟩
  exact nonTorsion
    (distinction.carrierAntiInvariant_factor_through_globalPairQuotient_forces_two_torsion
      covers observable specification point)

/-- Under a no-2-torsion value type, any nonzero contrast witness forbids
factorization through the orientation-forgetting quotient. -/
theorem carrierAntiInvariantPart_not_factor_through_globalPairQuotient_of_ne_zero
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier)
    [AddCommGroup Value]
    (observable : Carrier → Value)
    (noTwoTorsion : ∀ value : Value, 2 • value = 0 → value = 0)
    (point : Carrier)
    (nonzero : distinction.carrierAntiInvariantPart observable point ≠ 0) :
    ¬ ∃ factor : AxisQuotient
          (distinction.pairSwapGlobalInvolution covers) → Value,
        ∀ point,
          factor (axisClass (distinction.pairSwapGlobalInvolution covers) point) =
            distinction.carrierAntiInvariantPart observable point := by
  apply distinction.carrierAntiInvariantPart_not_factor_through_globalPairQuotient_of_two_nsmul_ne_zero
    covers observable point
  intro torsion
  exact nonzero (noTwoTorsion _ torsion)

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
