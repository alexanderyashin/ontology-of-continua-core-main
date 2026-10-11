import OCMaturityCompletionCycle.IdentityPredictiveBridge
import OCMaturityCompletionCycle.ContextNaturality
import Mathlib.MeasureTheory.MeasurableSpace.Defs

/-!
# Measurable specialization and the joint-characterization boundary

The measurable theorem below is stated for a supplied measurable-event law.  It
assumes a measurable quotient and a measurable section; it constructs neither
a Mathlib `Kernel` nor such a section.  The final record theorem exposes an
important negative result: merely packaging six known certificates is logically
equivalent to their conjunction and therefore cannot establish N3.
-/

namespace OCMaturityCompletionCycle

universe uState uAction uQuotient

/-- A measurable quotient together with an independently supplied section. -/
structure MeasurableQuotient
    (State : Type uState)
    (Quotient : Type uQuotient)
  [MeasurableSpace State]
  [MeasurableSpace Quotient] where
  encode : State → Quotient
  chooseRepresentative : Quotient → State
  measurable_encode : Measurable encode
  measurable_representative : Measurable chooseRepresentative
  representative_right_inverse :
    Function.RightInverse chooseRepresentative encode

/--
A supplied value for every measurable event and control.  This is deliberately
weaker than a Mathlib Markov kernel: normalization and countable additivity are
outside the mechanized claim.
-/
structure MeasurableControlledEventLaw
    (State : Type uState)
    (Action : Type uAction)
    [MeasurableSpace State] where
  eventValue : Action → State → Set State → ℚ

