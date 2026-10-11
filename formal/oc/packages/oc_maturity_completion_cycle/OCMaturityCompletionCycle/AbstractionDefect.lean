import OCMaturityCompletionCycle.ContextualOpenDynamics

/-!
# Five finite law defects and coherence-gated exactness

All five scientific components are concrete sums of finite total variations.
Memory, state, and resource costs are reported separately and are not silently
treated as failures of exactness.
-/

namespace OCMaturityCompletionCycle

universe uIndex uOutcome

/-- Two finite law families compared on one frozen index/outcome universe. -/
structure FiniteLawComparison
    (Index : Type uIndex)
    (Outcome : Type uOutcome)
    [Fintype Outcome] where
  reference : Index → FiniteProbabilityMass Outcome
  abstracted : Index → FiniteProbabilityMass Outcome

/-- Exact agreement of a frozen finite law comparison. -/
def FiniteLawComparison.Exact
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (comparison : FiniteLawComparison Index Outcome) : Prop :=
  FiniteLawFamilyExact comparison.reference comparison.abstracted

/-- Aggregate total-variation defect of a frozen finite law comparison. -/
def FiniteLawComparison.defect
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Index]
    [Fintype Outcome]
    (comparison : FiniteLawComparison Index Outcome) : ℚ :=
  finiteLawFamilyDefect comparison.reference comparison.abstracted

/-- Concrete zero/exact characterization for any frozen comparison. -/
theorem FiniteLawComparison.defect_eq_zero_iff_exact
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Index]
    [Fintype Outcome]
    (comparison : FiniteLawComparison Index Outcome) :
    comparison.defect = 0 ↔ comparison.Exact :=
  finiteLawFamilyDefect_eq_zero_iff_exact _ _

/-- The five declared scientific comparison lanes. -/
structure FiveLawComparisons
    (Index : Type uIndex)
    (Outcome : Type uOutcome)
    [Fintype Outcome] where
  prediction : FiniteLawComparison Index Outcome
  lumpability : FiniteLawComparison Index Outcome
  boundary : FiniteLawComparison Index Outcome
  context : FiniteLawComparison Index Outcome
  stitching : FiniteLawComparison Index Outcome

/-- Quantitative defect vector plus non-epistemic representation costs. -/
structure AbstractionDefect where
  prediction : ℚ
  lumpability : ℚ
  boundary : ℚ
  context : ℚ
  stitching : ℚ
  memoryCost : Nat
  stateCost : Nat
  resourceCost : Nat

/-- Construct the defect vector from five primitive TV comparisons. -/
def measuredAbstractionDefect
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Index]
    [Fintype Outcome]
    (comparisons : FiveLawComparisons Index Outcome)
    (memoryCost stateCost resourceCost : Nat) : AbstractionDefect where
  prediction := comparisons.prediction.defect
  lumpability := comparisons.lumpability.defect
  boundary := comparisons.boundary.defect
  context := comparisons.context.defect
  stitching := comparisons.stitching.defect
  memoryCost := memoryCost
  stateCost := stateCost
  resourceCost := resourceCost

/-- Every scientific component vanishes; costs are intentionally excluded. -/
def AbstractionDefect.ZeroScientificComponents
    (defect : AbstractionDefect) : Prop :=
  defect.prediction = 0 ∧
    defect.lumpability = 0 ∧
    defect.boundary = 0 ∧
    defect.context = 0 ∧
    defect.stitching = 0

/-- Exactness of all five frozen comparison lanes. -/
def FiveLawComparisons.Exact
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (comparisons : FiveLawComparisons Index Outcome) : Prop :=
  comparisons.prediction.Exact ∧
    comparisons.lumpability.Exact ∧
    comparisons.boundary.Exact ∧
    comparisons.context.Exact ∧
    comparisons.stitching.Exact

