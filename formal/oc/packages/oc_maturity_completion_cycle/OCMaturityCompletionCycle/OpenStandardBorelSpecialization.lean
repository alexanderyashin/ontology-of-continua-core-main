import OCMaturityCompletionCycle.StandardBorelQuotientKernel
import OCMaturityCompletionCycle.JointIdentityLawCoherence

/-!
# Measurable open joint-kernel specialization

The kernel emits `(nextState × boundaryOut)`.  State and current inputs have
independent measurable quotient/section data; boundary output has the weaker
forward measurable encoder actually used by the construction.  The commutation
theorem uses both state lumpability and current-control congruence; a coordinate
relabeling alone is insufficient.
-/

namespace OCMaturityCompletionCycle

open ProbabilityTheory
open scoped ENNReal

universe uState uContext uBoundaryIn uAction uBoundaryOut
  uAbstractState uAbstractContext uAbstractBoundaryIn uAbstractAction
  uAbstractBoundaryOut

/-- Actual Markov family with joint state/boundary output. -/
structure MarkovJointOpenKernel
    (State : Type uState)
    (Context : Type uContext)
    (BoundaryIn : Type uBoundaryIn)
    (Action : Type uAction)
    (BoundaryOut : Type uBoundaryOut)
    [MeasurableSpace State]
    [MeasurableSpace BoundaryOut] where
  transition : JointOpenControl Context BoundaryIn Action →
    Kernel State (State × BoundaryOut)
  isMarkov : ∀ control, IsMarkovKernel (transition control)

/--
A measurable output encoder.  Unlike state and current inputs, an emitted
boundary value is only mapped forward in the quotient kernel, so no unused
section/right-inverse assumption is imposed on it.
-/
structure MeasurableOutputEncoder
    (Fine : Type*)
    (Abstract : Type*)
    [MeasurableSpace Fine]
    [MeasurableSpace Abstract] where
  encode : Fine → Abstract
  measurable_encode : Measurable encode

/-- Measurable quotient/section data for state and open inputs. -/
structure MeasurableJointOpenAbstraction
    (State : Type uState)
    (Context : Type uContext)
    (BoundaryIn : Type uBoundaryIn)
    (Action : Type uAction)
    (BoundaryOut : Type uBoundaryOut)
    (AbstractState : Type uAbstractState)
    (AbstractContext : Type uAbstractContext)
    (AbstractBoundaryIn : Type uAbstractBoundaryIn)
    (AbstractAction : Type uAbstractAction)
    (AbstractBoundaryOut : Type uAbstractBoundaryOut)
    [MeasurableSpace State]
    [MeasurableSpace Context]
    [MeasurableSpace BoundaryIn]
    [MeasurableSpace Action]
    [MeasurableSpace BoundaryOut]
    [MeasurableSpace AbstractState]
    [MeasurableSpace AbstractContext]
    [MeasurableSpace AbstractBoundaryIn]
    [MeasurableSpace AbstractAction]
    [MeasurableSpace AbstractBoundaryOut] where
  state : MeasurableQuotient State AbstractState
  context : MeasurableQuotient Context AbstractContext
  boundaryIn : MeasurableQuotient BoundaryIn AbstractBoundaryIn
  action : MeasurableQuotient Action AbstractAction
  boundaryOut : MeasurableOutputEncoder BoundaryOut AbstractBoundaryOut

/-- Encode one joint state/output outcome. -/
def measurableJointOutcomeEncode
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [MeasurableSpace State]
    [MeasurableSpace Context]
    [MeasurableSpace BoundaryIn]
    [MeasurableSpace Action]
    [MeasurableSpace BoundaryOut]
    [MeasurableSpace AbstractState]
    [MeasurableSpace AbstractContext]
    [MeasurableSpace AbstractBoundaryIn]
    [MeasurableSpace AbstractAction]
    [MeasurableSpace AbstractBoundaryOut]
    (abstraction : MeasurableJointOpenAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut) :
    State × BoundaryOut → AbstractState × AbstractBoundaryOut :=
  fun outcome =>
    (abstraction.state.encode outcome.1,
      abstraction.boundaryOut.encode outcome.2)

