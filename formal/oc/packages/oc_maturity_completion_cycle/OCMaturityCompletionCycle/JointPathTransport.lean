import OCMaturityCompletionCycle.CrossStateAbstractionBounds

/-!
# Joint path-law transport from one-step commutation

The theorem below makes the one-step open-kernel condition operative: exact
initial and policy transport plus exact joint state/output commutation imply
exact transport of every induced finite path law.
-/

namespace OCMaturityCompletionCycle

universe uState uContext uBoundaryIn uAction uBoundaryOut
  uAbstractState uAbstractContext uAbstractBoundaryIn uAbstractAction
  uAbstractBoundaryOut

/-- Mapping a joint path commutes with taking its last state. -/
theorem finiteStateOutputPathLastState_map
    {State : Type uState}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    (stateMap : State → AbstractState)
    (boundaryOutMap : BoundaryOut → AbstractBoundaryOut) :
    ∀ horizon path,
      finiteStateOutputPathLastState horizon
          (mapFiniteStateOutputPath stateMap boundaryOutMap horizon path) =
        stateMap (finiteStateOutputPathLastState horizon path) := by
  intro horizon
  cases horizon <;> intro path <;> rfl

/--
Pointwise finite-path factorization.  The left side sums the fine path weights
over exactly one abstract path fibre.
-/
theorem inducedJointPathWeight_fibre_eq_abstract
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
    (finePolicy : Nat → JointOpenControl Context BoundaryIn Action)
    (abstractPolicy : Nat →
      JointOpenControl AbstractContext AbstractBoundaryIn AbstractAction)
    (initialTransport : abstractInitial.mass =
      (pushforwardFiniteProbability abstraction.stateMap fineInitial).mass)
    (kernelCommutes : JointOpenKernelCommutes abstraction) :
    ∀ horizon,
      (∀ step, step < horizon →
        abstractPolicy step =
          (abstraction.contextMap (finePolicy step).1,
            abstraction.boundaryInMap (finePolicy step).2.1,
            abstraction.actionMap (finePolicy step).2.2)) →
      ∀ abstractPath :
        FiniteStateOutputPath AbstractState AbstractBoundaryOut horizon,
        (∑ finePath : FiniteStateOutputPath State BoundaryOut horizon,
          if mapFiniteStateOutputPath abstraction.stateMap
              abstraction.boundaryOutMap horizon finePath = abstractPath then
            inducedJointPathWeightAt abstraction.fine fineInitial finePolicy
              horizon finePath
          else 0) =
        inducedJointPathWeightAt abstraction.abstract abstractInitial
          abstractPolicy horizon abstractPath := by
  intro horizon
  induction horizon with
  | zero =>
      intro policyTransport abstractPath
      rcases abstractPath with ⟨abstractState⟩
      have initialAt := congrFun initialTransport abstractState
      calc
        (∑ finePath : FiniteStateOutputPath State BoundaryOut 0,
          if mapFiniteStateOutputPath abstraction.stateMap
              abstraction.boundaryOutMap 0 finePath = ULift.up abstractState then
            inducedJointPathWeightAt abstraction.fine fineInitial finePolicy
              0 finePath
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
                inducedJointPathWeightAt abstraction.fine fineInitial finePolicy
                  0 finePath
              else 0)
            (by intro fineState; rfl)).symm
        _ = abstractInitial.mass abstractState := by
          simpa [pushforwardFiniteProbability] using initialAt.symm
  | succ prior inductionHypothesis =>
      intro policyTransport abstractPath
      rcases abstractPath with ⟨abstractPrefix, abstractOutcome⟩
      have priorPolicyTransport : ∀ step, step < prior →
          abstractPolicy step =
            (abstraction.contextMap (finePolicy step).1,
              abstraction.boundaryInMap (finePolicy step).2.1,
              abstraction.actionMap (finePolicy step).2.2) := by
        intro step stepPrior
        exact policyTransport step (Nat.lt.step stepPrior)
      have currentPolicyTransport := policyTransport prior (Nat.lt_succ_self prior)
      have prefixFibre := inductionHypothesis priorPolicyTransport abstractPrefix
      have pair_eq_iff (finePrefix : FiniteStateOutputPath State BoundaryOut prior)
          (fineOutcome : State × BoundaryOut) :
          (mapFiniteStateOutputPath abstraction.stateMap abstraction.boundaryOutMap prior finePrefix,
              jointOutcomeMap abstraction.stateMap abstraction.boundaryOutMap fineOutcome) =
              (abstractPrefix, abstractOutcome) ↔
            mapFiniteStateOutputPath abstraction.stateMap abstraction.boundaryOutMap prior finePrefix = abstractPrefix ∧
              jointOutcomeMap abstraction.stateMap abstraction.boundaryOutMap fineOutcome = abstractOutcome := by
        exact Prod.ext_iff
      change (∑ finePath : FiniteStateOutputPath State BoundaryOut prior × (State × BoundaryOut), _) = _
      rw [Fintype.sum_prod_type]
      simp only [mapFiniteStateOutputPath, inducedJointPathWeightAt]
      simp_rw [pair_eq_iff]
      calc
        (∑ finePrefix,
          ∑ fineOutcome,
            if mapFiniteStateOutputPath abstraction.stateMap
                  abstraction.boundaryOutMap prior finePrefix = abstractPrefix ∧
                jointOutcomeMap abstraction.stateMap abstraction.boundaryOutMap
                  fineOutcome = abstractOutcome then
              inducedJointPathWeightAt abstraction.fine fineInitial finePolicy
                  prior finePrefix *
                abstraction.fine.mass
                  (finiteStateOutputPathLastState prior finePrefix)
                  (finePolicy prior) fineOutcome
            else 0) =
          ∑ finePrefix,
            if mapFiniteStateOutputPath abstraction.stateMap
                abstraction.boundaryOutMap prior finePrefix = abstractPrefix then
              inducedJointPathWeightAt abstraction.fine fineInitial finePolicy
                  prior finePrefix *
                abstraction.abstract.mass
                  (abstraction.stateMap (finiteStateOutputPathLastState prior finePrefix))
                  (abstractPolicy prior) abstractOutcome
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
            have rowAt := congrFun
              (kernelCommutes
                (finiteStateOutputPathLastState prior finePrefix)
                (finePolicy prior).1 (finePolicy prior).2.1
                (finePolicy prior).2.2) abstractOutcome
            rw [currentPolicyTransport]
            change _ = if mapFiniteStateOutputPath abstraction.stateMap
                abstraction.boundaryOutMap prior finePrefix = abstractPrefix then
                inducedJointPathWeightAt abstraction.fine fineInitial finePolicy prior finePrefix *
                (jointStepProbability abstraction.abstract
                  (abstraction.stateMap (finiteStateOutputPathLastState prior finePrefix))
                  (abstraction.contextMap (finePolicy prior).1,
                    abstraction.boundaryInMap (finePolicy prior).2.1,
                    abstraction.actionMap (finePolicy prior).2.2)).mass abstractOutcome
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
                inducedJointPathWeightAt abstraction.fine fineInitial finePolicy
                  prior finePrefix
              else 0) *
            abstraction.abstract.mass
              (finiteStateOutputPathLastState prior abstractPrefix)
              (abstractPolicy prior) abstractOutcome := by
          rw [Finset.sum_mul]
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
            simp [prefixMaps, endpointMaps]
          · simp [prefixMaps]
        _ = inducedJointPathWeightAt abstraction.abstract abstractInitial
              abstractPolicy prior abstractPrefix *
            abstraction.abstract.mass
              (finiteStateOutputPathLastState prior abstractPrefix)
              (abstractPolicy prior) abstractOutcome := by
          rw [prefixFibre]
        _ = inducedJointPathWeightAt abstraction.abstract abstractInitial
              abstractPolicy (prior + 1) (abstractPrefix, abstractOutcome) := rfl