/-- Prediction defect is zero exactly when the prediction laws agree. -/
theorem predictionDefect_eq_zero_iff_exact
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Index]
    [Fintype Outcome]
    (comparisons : FiveLawComparisons Index Outcome) :
    comparisons.prediction.defect = 0 ↔ comparisons.prediction.Exact :=
  comparisons.prediction.defect_eq_zero_iff_exact

/-- Lumpability defect is zero exactly when representative laws agree. -/
theorem lumpabilityDefect_eq_zero_iff_exact
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Index]
    [Fintype Outcome]
    (comparisons : FiveLawComparisons Index Outcome) :
    comparisons.lumpability.defect = 0 ↔ comparisons.lumpability.Exact :=
  comparisons.lumpability.defect_eq_zero_iff_exact

/-- Boundary defect is zero exactly when the frozen boundary laws agree. -/
theorem boundaryDefect_eq_zero_iff_exact
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Index]
    [Fintype Outcome]
    (comparisons : FiveLawComparisons Index Outcome) :
    comparisons.boundary.defect = 0 ↔ comparisons.boundary.Exact :=
  comparisons.boundary.defect_eq_zero_iff_exact

/-- Context defect is zero exactly when the frozen context laws agree. -/
theorem contextDefect_eq_zero_iff_exact
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Index]
    [Fintype Outcome]
    (comparisons : FiveLawComparisons Index Outcome) :
    comparisons.context.defect = 0 ↔ comparisons.context.Exact :=
  comparisons.context.defect_eq_zero_iff_exact

/-- Stitching defect is zero exactly when the frozen path laws agree. -/
theorem stitchingDefect_eq_zero_iff_exact
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Index]
    [Fintype Outcome]
    (comparisons : FiveLawComparisons Index Outcome) :
    comparisons.stitching.defect = 0 ↔ comparisons.stitching.Exact :=
  comparisons.stitching.defect_eq_zero_iff_exact

/-- The five concrete zero tests are jointly equivalent to five exact laws. -/
theorem scientificDefects_zero_iff_fiveExact
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Index]
    [Fintype Outcome]
    (comparisons : FiveLawComparisons Index Outcome)
    (memoryCost stateCost resourceCost : Nat) :
    AbstractionDefect.ZeroScientificComponents
        (measuredAbstractionDefect comparisons memoryCost stateCost resourceCost) ↔
      comparisons.Exact := by
  simp only [AbstractionDefect.ZeroScientificComponents,
    measuredAbstractionDefect, FiveLawComparisons.Exact]
  rw [predictionDefect_eq_zero_iff_exact,
    lumpabilityDefect_eq_zero_iff_exact,
    boundaryDefect_eq_zero_iff_exact,
    contextDefect_eq_zero_iff_exact,
    stitchingDefect_eq_zero_iff_exact]

/-- Joint exactness explicitly includes both independent coherence gates. -/
def CoherentJointExactness
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (identityStateCompatible lawRealized : Prop)
    (comparisons : FiveLawComparisons Index Outcome) : Prop :=
  identityStateCompatible ∧ lawRealized ∧ comparisons.Exact

/--
N1 component synthesis: under proofs of both independent gates, zero scientific
defects characterize the declared joint exactness.  This is not an N3 claim.
-/
theorem coherentJointExactness_iff_zeroScientificDefects
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Index]
    [Fintype Outcome]
    (identityStateCompatible lawRealized : Prop)
    (identityGate : identityStateCompatible)
    (lawGate : lawRealized)
    (comparisons : FiveLawComparisons Index Outcome)
    (memoryCost stateCost resourceCost : Nat) :
    CoherentJointExactness identityStateCompatible lawRealized comparisons ↔
      AbstractionDefect.ZeroScientificComponents
        (measuredAbstractionDefect comparisons memoryCost stateCost resourceCost) := by
  rw [scientificDefects_zero_iff_fiveExact]
  constructor
  · exact fun joint => joint.2.2
  · exact fun exactFive => ⟨identityGate, lawGate, exactFive⟩

end OCMaturityCompletionCycle