theorem measurable_measurableJointOutcomeEncode
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [MeasurableSpace State]
    [MeasurableSpace Context]
    [MeasurableSpace BoundaryIn]
    [MeasurableSpace Action]
    [MeasurableSpace BoundaryOut]
    [MeasurableSpace AbstractState]
    [MeasurableSpace AbstractContext]
    [MeasurableSpace AbstractBoundaryIn]
    [MeasurableSpace AbstractAction]
    [MeasurableSpace AbstractBoundaryOut]
    (abstraction : MeasurableJointOpenAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut) :
    Measurable (measurableJointOutcomeEncode abstraction) := by
  exact
    (abstraction.state.measurable_encode.comp measurable_fst).prodMk
      (abstraction.boundaryOut.measurable_encode.comp measurable_snd)

/-- Encode one fine context/boundary/action input. -/
def measurableOpenControlEncode
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [MeasurableSpace State]
    [MeasurableSpace Context]
    [MeasurableSpace BoundaryIn]
    [MeasurableSpace Action]
    [MeasurableSpace BoundaryOut]
    [MeasurableSpace AbstractState]
    [MeasurableSpace AbstractContext]
    [MeasurableSpace AbstractBoundaryIn]
    [MeasurableSpace AbstractAction]
    [MeasurableSpace AbstractBoundaryOut]
    (abstraction : MeasurableJointOpenAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut) :
    JointOpenControl Context BoundaryIn Action →
      JointOpenControl AbstractContext AbstractBoundaryIn AbstractAction :=
  fun control =>
    (abstraction.context.encode control.1,
      abstraction.boundaryIn.encode control.2.1,
      abstraction.action.encode control.2.2)

/-- Select fine representatives of one abstract open input. -/
def measurableOpenControlRepresentative
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [MeasurableSpace State]
    [MeasurableSpace Context]
    [MeasurableSpace BoundaryIn]
    [MeasurableSpace Action]
    [MeasurableSpace BoundaryOut]
    [MeasurableSpace AbstractState]
    [MeasurableSpace AbstractContext]
    [MeasurableSpace AbstractBoundaryIn]
    [MeasurableSpace AbstractAction]
    [MeasurableSpace AbstractBoundaryOut]
    (abstraction : MeasurableJointOpenAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut) :
    JointOpenControl AbstractContext AbstractBoundaryIn AbstractAction →
      JointOpenControl Context BoundaryIn Action :=
  fun control =>
    (abstraction.context.chooseRepresentative control.1,
      abstraction.boundaryIn.chooseRepresentative control.2.1,
      abstraction.action.chooseRepresentative control.2.2)

theorem measurable_measurableOpenControlRepresentative
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [MeasurableSpace State]
    [MeasurableSpace Context]
    [MeasurableSpace BoundaryIn]
    [MeasurableSpace Action]
    [MeasurableSpace BoundaryOut]
    [MeasurableSpace AbstractState]
    [MeasurableSpace AbstractContext]
    [MeasurableSpace AbstractBoundaryIn]
    [MeasurableSpace AbstractAction]
    [MeasurableSpace AbstractBoundaryOut]
    (abstraction : MeasurableJointOpenAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut) :
    Measurable (measurableOpenControlRepresentative abstraction) := by
  exact
    (abstraction.context.measurable_representative.comp measurable_fst).prodMk
      ((abstraction.boundaryIn.measurable_representative.comp
          (measurable_fst.comp measurable_snd)).prodMk
        (abstraction.action.measurable_representative.comp
          (measurable_snd.comp measurable_snd)))

theorem measurableOpenControlRepresentative_rightInverse
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [MeasurableSpace State]
    [MeasurableSpace Context]
    [MeasurableSpace BoundaryIn]
    [MeasurableSpace Action]
    [MeasurableSpace BoundaryOut]
    [MeasurableSpace AbstractState]
    [MeasurableSpace AbstractContext]
    [MeasurableSpace AbstractBoundaryIn]
    [MeasurableSpace AbstractAction]
    [MeasurableSpace AbstractBoundaryOut]
    (abstraction : MeasurableJointOpenAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut) :
    Function.RightInverse
      (measurableOpenControlRepresentative abstraction)
      (measurableOpenControlEncode abstraction) := by
  intro control
  apply Prod.ext
  · exact abstraction.context.representative_right_inverse control.1
  · apply Prod.ext
    · exact abstraction.boundaryIn.representative_right_inverse control.2.1
    · exact abstraction.action.representative_right_inverse control.2.2

