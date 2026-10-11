import OCKIndividuationMSpaceComposition.StochasticKernelDefectBridge
import OCKIndividuationMSpaceComposition.OpenDiscreteDynamics
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe uState uAction uQuotient uFineState uAbstractState uFineAction
  uAbstractAction

/-!
# Operational stochastic quotient radius and contractive transport

Classical approximate-lumpability and Dobrushin theory supply the metric
ingredients used here.  The OC-specific bridge is the typed chain

`same optic cell -> pairwise pushed-row diameter -> unavoidable quotient-row
radius -> finite-horizon prediction envelope`.

The pairwise theorem is a minimax no-go: every single memoryless quotient row
approximating two fine representatives within `epsilon` forces their mutual
TV separation to be at most `2 * epsilon`.  The midpoint of two finite laws
attains exactly half their separation, so the factor two is sharp already on
a two-representative fibre.  A supplied section constructs a normalized
quotient kernel with row error bounded by the fibre diameter.  Under an
independently verified TV contraction of that quotient kernel, this structural
row error propagates through the standard geometric envelope.
-/

/-! ## The sharp two-law radius -/

/-- Finite total variation is symmetric. -/
theorem finiteTotalVariation_symm
    {Outcome : Type uState}
    [Fintype Outcome]
    (left right : FiniteProbabilityMass Outcome) :
    finiteTotalVariation left right = finiteTotalVariation right left := by
  simp only [finiteTotalVariation]
  congr 1
  apply Finset.sum_congr rfl
  intro outcome _
  exact abs_sub_comm _ _

/-- The normalized midpoint of two finite probability laws. -/
def finiteProbabilityMidpoint
    {Outcome : Type uState}
    [Fintype Outcome]
    (left right : FiniteProbabilityMass Outcome) :
    FiniteProbabilityMass Outcome where
  mass outcome := (left.mass outcome + right.mass outcome) / 2
  nonnegative outcome := by
    exact div_nonneg
      (add_nonneg (left.nonnegative outcome) (right.nonnegative outcome))
      (by norm_num)
  normalized := by
    simp_rw [div_eq_mul_inv]
    rw [← Finset.sum_mul, Finset.sum_add_distrib, left.normalized,
      right.normalized]
    norm_num [div_eq_mul_inv]

/-- The midpoint is exactly half the pairwise TV distance from the left law. -/
theorem finiteTotalVariation_left_midpoint
    {Outcome : Type uState}
    [Fintype Outcome]
    (left right : FiniteProbabilityMass Outcome) :
    finiteTotalVariation left (finiteProbabilityMidpoint left right) =
      finiteTotalVariation left right / 2 := by
  simp only [finiteTotalVariation, finiteProbabilityMidpoint]
  have pointwise :
      ∀ outcome,
        |left.mass outcome - (left.mass outcome + right.mass outcome) / 2| =
          |left.mass outcome - right.mass outcome| / 2 := by
    intro outcome
    rw [show left.mass outcome -
          (left.mass outcome + right.mass outcome) / 2 =
        (left.mass outcome - right.mass outcome) / 2 by ring]
    rw [div_eq_mul_inv, abs_mul]
    norm_num
    ring
  simp_rw [pointwise]
  simp_rw [div_eq_mul_inv]
  rw [← Finset.sum_mul]

/-- The midpoint is exactly half the pairwise TV distance from the right law. -/
theorem finiteTotalVariation_right_midpoint
    {Outcome : Type uState}
    [Fintype Outcome]
    (left right : FiniteProbabilityMass Outcome) :
    finiteTotalVariation right (finiteProbabilityMidpoint left right) =
      finiteTotalVariation left right / 2 := by
  rw [finiteTotalVariation_symm right (finiteProbabilityMidpoint left right)]
  simp only [finiteTotalVariation, finiteProbabilityMidpoint]
  have pointwise :
      ∀ outcome,
        |(left.mass outcome + right.mass outcome) / 2 - right.mass outcome| =
          |left.mass outcome - right.mass outcome| / 2 := by
    intro outcome
    rw [show (left.mass outcome + right.mass outcome) / 2 -
          right.mass outcome =
        (left.mass outcome - right.mass outcome) / 2 by ring]
    rw [div_eq_mul_inv, abs_mul]
    norm_num [div_eq_mul_inv]
  simp_rw [pointwise]
  simp_rw [div_eq_mul_inv]
  rw [← Finset.sum_mul]

