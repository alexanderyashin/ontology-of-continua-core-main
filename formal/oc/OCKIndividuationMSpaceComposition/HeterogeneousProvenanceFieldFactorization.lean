import OCKIndividuationMSpaceComposition.ProvenanceFieldFactorization
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Finset.Card
import Mathlib.Data.Finset.Max
import Mathlib.Data.Finset.Powerset
import Mathlib.Data.Nat.Find
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.Linarith

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

universe uField uObject uValue uOutcome

/-!
# Heterogeneous minimal provenance-field factorisation

Real provenance records contain fields of different types.  This module
removes the Boolean-coordinate restriction from the earlier finite-field
theorem.  A selected signature is a dependent function whose coordinate at
field `f` has type `Option (Value f)`: selected fields contain their typed
value and unselected fields contain `none`.

The unconditional canonical factor is defined only on reachable signatures.
A total decoder on all signatures is separated and requires an explicit
inhabited outcome type.  This preserves the empty-object/unreachable-codomain
boundary established for task quotients.
-/

variable {Field : Type uField} {Object : Type uObject}
  {Value : Field → Type uValue} {Outcome : Type uOutcome}
  [DecidableEq Field]

/-- A dependent, typed signature of exactly the selected provenance fields. -/
def typedSelectedFieldSignature
    (selected : Finset Field)
    (fieldValue : (field : Field) → Object → Value field)
    (object : Object) : (field : Field) → Option (Value field) :=
  fun field => if field ∈ selected then some (fieldValue field object) else none

/-- Two occurrences agree on every selected field, without coercing
heterogeneous field values to a common scalar. -/
def SameOnTypedFields
    (selected : Finset Field)
    (fieldValue : (field : Field) → Object → Value field)
    (left right : Object) : Prop :=
  ∀ field, field ∈ selected → fieldValue field left = fieldValue field right

theorem typedSelectedFieldSignature_eq_iff_sameOn
    (selected : Finset Field)
    (fieldValue : (field : Field) → Object → Value field)
    (left right : Object) :
    typedSelectedFieldSignature selected fieldValue left =
        typedSelectedFieldSignature selected fieldValue right ↔
      SameOnTypedFields selected fieldValue left right := by
  constructor
  · intro signaturesEqual field selectedField
    have atField := congrFun signaturesEqual field
    simpa [typedSelectedFieldSignature, selectedField] using atField
  · intro same
    funext field
    by_cases selectedField : field ∈ selected
    · simp [typedSelectedFieldSignature, selectedField,
        same field selectedField]
    · simp [typedSelectedFieldSignature, selectedField]

/-- A successor/admissibility profile is constant on the selected typed-field
fibres. -/
def ProfileConstantOnTypedFields
    (selected : Finset Field)
    (fieldValue : (field : Field) → Object → Value field)
    (profile : Object → Outcome) : Prop :=
  ∀ left right, SameOnTypedFields selected fieldValue left right →
    profile left = profile right

/-- Unconditional exact factorisation on the actually reachable signature
range.  This remains meaningful when `Object` and the reachable range are
empty, even if `Outcome` is empty. -/
def ReachableTypedFieldProfileFactorExists
    (selected : Finset Field)
    (fieldValue : (field : Field) → Object → Value field)
    (profile : Object → Outcome) : Prop :=
  ∃ decode : Set.range (typedSelectedFieldSignature selected fieldValue) → Outcome,
    ∀ object,
      decode ⟨typedSelectedFieldSignature selected fieldValue object,
        ⟨object, rfl⟩⟩ = profile object

/-- Reachable factorisation exists exactly at typed-fibre constancy. -/
theorem reachable_typed_field_factor_exists_iff_constant
    (selected : Finset Field)
    (fieldValue : (field : Field) → Object → Value field)
    (profile : Object → Outcome) :
    ReachableTypedFieldProfileFactorExists selected fieldValue profile ↔
      ProfileConstantOnTypedFields selected fieldValue profile := by
  constructor
  · rintro ⟨decode, decodes⟩ left right same
    have signaturesEqual :=
      (typedSelectedFieldSignature_eq_iff_sameOn
        selected fieldValue left right).2 same
    have reachableEqual :
        (⟨typedSelectedFieldSignature selected fieldValue left,
            ⟨left, rfl⟩⟩ :
          Set.range (typedSelectedFieldSignature selected fieldValue)) =
        ⟨typedSelectedFieldSignature selected fieldValue right,
            ⟨right, rfl⟩⟩ :=
      Subtype.ext signaturesEqual
    rw [← decodes left, ← decodes right, reachableEqual]
  · intro constant
    classical
    let decode :
        Set.range (typedSelectedFieldSignature selected fieldValue) → Outcome :=
      fun signature => profile (Classical.choose signature.property)
    refine ⟨decode, ?_⟩
    intro object
    let witness : ∃ candidate,
        typedSelectedFieldSignature selected fieldValue candidate =
          typedSelectedFieldSignature selected fieldValue object := ⟨object, rfl⟩
    change profile (Classical.choose witness) = profile object
    apply constant
    apply (typedSelectedFieldSignature_eq_iff_sameOn
      selected fieldValue _ object).1
    exact Classical.choose_spec witness

