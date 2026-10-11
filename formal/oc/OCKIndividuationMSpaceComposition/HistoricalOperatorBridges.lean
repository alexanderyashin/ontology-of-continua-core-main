import OCKIndividuationMSpaceComposition.OperatorTransport
import OCKIndividuationMSpaceComposition.KAxisAndCurrentKBridge

namespace OCKIndividuationMSpaceComposition

universe uA uB uState uSource uTarget uSource' uTarget'

/-!
# Typed bridges for the historical operator vocabulary

The historical glyphs are source terms, not operator identities.  This module
adjudicates the bounded retained register with dependent evidence rows and
provides exact operational bridges for the three previously overloaded
transition terms: `Psi` (resolution refinement), `X` (operational continuation
exhaustion), and `Phi` (typed transport between operator doctrines).

Ontic readings remain separate propositions: three unconditional strong forms
are refuted below, while the remaining ontic rows are hypotheses or missing.
In particular, strict observational refinement need not add a physical
coordinate, an empty continuation relation need not mean physical
destruction, and an exact operator transport need not mean that an ontology
changed.  Totality below is only totality over the twelve-constructor source
enum.  It is not semantic, historical, or scientific completeness of an
operator catalogue.
-/

/-! ## Bounded source-term register and evidence-bearing adjudication -/

inductive HistoricalOperatorGlyph
  | E
  | Eint
  | F
  | G
  | H
  | Psi
  | Q
  | R
  | S
  | U
  | X
  | Phi
  deriving DecidableEq, Repr

inductive HistoricalOperatorReading
  | operational
  | ontic
  deriving DecidableEq, Repr

/-- Each constructor names an exact Lean role family defined in this module.
It is a type placement, not evidence that the historical glyph has that
meaning in a scientific domain. -/
inductive HistoricalTypedRolePlacement
  | evolution
  | interaction
  | axisEvolution
  | potentialEvolution
  | thresholdEvolution
  | flowEvolution
  | boundaryEvolution
  | structureReconfiguration
  | continuumnessEvolution
  | profileRefinement
  | continuationExhaustion
  | exactRelTransport
  | unresolved
  deriving DecidableEq, Repr

/-- Dependent evidence state for an optional proposition.  `proved` carries
`P`, `refuted` carries `¬ P`, `hypothesis` carries neither, and `missing`
states that no proposition has yet been typed. -/
inductive HistoricalAdjudicationEvidence : Option Prop → Type
  | proved {claim : Prop} : claim →
      HistoricalAdjudicationEvidence (some claim)
  | refuted {claim : Prop} : (¬ claim) →
      HistoricalAdjudicationEvidence (some claim)
  | hypothesis {claim : Prop} :
      HistoricalAdjudicationEvidence (some claim)
  | missing : HistoricalAdjudicationEvidence none

/-- One evidence-bearing operational or ontic adjudication row. -/
structure HistoricalAdjudicationRow where
  glyph : HistoricalOperatorGlyph
  reading : HistoricalOperatorReading
  role : HistoricalTypedRolePlacement
  claim : Option Prop
  evidence : HistoricalAdjudicationEvidence claim

/-! ## Current typed placements for the non-exact glyphs -/

abbrev TypedEvolution (State : Type uState) := RelOperator State State

abbrev TypedInteraction (Left : Type uA) (Right : Type uB) :=
  RelOperator (Left × Right) (Left × Right)

abbrev TypedAxisEvolution (Axis : Type uA) := RelOperator Axis Axis
abbrev TypedPotentialEvolution (Potential : Type uA) :=
  RelOperator Potential Potential
abbrev TypedThresholdEvolution (Threshold : Type uA) :=
  RelOperator Threshold Threshold
abbrev TypedFlowEvolution (Flow : Type uA) := RelOperator Flow Flow
abbrev TypedBoundaryEvolution (Boundary : Type uA) :=
  RelOperator Boundary Boundary
