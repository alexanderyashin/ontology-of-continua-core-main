import OCKIndividuationMSpaceComposition.TaskConditionedOptics
import Mathlib.Order.Preorder.Finite

namespace OCKIndividuationMSpaceComposition

universe uOptic uCost

inductive OpticAbstention where
  | insufficientObservation
  | insufficientData
  | taskNotIdentifiable
  | opticRefinementRequired
  | noBudgetFeasibleOptic
  deriving DecidableEq, Repr

/-- The declared finite contract.  `riskUpper` already includes the chosen
confidence construction; the separate predicate prevents a numerical upper
bound from being used without its evidence contract. -/
def OpticContractAdmissible
    {Optic : Type uOptic} {CostDimension : Type uCost}
    [Fintype CostDimension]
    (registered : Finset Optic)
    (riskUpper : Optic → ℝ) (epsilon : ℝ)
    (confidenceMet : Optic → Prop)
    (cost : Optic → CostDimension → ℝ)
    (budget : CostDimension → ℝ)
    (optic : Optic) : Prop :=
  optic ∈ registered ∧ riskUpper optic ≤ epsilon ∧ confidenceMet optic ∧
    ∀ dimension, cost optic dimension ≤ budget dimension

/-- Pareto minimality among contract-admissible optics.  Weak domination must
be reversible, so equal cost vectors may coexist and uniqueness is not
silently asserted. -/
def IsParetoMinimalOptic
    {Optic : Type uOptic} {CostDimension : Type uCost}
    [Fintype CostDimension]
    (admissible : Optic → Prop)
    (cost : Optic → CostDimension → ℝ)
    (optic : Optic) : Prop :=
  admissible optic ∧
    ∀ other, admissible other → cost other ≤ cost optic → cost optic ≤ cost other

noncomputable def finiteParetoOptics
    {Optic : Type uOptic} {CostDimension : Type uCost}
    [Fintype CostDimension]
    (registered : Finset Optic)
    (admissible : Optic → Prop)
    (cost : Optic → CostDimension → ℝ) : Finset Optic := by
  classical
  exact registered.filter (IsParetoMinimalOptic admissible cost)

theorem finiteParetoOptics_member_is_admissible_and_minimal
    {Optic : Type uOptic} {CostDimension : Type uCost}
    [Fintype CostDimension]
    (registered : Finset Optic)
    (admissible : Optic → Prop)
    (cost : Optic → CostDimension → ℝ)
    {optic : Optic}
    (member : optic ∈ finiteParetoOptics registered admissible cost) :
    IsParetoMinimalOptic admissible cost optic := by
  classical
  exact (Finset.mem_filter.mp (by simpa [finiteParetoOptics] using member)).2

/-- The generic Pareto theorem specializes to the full task contract: every
returned optic meets the registered risk, confidence and componentwise budget
bounds. -/
theorem contract_pareto_member_meets_declared_bounds
    {Optic : Type uOptic} {CostDimension : Type uCost}
    [Fintype CostDimension]
    (registered : Finset Optic)
    (riskUpper : Optic → ℝ) (epsilon : ℝ)
    (confidenceMet : Optic → Prop)
    (cost : Optic → CostDimension → ℝ)
    (budget : CostDimension → ℝ)
    {optic : Optic}
    (member : optic ∈ finiteParetoOptics registered
      (OpticContractAdmissible registered riskUpper epsilon confidenceMet cost budget)
      cost) :
    optic ∈ registered ∧ riskUpper optic ≤ epsilon ∧ confidenceMet optic ∧
      ∀ dimension, cost optic dimension ≤ budget dimension := by
  exact (finiteParetoOptics_member_is_admissible_and_minimal
    registered
    (OpticContractAdmissible registered riskUpper epsilon confidenceMet cost budget)
    cost member).1