/-- Supplied value assigned to one measurable quotient event. -/
def quotientEventValue
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [MeasurableSpace State]
    [MeasurableSpace Quotient]
    (law : MeasurableControlledEventLaw State Action)
    (quotient : MeasurableQuotient State Quotient)
    (state : State)
    (action : Action)
    (event : Set Quotient) : ℚ :=
  law.eventValue action state (quotient.encode ⁻¹' event)

/-- Strong lumpability tested on every measurable quotient event. -/
def MeasurableControlledLumpability
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [MeasurableSpace State]
    [MeasurableSpace Quotient]
    (law : MeasurableControlledEventLaw State Action)
    (quotient : MeasurableQuotient State Quotient) : Prop :=
  ∀ ⦃left right⦄,
    quotient.encode left = quotient.encode right →
      ∀ action event,
        MeasurableSet event →
          quotientEventValue law quotient left action event =
            quotientEventValue law quotient right action event

/-- Compare every state to the chosen section representative of its class. -/
def SectionRepresentativeAgreement
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [MeasurableSpace State]
    [MeasurableSpace Quotient]
    (law : MeasurableControlledEventLaw State Action)
    (quotient : MeasurableQuotient State Quotient) : Prop :=
  ∀ state action event,
    MeasurableSet event →
      quotientEventValue law quotient state action event =
        quotientEventValue law quotient
          (quotient.chooseRepresentative (quotient.encode state)) action event

/--
Measurable section characterization.  Since it holds for arbitrary measurable
spaces, it specializes in particular to standard-Borel instances.  It proves no
automatic measurable-section existence theorem.
-/
theorem measurableSection_lumpability_iff_representativeAgreement
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [MeasurableSpace State]
    [MeasurableSpace Quotient]
    (law : MeasurableControlledEventLaw State Action)
    (quotient : MeasurableQuotient State Quotient) :
    MeasurableControlledLumpability law quotient ↔
      SectionRepresentativeAgreement law quotient := by
  constructor
  · intro lumpable state action event measurableEvent
    apply lumpable
      (left := state)
      (right := quotient.chooseRepresentative (quotient.encode state))
      ?_ action event measurableEvent
    exact (quotient.representative_right_inverse (quotient.encode state)).symm
  · intro agreement left right sameClass action event measurableEvent
    calc
      quotientEventValue law quotient left action event =
          quotientEventValue law quotient
            (quotient.chooseRepresentative (quotient.encode left)) action event :=
        agreement left action event measurableEvent
      _ = quotientEventValue law quotient
            (quotient.chooseRepresentative (quotient.encode right)) action event := by
        rw [sameClass]
      _ = quotientEventValue law quotient right action event :=
        (agreement right action event measurableEvent).symm

/-! ## Joint certificate and non-novel conjunction boundary -/

/--
Six separately stated properties required by the current joint candidate.  The fields
are propositions because this record is an adjudication boundary, not a claim
that a single universal object has already coupled them.
-/
structure JointAbstractionCertificate
    (evidenceConsistency : Prop)
    (predictiveExactness : Prop)
    (controlledLumpability : Prop)
    (contextNaturality : Prop)
    (contextualCongruence : Prop)
    (supportAndLawStitching : Prop) : Prop where
  evidence_consistent : evidenceConsistency
  predictive_exact : predictiveExactness
  controlled_lumpable : controlledLumpability
  context_natural : contextNaturality
  contextually_congruent : contextualCongruence
  support_and_law_stitching : supportAndLawStitching

/-- Packaging the six properties is exactly their conjunction, nothing more. -/
theorem jointCertificate_iff_componentConjunction
    (evidenceConsistency : Prop)
    (predictiveExactness : Prop)
    (controlledLumpability : Prop)
    (contextNaturality : Prop)
    (contextualCongruence : Prop)
    (supportAndLawStitching : Prop) :
    JointAbstractionCertificate evidenceConsistency predictiveExactness
        controlledLumpability contextNaturality contextualCongruence
        supportAndLawStitching ↔
      evidenceConsistency ∧ predictiveExactness ∧ controlledLumpability ∧
        contextNaturality ∧ contextualCongruence ∧ supportAndLawStitching := by
  constructor
  · intro certificate
    exact ⟨certificate.evidence_consistent, certificate.predictive_exact,
      certificate.controlled_lumpable, certificate.context_natural,
      certificate.contextually_congruent,
      certificate.support_and_law_stitching⟩
  · rintro ⟨evidence, predictive, lumpable, natural, congruent, stitching⟩
    exact ⟨evidence, predictive, lumpable, natural, congruent, stitching⟩

/-- Which independent component defeated a proposed joint certificate. -/
inductive JointObstruction
  | evidenceInconsistent
  | predictiveInsufficient
  | nonlumpable
  | contextTransportFailure
  | distinguishingOpenContext
  | supportOrLawStitchingFailure
  deriving DecidableEq, Repr

/-- Failure of any one component prevents the conjunction-only certificate. -/
theorem missing_component_precludes_jointCertificate
    {evidenceConsistency predictiveExactness controlledLumpability
      contextNaturality contextualCongruence supportAndLawStitching : Prop}
    (missing :
      ¬ evidenceConsistency ∨ ¬ predictiveExactness ∨
      ¬ controlledLumpability ∨ ¬ contextNaturality ∨
      ¬ contextualCongruence ∨ ¬ supportAndLawStitching) :
    ¬ JointAbstractionCertificate evidenceConsistency predictiveExactness
      controlledLumpability contextNaturality contextualCongruence
      supportAndLawStitching := by
  intro certificate
  rcases missing with missing | missing | missing | missing | missing | missing
  · exact missing certificate.evidence_consistent
  · exact missing certificate.predictive_exact
  · exact missing certificate.controlled_lumpable
  · exact missing certificate.context_natural
  · exact missing certificate.contextually_congruent
  · exact missing certificate.support_and_law_stitching

/-- The finite package supplies four different obstruction fixtures. -/
theorem four_distinct_joint_obstruction_fixtures_exist :
    (¬ ControlledLumpability supportKernel supportQuotient) ∧
    IsEmpty (UsedContextTransport rowAssembly columnAssembly) ∧
    (¬ BoundaryResponseFactors feedbackStateEncoder feedbackBoundaryEncoder
      feedbackResponse) ∧
    (∃ first second : Bool × Bool,
      firstBit first = firstBit second ∧
        ∀ reported,
          ExactReportLoss reported
              (secondBitPredictiveKernel.trueWeight first) = 1 ∨
            ExactReportLoss reported
              (secondBitPredictiveKernel.trueWeight second) = 1) := by
  exact ⟨equal_support_not_lumpable,
    crossing_contexts_have_no_strict_transport.1,
    feedback_without_boundary_congruence_no_go,
    finite_stochastic_exactReportLoss_fixture⟩

/-! ## Successor attempt: greatest compatible behavioral relation -/

/--
A relation is observationally invariant when it preserves the current
observation and is closed by one process step.
-/
structure ObservationInvariantRelation
    {State : Type uState}
    {Observation : Type uQuotient}
    (observe : State → Observation)
    (step : State → State)
    (relation : State → State → Prop) : Prop where
  observes : ∀ ⦃left right⦄, relation left right → observe left = observe right
  step_closed : ∀ ⦃left right⦄, relation left right →
    relation (step left) (step right)

/-- Equality of the entire observation stream generated by repeated stepping. -/
def GreatestObservationBehavior
    {State : Type uState}
    {Observation : Type uQuotient}
    (observe : State → Observation)
    (step : State → State) : State → State → Prop :=
  fun left right => ∀ horizon,
    observe (iterateMap step horizon left) =
      observe (iterateMap step horizon right)

/-- The stream relation is itself observation invariant. -/
theorem greatestObservationBehavior_is_invariant
    {State : Type uState}
    {Observation : Type uQuotient}
    (observe : State → Observation)
    (step : State → State) :
    ObservationInvariantRelation observe step
      (GreatestObservationBehavior observe step) := by
  constructor
  · intro left right behavior
    exact behavior 0
  · intro left right behavior horizon
    exact behavior (horizon + 1)

/--
Universal-property form: every observation-invariant relation is contained in
the stream relation.  Thus the latter is the greatest compatible relation.
-/
theorem observationInvariantRelation_below_greatestBehavior
    {State : Type uState}
    {Observation : Type uQuotient}
    (observe : State → Observation)
    (step : State → State)
    (relation : State → State → Prop)
    (invariant : ObservationInvariantRelation observe step relation) :
    RelationRefines relation (GreatestObservationBehavior observe step) := by
  intro left right related horizon
  induction horizon generalizing left right with
  | zero => exact invariant.observes related
  | succ horizon inductionHypothesis =>
      exact inductionHypothesis (invariant.step_closed related)

/-- The greatest behavioral relation is an equivalence relation. -/
theorem greatestObservationBehavior_equivalence
    {State : Type uState}
    {Observation : Type uQuotient}
    (observe : State → Observation)
    (step : State → State) :
    Equivalence (GreatestObservationBehavior observe step) := by
  constructor
  · intro state horizon
    rfl
  · intro left right related horizon
    exact (related horizon).symm
  · intro first second third firstSecond secondThird horizon
    exact (firstSecond horizon).trans (secondThird horizon)

/--
The successor attempt earns a universal property, but its construction is the
standard deterministic behavioral-equivalence/bisimulation pattern.  Novelty
therefore remains a separate prior-art adjudication, not a consequence of this
proof.
-/
structure GreatestCompatibleAbstractionCertificate
    {State : Type uState}
    {Observation : Type uQuotient}
    (observe : State → Observation)
    (step : State → State) : Prop where
  invariant : ObservationInvariantRelation observe step
    (GreatestObservationBehavior observe step)
  greatest : ∀ relation,
    ObservationInvariantRelation observe step relation →
      RelationRefines relation (GreatestObservationBehavior observe step)
  equivalence : Equivalence (GreatestObservationBehavior observe step)

theorem greatestCompatibleAbstractionCertificate_exists
    {State : Type uState}
    {Observation : Type uQuotient}
    (observe : State → Observation)
    (step : State → State) :
    GreatestCompatibleAbstractionCertificate observe step := by
  exact ⟨greatestObservationBehavior_is_invariant observe step,
    fun relation invariant =>
      observationInvariantRelation_below_greatestBehavior
        observe step relation invariant,
    greatestObservationBehavior_equivalence observe step⟩

/-! ## Successor attempt 2: absorb every context into the experiment type -/

/-- Equality under every admitted typed experiment, including open contexts. -/
def AllExperimentBehavior
    {State : Type uState}
    {Experiment : Type uAction}
    {Outcome : Type uQuotient}
    (law : State → Experiment → Outcome) : State → State → Prop :=
  fun left right => ∀ experiment,
    law left experiment = law right experiment

/-- A candidate relation is sound for the full experiment family. -/
def ExperimentSoundRelation
    {State : Type uState}
    {Experiment : Type uAction}
    {Outcome : Type uQuotient}
    (law : State → Experiment → Outcome)
    (relation : State → State → Prop) : Prop :=
  RelationRefines relation (AllExperimentBehavior law)

/-- Full-experiment equality is the greatest sound relation by definition. -/
theorem experimentSoundRelation_below_allExperimentBehavior
    {State : Type uState}
    {Experiment : Type uAction}
    {Outcome : Type uQuotient}
    (law : State → Experiment → Outcome)
    (relation : State → State → Prop)
    (sound : ExperimentSoundRelation law relation) :
    RelationRefines relation (AllExperimentBehavior law) := sound

theorem allExperimentBehavior_equivalence
    {State : Type uState}
    {Experiment : Type uAction}
    {Outcome : Type uQuotient}
    (law : State → Experiment → Outcome) :
    Equivalence (AllExperimentBehavior law) := by
  constructor
  · intro state experiment
    rfl
  · intro left right related experiment
    exact (related experiment).symm
  · intro first second third firstSecond secondThird experiment
    exact (firstSecond experiment).trans (secondThird experiment)

/--
This second successor is mathematically exact, but it obtains jointness only by
placing every context/path/control query in `Experiment`.  It is therefore the
canonical observational quotient pattern, not a coupling theorem deriving open
context exactness from weaker local components.
-/
structure FullExperimentQuotientBoundary
    {State : Type uState}
    {Experiment : Type uAction}
    {Outcome : Type uQuotient}
    (law : State → Experiment → Outcome) : Prop where
  equivalence : Equivalence (AllExperimentBehavior law)
  greatest_sound : ∀ relation,
    ExperimentSoundRelation law relation →
      RelationRefines relation (AllExperimentBehavior law)

theorem fullExperimentQuotientBoundary_exists
    {State : Type uState}
    {Experiment : Type uAction}
    {Outcome : Type uQuotient}
    (law : State → Experiment → Outcome) :
    FullExperimentQuotientBoundary law := by
  exact ⟨allExperimentBehavior_equivalence law,
    fun relation sound =>
      experimentSoundRelation_below_allExperimentBehavior law relation sound⟩

end OCMaturityCompletionCycle
