import OCMaturityCompletionCycle.JointIdentityLawCoherence

/-!
# Five-component defect derived from one joint open/history study

Every component below is computed from the same typed joint process,
abstraction, frozen operational histories, and aligned path experiment.  No
arbitrary external law pair is accepted by the combined constructor.
-/

namespace OCMaturityCompletionCycle

universe uHistory uObservation uState uContext uBoundaryIn uAction uBoundaryOut
  uAbstractState uAbstractContext uAbstractBoundaryIn uAbstractAction
  uAbstractBoundaryOut

/--
A prospectively declared morphism between frozen operational contexts.  The
relation is computable and nonempty.  Its alignment fields say how abstract
  context, boundary input, action, and encoded state are transported.
  Naturality below is therefore a covariance statement across related
  contexts, not a duplicate test inside one lumpability fibre.  Boundary-output
  accuracy remains the separate boundary defect; this context functor does not
  claim an unused output transport.
-/
structure OperationalHistoryContextFunctor
    {HistoryIndex : Type uHistory}
    {Observation : Type uObservation}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    (abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut)
    (historyAbstraction :
      OperationalHistoryAbstraction (Observation := Observation) abstraction)
    (historyProcess : FiniteHistoryJointOpenProcess HistoryIndex Observation
      State Context BoundaryIn Action BoundaryOut) where
  related : HistoryIndex → HistoryIndex → Bool
  anchor : HistoryIndex
  anchor_covers : ∀ index, related anchor index = true
  related_reflexive : ∀ index, related index index = true
  related_transitive : ∀ left middle right,
    related left middle = true → related middle right = true →
      related left right = true
  contextMap : HistoryIndex → HistoryIndex → AbstractContext → AbstractContext
  boundaryInMap : HistoryIndex → HistoryIndex →
    AbstractBoundaryIn → AbstractBoundaryIn
  actionMap : HistoryIndex → HistoryIndex → AbstractAction → AbstractAction
  stateMap : HistoryIndex → HistoryIndex → AbstractState → AbstractState
  context_identity : ∀ index, contextMap index index = id
  boundaryIn_identity : ∀ index, boundaryInMap index index = id
  action_identity : ∀ index, actionMap index index = id
  state_identity : ∀ index, stateMap index index = id
  context_composition : ∀ left middle right,
    related left middle = true → related middle right = true →
      contextMap middle right ∘ contextMap left middle = contextMap left right
  boundaryIn_composition : ∀ left middle right,
    related left middle = true → related middle right = true →
      boundaryInMap middle right ∘ boundaryInMap left middle =
        boundaryInMap left right
  action_composition : ∀ left middle right,
    related left middle = true → related middle right = true →
      actionMap middle right ∘ actionMap left middle = actionMap left right
  state_composition : ∀ left middle right,
    related left middle = true → related middle right = true →
      stateMap middle right ∘ stateMap left middle = stateMap left right
  context_aligned : ∀ left right, related left right = true →
    contextMap left right
        (abstraction.contextMap
          (historyProcess.support.currentContext left)) =
      abstraction.contextMap
        (historyProcess.support.currentContext right)
  boundaryIn_aligned : ∀ left right, related left right = true →
    boundaryInMap left right
        (abstraction.boundaryInMap
          (historyProcess.support.currentBoundaryIn left)) =
      abstraction.boundaryInMap
        (historyProcess.support.currentBoundaryIn right)
  action_aligned : ∀ left right, related left right = true →
    actionMap left right
        (abstraction.actionMap
          (historyProcess.support.currentAction left)) =
      abstraction.actionMap
        (historyProcess.support.currentAction right)
  encodedState_aligned : ∀ left right, related left right = true →
    stateMap left right
        (operationalHistoryAbstractState historyAbstraction historyProcess left) =
      operationalHistoryAbstractState historyAbstraction historyProcess right

