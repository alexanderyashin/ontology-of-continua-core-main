import OCKIndividuationMSpaceComposition.SymmetryIntrinsicDimensionInterface

namespace OCKIndividuationMSpaceComposition

universe uToken

namespace IntrinsicDimensionExchangeAugmentation

open IntrinsicDimensionInterface
open IntrinsicFinitaryRank

variable {Token : Type uToken} [DecidableEq Token]

/-!
# Exchange implies the finite augmentation interface

`FinitaryDistinctionClosure.exchange` is the Steinitz closure-exchange law.
This file makes explicit the finite argument that was previously left as an
interface premise: a maximum-cardinality independent witness spans its seed;
adding a generated token leaves rank unchanged; and a finite induction then
gives augmentation.  No vector, module or matroid realization is imported.
-/

/-! Rank cannot exceed the cardinality of its finite seed. -/
theorem rank_le_card
    (closure : FinitaryDistinctionClosure Token)
    (seed : Finset Token) :
    closure.rank seed ≤ seed.card := by
  classical
  unfold FinitaryDistinctionClosure.rank
  apply Finset.sup_le
  intro family familyMember
  exact Finset.card_le_card (Finset.mem_powerset.mp
    (Finset.mem_filter.mp familyMember).1)

/-! An independent finite family attains the rank of itself. -/
theorem rank_eq_card_of_independent
    (closure : FinitaryDistinctionClosure Token)
    {family : Finset Token}
    (independent : closure.Independent family) :
    closure.rank family = family.card := by
  apply Nat.le_antisymm
  · exact rank_le_card closure family
  · exact closure.independent_card_le_rank subset_rfl independent

/-!
A maximum-cardinality independent subfamily spans the supplied seed.  If a
seed element were outside its closure, the existing exchange-based insertion
lemma would increase the supposedly maximum rank.
-/
theorem rank_witness_spans_seed
    (closure : FinitaryDistinctionClosure Token)
    (seed family : Finset Token)
    (familySubset : family ⊆ seed)
    (familyIndependent : closure.Independent family)
    (familyCard : family.card = closure.rank seed) :
    seed ⊆ closure.close family := by
  intro token tokenInSeed
  by_contra tokenNotGenerated
  have tokenNotFamily : token ∉ family := by
    intro tokenInFamily
    exact tokenNotGenerated (closure.extensive family tokenInFamily)
  have extendedIndependent :
      closure.Independent (insert token family) :=
    familyIndependent.insert_of_not_generated tokenNotGenerated
  have extendedSubset : insert token family ⊆ seed := by
    intro current currentMember
    rcases Finset.mem_insert.mp currentMember with rfl | currentInFamily
    · exact tokenInSeed
    · exact familySubset currentInFamily
  have extendedBound := closure.independent_card_le_rank
    extendedSubset extendedIndependent
  rw [Finset.card_insert_of_notMem tokenNotFamily, familyCard] at extendedBound
  exact Nat.not_succ_le_self _ extendedBound

/-!
Generated elements do not increase finite closure-rank.  The proof uses a
rank witness for the enlarged seed and the preceding spanning lemma; this is
the finite closure argument that prevents a hidden basis-independence premise.
-/
theorem rank_insert_eq_of_generated
    (closure : FinitaryDistinctionClosure Token)
    (seed : Finset Token) (token : Token)
    (generated : token ∈ closure.close seed) :
    closure.rank (insert token seed) = closure.rank seed := by
  classical
  by_cases tokenInSeed : token ∈ seed
  · simp [Finset.insert_eq_of_mem tokenInSeed]
  · apply Nat.le_antisymm
    · by_contra notLe
      have rankLower : closure.rank seed < closure.rank (insert token seed) :=
        Nat.lt_of_not_ge notLe
      have rankUpper :
          closure.rank (insert token seed) ≤ closure.rank seed + 1 := by
        unfold FinitaryDistinctionClosure.rank
        apply Finset.sup_le
        intro family familyMember
        exact closure.independent_insert_card_le
          (Finset.mem_powerset.mp (Finset.mem_filter.mp familyMember).1)
          (Finset.mem_filter.mp familyMember).2
      have rankSucc :
          closure.rank (insert token seed) = closure.rank seed + 1 := by
        omega
      rcases closure.exists_independent_rank_witness (insert token seed) with
        ⟨family, familySubset, familyIndependent, familyCard⟩
      have tokenInFamily : token ∈ family := by
        by_contra tokenNotInFamily
        have familySubsetSeed : family ⊆ seed := by
          intro current currentMember
          rcases Finset.mem_insert.mp (familySubset currentMember) with
            rfl | currentInSeed
          · exact False.elim (tokenNotInFamily currentMember)
          · exact currentInSeed
        have familyBound := closure.independent_card_le_rank
          familySubsetSeed familyIndependent
        rw [familyCard, rankSucc] at familyBound
        exact Nat.not_succ_le_self _ familyBound
      have erasedSubset : family.erase token ⊆ seed :=
        Finset.subset_insert_iff.mp familySubset
      have erasedIndependent : closure.Independent (family.erase token) :=
        familyIndependent.mono (Finset.erase_subset token family)
      have erasedCard : (family.erase token).card = closure.rank seed := by
        have erasedCardSucc :
            (family.erase token).card + 1 = closure.rank seed + 1 := by
          rw [Finset.card_erase_add_one tokenInFamily, familyCard, rankSucc]
        omega
      have seedSubsetClosure : seed ⊆ closure.close (family.erase token) :=
        rank_witness_spans_seed closure seed (family.erase token)
          erasedSubset erasedIndependent erasedCard
      have generatedByErased : token ∈ closure.close (family.erase token) := by
        have generatedByClosed :
            token ∈ closure.close (closure.close (family.erase token)) :=
          closure.monotone seedSubsetClosure generated
        simpa [closure.idempotent] using generatedByClosed
      exact familyIndependent token tokenInFamily generatedByErased
    · rcases closure.exists_independent_rank_witness seed with
        ⟨family, familySubset, familyIndependent, familyCard⟩
      have familyBound := closure.independent_card_le_rank
        (familySubset.trans (Finset.subset_insert token seed)) familyIndependent
      rw [familyCard] at familyBound
      exact familyBound

