import OCKIndividuationMSpaceComposition.EvidenceTransportDefect

namespace OCKIndividuationMSpaceComposition

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame
  uFamilyA uFamilyB uFamilyC uFamilyD

/-!
# Nonexpansive quantitative transport between continuation contexts

The evidence-defect algebra becomes cross-context only after a typed transport
is required to be nonexpansive.  This module gives identity and composition,
connects that transport to `ContextCompatibility`, and exposes round-trip
defect as a quantitative holonomy obstruction.
-/

/-- A map of evidence potentials that cannot increase registered defect. -/
structure CalibratedEvidenceTransport
    (SourceFamily : Type uFamilyA) [PseudoMetricSpace SourceFamily]
    (TargetFamily : Type uFamilyB) [PseudoMetricSpace TargetFamily]
    (sourceWeights targetWeights : EvidenceTransportWeights) where
  map : EvidencePotential SourceFamily → EvidencePotential TargetFamily
  nonexpansive : ∀ source target,
    weightedEvidenceTransportDefect targetWeights (map source) (map target) ≤
      weightedEvidenceTransportDefect sourceWeights source target

namespace CalibratedEvidenceTransport

def identity
    {Family : Type uFamilyA} [PseudoMetricSpace Family]
    (weights : EvidenceTransportWeights) :
    CalibratedEvidenceTransport Family Family weights weights where
  map := id
  nonexpansive := by
    intro source target
    exact le_rfl

def comp
    {FamilyA : Type uFamilyA} [PseudoMetricSpace FamilyA]
    {FamilyB : Type uFamilyB} [PseudoMetricSpace FamilyB]
    {FamilyC : Type uFamilyC} [PseudoMetricSpace FamilyC]
    {weightsA weightsB weightsC : EvidenceTransportWeights}
    (first : CalibratedEvidenceTransport FamilyA FamilyB weightsA weightsB)
    (second : CalibratedEvidenceTransport FamilyB FamilyC weightsB weightsC) :
    CalibratedEvidenceTransport FamilyA FamilyC weightsA weightsC where
  map := second.map ∘ first.map
  nonexpansive := by
    intro source target
    exact (second.nonexpansive (first.map source) (first.map target)).trans
      (first.nonexpansive source target)

theorem identity_map
    {Family : Type uFamilyA} [PseudoMetricSpace Family]
    (weights : EvidenceTransportWeights)
    (state : EvidencePotential Family) :
    (identity weights).map state = state := rfl

theorem comp_map
    {FamilyA : Type uFamilyA} [PseudoMetricSpace FamilyA]
    {FamilyB : Type uFamilyB} [PseudoMetricSpace FamilyB]
    {FamilyC : Type uFamilyC} [PseudoMetricSpace FamilyC]
    {weightsA weightsB weightsC : EvidenceTransportWeights}
    (first : CalibratedEvidenceTransport FamilyA FamilyB weightsA weightsB)
    (second : CalibratedEvidenceTransport FamilyB FamilyC weightsB weightsC)
    (state : EvidencePotential FamilyA) :
    (first.comp second).map state = second.map (first.map state) := rfl

theorem comp_map_assoc
    {FamilyA : Type uFamilyA} [PseudoMetricSpace FamilyA]
    {FamilyB : Type uFamilyB} [PseudoMetricSpace FamilyB]
    {FamilyC : Type uFamilyC} [PseudoMetricSpace FamilyC]
    {FamilyD : Type uFamilyD} [PseudoMetricSpace FamilyD]
    {weightsA weightsB weightsC weightsD : EvidenceTransportWeights}
    (first : CalibratedEvidenceTransport FamilyA FamilyB weightsA weightsB)
    (second : CalibratedEvidenceTransport FamilyB FamilyC weightsB weightsC)
    (third : CalibratedEvidenceTransport FamilyC FamilyD weightsC weightsD)
    (state : EvidencePotential FamilyA) :
    ((first.comp second).comp third).map state =
      (first.comp (second.comp third)).map state := rfl

end CalibratedEvidenceTransport

namespace ContextCompatibility

def identity
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    (context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame) :
    ContextCompatibility context context where
  taskCompatible := rfl
  projectionCompatible := rfl
  boundaryCompatible := rfl
  scopeCompatible := rfl
  frameCompatible := rfl
  transport := fun _ _ witness => witness

