import OCMaturityCompletionCycle.MarkovKernelSpecialization
import Mathlib.Probability.Kernel.Composition.MapComap
import Mathlib.MeasureTheory.Constructions.Polish.Basic

/-!
# Actual quotient Markov kernel from an explicit measurable section

The quotient kernel first maps the fine transition measure through `encode`
and then evaluates it at the explicitly selected representative.  No selection
theorem is claimed: measurability and right-inverse laws of the section remain
inputs and occur in the construction/proof.
-/

namespace OCMaturityCompletionCycle

open ProbabilityTheory
open scoped ENNReal

universe uState uAction uQuotient

/-- Actual quotient kernel for one action, built by `map` then section `comap`. -/
noncomputable def quotientKernelFromMeasurableSection
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [MeasurableSpace State]
    [MeasurableSpace Quotient]
    (law : MarkovControlledKernel State Action)
    (quotient : MeasurableQuotient State Quotient)
    (action : Action) : Kernel Quotient Quotient :=
  Kernel.comap
    (Kernel.map (law.transition action) quotient.encode)
    quotient.chooseRepresentative
    quotient.measurable_representative

/-- The constructed quotient family is an actual family of Markov kernels. -/
noncomputable def quotientMarkovControlledKernelFromSection
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [MeasurableSpace State]
    [MeasurableSpace Quotient]
    (law : MarkovControlledKernel State Action)
    (quotient : MeasurableQuotient State Quotient) :
    MarkovControlledKernel Quotient Action where
  transition action := quotientKernelFromMeasurableSection law quotient action
  isMarkov action := by
    letI : IsMarkovKernel (law.transition action) := law.isMarkov action
    have mappedMarkov :
        IsMarkovKernel (Kernel.map (law.transition action) quotient.encode) :=
      Kernel.IsMarkovKernel.map _ quotient.measurable_encode
    letI : IsMarkovKernel
        (Kernel.map (law.transition action) quotient.encode) := mappedMarkov
    exact Kernel.IsMarkovKernel.comap _ quotient.measurable_representative

/--
Under actual strong lumpability, the section-built quotient kernel commutes on
every measurable quotient event.
-/
theorem quotientKernelFromSection_commutes_on_measurableEvent
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [MeasurableSpace State]
    [MeasurableSpace Quotient]
    (law : MarkovControlledKernel State Action)
    (quotient : MeasurableQuotient State Quotient)
    (lumpable : MarkovControlledLumpability law quotient)
    (state : State)
    (action : Action)
    (event : Set Quotient)
    (measurableEvent : MeasurableSet event) :
    quotientKernelFromMeasurableSection law quotient action
        (quotient.encode state) event =
      law.transition action state (quotient.encode ⁻¹' event) := by
  rw [quotientKernelFromMeasurableSection, Kernel.comap_apply',
    Kernel.map_apply' _ quotient.measurable_encode _ measurableEvent]
  exact lumpable
    (left := quotient.chooseRepresentative (quotient.encode state))
    (right := state)
    (quotient.representative_right_inverse (quotient.encode state))
    action event measurableEvent

/--
Standard-Borel singleton specialization.  The Standard-Borel assumption on the
quotient is used to make singleton events measurable; the state space needs no
stronger assumption than its declared measurable structure.
-/
theorem standardBorelQuotientKernel_commutes_on_singleton
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [MeasurableSpace State]
    [MeasurableSpace Quotient]
    [StandardBorelSpace Quotient]
    (law : MarkovControlledKernel State Action)
    (quotient : MeasurableQuotient State Quotient)
    (lumpable : MarkovControlledLumpability law quotient)
    (state : State)
    (action : Action)
    (target : Quotient) :
    quotientKernelFromMeasurableSection law quotient action
        (quotient.encode state) {target} =
      law.transition action state (quotient.encode ⁻¹' {target}) :=
  quotientKernelFromSection_commutes_on_measurableEvent
    law quotient lumpable state action {target} (MeasurableSet.singleton target)

end OCMaturityCompletionCycle
