import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Ring
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Local linearisation boundary for nonlinear observations

Many enterprise observables are nonlinear.  This module does not declare them
linear: it accepts an explicit local slope and a bounded remainder, then
transports that remainder and a measurement error into a total observation
error.  A local bound is not a global Jacobian, convergence or model-validity
certificate.
-/

def tomographicLinearizedObservation
    (valueAtReference slope reference coordinate : ℝ) : ℝ :=
  valueAtReference + slope * (coordinate - reference)

theorem tomographicLinearization_residual_decomposition
    (valueAtReference slope reference coordinate trueValue observed : ℝ) :
    trueValue - observed =
      (trueValue - tomographicLinearizedObservation
        valueAtReference slope reference coordinate) +
        (tomographicLinearizedObservation
          valueAtReference slope reference coordinate - observed) := by
  ring

theorem tomographicLocalLinearization_error_bound
    (valueAtReference slope reference coordinate trueValue observed
      remainderBound noiseBound : ℝ)
    (remainder_bound :
      |trueValue - tomographicLinearizedObservation
        valueAtReference slope reference coordinate| ≤ remainderBound)
    (noise_bound :
      |tomographicLinearizedObservation
        valueAtReference slope reference coordinate - observed| ≤ noiseBound) :
    |trueValue - observed| ≤ remainderBound + noiseBound := by
  rw [tomographicLinearization_residual_decomposition
    valueAtReference slope reference coordinate trueValue observed]
  exact le_trans (abs_add_le _ _)
    (add_le_add remainder_bound noise_bound)

end OCKIndividuationMSpaceComposition