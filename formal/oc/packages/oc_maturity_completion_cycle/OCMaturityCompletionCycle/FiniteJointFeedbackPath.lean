import OCMaturityCompletionCycle.JointPathTransport

/-!
# Finite joint path laws under state/output feedback

Unlike `FiniteJointOpenExperiment`, the control at a step is selected from the
actual state/output prefix.  The exact transport theorem therefore needs a
policy-naturality gate on every mapped prefix; one-step kernel commutation alone
is insufficient.
-/

namespace OCMaturityCompletionCycle

universe uState uContext uBoundaryIn uAction uBoundaryOut
  uAbstractState uAbstractContext uAbstractBoundaryIn uAbstractAction
  uAbstractBoundaryOut

/-- A finite experiment whose control is a function of the realized path prefix. -/
structure FiniteJointFeedbackExperiment
    (State : Type uState)
    (Context : Type uContext)
    (BoundaryIn : Type uBoundaryIn)
    (Action : Type uAction)
    (BoundaryOut : Type uBoundaryOut)
    [Fintype State]
    [Fintype BoundaryOut] where
  process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut
  horizon : Nat
  initial : FiniteProbabilityMass State
  policy : (step : Nat) → FiniteStateOutputPath State BoundaryOut step →
    JointOpenControl Context BoundaryIn Action

/-- Product path weight under a path-dependent feedback policy. -/
def inducedFeedbackJointPathWeightAt
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut)
    (initial : FiniteProbabilityMass State)
    (policy : (step : Nat) → FiniteStateOutputPath State BoundaryOut step →
      JointOpenControl Context BoundaryIn Action) :
    ∀ horizon, FiniteStateOutputPath State BoundaryOut horizon → ℚ
  | 0, state => initial.mass state.down
  | horizon + 1, path =>
      inducedFeedbackJointPathWeightAt process initial policy horizon path.1 *
        process.mass
          (finiteStateOutputPathLastState horizon path.1)
          (policy horizon path.1) path.2

theorem inducedFeedbackJointPathWeightAt_nonnegative
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut)
    (initial : FiniteProbabilityMass State)
    (policy : (step : Nat) → FiniteStateOutputPath State BoundaryOut step →
      JointOpenControl Context BoundaryIn Action) :
    ∀ horizon path,
      0 ≤ inducedFeedbackJointPathWeightAt process initial policy horizon path := by
  intro horizon
  induction horizon with
  | zero =>
      intro path
      exact initial.nonnegative path.down
  | succ prior inductionHypothesis =>
      intro path
      exact mul_nonneg (inductionHypothesis path.1)
        (process.nonnegative
          (finiteStateOutputPathLastState prior path.1)
          (policy prior path.1) path.2)

theorem inducedFeedbackJointPathWeightAt_normalized
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut)
    (initial : FiniteProbabilityMass State)
    (policy : (step : Nat) → FiniteStateOutputPath State BoundaryOut step →
      JointOpenControl Context BoundaryIn Action) :
    ∀ horizon,
      ∑ path : FiniteStateOutputPath State BoundaryOut horizon,
        inducedFeedbackJointPathWeightAt process initial policy horizon path = 1 := by
  intro horizon
  induction horizon with
  | zero =>
      calc
        (∑ path : FiniteStateOutputPath State BoundaryOut 0,
          inducedFeedbackJointPathWeightAt process initial policy 0 path) =
            ∑ state : State, initial.mass state := by
          exact (Fintype.sum_equiv
            (finiteStateOutputPathZeroEquiv State BoundaryOut)
            (fun state => initial.mass state)
            (fun path =>
              inducedFeedbackJointPathWeightAt process initial policy 0 path)
            (by intro state; rfl)).symm
        _ = 1 := initial.normalized
  | succ prior inductionHypothesis =>
      change
        (∑ path : FiniteStateOutputPath State BoundaryOut prior ×
            (State × BoundaryOut),
          inducedFeedbackJointPathWeightAt process initial policy prior path.1 *
            process.mass
              (finiteStateOutputPathLastState prior path.1)
              (policy prior path.1) path.2) = 1
      rw [Fintype.sum_prod_type]
      calc
        (∑ pathPrefix : FiniteStateOutputPath State BoundaryOut prior,
          ∑ outcome : State × BoundaryOut,
            inducedFeedbackJointPathWeightAt process initial policy prior pathPrefix *
              process.mass
                (finiteStateOutputPathLastState prior pathPrefix)
                (policy prior pathPrefix) outcome) =
            ∑ pathPrefix : FiniteStateOutputPath State BoundaryOut prior,
              inducedFeedbackJointPathWeightAt process initial policy prior pathPrefix *
                (∑ outcome : State × BoundaryOut,
                  process.mass
                    (finiteStateOutputPathLastState prior pathPrefix)
                    (policy prior pathPrefix) outcome) := by
          apply Finset.sum_congr rfl
          intro pathPrefix _
          rw [Finset.mul_sum]
        _ = ∑ pathPrefix : FiniteStateOutputPath State BoundaryOut prior,
              inducedFeedbackJointPathWeightAt process initial policy prior
                pathPrefix := by
          apply Finset.sum_congr rfl
          intro pathPrefix _
          rw [process.normalized]
          simp
        _ = 1 := inductionHypothesis

