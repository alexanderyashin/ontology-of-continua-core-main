import Mathlib.Data.Fintype.Card
import OCKIndividuationMSpaceComposition.POMDPSupportMSpaceCorrespondence

namespace OCKIndividuationMSpaceComposition

universe uEvent uSummary uLabel

/-!
# Full-history Markovization and the exact compression price

Path dependence alone is not an expressivity separation from state-space or
POMDP models: the complete history can always be used as the state.  The
scientific question is whether a smaller observable recursive summary is
sufficient for the declared task.  This module proves both sides and an exact
finite worst-case state-cardinality lower bound.
-/

/-- Full-history state used by the universal Markovization construction. -/
structure FullHistoryState (Event : Type uEvent) where
  trace : List Event
  deriving DecidableEq

/-- One event advances the augmented state by appending it to the trace. -/
def FullHistoryState.advance {Event : Type uEvent}
    (state : FullHistoryState Event) (event : Event) : FullHistoryState Event :=
  ⟨state.trace ++ [event]⟩

/-- The augmented transition is deterministic. -/
theorem full_history_advance_injective_in_event
    {Event : Type uEvent} (state : FullHistoryState Event) :
    Function.Injective state.advance := by
  intro left right equal
  have traceEqual : state.trace ++ [left] = state.trace ++ [right] :=
    congrArg FullHistoryState.trace equal
  simpa using List.append_cancel_left traceEqual

/-- Every path-dependent target is a state-only target on full-history state. -/
def markovizedHistoryDecision
    {Event : Type uEvent} {Label : Type uLabel}
    (target : List Event → Label) : FullHistoryState Event → Label :=
  fun state => target state.trace

/-- Universal positive reduction: evaluating the Markovized decision on the
state carrying `history` recovers the original path-dependent decision exactly. -/
theorem every_history_decision_is_markov_on_full_history_state
    {Event : Type uEvent} {Label : Type uLabel}
    (target : List Event → Label) (history : List Event) :
    markovizedHistoryDecision target ⟨history⟩ = target history := by
  rfl

/-- A recursive online statistic of an event history. -/
structure RecursiveHistorySummary
    (Event : Type uEvent) (Summary : Type uSummary) where
  initial : Summary
  update : Summary → Event → Summary

/-- State reached by folding a recursive summary over the observed path. -/
def RecursiveHistorySummary.summarize
    {Event : Type uEvent} {Summary : Type uSummary}
    (summary : RecursiveHistorySummary Event Summary) : List Event → Summary :=
  List.foldl summary.update summary.initial

/-- Recursive summaries have the Markov update property exactly. -/
theorem RecursiveHistorySummary.summarize_append_event
    {Event : Type uEvent} {Summary : Type uSummary}
    (summary : RecursiveHistorySummary Event Summary)
    (history : List Event) (event : Event) :
    summary.summarize (history ++ [event]) =
      summary.update (summary.summarize history) event := by
  simp [RecursiveHistorySummary.summarize, List.foldl_append]

/-- Exact decision sufficiency for an arbitrary label type. -/
def ExactDecisionSufficient
    {History : Type*} {Summary : Type uSummary} {Label : Type uLabel}
    (summary : History → Summary) (target : History → Label) : Prop :=
  ∃ decode : Summary → Label, ∀ history, decode (summary history) = target history

/-- If a recursive statistic is sufficient, a state-only decoder reproduces
the path target online after every prefix. -/
theorem recursive_sufficiency_gives_online_markov_decision
    {Event : Type uEvent} {Summary : Type uSummary} {Label : Type uLabel}
    (summary : RecursiveHistorySummary Event Summary)
    (target : List Event → Label)
    (sufficient : ExactDecisionSufficient summary.summarize target) :
    ∃ decode : Summary → Label,
      ∀ history, decode (summary.summarize history) = target history :=
  sufficient

/-- Full history is always a recursive sufficient statistic. -/
def fullHistoryRecursiveSummary (Event : Type uEvent) :
    RecursiveHistorySummary Event (List Event) where
  initial := []
  update := fun history event => history ++ [event]

