import OCKIndividuationMSpaceComposition.ProductMeasureKL
import Mathlib.Probability.Kernel.Composition.IntegralCompProd
import Mathlib.Probability.Kernel.Composition.AbsolutelyContinuous
import Mathlib.Probability.Kernel.CompProdEqIff

namespace OCKIndividuationMSpaceComposition

open MeasureTheory InformationTheory ProbabilityTheory
open scoped ENNReal

/-!
## Measure-kernel KL chain rule under an explicit adapter contract

Mathlib supplies composition-product measures, their Fubini theorem, and
absolute-continuity criteria.  It does not presently expose a general theorem
factoring the Radon--Nikodym derivative of two composition-products with two
different base measures and kernels.  The structure below therefore records
the exact missing semantic adapter: the joint log-likelihood ratio must split
almost everywhere into a marginal term and a registered conditional term.

This is stronger than a finite table and weaker than pretending that every
kernel admits the factorization without measurability and integrability
hypotheses.  Once the contract is established in a domain, the KL chain rule
below is a theorem.
-/

variable {State Observation : Type*}
  [MeasurableSpace State] [MeasurableSpace Observation]

/-- Measurable kernel log-likelihood ratio.  It uses the jointly measurable
kernel Radon--Nikodym derivative rather than choosing unrelated pointwise
versions of the measure derivative. -/
noncomputable def kernelLogLikelihoodRatio
    (firstKernel secondKernel : Kernel State Observation)
    [MeasurableSpace.CountableOrCountablyGenerated State Observation]
    (state : State) (observation : Observation) : ℝ :=
  Real.log (firstKernel.rnDeriv secondKernel state observation).toReal

