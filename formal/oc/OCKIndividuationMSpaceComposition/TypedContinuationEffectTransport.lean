import OCKIndividuationMSpaceComposition.TypedEffectDoctrine
import OCKIndividuationMSpaceComposition.QuantitativeContextTransport

namespace OCKIndividuationMSpaceComposition

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame
  uA uB uC uD uE uF

/-!
# Joint transport of an evolving referent and a typed effect

`ContextCompatibility` transports a path witness; `ExactEffectTransport`
transports only the support of an effect.  Neither implies the other.  This
module packages the two certificates, proves that their package has identity
and associative composition at the observable maps, and adds the strictly
stronger quantitative law needed to transport effect magnitudes.

The construction is an OC adapter over ordinary relational and weighted
transport.  It does not infer causality, stochastic normalization,
independence, stationarity, or identifiability.
-/

/-- Exact quantitative transport is exact support transport plus an explicit
commuting law for the quantitative weights. -/
structure ExactQuantitativeEffectTransport
    {Source : Type uA} {Target : Type uB}
    {Source' : Type uC} {Target' : Type uD}
    (sourceEffect : TypedEffectInterface Source Target)
    (targetEffect : TypedEffectInterface Source' Target') where
  structural : ExactEffectTransport sourceEffect targetEffect
  sourceWeights : Source → Target → ℚ
  targetWeights : Source' → Target' → ℚ
  sourceQuantitative : sourceEffect.quantitative = some sourceWeights
  targetQuantitative : targetEffect.quantitative = some targetWeights
  preserves_weight : ∀ source target,
    targetWeights (structural.sourceMap source) (structural.targetMap target) =
      sourceWeights source target

namespace ExactQuantitativeEffectTransport

/-- Identity preserves both support and weights. -/
def identity
    {Source : Type uA} {Target : Type uB}
    (effect : TypedEffectInterface Source Target)
    (weights : Source → Target → ℚ)
    (quantitative : effect.quantitative = some weights) :
    ExactQuantitativeEffectTransport effect effect where
  structural := ExactRelTransport.identity effect.support
  sourceWeights := weights
  targetWeights := weights
  sourceQuantitative := quantitative
  targetQuantitative := quantitative
  preserves_weight := by intro _ _; rfl

/-- Quantitative transports compose when the middle interface is literally
the same typed effect.  Equality of the two supplied middle weight functions
is derived from their common `quantitative` field. -/
def comp
    {A : Type uA} {B : Type uB}
    {C : Type uC} {D : Type uD}
    {E : Type uE} {F : Type uF}
    {firstEffect : TypedEffectInterface A B}
    {middleEffect : TypedEffectInterface C D}
    {lastEffect : TypedEffectInterface E F}
    (first : ExactQuantitativeEffectTransport firstEffect middleEffect)
    (second : ExactQuantitativeEffectTransport middleEffect lastEffect) :
    ExactQuantitativeEffectTransport firstEffect lastEffect where
  structural := ExactRelTransport.comp second.structural first.structural
  sourceWeights := first.sourceWeights
  targetWeights := second.targetWeights
  sourceQuantitative := first.sourceQuantitative
  targetQuantitative := second.targetQuantitative
  preserves_weight := by
    intro source target
    have middleWeights : first.targetWeights = second.sourceWeights :=
      Option.some.inj
        (first.targetQuantitative.symm.trans second.sourceQuantitative)
    calc
      second.targetWeights
          (second.structural.sourceMap (first.structural.sourceMap source))
          (second.structural.targetMap (first.structural.targetMap target)) =
          second.sourceWeights (first.structural.sourceMap source)
            (first.structural.targetMap target) :=
        second.preserves_weight _ _
      _ = first.targetWeights (first.structural.sourceMap source)
            (first.structural.targetMap target) := by rw [middleWeights]
      _ = first.sourceWeights source target := first.preserves_weight _ _

theorem comp_preserves_weight
    {A : Type uA} {B : Type uB}
    {C : Type uC} {D : Type uD}
    {E : Type uE} {F : Type uF}
    {firstEffect : TypedEffectInterface A B}
    {middleEffect : TypedEffectInterface C D}
    {lastEffect : TypedEffectInterface E F}
    (first : ExactQuantitativeEffectTransport firstEffect middleEffect)
    (second : ExactQuantitativeEffectTransport middleEffect lastEffect)
    (source : A) (target : B) :
    (first.comp second).targetWeights
        ((first.comp second).structural.sourceMap source)
        ((first.comp second).structural.targetMap target) =
      (first.comp second).sourceWeights source target :=
  (first.comp second).preserves_weight source target

end ExactQuantitativeEffectTransport