def comp
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {firstContext middleContext lastContext :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    (first : ContextCompatibility firstContext middleContext)
    (second : ContextCompatibility middleContext lastContext) :
    ContextCompatibility firstContext lastContext where
  taskCompatible := first.taskCompatible.trans second.taskCompatible
  projectionCompatible :=
    first.projectionCompatible.trans second.projectionCompatible
  boundaryCompatible := first.boundaryCompatible.trans second.boundaryCompatible
  scopeCompatible := first.scopeCompatible.trans second.scopeCompatible
  frameCompatible := first.frameCompatible.trans second.frameCompatible
  transport := fun initial endpoint witness =>
    second.transport initial endpoint (first.transport initial endpoint witness)

end ContextCompatibility

/--
Context compatibility plus a commuting nonexpansive map of evidence accounts.
No target-side inheritance contract is hidden in this structure.
-/
structure QuantitativeContextEvidenceTransport
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    (sourceContext targetContext :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (SourceFamily : Type uFamilyA) [PseudoMetricSpace SourceFamily]
    (TargetFamily : Type uFamilyB) [PseudoMetricSpace TargetFamily]
    (sourceWeights targetWeights : EvidenceTransportWeights)
    (sourceAccount : State → SequentialEvidenceAccount SourceFamily)
    (targetAccount : State → SequentialEvidenceAccount TargetFamily) where
  context : ContextCompatibility sourceContext targetContext
  evidence : CalibratedEvidenceTransport
    SourceFamily TargetFamily sourceWeights targetWeights
  account_commutes : ∀ state,
    evidence.map (sourceAccount state).toPotential =
      (targetAccount state).toPotential

namespace QuantitativeContextEvidenceTransport

def identity
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {Family : Type uFamilyA} [PseudoMetricSpace Family]
    (context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (weights : EvidenceTransportWeights)
    (account : State → SequentialEvidenceAccount Family) :
    QuantitativeContextEvidenceTransport context context
      Family Family weights weights account account where
  context := ContextCompatibility.identity context
  evidence := CalibratedEvidenceTransport.identity weights
  account_commutes := by intro state; rfl

def comp
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {FamilyA : Type uFamilyA} [PseudoMetricSpace FamilyA]
    {FamilyB : Type uFamilyB} [PseudoMetricSpace FamilyB]
    {FamilyC : Type uFamilyC} [PseudoMetricSpace FamilyC]
    {contextA contextB contextC :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {weightsA weightsB weightsC : EvidenceTransportWeights}
    {accountA : State → SequentialEvidenceAccount FamilyA}
    {accountB : State → SequentialEvidenceAccount FamilyB}
    {accountC : State → SequentialEvidenceAccount FamilyC}
    (first : QuantitativeContextEvidenceTransport contextA contextB
      FamilyA FamilyB weightsA weightsB accountA accountB)
    (second : QuantitativeContextEvidenceTransport contextB contextC
      FamilyB FamilyC weightsB weightsC accountB accountC) :
    QuantitativeContextEvidenceTransport contextA contextC
      FamilyA FamilyC weightsA weightsC accountA accountC where
  context := first.context.comp second.context
  evidence := first.evidence.comp second.evidence
  account_commutes := by
    intro state
    calc
      (first.evidence.comp second.evidence).map
          (accountA state).toPotential =
          second.evidence.map
            (first.evidence.map (accountA state).toPotential) := rfl
      _ = second.evidence.map (accountB state).toPotential := by
        rw [first.account_commutes state]
      _ = (accountC state).toPotential := second.account_commutes state

/--
A source-side inheritance theorem and a nonexpansive commuting context transport
are sufficient to derive zero target defect; no target inheritance axiom is
required.
-/
theorem transportWitness_zero_targetDefect
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {SourceFamily : Type uFamilyA} [MetricSpace SourceFamily]
    {TargetFamily : Type uFamilyB} [MetricSpace TargetFamily]
    {sourceContext targetContext :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {sourceWeights targetWeights : EvidenceTransportWeights}
    (targetWeightsNonnegative : targetWeights.Nonnegative)
    {sourceAccount : State → SequentialEvidenceAccount SourceFamily}
    {targetAccount : State → SequentialEvidenceAccount TargetFamily}
    {revisionOnly : Evidence → Prop}
    (sourceContract :
      EvidenceInheritanceContract sourceContext sourceAccount revisionOnly)
    (transport : QuantitativeContextEvidenceTransport sourceContext targetContext
      SourceFamily TargetFamily sourceWeights targetWeights
      sourceAccount targetAccount)
    {initial endpoint : State}
    (witness : ContinuationWitness sourceContext initial endpoint) :
    Nonempty (ContinuationWitness targetContext initial endpoint) ∧
      weightedEvidenceTransportDefect targetWeights
        (targetAccount initial).toPotential
        (targetAccount endpoint).toPotential = 0 := by
  have sourceZero := witness.sequentialEvidence_zero_weightedTransportDefect
    sourceWeights sourceContract
  have upper := transport.evidence.nonexpansive
    (sourceAccount initial).toPotential (sourceAccount endpoint).toPotential
  rw [transport.account_commutes initial,
    transport.account_commutes endpoint, sourceZero] at upper
  have lower := weightedEvidenceTransportDefect_nonnegative
    targetWeights targetWeightsNonnegative
    (targetAccount initial).toPotential (targetAccount endpoint).toPotential
  exact ⟨⟨transport.context.transport initial endpoint witness⟩,
    le_antisymm upper lower⟩

/--
No-go: positive target defect refutes the existence of a commuting
nonexpansive transport for an admitted zero-defect source path.
-/
theorem positive_targetDefect_obstructs_transport
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {SourceFamily : Type uFamilyA} [MetricSpace SourceFamily]
    {TargetFamily : Type uFamilyB} [MetricSpace TargetFamily]
    {sourceContext targetContext :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {sourceWeights targetWeights : EvidenceTransportWeights}
    (targetWeightsNonnegative : targetWeights.Nonnegative)
    {sourceAccount : State → SequentialEvidenceAccount SourceFamily}
    {targetAccount : State → SequentialEvidenceAccount TargetFamily}
    {revisionOnly : Evidence → Prop}
    (sourceContract :
      EvidenceInheritanceContract sourceContext sourceAccount revisionOnly)
    {initial endpoint : State}
    (witness : ContinuationWitness sourceContext initial endpoint)
    (targetPositive : 0 < weightedEvidenceTransportDefect targetWeights
      (targetAccount initial).toPotential
      (targetAccount endpoint).toPotential) :
    QuantitativeContextEvidenceTransport sourceContext targetContext
      SourceFamily TargetFamily sourceWeights targetWeights
      sourceAccount targetAccount → False := by
  intro transport
  have targetZero := (transport.transportWitness_zero_targetDefect
    targetWeightsNonnegative sourceContract witness).2
  rw [targetZero] at targetPositive
  exact lt_irrefl 0 targetPositive

end QuantitativeContextEvidenceTransport

/-- Defect accumulated by transporting an evidence potential around a loop. -/
def evidenceTransportHolonomyDefect
    {FamilyA : Type uFamilyA} [PseudoMetricSpace FamilyA]
    {FamilyB : Type uFamilyB} [PseudoMetricSpace FamilyB]
    {weightsA weightsB : EvidenceTransportWeights}
    (forward : CalibratedEvidenceTransport FamilyA FamilyB weightsA weightsB)
    (backward : CalibratedEvidenceTransport FamilyB FamilyA weightsB weightsA)
    (state : EvidencePotential FamilyA) : ℝ :=
  weightedEvidenceTransportDefect weightsA state
    ((forward.comp backward).map state)

theorem identity_roundTrip_has_zero_holonomyDefect
    {FamilyA : Type uFamilyA} [MetricSpace FamilyA]
    {FamilyB : Type uFamilyB} [PseudoMetricSpace FamilyB]
    {weightsA weightsB : EvidenceTransportWeights}
    (forward : CalibratedEvidenceTransport FamilyA FamilyB weightsA weightsB)
    (backward : CalibratedEvidenceTransport FamilyB FamilyA weightsB weightsA)
    (roundTripIdentity : ∀ state,
      (forward.comp backward).map state = state)
    (state : EvidencePotential FamilyA) :
    evidenceTransportHolonomyDefect forward backward state = 0 := by
  simp [evidenceTransportHolonomyDefect, roundTripIdentity,
    weightedEvidenceTransportDefect, directedDrop]

/-- Positive loop defect is a quantitative obstruction to identity holonomy. -/
theorem positive_holonomyDefect_obstructs_identity_roundTrip
    {FamilyA : Type uFamilyA} [MetricSpace FamilyA]
    {FamilyB : Type uFamilyB} [PseudoMetricSpace FamilyB]
    {weightsA weightsB : EvidenceTransportWeights}
    (forward : CalibratedEvidenceTransport FamilyA FamilyB weightsA weightsB)
    (backward : CalibratedEvidenceTransport FamilyB FamilyA weightsB weightsA)
    (state : EvidencePotential FamilyA)
    (positive : 0 < evidenceTransportHolonomyDefect forward backward state) :
    (forward.comp backward).map state ≠ state := by
  intro identity
  unfold evidenceTransportHolonomyDefect at positive
  rw [identity] at positive
  simp [weightedEvidenceTransportDefect, directedDrop] at positive

end OCKIndividuationMSpaceComposition
