import OCKIndividuationMSpaceComposition.SymmetryIntrinsicFinitaryRank

namespace OCKIndividuationMSpaceComposition

universe uToken

namespace IntrinsicDimensionInterface

open IntrinsicFinitaryRank

variable {Token : Type uToken} [DecidableEq Token]

/-!
# Finite intrinsic-dimension interface

`FinitaryDistinctionClosure.rank` is already a canonical maximum over finite
closure-independent subfamilies.  The missing step before calling that number
an intrinsic dimension is the basis-independence statement: every maximal
independent family in the same finite seed must have the same cardinality.

This file makes the exact bridge explicit.  `BasisAugmentation` is kept as a
visible generic finite premise, not part of the rank definition and not
silently imported from vectors, matroids or a linear realization.  For the
current `FinitaryDistinctionClosure` the companion
`SymmetryExchangeAugmentation` theorem derives this premise from the existing
`exchange` field.  Under that premise, a maximal independent family has
cardinality equal to the existing exchange-rank, and two such families have
equal cardinality.

The current corpus has a separate finite countermodel showing that ordinary
extensive/monotone/idempotent closure laws alone do not ensure this interface
(`IntrinsicDimensionBoundary.closure_laws_do_not_force_wellDefined_rank`).
Therefore the theorem below records a conditional dimension boundary rather
than claiming that OC's present distinction vocabulary has already selected a
global intrinsic dimension.
-/

/-! Inclusion-maximal independent family inside a supplied finite seed. -/
def MaximalIndependent
    (closure : FinitaryDistinctionClosure Token)
    (seed family : Finset Token) : Prop :=
  closure.Independent family ∧
    family ⊆ seed ∧
      ∀ token ∈ seed, token ∉ family →
        ¬ closure.Independent (insert token family)

/-!
The finite augmentation property is the exact basis-independence interface
used below.  It says that a smaller independent family can be extended by a
member of any larger independent family in the same seed.  It is stated
separately so that generic callers can provide the appropriate law without
changing the rank definition; for the exchange-bearing OC closure it is
proved rather than assumed by `basisAugmentation_of_exchange`.
-/
def BasisAugmentation
    (closure : FinitaryDistinctionClosure Token)
    (seed : Finset Token) : Prop :=
  ∀ ⦃first second : Finset Token⦄,
    closure.Independent first →
    first ⊆ seed →
    closure.Independent second →
    second ⊆ seed →
    first.card < second.card →
    ∃ token ∈ second, token ∉ first ∧
      closure.Independent (insert token first)

/-! A maximal independent family realizes the canonical finite rank whenever
the explicit augmentation interface is available. -/
theorem maximalIndependent_card_eq_rank_of_augmentation
    (closure : FinitaryDistinctionClosure Token)
    (seed family : Finset Token)
    (maximal : MaximalIndependent closure seed family)
    (augmentation : BasisAugmentation closure seed) :
    family.card = closure.rank seed := by
  apply Nat.le_antisymm
  · exact closure.independent_card_le_rank maximal.2.1 maximal.1
  · by_contra notLe
    have familyCard_lt_rank : family.card < closure.rank seed :=
      Nat.lt_of_not_ge notLe
    rcases closure.exists_independent_rank_witness seed with
      ⟨basis, basisSubset, basisIndependent, basisCard⟩
    have familyCard_lt_basis : family.card < basis.card := by
      rw [basisCard]
      exact familyCard_lt_rank
    rcases augmentation maximal.1 maximal.2.1 basisIndependent basisSubset
      familyCard_lt_basis with
      ⟨token, tokenInBasis, tokenNotFamily, extendedIndependent⟩
    exact maximal.2.2 token (basisSubset tokenInBasis) tokenNotFamily
      extendedIndependent

/-! The rank is therefore independent of which maximal independent family is
chosen inside the same seed. -/
theorem maximalIndependent_card_unique_of_augmentation
    (closure : FinitaryDistinctionClosure Token)
    (seed left right : Finset Token)
    (leftMaximal : MaximalIndependent closure seed left)
    (rightMaximal : MaximalIndependent closure seed right)
    (augmentation : BasisAugmentation closure seed) :
    left.card = right.card := by
  rw [maximalIndependent_card_eq_rank_of_augmentation
      closure seed left leftMaximal augmentation,
    maximalIndependent_card_eq_rank_of_augmentation
      closure seed right rightMaximal augmentation]

/-! The dimension interpretation is exactly conditional: the exchange-rank
becomes a well-defined cardinality of maximal independent distinctions only
after `BasisAugmentation` has been proved for the selected OC closure. -/
theorem rank_is_wellDefined_maximalIndependent_dimension
    (closure : FinitaryDistinctionClosure Token)
    (seed family : Finset Token)
    (maximal : MaximalIndependent closure seed family)
    (augmentation : BasisAugmentation closure seed) :
    closure.rank seed = family.card := by
  exact (maximalIndependent_card_eq_rank_of_augmentation
    closure seed family maximal augmentation).symm

end IntrinsicDimensionInterface

end OCKIndividuationMSpaceComposition
