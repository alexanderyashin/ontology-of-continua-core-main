import OCKIndividuationMSpaceComposition.SymmetryJointCompositionBoundary
import OCKIndividuationMSpaceComposition.SymmetryExchangeAugmentation

namespace OCKIndividuationMSpaceComposition

universe uToken

namespace OCExchangeProducingComposition

open JointCompositionBoundary
open IntrinsicDimensionInterface
open IntrinsicDimensionExchangeAugmentation
open IntrinsicFinitaryRank

variable {Token : Type uToken} [DecidableEq Token]

/-!
# Exchange-producing composition as an explicit OC interface

The current OC vocabulary contains singleton-generated causal closure and a
separate joint-composition boundary.  Neither one supplies the exchange law
needed by finite intrinsic rank.  This file therefore isolates the smallest
useful semantic interface for the missing step:

* `generated` is the OC composition relation;
* `close` is its finite materialization, linked by `generated_iff_mem_close`;
* `composition` and `pair_rule` witness a genuine two-root composition;
* `generated_exchange` is an independent semantic premise, not a consequence
  of the preceding fields and not hidden in the definition of rank.

The resulting `toFinitaryClosure` is a derived object.  Existing finite
exchange/rank theorems then apply without importing vectors, coordinates or a
generic matroid claim.  The two-root countermodel at the end shows that joint
composition plus ordinary closure laws do not manufacture this premise.
-/

/-! ## The explicit composition-to-closure interface -/

/-- A finite OC composition model whose exchange law is supplied at the
semantic relation level.  `generated_exchange` is deliberately a field of
evidence: it is not part of `close`'s definition and is not inferred from
`pair_rule`. -/
structure Model where
  composition : JointComposition Token
  generated : Finset Token → Token → Prop
  close : Finset Token → Finset Token
  generated_iff_mem_close : ∀ seed token,
    generated seed token ↔ token ∈ close seed
  extensive : ∀ seed, seed ⊆ close seed
  monotone : ∀ ⦃first second : Finset Token⦄,
    first ⊆ second → close first ⊆ close second
  idempotent : ∀ seed, close (close seed) = close seed
  pair_rule : ∀ (first second : Token),
    generated ({first, second} : Finset Token)
      (composition.combine first second)
  generated_exchange : ∀ (seed : Finset Token) (first second : Token),
    generated (insert second seed) first →
    ¬ generated seed first →
    generated (insert first seed) second

/-! ## The genuine joint-composition witness -/

theorem composition_target_generated
    (model : Model) (first second : Token) :
    model.generated ({first, second} : Finset Token)
      (model.composition.combine first second) := by
  exact model.pair_rule first second

theorem composition_target_mem_close
    (model : Model) (first second : Token) :
    model.composition.combine first second ∈
      model.close ({first, second} : Finset Token) := by
  exact (model.generated_iff_mem_close _ _).mp
    (composition_target_generated model first second)

/-! ## Transfer to the existing exchange-bearing finite closure -/

/-- The semantic composition relation induces the existing finitary closure.
The exchange field is proved from `generated_exchange` and the exact
generated/closed-membership correspondence; it is not copied from a target
closure interface. -/
def toFinitaryClosure {Token : Type uToken} [DecidableEq Token]
    (model : Model (Token := Token)) :
      IntrinsicFinitaryRank.FinitaryDistinctionClosure Token where
  close := model.close
  extensive := model.extensive
  monotone := model.monotone
  idempotent := model.idempotent
  exchange := by
    intro seed first second firstGenerated firstNotGenerated
    apply (model.generated_iff_mem_close _ _).mp
    apply model.generated_exchange seed first second
    · exact (model.generated_iff_mem_close _ _).mpr firstGenerated
    · intro generated
      apply firstNotGenerated
      exact (model.generated_iff_mem_close _ _).mp generated

theorem generated_iff_toClosure_mem
    (model : Model) (seed : Finset Token) (token : Token) :
    model.generated seed token ↔
      token ∈ (toFinitaryClosure model).close seed := by
  exact model.generated_iff_mem_close seed token

/-! ## Conditional rank and basis consequences -/