/-- Any two exact decoders agree on every reachable typed signature. -/
theorem reachable_typed_field_factor_unique
    (selected : Finset Field)
    (fieldValue : (field : Field) → Object → Value field)
    (profile : Object → Outcome)
    (first second :
      Set.range (typedSelectedFieldSignature selected fieldValue) → Outcome)
    (firstExact : ∀ object,
      first ⟨typedSelectedFieldSignature selected fieldValue object,
        ⟨object, rfl⟩⟩ = profile object)
    (secondExact : ∀ object,
      second ⟨typedSelectedFieldSignature selected fieldValue object,
        ⟨object, rfl⟩⟩ = profile object) :
    first = second := by
  funext signature
  obtain ⟨object, objectSignature⟩ := signature.property
  have signatureEq :
      signature =
        ⟨typedSelectedFieldSignature selected fieldValue object,
          ⟨object, rfl⟩⟩ := by
    apply Subtype.ext
    exact objectSignature.symm
  rw [signatureEq, firstExact object, secondExact object]

/-- Totalisation over unreachable signatures is a separate contract. -/
def TotalTypedFieldProfileFactorExists
    (selected : Finset Field)
    (fieldValue : (field : Field) → Object → Value field)
    (profile : Object → Outcome) : Prop :=
  ∃ decode : ((field : Field) → Option (Value field)) → Outcome,
    ∀ object,
      decode (typedSelectedFieldSignature selected fieldValue object) =
        profile object

theorem total_typed_field_factor_implies_constant
    (selected : Finset Field)
    (fieldValue : (field : Field) → Object → Value field)
    (profile : Object → Outcome) :
    TotalTypedFieldProfileFactorExists selected fieldValue profile →
      ProfileConstantOnTypedFields selected fieldValue profile := by
  rintro ⟨decode, decodes⟩ left right same
  rw [← decodes left, ← decodes right,
    (typedSelectedFieldSignature_eq_iff_sameOn
      selected fieldValue left right).2 same]

/-- With an explicit default outcome, reachable factorisation extends to all
typed signatures.  No hidden totalisation is used. -/
theorem constant_typed_fields_gives_total_factor
    [Inhabited Outcome]
    (selected : Finset Field)
    (fieldValue : (field : Field) → Object → Value field)
    (profile : Object → Outcome)
    (constant : ProfileConstantOnTypedFields selected fieldValue profile) :
    TotalTypedFieldProfileFactorExists selected fieldValue profile := by
  classical
  let decode : ((field : Field) → Option (Value field)) → Outcome :=
    fun signature =>
      if witness : ∃ object,
          typedSelectedFieldSignature selected fieldValue object = signature then
        profile (Classical.choose witness)
      else default
  refine ⟨decode, ?_⟩
  intro object
  dsimp [decode]
  have witness : ∃ candidate,
      typedSelectedFieldSignature selected fieldValue candidate =
        typedSelectedFieldSignature selected fieldValue object := ⟨object, rfl⟩
  rw [dif_pos witness]
  apply constant
  apply (typedSelectedFieldSignature_eq_iff_sameOn
    selected fieldValue _ object).1
  exact Classical.choose_spec witness

/-- Inclusion-minimality for heterogeneous provenance fields. -/
def IsInclusionMinimalTypedProfileFieldSet
    (selected : Finset Field)
    (fieldValue : (field : Field) → Object → Value field)
    (profile : Object → Outcome) : Prop :=
  ProfileConstantOnTypedFields selected fieldValue profile ∧
    ∀ field, field ∈ selected →
      ¬ ProfileConstantOnTypedFields (selected.erase field) fieldValue profile

