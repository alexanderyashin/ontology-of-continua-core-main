import OCKIndividuationMSpaceComposition.SymmetryNativeActionRank

namespace OCKIndividuationMSpaceComposition

universe uToken uIndex uCarrier

namespace PrimitiveDistinction.NativeIntrinsicRankBoundary

open IntrinsicFinitaryRank

variable {Token : Type uToken} [DecidableEq Token]
variable {Index : Type uIndex} {Carrier : Type uCarrier}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype Carrier] [DecidableEq Carrier]

/-!
# Generator-to-native-action correspondence

`CardinalityRealization` is intentionally only a rank-cardinality interface:
it records an independent intrinsic seed and a native disjoint family with the
same finite cardinality.  It does not say that a token in the seed denotes a
particular native reversal.

`ActionCorrespondence` adds exactly that missing semantic edge.  Its action is
an externally supplied action on seed generators, and the structure requires
an explicit equivalence from those generators to the native family indices
plus equality with the corresponding ambient pair swap.  Thus no
token-to-permutation map, generator order, or closure compatibility is hidden
in a definition.

The resulting theorems are deliberately conditional.  They show that the
action presentation and the intrinsic finite rank agree once this
correspondence is supplied; they do not derive the correspondence from a
bare distinction, a cardinality equality, or the native permutation algebra.
-/

abbrev SeedGenerator
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier)) :=
  {token // token ∈ realization.seed}

/-! An explicit semantic edge from intrinsic generators to native reversals. -/
structure ActionCorrespondence
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier) where
  generatorEquiv : SeedGenerator realization ≃ Index
  action_eq_pairSwap : ∀ generator,
    tokenAction generator =
      pairSwapEquiv
        (realization.family.distinction (generatorEquiv generator))

/-! The correspondence carries the independent seed and native index family
through the same finite cardinality, but the equality is proved from the
explicit equivalence rather than being silently inferred from labels. -/
theorem seed_card_eq_index_card_of_actionCorrespondence
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction) :
    realization.seed.card = Fintype.card Index := by
  calc
    realization.seed.card =
        Fintype.card (SeedGenerator realization) := by
          symm
          exact Fintype.card_coe realization.seed
    _ = Fintype.card Index := Fintype.card_congr correspondence.generatorEquiv

/-! A factor using the supplied generator action, indexed by the native
family's index type. -/
noncomputable def correspondenceActionFactor
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction)
    (mask : Index → Bool) (index : Index) : Equiv.Perm Carrier :=
  if mask index = true then
    tokenAction (correspondence.generatorEquiv.symm index)
  else 1

theorem correspondenceActionFactor_eq_maskFactor
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction)
    (mask : Index → Bool) (index : Index) :
    correspondenceActionFactor realization tokenAction correspondence mask index =
      realization.family.maskFactor mask index := by
  by_cases selected : mask index = true
  · simp only [correspondenceActionFactor,
      DisjointDistinctionFamily.maskFactor, selected, if_true]
    simpa using correspondence.action_eq_pairSwap
      (correspondence.generatorEquiv.symm index)
  · simp [correspondenceActionFactor,
      DisjointDistinctionFamily.maskFactor, selected]

theorem correspondenceActionFactor_pairwise_commute
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction)
    (mask : Index → Bool) :
    ((Finset.univ : Finset Index) : Set Index).Pairwise
      (fun first second =>
        Commute
          (correspondenceActionFactor realization tokenAction correspondence mask first)
          (correspondenceActionFactor realization tokenAction correspondence mask second)) := by
  simpa only [correspondenceActionFactor_eq_maskFactor realization tokenAction
      correspondence mask] using
    realization.family.maskFactor_pairwise_commute mask

/-! Product of the explicitly supplied generator actions. -/
noncomputable def correspondenceMaskProduct
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction)
    (mask : Index → Bool) : Equiv.Perm Carrier :=
  (Finset.univ : Finset Index).noncommProd
    (correspondenceActionFactor realization tokenAction correspondence mask)
    (correspondenceActionFactor_pairwise_commute
      realization tokenAction correspondence mask)