/-- One coherent input package for all five quantitative defect components. -/
structure JointOpenHistoryStudy
    (HistoryIndex : Type uHistory)
    (Observation : Type uObservation)
    (State : Type uState)
    (Context : Type uContext)
    (BoundaryIn : Type uBoundaryIn)
    (Action : Type uAction)
    (BoundaryOut : Type uBoundaryOut)
    (AbstractState : Type uAbstractState)
    (AbstractContext : Type uAbstractContext)
    (AbstractBoundaryIn : Type uAbstractBoundaryIn)
    (AbstractAction : Type uAbstractAction)
    (AbstractBoundaryOut : Type uAbstractBoundaryOut)
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut] where
  abstraction : FiniteJointContextualAbstraction State Context BoundaryIn Action
    BoundaryOut AbstractState AbstractContext AbstractBoundaryIn AbstractAction
    AbstractBoundaryOut
  historyAbstraction :
    OperationalHistoryAbstraction (Observation := Observation) abstraction
  historyProcess : FiniteHistoryJointOpenProcess HistoryIndex Observation State
    Context BoundaryIn Action BoundaryOut
  historyRealization : FrozenHistoryMarkovRealization historyProcess
    abstraction.fine
  observationMap_agrees :
    historyRealization.observeState = historyAbstraction.observeState
  historyPrefixConsistency : FrozenHistoryPrefixConsistency historyRealization
  contextTransport : OperationalHistoryContextFunctor abstraction
    historyAbstraction historyProcess
  pathExperiment : HistoryIndex → AlignedJointOpenExperiments abstraction
  pathExperiment_binds_history : ∀ index,
    (pathExperiment index).fineExperiment =
      historyRealization.experiment index
  memoryCost : Nat
  stateCost : Nat
  resourceCost : Nat

/-- Abstract next-state law transported along the declared context morphism. -/
def transportedHistoryContextLaw
    {HistoryIndex : Type uHistory}
    {Observation : Type uObservation}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    (study : JointOpenHistoryStudy HistoryIndex Observation State Context
      BoundaryIn Action BoundaryOut AbstractState AbstractContext
      AbstractBoundaryIn AbstractAction AbstractBoundaryOut)
    (left right : HistoryIndex) :
    FiniteProbabilityMass AbstractState :=
  pushforwardFiniteProbability
    (study.contextTransport.stateMap left right)
    (abstractHistoryStateLaw study.abstraction study.historyAbstraction
      study.historyProcess left)

/-- Explicit context transport is nonexpansive in finite total variation. -/
theorem transportedHistoryContextLaw_nonexpansive
    {HistoryIndex : Type uHistory}
    {Observation : Type uObservation}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    (study : JointOpenHistoryStudy HistoryIndex Observation State Context
      BoundaryIn Action BoundaryOut AbstractState AbstractContext
      AbstractBoundaryIn AbstractAction AbstractBoundaryOut)
    (source target : HistoryIndex)
    (left right : FiniteProbabilityMass AbstractState) :
    finiteTotalVariation
        (pushforwardFiniteProbability
          (study.contextTransport.stateMap source target) left)
        (pushforwardFiniteProbability
          (study.contextTransport.stateMap source target) right) ≤
      finiteTotalVariation left right :=
  pushforwardFiniteProbability_nonexpansive
    (study.contextTransport.stateMap source target) _ _

/-- Exact law covariance along every declared context morphism. -/
def HistoryContextNatural
    {HistoryIndex : Type uHistory}
    {Observation : Type uObservation}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    (study : JointOpenHistoryStudy HistoryIndex Observation State Context
      BoundaryIn Action BoundaryOut AbstractState AbstractContext
      AbstractBoundaryIn AbstractAction AbstractBoundaryOut) : Prop :=
  ∀ left right,
    study.contextTransport.related left right = true →
      (transportedHistoryContextLaw study left right).mass =
        (abstractHistoryStateLaw study.abstraction study.historyAbstraction
          study.historyProcess right).mass

