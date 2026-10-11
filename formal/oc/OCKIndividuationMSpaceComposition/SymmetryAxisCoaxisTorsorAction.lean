import OCKIndividuationMSpaceComposition.SymmetryAxisCoaxisTorsor

namespace OCKIndividuationMSpaceComposition

universe u

namespace PrimitiveDistinction

/-!
# Principal `C₂` action on coorientations

`SymmetryAxisCoaxisTorsor` gives a Boolean coordinate for the two possible
coorientations of a generated two-point axis.  Here that coordinate is
promoted to the explicit principal-action statement: the reversal action is
free, transitive, and has a unique group element carrying any coaxis to any
other.  No extra torsor premise is introduced; the result follows from the
already proved two-element classification.
-/

theorem axisCoaxisCode_coaxisC2Action {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (bit : Bool) (coaxis : AxisCoaxis symmetry x) :
    axisCoaxisCode (coaxisC2Action bit coaxis) =
      bit ^^ axisCoaxisCode coaxis := by
  cases bit <;> simp [coaxisC2Action, axisCoaxisCode_coaxisSwap]

/-- Any two coorientations differ by either the identity or reversal. -/
theorem coaxis_eq_self_or_swap {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (first second : AxisCoaxis symmetry x) :
    second = first ∨ second = coaxisSwap first := by
  by_cases sameCode : axisCoaxisCode second = axisCoaxisCode first
  · left
    exact (axisCoaxisEquivBool symmetry x).injective sameCode
  · right
    apply (axisCoaxisEquivBool symmetry x).injective
    change axisCoaxisCode second = axisCoaxisCode (coaxisSwap first)
    rw [axisCoaxisCode_coaxisSwap]
    cases firstCode : axisCoaxisCode first <;>
      cases secondCode : axisCoaxisCode second <;>
      simp_all

/-- The Boolean action is transitive on the coaxis choices. -/
theorem coaxisC2Action_transitive {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (first second : AxisCoaxis symmetry x) :
    ∃ bit : Bool, coaxisC2Action bit first = second := by
  rcases coaxis_eq_self_or_swap first second with same | swapped
  · exact ⟨false, same.symm ▸ coaxisC2Action_false first⟩
  · exact ⟨true, swapped.symm ▸ coaxisC2Action_true first⟩

/-- No non-trivial Boolean element fixes a coaxis. -/
theorem coaxisC2Action_free {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (bit : Bool) (coaxis : AxisCoaxis symmetry x)
    (fixed : coaxisC2Action bit coaxis = coaxis) :
    bit = false := by
  cases bit
  · rfl
  · exfalso
    exact coaxisSwap_ne_self coaxis (by simpa [coaxisC2Action] using fixed)

/-- Every target coaxis is reached by a unique element of `C₂`. -/
theorem coaxisC2Action_unique {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (first second : AxisCoaxis symmetry x) :
    ∃! bit : Bool, coaxisC2Action bit first = second := by
  rcases coaxisC2Action_transitive first second with ⟨bit, reaches⟩
  refine ⟨bit, reaches, ?_⟩
  intro other otherReaches
  cases bit with
  | false =>
    cases other with
    | false => rfl
    | true =>
      exfalso
      apply coaxisSwap_ne_self first
      calc
        coaxisSwap first = second := by
          simpa [coaxisC2Action] using otherReaches
        _ = first := reaches.symm
  | true =>
    cases other with
    | false =>
      exfalso
      apply coaxisSwap_ne_self first
      calc
        coaxisSwap first = second := reaches
        _ = first := by
          simpa [coaxisC2Action] using otherReaches.symm
    | true => rfl

/-! ## Compact principal-torsor spine -/

theorem axisCoaxis_principal_c2_spine {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier} :
    (∀ (first second : AxisCoaxis symmetry x),
      ∃ bit : Bool, coaxisC2Action bit first = second) ∧
    (∀ (bit : Bool) (coaxis : AxisCoaxis symmetry x)
      (_fixed : coaxisC2Action bit coaxis = coaxis), bit = false) ∧
    (∀ (first second : AxisCoaxis symmetry x),
      ∃! bit : Bool, coaxisC2Action bit first = second) := by
  exact ⟨coaxisC2Action_transitive,
    fun bit coaxis fixed => coaxisC2Action_free bit coaxis fixed,
    coaxisC2Action_unique⟩

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
