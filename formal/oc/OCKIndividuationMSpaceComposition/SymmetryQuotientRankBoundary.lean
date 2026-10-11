import OCKIndividuationMSpaceComposition.SymmetryFinitaryRankComposition
import OCKIndividuationMSpaceComposition.SymmetryFiniteCubeRankRealization
import OCKIndividuationMSpaceComposition.SymmetryExchangeAugmentation

namespace OCKIndividuationMSpaceComposition

namespace IntrinsicFinitaryRank

/-!
# Quotient / identification boundary for finite intrinsic rank

The finite rank calculus has a sharp and useful quotient boundary.  A map of
tokens can identify observations, so the rank of the mapped seed cannot exceed
the source cardinality (and, for an independent source seed, cannot exceed its
source rank).  Equality is not automatic: a concrete Boolean two-coordinate
family collapsed to one coordinate loses one rank unit.

This is deliberately a boundary theorem, not a definition of an OC quotient.
No closure homomorphism or exchange law for the target is smuggled into the
map.  To obtain equality one must separately prove that the map is injective on
the relevant family and that the target image is independent.
-/

universe uSource uTarget

variable {Source Target : Type*} [DecidableEq Source] [DecidableEq Target]

/-! ## General finite image bounds -/

/-- Any target rank measured on the image of a finite source seed is bounded by
the number of source tokens.  This is a pure finite-image bound and does not
identify the target closure with the source closure. -/
theorem FinitaryDistinctionClosure.rank_image_le_source_card
    (targetClosure : FinitaryDistinctionClosure Target)
    (seed : Finset Source) (map : Source → Target) :
    targetClosure.rank (seed.image map) ≤ seed.card := by
  classical
  rcases targetClosure.exists_independent_rank_witness (seed.image map) with
    ⟨family, familySubset, independent, familyCard⟩
  rw [← familyCard]
  exact (Finset.card_le_card familySubset).trans
    (Finset.card_image_le)

/-- If the source seed is independent, a finite identification cannot increase
its intrinsic rank.  The source rank is used only through the proved
independent-witness lower bound; no source/target closure compatibility is
assumed. -/
theorem FinitaryDistinctionClosure.rank_image_le_source_rank_of_independent
    (sourceClosure : FinitaryDistinctionClosure Source)
    (targetClosure : FinitaryDistinctionClosure Target)
    (seed : Finset Source) (map : Source → Target)
    (sourceIndependent : sourceClosure.Independent seed) :
    targetClosure.rank (seed.image map) ≤ sourceClosure.rank seed := by
  have sourceCardBound : seed.card ≤ sourceClosure.rank seed :=
    sourceClosure.independent_card_le_rank (subset_refl _) sourceIndependent
  exact (rank_image_le_source_card targetClosure seed map).trans sourceCardBound

/-- Equality after identification requires explicit injectivity on the seed and
an independent target image.  This is the exact finite realization criterion
for recovering the source cardinal rank. -/
theorem FinitaryDistinctionClosure.rank_image_eq_source_rank_of_independent
    (sourceClosure : FinitaryDistinctionClosure Source)
    (targetClosure : FinitaryDistinctionClosure Target)
    (seed : Finset Source) (map : Source → Target)
    (sourceIndependent : sourceClosure.Independent seed)
    (mapInjective : Set.InjOn map (↑seed : Set Source))
    (targetImageIndependent :
      targetClosure.Independent (seed.image map)) :
    targetClosure.rank (seed.image map) = sourceClosure.rank seed := by
  classical
  have sourceRank : sourceClosure.rank seed = seed.card := by
    apply Nat.le_antisymm
    · unfold FinitaryDistinctionClosure.rank
      apply Finset.sup_le
      intro family familyMember
      exact Finset.card_le_card
        (Finset.mem_powerset.mp (Finset.mem_filter.mp familyMember).1)
    · exact sourceClosure.independent_card_le_rank
        (subset_refl _) sourceIndependent
  have imageCard : (seed.image map).card = seed.card := by
    exact Finset.card_image_iff.mpr mapInjective
  have targetRank : targetClosure.rank (seed.image map) =
      (seed.image map).card := by
    apply Nat.le_antisymm
    · unfold FinitaryDistinctionClosure.rank
      apply Finset.sup_le
      intro family familyMember
      exact Finset.card_le_card
        (Finset.mem_powerset.mp (Finset.mem_filter.mp familyMember).1)
    · exact targetClosure.independent_card_le_rank
        (subset_refl _) targetImageIndependent
  rw [targetRank, imageCard, sourceRank]