/-- The minimal joint certificate: the intended evolving referent and the
effect support both transport to their target types. -/
structure TypedContinuationEffectTransport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (sourceContext targetContext :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    {Source : Type uA} {Target : Type uB}
    {Source' : Type uC} {Target' : Type uD}
    (sourceEffect : TypedEffectInterface Source Target)
    (targetEffect : TypedEffectInterface Source' Target') where
  context : ContextCompatibility sourceContext targetContext
  effect : ExactEffectTransport sourceEffect targetEffect

namespace TypedContinuationEffectTransport

def identity
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    {Source : Type uA} {Target : Type uB}
    (effect : TypedEffectInterface Source Target) :
    TypedContinuationEffectTransport context context effect effect where
  context := ContextCompatibility.identity context
  effect := ExactRelTransport.identity effect.support

def comp
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {contextA contextB contextC :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {A : Type uA} {B : Type uB}
    {C : Type uC} {D : Type uD}
    {E : Type uE} {F : Type uF}
    {effectA : TypedEffectInterface A B}
    {effectB : TypedEffectInterface C D}
    {effectC : TypedEffectInterface E F}
    (first : TypedContinuationEffectTransport contextA contextB effectA effectB)
    (second : TypedContinuationEffectTransport contextB contextC effectB effectC) :
    TypedContinuationEffectTransport contextA contextC effectA effectC where
  context := first.context.comp second.context
  effect := ExactRelTransport.comp second.effect first.effect

/-- Three joint transports associate on the witness-transporting map.  Proof
fields are intentionally not quotiented; the executable observable is the
transported witness. -/
theorem comp_context_transport_assoc
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {contextA contextB contextC contextD :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {A : Type uA} {B : Type uB}
    {C : Type uC} {D : Type uD}
    {E : Type uE} {F : Type uF}
    {effectA : TypedEffectInterface A B}
    {effectB : TypedEffectInterface C D}
    {effectC : TypedEffectInterface E F}
    {effectD : TypedEffectInterface E F}
    (first : TypedContinuationEffectTransport contextA contextB effectA effectB)
    (second : TypedContinuationEffectTransport contextB contextC effectB effectC)
    (third : TypedContinuationEffectTransport contextC contextD effectC effectD)
    {initial endpoint : State}
    (witness : ContinuationWitness contextA initial endpoint) :
    ((first.comp second).comp third).context.transport initial endpoint witness =
      (first.comp (second.comp third)).context.transport initial endpoint witness :=
  rfl

/-- Three joint transports associate on both typed effect maps. -/
theorem comp_effect_maps_assoc
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {contextA contextB contextC contextD :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {A : Type uA} {B : Type uB}
    {C : Type uC} {D : Type uD}
    {E : Type uE} {F : Type uF}
    {effectA : TypedEffectInterface A B}
    {effectB : TypedEffectInterface C D}
    {effectC : TypedEffectInterface E F}
    {effectD : TypedEffectInterface E F}
    (first : TypedContinuationEffectTransport contextA contextB effectA effectB)
    (second : TypedContinuationEffectTransport contextB contextC effectB effectC)
    (third : TypedContinuationEffectTransport contextC contextD effectC effectD)
    (source : A) (target : B) :
    (((first.comp second).comp third).effect.sourceMap source =
        (first.comp (second.comp third)).effect.sourceMap source) ∧
      (((first.comp second).comp third).effect.targetMap target =
        (first.comp (second.comp third)).effect.targetMap target) :=
  ⟨rfl, rfl⟩

/-- The joint certificate simultaneously transports the referent witness and
the selected effect edge. -/
theorem certifies_continuation_and_support
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {sourceContext targetContext :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {Source : Type uA} {Target : Type uB}
    {Source' : Type uC} {Target' : Type uD}
    {sourceEffect : TypedEffectInterface Source Target}
    {targetEffect : TypedEffectInterface Source' Target'}
    (certificate : TypedContinuationEffectTransport
      sourceContext targetContext sourceEffect targetEffect)
    {initial endpoint : State}
    (continuation : ContinuationWitness sourceContext initial endpoint)
    {source : Source} {target : Target}
    (edge : sourceEffect.support source target) :
    Continues targetContext initial endpoint ∧
      targetEffect.support
        (certificate.effect.sourceMap source)
        (certificate.effect.targetMap target) := by
  exact ⟨⟨certificate.context.transport initial endpoint continuation⟩,
    certificate.effect.preserves edge⟩

/-- Frame mismatch blocks the joint certificate even when an effect-support
transport exists independently. -/
theorem frame_mismatch_blocks_joint_effect_transport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {sourceContext targetContext :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {Source : Type uA} {Target : Type uB}
    {Source' : Type uC} {Target' : Type uD}
    {sourceEffect : TypedEffectInterface Source Target}
    {targetEffect : TypedEffectInterface Source' Target'}
    (mismatch : sourceContext.frame ≠ targetContext.frame) :
    ¬ Nonempty (TypedContinuationEffectTransport
      sourceContext targetContext sourceEffect targetEffect) := by
  rintro ⟨certificate⟩
  exact mismatch certificate.context.frameCompatible

end TypedContinuationEffectTransport

/-- Strong joint certificate retaining quantitative effect magnitudes. -/
structure TypedQuantitativeContinuationEffectTransport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (sourceContext targetContext :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    {Source : Type uA} {Target : Type uB}
    {Source' : Type uC} {Target' : Type uD}
    (sourceEffect : TypedEffectInterface Source Target)
    (targetEffect : TypedEffectInterface Source' Target') where
  context : ContextCompatibility sourceContext targetContext
  effect : ExactQuantitativeEffectTransport sourceEffect targetEffect

namespace TypedQuantitativeContinuationEffectTransport

def identity
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    {Source : Type uA} {Target : Type uB}
    (effect : TypedEffectInterface Source Target)
    (weights : Source → Target → ℚ)
    (quantitative : effect.quantitative = some weights) :
    TypedQuantitativeContinuationEffectTransport context context effect effect where
  context := ContextCompatibility.identity context
  effect := ExactQuantitativeEffectTransport.identity effect weights quantitative

def comp
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {contextA contextB contextC :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {A : Type uA} {B : Type uB}
    {C : Type uC} {D : Type uD}
    {E : Type uE} {F : Type uF}
    {effectA : TypedEffectInterface A B}
    {effectB : TypedEffectInterface C D}
    {effectC : TypedEffectInterface E F}
    (first : TypedQuantitativeContinuationEffectTransport contextA contextB effectA effectB)
    (second : TypedQuantitativeContinuationEffectTransport contextB contextC effectB effectC) :
    TypedQuantitativeContinuationEffectTransport contextA contextC effectA effectC where
  context := first.context.comp second.context
  effect := first.effect.comp second.effect

end TypedQuantitativeContinuationEffectTransport

/-- A quantitative joint certificate gives both target continuation and exact
transported effect magnitude. -/
theorem quantitative_joint_transport_certifies_weight
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {sourceContext targetContext :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {Source : Type uA} {Target : Type uB}
    {Source' : Type uC} {Target' : Type uD}
    {sourceEffect : TypedEffectInterface Source Target}
    {targetEffect : TypedEffectInterface Source' Target'}
    (certificate : TypedQuantitativeContinuationEffectTransport
      sourceContext targetContext sourceEffect targetEffect)
    {initial endpoint : State}
    (continuation : ContinuationWitness sourceContext initial endpoint)
    (source : Source) (target : Target) :
    Continues targetContext initial endpoint ∧
      certificate.effect.targetWeights
          (certificate.effect.structural.sourceMap source)
          (certificate.effect.structural.targetMap target) =
        certificate.effect.sourceWeights source target := by
  exact ⟨⟨certificate.context.transport initial endpoint continuation⟩,
    certificate.effect.preserves_weight source target⟩

/-!
## Sharp normalized countermodel
-/

private def fairBoolStochasticEffect : FiniteStochasticEffect Unit Bool where
  mass := fun _ _ => (1 : ℚ) / 2
  nonnegative := by intro _ _; norm_num
  normalized := by intro _; norm_num [Fintype.sum_bool]

private def biasedBoolStochasticEffect : FiniteStochasticEffect Unit Bool where
  mass := fun _ target => if target then (2 : ℚ) / 3 else (1 : ℚ) / 3
  nonnegative := by intro _ target; cases target <;> norm_num
  normalized := by intro _; norm_num [Fintype.sum_bool]

/-- Even normalized stochastic effects can have identical support and unequal
magnitudes.  Hence exact support transport alone cannot entail quantitative
transport; the weight law above is genuinely additional. -/
theorem normalized_support_transport_does_not_determine_weights :
    fairBoolStochasticEffect.support = biasedBoolStochasticEffect.support ∧
      fairBoolStochasticEffect.mass () true ≠
        biasedBoolStochasticEffect.mass () true := by
  constructor
  · funext source target
    apply propext
    cases source
    cases target <;>
      norm_num [FiniteStochasticEffect.support, fairBoolStochasticEffect,
        biasedBoolStochasticEffect]
  · norm_num [fairBoolStochasticEffect, biasedBoolStochasticEffect]

end OCKIndividuationMSpaceComposition