/-- No common centre can put two laws inside a radius smaller than half their
mutual TV separation. -/
theorem any_common_tv_radius_ge_half_pairwise
    {Outcome : Type uState}
    [Fintype Outcome]
    (left right centre : FiniteProbabilityMass Outcome)
    (epsilon : ℚ)
    (leftBound : finiteTotalVariation left centre ≤ epsilon)
    (rightBound : finiteTotalVariation right centre ≤ epsilon) :
    finiteTotalVariation left right / 2 ≤ epsilon := by
  have triangle := finiteTotalVariation_triangle left centre right
  have centreToRight : finiteTotalVariation centre right ≤ epsilon := by
    rw [finiteTotalVariation_symm]
    exact rightBound
  linarith

/-- Matching upper and lower theorem: for two finite laws the exact minimax
radius is half their TV separation, attained by their midpoint. -/
theorem two_law_tv_minimax_radius_characterization
    {Outcome : Type uState}
    [Fintype Outcome]
    (left right : FiniteProbabilityMass Outcome) :
    (finiteTotalVariation left
        (finiteProbabilityMidpoint left right) =
      finiteTotalVariation left right / 2) ∧
    (finiteTotalVariation right
        (finiteProbabilityMidpoint left right) =
      finiteTotalVariation left right / 2) ∧
    (∀ centre epsilon,
      finiteTotalVariation left centre ≤ epsilon →
      finiteTotalVariation right centre ≤ epsilon →
      finiteTotalVariation left right / 2 ≤ epsilon) := by
  exact ⟨finiteTotalVariation_left_midpoint left right,
    finiteTotalVariation_right_midpoint left right,
    fun centre epsilon leftBound rightBound =>
      any_common_tv_radius_ge_half_pairwise left right centre epsilon
        leftBound rightBound⟩

/-! ## Finite-sample adapter once row confidence radii are supplied -/

/-- If each estimated row is within `eta` of its true row, the estimated
pairwise TV separation differs from the true separation by at most `2*eta`.
The theorem is deterministic; a statistical adapter must separately justify
the two confidence-radius premises. -/
theorem finiteTV_pair_estimation_error_le_two_eta
    {Outcome : Type uState}
    [Fintype Outcome]
    (trueLeft trueRight estimatedLeft estimatedRight :
      FiniteProbabilityMass Outcome)
    (eta : ℚ)
    (leftError : finiteTotalVariation trueLeft estimatedLeft ≤ eta)
    (rightError : finiteTotalVariation trueRight estimatedRight ≤ eta) :
    |finiteTotalVariation trueLeft trueRight -
      finiteTotalVariation estimatedLeft estimatedRight| ≤ 2 * eta := by
  have estimatedRightToTrueRight :
      finiteTotalVariation estimatedRight trueRight ≤ eta := by
    rw [finiteTotalVariation_symm]
    exact rightError
  have trueUpper :
      finiteTotalVariation trueLeft trueRight ≤
        finiteTotalVariation estimatedLeft estimatedRight + 2 * eta := by
    have firstTriangle :=
      finiteTotalVariation_triangle trueLeft estimatedLeft trueRight
    have secondTriangle :=
      finiteTotalVariation_triangle estimatedLeft estimatedRight trueRight
    linarith
  have trueLeftToEstimatedLeft :
      finiteTotalVariation estimatedLeft trueLeft ≤ eta := by
    rw [finiteTotalVariation_symm]
    exact leftError
  have estimatedUpper :
      finiteTotalVariation estimatedLeft estimatedRight ≤
        finiteTotalVariation trueLeft trueRight + 2 * eta := by
    have firstTriangle :=
      finiteTotalVariation_triangle estimatedLeft trueLeft estimatedRight
    have secondTriangle :=
      finiteTotalVariation_triangle trueLeft trueRight estimatedRight
    linarith
  rw [abs_le]
  constructor <;> linarith

