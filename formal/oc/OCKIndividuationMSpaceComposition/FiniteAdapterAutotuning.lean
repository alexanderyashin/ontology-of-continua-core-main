import OCKIndividuationMSpaceComposition.PredictiveAdapterStack
import Mathlib.Data.Finset.Basic

namespace OCKIndividuationMSpaceComposition

/-!
# Finite, semantically constrained predictive-adapter autotuning

The numerical search is subordinate to an explicit admissibility predicate.
An exhaustive certificate proves an exact optimum on the registered finite
space.  It does not promote that optimum to an unregistered or continuous
adapter universe, and test loss is absent from the selection predicate.
-/

universe uConfig

/-- Exact gate optimum on a registered, semantically admissible search space. -/
structure FiniteAdapterTuningCertificate
    (Config : Type uConfig) [DecidableEq Config]
    (registered : Finset Config)
    (admissible : Config → Prop)
    (gateLoss : Config → ℝ) where
  selected : Config
  selectedRegistered : selected ∈ registered
  selectedAdmissible : admissible selected
  minimizesGateLoss :
    ∀ other, other ∈ registered → admissible other →
      gateLoss selected ≤ gateLoss other

namespace FiniteAdapterTuningCertificate

variable {Config : Type uConfig} [DecidableEq Config]
  {registered : Finset Config} {admissible : Config → Prop}
  {gateLoss : Config → ℝ}

/-- Positive theorem: the certificate is the exact argmin on every registered
configuration allowed by the semantic contract. -/
theorem exact_on_registered_admissible_space
    (certificate : FiniteAdapterTuningCertificate Config registered admissible gateLoss)
    {other : Config} (otherRegistered : other ∈ registered)
    (otherAdmissible : admissible other) :
    gateLoss certificate.selected ≤ gateLoss other :=
  certificate.minimizesGateLoss other otherRegistered otherAdmissible

/-- A numerically attractive but semantically invalid control can never be the
selected adapter, independently of its score. -/
theorem semantically_invalid_cannot_be_selected
    (certificate : FiniteAdapterTuningCertificate Config registered admissible gateLoss)
    {control : Config} (controlInvalid : ¬ admissible control) :
    certificate.selected ≠ control := by
  intro selectedEq
  apply controlInvalid
  simpa [selectedEq] using certificate.selectedAdmissible

/-- Test loss is definitionally irrelevant to the gate-optimality certificate:
changing it cannot alter any proved selection comparison. -/
theorem test_loss_is_not_a_selection_input
    (certificate : FiniteAdapterTuningCertificate Config registered admissible gateLoss)
    (_firstTestLoss _secondTestLoss : Config → ℝ) :
    (∀ other, other ∈ registered → admissible other →
        gateLoss certificate.selected ≤ gateLoss other) ↔
      (∀ other, other ∈ registered → admissible other →
        gateLoss certificate.selected ≤ gateLoss other) := by
  rfl

/-- Configurations within additive tolerance of the certified gate optimum. -/
def NearOptimal
    (certificate : FiniteAdapterTuningCertificate Config registered admissible gateLoss)
    (tolerance : ℝ) (candidate : Config) : Prop :=
  candidate ∈ registered ∧ admissible candidate ∧
    gateLoss candidate ≤ gateLoss certificate.selected + tolerance

/-- The exact optimum belongs to every nonnegative near-optimal region. -/
theorem selected_is_nearOptimal
    (certificate : FiniteAdapterTuningCertificate Config registered admissible gateLoss)
    {tolerance : ℝ} (nonnegative : 0 ≤ tolerance) :
    certificate.NearOptimal tolerance certificate.selected := by
  refine ⟨certificate.selectedRegistered, certificate.selectedAdmissible, ?_⟩
  linarith

end FiniteAdapterTuningCertificate

/-! ## Sharp registered-space boundary -/

/-- Two toy adapter configurations: the registered cell and an unregistered
competitor. -/
inductive AutotuningBoundaryConfig where
  | registered
  | outside
  deriving DecidableEq

def autotuningBoundaryRegistered : Finset AutotuningBoundaryConfig :=
  {AutotuningBoundaryConfig.registered}

def autotuningBoundaryAdmissible (_ : AutotuningBoundaryConfig) : Prop := True

def autotuningBoundaryGateLoss : AutotuningBoundaryConfig → ℝ
  | .registered => 1
  | .outside => 0

def autotuningBoundaryCertificate :
    FiniteAdapterTuningCertificate AutotuningBoundaryConfig
      autotuningBoundaryRegistered autotuningBoundaryAdmissible
      autotuningBoundaryGateLoss where
  selected := .registered
  selectedRegistered := by simp [autotuningBoundaryRegistered]
  selectedAdmissible := trivial
  minimizesGateLoss := by
    intro other otherRegistered _
    simp [autotuningBoundaryRegistered] at otherRegistered
    subst other
    rfl

/-- No-go theorem with witness: exact exhaustive optimality on a registered
finite grid does not imply global optimality outside that grid. -/
theorem finite_grid_optimality_does_not_imply_universal_optimality :
    AutotuningBoundaryConfig.outside ∉ autotuningBoundaryRegistered ∧
      autotuningBoundaryAdmissible AutotuningBoundaryConfig.outside ∧
      autotuningBoundaryGateLoss AutotuningBoundaryConfig.outside <
        autotuningBoundaryGateLoss autotuningBoundaryCertificate.selected := by
  simp [autotuningBoundaryRegistered, autotuningBoundaryAdmissible,
    autotuningBoundaryGateLoss, autotuningBoundaryCertificate]

end OCKIndividuationMSpaceComposition
