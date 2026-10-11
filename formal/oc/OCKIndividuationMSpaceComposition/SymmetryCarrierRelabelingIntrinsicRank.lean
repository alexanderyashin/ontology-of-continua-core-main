import OCKIndividuationMSpaceComposition.SymmetryActionCorrespondence
import OCKIndividuationMSpaceComposition.SymmetryNativeReversalClosure
import OCKIndividuationMSpaceComposition.SymmetryCanonicalFiniteRankOrientationInvariant

namespace OCKIndividuationMSpaceComposition

universe uToken uIndex uCarrier uTargetCarrier

namespace PrimitiveDistinction

/-!
# Carrier relabeling at the conditional intrinsic-rank boundary

`NativeCarrierTransport.transportPermutation` is conjugation by a carrier
equivalence.  This file connects that object-level naturality to the explicit
`CardinalityRealization`/`ActionCorrespondence` boundary.  The resulting rank
invariance is conditional on the existing finite realization and semantic
correspondence interfaces; it is not a generic intrinsic-dimension theorem.

The orientation result at the end reuses the established fact that reversing
the displayed endpoints leaves each ambient pair swap unchanged.  Thus it is
presentation invariance, not an additional global action or coverage premise.
The countermodel `cardinality_only_does_not_supply_action_correspondence` in
`SymmetryActionCorrespondence` remains the boundary witness: cardinality alone
does not create the semantic edge used below.
-/

namespace NativeCarrierTransport

variable {Index : Type uIndex} {Carrier : Type uCarrier}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype Carrier] [DecidableEq Carrier]
variable {TargetCarrier : Type uTargetCarrier}
variable [Fintype TargetCarrier] [DecidableEq TargetCarrier]

/-! ## Conjugation is a monoid homomorphism -/

/-- Conjugation by a carrier equivalence preserves the permutation monoid
operation.  The proof is pointwise, so no unproved action law is introduced. -/
def transportPermutationHom
    (relabel : Carrier ≃ TargetCarrier) :
    Equiv.Perm Carrier →* Equiv.Perm TargetCarrier where
  toFun := transportPermutation relabel
  map_one' := by
    ext point
    simp [transportPermutation_apply]
  map_mul' := by
    intro first second
    ext point
    simp [transportPermutation_apply, Equiv.Perm.mul_apply]

@[simp] theorem transportPermutationHom_apply
    (relabel : Carrier ≃ TargetCarrier)
    (permutation : Equiv.Perm Carrier) :
    transportPermutationHom relabel permutation =
      transportPermutation relabel permutation :=
  rfl

@[simp] theorem transportPermutation_one
    (relabel : Carrier ≃ TargetCarrier) :
    transportPermutation relabel (1 : Equiv.Perm Carrier) = 1 := by
  ext point
  simp [transportPermutation_apply]

/-! ## Factor and finite-product naturality -/

theorem transport_maskFactor
    (relabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index → Bool) (index : Index) :
    transportPermutation relabel (family.maskFactor mask index) =
      (transportFamily relabel family).maskFactor mask index := by
  by_cases selected : mask index = true
  · simp only [DisjointDistinctionFamily.maskFactor, selected, if_true]
    exact transport_pairSwap relabel (family.distinction index)
  · simp [DisjointDistinctionFamily.maskFactor, selected]

theorem transport_maskPermutationProduct
    (relabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index → Bool) :
    transportPermutation relabel (family.maskPermutationProduct mask) =
      (transportFamily relabel family).maskPermutationProduct mask := by
  unfold DisjointDistinctionFamily.maskPermutationProduct
  change transportPermutationHom relabel
      ((Finset.univ : Finset Index).noncommProd
        (DisjointDistinctionFamily.maskFactor family mask)
        (family.maskFactor_pairwise_commute mask)) = _
  rw [Finset.map_noncommProd]
  apply Finset.noncommProd_congr rfl
  intro index _
  exact transport_maskFactor relabel family mask index

/-! The actual finite action rank is invariant under the conjugation bridge. -/

theorem transport_symmetryAlgebraLogRank
    (relabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier) :
    DisjointDistinctionFamily.symmetryAlgebraLogRank
        (transportFamily relabel family) =
      DisjointDistinctionFamily.symmetryAlgebraLogRank family := by
  rw [DisjointDistinctionFamily.symmetryAlgebraLogRank_eq_card,
    DisjointDistinctionFamily.symmetryAlgebraLogRank_eq_card]

end NativeCarrierTransport

namespace NativeIntrinsicRankBoundary

open IntrinsicFinitaryRank

variable {Token : Type uToken} [DecidableEq Token]
variable {Index : Type uIndex} {Carrier : Type uCarrier}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype Carrier] [DecidableEq Carrier]
variable {TargetCarrier : Type uTargetCarrier}
variable [Fintype TargetCarrier] [DecidableEq TargetCarrier]

/-! ## Transporting the explicit realization interface -/

