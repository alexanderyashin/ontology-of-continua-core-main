import OCKIndividuationMSpaceComposition.CausalObservationalBridge

namespace OCKIndividuationMSpaceComposition

universe uPresentation uProvenance uFuture

/-!
# Provenance-sensitive revision profile

An occurrence may render the same presentation while carrying a different
provenance token.  The theorem below gives the exact boundary for a
presentation-only resolver: it exists iff every future-admissibility profile
is constant on presentation fibres.  Thus provenance is not an optional
annotation when it changes successor admissibility.
-/

def PresentationProfileConstant
    {Presentation : Type uPresentation} {Provenance : Type uProvenance}
    {Future : Type uFuture}
    (profile : ProvenancedPresentation Presentation Provenance → Future → Prop) : Prop :=
  ∀ left right,
    left.presentation = right.presentation →
    ∀ future, profile left future ↔ profile right future

def PresentationProfileDecoder
    {Presentation : Type uPresentation} {Future : Type uFuture}
    (profile : ProvenancedPresentation Presentation Bool → Future → Prop) : Prop :=
  ∃ decode : Presentation → Future → Prop,
    ∀ occurrence future,
      decode occurrence.presentation future ↔ profile occurrence future

/-!
The generic version uses an inhabited provenance carrier.  The Bool-specialised
abbreviation above is retained for the common two-token countermodel.
-/
theorem presentation_profile_decoder_exists_iff_constant
    {Presentation : Type uPresentation} {Provenance : Type uProvenance}
    {Future : Type uFuture} [Inhabited Provenance]
    (profile : ProvenancedPresentation Presentation Provenance → Future → Prop) :
    (∃ decode : Presentation → Future → Prop,
      ∀ occurrence future,
        decode occurrence.presentation future ↔ profile occurrence future) ↔
      PresentationProfileConstant profile := by
  constructor
  · rintro ⟨decode, sound⟩
    intro left right samePresentation future
    rw [← sound left future, ← sound right future, samePresentation]
  · intro constant
    refine ⟨fun presentation future =>
      profile ⟨presentation, default⟩ future, ?_⟩
    intro occurrence future
    exact (constant occurrence ⟨occurrence.presentation, default⟩ rfl future).symm

/-- A single same-presentation/different-profile witness kills every
presentation-only future-admissibility decoder. -/
theorem provenance_profile_collision_blocks_presentation_decoder
    {Presentation : Type uPresentation} {Provenance : Type uProvenance}
    {Future : Type uFuture} [Inhabited Provenance]
    (profile : ProvenancedPresentation Presentation Provenance → Future → Prop)
    {left right : ProvenancedPresentation Presentation Provenance}
    (samePresentation : left.presentation = right.presentation)
    (differentProfile : ∃ future, ¬ (profile left future ↔ profile right future)) :
    ¬ ∃ decode : Presentation → Future → Prop,
      ∀ occurrence future,
        decode occurrence.presentation future ↔ profile occurrence future := by
  intro decoder
  have constant := (presentation_profile_decoder_exists_iff_constant profile).mp decoder
  rcases differentProfile with ⟨future, different⟩
  exact different (constant left right samePresentation future)

/-! A Bool witness instantiates the abstract no-go with two provenance tokens. -/
def boolProvenanceRevisionProfile
    (occurrence : ProvenancedPresentation Unit Bool) (future : Bool) : Prop :=
  occurrence.provenance = future

theorem bool_provenance_profile_requires_provenance
    : ¬ PresentationProfileDecoder boolProvenanceRevisionProfile := by
  letI : Inhabited Bool := ⟨false⟩
  apply provenance_profile_collision_blocks_presentation_decoder
    (left := ⟨(), false⟩) (right := ⟨(), true⟩)
    boolProvenanceRevisionProfile rfl
  refine ⟨false, ?_⟩
  simp [boolProvenanceRevisionProfile]

end OCKIndividuationMSpaceComposition