/-- Every retained typed field in a minimal sufficient basis has a concrete
omission witness with equal remaining signature and unequal future profile. -/
theorem minimal_typed_profile_field_has_omission_witness
    (selected : Finset Field)
    (fieldValue : (field : Field) → Object → Value field)
    (profile : Object → Outcome)
    (minimal :
      IsInclusionMinimalTypedProfileFieldSet selected fieldValue profile)
    {field : Field} (fieldSelected : field ∈ selected) :
    ∃ left right : Object,
      SameOnTypedFields (selected.erase field) fieldValue left right ∧
        profile left ≠ profile right := by
  have notConstant := minimal.2 field fieldSelected
  by_contra noWitness
  apply notConstant
  intro left right same
  by_contra profileDifferent
  exact noWitness ⟨left, right, same, profileDifferent⟩

/-- Every finite sufficient field catalogue contains an inclusion-minimal
sufficient typed basis.  The proof minimizes cardinality and then derives
inclusion-minimality. -/
theorem finite_sufficient_catalogue_has_minimal_typed_basis
    (catalogue : Finset Field)
    (fieldValue : (field : Field) → Object → Value field)
    (profile : Object → Outcome)
    (catalogueSufficient :
      ProfileConstantOnTypedFields catalogue fieldValue profile) :
    ∃ basis : Finset Field,
      basis ⊆ catalogue ∧
        IsInclusionMinimalTypedProfileFieldSet basis fieldValue profile := by
  classical
  let hasBasisCard : Nat → Prop := fun size =>
    ∃ candidate : Finset Field,
      candidate ⊆ catalogue ∧
        ProfileConstantOnTypedFields candidate fieldValue profile ∧
        candidate.card = size
  have existsCard : ∃ size, hasBasisCard size :=
    ⟨catalogue.card, catalogue, Finset.Subset.rfl,
      catalogueSufficient, rfl⟩
  let minimumCard := Nat.find existsCard
  obtain ⟨basis, basisSubset, basisSufficient, basisCard⟩ :=
    Nat.find_spec existsCard
  refine ⟨basis, basisSubset, basisSufficient, ?_⟩
  intro field fieldInBasis erasedSufficient
  have erasedSubset : basis.erase field ⊆ catalogue :=
    Finset.Subset.trans (Finset.erase_subset field basis) basisSubset
  have erasedCardSmaller : (basis.erase field).card < minimumCard := by
    change (basis.erase field).card < Nat.find existsCard
    rw [← basisCard]
    exact Finset.card_erase_lt_of_mem fieldInBasis
  have forbidden := Nat.find_min existsCard erasedCardSmaller
  exact forbidden ⟨basis.erase field, erasedSubset, erasedSufficient, rfl⟩

/-! ## Non-uniqueness boundary -/

def duplicateBoolProvenanceFieldValue
    (_field : Bool) (object : Bool) : Bool := object

def boolSuccessorProfile (object : Bool) : Bool := object

theorem false_field_is_minimal_duplicate_basis :
    IsInclusionMinimalTypedProfileFieldSet
      ({false} : Finset Bool)
      (Value := fun _ : Bool => Bool)
      duplicateBoolProvenanceFieldValue boolSuccessorProfile := by
  constructor
  · intro left right same
    exact same false (by simp)
  · intro field fieldIn
    have fieldFalse : field = false := by simpa using fieldIn
    subst field
    intro emptyConstant
    have collision := emptyConstant false true (by
      intro candidate candidateIn
      simp at candidateIn)
    simp [boolSuccessorProfile] at collision

theorem true_field_is_minimal_duplicate_basis :
    IsInclusionMinimalTypedProfileFieldSet
      ({true} : Finset Bool)
      (Value := fun _ : Bool => Bool)
      duplicateBoolProvenanceFieldValue boolSuccessorProfile := by
  constructor
  · intro left right same
    exact same true (by simp)
  · intro field fieldIn
    have fieldTrue : field = true := by simpa using fieldIn
    subst field
    intro emptyConstant
    have collision := emptyConstant false true (by
      intro candidate candidateIn
      simp at candidateIn)
    simp [boolSuccessorProfile] at collision

/-- Minimal sufficient provenance bases need not be unique: two duplicated
typed fields yield distinct singleton bases for the same future profile. -/
theorem minimal_typed_provenance_basis_not_unique :
    IsInclusionMinimalTypedProfileFieldSet
        ({false} : Finset Bool)
        (Value := fun _ : Bool => Bool)
        duplicateBoolProvenanceFieldValue boolSuccessorProfile ∧
      IsInclusionMinimalTypedProfileFieldSet
        ({true} : Finset Bool)
        (Value := fun _ : Bool => Bool)
        duplicateBoolProvenanceFieldValue boolSuccessorProfile ∧
      ({false} : Finset Bool) ≠ {true} := by
  exact ⟨false_field_is_minimal_duplicate_basis,
    true_field_is_minimal_duplicate_basis, by simp⟩