/-- Observable no-go rule: after adding the two row-estimation radii, an
estimated separation still forces a lower bound on every true common quotient
radius. -/
theorem empirical_pairwise_separation_forces_true_radius
    {Outcome : Type uState}
    [Fintype Outcome]
    (trueLeft trueRight estimatedLeft estimatedRight centre :
      FiniteProbabilityMass Outcome)
    (eta epsilon : ℚ)
    (leftError : finiteTotalVariation trueLeft estimatedLeft ≤ eta)
    (rightError : finiteTotalVariation trueRight estimatedRight ≤ eta)
    (leftRadius : finiteTotalVariation trueLeft centre ≤ epsilon)
    (rightRadius : finiteTotalVariation trueRight centre ≤ epsilon) :
    finiteTotalVariation estimatedLeft estimatedRight / 2 - eta ≤ epsilon := by
  have estimation := finiteTV_pair_estimation_error_le_two_eta
    trueLeft trueRight estimatedLeft estimatedRight eta leftError rightError
  have radius := any_common_tv_radius_ge_half_pairwise
    trueLeft trueRight centre epsilon leftRadius rightRadius
  rw [abs_le] at estimation
  linarith

/-! ## Structural fibre diameter and approximate quotient kernels -/

/-- Every same-cell pushed-row pair is within the declared operational
diameter for one action. -/
def PairwiseLumpabilityDiameterBound
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [Fintype Quotient]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient)
    (action : Action)
    (diameter : ℚ) : Prop :=
  ∀ ⦃left right : State⦄,
    encode left = encode right →
      sameCellRowTV kernel encode left right action ≤ diameter

/-- A candidate quotient kernel has a uniform row radius around all pushed
fine rows for the registered action. -/
def ApproximateQuotientRowBound
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [Fintype Quotient]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (abstract : FiniteControlledKernel Quotient Action)
    (encode : State → Quotient)
    (action : Action)
    (epsilon : ℚ) : Prop :=
  TransportedKernelRowTVBound kernel abstract encode id action epsilon

/-- Any quotient row of radius `epsilon` forces every same-cell pair to have
diameter at most `2 * epsilon`.  This is the operational lower bound absent
from a zero-only lumpability defect. -/
theorem approximateQuotientRowBound_implies_pairwise_two_radius
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [Fintype Quotient]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (abstract : FiniteControlledKernel Quotient Action)
    (encode : State → Quotient)
    (action : Action)
    (epsilon : ℚ)
    (uniform : ApproximateQuotientRowBound kernel abstract encode action epsilon)
    {left right : State}
    (sameCell : encode left = encode right) :
    sameCellRowTV kernel encode left right action ≤ 2 * epsilon := by
  have leftBound := uniform left
  have rightBound := uniform right
  change finiteTotalVariation
      (pushedKernelRowProbability kernel encode left action)
      (pushedKernelRowProbability kernel encode right action) ≤ 2 * epsilon
  have rightBound' :
      finiteTotalVariation
        (pushedKernelRowProbability kernel encode right action)
        (kernelRowProbability abstract (encode left) action) ≤ epsilon := by
    simpa [ApproximateQuotientRowBound, pushedKernelRowProbability,
      sameCell] using rightBound
  have triangle := finiteTotalVariation_triangle
    (pushedKernelRowProbability kernel encode left action)
    (kernelRowProbability abstract (encode left) action)
    (pushedKernelRowProbability kernel encode right action)
  have centreToRight :
      finiteTotalVariation
        (kernelRowProbability abstract (encode left) action)
        (pushedKernelRowProbability kernel encode right action) ≤ epsilon := by
    rw [finiteTotalVariation_symm]
    exact rightBound'
  have leftBound' :
      finiteTotalVariation
        (pushedKernelRowProbability kernel encode left action)
        (kernelRowProbability abstract (encode left) action) ≤ epsilon := by
    simpa [ApproximateQuotientRowBound, pushedKernelRowProbability] using leftBound
  linarith

