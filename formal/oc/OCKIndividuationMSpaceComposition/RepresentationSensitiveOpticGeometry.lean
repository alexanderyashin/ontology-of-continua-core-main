import Mathlib.Data.Real.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.Order.Chebyshev
import Mathlib.Algebra.BigOperators.Field
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.FieldSimp

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-!
# Representation-sensitive optic geometry

An optic can be information-equivalent to another optic while changing a
regularized learner.  The O5 factorial control duplicates every O2 coordinate;
ordinary ridge then penalizes two coefficient copies separately.  The exact
identity below shows that this halves the effective penalty on their aggregate
predictor.  Consequently an empirical modulus indexed only by information
content omits a real learner-by-representation interaction.
-/

/-- One-dimensional ridge objective for one represented feature. -/
def ScalarRidgeObjective (lambda target coefficient : ℝ) : ℝ :=
  (target - coefficient) ^ 2 + lambda * coefficient ^ 2

/-- The same predictor represented by two duplicate feature coordinates. -/
def DuplicatedScalarRidgeObjective
    (lambda target leftCoefficient rightCoefficient : ℝ) : ℝ :=
  (target - (leftCoefficient + rightCoefficient)) ^ 2 +
    lambda * (leftCoefficient ^ 2 + rightCoefficient ^ 2)

/-- Exact decomposition: two duplicate coordinates with penalty `lambda`
induce penalty `lambda / 2` on their aggregate predictor, plus a nonnegative
coefficient-imbalance term. -/
theorem duplicated_ridge_effective_penalty_decomposition
    (lambda target leftCoefficient rightCoefficient : ℝ) :
    DuplicatedScalarRidgeObjective lambda target leftCoefficient rightCoefficient =
      ScalarRidgeObjective (lambda / 2) target
        (leftCoefficient + rightCoefficient) +
      (lambda / 2) * (leftCoefficient - rightCoefficient) ^ 2 := by
  simp [DuplicatedScalarRidgeObjective, ScalarRidgeObjective]
  ring

/-- For nonnegative regularization, the duplicate objective is bounded below
by the single-representation objective with halved effective penalty. -/
theorem duplicated_ridge_lower_bounded_by_halved_penalty
    (lambda target leftCoefficient rightCoefficient : ℝ)
    (lambda_nonnegative : 0 ≤ lambda) :
    ScalarRidgeObjective (lambda / 2) target
        (leftCoefficient + rightCoefficient) ≤
      DuplicatedScalarRidgeObjective lambda target
        leftCoefficient rightCoefficient := by
  rw [duplicated_ridge_effective_penalty_decomposition]
  have imbalance_nonnegative :
      0 ≤ (lambda / 2) * (leftCoefficient - rightCoefficient) ^ 2 :=
    mul_nonneg (div_nonneg lambda_nonnegative (by norm_num)) (sq_nonneg _)
  linarith

/-- With positive regularization, the lower bound is attained exactly when the
two duplicate coefficients split the aggregate predictor equally. -/
theorem duplicated_ridge_equality_iff_balanced
    (lambda target leftCoefficient rightCoefficient : ℝ)
    (lambda_positive : 0 < lambda) :
    DuplicatedScalarRidgeObjective lambda target leftCoefficient rightCoefficient =
        ScalarRidgeObjective (lambda / 2) target
          (leftCoefficient + rightCoefficient) ↔
      leftCoefficient = rightCoefficient := by
  constructor
  · intro equality
    have decomposition :=
      duplicated_ridge_effective_penalty_decomposition
        lambda target leftCoefficient rightCoefficient
    have product_zero :
        (lambda / 2) * (leftCoefficient - rightCoefficient) ^ 2 = 0 := by
      linarith
    have half_positive : 0 < lambda / 2 := by linarith
    have square_zero : (leftCoefficient - rightCoefficient) ^ 2 = 0 :=
      (mul_eq_zero.mp product_zero).resolve_left (ne_of_gt half_positive)
    nlinarith
  · intro balanced
    subst rightCoefficient
    simp [duplicated_ridge_effective_penalty_decomposition]

/-- A balanced duplicate representation realizes the halved-penalty objective
for every aggregate predictor. -/
theorem balanced_duplicate_realizes_halved_penalty
    (lambda target aggregateCoefficient : ℝ) :
    DuplicatedScalarRidgeObjective lambda target
        (aggregateCoefficient / 2) (aggregateCoefficient / 2) =
      ScalarRidgeObjective (lambda / 2) target aggregateCoefficient := by
  simp [DuplicatedScalarRidgeObjective, ScalarRidgeObjective]
  ring

/-- Engineering correction: multiplying each duplicate-coordinate penalty by
the duplication count restores the original aggregate penalty. -/
theorem duplicate_penalty_rescaling_restores_single_objective
    (lambda target aggregateCoefficient : ℝ) :
    DuplicatedScalarRidgeObjective (2 * lambda) target
        (aggregateCoefficient / 2) (aggregateCoefficient / 2) =
      ScalarRidgeObjective lambda target aggregateCoefficient := by
  simp [DuplicatedScalarRidgeObjective, ScalarRidgeObjective]
  ring

/-- For target one and unit penalty, the unique single-coordinate ridge
prediction is `1/2`. -/
theorem unit_single_ridge_minimizer (coefficient : ℝ) :
    ScalarRidgeObjective 1 1 (1 / 2 : ℝ) ≤
      ScalarRidgeObjective 1 1 coefficient := by
  simp [ScalarRidgeObjective]
  nlinarith [sq_nonneg (coefficient - (1 / 2 : ℝ))]

