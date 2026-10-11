import OCKIndividuationMSpaceComposition.QualifiedObjectHierarchy
import OCKIndividuationMSpaceComposition.KAxisAndCurrentKBridge

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine
open OCMinimalObligationSpine.UnifiedEntityProjection
open OCMaturityCompletionCycle

universe
  uMechanism uIntervention uOutcome uProvenance uTime uAccess
  uMemberOccurrence uMemberExperiment uMemberOutcome
  uObjectOccurrence uInput uObjectExperiment uObjectOutcome

/-!
# A `CurrentK` bridge for atomic-or-composite qualified objects

`CurrentKObjectBridge` correctly targets the earlier composite-only
`DynamicQualifiedObject`.  `QualifiedObjectHierarchy` widens the object layer:
each generalized snapshot may be atomic or composite in its declared access
and intervention context.  This additive module supplies the matching explicit
representational bridge without changing either accepted API.

The bridge remains deliberately weaker than identity.  It records a state map,
exact `CurrentK` semantics, and step commutation.  K-trajectory equivalence is
only observational equivalence.  Either direction between that equivalence and
whole-object token identity requires a separately declared synchronization or
separation contract.
-/

/-! ## Conservative embedding of legacy composite dynamics -/

namespace GeneralizedDynamicQualifiedObject

/-- Embed an accepted composite-only changing object into the generalized
atomic-or-composite surface.  Every snapshot is explicitly tagged composite;
the whole-object dynamics, continuation evidence, and identity-test semantics
are unchanged. -/
def ofComposite
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {formedBy : Mechanism → Provenance → Prop}
    {continuesAt : Mechanism → Time → Prop}
    {robustAtScale : (Mechanism → Prop) → Prop}
    {Access : Type uAccess}
    (accessContext : AtomicAccessContext Mechanism Access)
    {MemberOccurrence : Type uMemberOccurrence}
    {MemberExperiment : Type uMemberExperiment}
    {MemberOutcome : Type uMemberOutcome}
    {memberEvidence : BinaryRelation MemberOccurrence}
    {memberLaw : MemberOccurrence → MemberExperiment → MemberOutcome}
    {ObjectOccurrence : Type uObjectOccurrence}
    {Input : Type uInput}
    {ObjectExperiment : Type uObjectExperiment}
    {ObjectOutcome : Type uObjectOutcome}
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome) :
    GeneralizedDynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale Access accessContext MemberOccurrence MemberExperiment
      MemberOutcome memberEvidence memberLaw ObjectOccurrence Input
      ObjectExperiment ObjectOutcome where
  seed := object.seed
  snapshot := fun occurrence =>
    GeneralizedStaticObjectCut.ofConstraintGeneratedObject accessContext
      (object.snapshot occurrence)
  openStep := object.openStep
  continuationEvidence := object.continuationEvidence
  continuation_grounded := object.continuation_grounded
  identityExperimentLaw := object.experimentLaw
  identityConverges := object.identityConverges

/-- The conservative composite embedding preserves open steps definitionally. -/
theorem ofComposite_openStep_iff
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {formedBy : Mechanism → Provenance → Prop}
    {continuesAt : Mechanism → Time → Prop}
    {robustAtScale : (Mechanism → Prop) → Prop}
    {Access : Type uAccess}
    (accessContext : AtomicAccessContext Mechanism Access)
    {MemberOccurrence : Type uMemberOccurrence}
    {MemberExperiment : Type uMemberExperiment}
    {MemberOutcome : Type uMemberOutcome}
    {memberEvidence : BinaryRelation MemberOccurrence}
    {memberLaw : MemberOccurrence → MemberExperiment → MemberOutcome}
    {ObjectOccurrence : Type uObjectOccurrence}
    {Input : Type uInput}
    {ObjectExperiment : Type uObjectExperiment}
    {ObjectOutcome : Type uObjectOutcome}
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome)
    (source : ObjectOccurrence)
    (input : Input)
    (target : ObjectOccurrence) :
    (ofComposite accessContext object).openStep source input target ↔
      object.openStep source input target :=
  Iff.rfl