/-- Quantitative no-go: a candidate radius strictly below half one witnessed
same-cell separation is impossible for every memoryless quotient kernel. -/
theorem subhalf_pairwise_radius_no_approximate_quotient
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [Fintype Quotient]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient)
    (action : Action)
    (epsilon : ℚ)
    {left right : State}
    (sameCell : encode left = encode right)
    (tooSmall : epsilon < sameCellRowTV kernel encode left right action / 2) :
    ∀ abstract : FiniteControlledKernel Quotient Action,
      ¬ ApproximateQuotientRowBound kernel abstract encode action epsilon := by
  intro abstract uniform
  have bound := approximateQuotientRowBound_implies_pairwise_two_radius
    kernel abstract encode action epsilon uniform sameCell
  linarith

/-- A chosen representative in every quotient cell induces a normalized
memoryless quotient kernel, without claiming representative independence. -/
def representativeQuotientKernel
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [Fintype Quotient]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient)
    (chooseRepresentative : Quotient → State) :
    FiniteControlledKernel Quotient Action where
  mass source action target :=
    (pushedKernelRowProbability kernel encode
      (chooseRepresentative source) action).mass target
  nonnegative source action target :=
    (pushedKernelRowProbability kernel encode
      (chooseRepresentative source) action).nonnegative target
  normalized source action :=
    (pushedKernelRowProbability kernel encode
      (chooseRepresentative source) action).normalized

/-- A right-inverse section turns a fibre-diameter bound into an explicit
quotient-kernel row bound of the same radius. -/
theorem representativeQuotientKernel_rowBound_of_pairwiseDiameter
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [Fintype Quotient]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient)
    (chooseRepresentative : Quotient → State)
    (rightInverse : Function.RightInverse chooseRepresentative encode)
    (action : Action)
    (diameter : ℚ)
    (pairwise : PairwiseLumpabilityDiameterBound kernel encode action diameter) :
    ApproximateQuotientRowBound kernel
      (representativeQuotientKernel kernel encode chooseRepresentative)
      encode action diameter := by
  intro state
  have sameCell :
      encode state = encode (chooseRepresentative (encode state)) :=
    (rightInverse (encode state)).symm
  have bound := pairwise sameCell
  simpa [ApproximateQuotientRowBound, sameCellRowTV,
    representativeQuotientKernel, pushedKernelRowProbability,
    kernelRowProbability] using bound

/-! ## Contractive finite-horizon transport -/