/-- Context-transport right law; unrelated pairs contribute zero defect. -/
def historyContextRightLaw
    {HistoryIndex : Type uHistory}
    {Observation : Type uObservation}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    (study : JointOpenHistoryStudy HistoryIndex Observation State Context
      BoundaryIn Action BoundaryOut AbstractState AbstractContext
      AbstractBoundaryIn AbstractAction AbstractBoundaryOut) :
    HistoryIndex × HistoryIndex →
      FiniteProbabilityMass AbstractState :=
  fun pair =>
    if study.contextTransport.related pair.1 pair.2 then
      abstractHistoryStateLaw study.abstraction study.historyAbstraction
        study.historyProcess pair.2
    else
      transportedHistoryContextLaw study pair.1 pair.2

/-- Quantitative context-naturality defect derived from primitive history laws. -/
def historyContextNaturalityDefect
    {HistoryIndex : Type uHistory}
    {Observation : Type uObservation}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    (study : JointOpenHistoryStudy HistoryIndex Observation State Context
      BoundaryIn Action BoundaryOut AbstractState AbstractContext
      AbstractBoundaryIn AbstractAction AbstractBoundaryOut) : ℚ :=
  finiteLawFamilyDefect
    (fun pair : HistoryIndex × HistoryIndex =>
      transportedHistoryContextLaw study pair.1 pair.2)
    (historyContextRightLaw study)

theorem historyContextNaturalityDefect_eq_zero_iff_natural
    {HistoryIndex : Type uHistory}
    {Observation : Type uObservation}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    (study : JointOpenHistoryStudy HistoryIndex Observation State Context
      BoundaryIn Action BoundaryOut AbstractState AbstractContext
      AbstractBoundaryIn AbstractAction AbstractBoundaryOut) :
    historyContextNaturalityDefect study = 0 ↔ HistoryContextNatural study := by
  change
    finiteLawFamilyDefect
        (fun pair : HistoryIndex × HistoryIndex =>
          transportedHistoryContextLaw study pair.1 pair.2)
        (historyContextRightLaw study) = 0 ↔ _
  rw [finiteLawFamilyDefect_eq_zero_iff_exact]
  constructor
  · intro exactFamilies left right aligned
    have pairExact := exactFamilies (left, right)
    simpa [historyContextRightLaw, aligned] using pairExact
  · intro natural pair
    by_cases aligned : study.contextTransport.related pair.1 pair.2 = true
    · simpa [historyContextRightLaw, aligned] using
        natural pair.1 pair.2 aligned
    · have isFalse : study.contextTransport.related pair.1 pair.2 = false :=
        Bool.eq_false_of_not_eq_true aligned
      simp [historyContextRightLaw, isFalse]

/-! Aggregate path-law stitching over the history-indexed experiment family. -/

def historyPathStitchingDefect
    {HistoryIndex : Type uHistory}
    {Observation : Type uObservation}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    (study : JointOpenHistoryStudy HistoryIndex Observation State Context
      BoundaryIn Action BoundaryOut AbstractState AbstractContext
      AbstractBoundaryIn AbstractAction AbstractBoundaryOut) : ℚ :=
  ∑ index, jointOpenPathStitchingDefect (study.pathExperiment index)

theorem historyPathStitchingDefect_eq_zero_iff_all_exact
    {HistoryIndex : Type uHistory}
    {Observation : Type uObservation}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    (study : JointOpenHistoryStudy HistoryIndex Observation State Context
      BoundaryIn Action BoundaryOut AbstractState AbstractContext
      AbstractBoundaryIn AbstractAction AbstractBoundaryOut) :
    historyPathStitchingDefect study = 0 ↔
      ∀ index,
        (transportedFineJointPathLaw (study.pathExperiment index)).mass =
          (inducedFiniteStateOutputPathLaw
            (study.pathExperiment index).abstractExperiment).mass := by
  constructor
  · intro aggregateZero index
    have termNonnegative :
        0 ≤ jointOpenPathStitchingDefect (study.pathExperiment index) :=
      finiteTotalVariation_nonnegative _ _
    have termLeAggregate :
        jointOpenPathStitchingDefect (study.pathExperiment index) ≤
          historyPathStitchingDefect study := by
      exact Finset.single_le_sum
        (fun other _ => finiteTotalVariation_nonnegative
          (transportedFineJointPathLaw (study.pathExperiment other))
          (inducedFiniteStateOutputPathLaw
            (study.pathExperiment other).abstractExperiment))
        (Finset.mem_univ index)
    have termLeZero :
        jointOpenPathStitchingDefect (study.pathExperiment index) ≤ 0 := by
      simpa [aggregateZero] using termLeAggregate
    have termZero :
        jointOpenPathStitchingDefect (study.pathExperiment index) = 0 :=
      le_antisymm termLeZero termNonnegative
    exact (jointOpenPathStitchingDefect_eq_zero_iff_exact
      (study.pathExperiment index)).1 termZero
  · intro everyExact
    simp only [historyPathStitchingDefect]
    calc
      (∑ index, jointOpenPathStitchingDefect (study.pathExperiment index)) =
          ∑ _index : HistoryIndex, 0 := by
        apply Finset.sum_congr rfl
        intro index _
        exact (jointOpenPathStitchingDefect_eq_zero_iff_exact
          (study.pathExperiment index)).2 (everyExact index)
      _ = 0 := by simp