/-- One-step exactness and aligned inputs force exact finite path-law transport. -/
theorem jointOpenKernelCommutes_and_alignment_imply_pathLawExact
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
    [DecidableEq AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (data : AlignedJointOpenExperiments abstraction)
    (alignment : JointExperimentTransportAlignment data)
    (kernelCommutes : JointOpenKernelCommutes abstraction) :
    (transportedFineJointPathLaw data).mass =
      (inducedFiniteStateOutputPathLaw data.abstractExperiment).mass := by
  funext abstractPath
  exact inducedJointPathWeight_fibre_eq_abstract abstraction data.fineInitial
    data.abstractInitial data.finePolicy data.abstractPolicy
    alignment.initial_transport kernelCommutes data.horizon
    alignment.policy_transport abstractPath

/-- Exact one-step commutation and alignment make stitching defect vanish. -/
theorem jointOpenKernelCommutes_and_alignment_imply_zero_stitchingDefect
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
    [DecidableEq AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (data : AlignedJointOpenExperiments abstraction)
    (alignment : JointExperimentTransportAlignment data)
    (kernelCommutes : JointOpenKernelCommutes abstraction) :
    jointOpenPathStitchingDefect data = 0 :=
  (jointOpenPathStitchingDefect_eq_zero_iff_exact data).2
    (jointOpenKernelCommutes_and_alignment_imply_pathLawExact data alignment
      kernelCommutes)

end OCMaturityCompletionCycle
