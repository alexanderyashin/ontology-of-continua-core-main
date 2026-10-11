import OCKIndividuationMSpaceComposition.SymmetryPrimitivePresentationOrientationQuotient

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# Principal `C₂` action on the orientation fibre

The unordered-support quotient has an exactly two-element orientation fibre.
This module records the corresponding principal action explicitly, rather
than leaving transitivity and freeness implicit in the R3 interface.  The
non-trivial element is endpoint reversal; the action is derived from the
classification of presentations and introduces no new orientation premise.
-/

def orientationC2Action {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier) (bit : Bool)
    (presentation : OrientationFiber base) : OrientationFiber base :=
  if bit then orientationReverse base presentation else presentation

theorem orientationC2Action_false {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier)
    (presentation : OrientationFiber base) :
    orientationC2Action base false presentation = presentation := by
  rfl

theorem orientationC2Action_true {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier)
    (presentation : OrientationFiber base) :
    orientationC2Action base true presentation =
      orientationReverse base presentation := by
  rfl

theorem orientationC2Action_xor {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier) (first second : Bool)
    (presentation : OrientationFiber base) :
    orientationC2Action base (first ^^ second) presentation =
      orientationC2Action base first
        (orientationC2Action base second presentation) := by
  cases first <;> cases second <;>
    simp [orientationC2Action, orientationReverse_involutive]

/-- Any two presentations of one unordered distinction differ by identity or
    endpoint reversal. -/
theorem orientation_eq_self_or_reverse {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier)
    (first second : OrientationFiber base) :
    second = first ∨ second = orientationReverse base first :=
  orientationFiber_pairTransitive base first second

/-- The Boolean action is transitive on the orientation fibre. -/
theorem orientationC2Action_transitive {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier)
    (first second : OrientationFiber base) :
    ∃ bit : Bool, orientationC2Action base bit first = second := by
  rcases orientation_eq_self_or_reverse base first second with same | reversed
  · exact ⟨false, same.symm ▸ orientationC2Action_false base first⟩
  · exact ⟨true, reversed.symm ▸ orientationC2Action_true base first⟩

/-- No non-trivial Boolean element fixes an orientation presentation. -/
theorem orientationC2Action_free {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier) (bit : Bool)
    (presentation : OrientationFiber base)
    (fixed : orientationC2Action base bit presentation = presentation) :
    bit = false := by
  cases bit
  · rfl
  · exfalso
    apply orientationReverse_fixedPointFree base presentation
    simpa [orientationC2Action] using fixed

/-- Every target presentation is reached by a unique element of `C₂`. -/
theorem orientationC2Action_unique {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier)
    (first second : OrientationFiber base) :
    ∃! bit : Bool, orientationC2Action base bit first = second := by
  rcases orientationC2Action_transitive base first second with
    ⟨bit, reaches⟩
  refine ⟨bit, reaches, ?_⟩
  intro other otherReaches
  cases bit with
  | false =>
    cases other with
    | false => rfl
    | true =>
      exfalso
      apply orientationReverse_fixedPointFree base first
      calc
        orientationReverse base first = second := by
          simpa [orientationC2Action] using otherReaches
        _ = first := reaches.symm
  | true =>
    cases other with
    | false =>
      exfalso
      apply orientationReverse_fixedPointFree base first
      calc
        orientationReverse base first = second := reaches
        _ = first := by
          simpa [orientationC2Action] using otherReaches.symm
    | true => rfl

/-! ## Compact principal-torsor spine -/

theorem orientationFiber_principal_c2_spine {Carrier : Type uCarrier}
    (base : PrimitiveDistinction Carrier) :
    (∀ (first second : OrientationFiber base),
      ∃ bit : Bool, orientationC2Action base bit first = second) ∧
    (∀ (bit : Bool) (presentation : OrientationFiber base)
      (_fixed : orientationC2Action base bit presentation = presentation),
      bit = false) ∧
    (∀ (first second : OrientationFiber base),
      ∃! bit : Bool, orientationC2Action base bit first = second) := by
  exact ⟨orientationC2Action_transitive base,
    fun bit presentation fixed =>
      orientationC2Action_free base bit presentation fixed,
    orientationC2Action_unique base⟩

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