abbrev TypedStructureReconfiguration (Structure : Type uA) :=
  RelOperator Structure Structure
abbrev TypedContinuumnessEvolution (Continuumness : Type uA) :=
  RelOperator Continuumness Continuumness

/-!
These aliases supply typed candidate roles only.  They do not equate the
historical terms with one another, select a scientific law, recover weights,
or resolve the `F`/`Q`/`S` cross-version collisions.
-/

/-! ## `Psi`: strict operational refinement without ontic coordinate birth -/

/-- The exact operational reading of `Psi`: one declared profile retains all
old distinctions and adds at least one new distinction extensionally. -/
structure TypedPsiRefinement (State : Type uState) where
  coarse : DistinctionProfile State
  fine : DistinctionProfile State
  preserves : AtLeastAsDiscriminating fine coarse
  strict : coarse ≠ fine

def noBoolDistinctions : DistinctionProfile Bool := fun _ _ => False
def boolInequalityDistinctions : DistinctionProfile Bool := fun left right =>
  left ≠ right

def strictBoolPsiRefinement : TypedPsiRefinement Bool where
  coarse := noBoolDistinctions
  fine := boolInequalityDistinctions
  preserves := by
    intro left right distinguished
    exact False.elim distinguished
  strict := by
    intro sameProfile
    have atFalseTrue := congrFun (congrFun sameProfile false) true
    simp [noBoolDistinctions, boolInequalityDistinctions] at atFalseTrue

/-- A proposed independent-coordinate interpretation is explicit and stronger
than profile refinement. -/
def AddsIndependentCoordinate
    {Fine : Type uA}
    {Coarse : Type uB}
    (forget : Fine → Coarse) : Prop :=
  ¬ Function.Injective forget

/-- Strict profile refinement can occur on the same carrier with an injective
identity map.  Therefore operational `Psi` does not entail physical mode or
dimension birth. -/
theorem operationalPsi_does_not_force_independentCoordinate :
    Nonempty (TypedPsiRefinement Bool) ∧
      ¬ AddsIndependentCoordinate (id : Bool → Bool) := by
  constructor
  · exact ⟨strictBoolPsiRefinement⟩
  · intro identityNotInjective
    exact identityNotInjective (by
      intro first second equal
      exact equal)

/-! ## `X`: exact operational exhaustion without physical destruction -/

def OperationalContinuationExhausted
    {State : Type uState}
    (step : RelOperator State State)
    (source : State) : Prop :=
  ∀ target, ¬ step source target

/-- The powerset bridge makes operational `X` exact: exhaustion means that no
target belongs to the relation-derived successor predicate. -/
theorem operationalX_iff_no_successorMembership
    {State : Type uState}
    (step : RelOperator State State)
    (source : State) :
    OperationalContinuationExhausted step source ↔
      ∀ target, target ∉ relationToPowersetStep step source := by
  rfl

/-- A continuation relation may be empty while an independently supplied
physical-destruction predicate is false. -/
theorem operationalX_does_not_imply_onticDestruction :
    ∃ step : RelOperator Unit Unit,
      OperationalContinuationExhausted step () ∧
        ¬ (False : Prop) := by
  exact ⟨fun _ _ => False, by
    intro target edge
    exact edge, by
      intro impossible
      exact impossible⟩

/-! ## `Phi`: exact typed transport without automatic ontology evolution -/