/-- For the information-equivalent duplicated representation, unit penalty
has balanced minimizer `(1/3, 1/3)` and aggregate prediction `2/3`. -/
theorem unit_duplicated_ridge_minimizer
    (leftCoefficient rightCoefficient : ℝ) :
    DuplicatedScalarRidgeObjective 1 1 (1 / 3 : ℝ) (1 / 3 : ℝ) ≤
      DuplicatedScalarRidgeObjective 1 1 leftCoefficient rightCoefficient := by
  simp [DuplicatedScalarRidgeObjective]
  nlinarith [
    sq_nonneg (leftCoefficient - (1 / 3 : ℝ)),
    sq_nonneg (rightCoefficient - (1 / 3 : ℝ)),
    sq_nonneg
      ((leftCoefficient - (1 / 3 : ℝ)) +
        (rightCoefficient - (1 / 3 : ℝ)))]

/-- **No-go theorem.** Information-equivalent feature duplication does not
imply ridge-prediction invariance: the same unit signal and target produce
predictions `1/2` and `2/3` under the ordinary per-coordinate penalty. -/
theorem information_equivalence_does_not_imply_ridge_prediction_invariance :
    (∀ coefficient : ℝ,
      ScalarRidgeObjective 1 1 (1 / 2 : ℝ) ≤
        ScalarRidgeObjective 1 1 coefficient) ∧
    (∀ leftCoefficient rightCoefficient : ℝ,
      DuplicatedScalarRidgeObjective 1 1 (1 / 3 : ℝ) (1 / 3 : ℝ) ≤
        DuplicatedScalarRidgeObjective 1 1
          leftCoefficient rightCoefficient) ∧
    (1 / 2 : ℝ) ≠ (1 / 3 : ℝ) + (1 / 3 : ℝ) := by
  constructor
  · exact unit_single_ridge_minimizer
  · constructor
    · exact unit_duplicated_ridge_minimizer
    · norm_num

/-! ## Arbitrary finite feature blocks and arbitrary residual loss -/

/-- Ridge objective for an arbitrary residual functional on a finite
coefficient vector.  The residual can encode any design matrix, response
vector, intercept treatment, and squared-error aggregation. -/
def FiniteVectorRidgeObjective
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (coefficient : Fin dimension → ℝ) : ℝ :=
  residual coefficient + lambda * ∑ coordinate, coefficient coordinate ^ 2

/-- Duplicate-feature objective.  Its residual depends only on the aggregate
coefficient, while ordinary ridge penalizes both represented blocks. -/
def DuplicatedFiniteVectorRidgeObjective
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (leftCoefficient rightCoefficient : Fin dimension → ℝ) : ℝ :=
  residual (fun coordinate =>
      leftCoefficient coordinate + rightCoefficient coordinate) +
    lambda * ∑ coordinate,
      (leftCoefficient coordinate ^ 2 + rightCoefficient coordinate ^ 2)

/-- Coordinatewise parallelogram identity summed over the represented feature
block. -/
theorem duplicate_vector_penalty_parallelogram
    {dimension : ℕ}
    (leftCoefficient rightCoefficient : Fin dimension → ℝ) :
    2 * (∑ coordinate,
      (leftCoefficient coordinate ^ 2 + rightCoefficient coordinate ^ 2)) =
      (∑ coordinate,
        (leftCoefficient coordinate + rightCoefficient coordinate) ^ 2) +
      ∑ coordinate,
        (leftCoefficient coordinate - rightCoefficient coordinate) ^ 2 := by
  calc
    2 * (∑ coordinate,
        (leftCoefficient coordinate ^ 2 + rightCoefficient coordinate ^ 2)) =
        (∑ coordinate,
          (leftCoefficient coordinate ^ 2 + rightCoefficient coordinate ^ 2)) +
        ∑ coordinate,
          (leftCoefficient coordinate ^ 2 + rightCoefficient coordinate ^ 2) := by
            ring
    _ = ∑ coordinate,
          ((leftCoefficient coordinate ^ 2 + rightCoefficient coordinate ^ 2) +
            (leftCoefficient coordinate ^ 2 + rightCoefficient coordinate ^ 2)) := by
            exact Finset.sum_add_distrib.symm
    _ = ∑ coordinate,
          ((leftCoefficient coordinate + rightCoefficient coordinate) ^ 2 +
            (leftCoefficient coordinate - rightCoefficient coordinate) ^ 2) := by
            apply Finset.sum_congr rfl
            intro coordinate _
            ring
    _ = (∑ coordinate,
          (leftCoefficient coordinate + rightCoefficient coordinate) ^ 2) +
        ∑ coordinate,
          (leftCoefficient coordinate - rightCoefficient coordinate) ^ 2 := by
            rw [Finset.sum_add_distrib]

/-- General finite-dimensional decomposition.  It is independent of the
design matrix because every residual depending only on the aggregate
coefficient cancels exactly. -/
theorem duplicated_vector_ridge_effective_penalty_decomposition
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (leftCoefficient rightCoefficient : Fin dimension → ℝ) :
    DuplicatedFiniteVectorRidgeObjective residual lambda
        leftCoefficient rightCoefficient =
      FiniteVectorRidgeObjective residual (lambda / 2)
        (fun coordinate =>
          leftCoefficient coordinate + rightCoefficient coordinate) +
      (lambda / 2) * ∑ coordinate,
        (leftCoefficient coordinate - rightCoefficient coordinate) ^ 2 := by
  have parallelogram :=
    duplicate_vector_penalty_parallelogram leftCoefficient rightCoefficient
  have penalty_decomposition :
      (∑ coordinate,
        (leftCoefficient coordinate ^ 2 + rightCoefficient coordinate ^ 2)) =
        (1 / 2 : ℝ) * (∑ coordinate,
          (leftCoefficient coordinate + rightCoefficient coordinate) ^ 2) +
        (1 / 2 : ℝ) * ∑ coordinate,
          (leftCoefficient coordinate - rightCoefficient coordinate) ^ 2 := by
    nlinarith
  simp only [DuplicatedFiniteVectorRidgeObjective, FiniteVectorRidgeObjective]
  rw [penalty_decomposition]
  ring