/-- Normalized state/output path law induced by a path-dependent policy. -/
def inducedFiniteFeedbackStateOutputPathLaw
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (experiment : FiniteJointFeedbackExperiment State Context BoundaryIn Action
      BoundaryOut) :
    FiniteProbabilityMass
      (FiniteStateOutputPath State BoundaryOut experiment.horizon) where
  mass := inducedFeedbackJointPathWeightAt experiment.process experiment.initial
    experiment.policy experiment.horizon
  nonnegative := inducedFeedbackJointPathWeightAt_nonnegative experiment.process
    experiment.initial experiment.policy experiment.horizon
  normalized := inducedFeedbackJointPathWeightAt_normalized experiment.process
    experiment.initial experiment.policy experiment.horizon

/-- Transport one context/boundary/action input through an abstraction. -/
def mapJointOpenControl
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
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    (abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut)
    (control : JointOpenControl Context BoundaryIn Action) :
    JointOpenControl AbstractContext AbstractBoundaryIn AbstractAction :=
  (abstraction.contextMap control.1,
    abstraction.boundaryInMap control.2.1,
    abstraction.actionMap control.2.2)

/-- Fine and abstract feedback experiments sharing one finite horizon. -/
structure AlignedJointFeedbackExperiments
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
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    (abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut) where
  horizon : Nat
  fineInitial : FiniteProbabilityMass State
  abstractInitial : FiniteProbabilityMass AbstractState
  finePolicy : (step : Nat) → FiniteStateOutputPath State BoundaryOut step →
    JointOpenControl Context BoundaryIn Action
  abstractPolicy : (step : Nat) →
    FiniteStateOutputPath AbstractState AbstractBoundaryOut step →
      JointOpenControl AbstractContext AbstractBoundaryIn AbstractAction

/-- Fine feedback experiment extracted from aligned data. -/
def AlignedJointFeedbackExperiments.fineExperiment
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
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (data : AlignedJointFeedbackExperiments abstraction) :
    FiniteJointFeedbackExperiment State Context BoundaryIn Action BoundaryOut where
  process := abstraction.fine
  horizon := data.horizon
  initial := data.fineInitial
  policy := data.finePolicy

/-- Abstract feedback experiment extracted from aligned data. -/
def AlignedJointFeedbackExperiments.abstractExperiment
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
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (data : AlignedJointFeedbackExperiments abstraction) :
    FiniteJointFeedbackExperiment AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut where
  process := abstraction.abstract
  horizon := data.horizon
  initial := data.abstractInitial
  policy := data.abstractPolicy

/-- Initial transport plus naturality of feedback control on every mapped prefix. -/
structure JointFeedbackExperimentTransportAlignment
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
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (data : AlignedJointFeedbackExperiments abstraction) where
  initial_transport : data.abstractInitial.mass =
    (pushforwardFiniteProbability abstraction.stateMap data.fineInitial).mass
  policy_transport : ∀ step finePrefix,
    data.abstractPolicy step
        (mapFiniteStateOutputPath abstraction.stateMap abstraction.boundaryOutMap
          step finePrefix) =
      mapJointOpenControl abstraction (data.finePolicy step finePrefix)

