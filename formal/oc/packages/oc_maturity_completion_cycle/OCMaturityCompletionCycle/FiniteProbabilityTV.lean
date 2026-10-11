import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Piecewise
import Mathlib.Data.Fintype.Basic
import Mathlib.Tactic.NormNum

/-!
# Primitive finite probability and total variation

This layer does not reuse the signed `MassVector` abbreviation as a probability
type.  Nonnegativity and normalization are explicit fields.
-/

namespace OCMaturityCompletionCycle

universe uOutcome uIndex

/-- An exact rational probability mass on a finite carrier. -/
structure FiniteProbabilityMass
    (Outcome : Type uOutcome)
    [Fintype Outcome] where
  mass : Outcome → ℚ
  nonnegative : ∀ outcome, 0 ≤ mass outcome
  normalized : ∑ outcome, mass outcome = 1

/-- Finite total variation, one half of the `ℓ¹` distance. -/
def finiteTotalVariation
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (left right : FiniteProbabilityMass Outcome) : ℚ :=
  (∑ outcome, |left.mass outcome - right.mass outcome|) / 2

/-- Total variation is nonnegative. -/
theorem finiteTotalVariation_nonnegative
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (left right : FiniteProbabilityMass Outcome) :
    0 ≤ finiteTotalVariation left right := by
  apply div_nonneg
  · exact Finset.sum_nonneg fun _ _ => abs_nonneg _
  · norm_num

/-- Finite total variation vanishes exactly when the mass functions agree. -/
theorem finiteTotalVariation_eq_zero_iff_mass_eq
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (left right : FiniteProbabilityMass Outcome) :
    finiteTotalVariation left right = 0 ↔ left.mass = right.mass := by
  constructor
  · intro variationZero
    have sumZero :
        ∑ outcome, |left.mass outcome - right.mass outcome| = 0 := by
      simpa [finiteTotalVariation] using variationZero
    funext outcome
    have everyTermZero :
        (fun candidate => |left.mass candidate - right.mass candidate|) = 0 :=
      (Fintype.sum_eq_zero_iff_of_nonneg fun candidate =>
        abs_nonneg (left.mass candidate - right.mass candidate)).mp sumZero
    have termZero : |left.mass outcome - right.mass outcome| = 0 :=
      congrFun everyTermZero outcome
    exact sub_eq_zero.mp (abs_eq_zero.mp termZero)
  · intro sameMass
    simp [finiteTotalVariation, sameMass]

/-- Exact equality of two finite law families. -/
def FiniteLawFamilyExact
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    (left right : Index → FiniteProbabilityMass Outcome) : Prop :=
  ∀ index, (left index).mass = (right index).mass

/-- Aggregate total-variation defect of a finite indexed family. -/
def finiteLawFamilyDefect
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Index]
    [Fintype Outcome]
    (left right : Index → FiniteProbabilityMass Outcome) : ℚ :=
  ∑ index, finiteTotalVariation (left index) (right index)

/-- The aggregate family defect is nonnegative. -/
theorem finiteLawFamilyDefect_nonnegative
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Index]
    [Fintype Outcome]
    (left right : Index → FiniteProbabilityMass Outcome) :
    0 ≤ finiteLawFamilyDefect left right := by
  exact Finset.sum_nonneg fun _ _ => finiteTotalVariation_nonnegative _ _

/-- A finite aggregate defect is zero exactly when every indexed law agrees. -/
theorem finiteLawFamilyDefect_eq_zero_iff_exact
    {Index : Type uIndex}
    {Outcome : Type uOutcome}
    [Fintype Index]
    [Fintype Outcome]
    (left right : Index → FiniteProbabilityMass Outcome) :
    finiteLawFamilyDefect left right = 0 ↔
      FiniteLawFamilyExact left right := by
  constructor
  · intro defectZero index
    have everyTermZero :
        (fun candidate => finiteTotalVariation (left candidate) (right candidate)) = 0 :=
      (Fintype.sum_eq_zero_iff_of_nonneg fun candidate =>
        finiteTotalVariation_nonnegative (left candidate) (right candidate)).mp
          defectZero
    have termZero : finiteTotalVariation (left index) (right index) = 0 :=
      congrFun everyTermZero index
    exact (finiteTotalVariation_eq_zero_iff_mass_eq _ _).mp termZero
  · intro exactLaws
    apply (Fintype.sum_eq_zero_iff_of_nonneg fun index =>
      finiteTotalVariation_nonnegative (left index) (right index)).mpr
    funext index
    exact (finiteTotalVariation_eq_zero_iff_mass_eq _ _).mpr (exactLaws index)

/-- A point mass used by deterministic countermodels. -/
def finiteDirac
    {Outcome : Type uOutcome}
    [Fintype Outcome]
    [DecidableEq Outcome]
    (point : Outcome) : FiniteProbabilityMass Outcome where
  mass outcome := if outcome = point then 1 else 0
  nonnegative outcome := by split <;> norm_num
  normalized := by
    simpa using
      (Finset.sum_ite_eq' point (fun _ : Outcome => (1 : ℚ)))

/-- Push a normalized finite probability through a deterministic encoder. -/
def pushforwardFiniteProbability
    {Fine : Type uIndex}
    {Coarse : Type uOutcome}
    [Fintype Fine]
    [Fintype Coarse]
    [DecidableEq Coarse]
    (encode : Fine → Coarse)
    (probability : FiniteProbabilityMass Fine) :
    FiniteProbabilityMass Coarse where
  mass target :=
    ∑ source, if encode source = target then probability.mass source else 0
  nonnegative target := by
    exact Finset.sum_nonneg fun source _ => by
      split
      · exact probability.nonnegative source
      · exact le_rfl
  normalized := by
    classical
    rw [Finset.sum_comm]
    calc
      (∑ source,
        ∑ target,
          if encode source = target then probability.mass source else 0) =
          ∑ source, probability.mass source := by
        apply Finset.sum_congr rfl
        intro source _
        simpa [eq_comm] using
          (Finset.sum_ite_eq' (encode source)
            (fun _ : Coarse => probability.mass source))
      _ = 1 := probability.normalized

end OCMaturityCompletionCycle