/-- Nonnegative regularization leaves only a nonnegative imbalance remainder
above the halved-penalty aggregate objective. -/
theorem duplicated_vector_ridge_lower_bound
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (leftCoefficient rightCoefficient : Fin dimension → ℝ)
    (lambda_nonnegative : 0 ≤ lambda) :
    FiniteVectorRidgeObjective residual (lambda / 2)
        (fun coordinate =>
          leftCoefficient coordinate + rightCoefficient coordinate) ≤
      DuplicatedFiniteVectorRidgeObjective residual lambda
        leftCoefficient rightCoefficient := by
  rw [duplicated_vector_ridge_effective_penalty_decomposition]
  have square_sum_nonnegative :
      0 ≤ ∑ coordinate,
        (leftCoefficient coordinate - rightCoefficient coordinate) ^ 2 := by
    exact Finset.sum_nonneg (fun coordinate _ => sq_nonneg _)
  have remainder_nonnegative :
      0 ≤ (lambda / 2) * ∑ coordinate,
        (leftCoefficient coordinate - rightCoefficient coordinate) ^ 2 :=
    mul_nonneg (div_nonneg lambda_nonnegative (by norm_num))
      square_sum_nonnegative
  linarith

/-- Equal coefficient splitting realizes exactly the aggregate objective with
halved penalty. -/
theorem balanced_vector_duplicate_realizes_halved_penalty
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (aggregateCoefficient : Fin dimension → ℝ) :
    DuplicatedFiniteVectorRidgeObjective residual lambda
        (fun coordinate => aggregateCoefficient coordinate / 2)
        (fun coordinate => aggregateCoefficient coordinate / 2) =
      FiniteVectorRidgeObjective residual (lambda / 2)
        aggregateCoefficient := by
  rw [duplicated_vector_ridge_effective_penalty_decomposition]
  have aggregate_identity :
      (fun coordinate =>
        aggregateCoefficient coordinate / 2 +
          aggregateCoefficient coordinate / 2) = aggregateCoefficient := by
    funext coordinate
    ring
  rw [aggregate_identity]
  simp

/-- Any minimizer at penalty `lambda/2` lifts to a balanced minimizer of the
ordinary duplicate representation at penalty `lambda`. -/
theorem halved_penalty_minimizer_lifts_to_duplicate_representation
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (aggregateMinimizer : Fin dimension → ℝ)
    (lambda_nonnegative : 0 ≤ lambda)
    (aggregate_minimal : ∀ candidate,
      FiniteVectorRidgeObjective residual (lambda / 2) aggregateMinimizer ≤
        FiniteVectorRidgeObjective residual (lambda / 2) candidate) :
    ∀ leftCoefficient rightCoefficient,
      DuplicatedFiniteVectorRidgeObjective residual lambda
          (fun coordinate => aggregateMinimizer coordinate / 2)
          (fun coordinate => aggregateMinimizer coordinate / 2) ≤
        DuplicatedFiniteVectorRidgeObjective residual lambda
          leftCoefficient rightCoefficient := by
  intro leftCoefficient rightCoefficient
  rw [balanced_vector_duplicate_realizes_halved_penalty]
  exact le_trans
    (aggregate_minimal (fun coordinate =>
      leftCoefficient coordinate + rightCoefficient coordinate))
    (duplicated_vector_ridge_lower_bound residual lambda
      leftCoefficient rightCoefficient lambda_nonnegative)

/-- Scaling each duplicate-coordinate penalty by the duplication count restores
the original aggregate ridge objective exactly. -/
theorem duplicate_vector_penalty_rescaling_restores_single_objective
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (aggregateCoefficient : Fin dimension → ℝ) :
    DuplicatedFiniteVectorRidgeObjective residual (2 * lambda)
        (fun coordinate => aggregateCoefficient coordinate / 2)
        (fun coordinate => aggregateCoefficient coordinate / 2) =
      FiniteVectorRidgeObjective residual lambda aggregateCoefficient := by
  rw [balanced_vector_duplicate_realizes_halved_penalty]
  congr 1
  ring

/-- Therefore every original ridge minimizer lifts to the rescaled duplicate
representation without changing its aggregate predictor. -/
theorem original_minimizer_lifts_to_rescaled_duplicate_representation
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (aggregateMinimizer : Fin dimension → ℝ)
    (lambda_nonnegative : 0 ≤ lambda)
    (aggregate_minimal : ∀ candidate,
      FiniteVectorRidgeObjective residual lambda aggregateMinimizer ≤
        FiniteVectorRidgeObjective residual lambda candidate) :
    ∀ leftCoefficient rightCoefficient,
      DuplicatedFiniteVectorRidgeObjective residual (2 * lambda)
          (fun coordinate => aggregateMinimizer coordinate / 2)
          (fun coordinate => aggregateMinimizer coordinate / 2) ≤
        DuplicatedFiniteVectorRidgeObjective residual (2 * lambda)
          leftCoefficient rightCoefficient := by
  intro leftCoefficient rightCoefficient
  rw [duplicate_vector_penalty_rescaling_restores_single_objective]
  have doubled_nonnegative : 0 ≤ 2 * lambda := mul_nonneg (by norm_num) lambda_nonnegative
  have lower := duplicated_vector_ridge_lower_bound residual (2 * lambda)
    leftCoefficient rightCoefficient doubled_nonnegative
  have penalty_identity : (2 * lambda) / 2 = lambda := by ring
  rw [penalty_identity] at lower
  exact le_trans
    (aggregate_minimal (fun coordinate =>
      leftCoefficient coordinate + rightCoefficient coordinate))
    lower

/-! ## Arbitrary replication multiplicity -/