/-- Actual abstract joint kernel built by map then state-section comap. -/
noncomputable def quotientJointOpenKernelFromSections
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [MeasurableSpace State]
    [MeasurableSpace Context]
    [MeasurableSpace BoundaryIn]
    [MeasurableSpace Action]
    [MeasurableSpace BoundaryOut]
    [MeasurableSpace AbstractState]
    [MeasurableSpace AbstractContext]
    [MeasurableSpace AbstractBoundaryIn]
    [MeasurableSpace AbstractAction]
    [MeasurableSpace AbstractBoundaryOut]
    (law : MarkovJointOpenKernel State Context BoundaryIn Action BoundaryOut)
    (abstraction : MeasurableJointOpenAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut)
    (control : JointOpenControl AbstractContext AbstractBoundaryIn AbstractAction) :
    Kernel AbstractState (AbstractState × AbstractBoundaryOut) :=
  Kernel.comap
    (Kernel.map
      (law.transition (measurableOpenControlRepresentative abstraction control))
      (measurableJointOutcomeEncode abstraction))
    abstraction.state.chooseRepresentative
    abstraction.state.measurable_representative

/-- The section-built open quotient is an actual Markov joint kernel. -/
noncomputable def quotientMarkovJointOpenKernelFromSections
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [MeasurableSpace State]
    [MeasurableSpace Context]
    [MeasurableSpace BoundaryIn]
    [MeasurableSpace Action]
    [MeasurableSpace BoundaryOut]
    [MeasurableSpace AbstractState]
    [MeasurableSpace AbstractContext]
    [MeasurableSpace AbstractBoundaryIn]
    [MeasurableSpace AbstractAction]
    [MeasurableSpace AbstractBoundaryOut]
    (law : MarkovJointOpenKernel State Context BoundaryIn Action BoundaryOut)
    (abstraction : MeasurableJointOpenAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut) :
    MarkovJointOpenKernel AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut where
  transition := quotientJointOpenKernelFromSections law abstraction
  isMarkov control := by
    letI : IsMarkovKernel
        (law.transition (measurableOpenControlRepresentative abstraction control)) :=
      law.isMarkov _
    have mappedMarkov : IsMarkovKernel
        (Kernel.map
          (law.transition (measurableOpenControlRepresentative abstraction control))
          (measurableJointOutcomeEncode abstraction)) :=
      Kernel.IsMarkovKernel.map _
        (measurable_measurableJointOutcomeEncode abstraction)
    letI := mappedMarkov
    exact Kernel.IsMarkovKernel.comap _
      abstraction.state.measurable_representative