/-- A carrier equivalence changes only the native family part of a
`CardinalityRealization`; the intrinsic closure and its seed are preserved. -/
def transportCardinalityRealization
    (relabel : Carrier ≃ TargetCarrier)
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier)) :
    CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := TargetCarrier) where
  closure := realization.closure
  seed := realization.seed
  family := NativeCarrierTransport.transportFamily relabel realization.family
  seedIndependent := realization.seedIndependent
  seed_card_eq_index_card := realization.seed_card_eq_index_card

@[simp] theorem transport_realization_closure_rank
    (relabel : Carrier ≃ TargetCarrier)
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier)) :
    (transportCardinalityRealization relabel realization).closure.rank
        (transportCardinalityRealization relabel realization).seed =
      realization.closure.rank realization.seed :=
  rfl

theorem transport_realization_native_rank
    (relabel : Carrier ≃ TargetCarrier)
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier)) :
    DisjointDistinctionFamily.symmetryAlgebraLogRank
        (transportCardinalityRealization relabel realization).family =
      DisjointDistinctionFamily.symmetryAlgebraLogRank realization.family := by
  exact NativeCarrierTransport.transport_symmetryAlgebraLogRank
    relabel realization.family

/-! ## Correspondence and action-rank transport -/

/-- Transport the explicitly supplied generator action by conjugation. -/
def transportTokenAction
    (relabel : Carrier ≃ TargetCarrier)
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier) :
    SeedGenerator (transportCardinalityRealization relabel realization) →
      Equiv.Perm TargetCarrier :=
  fun generator => NativeCarrierTransport.transportPermutation relabel
    (tokenAction ⟨generator.1, generator.2⟩)

/-! The generator subtype is unchanged by carrier transport, so the original
index equivalence can be reused without inventing a token relabeling. -/
noncomputable def transportActionCorrespondence
    (relabel : Carrier ≃ TargetCarrier)
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction) :
    ActionCorrespondence (transportCardinalityRealization relabel realization)
      (transportTokenAction relabel realization tokenAction) where
  generatorEquiv := correspondence.generatorEquiv
  action_eq_pairSwap := by
    intro generator
    change NativeCarrierTransport.transportPermutation relabel
        (tokenAction generator) =
      pairSwapEquiv
        (NativeCarrierTransport.transportDistinction relabel
          (realization.family.distinction
            (correspondence.generatorEquiv generator)))
    rw [correspondence.action_eq_pairSwap generator]
    exact NativeCarrierTransport.transport_pairSwap relabel
      (realization.family.distinction
        (correspondence.generatorEquiv generator))

theorem transport_correspondenceActionLogRank
    (relabel : Carrier ≃ TargetCarrier)
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction) :
    correspondenceActionLogRank
        (transportCardinalityRealization relabel realization)
        (transportTokenAction relabel realization tokenAction)
        (transportActionCorrespondence relabel realization tokenAction correspondence) =
      correspondenceActionLogRank realization tokenAction correspondence := by
  rw [correspondenceActionLogRank_eq_native,
    correspondenceActionLogRank_eq_native]
  exact NativeCarrierTransport.transport_symmetryAlgebraLogRank
    relabel realization.family

/-- The transported action rank and the original intrinsic rank agree through
the explicit correspondence interface. -/
theorem transport_correspondenceActionLogRank_eq_intrinsic_rank
    (relabel : Carrier ≃ TargetCarrier)
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction) :
    correspondenceActionLogRank
        (transportCardinalityRealization relabel realization)
        (transportTokenAction relabel realization tokenAction)
        (transportActionCorrespondence relabel realization tokenAction correspondence) =
      realization.closure.rank realization.seed := by
  rw [correspondenceActionLogRank_eq_intrinsic_rank]
  rfl

/-! ## Orientation reversal is the already-proved presentation symmetry -/

def reverseLabelsCardinalityRealization
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier)) :
    CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier) where
  closure := realization.closure
  seed := realization.seed
  family := realization.family.reverseLabelsFamily
  seedIndependent := realization.seedIndependent
  seed_card_eq_index_card := realization.seed_card_eq_index_card

def reverseLabelsActionCorrespondence
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction) :
    ActionCorrespondence (reverseLabelsCardinalityRealization realization)
      tokenAction where
  generatorEquiv := correspondence.generatorEquiv
  action_eq_pairSwap := by
    intro generator
    rw [correspondence.action_eq_pairSwap generator]
    exact (DisjointDistinctionFamily.reverseLabelsFamily_pairSwapEquiv
      realization.family (correspondence.generatorEquiv generator)).symm

theorem reverseLabels_correspondenceActionLogRank
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction) :
    correspondenceActionLogRank
        (reverseLabelsCardinalityRealization realization)
        tokenAction
        (reverseLabelsActionCorrespondence realization tokenAction correspondence) =
      correspondenceActionLogRank realization tokenAction correspondence := by
  rw [correspondenceActionLogRank_eq_native,
    correspondenceActionLogRank_eq_native]
  exact DisjointDistinctionFamily.reverseLabelsFamily_symmetryAlgebraLogRank
    realization.family

end NativeIntrinsicRankBoundary

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
