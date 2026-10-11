import OCKIndividuationMSpaceComposition.SymmetryGlobalC2OddQuotientBoundary

namespace OCKIndividuationMSpaceComposition

universe uCarrier uValue

namespace PrimitiveDistinction

/-!
# Exactness of the odd quotient obstruction

The preceding boundary theorem showed that factorization of an odd observable
through the orientation-forgetting quotient forces pointwise 2-torsion.  This
file closes the converse: for an arbitrary anti-invariant observable, that
2-torsion condition is also sufficient.  Thus the obstruction is an exact
characterization, not merely a one-way diagnostic.

No freeness, involution, or factorization law is hidden in the definition of
`CarrierAntiInvariant`; the only global action used here is the pair swap
already derived from the primitive distinction and its coverage proof.
-/

/-- An anti-invariant observable factors through the global pair quotient
exactly when every value is 2-torsion.  In a value type with no nontrivial
2-torsion this reduces to the expected vanishing obstruction. -/
theorem carrierAntiInvariant_factor_through_globalPairQuotient_iff_two_torsion
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier)
    [AddCommGroup Value]
    (observable : Carrier → Value)
    (antiInvariant : CarrierAntiInvariant distinction observable) :
    (∃ factor : AxisQuotient
        (distinction.pairSwapGlobalInvolution covers) → Value,
      ∀ point,
        factor (axisClass (distinction.pairSwapGlobalInvolution covers) point) =
          observable point) ↔
      ∀ point, 2 • observable point = 0 := by
  constructor
  · rintro ⟨factor, specification⟩ point
    have invariant : CarrierInvariant distinction observable := by
      exact (distinction.carrierInvariant_iff_globalPairQuotient_factor_of_covers
        covers observable).mpr ⟨factor, specification⟩
    have same : observable (distinction.pairSwap point) = observable point :=
      invariant point
    have opposite : observable (distinction.pairSwap point) = - observable point :=
      antiInvariant point
    calc
      2 • observable point = observable point + observable point := by
        rw [two_nsmul]
      _ = observable point + observable (distinction.pairSwap point) := by
        congr 1
        exact same.symm
      _ = observable point + (- observable point) := by
        rw [opposite]
      _ = 0 := add_neg_cancel _
  · intro twoTorsion
    have invariant : CarrierInvariant distinction observable := by
      intro point
      have sumZero : observable point + observable point = 0 := by
        simpa [two_nsmul] using twoTorsion point
      have negEq : - observable point = observable point := by
        calc
          - observable point = - observable point + 0 := by simp
          _ = - observable point +
              (observable point + observable point) := by rw [sumZero]
          _ = observable point := by abel
      exact (antiInvariant point).trans negEq
    exact (distinction.carrierInvariant_iff_globalPairQuotient_factor_of_covers
      covers observable).mp invariant

/-- The derived contrast layer is quotient-factorable precisely in the
2-torsion regime. -/
theorem carrierAntiInvariantPart_factor_through_globalPairQuotient_iff_two_torsion
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier)
    [AddCommGroup Value]
    (observable : Carrier → Value) :
    (∃ factor : AxisQuotient
        (distinction.pairSwapGlobalInvolution covers) → Value,
      ∀ point,
        factor (axisClass (distinction.pairSwapGlobalInvolution covers) point) =
          distinction.carrierAntiInvariantPart observable point) ↔
      ∀ point, 2 • distinction.carrierAntiInvariantPart observable point = 0 :=
  distinction.carrierAntiInvariant_factor_through_globalPairQuotient_iff_two_torsion
    covers (distinction.carrierAntiInvariantPart observable)
    (distinction.carrierAntiInvariantPart_antiInvariant observable)

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