theorem full_history_recursive_summary_is_exact
    {Event : Type uEvent} {Label : Type uLabel}
    (target : List Event → Label) :
    ExactDecisionSufficient
      (fullHistoryRecursiveSummary Event).summarize target := by
  refine ⟨target, ?_⟩
  intro history
  have foldAppend : ∀ (accumulator rest : List Event),
      List.foldl (fun (acc : List Event) (event : Event) => acc ++ [event])
          accumulator rest =
        accumulator ++ rest := by
    intro accumulator rest
    induction rest generalizing accumulator with
    | nil => simp
    | cons head tail inductionHypothesis =>
        simp only [List.foldl_cons]
        rw [inductionHypothesis]
        simp [List.append_assoc]
  simp only [RecursiveHistorySummary.summarize, fullHistoryRecursiveSummary]
  rw [foldAppend [] history]
  rfl

/-! ## Exact finite lower bound for lossless path compression -/

/-- If the target distinguishes every history, any exact sufficient summary
must also distinguish every history. -/
theorem injective_target_forces_sufficient_summary_injective
    {History : Type*} {Summary : Type uSummary} {Label : Type uLabel}
    (summary : History → Summary) (target : History → Label)
    (targetInjective : Function.Injective target)
    (sufficient : ExactDecisionSufficient summary target) :
    Function.Injective summary := by
  rcases sufficient with ⟨decode, recovers⟩
  intro left right sameSummary
  apply targetInjective
  rw [← recovers left, ← recovers right, sameSummary]

/-- Finite cardinality consequence: an exact summary of an injective path
target cannot have fewer states than the history space. -/
theorem injective_target_forces_summary_cardinality_lower_bound
    {History : Type*} {Summary : Type uSummary} {Label : Type uLabel}
    [Fintype History] [Fintype Summary]
    (summary : History → Summary) (target : History → Label)
    (targetInjective : Function.Injective target)
    (sufficient : ExactDecisionSufficient summary target) :
    Fintype.card History ≤ Fintype.card Summary := by
  exact Fintype.card_le_of_injective summary
    (injective_target_forces_sufficient_summary_injective
      summary target targetInjective sufficient)

/-- Fixed-horizon histories over an event alphabet have exactly `q^H` states. -/
theorem fixed_horizon_history_cardinality
    (Event : Type uEvent) [Fintype Event] (horizon : Nat) :
    Fintype.card (Fin horizon → Event) = Fintype.card Event ^ horizon := by
  simp

/-- **Worst-case exponential memory lower bound.** If the task may demand the
entire fixed-horizon history, every exact sufficient summary has at least
`|Event|^H` states.  Thus universal Markovization exists, but lossless state
compression is not free. -/
theorem full_path_recovery_requires_exponential_summary
    (Event : Type uEvent) [Fintype Event]
    (Summary : Type uSummary) [Fintype Summary]
    (horizon : Nat)
    (summary : (Fin horizon → Event) → Summary)
    (sufficient : ExactDecisionSufficient summary id) :
    Fintype.card Event ^ horizon ≤ Fintype.card Summary := by
  rw [← fixed_horizon_history_cardinality Event horizon]
  exact injective_target_forces_summary_cardinality_lower_bound
    summary id Function.injective_id sufficient

/-- Binary histories give the concrete lower bound `2^H`. -/
theorem binary_full_path_recovery_requires_two_pow_horizon_states
    (Summary : Type uSummary) [Fintype Summary]
    (horizon : Nat)
    (summary : (Fin horizon → Bool) → Summary)
    (sufficient : ExactDecisionSufficient summary id) :
    2 ^ horizon ≤ Fintype.card Summary := by
  simpa using full_path_recovery_requires_exponential_summary
    Bool Summary horizon summary sufficient

/-- The exponential lower bound is sharp: the identity/full-history summary
attains exactly `|Event|^H` states. -/
theorem full_path_exponential_summary_bound_is_attained
    (Event : Type uEvent) [Fintype Event] (horizon : Nat) :
    ∃ summary : (Fin horizon → Event) → (Fin horizon → Event),
      ExactDecisionSufficient summary id ∧
        Fintype.card (Fin horizon → Event) =
          Fintype.card Event ^ horizon := by
  refine ⟨id, ⟨id, ?_⟩, fixed_horizon_history_cardinality Event horizon⟩
  intro history
  rfl

/-- Concrete engineering consequence: arbitrary exact recovery of a ten-event
binary path requires at least 1024 summary states. -/
theorem binary_ten_step_full_path_recovery_requires_1024_states
    (Summary : Type uSummary) [Fintype Summary]
    (summary : (Fin 10 → Bool) → Summary)
    (sufficient : ExactDecisionSufficient summary id) :
    1024 ≤ Fintype.card Summary := by
  simpa using binary_full_path_recovery_requires_two_pow_horizon_states
    Summary 10 summary sufficient

end OCKIndividuationMSpaceComposition