abbrev TypedPhiTransform
    {Source : Type uSource}
    {Target : Type uTarget}
    {Source' : Type uSource'}
    {Target' : Type uTarget'}
    (operator : RelOperator Source Target)
    (operator' : RelOperator Source' Target') :=
  ExactRelTransport operator operator'

def identityTypedPhiTransform
    {Source : Type uSource}
    {Target : Type uTarget}
    (operator : RelOperator Source Target) :
    TypedPhiTransform operator operator :=
  ExactRelTransport.identity operator

def composeTypedPhiTransform
    {A : Type uA}
    {B : Type uB}
    {C : Type uSource}
    {D : Type uTarget}
    {E : Type uSource'}
    {F : Type uTarget'}
    {first : RelOperator A B}
    {second : RelOperator C D}
    {third : RelOperator E F}
    (later : TypedPhiTransform second third)
    (earlier : TypedPhiTransform first second) :
    TypedPhiTransform first third :=
  ExactRelTransport.comp later earlier

/-- Even an exact identity `Phi` transport coexists with a false independently
declared ontic-change claim.  Ontology evolution is therefore not a theorem of
operator transport alone. -/
theorem operationalPhi_does_not_entail_onticChange
    {Source : Type uSource}
    {Target : Type uTarget}
    (operator : RelOperator Source Target)
    (onticChange : Prop)
    (notChanged : ¬ onticChange) :
    Nonempty (TypedPhiTransform operator operator) ∧ ¬ onticChange :=
  ⟨⟨identityTypedPhiTransform operator⟩, notChanged⟩

/-! ## Typed role families and evidence-bearing crosswalk -/

/-- Exact Lean type family denoted by each role-placement constructor.  The
sigma packages quantify over a carrier without selecting a historical domain
carrier. -/
def HistoricalTypedRolePlacement.WitnessType :
    HistoricalTypedRolePlacement → Type 1
  | .evolution => Σ State : Type, TypedEvolution State
  | .interaction =>
      Σ Left : Type, Σ Right : Type, TypedInteraction Left Right
  | .axisEvolution => Σ Axis : Type, TypedAxisEvolution Axis
  | .potentialEvolution =>
      Σ Potential : Type, TypedPotentialEvolution Potential
  | .thresholdEvolution =>
      Σ Threshold : Type, TypedThresholdEvolution Threshold
  | .flowEvolution => Σ Flow : Type, TypedFlowEvolution Flow
  | .boundaryEvolution =>
      Σ Boundary : Type, TypedBoundaryEvolution Boundary
  | .structureReconfiguration =>
      Σ Structure : Type, TypedStructureReconfiguration Structure
  | .continuumnessEvolution =>
      Σ Continuumness : Type, TypedContinuumnessEvolution Continuumness
  | .profileRefinement => Σ State : Type, TypedPsiRefinement State
  | .continuationExhaustion =>
      Σ State : Type,
        Σ step : RelOperator State State,
          { source : State // OperationalContinuationExhausted step source }
  | .exactRelTransport =>
      Σ Source : Type,
        Σ Target : Type,
          Σ Source' : Type,
            Σ Target' : Type,
              Σ operator : RelOperator Source Target,
                Σ operator' : RelOperator Source' Target',
                  TypedPhiTransform operator operator'
  | .unresolved => PUnit

/-- Evidence contract required before a proposed historical source term may be
identified with one typed role family.  Hypothesis rows below intentionally do
not carry such a witness. -/
structure HistoricalRoleAttribution
    (glyph : HistoricalOperatorGlyph)
    (reading : HistoricalOperatorReading)
    (role : HistoricalTypedRolePlacement) where
  sourceBindingDigest : String
  sourceBinding_nonempty : sourceBindingDigest ≠ ""
  interpretationRuleId : String
  interpretationRule_nonempty : interpretationRuleId ≠ ""
  typedWitness : Nonempty role.WitnessType

def PsiOperationalClaim : Prop := Nonempty (TypedPsiRefinement Bool)

def PsiStrongCoordinateBirthClaim : Prop :=
  ∀ refinement : TypedPsiRefinement Bool,
    AddsIndependentCoordinate (id : Bool → Bool)

theorem psiOperationalClaim_proved : PsiOperationalClaim :=
  ⟨strictBoolPsiRefinement⟩

theorem psiStrongCoordinateBirthClaim_refuted :
    ¬ PsiStrongCoordinateBirthClaim := by
  intro strongClaim
  have coordinateBirth := strongClaim strictBoolPsiRefinement
  exact operationalPsi_does_not_force_independentCoordinate.2 coordinateBirth

def XOperationalClaim : Prop :=
  ∀ (State : Type) (step : RelOperator State State) (source : State),
    OperationalContinuationExhausted step source ↔
      ∀ target, target ∉ relationToPowersetStep step source

def XStrongOnticDestructionClaim : Prop :=
  ∀ (State : Type) (step : RelOperator State State) (source : State)
    (onticDestruction : Prop),
    OperationalContinuationExhausted step source → onticDestruction

theorem xOperationalClaim_proved : XOperationalClaim := by
  intro State step source
  exact operationalX_iff_no_successorMembership step source

theorem xStrongOnticDestructionClaim_refuted :
    ¬ XStrongOnticDestructionClaim := by
  intro strongClaim
  let emptyStep : RelOperator Unit Unit := fun _ _ => False
  have exhausted : OperationalContinuationExhausted emptyStep () := by
    intro target edge
    exact edge
  exact strongClaim Unit emptyStep () False exhausted

def PhiOperationalClaim : Prop :=
  ∀ (Source Target : Type) (operator : RelOperator Source Target),
    Nonempty (TypedPhiTransform operator operator)

def PhiStrongOnticChangeClaim : Prop :=
  ∀ (Source Target : Type) (operator : RelOperator Source Target)
    (onticChange : Prop),
    Nonempty (TypedPhiTransform operator operator) → onticChange

theorem phiOperationalClaim_proved : PhiOperationalClaim := by
  intro Source Target operator
  exact ⟨identityTypedPhiTransform operator⟩

theorem phiStrongOnticChangeClaim_refuted :
    ¬ PhiStrongOnticChangeClaim := by
  intro strongClaim
  let emptyOperator : RelOperator Unit Unit := fun _ _ => False
  exact strongClaim Unit Unit emptyOperator False
    ⟨identityTypedPhiTransform emptyOperator⟩

/-- Operational rows for the bounded twelve-constructor source register.
Only `Psi`, `X`, and `Phi` carry proofs; other rows are explicitly hypotheses
or lack a typed proposition. -/
def historicalOperationalAdjudication :
    HistoricalOperatorGlyph → HistoricalAdjudicationRow
  | .E =>
      ⟨.E, .operational, .evolution,
        some (Nonempty (HistoricalRoleAttribution .E .operational .evolution)),
        .hypothesis⟩
  | .Eint =>
      ⟨.Eint, .operational, .interaction,
        some (Nonempty (HistoricalRoleAttribution .Eint .operational .interaction)),
        .hypothesis⟩
  | .F => ⟨.F, .operational, .unresolved, none, .missing⟩
  | .G =>
      ⟨.G, .operational, .potentialEvolution,
        some (Nonempty (HistoricalRoleAttribution .G .operational .potentialEvolution)),
        .hypothesis⟩
  | .H =>
      ⟨.H, .operational, .thresholdEvolution,
        some (Nonempty (HistoricalRoleAttribution .H .operational .thresholdEvolution)),
        .hypothesis⟩
  | .Psi =>
      ⟨.Psi, .operational, .profileRefinement,
        some PsiOperationalClaim, .proved psiOperationalClaim_proved⟩
  | .Q => ⟨.Q, .operational, .unresolved, none, .missing⟩
  | .R =>
      ⟨.R, .operational, .boundaryEvolution,
        some (Nonempty (HistoricalRoleAttribution .R .operational .boundaryEvolution)),
        .hypothesis⟩
  | .S =>
      ⟨.S, .operational, .structureReconfiguration,
        some (Nonempty (HistoricalRoleAttribution .S .operational
          .structureReconfiguration)), .hypothesis⟩
  | .U =>
      ⟨.U, .operational, .continuumnessEvolution,
        some (Nonempty (HistoricalRoleAttribution .U .operational
          .continuumnessEvolution)), .hypothesis⟩
  | .X =>
      ⟨.X, .operational, .continuationExhaustion,
        some XOperationalClaim, .proved xOperationalClaim_proved⟩
  | .Phi =>
      ⟨.Phi, .operational, .exactRelTransport,
        some PhiOperationalClaim, .proved phiOperationalClaim_proved⟩

/-- Ontic rows remain open except for explicit refutations of the three strong
claims paired with the proved operational bridges. -/
def historicalOnticAdjudication :
    HistoricalOperatorGlyph → HistoricalAdjudicationRow
  | .E => ⟨.E, .ontic, .unresolved, none, .missing⟩
  | .Eint =>
      ⟨.Eint, .ontic, .interaction,
        some (Nonempty (HistoricalRoleAttribution .Eint .ontic .interaction)),
        .hypothesis⟩
  | .F => ⟨.F, .ontic, .unresolved, none, .missing⟩
  | .G => ⟨.G, .ontic, .unresolved, none, .missing⟩
  | .H => ⟨.H, .ontic, .unresolved, none, .missing⟩
  | .Psi =>
      ⟨.Psi, .ontic, .profileRefinement,
        some PsiStrongCoordinateBirthClaim,
        .refuted psiStrongCoordinateBirthClaim_refuted⟩
  | .Q => ⟨.Q, .ontic, .unresolved, none, .missing⟩
  | .R =>
      ⟨.R, .ontic, .boundaryEvolution,
        some (Nonempty (HistoricalRoleAttribution .R .ontic .boundaryEvolution)),
        .hypothesis⟩
  | .S =>
      ⟨.S, .ontic, .structureReconfiguration,
        some (Nonempty (HistoricalRoleAttribution .S .ontic
          .structureReconfiguration)), .hypothesis⟩
  | .U =>
      ⟨.U, .ontic, .continuumnessEvolution,
        some (Nonempty (HistoricalRoleAttribution .U .ontic
          .continuumnessEvolution)), .hypothesis⟩
  | .X =>
      ⟨.X, .ontic, .continuationExhaustion,
        some XStrongOnticDestructionClaim,
        .refuted xStrongOnticDestructionClaim_refuted⟩
  | .Phi =>
      ⟨.Phi, .ontic, .exactRelTransport,
        some PhiStrongOnticChangeClaim,
        .refuted phiStrongOnticChangeClaim_refuted⟩

theorem historicalOperationalAdjudication_is_total_on_register
    (glyph : HistoricalOperatorGlyph) :
    (historicalOperationalAdjudication glyph).glyph = glyph := by
  cases glyph <;> rfl

theorem historicalOnticAdjudication_is_total_on_register
    (glyph : HistoricalOperatorGlyph) :
    (historicalOnticAdjudication glyph).glyph = glyph := by
  cases glyph <;> rfl

/-! ## Catalogue-wide no-go boundaries -/

def AllTypedOperatorRolesInterchangeable : Prop :=
  ∀ first second : TypedOperatorRole.{0}, first.Compatible second

/-- A finite list of untyped glyphs cannot erase incompatible source/target
roles. -/
theorem historicalGlyphs_cannot_erase_typedRoles :
    ¬ AllTypedOperatorRolesInterchangeable := by
  intro interchangeable
  exact reversed_roles_are_incompatible
    (interchangeable inhabitedToEmptyRole emptyToInhabitedRole)

/-- Relational support also cannot make the catalogue quantitatively complete:
different weights can inhabit the same typed support operator. -/
theorem historicalGlyphSupport_is_not_quantitativelyFaithful :
    ¬ Function.Injective (@weightedSupport Unit Bool) :=
  quantitativeSupport_not_faithful

end OCKIndividuationMSpaceComposition
