import OCMaturityCompletionCycle.StochasticOpen
import OCMaturityCompletionCycle.ContextNaturality
import OCMaturityCompletionCycle.JointCharacterization

open OCMaturityCompletionCycle

example : ¬ ControlledLumpability supportKernel supportQuotient :=
  equal_support_not_lumpable

example :
    IsEmpty (UsedContextTransport rowAssembly columnAssembly) ∧
      IsEmpty (UsedContextTransport columnAssembly rowAssembly) :=
  crossing_contexts_have_no_strict_transport

example :
    ¬ BoundaryResponseFactors feedbackStateEncoder feedbackBoundaryEncoder
      feedbackResponse :=
  feedback_without_boundary_congruence_no_go

example :
    (∀ path, 0 < firstPathLaw path ↔ 0 < secondPathLaw path) ∧
      ¬ PathLawStitching firstPathLaw secondPathLaw id :=
  path_support_equality_does_not_determine_law

example :
    (∀ value, firstMarginal .correlated value = firstMarginal .anticorrelated value) ∧
    (∀ value, secondMarginal .correlated value = secondMarginal .anticorrelated value) ∧
    jointMass .correlated (false, false) ≠
      jointMass .anticorrelated (false, false) :=
  hidden_common_cause_breaks_local_composition

example :
    JointAbstractionCertificate True True True True True True ↔
      True ∧ True ∧ True ∧ True ∧ True ∧ True :=
  jointCertificate_iff_componentConjunction True True True True True True
