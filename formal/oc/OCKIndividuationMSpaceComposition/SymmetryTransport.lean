import OCKIndividuationMSpaceComposition.SymmetryInvariantQuotient

namespace OCKIndividuationMSpaceComposition

universe uCarrier uObservable

/-!
# Transport of axes and the symmetry-defect boundary

This layer turns the local two-point result into a transformation rule.  A
map is allowed to transport an axis only when it commutes with the generating
involution.  Under that condition it induces a well-defined map on the axis
quotient, and composition of commuting equivalences is respected exactly.
The complementary set of failed commutation points is a concrete defect
surface: it is empty exactly when the transformation is symmetry preserving.
-/

/-- Points at which a transformation fails to commute with the symmetry. -/
def symmetryDefect {Carrier : Type uCarrier}
    (symmetry : FixedPointFreeInvolution Carrier)
    (map : Carrier → Carrier) : Set Carrier :=
  {x | map (symmetry.action x) ≠ symmetry.action (map x)}

theorem symmetryDefect_empty_iff {Carrier : Type uCarrier}
    (symmetry : FixedPointFreeInvolution Carrier) (map : Carrier → Carrier) :
    symmetryDefect symmetry map = (∅ : Set Carrier) ↔
      CommutesWithInvolution symmetry map := by
  constructor
  · intro empty x
    by_contra failure
    have member : x ∈ symmetryDefect symmetry map := failure
    rw [empty] at member
    exact member
  · intro commutes
    ext x
    constructor
    · intro member
      change map (symmetry.action x) ≠ symmetry.action (map x) at member
      exact (member (commutes x)).elim
    · intro member
      exact (by simpa using member : False).elim

/-- A commuting map descends to a well-defined map of axis classes. -/
def commutingAxisMap {Carrier : Type uCarrier}
    (symmetry : FixedPointFreeInvolution Carrier)
    (map : Carrier ≃ Carrier)
    (commutes : CommutesWithInvolution symmetry map) :
    AxisQuotient symmetry → AxisQuotient symmetry :=
  Quotient.lift (fun x => axisClass symmetry (map x)) (by
    intro left right same
    apply Quotient.sound (s := axisSetoid symmetry)
    rcases same with same | same
    · exact Or.inl (congrArg map same)
    · exact Or.inr ((congrArg map same).trans (commutes left)))

@[simp] theorem commutingAxisMap_spec {Carrier : Type uCarrier}
    (symmetry : FixedPointFreeInvolution Carrier)
    (map : Carrier ≃ Carrier)
    (commutes : CommutesWithInvolution symmetry map) (x : Carrier) :
    commutingAxisMap symmetry map commutes (axisClass symmetry x) =
      axisClass symmetry (map x) :=
  rfl

theorem commuting_equiv_trans_commutes {Carrier : Type uCarrier}
    (symmetry : FixedPointFreeInvolution Carrier)
    (first second : Carrier ≃ Carrier)
    (first_commutes : CommutesWithInvolution symmetry first)
    (second_commutes : CommutesWithInvolution symmetry second) :
    CommutesWithInvolution symmetry (first.trans second) := by
  intro x
  change second (first (symmetry.action x)) =
    symmetry.action (second (first x))
  calc
    second (first (symmetry.action x)) =
        second (symmetry.action (first x)) :=
      congrArg second (first_commutes x)
    _ = symmetry.action (second (first x)) := second_commutes (first x)

/-!
The quotient transport is functorial for the order convention of `Equiv.trans`:
`first.trans second` means first, then second.
-/
theorem commutingAxisMap_trans_comp {Carrier : Type uCarrier}
    (symmetry : FixedPointFreeInvolution Carrier)
    (first second : Carrier ≃ Carrier)
    (first_commutes : CommutesWithInvolution symmetry first)
    (second_commutes : CommutesWithInvolution symmetry second) :
    commutingAxisMap symmetry (first.trans second)
        (commuting_equiv_trans_commutes symmetry first second
          first_commutes second_commutes) =
      (commutingAxisMap symmetry second second_commutes) ∘
        (commutingAxisMap symmetry first first_commutes) := by
  funext quotient
  refine Quotient.inductionOn quotient ?_
  intro x
  rfl

theorem commutingAxisMap_identity {Carrier : Type uCarrier}
    (symmetry : FixedPointFreeInvolution Carrier) :
    commutingAxisMap symmetry (Equiv.refl Carrier) (by
      intro x
      rfl) = id := by
  funext quotient
  refine Quotient.inductionOn quotient ?_
  intro x
  rfl

/-- An invariant observable is compatible with every induced commuting map. -/
theorem invariant_factor_after_commuting_map {Carrier : Type uCarrier}
    {Observable : Type uObservable}
    (symmetry : FixedPointFreeInvolution Carrier)
    (observable : Carrier → Observable)
    (invariant : InvariantObservable symmetry observable)
    (map : Carrier ≃ Carrier)
    (commutes : CommutesWithInvolution symmetry map) (x : Carrier) :
    invariantObservableFactor symmetry observable invariant
        (commutingAxisMap symmetry map commutes (axisClass symmetry x)) =
      observable (map x) := by
  rfl

end OCKIndividuationMSpaceComposition