/-- The one-step transported error contracts the inherited mismatch and adds
only the registered row error. -/
theorem transportedEvolve_tv_le_contracted_initial_add_rowError
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : FiniteControlledKernel FineState FineAction)
    (abstract : FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (action : FineAction)
    (fineInitial : FiniteProbabilityMass FineState)
    (abstractInitial : FiniteProbabilityMass AbstractState)
    (epsilon rho : ℚ)
    (uniform : TransportedKernelRowTVBound fine abstract stateMap actionMap
      action epsilon)
    (contraction : FiniteEvolutionContraction abstract (actionMap action) rho) :
    finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveFiniteProbability fine action fineInitial))
        (evolveFiniteProbability abstract (actionMap action) abstractInitial) ≤
      rho * finiteTotalVariation
        (pushforwardFiniteProbability stateMap fineInitial) abstractInitial +
      epsilon := by
  let transportedInitial := pushforwardFiniteProbability stateMap fineInitial
  have rowMixture :
      finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveFiniteProbability fine action fineInitial))
        (evolveFiniteProbability abstract (actionMap action)
          transportedInitial) ≤ epsilon := by
    simp only [finiteTotalVariation]
    rw [pushforward_evolve_mass_eq_transportedRowMixture,
      evolve_pushforward_mass_eq_mappedAbstractRowMixture]
    exact finiteProbabilityMixture_tv_le_uniform_row_tv fineInitial _ _ epsilon
      uniform
  calc
    finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveFiniteProbability fine action fineInitial))
        (evolveFiniteProbability abstract (actionMap action) abstractInitial) ≤
      finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveFiniteProbability fine action fineInitial))
        (evolveFiniteProbability abstract (actionMap action)
          transportedInitial) +
      finiteTotalVariation
        (evolveFiniteProbability abstract (actionMap action) transportedInitial)
        (evolveFiniteProbability abstract (actionMap action) abstractInitial) :=
      finiteTotalVariation_triangle _ _ _
    _ ≤ epsilon + rho * finiteTotalVariation transportedInitial abstractInitial :=
      add_le_add rowMixture (contraction transportedInitial abstractInitial)
    _ = rho * finiteTotalVariation
        (pushforwardFiniteProbability stateMap fineInitial) abstractInitial +
      epsilon := by ring

/-- Sequential transported laws obey the exact geometric robust envelope when
every abstract step has the declared common TV contraction coefficient. -/
theorem transportedEvolveMany_tv_le_robustErrorEnvelope
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : Nat → FiniteControlledKernel FineState FineAction)
    (abstract : Nat → FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (actions : Nat → FineAction)
    (fineInitial : FiniteProbabilityMass FineState)
    (abstractInitial : FiniteProbabilityMass AbstractState)
    (epsilon rho : ℚ)
    (rhoNonnegative : 0 ≤ rho)
    (uniform : ∀ step,
      TransportedKernelRowTVBound (fine step) (abstract step) stateMap actionMap
        (actions step) epsilon)
    (contractions : ∀ step,
      FiniteEvolutionContraction (abstract step)
        (actionMap (actions step)) rho) :
    ∀ horizon,
    finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveMany fine actions horizon fineInitial))
        (evolveMany abstract (fun step => actionMap (actions step)) horizon
          abstractInitial) ≤
      robustErrorEnvelope rho epsilon
        (finiteTotalVariation
          (pushforwardFiniteProbability stateMap fineInitial) abstractInitial)
        horizon := by
  intro horizon
  induction horizon with
  | zero => simp [evolveMany, robustErrorEnvelope]
  | succ prior inductionHypothesis =>
      have oneStep := transportedEvolve_tv_le_contracted_initial_add_rowError
        (fine prior) (abstract prior) stateMap actionMap (actions prior)
        (evolveMany fine actions prior fineInitial)
        (evolveMany abstract (fun step => actionMap (actions step)) prior
          abstractInitial)
        epsilon rho (uniform prior) (contractions prior)
      calc
        finiteTotalVariation
            (pushforwardFiniteProbability stateMap
              (evolveMany fine actions (prior + 1) fineInitial))
            (evolveMany abstract (fun step => actionMap (actions step))
              (prior + 1) abstractInitial) ≤
          rho * finiteTotalVariation
            (pushforwardFiniteProbability stateMap
              (evolveMany fine actions prior fineInitial))
            (evolveMany abstract (fun step => actionMap (actions step)) prior
              abstractInitial) + epsilon := oneStep
        _ ≤ rho * robustErrorEnvelope rho epsilon
            (finiteTotalVariation
              (pushforwardFiniteProbability stateMap fineInitial)
              abstractInitial) prior + epsilon := by
          have scaled :=
            mul_le_mul_of_nonneg_left inductionHypothesis rhoNonnegative
          linarith
        _ = robustErrorEnvelope rho epsilon
            (finiteTotalVariation
              (pushforwardFiniteProbability stateMap fineInitial)
              abstractInitial) (prior + 1) := rfl