theorem correspondenceMaskProduct_eq_native
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction)
    (mask : Index → Bool) :
    correspondenceMaskProduct realization tokenAction correspondence mask =
      realization.family.maskPermutationProduct mask := by
  unfold correspondenceMaskProduct DisjointDistinctionFamily.maskPermutationProduct
  apply Finset.noncommProd_congr rfl
  intro index _
  exact correspondenceActionFactor_eq_maskFactor
    realization tokenAction correspondence mask index

/-! The action-range cardinality is now the native Boolean action range. -/
noncomputable def correspondenceActionLogRank
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction) : Nat :=
  Nat.log 2 (Set.ncard (Set.range
    (correspondenceMaskProduct realization tokenAction correspondence)))

theorem correspondenceActionLogRank_eq_native
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction) :
    correspondenceActionLogRank realization tokenAction correspondence =
      DisjointDistinctionFamily.symmetryAlgebraLogRank realization.family := by
  have ranges :
      Set.range (correspondenceMaskProduct realization tokenAction correspondence) =
        Set.range realization.family.maskPermutationProduct := by
    ext transformation
    constructor
    · rintro ⟨mask, rfl⟩
      exact ⟨mask, (correspondenceMaskProduct_eq_native
        realization tokenAction correspondence mask).symm⟩
    · rintro ⟨mask, rfl⟩
      exact ⟨mask, correspondenceMaskProduct_eq_native
        realization tokenAction correspondence mask⟩
  unfold correspondenceActionLogRank
    DisjointDistinctionFamily.symmetryAlgebraLogRank
  rw [ranges]

/-! Main bridge: intrinsic closure rank agrees with the action rank only after
the explicit generator/action correspondence has been supplied. -/
theorem intrinsic_rank_eq_correspondence_action_log_rank
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction) :
    realization.closure.rank realization.seed =
      correspondenceActionLogRank realization tokenAction correspondence := by
  rw [correspondenceActionLogRank_eq_native
    realization tokenAction correspondence]
  exact intrinsic_rank_eq_native_action_log_rank realization

/-! The same bridge in the opposite direction is useful when the action rank
is the observed quantity. -/
theorem correspondenceActionLogRank_eq_intrinsic_rank
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction) :
    correspondenceActionLogRank realization tokenAction correspondence =
      realization.closure.rank realization.seed := by
  exact (intrinsic_rank_eq_correspondence_action_log_rank
    realization tokenAction correspondence).symm

/-! Realization-independence is now explicit: two externally supplied action
maps on the same intrinsic realization may differ as functions or as
correspondence witnesses, but if both satisfy the correspondence interface,
their Boolean action ranks are equal.  Both are also equal to the same
intrinsic finite rank and to the same native action rank.  The hypothesis is
not a choice of labels; it is the pair of explicit semantic correspondences.
Without those correspondences, the concrete identity-action countermodel
below still satisfies the cardinality interface but has no such conclusion. -/
theorem correspondenceActionLogRank_realization_independent
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (leftAction : SeedGenerator realization → Equiv.Perm Carrier)
    (leftCorrespondence : ActionCorrespondence realization leftAction)
    (rightAction : SeedGenerator realization → Equiv.Perm Carrier)
    (rightCorrespondence : ActionCorrespondence realization rightAction) :
    correspondenceActionLogRank realization leftAction leftCorrespondence =
        correspondenceActionLogRank realization rightAction rightCorrespondence ∧
      correspondenceActionLogRank realization leftAction leftCorrespondence =
        realization.closure.rank realization.seed ∧
      correspondenceActionLogRank realization rightAction rightCorrespondence =
        DisjointDistinctionFamily.symmetryAlgebraLogRank realization.family := by
  refine ⟨?_, ?_, ?_⟩
  · rw [correspondenceActionLogRank_eq_native
      realization leftAction leftCorrespondence,
    correspondenceActionLogRank_eq_native
      realization rightAction rightCorrespondence]
  · exact correspondenceActionLogRank_eq_intrinsic_rank
      realization leftAction leftCorrespondence
  · exact correspondenceActionLogRank_eq_native
      realization rightAction rightCorrespondence