/-- Pointwise feedback-path factorization over one abstract path fibre. -/
theorem inducedFeedbackJointPathWeight_fibre_eq_abstract
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
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    (abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut)
    (fineInitial : FiniteProbabilityMass State)
    (abstractInitial : FiniteProbabilityMass AbstractState)
    (finePolicy : (step : Nat) → FiniteStateOutputPath State BoundaryOut step →
      JointOpenControl Context BoundaryIn Action)
    (abstractPolicy : (step : Nat) →
      FiniteStateOutputPath AbstractState AbstractBoundaryOut step →
        JointOpenControl AbstractContext AbstractBoundaryIn AbstractAction)
    (initialTransport : abstractInitial.mass =
      (pushforwardFiniteProbability abstraction.stateMap fineInitial).mass)
    (policyTransport : ∀ step finePrefix,
      abstractPolicy step
          (mapFiniteStateOutputPath abstraction.stateMap abstraction.boundaryOutMap
            step finePrefix) =
        mapJointOpenControl abstraction (finePolicy step finePrefix))
    (kernelCommutes : JointOpenKernelCommutes abstraction) :
    ∀ horizon abstractPath,
      (∑ finePath : FiniteStateOutputPath State BoundaryOut horizon,
        if mapFiniteStateOutputPath abstraction.stateMap abstraction.boundaryOutMap
            horizon finePath = abstractPath then
          inducedFeedbackJointPathWeightAt abstraction.fine fineInitial finePolicy
            horizon finePath
        else 0) =
      inducedFeedbackJointPathWeightAt abstraction.abstract abstractInitial
        abstractPolicy horizon abstractPath := by
  intro horizon
  induction horizon with
  | zero =>
      intro abstractPath
      rcases abstractPath with ⟨abstractState⟩
      have initialAt := congrFun initialTransport abstractState
      calc
        (∑ finePath : FiniteStateOutputPath State BoundaryOut 0,
          if mapFiniteStateOutputPath abstraction.stateMap
              abstraction.boundaryOutMap 0 finePath = ULift.up abstractState then
            inducedFeedbackJointPathWeightAt abstraction.fine fineInitial
              finePolicy 0 finePath
          else 0) =
            ∑ fineState : State,
              if (ULift.up (abstraction.stateMap fineState) :
                  FiniteStateOutputPath AbstractState AbstractBoundaryOut 0) =
                    ULift.up abstractState then
                fineInitial.mass fineState
              else 0 := by
          exact (Fintype.sum_equiv
            (finiteStateOutputPathZeroEquiv State BoundaryOut)
            (fun fineState =>
              if (ULift.up (abstraction.stateMap fineState) :
                  FiniteStateOutputPath AbstractState AbstractBoundaryOut 0) =
                    ULift.up abstractState then
                fineInitial.mass fineState
              else 0)
            (fun finePath =>
              if mapFiniteStateOutputPath abstraction.stateMap
                  abstraction.boundaryOutMap 0 finePath = ULift.up abstractState then
                inducedFeedbackJointPathWeightAt abstraction.fine fineInitial
                  finePolicy 0 finePath
              else 0)
            (by intro fineState; rfl)).symm
        _ = abstractInitial.mass abstractState := by
          simpa [pushforwardFiniteProbability] using initialAt.symm
  | succ prior inductionHypothesis =>
      intro abstractPath
      rcases abstractPath with ⟨abstractPrefix, abstractOutcome⟩
      have prefixFibre := inductionHypothesis abstractPrefix
      change (∑ finePath : FiniteStateOutputPath State BoundaryOut prior × (State × BoundaryOut), _) = _
      rw [Fintype.sum_prod_type]
      have pair_eq_iff (finePrefix : FiniteStateOutputPath State BoundaryOut prior)
          (fineOutcome : State × BoundaryOut) :
          (mapFiniteStateOutputPath abstraction.stateMap abstraction.boundaryOutMap prior finePrefix,
              jointOutcomeMap abstraction.stateMap abstraction.boundaryOutMap fineOutcome) =
              (abstractPrefix, abstractOutcome) ↔
            mapFiniteStateOutputPath abstraction.stateMap abstraction.boundaryOutMap prior finePrefix = abstractPrefix ∧
              jointOutcomeMap abstraction.stateMap abstraction.boundaryOutMap fineOutcome = abstractOutcome := by
        exact Prod.ext_iff
      simp only [mapFiniteStateOutputPath, inducedFeedbackJointPathWeightAt]
      simp_rw [pair_eq_iff]
      calc
        (∑ finePrefix,
          ∑ fineOutcome,
            if mapFiniteStateOutputPath abstraction.stateMap
                  abstraction.boundaryOutMap prior finePrefix = abstractPrefix ∧
                jointOutcomeMap abstraction.stateMap abstraction.boundaryOutMap
                  fineOutcome = abstractOutcome then
              inducedFeedbackJointPathWeightAt abstraction.fine fineInitial
                  finePolicy prior finePrefix *
                abstraction.fine.mass
                  (finiteStateOutputPathLastState prior finePrefix)
                  (finePolicy prior finePrefix) fineOutcome
            else 0) =
          ∑ finePrefix,
            if mapFiniteStateOutputPath abstraction.stateMap
                abstraction.boundaryOutMap prior finePrefix = abstractPrefix then
              inducedFeedbackJointPathWeightAt abstraction.fine fineInitial
                  finePolicy prior finePrefix *
                abstraction.abstract.mass
                  (finiteStateOutputPathLastState prior abstractPrefix)
                  (abstractPolicy prior abstractPrefix) abstractOutcome
            else 0 := by
          apply Finset.sum_congr rfl
          intro finePrefix _
          by_cases prefixMaps :
              mapFiniteStateOutputPath abstraction.stateMap
                abstraction.boundaryOutMap prior finePrefix = abstractPrefix
          · have endpointMaps :
                abstraction.stateMap
                    (finiteStateOutputPathLastState prior finePrefix) =
                  finiteStateOutputPathLastState prior abstractPrefix := by
              rw [← finiteStateOutputPathLastState_map abstraction.stateMap
                abstraction.boundaryOutMap prior finePrefix, prefixMaps]
            have currentPolicyTransport :
                abstractPolicy prior abstractPrefix =
                  mapJointOpenControl abstraction (finePolicy prior finePrefix) := by
              rw [← prefixMaps]
              exact policyTransport prior finePrefix
            have rowAt := congrFun
              (kernelCommutes
                (finiteStateOutputPathLastState prior finePrefix)
                (finePolicy prior finePrefix).1
                (finePolicy prior finePrefix).2.1
                (finePolicy prior finePrefix).2.2) abstractOutcome
            rw [currentPolicyTransport, ← endpointMaps]
            change _ = if mapFiniteStateOutputPath abstraction.stateMap
                abstraction.boundaryOutMap prior finePrefix = abstractPrefix then
              inducedFeedbackJointPathWeightAt abstraction.fine fineInitial finePolicy prior finePrefix *
                (jointStepProbability abstraction.abstract
                  (abstraction.stateMap (finiteStateOutputPathLastState prior finePrefix))
                  (abstraction.contextMap (finePolicy prior finePrefix).1,
                    abstraction.boundaryInMap (finePolicy prior finePrefix).2.1,
                    abstraction.actionMap (finePolicy prior finePrefix).2.2)).mass abstractOutcome
            else 0
            rw [rowAt]
            simp only [pushforwardFiniteProbability]
            simp only [prefixMaps, if_true]
            rw [Finset.mul_sum]
            apply Finset.sum_congr rfl
            intro fineOutcome _
            by_cases outcomeMaps :
                jointOutcomeMap abstraction.stateMap abstraction.boundaryOutMap
                  fineOutcome = abstractOutcome <;>
              simp [prefixMaps, outcomeMaps, jointStepProbability]
          · simp [prefixMaps]
        _ = (∑ finePrefix,
              if mapFiniteStateOutputPath abstraction.stateMap
                    abstraction.boundaryOutMap prior finePrefix = abstractPrefix then
                inducedFeedbackJointPathWeightAt abstraction.fine fineInitial
                  finePolicy prior finePrefix
              else 0) *
            abstraction.abstract.mass
              (finiteStateOutputPathLastState prior abstractPrefix)
              (abstractPolicy prior abstractPrefix) abstractOutcome := by
          rw [Finset.sum_mul]
          apply Finset.sum_congr rfl
          intro finePrefix _
          by_cases prefixMaps :
              mapFiniteStateOutputPath abstraction.stateMap
                abstraction.boundaryOutMap prior finePrefix = abstractPrefix <;>
            simp [prefixMaps]
        _ = inducedFeedbackJointPathWeightAt abstraction.abstract abstractInitial
              abstractPolicy prior abstractPrefix *
            abstraction.abstract.mass
              (finiteStateOutputPathLastState prior abstractPrefix)
              (abstractPolicy prior abstractPrefix) abstractOutcome := by
          rw [prefixFibre]
        _ = inducedFeedbackJointPathWeightAt abstraction.abstract abstractInitial
              abstractPolicy (prior + 1) (abstractPrefix, abstractOutcome) := rfl