/-- Exact initial alignment and strict contraction give a uniform finite
horizon plateau. -/
theorem transportedEvolveMany_tv_le_strict_contraction_plateau
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : Nat → FiniteControlledKernel FineState FineAction)
    (abstract : Nat → FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (actions : Nat → FineAction)
    (fineInitial : FiniteProbabilityMass FineState)
    (epsilon rho : ℚ)
    (rhoNonnegative : 0 ≤ rho)
    (rhoLessThanOne : rho < 1)
    (epsilonNonnegative : 0 ≤ epsilon)
    (uniform : ∀ step,
      TransportedKernelRowTVBound (fine step) (abstract step) stateMap actionMap
        (actions step) epsilon)
    (contractions : ∀ step,
      FiniteEvolutionContraction (abstract step)
        (actionMap (actions step)) rho)
    (horizon : Nat) :
    finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveMany fine actions horizon fineInitial))
        (evolveMany abstract (fun step => actionMap (actions step)) horizon
          (pushforwardFiniteProbability stateMap fineInitial)) ≤
      epsilon / (1 - rho) := by
  have envelope := transportedEvolveMany_tv_le_robustErrorEnvelope
    fine abstract stateMap actionMap actions fineInitial
    (pushforwardFiniteProbability stateMap fineInitial) epsilon rho
    rhoNonnegative uniform contractions horizon
  have plateau := robustErrorEnvelope_le_contracting_plateau
    rho epsilon 0 rhoNonnegative rhoLessThanOne epsilonNonnegative
    (by norm_num) horizon
  have initialZero :
      finiteTotalVariation
        (pushforwardFiniteProbability stateMap fineInitial)
        (pushforwardFiniteProbability stateMap fineInitial) = 0 := by
    exact (finiteTotalVariation_eq_zero_iff_mass_eq _ _).2 rfl
  rw [initialZero] at envelope
  linarith

/-- End-to-end OC bridge: fibre diameter plus a representative section and a
verified quotient contraction yield the numeric horizon prediction envelope. -/
theorem representativeQuotient_horizon_error_le_plateau
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [Fintype Quotient]
    [DecidableEq Quotient]
    (fine : Nat → FiniteControlledKernel State Action)
    (encode : State → Quotient)
    (chooseRepresentative : Quotient → State)
    (rightInverse : Function.RightInverse chooseRepresentative encode)
    (actions : Nat → Action)
    (initial : FiniteProbabilityMass State)
    (diameter rho : ℚ)
    (diameterNonnegative : 0 ≤ diameter)
    (rhoNonnegative : 0 ≤ rho)
    (rhoLessThanOne : rho < 1)
    (pairwise : ∀ step,
      PairwiseLumpabilityDiameterBound (fine step) encode (actions step)
        diameter)
    (contractions : ∀ step,
      FiniteEvolutionContraction
        (representativeQuotientKernel (fine step) encode chooseRepresentative)
        (actions step) rho)
    (horizon : Nat) :
    finiteTotalVariation
        (pushforwardFiniteProbability encode
          (evolveMany fine actions horizon initial))
        (evolveMany
          (fun step => representativeQuotientKernel
            (fine step) encode chooseRepresentative)
          actions horizon (pushforwardFiniteProbability encode initial)) ≤
      diameter / (1 - rho) := by
  apply transportedEvolveMany_tv_le_strict_contraction_plateau
    fine
    (fun step => representativeQuotientKernel
      (fine step) encode chooseRepresentative)
    encode id actions initial diameter rho rhoNonnegative rhoLessThanOne
    diameterNonnegative
  · intro step
    exact representativeQuotientKernel_rowBound_of_pairwiseDiameter
      (fine step) encode chooseRepresentative rightInverse (actions step) diameter
      (pairwise step)
  · exact contractions

end OCKIndividuationMSpaceComposition
