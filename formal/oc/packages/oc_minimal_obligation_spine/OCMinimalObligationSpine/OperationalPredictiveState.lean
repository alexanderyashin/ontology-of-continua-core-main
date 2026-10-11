import OCMinimalObligationSpine.ProjectionFoundationsClosure
import Mathlib.Logic.Function.Basic
import Mathlib.Logic.Equiv.Basic

namespace OCMinimalObligationSpine

open UnifiedEntityProjection

universe uHistory uPolicy uOutcome uCarrier uObservation uAction

/-!
# Operational predictive state

This module derives state from a declared experimental interface.  The process
law is deterministic here; stochastic laws are supplied by the existing
`StochasticMetakernelMathlib` module.  Deterministic laws are the Dirac special
case closed separately in `FiniteOperationalOptimality`.
-/

/-- The types through which histories can be intervened on and observed. -/
structure ExperimentalInterface where
  History : Type uHistory
  Policy : Type uPolicy
  Outcome : Type uOutcome

/-- An intervention is typed by, and cannot escape, its interface. -/
abbrev InterventionPolicy (interface : ExperimentalInterface) := interface.Policy

/-- A future test is an admitted policy together with the outcome it asks for. -/
structure FutureTest (interface : ExperimentalInterface) where
  policy : InterventionPolicy interface
  accepts : interface.Outcome -> Prop

/-- Exact conditional future behaviour for the deterministic operational layer. -/
structure OperationalProcess (interface : ExperimentalInterface) where
  futureLaw : interface.History -> interface.Policy -> interface.Outcome

/-- Histories are predictively equivalent exactly when every admitted policy agrees. -/
def PredictiveEquivalence
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    (left right : interface.History) : Prop :=
  forall policy, process.futureLaw left policy = process.futureLaw right policy

/-- Predictive equivalence is an equivalence relation. -/
def predictiveEquivalenceSetoid
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface) : Setoid interface.History where
  r := PredictiveEquivalence process
  iseqv := {
    refl := fun _ _ => rfl
    symm := fun equality policy => (equality policy).symm
    trans := fun leftMiddle middleRight policy =>
      (leftMiddle policy).trans (middleRight policy)
  }

/-- The canonical state is the quotient by all admitted future distinctions. -/
abbrev CanonicalPredictiveState
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface) :=
  Quotient (predictiveEquivalenceSetoid process)

/-- Canonical projection from histories to predictive states. -/
def canonicalPredictiveState
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface) :
    interface.History -> CanonicalPredictiveState process :=
  Quotient.mk (predictiveEquivalenceSetoid process)

/-- The future law factors through the quotient for every admitted policy. -/
def canonicalFutureLaw
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface) :
    CanonicalPredictiveState process -> interface.Policy -> interface.Outcome :=
  fun state policy =>
    Quotient.lift
      (fun history => process.futureLaw history policy)
      (fun left right sameLaw => by
        change PredictiveEquivalence process left right at sameLaw
        exact sameLaw policy)
      state

theorem canonicalFutureLaw_mk
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    (history : interface.History)
    (policy : interface.Policy) :
    canonicalFutureLaw process (canonicalPredictiveState process history) policy =
      process.futureLaw history policy := by
  rfl

/-- An encoder is exact-sufficient when none of its collisions changes a future law. -/
def PredictivelySufficient
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    (encode : interface.History -> Carrier) : Prop :=
  forall left right,
    encode left = encode right -> PredictiveEquivalence process left right

/-- The quotient itself is sufficient for all admitted policies. -/
theorem canonicalPredictiveState_sufficient
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface) :
    PredictivelySufficient process (canonicalPredictiveState process) := by
  intro left right sameState
  exact Quotient.exact sameState

/-- Every exact sufficient encoder is at least as fine as the canonical quotient. -/
theorem sufficient_encoder_refines_canonical
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    {encode : interface.History -> Carrier}
    (sufficient : PredictivelySufficient process encode) :
    EncoderKernelRefines encode (canonicalPredictiveState process) := by
  intro left right sameEncoding
  exact Quotient.sound (sufficient left right sameEncoding)

