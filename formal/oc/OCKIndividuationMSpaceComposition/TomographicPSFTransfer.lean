import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Data.Fintype.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.BigOperators.Ring.Finset
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite point-spread transfer

The operator below is a finite linear point-spread model.  It is a candidate
for a structural PSF only when a real observation pipeline supplies the kernel
and its coordinate meaning.  The algebra proves superposition and a nullspace
boundary; it does not assert that an arbitrary graph or ETL path is a
convolution, nor that a point response is causal.
-/

section FinitePSF

variable {Index : Type*} [Fintype Index] [DecidableEq Index]

def tomographicPSFTransfer
    (kernel : Index → Index → ℝ) (signal : Index → ℝ) : Index → ℝ :=
  fun output => ∑ input, kernel output input * signal input

def tomographicImpulse (index : Index) : Index → ℝ :=
  fun input => if input = index then 1 else 0

def tomographicPSFRowGain
    (kernel : Index → Index → ℝ) (output : Index) : ℝ :=
  ∑ input, |kernel output input|

theorem tomographicPSFTransfer_add
    (kernel : Index → Index → ℝ) (first second : Index → ℝ) :
    tomographicPSFTransfer kernel (first + second) =
      tomographicPSFTransfer kernel first + tomographicPSFTransfer kernel second := by
  funext output
  simp [tomographicPSFTransfer, mul_add, Finset.sum_add_distrib]

theorem tomographicPSFTransfer_smul
    (kernel : Index → Index → ℝ) (factor : ℝ) (signal : Index → ℝ) :
    tomographicPSFTransfer kernel (factor • signal) =
      factor • tomographicPSFTransfer kernel signal := by
  funext output
  simp only [tomographicPSFTransfer, Pi.smul_apply, smul_eq_mul]
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro input _
  rw [← mul_assoc, mul_comm (kernel output input) factor, mul_assoc]

theorem tomographicPSFTransfer_impulse_response
    (kernel : Index → Index → ℝ) (index output : Index) :
    tomographicPSFTransfer kernel (tomographicImpulse index) output =
      kernel output index := by
  classical
  simp [tomographicPSFTransfer, tomographicImpulse]

theorem tomographicPSFTransfer_abs_bound
    (kernel : Index → Index → ℝ) (signal : Index → ℝ)
    (bound : ℝ) (output : Index)
    (bound_nonnegative : 0 ≤ bound)
    (signal_bound : ∀ input, |signal input| ≤ bound) :
    |tomographicPSFTransfer kernel signal output| ≤
      tomographicPSFRowGain kernel output * bound := by
  unfold tomographicPSFTransfer tomographicPSFRowGain
  calc
    |∑ input, kernel output input * signal input| ≤
        ∑ input, |kernel output input * signal input| :=
      Finset.abs_sum_le_sum_abs _ _
    _ = ∑ input, |kernel output input| * |signal input| := by
      apply Finset.sum_congr rfl
      intro input _
      rw [abs_mul]
    _ ≤ ∑ input, |kernel output input| * bound := by
      apply Finset.sum_le_sum
      intro input _
      exact mul_le_mul_of_nonneg_left (signal_bound input)
        (abs_nonneg _)
    _ = (∑ input, |kernel output input|) * bound := by
      rw [Finset.sum_mul]

theorem tomographicPSFTransfer_nullspace_no_go
    (kernel : Index → Index → ℝ) (signal invisible : Index → ℝ)
    (invisible_zero : tomographicPSFTransfer kernel invisible = 0) :
    tomographicPSFTransfer kernel (signal + invisible) =
      tomographicPSFTransfer kernel signal := by
  rw [tomographicPSFTransfer_add, invisible_zero, add_zero]

end FinitePSF

end OCKIndividuationMSpaceComposition