/-- Ridge objective for a feature block represented by `copyCount` perfectly
redundant coordinate blocks.  Only the sum of the represented coefficients
enters the residual, while the ordinary ridge penalty is charged per copy. -/
def ReplicatedFiniteVectorRidgeObjective
    {copyCount dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (coefficient : Fin copyCount → Fin dimension → ℝ) : ℝ :=
  residual (fun coordinate =>
      ∑ copy, coefficient copy coordinate) +
    lambda * ∑ copy, ∑ coordinate, coefficient copy coordinate ^ 2

/-- A block represented `copyCount + 1` times realizes the original residual
with effective aggregate penalty `lambda / (copyCount + 1)` when its
coefficient is split evenly.  This is an exact law for arbitrary dimension and
arbitrary residual loss. -/
theorem balanced_replication_realizes_divided_penalty
    (copyCount : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (aggregateCoefficient : Fin dimension → ℝ) :
    ReplicatedFiniteVectorRidgeObjective (copyCount := copyCount + 1)
        residual lambda
        (fun _ coordinate =>
          aggregateCoefficient coordinate / (copyCount + 1 : ℕ)) =
      FiniteVectorRidgeObjective residual
        (lambda / (copyCount + 1 : ℕ)) aggregateCoefficient := by
  have count_positive : (0 : ℝ) < (copyCount + 1 : ℕ) := by
    exact_mod_cast Nat.succ_pos copyCount
  have aggregate_identity :
      (fun coordinate =>
        ∑ _copy : Fin (copyCount + 1),
          aggregateCoefficient coordinate / (copyCount + 1 : ℕ)) =
        aggregateCoefficient := by
    funext coordinate
    simp
    field_simp
  simp only [ReplicatedFiniteVectorRidgeObjective, FiniteVectorRidgeObjective]
  rw [aggregate_identity]
  have count_nonzero : ((copyCount + 1 : ℕ) : ℝ) ≠ 0 :=
    ne_of_gt count_positive
  have square_division (coordinate : Fin dimension) :
      (aggregateCoefficient coordinate / (copyCount + 1 : ℕ)) ^ 2 =
        aggregateCoefficient coordinate ^ 2 /
          (((copyCount + 1 : ℕ) : ℝ) ^ 2) := by
    ring
  congr 1
  simp only [Finset.sum_const, Finset.card_univ, Fintype.card_fin,
    nsmul_eq_mul]
  simp_rw [square_division]
  rw [← Finset.sum_div]
  have normalized_count_nonzero : ((1 + copyCount : ℕ) : ℝ) ≠ 0 := by
    positivity
  field_simp [count_nonzero, normalized_count_nonzero]

/-- Cauchy-Schwarz lower bound: for nonnegative regularization, no allocation
across `copyCount + 1` redundant blocks can beat the aggregate objective with
penalty divided by the representation multiplicity. -/
theorem replicated_vector_ridge_lower_bound
    (copyCount : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (coefficient : Fin (copyCount + 1) → Fin dimension → ℝ)
    (lambda_nonnegative : 0 ≤ lambda) :
    FiniteVectorRidgeObjective residual
        (lambda / (copyCount + 1 : ℕ))
        (fun coordinate => ∑ copy, coefficient copy coordinate) ≤
      ReplicatedFiniteVectorRidgeObjective (copyCount := copyCount + 1)
        residual lambda coefficient := by
  have count_positive : (0 : ℝ) < (copyCount + 1 : ℕ) := by
    exact_mod_cast Nat.succ_pos copyCount
  have coordinate_bound (coordinate : Fin dimension) :
      (∑ copy, coefficient copy coordinate) ^ 2 /
          (copyCount + 1 : ℕ) ≤
        ∑ copy, coefficient copy coordinate ^ 2 := by
    rw [div_le_iff₀ count_positive]
    have cauchy := sq_sum_le_card_mul_sum_sq
      (s := (Finset.univ : Finset (Fin (copyCount + 1))))
      (f := fun copy => coefficient copy coordinate)
    simpa [mul_comm] using cauchy
  have summed_bound :
      (∑ coordinate,
          (∑ copy, coefficient copy coordinate) ^ 2) /
          (copyCount + 1 : ℕ) ≤
        ∑ copy, ∑ coordinate, coefficient copy coordinate ^ 2 := by
    rw [Finset.sum_div]
    calc
      (∑ coordinate,
          (∑ copy, coefficient copy coordinate) ^ 2 /
            (copyCount + 1 : ℕ)) ≤
          ∑ coordinate, ∑ copy, coefficient copy coordinate ^ 2 := by
            exact Finset.sum_le_sum (fun coordinate _ =>
              coordinate_bound coordinate)
      _ = ∑ copy, ∑ coordinate, coefficient copy coordinate ^ 2 := by
            rw [Finset.sum_comm]
  have penalized_bound :
      (lambda / (copyCount + 1 : ℕ)) *
          ∑ coordinate,
            (∑ copy, coefficient copy coordinate) ^ 2 ≤
        lambda * ∑ copy, ∑ coordinate,
          coefficient copy coordinate ^ 2 := by
    have multiplied := mul_le_mul_of_nonneg_left summed_bound lambda_nonnegative
    calc
      (lambda / (copyCount + 1 : ℕ)) *
          ∑ coordinate,
            (∑ copy, coefficient copy coordinate) ^ 2 =
          lambda * ((∑ coordinate,
            (∑ copy, coefficient copy coordinate) ^ 2) /
              (copyCount + 1 : ℕ)) := by ring
      _ ≤ lambda * ∑ copy, ∑ coordinate,
          coefficient copy coordinate ^ 2 := multiplied
  simp only [FiniteVectorRidgeObjective,
    ReplicatedFiniteVectorRidgeObjective]
  linarith

/-- Every minimizer at penalty `lambda / n` therefore lifts to an evenly split
global minimizer of the `n`-copy ordinary ridge representation. -/
theorem divided_penalty_minimizer_lifts_to_replication
    (copyCount : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (aggregateMinimizer : Fin dimension → ℝ)
    (lambda_nonnegative : 0 ≤ lambda)
    (aggregate_minimal : ∀ candidate,
      FiniteVectorRidgeObjective residual
          (lambda / (copyCount + 1 : ℕ)) aggregateMinimizer ≤
        FiniteVectorRidgeObjective residual
          (lambda / (copyCount + 1 : ℕ)) candidate) :
    ∀ coefficient : Fin (copyCount + 1) → Fin dimension → ℝ,
      ReplicatedFiniteVectorRidgeObjective (copyCount := copyCount + 1)
          residual lambda
          (fun _ coordinate =>
            aggregateMinimizer coordinate / (copyCount + 1 : ℕ)) ≤
        ReplicatedFiniteVectorRidgeObjective (copyCount := copyCount + 1)
          residual lambda coefficient := by
  intro coefficient
  rw [balanced_replication_realizes_divided_penalty]
  exact le_trans
    (aggregate_minimal (fun coordinate => ∑ copy, coefficient copy coordinate))
    (replicated_vector_ridge_lower_bound copyCount residual lambda coefficient
      lambda_nonnegative)

/-- Representation-normalized regularization restores the original objective:
charging `(copyCount + 1) * lambda` per replicated coordinate exactly cancels
the `1 / (copyCount + 1)` effective-penalty shift. -/
theorem replication_penalty_rescaling_restores_single_objective
    (copyCount : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (aggregateCoefficient : Fin dimension → ℝ) :
    ReplicatedFiniteVectorRidgeObjective (copyCount := copyCount + 1) residual
        ((copyCount + 1 : ℕ) * lambda)
        (fun _ coordinate =>
          aggregateCoefficient coordinate / (copyCount + 1 : ℕ)) =
      FiniteVectorRidgeObjective residual lambda aggregateCoefficient := by
  rw [balanced_replication_realizes_divided_penalty]
  have count_nonzero : (copyCount + 1 : ℝ) ≠ 0 := by positivity
  congr 1
  field_simp

/-- Hence an original ridge minimizer lifts to every normalized replicated
representation, giving a constructive representation-invariance adapter. -/
theorem original_minimizer_lifts_to_normalized_replication
    (copyCount : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (aggregateMinimizer : Fin dimension → ℝ)
    (lambda_nonnegative : 0 ≤ lambda)
    (aggregate_minimal : ∀ candidate,
      FiniteVectorRidgeObjective residual lambda aggregateMinimizer ≤
        FiniteVectorRidgeObjective residual lambda candidate) :
    ∀ coefficient : Fin (copyCount + 1) → Fin dimension → ℝ,
      ReplicatedFiniteVectorRidgeObjective (copyCount := copyCount + 1) residual
          ((copyCount + 1 : ℕ) * lambda)
          (fun _ coordinate =>
            aggregateMinimizer coordinate / (copyCount + 1 : ℕ)) ≤
        ReplicatedFiniteVectorRidgeObjective (copyCount := copyCount + 1)
          residual
          ((copyCount + 1 : ℕ) * lambda) coefficient := by
  intro coefficient
  rw [replication_penalty_rescaling_restores_single_objective]
  have scaled_nonnegative :
      0 ≤ ((copyCount + 1 : ℕ) : ℝ) * lambda :=
    mul_nonneg (by positivity) lambda_nonnegative
  have lower := replicated_vector_ridge_lower_bound copyCount residual
    (((copyCount + 1 : ℕ) : ℝ) * lambda) coefficient scaled_nonnegative
  have penalty_identity :
      (((copyCount + 1 : ℕ) : ℝ) * lambda) /
          (copyCount + 1 : ℕ) = lambda := by
    field_simp
  rw [penalty_identity] at lower
  exact le_trans
    (aggregate_minimal (fun coordinate => ∑ copy, coefficient copy coordinate))
    lower

/-! ## Exact learner-equivalence boundary between representations -/

/-- Exact objective displacement between two balanced representations.  The
residual cancels, so the entire representation effect is the difference of
the two penalties normalized by their copy counts. -/
theorem balanced_replication_objective_difference
    (leftExtraCopies rightExtraCopies : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (leftPenalty rightPenalty : ℝ)
    (aggregateCoefficient : Fin dimension → ℝ) :
    ReplicatedFiniteVectorRidgeObjective
          (copyCount := leftExtraCopies + 1) residual leftPenalty
          (fun _ coordinate => aggregateCoefficient coordinate /
            (leftExtraCopies + 1 : ℕ)) -
        ReplicatedFiniteVectorRidgeObjective
          (copyCount := rightExtraCopies + 1) residual rightPenalty
          (fun _ coordinate => aggregateCoefficient coordinate /
            (rightExtraCopies + 1 : ℕ)) =
      (leftPenalty / (leftExtraCopies + 1 : ℕ) -
        rightPenalty / (rightExtraCopies + 1 : ℕ)) *
        ∑ coordinate, aggregateCoefficient coordinate ^ 2 := by
  rw [balanced_replication_realizes_divided_penalty,
    balanced_replication_realizes_divided_penalty]
  simp only [FiniteVectorRidgeObjective]
  ring

/-- **Necessary and sufficient boundary.**  On any nonzero aggregate feature
block, two balanced replicated representations have exactly the same ridge
objective iff their per-coordinate penalties divided by representation
multiplicity agree. -/
theorem balanced_replications_equal_iff_normalized_penalties_equal
    (leftExtraCopies rightExtraCopies : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (leftPenalty rightPenalty : ℝ)
    (aggregateCoefficient : Fin dimension → ℝ)
    (aggregate_nonzero :
      (∑ coordinate, aggregateCoefficient coordinate ^ 2) ≠ 0) :
    ReplicatedFiniteVectorRidgeObjective
          (copyCount := leftExtraCopies + 1) residual leftPenalty
          (fun _ coordinate => aggregateCoefficient coordinate /
            (leftExtraCopies + 1 : ℕ)) =
        ReplicatedFiniteVectorRidgeObjective
          (copyCount := rightExtraCopies + 1) residual rightPenalty
          (fun _ coordinate => aggregateCoefficient coordinate /
            (rightExtraCopies + 1 : ℕ)) ↔
      leftPenalty / (leftExtraCopies + 1 : ℕ) =
        rightPenalty / (rightExtraCopies + 1 : ℕ) := by
  have difference := balanced_replication_objective_difference
    leftExtraCopies rightExtraCopies residual leftPenalty rightPenalty
      aggregateCoefficient
  constructor
  · intro objective_equal
    have product_zero :
        (leftPenalty / (leftExtraCopies + 1 : ℕ) -
          rightPenalty / (rightExtraCopies + 1 : ℕ)) *
          ∑ coordinate, aggregateCoefficient coordinate ^ 2 = 0 := by
      linarith
    have normalized_difference_zero :
        leftPenalty / (leftExtraCopies + 1 : ℕ) -
          rightPenalty / (rightExtraCopies + 1 : ℕ) = 0 :=
      (mul_eq_zero.mp product_zero).resolve_right aggregate_nonzero
    linarith
  · intro normalized_equal
    rw [balanced_replication_realizes_divided_penalty,
      balanced_replication_realizes_divided_penalty, normalized_equal]

/-- Specializing one side to the one-block representation gives the exact
engineering admission rule: a nonzero `n`-copy representation preserves the
original objective iff its coordinate penalty is normalized so that
`replicatedPenalty / n = originalPenalty`. -/
theorem replication_preserves_original_iff_normalized_penalty
    (extraCopies : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (replicatedPenalty originalPenalty : ℝ)
    (aggregateCoefficient : Fin dimension → ℝ)
    (aggregate_nonzero :
      (∑ coordinate, aggregateCoefficient coordinate ^ 2) ≠ 0) :
    ReplicatedFiniteVectorRidgeObjective
          (copyCount := extraCopies + 1) residual replicatedPenalty
          (fun _ coordinate => aggregateCoefficient coordinate /
            (extraCopies + 1 : ℕ)) =
        FiniteVectorRidgeObjective residual originalPenalty
          aggregateCoefficient ↔
      replicatedPenalty / (extraCopies + 1 : ℕ) = originalPenalty := by
  have one_copy_identity :
      ReplicatedFiniteVectorRidgeObjective (copyCount := 1)
          residual originalPenalty
          (fun _ coordinate => aggregateCoefficient coordinate) =
        FiniteVectorRidgeObjective residual originalPenalty
          aggregateCoefficient := by
    simpa using balanced_replication_realizes_divided_penalty
      0 residual originalPenalty aggregateCoefficient
  rw [← one_copy_identity]
  simpa using balanced_replications_equal_iff_normalized_penalties_equal
    extraCopies 0 residual replicatedPenalty originalPenalty
      aggregateCoefficient aggregate_nonzero

/-! ## Regularizer geometry: L1 is representation-invariant for exact copies -/

/-- L1-regularized objective for an arbitrary residual functional. -/
def FiniteVectorLassoObjective
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (coefficient : Fin dimension → ℝ) : ℝ :=
  residual coefficient + lambda * ∑ coordinate, |coefficient coordinate|

/-- L1 objective for a block represented by multiple exact copies. -/
def ReplicatedFiniteVectorLassoObjective
    {copyCount dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (coefficient : Fin copyCount → Fin dimension → ℝ) : ℝ :=
  residual (fun coordinate => ∑ copy, coefficient copy coordinate) +
    lambda * ∑ copy, ∑ coordinate, |coefficient copy coordinate|

/-- The triangle inequality makes the original aggregate L1 objective a lower
bound for every exact-copy allocation.  Unlike L2, no `1/n` factor appears. -/
theorem replicated_vector_lasso_lower_bound
    (copyCount : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (coefficient : Fin (copyCount + 1) → Fin dimension → ℝ)
    (lambda_nonnegative : 0 ≤ lambda) :
    FiniteVectorLassoObjective residual lambda
        (fun coordinate => ∑ copy, coefficient copy coordinate) ≤
      ReplicatedFiniteVectorLassoObjective
        (copyCount := copyCount + 1) residual lambda coefficient := by
  have coordinate_triangle (coordinate : Fin dimension) :
      |∑ copy, coefficient copy coordinate| ≤
        ∑ copy, |coefficient copy coordinate| := by
    simpa using Finset.abs_sum_le_sum_abs
      (fun copy : Fin (copyCount + 1) => coefficient copy coordinate)
      (Finset.univ : Finset (Fin (copyCount + 1)))
  have penalty_bound :
      ∑ coordinate, |∑ copy, coefficient copy coordinate| ≤
        ∑ copy, ∑ coordinate, |coefficient copy coordinate| := by
    calc
      (∑ coordinate, |∑ copy, coefficient copy coordinate|) ≤
          ∑ coordinate, ∑ copy, |coefficient copy coordinate| := by
            exact Finset.sum_le_sum (fun coordinate _ =>
              coordinate_triangle coordinate)
      _ = ∑ copy, ∑ coordinate, |coefficient copy coordinate| := by
            rw [Finset.sum_comm]
  have penalized_bound :=
    mul_le_mul_of_nonneg_left penalty_bound lambda_nonnegative
  simp only [FiniteVectorLassoObjective,
    ReplicatedFiniteVectorLassoObjective]
  linarith

/-- Placing the whole aggregate coefficient in the first copy and zero in all
remaining copies realizes the original L1 objective exactly. -/
theorem first_copy_lasso_realizes_single_objective
    (copyCount : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (aggregateCoefficient : Fin dimension → ℝ) :
    ReplicatedFiniteVectorLassoObjective
        (copyCount := copyCount + 1) residual lambda
        (fun copy => Fin.cases aggregateCoefficient
          (fun _ _ => 0) copy) =
      FiniteVectorLassoObjective residual lambda aggregateCoefficient := by
  simp [ReplicatedFiniteVectorLassoObjective, FiniteVectorLassoObjective,
    Fin.sum_univ_succ]

/-- Equal splitting also realizes the same aggregate L1 objective: positive
replication changes coefficient non-uniqueness but not the induced L1 penalty. -/
theorem balanced_replication_lasso_realizes_single_objective
    (copyCount : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (aggregateCoefficient : Fin dimension → ℝ) :
    ReplicatedFiniteVectorLassoObjective
        (copyCount := copyCount + 1) residual lambda
        (fun _ coordinate =>
          aggregateCoefficient coordinate / (copyCount + 1 : ℕ)) =
      FiniteVectorLassoObjective residual lambda aggregateCoefficient := by
  have count_positive : (0 : ℝ) < (copyCount + 1 : ℕ) := by
    exact_mod_cast Nat.succ_pos copyCount
  have count_nonzero : ((copyCount + 1 : ℕ) : ℝ) ≠ 0 :=
    ne_of_gt count_positive
  have aggregate_identity :
      (fun coordinate =>
        ∑ _copy : Fin (copyCount + 1),
          aggregateCoefficient coordinate / (copyCount + 1 : ℕ)) =
        aggregateCoefficient := by
    funext coordinate
    simp
    field_simp
  have absolute_division (coordinate : Fin dimension) :
      |aggregateCoefficient coordinate / (copyCount + 1 : ℕ)| =
        |aggregateCoefficient coordinate| / (copyCount + 1 : ℕ) := by
    rw [abs_div, abs_of_pos count_positive]
  simp only [ReplicatedFiniteVectorLassoObjective,
    FiniteVectorLassoObjective]
  rw [aggregate_identity]
  congr 1
  simp only [Finset.sum_const, Finset.card_univ, Fintype.card_fin,
    nsmul_eq_mul]
  simp_rw [absolute_division]
  rw [← Finset.sum_div]
  field_simp [count_nonzero]

/-- Every original L1 minimizer lifts to a global minimizer under any positive
exact-copy multiplicity without penalty rescaling.  Thus exact feature
duplication is learner-equivalent for the aggregate L1 predictor even though
it is not learner-equivalent for ordinary L2 ridge. -/
theorem original_lasso_minimizer_lifts_without_replication_rescaling
    (copyCount : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (lambda : ℝ)
    (aggregateMinimizer : Fin dimension → ℝ)
    (lambda_nonnegative : 0 ≤ lambda)
    (aggregate_minimal : ∀ candidate,
      FiniteVectorLassoObjective residual lambda aggregateMinimizer ≤
        FiniteVectorLassoObjective residual lambda candidate) :
    ∀ coefficient : Fin (copyCount + 1) → Fin dimension → ℝ,
      ReplicatedFiniteVectorLassoObjective
          (copyCount := copyCount + 1) residual lambda
          (fun copy => Fin.cases aggregateMinimizer
            (fun _ _ => 0) copy) ≤
        ReplicatedFiniteVectorLassoObjective
          (copyCount := copyCount + 1) residual lambda coefficient := by
  intro coefficient
  rw [first_copy_lasso_realizes_single_objective]
  exact le_trans
    (aggregate_minimal (fun coordinate => ∑ copy, coefficient copy coordinate))
    (replicated_vector_lasso_lower_bound copyCount residual lambda coefficient
      lambda_nonnegative)

/-! ## Elastic-net composition -/

/-- Elastic-net objective with independently visible L1 and L2 weights. -/
def FiniteVectorElasticNetObjective
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (l1Weight l2Weight : ℝ)
    (coefficient : Fin dimension → ℝ) : ℝ :=
  residual coefficient +
    l1Weight * ∑ coordinate, |coefficient coordinate| +
    l2Weight * ∑ coordinate, coefficient coordinate ^ 2

/-- Elastic-net objective on multiple exact copies. -/
def ReplicatedFiniteVectorElasticNetObjective
    {copyCount dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (l1Weight l2Weight : ℝ)
    (coefficient : Fin copyCount → Fin dimension → ℝ) : ℝ :=
  residual (fun coordinate => ∑ copy, coefficient copy coordinate) +
    l1Weight * ∑ copy, ∑ coordinate, |coefficient copy coordinate| +
    l2Weight * ∑ copy, ∑ coordinate, coefficient copy coordinate ^ 2

/-- Exact mixed-geometry law: replication leaves the L1 weight unchanged but
divides the effective L2 weight by the copy count. -/
theorem balanced_replication_elastic_net_effective_weights
    (copyCount : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (l1Weight l2Weight : ℝ)
    (aggregateCoefficient : Fin dimension → ℝ) :
    ReplicatedFiniteVectorElasticNetObjective
        (copyCount := copyCount + 1) residual l1Weight l2Weight
        (fun _ coordinate =>
          aggregateCoefficient coordinate / (copyCount + 1 : ℕ)) =
      FiniteVectorElasticNetObjective residual l1Weight
        (l2Weight / (copyCount + 1 : ℕ)) aggregateCoefficient := by
  have aggregate_identity :
      (fun coordinate =>
        ∑ _copy : Fin (copyCount + 1),
          aggregateCoefficient coordinate / (copyCount + 1 : ℕ)) =
        aggregateCoefficient := by
    funext coordinate
    simp
    field_simp
  have lasso_identity :=
    balanced_replication_lasso_realizes_single_objective copyCount residual
      l1Weight aggregateCoefficient
  have ridge_identity :=
    balanced_replication_realizes_divided_penalty copyCount residual
      l2Weight aggregateCoefficient
  simp only [ReplicatedFiniteVectorLassoObjective,
    FiniteVectorLassoObjective] at lasso_identity
  simp only [ReplicatedFiniteVectorRidgeObjective,
    FiniteVectorRidgeObjective] at ridge_identity
  simp only [ReplicatedFiniteVectorElasticNetObjective,
    FiniteVectorElasticNetObjective]
  rw [aggregate_identity] at lasso_identity ridge_identity ⊢
  linarith

/-- Nonnegative mixed weights give the corresponding global lower bound for
every allocation across the replicated blocks. -/
theorem replicated_vector_elastic_net_lower_bound
    (copyCount : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (l1Weight l2Weight : ℝ)
    (coefficient : Fin (copyCount + 1) → Fin dimension → ℝ)
    (l1_nonnegative : 0 ≤ l1Weight)
    (l2_nonnegative : 0 ≤ l2Weight) :
    FiniteVectorElasticNetObjective residual l1Weight
        (l2Weight / (copyCount + 1 : ℕ))
        (fun coordinate => ∑ copy, coefficient copy coordinate) ≤
      ReplicatedFiniteVectorElasticNetObjective
        (copyCount := copyCount + 1) residual l1Weight l2Weight
        coefficient := by
  have lasso_bound := replicated_vector_lasso_lower_bound copyCount residual
    l1Weight coefficient l1_nonnegative
  have ridge_bound := replicated_vector_ridge_lower_bound copyCount residual
    l2Weight coefficient l2_nonnegative
  simp only [FiniteVectorLassoObjective,
    ReplicatedFiniteVectorLassoObjective] at lasso_bound
  simp only [FiniteVectorRidgeObjective,
    ReplicatedFiniteVectorRidgeObjective] at ridge_bound
  simp only [FiniteVectorElasticNetObjective,
    ReplicatedFiniteVectorElasticNetObjective]
  linarith

/-- Any minimizer with the induced weights `(lambda1, lambda2/n)` lifts to a
balanced global minimizer of the replicated elastic-net representation. -/
theorem effective_elastic_net_minimizer_lifts_to_replication
    (copyCount : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (l1Weight l2Weight : ℝ)
    (aggregateMinimizer : Fin dimension → ℝ)
    (l1_nonnegative : 0 ≤ l1Weight)
    (l2_nonnegative : 0 ≤ l2Weight)
    (aggregate_minimal : ∀ candidate,
      FiniteVectorElasticNetObjective residual l1Weight
          (l2Weight / (copyCount + 1 : ℕ)) aggregateMinimizer ≤
        FiniteVectorElasticNetObjective residual l1Weight
          (l2Weight / (copyCount + 1 : ℕ)) candidate) :
    ∀ coefficient : Fin (copyCount + 1) → Fin dimension → ℝ,
      ReplicatedFiniteVectorElasticNetObjective
          (copyCount := copyCount + 1) residual l1Weight l2Weight
          (fun _ coordinate =>
            aggregateMinimizer coordinate / (copyCount + 1 : ℕ)) ≤
        ReplicatedFiniteVectorElasticNetObjective
          (copyCount := copyCount + 1) residual l1Weight l2Weight
          coefficient := by
  intro coefficient
  rw [balanced_replication_elastic_net_effective_weights]
  exact le_trans
    (aggregate_minimal (fun coordinate => ∑ copy, coefficient copy coordinate))
    (replicated_vector_elastic_net_lower_bound copyCount residual
      l1Weight l2Weight coefficient l1_nonnegative l2_nonnegative)

/-- Constructive elastic-net repair: preserve the L1 weight and multiply only
the replicated L2 weight by the copy count. -/
theorem replication_elastic_net_l2_rescaling_restores_original
    (copyCount : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (l1Weight l2Weight : ℝ)
    (aggregateCoefficient : Fin dimension → ℝ) :
    ReplicatedFiniteVectorElasticNetObjective
        (copyCount := copyCount + 1) residual l1Weight
        (((copyCount + 1 : ℕ) : ℝ) * l2Weight)
        (fun _ coordinate =>
          aggregateCoefficient coordinate / (copyCount + 1 : ℕ)) =
      FiniteVectorElasticNetObjective residual l1Weight l2Weight
        aggregateCoefficient := by
  rw [balanced_replication_elastic_net_effective_weights]
  have count_nonzero : ((copyCount + 1 : ℕ) : ℝ) ≠ 0 := by
    positivity
  congr 1
  field_simp [count_nonzero]

/-- Every original elastic-net minimizer therefore lifts to a balanced global
minimizer of the repaired replicated representation. -/
theorem original_elastic_net_minimizer_lifts_with_l2_rescaling
    (copyCount : ℕ)
    {dimension : ℕ}
    (residual : (Fin dimension → ℝ) → ℝ)
    (l1Weight l2Weight : ℝ)
    (aggregateMinimizer : Fin dimension → ℝ)
    (l1_nonnegative : 0 ≤ l1Weight)
    (l2_nonnegative : 0 ≤ l2Weight)
    (aggregate_minimal : ∀ candidate,
      FiniteVectorElasticNetObjective residual l1Weight l2Weight
          aggregateMinimizer ≤
        FiniteVectorElasticNetObjective residual l1Weight l2Weight candidate) :
    ∀ coefficient : Fin (copyCount + 1) → Fin dimension → ℝ,
      ReplicatedFiniteVectorElasticNetObjective
          (copyCount := copyCount + 1) residual l1Weight
          (((copyCount + 1 : ℕ) : ℝ) * l2Weight)
          (fun _ coordinate =>
            aggregateMinimizer coordinate / (copyCount + 1 : ℕ)) ≤
        ReplicatedFiniteVectorElasticNetObjective
          (copyCount := copyCount + 1) residual l1Weight
          (((copyCount + 1 : ℕ) : ℝ) * l2Weight) coefficient := by
  intro coefficient
  rw [replication_elastic_net_l2_rescaling_restores_original]
  have scaled_l2_nonnegative :
      0 ≤ ((copyCount + 1 : ℕ) : ℝ) * l2Weight :=
    mul_nonneg (by positivity) l2_nonnegative
  have lower := replicated_vector_elastic_net_lower_bound copyCount residual
    l1Weight (((copyCount + 1 : ℕ) : ℝ) * l2Weight) coefficient
      l1_nonnegative scaled_l2_nonnegative
  have effective_l2_identity :
      (((copyCount + 1 : ℕ) : ℝ) * l2Weight) /
          (copyCount + 1 : ℕ) = l2Weight := by
    field_simp
  rw [effective_l2_identity] at lower
  exact le_trans
    (aggregate_minimal (fun coordinate => ∑ copy, coefficient copy coordinate))
    lower

end OCKIndividuationMSpaceComposition