/-- Five reported numeric components derived from one bound study package. -/
def jointOpenHistoryDefect
    {HistoryIndex : Type uHistory}
    {Observation : Type uObservation}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractContext]
    [DecidableEq AbstractBoundaryIn]
    [DecidableEq AbstractAction]
    [DecidableEq AbstractBoundaryOut]
    (study : JointOpenHistoryStudy HistoryIndex Observation State Context
      BoundaryIn Action BoundaryOut AbstractState AbstractContext
      AbstractBoundaryIn AbstractAction AbstractBoundaryOut) : AbstractionDefect where
  prediction := historyPredictionDefect study.abstraction study.historyAbstraction
    study.historyProcess
  lumpability := historyLumpabilityDefect study.historyAbstraction
    study.historyProcess
  boundary := historyBoundaryOutputDefect study.abstraction
    study.historyAbstraction study.historyProcess
  context := historyContextNaturalityDefect study
  stitching := historyPathStitchingDefect study
  memoryCost := study.memoryCost
  stateCost := study.stateCost
  resourceCost := study.resourceCost

/--
Zero of the reported vector is exactly the five stated tests.  This is not an
automatic independence theorem, but state prediction and boundary output are
now separate marginals; only path stitching uses the full joint law.
-/
theorem jointOpenHistoryDefect_zero_iff_all_exact
    {HistoryIndex : Type uHistory}
    {Observation : Type uObservation}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractContext]
    [DecidableEq AbstractBoundaryIn]
    [DecidableEq AbstractAction]
    [DecidableEq AbstractBoundaryOut]
    (study : JointOpenHistoryStudy HistoryIndex Observation State Context
      BoundaryIn Action BoundaryOut AbstractState AbstractContext
      AbstractBoundaryIn AbstractAction AbstractBoundaryOut) :
    (jointOpenHistoryDefect study).ZeroScientificComponents ↔
      FiniteLawFamilyExact
        (transportedFineHistoryStateLaw study.abstraction study.historyProcess)
        (abstractHistoryStateLaw study.abstraction study.historyAbstraction
          study.historyProcess) ∧
      HistoryEncoderKernelConsistent study.historyAbstraction study.historyProcess ∧
      FiniteLawFamilyExact
        (transportedFineHistoryBoundaryLaw study.abstraction study.historyProcess)
        (abstractHistoryBoundaryLaw study.abstraction study.historyAbstraction
          study.historyProcess) ∧
      HistoryContextNatural study ∧
      (∀ index,
        (transportedFineJointPathLaw (study.pathExperiment index)).mass =
          (inducedFiniteStateOutputPathLaw
            (study.pathExperiment index).abstractExperiment).mass) := by
  simp only [AbstractionDefect.ZeroScientificComponents, jointOpenHistoryDefect]
  rw [historyPredictionDefect_eq_zero_iff_exact,
    historyLumpabilityDefect_eq_zero_iff_kernelConsistent,
    historyBoundaryOutputDefect_eq_zero_iff_exact,
    historyContextNaturalityDefect_eq_zero_iff_natural,
    historyPathStitchingDefect_eq_zero_iff_all_exact]

end OCMaturityCompletionCycle