/-- Every registered admissible optic is weakly dominated by a returned
Pareto-minimal optic.  This is the finite completeness theorem needed to
justify rejecting a dominated candidate. -/
theorem finiteParetoOptics_covers_every_admissible
    {Optic : Type uOptic} {CostDimension : Type uCost}
    [Fintype CostDimension]
    (registered : Finset Optic)
    (admissible : Optic → Prop)
    (admissibleRegistered : ∀ optic, admissible optic → optic ∈ registered)
    (cost : Optic → CostDimension → ℝ)
    {candidate : Optic} (candidateAdmissible : admissible candidate) :
    ∃ selected ∈ finiteParetoOptics registered admissible cost,
      cost selected ≤ cost candidate := by
  classical
  let eligible : Set Optic := {optic | admissible optic}
  have eligibleFinite : eligible.Finite := by
    apply Set.Finite.subset registered.finite_toSet
    intro optic opticEligible
    exact admissibleRegistered optic opticEligible
  let costSet : Set (CostDimension → ℝ) := cost '' eligible
  have costSetFinite : costSet.Finite := eligibleFinite.image cost
  have candidateCostMember : cost candidate ∈ costSet :=
    ⟨candidate, candidateAdmissible, rfl⟩
  obtain ⟨minimalCost, minimalLe, minimal⟩ :=
    costSetFinite.exists_le_minimal candidateCostMember
  rcases minimal.1 with ⟨selected, selectedAdmissible, selectedCost⟩
  have selectedMinimal : IsParetoMinimalOptic admissible cost selected := by
    refine ⟨selectedAdmissible, ?_⟩
    intro other otherAdmissible otherLe
    have otherCostMember : cost other ∈ costSet :=
      ⟨other, otherAdmissible, rfl⟩
    have minimalBack : minimalCost ≤ cost other :=
      minimal.2 otherCostMember (by simpa [selectedCost] using otherLe)
    simpa [selectedCost] using minimalBack
  refine ⟨selected, ?_, ?_⟩
  · simp [finiteParetoOptics, admissibleRegistered selected selectedAdmissible,
      selectedMinimal]
  · simpa [selectedCost] using minimalLe

theorem finiteParetoOptics_nonempty_iff_admissible_exists
    {Optic : Type uOptic} {CostDimension : Type uCost}
    [Fintype CostDimension]
    (registered : Finset Optic)
    (admissible : Optic → Prop)
    (admissibleRegistered : ∀ optic, admissible optic → optic ∈ registered)
    (cost : Optic → CostDimension → ℝ) :
    (finiteParetoOptics registered admissible cost).Nonempty ↔
      ∃ optic, admissible optic := by
  constructor
  · rintro ⟨optic, member⟩
    exact ⟨optic,
      (finiteParetoOptics_member_is_admissible_and_minimal
        registered admissible cost member).1⟩
  · rintro ⟨candidate, candidateAdmissible⟩
    obtain ⟨selected, selectedMember, _⟩ :=
      finiteParetoOptics_covers_every_admissible
        registered admissible admissibleRegistered cost candidateAdmissible
    exact ⟨selected, selectedMember⟩

inductive FiniteOpticSelectionResult (Optic : Type uOptic) where
  | selected (optics : Finset Optic)
  | abstain (reason : OpticAbstention)

noncomputable def SelectFiniteOptics
    {Optic : Type uOptic} {CostDimension : Type uCost}
    [Fintype CostDimension]
    (registered : Finset Optic)
    (admissible : Optic → Prop)
    (cost : Optic → CostDimension → ℝ)
    (failureReason : OpticAbstention) : FiniteOpticSelectionResult Optic := by
  classical
  let selected := finiteParetoOptics registered admissible cost
  exact if selected.Nonempty then .selected selected else .abstain failureReason

theorem selector_abstains_when_no_optic_is_admissible
    {Optic : Type uOptic} {CostDimension : Type uCost}
    [Fintype CostDimension]
    (registered : Finset Optic)
    (admissible : Optic → Prop)
    (admissibleRegistered : ∀ optic, admissible optic → optic ∈ registered)
    (cost : Optic → CostDimension → ℝ)
    (failureReason : OpticAbstention)
    (noneAdmissible : ¬ ∃ optic, admissible optic) :
    SelectFiniteOptics registered admissible cost failureReason =
      .abstain failureReason := by
  classical
  have empty : ¬ (finiteParetoOptics registered admissible cost).Nonempty := by
    intro nonempty
    exact noneAdmissible
      ((finiteParetoOptics_nonempty_iff_admissible_exists
        registered admissible admissibleRegistered cost).mp nonempty)
  simp [SelectFiniteOptics, empty]

theorem selector_returns_pareto_set_when_admissible_exists
    {Optic : Type uOptic} {CostDimension : Type uCost}
    [Fintype CostDimension]
    (registered : Finset Optic)
    (admissible : Optic → Prop)
    (admissibleRegistered : ∀ optic, admissible optic → optic ∈ registered)
    (cost : Optic → CostDimension → ℝ)
    (failureReason : OpticAbstention)
    (existsAdmissible : ∃ optic, admissible optic) :
    SelectFiniteOptics registered admissible cost failureReason =
      .selected (finiteParetoOptics registered admissible cost) := by
  classical
  have nonempty : (finiteParetoOptics registered admissible cost).Nonempty :=
    (finiteParetoOptics_nonempty_iff_admissible_exists
      registered admissible admissibleRegistered cost).mpr existsAdmissible
  simp [SelectFiniteOptics, nonempty]

end OCKIndividuationMSpaceComposition