/-- A density on the state marginal lifts to the first coordinate of a
composition-product density.  This is the missing left-density companion to
Mathlib's `Measure.compProd_withDensity` for kernel densities. -/
theorem withDensity_compProd_left
    (stateMeasure : Measure State) (kernel : Kernel State Observation)
    [SFinite stateMeasure] [IsSFiniteKernel kernel]
    (density : State → ℝ≥0∞) (densityMeasurable : Measurable density) :
    stateMeasure.withDensity density ⊗ₘ kernel =
      (stateMeasure ⊗ₘ kernel).withDensity
        (fun history => density history.1) := by
  ext measurableSet hMeasurableSet
  rw [Measure.compProd_apply hMeasurableSet]
  rw [lintegral_withDensity_eq_lintegral_mul stateMeasure
    densityMeasurable (Kernel.measurable_kernel_prodMk_left
      hMeasurableSet)]
  rw [withDensity_apply _ hMeasurableSet]
  rw [← lintegral_indicator hMeasurableSet]
  rw [Measure.lintegral_compProd]
  congr with state
  calc
    density state * kernel state (Prod.mk state ⁻¹' measurableSet) =
        ∫⁻ _observation in Prod.mk state ⁻¹' measurableSet,
          density state ∂(kernel state) := by
      rw [setLIntegral_const]
    _ = ∫⁻ observation,
        measurableSet.indicator (fun history => density history.1)
          (state, observation) ∂(kernel state) := by
      rw [← lintegral_indicator (measurable_prodMk_left hMeasurableSet)]
      rfl
  exact (densityMeasurable.comp measurable_fst).indicator hMeasurableSet

/-- Radon--Nikodym derivative for a changed state marginal and an unchanged
conditional kernel. -/
theorem rnDeriv_compProd_same_kernel
    (firstState secondState : Measure State)
    (kernel : Kernel State Observation)
    [IsProbabilityMeasure firstState] [IsProbabilityMeasure secondState]
    [IsMarkovKernel kernel]
    (stateAbsolutelyContinuous : firstState ≪ secondState) :
    (firstState ⊗ₘ kernel).rnDeriv (secondState ⊗ₘ kernel) =ᵐ[
        secondState ⊗ₘ kernel]
      fun history => firstState.rnDeriv secondState history.1 := by
  have representation :
      firstState ⊗ₘ kernel =
        (secondState ⊗ₘ kernel).withDensity
          (fun history => firstState.rnDeriv secondState history.1) := by
    calc
      firstState ⊗ₘ kernel =
          secondState.withDensity (firstState.rnDeriv secondState) ⊗ₘ
            kernel := by
        rw [Measure.withDensity_rnDeriv_eq firstState secondState
          stateAbsolutelyContinuous]
      _ = (secondState ⊗ₘ kernel).withDensity
          (fun history => firstState.rnDeriv secondState history.1) :=
        withDensity_compProd_left secondState kernel
          (firstState.rnDeriv secondState)
          (Measure.measurable_rnDeriv firstState secondState)
  rw [representation]
  exact Measure.rnDeriv_withDensity (secondState ⊗ₘ kernel) (by fun_prop)

/-- Radon--Nikodym derivative for an unchanged state marginal and a changed
conditional kernel. -/
theorem rnDeriv_compProd_same_state
    (stateMeasure : Measure State)
    (firstKernel secondKernel : Kernel State Observation)
    [IsProbabilityMeasure stateMeasure]
    [IsMarkovKernel firstKernel] [IsMarkovKernel secondKernel]
    [MeasurableSpace.CountableOrCountablyGenerated State Observation]
    (kernelAbsolutelyContinuous : ∀ᵐ state ∂stateMeasure,
      firstKernel state ≪ secondKernel state) :
    (stateMeasure ⊗ₘ firstKernel).rnDeriv
        (stateMeasure ⊗ₘ secondKernel) =ᵐ[
          stateMeasure ⊗ₘ secondKernel]
      fun history => firstKernel.rnDeriv secondKernel
        history.1 history.2 := by
  have kernelRepresentation :
      firstKernel =ᵐ[stateMeasure]
        secondKernel.withDensity (firstKernel.rnDeriv secondKernel) := by
    filter_upwards [kernelAbsolutelyContinuous] with state hState
    exact (Kernel.withDensity_rnDeriv_eq hState).symm
  have representation :
      stateMeasure ⊗ₘ firstKernel =
        (stateMeasure ⊗ₘ secondKernel).withDensity
          (fun history => firstKernel.rnDeriv secondKernel
            history.1 history.2) := by
    calc
      stateMeasure ⊗ₘ firstKernel =
          stateMeasure ⊗ₘ secondKernel.withDensity
            (firstKernel.rnDeriv secondKernel) :=
        Measure.compProd_congr kernelRepresentation
      _ = (stateMeasure ⊗ₘ secondKernel).withDensity
          (fun history => firstKernel.rnDeriv secondKernel
            history.1 history.2) := by
        exact Measure.compProd_withDensity
          (Kernel.measurable_rnDeriv firstKernel secondKernel)
  rw [representation]
  exact Measure.rnDeriv_withDensity (stateMeasure ⊗ₘ secondKernel)
    (by fun_prop)

/-- Full Radon--Nikodym chain rule for a changed state marginal and changed
conditional kernel, stated under the generating first joint law. -/
theorem rnDeriv_compProd_eq_marginal_mul_kernel
    (firstState secondState : Measure State)
    (firstKernel secondKernel : Kernel State Observation)
    [IsProbabilityMeasure firstState] [IsProbabilityMeasure secondState]
    [IsMarkovKernel firstKernel] [IsMarkovKernel secondKernel]
    [MeasurableSpace.CountableOrCountablyGenerated State Observation]
    (stateAbsolutelyContinuous : firstState ≪ secondState)
    (kernelAbsolutelyContinuous : ∀ᵐ state ∂firstState,
      firstKernel state ≪ secondKernel state) :
    (firstState ⊗ₘ firstKernel).rnDeriv
        (secondState ⊗ₘ secondKernel) =ᵐ[
          firstState ⊗ₘ firstKernel]
      fun history =>
        firstState.rnDeriv secondState history.1 *
          firstKernel.rnDeriv secondKernel history.1 history.2 := by
  let firstJoint := firstState ⊗ₘ firstKernel
  let intermediateJoint := firstState ⊗ₘ secondKernel
  let secondJoint := secondState ⊗ₘ secondKernel
  have firstToIntermediate : firstJoint ≪ intermediateJoint :=
    Measure.AbsolutelyContinuous.compProd_right kernelAbsolutelyContinuous
  have intermediateToSecond : intermediateJoint ≪ secondJoint :=
    stateAbsolutelyContinuous.compProd_left secondKernel
  have kernelFactorIntermediate := rnDeriv_compProd_same_state firstState
    firstKernel secondKernel kernelAbsolutelyContinuous
  have kernelFactorFirst :=
    firstToIntermediate.ae_le kernelFactorIntermediate
  have marginalFactorSecond := rnDeriv_compProd_same_kernel firstState
    secondState secondKernel stateAbsolutelyContinuous
  have marginalFactorFirst :=
    (firstToIntermediate.trans intermediateToSecond).ae_le marginalFactorSecond
  have transitiveFactorIntermediate :=
    Measure.rnDeriv_mul_rnDeriv'
      (μ := firstJoint) (ν := intermediateJoint) (κ := secondJoint)
      intermediateToSecond
  have transitiveFactorFirst :=
    firstToIntermediate.ae_le transitiveFactorIntermediate
  filter_upwards [kernelFactorFirst, marginalFactorFirst,
    transitiveFactorFirst] with history hKernel hMarginal hTransitive
  simp only [Pi.mul_apply] at hTransitive
  calc
    firstJoint.rnDeriv secondJoint history =
        firstJoint.rnDeriv intermediateJoint history *
          intermediateJoint.rnDeriv secondJoint history :=
      hTransitive.symm
    _ = firstKernel.rnDeriv secondKernel history.1 history.2 *
        firstState.rnDeriv secondState history.1 := by
      rw [hKernel, hMarginal]
    _ = firstState.rnDeriv secondState history.1 *
        firstKernel.rnDeriv secondKernel history.1 history.2 := mul_comm _ _

/-- Full log-likelihood chain rule obtained from the Radon--Nikodym chain,
not postulated as an external equality. -/
theorem llr_compProd_eq_marginal_add_kernel
    (firstState secondState : Measure State)
    (firstKernel secondKernel : Kernel State Observation)
    [IsProbabilityMeasure firstState] [IsProbabilityMeasure secondState]
    [IsMarkovKernel firstKernel] [IsMarkovKernel secondKernel]
    [MeasurableSpace.CountableOrCountablyGenerated State Observation]
    (stateAbsolutelyContinuous : firstState ≪ secondState)
    (kernelAbsolutelyContinuous : ∀ᵐ state ∂firstState,
      firstKernel state ≪ secondKernel state) :
    llr (firstState ⊗ₘ firstKernel)
        (secondState ⊗ₘ secondKernel) =ᵐ[
          firstState ⊗ₘ firstKernel]
      fun history =>
        llr firstState secondState history.1 +
          kernelLogLikelihoodRatio firstKernel secondKernel
            history.1 history.2 := by
  have jointAbsolutelyContinuous :
      firstState ⊗ₘ firstKernel ≪ secondState ⊗ₘ secondKernel :=
    stateAbsolutelyContinuous.compProd kernelAbsolutelyContinuous
  have factorization := rnDeriv_compProd_eq_marginal_mul_kernel firstState
    secondState firstKernel secondKernel stateAbsolutelyContinuous
    kernelAbsolutelyContinuous
  have factorizationFirst := factorization
  have positive := Measure.rnDeriv_pos jointAbsolutelyContinuous
  have finite := jointAbsolutelyContinuous.ae_le
    (Measure.rnDeriv_lt_top (firstState ⊗ₘ firstKernel)
      (secondState ⊗ₘ secondKernel))
  filter_upwards [factorizationFirst, positive, finite] with history
    hFactor hPositive hFinite
  have productToRealPositive :
      0 < ((firstState ⊗ₘ firstKernel).rnDeriv
        (secondState ⊗ₘ secondKernel) history).toReal :=
    ENNReal.toReal_pos hPositive.ne' hFinite.ne
  rw [hFactor, ENNReal.toReal_mul] at productToRealPositive
  have marginalToRealPositive :
      0 < (firstState.rnDeriv secondState history.1).toReal :=
    pos_of_mul_pos_left productToRealPositive ENNReal.toReal_nonneg
  have kernelToRealPositive :
      0 < (firstKernel.rnDeriv secondKernel
        history.1 history.2).toReal :=
    pos_of_mul_pos_right productToRealPositive ENNReal.toReal_nonneg
  simp only [llr_def, kernelLogLikelihoodRatio, hFactor, ENNReal.toReal_mul]
  exact Real.log_mul marginalToRealPositive.ne' kernelToRealPositive.ne'

/-- Exact hypotheses needed to lift a conditional information decomposition
from registered stochastic kernels to KL information of their joint laws. -/
structure KernelKLChainContract
    (firstState secondState : Measure State)
    (firstKernel secondKernel : Kernel State Observation)
    [IsProbabilityMeasure firstState] [IsProbabilityMeasure secondState]
    [IsMarkovKernel firstKernel] [IsMarkovKernel secondKernel] where
  marginalAbsolutelyContinuous : firstState ≪ secondState
  jointAbsolutelyContinuous :
    firstState ⊗ₘ firstKernel ≪ secondState ⊗ₘ secondKernel
  conditionalLogLikelihood : State → Observation → ℝ
  marginalIntegrable : Integrable (llr firstState secondState) firstState
  liftedMarginalIntegrable :
    Integrable (fun history : State × Observation =>
      llr firstState secondState history.1) (firstState ⊗ₘ firstKernel)
  conditionalIntegrable :
    Integrable (Function.uncurry conditionalLogLikelihood)
      (firstState ⊗ₘ firstKernel)
  jointLogLikelihoodDecomposition :
    llr (firstState ⊗ₘ firstKernel) (secondState ⊗ₘ secondKernel) =ᵐ[
        firstState ⊗ₘ firstKernel]
      fun history =>
        llr firstState secondState history.1 +
          conditionalLogLikelihood history.1 history.2

/-- The domain-observable conditional information contributed by the kernel,
averaged under the first joint law. -/
noncomputable def KernelKLChainContract.conditionalInformation
    {firstState secondState : Measure State}
    {firstKernel secondKernel : Kernel State Observation}
    [IsProbabilityMeasure firstState] [IsProbabilityMeasure secondState]
    [IsMarkovKernel firstKernel] [IsMarkovKernel secondKernel]
    (contract : KernelKLChainContract firstState secondState
      firstKernel secondKernel) : ℝ :=
  ∫ state, ∫ observation,
    contract.conditionalLogLikelihood state observation
      ∂(firstKernel state) ∂firstState

/-- General measure-kernel KL chain rule under the explicit likelihood
factorization contract. -/
theorem toReal_klDiv_compProd_eq_add_conditional
    (firstState secondState : Measure State)
    (firstKernel secondKernel : Kernel State Observation)
    [IsProbabilityMeasure firstState] [IsProbabilityMeasure secondState]
    [IsMarkovKernel firstKernel] [IsMarkovKernel secondKernel]
    (contract : KernelKLChainContract firstState secondState
      firstKernel secondKernel) :
    (klDiv (firstState ⊗ₘ firstKernel)
        (secondState ⊗ₘ secondKernel)).toReal =
      (klDiv firstState secondState).toReal +
        contract.conditionalInformation := by
  have jointIntegrable :
      Integrable
        (llr (firstState ⊗ₘ firstKernel)
          (secondState ⊗ₘ secondKernel))
        (firstState ⊗ₘ firstKernel) :=
    (contract.liftedMarginalIntegrable.add
      contract.conditionalIntegrable).congr
        contract.jointLogLikelihoodDecomposition.symm
  rw [toReal_klDiv contract.jointAbsolutelyContinuous jointIntegrable,
    toReal_klDiv contract.marginalAbsolutelyContinuous
      contract.marginalIntegrable]
  simp only [probReal_univ]
  rw [integral_congr_ae contract.jointLogLikelihoodDecomposition]
  change
    (∫ history : State × Observation,
        (fun history => llr firstState secondState history.1 +
          Function.uncurry contract.conditionalLogLikelihood history) history
          ∂(firstState ⊗ₘ firstKernel)) + 1 - 1 = _
  rw [integral_add contract.liftedMarginalIntegrable
    contract.conditionalIntegrable]
  rw [Measure.integral_compProd contract.liftedMarginalIntegrable]
  rw [Measure.integral_compProd contract.conditionalIntegrable]
  simp only [integral_const, probReal_univ, one_smul]
  rw [KernelKLChainContract.conditionalInformation]
  simp only [Function.uncurry]
  ring

/-- General measure-kernel KL chain rule with the conditional term expressed
as the actual kernel log-likelihood ratio.  The Radon--Nikodym factorization is
derived above; only the finite-information integrability conditions remain as
explicit hypotheses. -/
theorem toReal_klDiv_compProd_chain_rule
    (firstState secondState : Measure State)
    (firstKernel secondKernel : Kernel State Observation)
    [IsProbabilityMeasure firstState] [IsProbabilityMeasure secondState]
    [IsMarkovKernel firstKernel] [IsMarkovKernel secondKernel]
    [MeasurableSpace.CountableOrCountablyGenerated State Observation]
    (stateAbsolutelyContinuous : firstState ≪ secondState)
    (kernelAbsolutelyContinuous : ∀ᵐ state ∂firstState,
      firstKernel state ≪ secondKernel state)
    (marginalIntegrable : Integrable (llr firstState secondState) firstState)
    (liftedMarginalIntegrable :
      Integrable (fun history : State × Observation =>
        llr firstState secondState history.1)
        (firstState ⊗ₘ firstKernel))
    (conditionalIntegrable :
      Integrable
        (fun history : State × Observation =>
          kernelLogLikelihoodRatio firstKernel secondKernel
            history.1 history.2)
        (firstState ⊗ₘ firstKernel)) :
    (klDiv (firstState ⊗ₘ firstKernel)
        (secondState ⊗ₘ secondKernel)).toReal =
      (klDiv firstState secondState).toReal +
        ∫ state, ∫ observation,
          kernelLogLikelihoodRatio firstKernel secondKernel state observation
            ∂(firstKernel state) ∂firstState := by
  let contract : KernelKLChainContract firstState secondState
      firstKernel secondKernel := {
    marginalAbsolutelyContinuous := stateAbsolutelyContinuous
    jointAbsolutelyContinuous :=
      stateAbsolutelyContinuous.compProd kernelAbsolutelyContinuous
    conditionalLogLikelihood := fun state observation =>
      kernelLogLikelihoodRatio firstKernel secondKernel state observation
    marginalIntegrable := marginalIntegrable
    liftedMarginalIntegrable := liftedMarginalIntegrable
    conditionalIntegrable := conditionalIntegrable
    jointLogLikelihoodDecomposition :=
      llr_compProd_eq_marginal_add_kernel firstState secondState
        firstKernel secondKernel stateAbsolutelyContinuous
        kernelAbsolutelyContinuous
  }
  simpa [contract, KernelKLChainContract.conditionalInformation] using
    toReal_klDiv_compProd_eq_add_conditional firstState secondState
      firstKernel secondKernel contract

/-- No-go for an observationally decorative kernel.  If the registered
conditional likelihood is zero almost everywhere, composition adds exactly
no KL discrimination. -/
theorem zero_conditional_likelihood_adds_no_kernel_information
    (firstState secondState : Measure State)
    (firstKernel secondKernel : Kernel State Observation)
    [IsProbabilityMeasure firstState] [IsProbabilityMeasure secondState]
    [IsMarkovKernel firstKernel] [IsMarkovKernel secondKernel]
    (contract : KernelKLChainContract firstState secondState
      firstKernel secondKernel)
    (conditionalZero :
      Function.uncurry contract.conditionalLogLikelihood =ᵐ[
        firstState ⊗ₘ firstKernel] 0) :
    (klDiv (firstState ⊗ₘ firstKernel)
        (secondState ⊗ₘ secondKernel)).toReal =
      (klDiv firstState secondState).toReal := by
  rw [toReal_klDiv_compProd_eq_add_conditional firstState secondState
    firstKernel secondKernel contract]
  have integralZero : contract.conditionalInformation = 0 := by
    rw [KernelKLChainContract.conditionalInformation]
    change
      (∫ state, ∫ observation,
        Function.uncurry contract.conditionalLogLikelihood
          (state, observation) ∂(firstKernel state) ∂firstState) = 0
    rw [← Measure.integral_compProd contract.conditionalIntegrable]
    rw [integral_congr_ae conditionalZero]
    simp
  rw [integralZero, add_zero]

/-- A strictly positive registered conditional contribution produces a
strict improvement over the state marginal. -/
theorem marginal_kl_lt_joint_kl_of_positive_conditional
    (firstState secondState : Measure State)
    (firstKernel secondKernel : Kernel State Observation)
    [IsProbabilityMeasure firstState] [IsProbabilityMeasure secondState]
    [IsMarkovKernel firstKernel] [IsMarkovKernel secondKernel]
    (contract : KernelKLChainContract firstState secondState
      firstKernel secondKernel)
    (conditionalPositive : 0 < contract.conditionalInformation) :
    (klDiv firstState secondState).toReal <
      (klDiv (firstState ⊗ₘ firstKernel)
        (secondState ⊗ₘ secondKernel)).toReal := by
  rw [toReal_klDiv_compProd_eq_add_conditional firstState secondState
    firstKernel secondKernel contract]
  exact lt_add_of_pos_right _ conditionalPositive

/-- Exact falsifiability criterion: within a valid chain contract, the joint
law has the same KL information as the marginal exactly when the registered
conditional information is zero. -/
theorem joint_kl_eq_marginal_kl_iff_conditionalInformation_eq_zero
    (firstState secondState : Measure State)
    (firstKernel secondKernel : Kernel State Observation)
    [IsProbabilityMeasure firstState] [IsProbabilityMeasure secondState]
    [IsMarkovKernel firstKernel] [IsMarkovKernel secondKernel]
    (contract : KernelKLChainContract firstState secondState
      firstKernel secondKernel) :
    (klDiv (firstState ⊗ₘ firstKernel)
        (secondState ⊗ₘ secondKernel)).toReal =
        (klDiv firstState secondState).toReal ↔
      contract.conditionalInformation = 0 := by
  rw [toReal_klDiv_compProd_eq_add_conditional firstState secondState
    firstKernel secondKernel contract]
  constructor <;> intro h
  · linarith
  · rw [h, add_zero]

end OCKIndividuationMSpaceComposition