/-- State quotient consistency for every fine open input. -/
def MarkovJointOpenStateLumpability
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [MeasurableSpace State]
    [MeasurableSpace Context]
    [MeasurableSpace BoundaryIn]
    [MeasurableSpace Action]
    [MeasurableSpace BoundaryOut]
    [MeasurableSpace AbstractState]
    [MeasurableSpace AbstractContext]
    [MeasurableSpace AbstractBoundaryIn]
    [MeasurableSpace AbstractAction]
    [MeasurableSpace AbstractBoundaryOut]
    (law : MarkovJointOpenKernel State Context BoundaryIn Action BoundaryOut)
    (abstraction : MeasurableJointOpenAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut) : Prop :=
  ∀ ⦃left right⦄,
    abstraction.state.encode left = abstraction.state.encode right →
      ∀ control event,
        MeasurableSet event →
          law.transition control left
              ((measurableJointOutcomeEncode abstraction) ⁻¹' event) =
            law.transition control right
              ((measurableJointOutcomeEncode abstraction) ⁻¹' event)

/-- Fine controls in one abstract control fibre have the same joint output law. -/
def MarkovJointOpenControlCongruence
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [MeasurableSpace State]
    [MeasurableSpace Context]
    [MeasurableSpace BoundaryIn]
    [MeasurableSpace Action]
    [MeasurableSpace BoundaryOut]
    [MeasurableSpace AbstractState]
    [MeasurableSpace AbstractContext]
    [MeasurableSpace AbstractBoundaryIn]
    [MeasurableSpace AbstractAction]
    [MeasurableSpace AbstractBoundaryOut]
    (law : MarkovJointOpenKernel State Context BoundaryIn Action BoundaryOut)
    (abstraction : MeasurableJointOpenAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut) : Prop :=
  ∀ state ⦃left right⦄,
    measurableOpenControlEncode abstraction left =
        measurableOpenControlEncode abstraction right →
      ∀ event,
        MeasurableSet event →
          law.transition left state
              ((measurableJointOutcomeEncode abstraction) ⁻¹' event) =
            law.transition right state
              ((measurableJointOutcomeEncode abstraction) ⁻¹' event)

/-- Open quotient commutation at an encoded fine state and encoded fine input. -/
theorem quotientJointOpenKernel_commutes_on_measurableEvent
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [MeasurableSpace State]
    [MeasurableSpace Context]
    [MeasurableSpace BoundaryIn]
    [MeasurableSpace Action]
    [MeasurableSpace BoundaryOut]
    [MeasurableSpace AbstractState]
    [MeasurableSpace AbstractContext]
    [MeasurableSpace AbstractBoundaryIn]
    [MeasurableSpace AbstractAction]
    [MeasurableSpace AbstractBoundaryOut]
    (law : MarkovJointOpenKernel State Context BoundaryIn Action BoundaryOut)
    (abstraction : MeasurableJointOpenAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut)
    (stateLumpable : MarkovJointOpenStateLumpability law abstraction)
    (controlCongruent : MarkovJointOpenControlCongruence law abstraction)
    (state : State)
    (control : JointOpenControl Context BoundaryIn Action)
    (event : Set (AbstractState × AbstractBoundaryOut))
    (measurableEvent : MeasurableSet event) :
    quotientJointOpenKernelFromSections law abstraction
        (measurableOpenControlEncode abstraction control)
        (abstraction.state.encode state) event =
      law.transition control state
        ((measurableJointOutcomeEncode abstraction) ⁻¹' event) := by
  rw [quotientJointOpenKernelFromSections, Kernel.comap_apply',
    Kernel.map_apply' _ (measurable_measurableJointOutcomeEncode abstraction)
      _ measurableEvent]
  let representativeState :=
    abstraction.state.chooseRepresentative (abstraction.state.encode state)
  let representativeControl :=
    measurableOpenControlRepresentative abstraction
      (measurableOpenControlEncode abstraction control)
  have sameControl :
      measurableOpenControlEncode abstraction representativeControl =
        measurableOpenControlEncode abstraction control := by
    exact measurableOpenControlRepresentative_rightInverse abstraction
      (measurableOpenControlEncode abstraction control)
  have controlStep := controlCongruent representativeState sameControl event
    measurableEvent
  have sameState :
      abstraction.state.encode representativeState =
        abstraction.state.encode state :=
    abstraction.state.representative_right_inverse
      (abstraction.state.encode state)
  have stateStep := stateLumpable sameState control event measurableEvent
  exact controlStep.trans stateStep

/-- Standard-Borel singleton specialization for joint state/output outcomes. -/
theorem standardBorelJointOpenKernel_commutes_on_singleton
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [MeasurableSpace State]
    [MeasurableSpace Context]
    [MeasurableSpace BoundaryIn]
    [MeasurableSpace Action]
    [MeasurableSpace BoundaryOut]
    [MeasurableSpace AbstractState]
    [MeasurableSpace AbstractContext]
    [MeasurableSpace AbstractBoundaryIn]
    [MeasurableSpace AbstractAction]
    [MeasurableSpace AbstractBoundaryOut]
    [StandardBorelSpace AbstractState]
    [StandardBorelSpace AbstractBoundaryOut]
    (law : MarkovJointOpenKernel State Context BoundaryIn Action BoundaryOut)
    (abstraction : MeasurableJointOpenAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut)
    (stateLumpable : MarkovJointOpenStateLumpability law abstraction)
    (controlCongruent : MarkovJointOpenControlCongruence law abstraction)
    (state : State)
    (control : JointOpenControl Context BoundaryIn Action)
    (target : AbstractState × AbstractBoundaryOut) :
    quotientJointOpenKernelFromSections law abstraction
        (measurableOpenControlEncode abstraction control)
        (abstraction.state.encode state) {target} =
      law.transition control state
        ((measurableJointOutcomeEncode abstraction) ⁻¹' {target}) :=
  quotientJointOpenKernel_commutes_on_measurableEvent law abstraction
    stateLumpable controlCongruent state control {target}
    (MeasurableSet.singleton target)

end OCMaturityCompletionCycle