/-- The conservative composite embedding preserves operational token identity
definitionally; it does not introduce a second token relation. -/
theorem ofComposite_sameToken_iff
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {formedBy : Mechanism → Provenance → Prop}
    {continuesAt : Mechanism → Time → Prop}
    {robustAtScale : (Mechanism → Prop) → Prop}
    {Access : Type uAccess}
    (accessContext : AtomicAccessContext Mechanism Access)
    {MemberOccurrence : Type uMemberOccurrence}
    {MemberExperiment : Type uMemberExperiment}
    {MemberOutcome : Type uMemberOutcome}
    {memberEvidence : BinaryRelation MemberOccurrence}
    {memberLaw : MemberOccurrence → MemberExperiment → MemberOutcome}
    {ObjectOccurrence : Type uObjectOccurrence}
    {Input : Type uInput}
    {ObjectExperiment : Type uObjectExperiment}
    {ObjectOutcome : Type uObjectOutcome}
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome)
    (first second : ObjectOccurrence) :
    (ofComposite accessContext object).SameToken first second ↔
      object.SameToken first second :=
  Iff.rfl

end GeneralizedDynamicQualifiedObject

/-! ## Generalized occurrence-to-K evidence -/

/-- Evidence that an exact `CurrentK` represents the occurrence dynamics of a
generalized atomic-or-composite object.  No injectivity, token invariance, or
identity completeness is built into this base bridge. -/
structure QualifiedCurrentKBridge
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
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
    (object : GeneralizedDynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale Access accessContext MemberOccurrence
      MemberExperiment MemberOutcome memberEvidence memberLaw ObjectOccurrence
      Input ObjectExperiment ObjectOutcome)
    (K : CurrentK) where
  stateOf : ObjectOccurrence → K.State
  exactK : HasExactDeclaredSemantics K
  step_commutes : ∀ {source input target},
    object.openStep source input target →
      K.stateTransition (stateOf source) = stateOf target

namespace QualifiedCurrentKBridge

variable
  {Mechanism : Type uMechanism}
  {Intervention : Type uIntervention}
  {Outcome : Type uOutcome}
  {model : ActiveConstraintModel Mechanism Intervention Outcome}
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

/-- Equality under every declared receiver at every represented future step.
This is observational equivalence, not operational token identity. -/
def KTrajectoryEquivalent
    (bridge : QualifiedCurrentKBridge object K)
    (first second : ObjectOccurrence) : Prop :=
  ∀ step receiver,
    K.receiverEffect
        (evolveState K.stateTransition step (bridge.stateOf first)) receiver =
      K.receiverEffect
        (evolveState K.stateTransition step (bridge.stateOf second)) receiver

/-- Optional synchronization: one operational token has one K-observational
trajectory under the chosen representation.  Changing objects need not satisfy
this contract. -/
def TokenObservationInvariant
    (bridge : QualifiedCurrentKBridge object K) : Prop :=
  ∀ ⦃first second⦄, object.SameToken first second →
    bridge.KTrajectoryEquivalent first second

/-- Optional observational completeness in the reverse direction. -/
def KSeparatesTokens
    (bridge : QualifiedCurrentKBridge object K) : Prop :=
  ∀ ⦃first second⦄, bridge.KTrajectoryEquivalent first second →
    object.SameToken first second

theorem sameToken_implies_KTrajectoryEquivalent_of_invariant
    (bridge : QualifiedCurrentKBridge object K)
    (invariant : bridge.TokenObservationInvariant)
    {first second : ObjectOccurrence}
    (sameToken : object.SameToken first second) :
    bridge.KTrajectoryEquivalent first second :=
  invariant sameToken

/-- Equivalence with token identity requires both independent optional
contracts. -/
theorem KTrajectoryEquivalent_iff_sameToken_of_both_contracts
    (bridge : QualifiedCurrentKBridge object K)
    (invariant : bridge.TokenObservationInvariant)
    (separates : bridge.KSeparatesTokens)
    (first second : ObjectOccurrence) :
    bridge.KTrajectoryEquivalent first second ↔
      object.SameToken first second :=
  ⟨fun equivalent => separates equivalent,
    fun sameToken => invariant sameToken⟩