/-- A collision on the finite source seed forces strict rank loss.  This is the
exact contrapositive boundary of the equality theorem: if two distinct source
tokens are identified, the target image has strictly smaller cardinality and
therefore strictly smaller rank than an independent source seed. -/
theorem FinitaryDistinctionClosure.rank_image_lt_source_rank_of_collision
    (sourceClosure : FinitaryDistinctionClosure Source)
    (targetClosure : FinitaryDistinctionClosure Target)
    (seed : Finset Source) (map : Source → Target)
    (sourceIndependent : sourceClosure.Independent seed)
    (collision : ∃ first ∈ seed, ∃ second ∈ seed,
      first ≠ second ∧ map first = map second) :
    targetClosure.rank (seed.image map) < sourceClosure.rank seed := by
  have imageCardNe : (seed.image map).card ≠ seed.card := by
    intro imageCardEq
    have mapInjective : Set.InjOn map (↑seed : Set Source) :=
      Finset.card_image_iff.mp imageCardEq
    rcases collision with ⟨first, firstMember, second, secondMember,
      firstNeSecond, mappedEqual⟩
    exact firstNeSecond
      (mapInjective firstMember secondMember mappedEqual)
  have imageCardLt : (seed.image map).card < seed.card :=
    Nat.lt_of_le_of_ne Finset.card_image_le imageCardNe
  have targetRankBound : targetClosure.rank (seed.image map) ≤
      (seed.image map).card :=
    IntrinsicDimensionExchangeAugmentation.rank_le_card targetClosure
      (seed.image map)
  have sourceRank : sourceClosure.rank seed = seed.card :=
    IntrinsicDimensionExchangeAugmentation.rank_eq_card_of_independent
      sourceClosure sourceIndependent
  calc
    targetClosure.rank (seed.image map) ≤ (seed.image map).card :=
      targetRankBound
    _ < seed.card := imageCardLt
    _ = sourceClosure.rank seed := sourceRank.symm

/-! ## Explicit strict-loss countermodel -/

open BooleanCompositionRank
open FiniteCubeRankRealization

/-- A deliberately non-injective identification of all two-coordinate Boolean
tokens with the first one-coordinate token.  It is a finite quotient witness,
not an OC-native quotient definition. -/
noncomputable def collapseTwoCoordinates
    (token : BooleanMask (Fin 2)) : BooleanMask (Fin 1) :=
  coordinateMask (Index := Fin 1) 0

theorem collapseTwoCoordinates_full_family :
    (fullCoordinateFamily (Index := Fin 2)).image collapseTwoCoordinates =
      ({coordinateMask (Index := Fin 1) 0} : Finset (BooleanMask (Fin 1))) := by
  classical
  ext token
  constructor
  · intro tokenMember
    rcases Finset.mem_image.mp tokenMember with ⟨source, _, rfl⟩
    simp [collapseTwoCoordinates]
  · intro tokenMember
    have tokenEq : token = coordinateMask (Index := Fin 1) 0 := by
      simpa using tokenMember
    subst token
    refine Finset.mem_image.mpr ⟨coordinateMask (Index := Fin 2) 0, ?_, rfl⟩
    exact Finset.mem_image.mpr ⟨0, Finset.mem_univ _, rfl⟩

theorem collapseTwoCoordinates_target_singleton_independent :
    booleanGeneratedClosure.Independent
      ({coordinateMask (Index := Fin 1) 0} :
        Finset (BooleanMask (Fin 1))) := by
  classical
  apply fullCoordinateFamily_independent.mono
  intro token tokenMember
  have tokenEq : token = coordinateMask (Index := Fin 1) 0 := by
    simpa using tokenMember
  subst token
  exact Finset.mem_image.mpr ⟨0, Finset.mem_univ _, rfl⟩

/-- Identifying the two coordinate directions strictly lowers the Boolean
rank: the source has rank two while the quotient image has rank one. -/
theorem collapseTwoCoordinates_strict_rank_loss :
    booleanGeneratedClosure.rank
        ((fullCoordinateFamily (Index := Fin 2)).image collapseTwoCoordinates) <
      booleanGeneratedClosure.rank (fullCoordinateFamily (Index := Fin 2)) := by
  classical
  apply FinitaryDistinctionClosure.rank_image_lt_source_rank_of_collision
    (sourceClosure :=
      BooleanCompositionRank.booleanGeneratedClosure
        (Token := BooleanMask (Fin 2)))
    (targetClosure :=
      BooleanCompositionRank.booleanGeneratedClosure
        (Token := BooleanMask (Fin 1)))
    (seed := fullCoordinateFamily (Index := Fin 2))
    (map := collapseTwoCoordinates)
    (sourceIndependent := fullCoordinateFamily_independent)
  refine ⟨coordinateMask (Index := Fin 2) 0, ?_,
    coordinateMask (Index := Fin 2) 1, ?_, ?_, rfl⟩
  · exact Finset.mem_image.mpr ⟨0, Finset.mem_univ _, rfl⟩
  · exact Finset.mem_image.mpr ⟨1, Finset.mem_univ _, rfl⟩
  · intro equal
    exact Fin.zero_ne_one (coordinateMask_injective equal)

end IntrinsicFinitaryRank

end OCKIndividuationMSpaceComposition
