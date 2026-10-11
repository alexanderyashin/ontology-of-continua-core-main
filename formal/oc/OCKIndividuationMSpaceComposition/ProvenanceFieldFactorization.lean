import Mathlib.Data.Finset.Basic
import Mathlib.Data.Bool.Basic

namespace OCKIndividuationMSpaceComposition

/-!
# Minimal provenance-field factorisation

`ProvenanceRevisionProfile` proves the abstract fibre-constancy boundary for
presentation-only decoding.  This module makes the boundary operational for a
finite declared field catalogue: a field subset is sufficient exactly when
future admissibility is constant on its observed fibres.  It also proves the
necessity witness for every field in an inclusion-minimal sufficient subset.

The result is deliberately agnostic about which fields a domain uses.  A
domain adapter must provide the field map and the successor/admissibility
profile; the theorem then supplies the decoder and a falsifier for omitted
fields.
-/

variable {Field Object : Type*} [DecidableEq Field]

/-- Equality of the selected provenance coordinates. -/
def SameOnFields
    (selected : Finset Field)
    (fieldValue : Field → Object → Bool)
    (left right : Object) : Prop :=
  ∀ field, field ∈ selected → fieldValue field left = fieldValue field right

/-- The future/revision profile depends only on a selected field subset. -/
def ProfileConstantOnFields
    (selected : Finset Field)
    (fieldValue : Field → Object → Bool)
    (profile : Object → Bool) : Prop :=
  ∀ left right, SameOnFields selected fieldValue left right →
    profile left = profile right

/-- A decoder sees only the selected field vector. -/
def FieldProfileDecoderExists
    (selected : Finset Field)
    (fieldValue : Field → Object → Bool)
    (profile : Object → Bool) : Prop :=
  ∃ decode : (Field → Bool) → Bool, ∀ object,
    decode (fun field => if field ∈ selected then fieldValue field object else false) =
      profile object

theorem field_profile_decoder_exists_iff_constant_on_fields
    (selected : Finset Field)
    (fieldValue : Field → Object → Bool)
    (profile : Object → Bool) :
    FieldProfileDecoderExists selected fieldValue profile ↔
      ProfileConstantOnFields selected fieldValue profile := by
  constructor
  · rintro ⟨decode, decodes⟩ left right same
    rw [← decodes left, ← decodes right]
    congr 1
    funext field
    by_cases selectedField : field ∈ selected
    · simpa [selectedField] using same field selectedField
    · simp [selectedField]
  · intro constant
    classical
    let decode : (Field → Bool) → Bool := fun signature =>
      if witness : ∃ object,
          (fun field => if field ∈ selected then fieldValue field object else false) =
            signature then
        profile witness.choose
      else false
    refine ⟨decode, ?_⟩
    intro object
    dsimp [decode]
    have witness : ∃ candidate,
        (fun field => if field ∈ selected then fieldValue field candidate else false) =
          (fun field => if field ∈ selected then fieldValue field object else false) :=
      ⟨object, rfl⟩
    rw [dif_pos witness]
    apply constant
    intro field selectedField
    have equality := congrFun witness.choose_spec field
    simpa [selectedField] using equality

/-- Inclusion-minimality of a sufficient provenance field set. -/
def IsInclusionMinimalProfileFieldSet
    (selected : Finset Field)
    (fieldValue : Field → Object → Bool)
    (profile : Object → Bool) : Prop :=
  ProfileConstantOnFields selected fieldValue profile ∧
    ∀ field, field ∈ selected →
      ¬ ProfileConstantOnFields (selected.erase field) fieldValue profile

/-- Every retained field in an inclusion-minimal basis has a concrete
omission witness: removing it creates two objects with the same remaining
fields but different future/revision profiles. -/
theorem minimal_profile_field_has_omission_witness
    (selected : Finset Field)
    (fieldValue : Field → Object → Bool)
    (profile : Object → Bool)
    (minimal : IsInclusionMinimalProfileFieldSet selected fieldValue profile)
    {field : Field} (field_selected : field ∈ selected) :
    ∃ left right : Object,
      SameOnFields (selected.erase field) fieldValue left right ∧
        profile left ≠ profile right := by
  have not_constant := minimal.2 field field_selected
  by_contra no_witness
  apply not_constant
  intro left right same
  by_contra profile_diff
  apply no_witness
  exact ⟨left, right, same, profile_diff⟩

/-- A decoder built from a sufficient field set can be chosen to ignore every
unselected coordinate. -/
theorem sufficient_field_decoder_can_be_selected_coordinate_only
    (selected : Finset Field)
    (fieldValue : Field → Object → Bool)
    (profile : Object → Bool)
    (constant : ProfileConstantOnFields selected fieldValue profile) :
    ∃ decode : (Field → Bool) → Bool, ∀ object,
      decode (fun field => if field ∈ selected then fieldValue field object else false) =
        profile object := by
  classical
  let projected : Object → (Field → Bool) := fun object field =>
    if field ∈ selected then fieldValue field object else false
  let decode : (Field → Bool) → Bool := fun signature =>
    if witness : ∃ object, projected object = signature then
      profile witness.choose
    else false
  refine ⟨decode, ?_⟩
  intro object
  dsimp [decode, projected]
  have witness : ∃ candidate, projected candidate = projected object := ⟨object, rfl⟩
  rw [dif_pos witness]
  apply constant
  intro field selectedField
  have equality := congrFun witness.choose_spec field
  simpa [projected, selectedField] using equality

end OCKIndividuationMSpaceComposition
