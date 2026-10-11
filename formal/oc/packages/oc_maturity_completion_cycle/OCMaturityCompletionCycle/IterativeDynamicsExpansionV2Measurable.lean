import OCMaturityCompletionCycle.IterativeDynamicsExpansionV2
import OCMaturityCompletionCycle.OpenStandardBorelSpecialization

/-!
# OC iterative dynamics expansion V2 measurable follow-up

This root is deliberately separate from the finite replay cut.  Its current
ceiling is the exact content proved in `OpenStandardBorelSpecialization`; it must
not be described as measurable finite-horizon stitching until that theorem is
actually mechanized and replayed.
-/

namespace OCMaturityCompletionCycle

def iterativeDynamicsExpansionV2MeasurableScope : String :=
  "STANDARD_BOREL_ONE_STEP_OPEN_INPUT_OUTPUT_SPECIALIZATION_PENDING_PATH_TRANSPORT"

end OCMaturityCompletionCycle