/-- Fine feedback path law transported through both state and output maps. -/
def transportedFineFeedbackJointPathLaw
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
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (data : AlignedJointFeedbackExperiments abstraction) :
    FiniteProbabilityMass
      (FiniteStateOutputPath AbstractState AbstractBoundaryOut data.horizon) :=
  pushforwardFiniteProbability
    (mapFiniteStateOutputPath abstraction.stateMap abstraction.boundaryOutMap
      data.horizon)
    (inducedFiniteFeedbackStateOutputPathLaw data.fineExperiment)

/-- Exact finite feedback path transport under policy naturality and kernel commutation. -/
theorem jointOpenKernelCommutes_and_feedbackAlignment_imply_pathLawExact
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
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (data : AlignedJointFeedbackExperiments abstraction)
    (alignment : JointFeedbackExperimentTransportAlignment data)
    (kernelCommutes : JointOpenKernelCommutes abstraction) :
    (transportedFineFeedbackJointPathLaw data).mass =
      (inducedFiniteFeedbackStateOutputPathLaw data.abstractExperiment).mass := by
  funext abstractPath
  exact inducedFeedbackJointPathWeight_fibre_eq_abstract abstraction data.fineInitial
    data.abstractInitial data.finePolicy data.abstractPolicy
    alignment.initial_transport alignment.policy_transport kernelCommutes
    data.horizon abstractPath

end OCMaturityCompletionCycle