/-! Finite unions of elements already generated by the base preserve rank. -/
theorem rank_union_eq_of_subset_closure
    (closure : FinitaryDistinctionClosure Token)
    (base additions : Finset Token)
    (generated : ∀ token ∈ additions, token ∈ closure.close base) :
    closure.rank (base ∪ additions) = closure.rank base := by
  classical
  induction additions using Finset.induction_on with
  | empty => simp
  | @insert token additions tokenNotMember inductionHypothesis =>
      have tokenGenerated : token ∈ closure.close base :=
        generated token (by simp)
      have additionsGenerated :
          ∀ current ∈ additions, current ∈ closure.close base := by
        intro current currentMember
        exact generated current (by simp [currentMember])
      have inductionResult := inductionHypothesis additionsGenerated
      have tokenGeneratedByUnion :
          token ∈ closure.close (base ∪ additions) := by
        exact closure.monotone (by simp) tokenGenerated
      have unionIdentity :
          base ∪ insert token additions = insert token (base ∪ additions) := by
        ext current
        simp
      rw [unionIdentity, rank_insert_eq_of_generated closure
        (base ∪ additions) token tokenGeneratedByUnion, inductionResult]

/-!
The current exchange field therefore derives `BasisAugmentation`; it is not
needed to add that property to the closure structure.  The theorem keeps the
finite seed/subset arguments visible even though the cardinal proof works on
the two independent families themselves.
-/
theorem basisAugmentation_of_exchange
    (closure : FinitaryDistinctionClosure Token)
    (seed : Finset Token) :
    BasisAugmentation closure seed := by
  intro first second firstIndependent firstSubset secondIndependent secondSubset
    cardLt
  classical
  by_contra noAugment
  let additions := second \ first
  have additionsGenerated :
      ∀ token ∈ additions, token ∈ closure.close first := by
    intro token tokenInAdditions
    have tokenInSecond : token ∈ second :=
      (Finset.mem_sdiff.mp tokenInAdditions).1
    have tokenNotFirst : token ∉ first :=
      (Finset.mem_sdiff.mp tokenInAdditions).2
    by_contra tokenNotGenerated
    apply noAugment
    exact ⟨token, tokenInSecond, tokenNotFirst,
      firstIndependent.insert_of_not_generated tokenNotGenerated⟩
  have rankUnion :
      closure.rank (first ∪ additions) = closure.rank first :=
    rank_union_eq_of_subset_closure closure first additions additionsGenerated
  have secondSubsetUnion : second ⊆ first ∪ additions := by
    intro token tokenInSecond
    by_cases tokenInFirst : token ∈ first
    · exact Finset.mem_union.mpr (Or.inl tokenInFirst)
    · exact Finset.mem_union.mpr
        (Or.inr (Finset.mem_sdiff.mpr ⟨tokenInSecond, tokenInFirst⟩))
  have secondBound := closure.independent_card_le_rank
    secondSubsetUnion secondIndependent
  have firstRank : closure.rank first = first.card :=
    rank_eq_card_of_independent closure firstIndependent
  rw [rankUnion, firstRank] at secondBound
  exact (Nat.not_le_of_lt cardLt) secondBound

/-! The derived augmentation closes the maximal-family cardinality bridge
without asking callers to restate a second structural premise. -/
theorem maximalIndependent_card_unique_of_exchange
    (closure : FinitaryDistinctionClosure Token)
    (seed left right : Finset Token)
    (leftMaximal : MaximalIndependent closure seed left)
    (rightMaximal : MaximalIndependent closure seed right) :
    left.card = right.card := by
  exact maximalIndependent_card_unique_of_augmentation closure seed left right
    leftMaximal rightMaximal (basisAugmentation_of_exchange closure seed)

/-! The exchange field therefore supplies the finite dimension witness
directly: every maximal independent family in the seed has the canonical
closure-rank cardinality. -/
theorem rank_is_wellDefined_maximalIndependent_dimension_of_exchange
    (closure : FinitaryDistinctionClosure Token)
    (seed family : Finset Token)
    (maximal : MaximalIndependent closure seed family) :
    closure.rank seed = family.card := by
  exact rank_is_wellDefined_maximalIndependent_dimension closure seed family
    maximal (basisAugmentation_of_exchange closure seed)

end IntrinsicDimensionExchangeAugmentation

end OCKIndividuationMSpaceComposition