/-! ## Boundary witness: cardinality does not supply correspondence

The following finite model keeps the previous cardinality interface valid but
assigns every intrinsic generator the identity permutation.  The native
one-coordinate family is a nontrivial transposition, so no
`ActionCorrespondence` can exist for that supplied action.  This is a concrete
countermodel to reading semantic generator/action correspondence out of rank
cardinality alone.
-/

def identityFinitaryClosure : FinitaryDistinctionClosure (Fin 1) where
  close := id
  extensive := by
    intro seed token tokenMember
    exact tokenMember
  monotone := by
    intro first second subset token tokenMember
    exact subset tokenMember
  idempotent := by
    intro seed
    rfl
  exchange := by
    intro seed first second firstGenerated firstNotGenerated
    change first ∈ insert second seed at firstGenerated
    change first ∉ seed at firstNotGenerated
    rcases Finset.mem_insert.mp firstGenerated with firstEq | firstMember
    · subst first
      simp
    · exact (firstNotGenerated firstMember).elim

def identitySeed : Finset (Fin 1) := {0}

def oneCoordinateFamily :
    DisjointDistinctionFamily (Fin 1) (Fin 2) where
  distinction := fun _ =>
    ({ first := (0 : Fin 2), second := (1 : Fin 2), separated := by decide } :
      PrimitiveDistinction (Fin 2))
  supportsDisjoint := by
    intro first second different
    exact (different (Subsingleton.elim first second)).elim

def cardinalityOnlyRealization :
    CardinalityRealization (Token := Fin 1)
      (Index := Fin 1) (Carrier := Fin 2) where
  closure := identityFinitaryClosure
  seed := identitySeed
  family := oneCoordinateFamily
  seedIndependent := by
    intro token tokenMember
    rcases Finset.mem_singleton.mp tokenMember with rfl
    simp [identityFinitaryClosure, identitySeed]
  seed_card_eq_index_card := by
    decide

def constantIdentityAction : SeedGenerator cardinalityOnlyRealization → Equiv.Perm (Fin 2) :=
  fun _ => 1

theorem constantIdentityAction_no_correspondence :
    ¬ Nonempty (ActionCorrespondence cardinalityOnlyRealization
      constantIdentityAction) := by
  rintro ⟨correspondence⟩
  have actionEquality := correspondence.action_eq_pairSwap
    (correspondence.generatorEquiv.symm (0 : Fin 1))
  have actionAtZero := congrArg
    (fun permutation : Equiv.Perm (Fin 2) => permutation (0 : Fin 2))
    actionEquality
  have actionAtZero' :
      (0 : Fin 2) =
        (oneCoordinateFamily.distinction (0 : Fin 1)).pairSwap (0 : Fin 2) := by
    simpa [constantIdentityAction, cardinalityOnlyRealization,
      oneCoordinateFamily, pairSwapEquiv] using actionAtZero
  have moved0 :
      (oneCoordinateFamily.distinction (0 : Fin 1)).pairSwap (0 : Fin 2) = 1 := by
    simpa [oneCoordinateFamily] using
      (PrimitiveDistinction.pairSwap_first
        (oneCoordinateFamily.distinction (0 : Fin 1)))
  have impossible : (0 : Fin 2) = 1 := actionAtZero'.trans moved0
  exact (by decide : (0 : Fin 2) ≠ 1) impossible

theorem cardinality_only_does_not_supply_action_correspondence :
    ∃ (realization : CardinalityRealization (Token := Fin 1)
          (Index := Fin 1) (Carrier := Fin 2))
      (tokenAction : SeedGenerator realization → Equiv.Perm (Fin 2)),
      ¬ Nonempty (ActionCorrespondence realization tokenAction) := by
  exact ⟨cardinalityOnlyRealization, constantIdentityAction,
    constantIdentityAction_no_correspondence⟩

end PrimitiveDistinction.NativeIntrinsicRankBoundary

end OCKIndividuationMSpaceComposition
