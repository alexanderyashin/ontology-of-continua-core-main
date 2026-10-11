import Mathlib.Probability.Kernel.Composition.Comp

namespace OCMinimalObligationSpine
namespace StochasticBlackwell

open MeasureTheory ProbabilityTheory
open scoped ProbabilityTheory

universe uState uFine uCoarse uDecision uOutcome

/-- Stochastic experiment dominance is exact Markov-kernel garbling. -/
def BlackwellDominates
    {State : Type uState} {Fine : Type uFine} {Coarse : Type uCoarse}
    [MeasurableSpace State] [MeasurableSpace Fine] [MeasurableSpace Coarse]
    (fine : Kernel State Fine) (coarse : Kernel State Coarse) : Prop :=
  Exists fun garbling : Kernel Fine Coarse =>
    IsMarkovKernel garbling /\ coarse = garbling ∘ₖ fine

/-- Every downstream Markov decision channel can be simulated after the fine experiment. -/
def SimulatesAllDownstreamChannels
    {State : Type uState} {Fine : Type uFine} {Coarse : Type uCoarse}
    [MeasurableSpace State] [MeasurableSpace Fine] [MeasurableSpace Coarse]
    (fine : Kernel State Fine) (coarse : Kernel State Coarse) : Prop :=
  forall decision : Kernel Coarse Coarse,
    IsMarkovKernel decision ->
      Exists fun lifted : Kernel Fine Coarse =>
        IsMarkovKernel lifted /\ lifted ∘ₖ fine = decision ∘ₖ coarse

/-- Garbling is equivalent to universal downstream-channel simulation. -/
theorem blackwellDominates_iff_simulatesAllDownstreamChannels
    {State : Type uState} {Fine : Type uFine} {Coarse : Type uCoarse}
    [MeasurableSpace State] [MeasurableSpace Fine] [MeasurableSpace Coarse]
    (fine : Kernel State Fine) (coarse : Kernel State Coarse)
    [IsMarkovKernel fine] [IsMarkovKernel coarse] :
    BlackwellDominates fine coarse <->
      SimulatesAllDownstreamChannels fine coarse := by
  constructor
  · rintro ⟨garbling, garblingMarkov, rfl⟩ decision decisionMarkov
    letI : IsMarkovKernel garbling := garblingMarkov
    letI : IsMarkovKernel decision := decisionMarkov
    refine ⟨decision ∘ₖ garbling, inferInstance, ?_⟩
    rw [Kernel.comp_assoc]
  · intro simulates
    rcases simulates (Kernel.id) (by infer_instance) with
      ⟨garbling, garblingMarkov, factor⟩
    refine ⟨garbling, garblingMarkov, ?_⟩
    simpa only [Kernel.id_comp] using factor.symm

/-- Deterministic measurable maps embed as Dirac Markov kernels. -/
noncomputable def deterministicAsDiracKernel
    {State : Type uState} {Outcome : Type uOutcome}
    [MeasurableSpace State] [MeasurableSpace Outcome]
    (transition : State -> Outcome) (measurableTransition : Measurable transition) :
    Kernel State Outcome :=
  Kernel.deterministic transition measurableTransition

theorem deterministicAsDiracKernel_apply
    {State : Type uState} {Outcome : Type uOutcome}
    [MeasurableSpace State] [MeasurableSpace Outcome]
    (transition : State -> Outcome) (measurableTransition : Measurable transition)
    (state : State) :
    deterministicAsDiracKernel transition measurableTransition state =
      Measure.dirac (transition state) := by
  exact Kernel.deterministic_apply measurableTransition state

end StochasticBlackwell
end OCMinimalObligationSpine