/-- Occurrence-level carrier projection chosen by the explicit bridge. -/
def occurrenceProjection
    (bridge : QualifiedCurrentKBridge object K) :
    ObjectOccurrence → K.Carrier :=
  fun occurrence => K.encode (bridge.stateOf occurrence)

/-- Exact K semantics decodes each occurrence's receiver effect from the
chosen carrier projection. -/
theorem occurrenceProjection_decodes_receiverEffect
    (bridge : QualifiedCurrentKBridge object K)
    (occurrence : ObjectOccurrence)
    (receiver : K.Receiver) :
    K.decodeReceiverEffect (bridge.occurrenceProjection occurrence) receiver =
      K.receiverEffect (bridge.stateOf occurrence) receiver :=
  bridge.exactK.1 (bridge.stateOf occurrence) receiver

/-- A bridged generalized object step commutes with the encoded deterministic
K step. -/
theorem step_commutes_encode
    (bridge : QualifiedCurrentKBridge object K)
    {source : ObjectOccurrence}
    {input : Input}
    {target : ObjectOccurrence}
    (step : object.openStep source input target) :
    K.carrierTransition (K.encode (bridge.stateOf source)) =
      K.encode (bridge.stateOf target) := by
  calc
    K.carrierTransition (bridge.occurrenceProjection source) =
        K.encode (K.stateTransition (bridge.stateOf source)) :=
      (bridge.exactK.2 (bridge.stateOf source)).symm
    _ = bridge.occurrenceProjection target :=
      congrArg K.encode (bridge.step_commutes step)

/-! ## Conservative adapter from the legacy composite bridge -/

/-- Reuse an accepted composite-object bridge after the explicit conservative
embedding into the generalized object surface. -/
def ofCompositeBridge
    {legacyObject : DynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome}
    (accessContext : AtomicAccessContext Mechanism Access)
    (bridge : CurrentKObjectBridge legacyObject K) :
    QualifiedCurrentKBridge
      (GeneralizedDynamicQualifiedObject.ofComposite accessContext legacyObject)
      K where
  stateOf := bridge.stateOf
  exactK := bridge.exactK
  step_commutes := bridge.step_commutes

/-- Forget the generalized snapshot grade after restricting a bridge to an
object known to arise from the conservative composite embedding. -/
def toCompositeBridge
    {legacyObject : DynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome}
    (accessContext : AtomicAccessContext Mechanism Access)
    (bridge : QualifiedCurrentKBridge
      (GeneralizedDynamicQualifiedObject.ofComposite accessContext legacyObject)
      K) :
    CurrentKObjectBridge legacyObject K where
  stateOf := bridge.stateOf
  exactK := bridge.exactK
  step_commutes := bridge.step_commutes

/-- The adapter preserves the selected K state exactly. -/
theorem ofCompositeBridge_stateOf
    {legacyObject : DynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome}
    (accessContext : AtomicAccessContext Mechanism Access)
    (bridge : CurrentKObjectBridge legacyObject K)
    (occurrence : ObjectOccurrence) :
    (ofCompositeBridge accessContext bridge).stateOf occurrence =
      bridge.stateOf occurrence :=
  rfl

/-- The adapter preserves observational K-trajectory equivalence exactly. -/
theorem ofCompositeBridge_KTrajectoryEquivalent_iff
    {legacyObject : DynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome}
    (accessContext : AtomicAccessContext Mechanism Access)
    (bridge : CurrentKObjectBridge legacyObject K)
    (first second : ObjectOccurrence) :
    (ofCompositeBridge accessContext bridge).KTrajectoryEquivalent first second ↔
      bridge.KTrajectoryEquivalent first second :=
  Iff.rfl