/-- Exact minimality means equality of the encoder kernel and predictive kernel. -/
def ExactMinimalPredictiveEncoder
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    (encode : interface.History -> Carrier) : Prop :=
  EncoderKernelEquivalent encode (canonicalPredictiveState process)

/-- A minimal exact encoder induces a map from canonical states to its used range. -/
def exactEncoderOnCanonicalRange
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    {encode : interface.History -> Carrier}
    (minimal : ExactMinimalPredictiveEncoder process encode) :
    CanonicalPredictiveState process -> EncoderRange encode :=
  Quotient.lift
    (fun history => ⟨encode history, ⟨history, rfl⟩⟩)
    (fun left right sameLaw => by
      apply Subtype.ext
      exact (minimal left right).2 (Quotient.sound sameLaw))

/-- The canonical state recovered from a value in an exact encoder's used range. -/
noncomputable def canonicalFromExactEncoderRange
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    {encode : interface.History -> Carrier}
    (minimal : ExactMinimalPredictiveEncoder process encode) :
    EncoderRange encode -> CanonicalPredictiveState process :=
  kernelFactorOnRange
    (canonicalPredictiveState process)
    (fun left right sameEncoding => (minimal left right).1 sameEncoding)

theorem canonicalFromExactEncoderRange_leftInverse
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    {encode : interface.History -> Carrier}
    (minimal : ExactMinimalPredictiveEncoder process encode) :
    Function.LeftInverse
      (canonicalFromExactEncoderRange process minimal)
      (exactEncoderOnCanonicalRange process minimal) := by
  intro state
  refine Quotient.inductionOn state ?_
  intro history
  exact
    (kernelFactorOnRange_spec
      (fun left right sameEncoding => (minimal left right).1 sameEncoding)
      history).symm

theorem exactEncoderOnCanonicalRange_bijective
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    {encode : interface.History -> Carrier}
    (minimal : ExactMinimalPredictiveEncoder process encode) :
    Function.Bijective (exactEncoderOnCanonicalRange process minimal) := by
  constructor
  · exact (canonicalFromExactEncoderRange_leftInverse process minimal).injective
  · intro value
    rcases value.property with ⟨history, sameValue⟩
    refine ⟨canonicalPredictiveState process history, ?_⟩
    apply Subtype.ext
    exact sameValue

/-- Characterization: minimal exact representations are unique up to used-range isomorphism. -/
noncomputable def minimalEncoderRangeEquivCanonical
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    {encode : interface.History -> Carrier}
    (minimal : ExactMinimalPredictiveEncoder process encode) :
    (CanonicalPredictiveState process) ≃ (EncoderRange encode) :=
  Equiv.ofBijective
    (exactEncoderOnCanonicalRange process minimal)
    (exactEncoderOnCanonicalRange_bijective process minimal)

/-- A deterministic observation channel out of any state representation. -/
structure ObservationChannel (State : Type uHistory) (Observation : Type uObservation) where
  observe : State -> Observation

/-- A bounded decision problem; zero-one losses are the canonical witnesses below. -/
structure DecisionProblem (Outcome : Type uOutcome) where
  Action : Type uAction
  loss : Outcome -> Action -> Nat
  bounded : forall outcome action, loss outcome action <= 1

/-- Deterministic Blackwell dominance: the weaker channel is a garbling. -/
def DeterministicBlackwellDominates
    {State : Type uHistory}
    {Fine : Type uCarrier}
    {Coarse : Type uObservation}
    (fine : ObservationChannel State Fine)
    (coarse : ObservationChannel State Coarse) : Prop :=
  Exists fun garbling : Fine -> Coarse => coarse.observe = garbling ∘ fine.observe

/-- Predictive deficiency and complexity deliberately remain separate coordinates. -/
structure PredictiveDeficiency where
  worstCaseLoss : Nat
  representationComplexity : Nat
  deriving DecidableEq, Repr

/-- A certificate records adequacy and exact kernel minimality, not serialization. -/
structure OptimalityCertificate
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    (Carrier : Type uCarrier) where
  encode : interface.History -> Carrier
  sufficient : PredictivelySufficient process encode
  minimal : ExactMinimalPredictiveEncoder process encode

end OCMinimalObligationSpine
