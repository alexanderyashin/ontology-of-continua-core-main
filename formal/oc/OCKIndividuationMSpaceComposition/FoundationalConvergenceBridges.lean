import OCKIndividuationMSpaceComposition.StrongestUniversalization
import OCKIndividuationMSpaceComposition.QualifiedCurrentKBridge
import OCKIndividuationMSpaceComposition.ConstitutiveBridge
import OCMaturityCompletionCycle.IdentityPredictiveBridge
import OCMinimalObligationSpine.OperationalPredictiveState

/-!
# Foundational convergence bridges

This additive module records only compositional consequences of the frozen
identity and predictive-state interfaces. It is outside the frozen unified
successor denominator and makes no empirical or domain claim.
-/

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle
open OCMinimalObligationSpine

universe
  uHistory uOccurrence uToken uPolicy uOutcome
  uMechanism uIntervention uCausalOutcome uProvenance uTime uAccess
  uMemberOccurrence uMemberExperiment uMemberOutcome
  uObjectOccurrence uInput uObjectExperiment uObjectOutcome
  uIndex uChild uParent

/-- Raw continuation evidence is predictively safe when every evidence edge
preserves every future distinction admitted by the operational process. -/
def ContinuationPredictivelySafe
    {interface : ExperimentalInterface}
    (evidence : BinaryRelation interface.History)
    (process : OperationalProcess interface) : Prop :=
  ∀ ⦃left right⦄,
    evidence left right → PredictiveEquivalence process left right

/--
Exact characterization of predictive descent through the operational-token
quotient. The forward direction is the quotient universal property; the
reverse direction follows from commutation plus the fact that every raw
evidence edge becomes token equality.
-/
theorem continuationPredictivelySafe_iff_operationalToken_uniqueFactorization
    {interface : ExperimentalInterface}
    (evidence : BinaryRelation interface.History)
    (process : OperationalProcess interface) :
    ContinuationPredictivelySafe evidence process ↔
      ∃! factor : OperationalToken evidence → CanonicalPredictiveState process,
        ∀ history,
          factor (operationalTokenOf evidence history) =
            canonicalPredictiveState process history := by
  constructor
  · intro safe
    apply operationalToken_lift_unique (canonicalPredictiveState process)
    intro left right edge
    exact Quotient.sound (safe edge)
  · rintro ⟨factor, commutes, _unique⟩ left right edge
    have sameToken :
        operationalTokenOf evidence left = operationalTokenOf evidence right :=
      Quotient.sound (.ofEvidence edge)
    have samePredictiveState :
        canonicalPredictiveState process left =
          canonicalPredictiveState process right := by
      calc
        canonicalPredictiveState process left =
            factor (operationalTokenOf evidence left) := (commutes left).symm
        _ = factor (operationalTokenOf evidence right) := congrArg factor sameToken
        _ = canonicalPredictiveState process right := commutes right
    exact Quotient.exact samePredictiveState

/-- Exact equality of the token and predictive kernels yields the canonical
used-range equivalence already provided by the predictive-state apparatus. -/
theorem exactOperationalTokenBridge_has_usedRangeEquivalence
    {interface : ExperimentalInterface}
    (evidence : BinaryRelation interface.History)
    (process : OperationalProcess interface)
    (exactBridge :
      ExactIdentityPredictiveBridge
        (operationalTokenOf evidence)
        (canonicalPredictiveState process)) :
    Nonempty
      (CanonicalPredictiveState process ≃
        EncoderRange (operationalTokenOf evidence)) := by
  have minimal :
      ExactMinimalPredictiveEncoder process (operationalTokenOf evidence) := by
    intro left right
    exact exactBridge left right
  exact ⟨minimalEncoderRangeEquivCanonical process minimal⟩

/-! ## Causal-kernel underdetermination boundary -/