theorem rank_insert_eq_add_one_of_not_generated
    (model : Model) (seed : Finset Token) (token : Token)
    (notGenerated : ¬ model.generated seed token) :
    (toFinitaryClosure model).rank (insert token seed) =
      (toFinitaryClosure model).rank seed + 1 := by
  apply FinitaryDistinctionClosure.rank_insert_eq_add_one_of_not_generated
  intro generated
  apply notGenerated
  exact (model.generated_iff_mem_close _ _).mpr generated

theorem maximalIndependent_card_unique
    (model : Model) (seed left right : Finset Token)
    (leftMaximal : MaximalIndependent (toFinitaryClosure model) seed left)
    (rightMaximal : MaximalIndependent (toFinitaryClosure model) seed right) :
    left.card = right.card := by
  exact maximalIndependent_card_unique_of_exchange
    (toFinitaryClosure model) seed left right leftMaximal rightMaximal

theorem rank_is_wellDefined_maximalIndependent
    (model : Model) (seed family : Finset Token)
    (maximal : MaximalIndependent (toFinitaryClosure model) seed family) :
    (toFinitaryClosure model).rank seed = family.card := by
  exact rank_is_wellDefined_maximalIndependent_dimension_of_exchange
    (toFinitaryClosure model) seed family maximal

/-! ## Sharp negative boundary -/

/-!
The following relation-level theorem is stronger than merely restating that
`twoRootClosure` fails `ExchangeLaw`: even if one tries to name a separate OC
`generated` relation, the exact closure semantics force the same failed
exchange instance.  The model already has extensive/monotone/idempotent
closure, a genuine two-root target, and unequal maximal-independent sizes.
Thus `pair_rule` plus ordinary closure laws cannot be promoted to the
exchange-producing interface above.
-/
theorem twoRoot_closure_has_no_exchange_generating_relation :
    ¬ ∃ generated : Finset TwoRootToken → TwoRootToken → Prop,
      (∀ seed token, generated seed token ↔
        token ∈ twoRootClosure seed) ∧
      (∀ (seed : Finset TwoRootToken) (first second : TwoRootToken),
        generated (insert second seed) first →
        ¬ generated seed first →
        generated (insert first seed) second) := by
  rintro ⟨generated, generatedSpec, generatedExchange⟩
  apply twoRootClosure_fails_exchange
  intro seed first second firstGenerated firstNotGenerated
  have generatedFirst : generated (insert second seed) first :=
    (generatedSpec _ _).mpr firstGenerated
  have notGeneratedFirst : ¬ generated seed first := by
    intro generatedToken
    apply firstNotGenerated
    exact (generatedSpec _ _).mp generatedToken
  have generatedSecond := generatedExchange seed first second
    generatedFirst notGeneratedFirst
  exact (generatedSpec _ _).mp generatedSecond

theorem twoRoot_joint_composition_is_not_exchange_producing :
    twoRootJointPremise.jointGenerated ({0, 1} : Finset TwoRootToken) 2 ∧
    ¬ ∃ generated : Finset TwoRootToken → TwoRootToken → Prop,
      (∀ seed token, generated seed token ↔
        token ∈ twoRootClosure seed) ∧
      (∀ (seed : Finset TwoRootToken) (first second : TwoRootToken),
        generated (insert second seed) first →
        ¬ generated seed first →
        generated (insert first seed) second) := by
  exact ⟨twoRoot_target_is_joint,
    twoRoot_closure_has_no_exchange_generating_relation⟩

/-! ## Decision boundary -/

/-!
`Model` makes the missing premise explicit and transfers it to the existing
finite exchange/rank machinery.  This is a conditional reduction, not a
derivation of exchange from primitive distinction, a local C₂/torsor, or a
joint pair witness.  The strongest current decision is therefore:

`CONDITIONAL_REDUCIBLE_IF_OC_GENERATED_EXCHANGE_IS_JUSTIFIED`.

The sole unresolved scientific obligation is to justify
`generated_exchange` (or an equivalent native action correspondence) from
the actual general OC composition semantics.  No generic intrinsic dimension
is claimed before that obligation is met.
-/

end OCExchangeProducingComposition

end OCKIndividuationMSpaceComposition
