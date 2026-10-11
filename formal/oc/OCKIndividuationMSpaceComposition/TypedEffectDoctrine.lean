import OCKIndividuationMSpaceComposition.OperatorTransport

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

universe uA uB uC uD

/-!
# Typed effect doctrine: a conservative common interface

This module is an OC-facing adapter over the existing structural operator
language, not a second effect calculus.  It gives OC one minimal typed
interface over established deterministic, relational and weighted surfaces.
Quantitative kernels retain their weights in the interface; their support
relation is explicitly a forgetting map.

The stochastic normalization law is a supplied domain/model contract.  OC
does not infer it from a relation, nor does it infer independence, stationarity
or a causal interpretation from normalized weights.
-/

/-- A finite stochastic transition kernel with rational masses. -/
structure FiniteStochasticEffect
    (Source : Type uA)
    (Target : Type uB)
    [Fintype Target] where
  mass : Source → Target → ℚ
  nonnegative : ∀ source target, 0 ≤ mass source target
  normalized : ∀ source, Finset.univ.sum (mass source) = 1

namespace FiniteStochasticEffect

/-- The possibilistic support of a finite stochastic kernel. -/
def support
    {Source : Type uA}
    {Target : Type uB}
    [Fintype Target]
    (effect : FiniteStochasticEffect Source Target) :
    RelOperator Source Target :=
  fun source target => 0 < effect.mass source target

/-- Support records exactly which weights are positive, but no magnitudes. -/
theorem support_iff_positive_mass
    {Source : Type uA}
    {Target : Type uB}
    [Fintype Target]
    (effect : FiniteStochasticEffect Source Target)
    (source : Source) (target : Target) :
    effect.support source target ↔ 0 < effect.mass source target :=
  Iff.rfl

end FiniteStochasticEffect

/-- The common typed effect surface.  `quantitative = none` is intentional for
pure deterministic or relational effects; `some weights` must agree exactly
with the declared support. -/
structure TypedEffectInterface (Source : Type uA) (Target : Type uB) where
  support : RelOperator Source Target
  quantitative : Option (Source → Target → ℚ)
  quantitative_support_exact : ∀ weights,
    quantitative = some weights →
    ∀ source target, support source target ↔ 0 < weights source target

/-- A deterministic transition embeds faithfully as a support effect. -/
def deterministicTypedEffect
    {Source : Type uA}
    {Target : Type uB}
    (step : Source → Target) : TypedEffectInterface Source Target where
  support := deterministicAsRel step
  quantitative := none
  quantitative_support_exact := by
    intro weights impossible
    cases impossible

/-- A relational transition is already a typed effect at the support level. -/
def relationalTypedEffect
    {Source : Type uA}
    {Target : Type uB}
    (step : RelOperator Source Target) : TypedEffectInterface Source Target where
  support := step
  quantitative := none
  quantitative_support_exact := by
    intro weights impossible
    cases impossible

/-- A finite stochastic kernel enters the effect interface without dropping its
quantitative mass function. -/
def FiniteStochasticEffect.toTypedEffectInterface
    {Source : Type uA}
    {Target : Type uB}
    [Fintype Target]
    (effect : FiniteStochasticEffect Source Target) :
    TypedEffectInterface Source Target where
  support := effect.support
  quantitative := some effect.mass
  quantitative_support_exact := by
    intro weights sameWeights source target
    have massEq : effect.mass = weights := Option.some.inj sameWeights
    rw [← massEq]
    exact Iff.rfl

/-- Parallel composition of independent typed support effects.  Independence
is a domain premise about interpretation; this definition only gives the exact
product support relation. -/
def parallelRelEffect
    {A : Type uA} {B : Type uB}
    {C : Type uC} {D : Type uD}
    (left : RelOperator A B)
    (right : RelOperator C D) :
    RelOperator (A × C) (B × D) :=
  fun source target => left source.1 target.1 ∧ right source.2 target.2

theorem parallelRelEffect_iff
    {A : Type uA} {B : Type uB}
    {C : Type uC} {D : Type uD}
    (left : RelOperator A B)
    (right : RelOperator C D)
    (source : A × C) (target : B × D) :
    parallelRelEffect left right source target ↔
      left source.1 target.1 ∧ right source.2 target.2 :=
  Iff.rfl

/-- Feedback semantics at finite horizon is ordinary reflexive-transitive
closure of an endomorphic support effect. -/
abbrev feedbackClosure
    {State : Type uA}
    (effect : RelOperator State State) : RelOperator State State :=
  Relation.ReflTransGen effect

theorem feedbackClosure_refl
    {State : Type uA}
    (effect : RelOperator State State)
    (state : State) :
    feedbackClosure effect state state :=
  Relation.ReflTransGen.refl

theorem feedbackClosure_contains_step
    {State : Type uA}
    (effect : RelOperator State State)
    {source target : State}
    (step : effect source target) :
    feedbackClosure effect source target :=
  Relation.ReflTransGen.tail Relation.ReflTransGen.refl step

theorem feedbackClosure_trans
    {State : Type uA}
    {effect : RelOperator State State}
    {first middle last : State}
    (firstMiddle : feedbackClosure effect first middle)
    (middleLast : feedbackClosure effect middle last) :
    feedbackClosure effect first last :=
  Relation.ReflTransGen.trans firstMiddle middleLast

/-- Context transport of effects is exact direct-image transport of their
declared support relations.  Quantitative transport needs an additional
weight-preservation theorem and is deliberately not inferred here. -/
abbrev ExactEffectTransport
    {Source : Type uA}
    {Target : Type uB}
    {Source' : Type uC}
    {Target' : Type uD}
    (sourceEffect : TypedEffectInterface Source Target)
    (targetEffect : TypedEffectInterface Source' Target') :=
  ExactRelTransport sourceEffect.support targetEffect.support

theorem ExactEffectTransport.preserves_support
    {Source : Type uA}
    {Target : Type uB}
    {Source' : Type uC}
    {Target' : Type uD}
    {sourceEffect : TypedEffectInterface Source Target}
    {targetEffect : TypedEffectInterface Source' Target'}
    (transport : ExactEffectTransport sourceEffect targetEffect)
    {source : Source} {target : Target}
    (edge : sourceEffect.support source target) :
    targetEffect.support (transport.sourceMap source) (transport.targetMap target) :=
  transport.preserves edge

/-- Quantitative support forgetting is not faithful even before probability
normalization is imposed.  Consequently a support-only transport cannot be
promoted to a stochastic/effect-magnitude transport without a further law. -/
theorem support_forgetting_is_not_quantitatively_faithful :
    ¬ Function.Injective (@weightedSupport Unit Bool) :=
  quantitativeSupport_not_faithful

end OCKIndividuationMSpaceComposition