/--
A history interpretation can require every represented mechanism to lie in
one generated causal kernel while carrying an independently declared
equivalence relation on histories.  The relation is explicit because
`GeneratedKernel model root` is a unary membership predicate, not a binary
identity, predictive, or K-observational relation.
-/
structure KernelQualifiedHistoryEquivalence
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {CausalOutcome : Type uCausalOutcome}
    (model : ActiveConstraintModel Mechanism Intervention CausalOutcome)
    (root : Mechanism)
    (History : Type uHistory) where
  mechanismOf : History → Mechanism
  mechanism_generated : ∀ history, GeneratedKernel model root (mechanismOf history)
  equivalent : BinaryRelation History
  equivalent_refl : ∀ history, equivalent history history
  equivalent_symm : ∀ {first second}, equivalent first second → equivalent second first
  equivalent_trans : ∀ {first second third},
    equivalent first second → equivalent second third → equivalent first third

/--
Generated-kernel membership alone does not determine even an equivalence
relation on histories: two interpretations can have the identical carrier
map into the identical generated kernel while disagreeing on whether two
histories are equivalent.
-/
theorem generatedKernel_membership_does_not_determine_history_equivalence
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {CausalOutcome : Type uCausalOutcome}
    (model : ActiveConstraintModel Mechanism Intervention CausalOutcome)
    (root : Mechanism) :
    ∃ equalityInterpretation indiscreteInterpretation :
        KernelQualifiedHistoryEquivalence model root Bool,
      equalityInterpretation.mechanismOf =
          indiscreteInterpretation.mechanismOf ∧
        equalityInterpretation.equivalent ≠
          indiscreteInterpretation.equivalent := by
  let equalityInterpretation :
      KernelQualifiedHistoryEquivalence model root Bool := {
    mechanismOf := fun _ => root
    mechanism_generated := fun _ => generatedKernel_contains_root model root
    equivalent := fun first second => first = second
    equivalent_refl := fun _ => rfl
    equivalent_symm := fun equal => equal.symm
    equivalent_trans := fun firstSecond secondThird => firstSecond.trans secondThird
  }
  let indiscreteInterpretation :
      KernelQualifiedHistoryEquivalence model root Bool := {
    mechanismOf := fun _ => root
    mechanism_generated := fun _ => generatedKernel_contains_root model root
    equivalent := fun _ _ => True
    equivalent_refl := fun _ => trivial
    equivalent_symm := fun _ => trivial
    equivalent_trans := fun _ _ => trivial
  }
  refine ⟨equalityInterpretation, indiscreteInterpretation, rfl, ?_⟩
  intro relationsEqual
  have falseEqualsTrue : false = true := by
    have relationAtWitness :=
      congrFun (congrFun relationsEqual false) true
    exact Eq.mpr relationAtWitness trivial
  exact Bool.false_ne_true falseEqualsTrue

/-! ## Prediction--K composition through an explicit typed adapter -/

/--
The missing carrier map between histories and object occurrences.  This is
data, not an inferred identification: `endpoint` selects the represented
occurrence and `sameToken_iff_tokenEquality` states exactly when its object
token agrees with the history identity encoder.
-/
structure HistoryOccurrenceTokenAdapter
    {History : Type uHistory}
    {Occurrence : Type uOccurrence}
    {Token : Type uToken}
    (sameOccurrenceToken : BinaryRelation Occurrence)
    (tokenOf : History → Token) where
  endpoint : History → Occurrence
  sameToken_iff_tokenEquality : ∀ first second,
    sameOccurrenceToken (endpoint first) (endpoint second) ↔
      tokenOf first = tokenOf second

