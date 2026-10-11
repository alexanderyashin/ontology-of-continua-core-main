import OCKIndividuationMSpaceComposition.SymmetryCanonicalPairingRelabellingBoundary
import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionGlobalC2
import Mathlib.Data.Fintype.Card

namespace OCKIndividuationMSpaceComposition

universe uCarrier

/-!
# Exact global canonicality boundary for a primitive distinction

M42 proves that parity gives existence of some global free involution, while
M43 proves that a selected involution cannot be invariant under every carrier
relabeling when a third point lies outside one orbit.  This module closes the
positive side of that boundary for a primitive distinction.

The pair transposition is relabeling-invariant exactly when the displayed pair
covers the carrier.  In the covered case the carrier has only two points and
the already classified ambient permutation algebra is C₂, so conjugation fixes
the transposition.  Conversely, a relabeling-invariant free involution that
exchanges the pair cannot coexist with a third point: M43 supplies the exact
contradiction.  Thus the result identifies the missing premise for a canonical
global C₂ action without hiding it in a definition.
-/

namespace PrimitiveDistinction

open FixedPointFreeInvolution

variable {Carrier : Type uCarrier}

/-! ## Positive covered case -/

/-- If the primitive pair covers the carrier, its canonical global swap is
fixed by conjugation under every carrier relabeling. -/
theorem pairSwapGlobal_relabellingInvariant
    [Fintype Carrier]
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier) :
    RelabellingInvariant (distinction.pairSwapGlobalInvolution covers) := by
  intro relabel
  rcases distinction.carrierAutomorphism_eq_identity_or_pairSwap covers relabel with
    identity | swap
  · subst relabel
    apply Equiv.ext
    intro point
    rfl
  · subst relabel
    apply Equiv.ext
    intro point
    rcases covers point with first | second
    · subst point
      simp [pairSwapGlobalInvolution, pairSwapEquiv, pairSwap]
    · subst point
      simp [pairSwapGlobalInvolution, pairSwapEquiv, pairSwap]

/-! ## Exact converse -/

/-- A relabeling-invariant free involution exchanging the primitive pair
forces that pair to cover the carrier.  The proof uses the third-point
obstruction rather than assuming cardinality or a global C₂ action. -/
theorem covers_of_exists_relabellingInvariant_pair_exchange
    (distinction : PrimitiveDistinction Carrier)
    (witness : ∃ symmetry : FixedPointFreeInvolution Carrier,
      symmetry.action distinction.first = distinction.second ∧
        RelabellingInvariant symmetry) :
    distinction.CoversCarrier := by
  rcases witness with ⟨symmetry, exchanges, invariant⟩
  intro point
  by_cases pointFirst : point = distinction.first
  · exact Or.inl pointFirst
  by_cases pointSecond : point = distinction.second
  · exact Or.inr pointSecond
  exfalso
  have point_ne_partner : point ≠ symmetry.action distinction.first := by
    intro equality
    apply pointSecond
    rw [← exchanges]
    exact equality
  exact (no_relabelling_invariant_of_third_point symmetry
    ⟨distinction.first, point, pointFirst, point_ne_partner⟩) invariant

/-- The primitive pair admits a relabeling-invariant global free involution
exchanging its endpoints exactly when it covers the carrier. -/
theorem exists_relabellingInvariant_pair_exchange_iff_covers
    [Fintype Carrier]
    (distinction : PrimitiveDistinction Carrier) :
    (∃ symmetry : FixedPointFreeInvolution Carrier,
      symmetry.action distinction.first = distinction.second ∧
        RelabellingInvariant symmetry) ↔
      distinction.CoversCarrier := by
  constructor
  · exact covers_of_exists_relabellingInvariant_pair_exchange distinction
  · intro covers
    refine ⟨distinction.pairSwapGlobalInvolution covers, ?_, ?_⟩
    · exact distinction.pairSwapGlobalInvolution_exchanges_pair covers
    · exact pairSwapGlobal_relabellingInvariant distinction covers

/-! ## Finite cardinality corollary -/

/-- On a finite carrier, the same canonicality condition is exactly the
two-point cardinality boundary. -/
theorem exists_relabellingInvariant_pair_exchange_iff_card_eq_two
    [Fintype Carrier]
    (distinction : PrimitiveDistinction Carrier) :
    (∃ symmetry : FixedPointFreeInvolution Carrier,
      symmetry.action distinction.first = distinction.second ∧
        RelabellingInvariant symmetry) ↔
      Fintype.card Carrier = 2 := by
  rw [exists_relabellingInvariant_pair_exchange_iff_covers]
  exact distinction.coversCarrier_iff_card_eq_two

/-! ## Integrated boundary statement -/

/-- The complete boundary combines the existence side, the canonicality side,
and the exact local C₂ result: a primitive distinction generates a canonical
global C₂ action precisely at the two-point coverage boundary. -/
theorem global_canonical_c2_boundary_spine
    [Fintype Carrier]
    (distinction : PrimitiveDistinction Carrier) :
    (∃ symmetry : FixedPointFreeInvolution Carrier,
      symmetry.action distinction.first = distinction.second ∧
        RelabellingInvariant symmetry) ↔
      Fintype.card Carrier = 2 := by
  exact exists_relabellingInvariant_pair_exchange_iff_card_eq_two distinction

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