/-! ## Cost-indexed selection among non-unique sufficient bases -/

def typedFieldSetCost
    (fieldCost : Field → ℚ) (selected : Finset Field) : ℚ :=
  ∑ field ∈ selected, fieldCost field

/-- A finite sufficient catalogue always has a cost-minimizing sufficient
basis for any explicitly registered scalar field-cost function. -/
theorem finite_catalogue_has_cost_optimal_sufficient_basis
    (catalogue : Finset Field)
    (fieldValue : (field : Field) → Object → Value field)
    (profile : Object → Outcome)
    (fieldCost : Field → ℚ)
    (catalogueSufficient :
      ProfileConstantOnTypedFields catalogue fieldValue profile) :
    ∃ basis : Finset Field,
      basis ⊆ catalogue ∧
        ProfileConstantOnTypedFields basis fieldValue profile ∧
        ∀ candidate : Finset Field,
          candidate ⊆ catalogue →
          ProfileConstantOnTypedFields candidate fieldValue profile →
          typedFieldSetCost fieldCost basis ≤
            typedFieldSetCost fieldCost candidate := by
  classical
  let candidates := catalogue.powerset.filter
    (fun candidate =>
      ProfileConstantOnTypedFields candidate fieldValue profile)
  have catalogueCandidate : catalogue ∈ candidates := by
    simp [candidates, catalogueSufficient]
  let costs := candidates.image (typedFieldSetCost fieldCost)
  have costsNonempty : costs.Nonempty := by
    refine ⟨typedFieldSetCost fieldCost catalogue, ?_⟩
    exact Finset.mem_image.mpr ⟨catalogue, catalogueCandidate, rfl⟩
  have minimumMem := costs.min'_mem costsNonempty
  obtain ⟨basis, basisCandidate, basisCost⟩ :=
    Finset.mem_image.mp minimumMem
  have basisProperties := Finset.mem_filter.mp basisCandidate
  refine ⟨basis, Finset.mem_powerset.mp basisProperties.1,
    basisProperties.2, ?_⟩
  intro candidate candidateSubset candidateSufficient
  have candidateMember : candidate ∈ candidates := by
    exact Finset.mem_filter.mpr
      ⟨Finset.mem_powerset.mpr candidateSubset, candidateSufficient⟩
  have candidateCostMember :
      typedFieldSetCost fieldCost candidate ∈ costs :=
    Finset.mem_image.mpr ⟨candidate, candidateMember, rfl⟩
  have minimumLe := costs.min'_le _ candidateCostMember
  rw [← basisCost] at minimumLe
  exact minimumLe

/-- If every registered field has strictly positive cost, every cost-optimal
sufficient basis is inclusion-minimal. -/
theorem positive_cost_optimal_basis_is_inclusion_minimal
    (catalogue basis : Finset Field)
    (fieldValue : (field : Field) → Object → Value field)
    (profile : Object → Outcome)
    (fieldCost : Field → ℚ)
    (basisSubset : basis ⊆ catalogue)
    (basisSufficient :
      ProfileConstantOnTypedFields basis fieldValue profile)
    (strictlyPositive : ∀ field, 0 < fieldCost field)
    (optimal : ∀ candidate : Finset Field,
      candidate ⊆ catalogue →
      ProfileConstantOnTypedFields candidate fieldValue profile →
      typedFieldSetCost fieldCost basis ≤
        typedFieldSetCost fieldCost candidate) :
    IsInclusionMinimalTypedProfileFieldSet basis fieldValue profile := by
  refine ⟨basisSufficient, ?_⟩
  intro field fieldInBasis erasedSufficient
  have erasedSubset : basis.erase field ⊆ catalogue :=
    Finset.Subset.trans (Finset.erase_subset field basis) basisSubset
  have optimalErase := optimal (basis.erase field) erasedSubset erasedSufficient
  have costDecomposition :
      typedFieldSetCost fieldCost (basis.erase field) + fieldCost field =
        typedFieldSetCost fieldCost basis := by
    simp [typedFieldSetCost, Finset.sum_erase_add _ _ fieldInBasis]
  linarith [strictlyPositive field]

end OCKIndividuationMSpaceComposition