/-- Token identity is the same before and after the composite embedding. -/
theorem ofCompositeBridge_sameToken_iff
    {legacyObject : DynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome}
    (accessContext : AtomicAccessContext Mechanism Access)
    (_bridge : CurrentKObjectBridge legacyObject K)
    (first second : ObjectOccurrence) :
    (GeneralizedDynamicQualifiedObject.ofComposite accessContext legacyObject).SameToken
        first second ↔
      legacyObject.SameToken first second :=
  Iff.rfl

/-- The optional same-token observational synchronization contract is also
preserved exactly by the adapter. -/
theorem ofCompositeBridge_tokenObservationInvariant_iff
    {legacyObject : DynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome}
    (accessContext : AtomicAccessContext Mechanism Access)
    (bridge : CurrentKObjectBridge legacyObject K) :
    (ofCompositeBridge accessContext bridge).TokenObservationInvariant ↔
      bridge.TokenObservationInvariant :=
  Iff.rfl

/-- The optional observational separation contract is preserved exactly by
the adapter. -/
theorem ofCompositeBridge_KSeparatesTokens_iff
    {legacyObject : DynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome}
    (accessContext : AtomicAccessContext Mechanism Access)
    (bridge : CurrentKObjectBridge legacyObject K) :
    (ofCompositeBridge accessContext bridge).KSeparatesTokens ↔
      bridge.KSeparatesTokens :=
  Iff.rfl

end QualifiedCurrentKBridge

/-! ## Conservative transport of the existing bridge boundaries -/

/-- Access evidence used only to place the accepted composite toy dynamics on
the generalized object surface.  It does not reclassify those snapshots as
atomic: `ofComposite` tags every one as composite. -/
def toyCompositeAdapterAccessContext : AtomicAccessContext ToyMechanism Unit where
  accesses := fun _ _ => True

def qualifiedBoolFlipObjectKBridge :
    QualifiedCurrentKBridge
      (GeneralizedDynamicQualifiedObject.ofComposite
        toyCompositeAdapterAccessContext boolFlipDynamicQualifiedObject)
      boolFlipExactCurrentK :=
  QualifiedCurrentKBridge.ofCompositeBridge toyCompositeAdapterAccessContext
    boolFlipObjectKBridge

/-- The accepted changing-token countermodel survives the generalized bridge:
same token still need not imply K-trajectory equivalence. -/
theorem sameToken_need_not_imply_qualified_KTrajectoryEquivalent :
    (GeneralizedDynamicQualifiedObject.ofComposite
        toyCompositeAdapterAccessContext boolFlipDynamicQualifiedObject).SameToken
        false true ∧
      ¬ qualifiedBoolFlipObjectKBridge.KTrajectoryEquivalent false true := by
  rcases sameToken_need_not_imply_KTrajectoryEquivalent with
    ⟨sameToken, notEquivalent⟩
  constructor
  · exact (GeneralizedDynamicQualifiedObject.ofComposite_sameToken_iff
      toyCompositeAdapterAccessContext boolFlipDynamicQualifiedObject
      false true).2 sameToken
  · intro equivalent
    exact notEquivalent
      ((QualifiedCurrentKBridge.ofCompositeBridge_KTrajectoryEquivalent_iff
        toyCompositeAdapterAccessContext boolFlipObjectKBridge false true).1
        equivalent)

/-- Exact representational semantics still does not manufacture a generalized
object bridge.  Any such bridge on this explicitly embedded composite object
would forget back to the already refuted legacy bridge. -/
theorem exactCurrentK_need_not_yield_QualifiedCurrentKBridge :
    HasExactDeclaredSemantics boolFlipExactCurrentK ∧
      ¬ Nonempty
        (QualifiedCurrentKBridge
          (GeneralizedDynamicQualifiedObject.ofComposite
            toyCompositeAdapterAccessContext boolDynamicQualifiedObject)
          boolFlipExactCurrentK) := by
  refine ⟨exactCurrentK_need_not_bridge_chosen_object.1, ?_⟩
  rintro ⟨bridge⟩
  exact exactCurrentK_need_not_bridge_chosen_object.2
    ⟨QualifiedCurrentKBridge.toCompositeBridge
      toyCompositeAdapterAccessContext bridge⟩

end OCKIndividuationMSpaceComposition