/--
Once the carrier adapter and the four independent exactness contracts are
visible, K-trajectory equivalence is exactly predictive equivalence.  No cast,
carrier equality, or hidden identification is used: the proof composes
K-to-token, adapter, token-to-canonical-state, and quotient exactness.
-/
theorem prediction_K_exact_iff_of_typed_adapter
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {CausalOutcome : Type uCausalOutcome}
    {model : ActiveConstraintModel Mechanism Intervention CausalOutcome}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {formedBy : Mechanism → Provenance → Prop}
    {continuesAt : Mechanism → Time → Prop}
    {robustAtScale : (Mechanism → Prop) → Prop}
    {Access : Type uAccess}
    {accessContext : AtomicAccessContext Mechanism Access}
    {MemberOccurrence : Type uMemberOccurrence}
    {MemberExperiment : Type uMemberExperiment}
    {MemberOutcome : Type uMemberOutcome}
    {memberEvidence : BinaryRelation MemberOccurrence}
    {memberLaw : MemberOccurrence → MemberExperiment → MemberOutcome}
    {ObjectOccurrence : Type uObjectOccurrence}
    {Input : Type uInput}
    {ObjectExperiment : Type uObjectExperiment}
    {ObjectOutcome : Type uObjectOutcome}
    {object : GeneralizedDynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale Access accessContext MemberOccurrence
      MemberExperiment MemberOutcome memberEvidence memberLaw ObjectOccurrence
      Input ObjectExperiment ObjectOutcome}
    {K : CurrentK}
    {interface : ExperimentalInterface}
    {evidence : BinaryRelation interface.History}
    (bridge : QualifiedCurrentKBridge object K)
    (adapter : HistoryOccurrenceTokenAdapter object.SameToken
      (operationalTokenOf evidence))
    (invariant : bridge.TokenObservationInvariant)
    (separates : bridge.KSeparatesTokens)
    (process : OperationalProcess interface)
    (exactBridge : ExactIdentityPredictiveBridge
      (operationalTokenOf evidence) (canonicalPredictiveState
        (interface := interface) process))
    (first second : interface.History) :
    bridge.KTrajectoryEquivalent (adapter.endpoint first)
        (adapter.endpoint second) ↔
      PredictiveEquivalence process first second := by
  constructor
  · intro kEquivalent
    have sameObjectToken :
        object.SameToken (adapter.endpoint first) (adapter.endpoint second) :=
      (bridge.KTrajectoryEquivalent_iff_sameToken_of_both_contracts
        invariant separates (adapter.endpoint first) (adapter.endpoint second)).1
        kEquivalent
    have sameOperationalToken :
        operationalTokenOf evidence first = operationalTokenOf evidence second :=
      (adapter.sameToken_iff_tokenEquality first second).1 sameObjectToken
    have sameCanonicalState :
        canonicalPredictiveState process first =
          canonicalPredictiveState process second :=
      (exactBridge first second).1 sameOperationalToken
    exact Quotient.exact sameCanonicalState
  · intro predictivelyEquivalent
    have sameCanonicalState :
        canonicalPredictiveState process first =
          canonicalPredictiveState process second :=
      Quotient.sound predictivelyEquivalent
    have sameOperationalToken :
        operationalTokenOf evidence first = operationalTokenOf evidence second :=
      (exactBridge first second).2 sameCanonicalState
    have sameObjectToken :
        object.SameToken (adapter.endpoint first) (adapter.endpoint second) :=
      (adapter.sameToken_iff_tokenEquality first second).2 sameOperationalToken
    exact
      (bridge.KTrajectoryEquivalent_iff_sameToken_of_both_contracts
        invariant separates (adapter.endpoint first) (adapter.endpoint second)).2
        sameObjectToken

/-! ## Constitutive-fiber boundary with its exact positive contract -/

/-- Equal parent realization fibers determine token identity only when this
faithfulness contract is supplied explicitly. -/
def ParentFiberTokenFaithful
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    {ParentState : Type uParent}
    (bridge : ConstitutiveBridge Index ChildState ParentState)
    (sameToken : BinaryRelation ParentState) : Prop :=
  ∀ first second,
    ParentConfigurationFiber bridge first =
        ParentConfigurationFiber bridge second →
      sameToken first second

theorem equal_parentFiber_implies_sameToken_of_faithful
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    {ParentState : Type uParent}
    {bridge : ConstitutiveBridge Index ChildState ParentState}
    {sameToken : BinaryRelation ParentState}
    (faithful : ParentFiberTokenFaithful bridge sameToken)
    {first second : ParentState}
    (sameFiber : ParentConfigurationFiber bridge first =
      ParentConfigurationFiber bridge second) :
    sameToken first second :=
  faithful first second sameFiber

/-- The duplicated-token countermodel refutes the faithfulness contract
itself, strengthening the earlier pointwise no-go result. -/
theorem duplicatedTokenBridge_not_parentFiberTokenFaithful
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    (admissible : JointConfiguration Index ChildState → Prop) :
    ¬ ParentFiberTokenFaithful (duplicatedTokenBridge admissible) (· = ·) := by
  intro faithful
  exact Bool.false_ne_true
    (faithful false true
      (duplicatedTokenBridge_has_equal_parent_fibers admissible))

end OCKIndividuationMSpaceComposition
