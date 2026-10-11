import OCKIndividuationMSpaceComposition.TypedTransportComparativeBoundary
import Mathlib.Algebra.Order.BigOperators.Group.Finset

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

universe uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame

/-!
# Minimum path-dependent sequential intervention adapter

Longitudinal g-computation, sequential exchangeability and positivity are mature
causal-inference machinery and are reused as an explicit contract.  The OC
adapter adds only what the parent question needs: the intervention horizon is
aligned with a proof-carrying continuation path, and stagewise identification
and error budgets accumulate along that exact path.
-/

/-- Additive value of a finite sequential intervention regime. -/
def sequentialRegimeValue {horizon : Nat} (stageEffect : Fin horizon → ℚ) : ℚ :=
  ∑ stage, stageEffect stage

/-- Mature finite-horizon sequential identification assumptions, kept explicit. -/
structure SequentialRegimeIdentification (horizon : Nat) where
  latentStageEffect : Fin horizon → ℚ
  identifiedStageEffect : Fin horizon → ℚ
  treatmentPropensity : Fin horizon → ℚ
  sequentialPositivity : ∀ stage, 0 < treatmentPropensity stage
  propensityBelowOne : ∀ stage, treatmentPropensity stage < 1
  sequentialExchangeabilityConsistency :
    ∀ stage, identifiedStageEffect stage = latentStageEffect stage

/-- Sequential g-computation contract identifies the additive regime value. -/
theorem sequential_g_contract_identifies_regime_value
    {horizon : Nat} (contract : SequentialRegimeIdentification horizon) :
    sequentialRegimeValue contract.identifiedStageEffect =
      sequentialRegimeValue contract.latentStageEffect := by
  unfold sequentialRegimeValue
  apply Finset.sum_congr rfl
  intro stage _
  exact contract.sequentialExchangeabilityConsistency stage

/-- Stagewise estimation radii accumulate additively over a finite regime. -/
theorem sequential_regime_estimation_error_bound
    {horizon : Nat}
    (trueEffect estimatedEffect errorRadius : Fin horizon → ℚ)
    (stageError : ∀ stage,
      |estimatedEffect stage - trueEffect stage| ≤ errorRadius stage) :
    |sequentialRegimeValue estimatedEffect -
      sequentialRegimeValue trueEffect| ≤ ∑ stage, errorRadius stage := by
  have difference :
      sequentialRegimeValue estimatedEffect - sequentialRegimeValue trueEffect =
        ∑ stage, (estimatedEffect stage - trueEffect stage) := by
    unfold sequentialRegimeValue
    rw [← Finset.sum_sub_distrib]
  rw [difference]
  calc
    |∑ stage, (estimatedEffect stage - trueEffect stage)| ≤
      ∑ stage, |estimatedEffect stage - trueEffect stage| :=
        Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ stage, errorRadius stage := by
      exact Finset.sum_le_sum fun stage _ => stageError stage

/-- Two sequential policies retain their ordering beyond their accumulated radii. -/
theorem sequential_policy_order_stable
    (truePreferred trueCompetitor estimatedPreferred estimatedCompetitor
      preferredRadius competitorRadius : ℚ)
    (preferredError : |estimatedPreferred - truePreferred| ≤ preferredRadius)
    (competitorError : |estimatedCompetitor - trueCompetitor| ≤ competitorRadius)
    (margin : trueCompetitor + preferredRadius + competitorRadius < truePreferred) :
    estimatedCompetitor < estimatedPreferred := by
  have preferredLower := (abs_le.mp preferredError).1
  have competitorUpper := (abs_le.mp competitorError).2
  linarith

/-- The sequential causal contract is aligned to one exact OC continuation path. -/
structure PathDependentSequentialIntervention
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (initial endpoint : State) (horizon : Nat) where
  continuation : ContinuationWitness C initial endpoint
  horizonAligned : continuation.history.length = horizon
  identification : SequentialRegimeIdentification horizon

/-- A path-aligned sequential certificate yields continuation and exact regime value. -/
theorem path_dependent_sequential_certificate_is_sound
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {initial endpoint : State} {horizon : Nat}
    (certificate : PathDependentSequentialIntervention C initial endpoint horizon) :
    Continues C initial endpoint ∧
      certificate.continuation.history.length = horizon ∧
      sequentialRegimeValue certificate.identification.identifiedStageEffect =
        sequentialRegimeValue certificate.identification.latentStageEffect := by
  exact ⟨⟨certificate.continuation⟩, certificate.horizonAligned,
    sequential_g_contract_identifies_regime_value certificate.identification⟩

/-- Context transport that preserves the number of intervention stages. -/
structure HorizonPreservingContextCompatibility
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame) where
  context : ContextCompatibility source target
  lengthPreserved : ∀ initial endpoint
      (witness : ContinuationWitness source initial endpoint),
    (context.transport initial endpoint witness).history.length = witness.history.length

namespace HorizonPreservingContextCompatibility

def identity
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame) :
    HorizonPreservingContextCompatibility C C where
  context := ContextCompatibility.identity C
  lengthPreserved := by intro initial endpoint witness; rfl

def comp
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {first middle last :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    (left : HorizonPreservingContextCompatibility first middle)
    (right : HorizonPreservingContextCompatibility middle last) :
    HorizonPreservingContextCompatibility first last where
  context := left.context.comp right.context
  lengthPreserved := by
    intro initial endpoint witness
    exact (right.lengthPreserved initial endpoint
      (left.context.transport initial endpoint witness)).trans
        (left.lengthPreserved initial endpoint witness)

end HorizonPreservingContextCompatibility

/-- Sound transport of a sequential certificate under the stronger contract. -/
def PathDependentSequentialIntervention.transportPreservingHorizon
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {initial endpoint : State} {horizon : Nat}
    (compatibility : HorizonPreservingContextCompatibility source target)
    (certificate : PathDependentSequentialIntervention source initial endpoint horizon) :
    PathDependentSequentialIntervention target initial endpoint horizon where
  continuation := compatibility.context.transport initial endpoint certificate.continuation
  horizonAligned := by
    rw [compatibility.lengthPreserved initial endpoint certificate.continuation]
    exact certificate.horizonAligned
  identification := certificate.identification

/-- Missing target continuation blocks every target sequential certificate. -/
theorem continuation_obstruction_blocks_sequential_intervention
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {initial endpoint : State} {horizon : Nat}
    (obstruction : ¬ Continues C initial endpoint) :
    ¬ Nonempty (PathDependentSequentialIntervention C initial endpoint horizon) := by
  rintro ⟨certificate⟩
  exact obstruction ⟨certificate.continuation⟩

def earlyEffect (stage : Fin 2) : ℚ := if stage = 0 then 1 else 0
def lateEffect (stage : Fin 2) : ℚ := if stage = 0 then 0 else 1
def zeroSequentialPropensity (_stage : Fin 1) : ℚ := 0

/-- Endpoint regime value does not identify when the effect occurred. -/
theorem equal_regime_value_does_not_identify_effect_timing :
    sequentialRegimeValue earlyEffect = sequentialRegimeValue lateEffect ∧
      earlyEffect 0 ≠ lateEffect 0 := by
  norm_num [sequentialRegimeValue, earlyEffect, lateEffect, Fin.sum_univ_two]

/-- Zero propensity at one stage violates sequential positivity outright. -/
theorem zero_stage_propensity_blocks_sequential_positivity :
    ¬ (∀ stage : Fin 1, 0 < zeroSequentialPropensity stage) := by
  intro positive
  have := positive 0
  norm_num [zeroSequentialPropensity] at this

end OCKIndividuationMSpaceComposition
