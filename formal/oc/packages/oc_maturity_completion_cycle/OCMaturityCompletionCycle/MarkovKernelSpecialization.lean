import OCMaturityCompletionCycle.JointCharacterization
import Mathlib.Probability.Kernel.Basic
import Mathlib.MeasureTheory.Constructions.Polish.Basic

/-!
# Actual Markov-kernel section specialization

This module replaces the supplied-event-law placeholder by an actual Mathlib
`Kernel`.  The result remains section-relative: a measurable quotient and a
measurable right-inverse are inputs.  It does not construct a quotient kernel,
prove that a measurable section exists, or use a specifically standard-Borel
selection theorem.
-/

namespace OCMaturityCompletionCycle

open ProbabilityTheory
open scoped ENNReal

universe uState uAction uQuotient

/-- A controlled family of actual Mathlib Markov kernels. -/
structure MarkovControlledKernel
    (State : Type uState)
    (Action : Type uAction)
    [MeasurableSpace State] where
  transition : Action → Kernel State State
  isMarkov : ∀ action, IsMarkovKernel (transition action)

/-- Probability assigned by a controlled Markov kernel to a quotient event. -/
def markovQuotientEventValue
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [MeasurableSpace State]
    [MeasurableSpace Quotient]
    (law : MarkovControlledKernel State Action)
    (quotient : MeasurableQuotient State Quotient)
    (state : State)
    (action : Action)
    (event : Set Quotient) : ℝ≥0∞ :=
  law.transition action state (quotient.encode ⁻¹' event)

/-- Strong lumpability of the actual kernel on all measurable quotient events. -/
def MarkovControlledLumpability
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [MeasurableSpace State]
    [MeasurableSpace Quotient]
    (law : MarkovControlledKernel State Action)
    (quotient : MeasurableQuotient State Quotient) : Prop :=
  ∀ ⦃left right⦄,
    quotient.encode left = quotient.encode right →
      ∀ action event,
        MeasurableSet event →
          markovQuotientEventValue law quotient left action event =
            markovQuotientEventValue law quotient right action event

/-- Compare every state with the selected representative of its quotient class. -/
def MarkovSectionRepresentativeAgreement
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [MeasurableSpace State]
    [MeasurableSpace Quotient]
    (law : MarkovControlledKernel State Action)
    (quotient : MeasurableQuotient State Quotient) : Prop :=
  ∀ state action event,
    MeasurableSet event →
      markovQuotientEventValue law quotient state action event =
        markovQuotientEventValue law quotient
          (quotient.chooseRepresentative (quotient.encode state)) action event

/--
For an independently supplied measurable section, actual-kernel lumpability is
equivalent to representative agreement.  This theorem uses the kernel as a
measure-valued map; it does not construct a quotient kernel.
-/
theorem markovSection_lumpability_iff_representativeAgreement
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [MeasurableSpace State]
    [MeasurableSpace Quotient]
    (law : MarkovControlledKernel State Action)
    (quotient : MeasurableQuotient State Quotient) :
    MarkovControlledLumpability law quotient ↔
      MarkovSectionRepresentativeAgreement law quotient := by
  constructor
  · intro lumpable state action event measurableEvent
    apply lumpable
      (left := state)
      (right := quotient.chooseRepresentative (quotient.encode state))
      ?_ action event measurableEvent
    exact (quotient.representative_right_inverse (quotient.encode state)).symm
  · intro agreement left right sameClass action event measurableEvent
    calc
      markovQuotientEventValue law quotient left action event =
          markovQuotientEventValue law quotient
            (quotient.chooseRepresentative (quotient.encode left)) action event :=
        agreement left action event measurableEvent
      _ = markovQuotientEventValue law quotient
            (quotient.chooseRepresentative (quotient.encode right)) action event := by
        rw [sameClass]
      _ = markovQuotientEventValue law quotient right action event :=
        (agreement right action event measurableEvent).symm

/--
The preceding section-relative theorem remains valid when both spaces happen to
be standard Borel.  The extra typeclass assumptions are intentionally not used:
this specialization proves neither existence nor measurability of a quotient or
section, which are already explicit inputs.
-/
theorem standardBorelSection_lumpability_iff_representativeAgreement
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [MeasurableSpace State]
    [MeasurableSpace Quotient]
    [StandardBorelSpace State]
    [StandardBorelSpace Quotient]
    (law : MarkovControlledKernel State Action)
    (quotient : MeasurableQuotient State Quotient) :
    MarkovControlledLumpability law quotient ↔
      MarkovSectionRepresentativeAgreement law quotient :=
  markovSection_lumpability_iff_representativeAgreement law quotient

end OCMaturityCompletionCycle
