import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionGlobalC2
import Mathlib.Tactic.Abel

namespace OCKIndividuationMSpaceComposition

universe uCarrier uValue

namespace PrimitiveDistinction

/-!
# Global invariant and odd layers of a primitive distinction

The canonical pair swap is defined on the entire carrier, even when the
distinguished pair does not cover it.  This module therefore lifts the usual
two-point invariant/anti-invariant decomposition from the generated axis to
the ambient carrier.  The construction does not add an action hypothesis: it
uses only the involution already proved for `pairSwap`.

The exact algebraic statement is a reconstruction of `2 • f`.  Recovering
`f` from half-sums is deliberately not claimed; that requires an additional
assumption on the value type making two invertible.  Coverage is needed only
for the semantic statement that an invariant observable has equal values on
the two primitive poles.
-/

/-! ## Ambient invariant and odd predicates -/

/-- An ambient observable is invariant under the canonical pair swap. -/
noncomputable def CarrierInvariant
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    (observable : Carrier → Value)
    [Zero Value] : Prop :=
  ∀ point, observable (distinction.pairSwap point) = observable point

/-- An ambient observable is anti-invariant (odd) under the canonical swap. -/
noncomputable def CarrierAntiInvariant
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    (observable : Carrier → Value)
    [Neg Value] : Prop :=
  ∀ point, observable (distinction.pairSwap point) = - observable point

/-! ## The two projected layers -/

/-- The orbit-sum (invariant) layer of an ambient observable. -/
noncomputable def carrierInvariantPart
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [Add Value] (observable : Carrier → Value) : Carrier → Value :=
  fun point => observable point + observable (distinction.pairSwap point)

/-- The contrast (anti-invariant) layer of an ambient observable. -/
noncomputable def carrierAntiInvariantPart
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [Sub Value] (observable : Carrier → Value) : Carrier → Value :=
  fun point => observable point - observable (distinction.pairSwap point)

/-! ## Algebraic laws -/

/-- The orbit-sum layer is invariant under the ambient swap. -/
theorem carrierInvariantPart_invariant
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [AddCommMonoid Value]
    (observable : Carrier → Value) :
    CarrierInvariant distinction (distinction.carrierInvariantPart observable) := by
  intro point
  change observable (distinction.pairSwap point) +
      observable (distinction.pairSwap (distinction.pairSwap point)) =
    observable point + observable (distinction.pairSwap point)
  rw [distinction.pairSwap_involutive]
  exact add_comm _ _

/-- The contrast layer is anti-invariant under the ambient swap. -/
theorem carrierAntiInvariantPart_antiInvariant
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [AddCommGroup Value]
    (observable : Carrier → Value) :
    CarrierAntiInvariant distinction (distinction.carrierAntiInvariantPart observable) := by
  intro point
  change observable (distinction.pairSwap point) -
      observable (distinction.pairSwap (distinction.pairSwap point)) =
    -(observable point - observable (distinction.pairSwap point))
  rw [distinction.pairSwap_involutive]
  abel

/-- The invariant and odd layers reconstruct twice the original observable. -/
theorem carrierInvariantPart_add_carrierAntiInvariantPart_eq_two_smul
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [AddCommGroup Value]
    (observable : Carrier → Value) (point : Carrier) :
    distinction.carrierInvariantPart observable point +
        distinction.carrierAntiInvariantPart observable point =
      2 • observable point := by
  change (observable point + observable (distinction.pairSwap point)) +
      (observable point - observable (distinction.pairSwap point)) =
    2 • observable point
  rw [two_nsmul]
  abel

/-! ## Semantic link back to the primitive poles -/

/-- Under exact coverage, global invariance is equivalent to equality of the
primitive endpoint values.  Without coverage, endpoint equality alone cannot
control values on an outside complement. -/
theorem carrierInvariant_iff_endpoint_equal_of_covers
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier)
    [Zero Value]
    (observable : Carrier → Value) :
    CarrierInvariant distinction observable ↔
      observable distinction.first = observable distinction.second := by
  constructor
  · intro invariant
    have endpoint := invariant distinction.first
    simpa [distinction.pairSwap_first] using endpoint.symm
  · intro endpointEqual point
    rcases covers point with pointFirst | pointSecond
    · subst point
      simpa [distinction.pairSwap_first] using endpointEqual.symm
    · subst point
      simpa [distinction.pairSwap_second] using endpointEqual

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
