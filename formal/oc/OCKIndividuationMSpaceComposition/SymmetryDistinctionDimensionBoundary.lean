import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionExtension

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# Magnitude and betweenness at the two-point dimensional boundary

A primitive distinction already generates its exact two-point axis and local
`C₂` reversal.  This module asks what quantitative and interpolative content
is forced before any interval, order, topology, metric space or path is added.

The answer separates two levels.  Equality alone gives a canonical discrete
`0/1` magnitude which is symmetric, separating, triangular and invariant under
reversal.  But every symmetric zero-diagonal magnitude on the generated axis
has only one off-diagonal value.  Hence the pair has extent, but no internally
graded extent.

Likewise, any strict betweenness relation would require an intermediate point
different from both endpoints.  The generated axis has no such point.  A third
ambient point is therefore necessary for strict interpolation, while a finite
countermodel shows that a third point alone still does not select a betweenness
relation.  No notion of dimension or continuum is hidden in the definitions.
-/

/-! ## The canonical discrete magnitude -/

/-- Equality supplies a canonical discrete magnitude on the generated axis:
zero on the diagonal and one off it.  No ordering of all possible magnitude
structures, and hence no minimality claim among them, is assumed here. -/
noncomputable def axisDiscreteMagnitude {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (left right : distinction.Axis) : Nat := by
  classical
  exact if left = right then 0 else 1

@[simp] theorem axisDiscreteMagnitude_self {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (point : distinction.Axis) :
    distinction.axisDiscreteMagnitude point point = 0 := by
  simp [axisDiscreteMagnitude]

theorem axisDiscreteMagnitude_eq_zero_iff {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (left right : distinction.Axis) :
    distinction.axisDiscreteMagnitude left right = 0 ↔ left = right := by
  classical
  simp [axisDiscreteMagnitude]

theorem axisDiscreteMagnitude_pos_iff {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (left right : distinction.Axis) :
    0 < distinction.axisDiscreteMagnitude left right ↔ left ≠ right := by
  classical
  by_cases same : left = right <;> simp [axisDiscreteMagnitude, same]

theorem axisDiscreteMagnitude_symmetric {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (left right : distinction.Axis) :
    distinction.axisDiscreteMagnitude left right =
      distinction.axisDiscreteMagnitude right left := by
  classical
  by_cases same : left = right
  · subst right
    simp
  · have reverseDifferent : right ≠ left := Ne.symm same
    simp [axisDiscreteMagnitude, same, reverseDifferent]

theorem axisDiscreteMagnitude_triangle {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (left middle right : distinction.Axis) :
    distinction.axisDiscreteMagnitude left right ≤
      distinction.axisDiscreteMagnitude left middle +
        distinction.axisDiscreteMagnitude middle right := by
  rcases distinction.axis_cases left with rfl | rfl <;>
    rcases distinction.axis_cases middle with rfl | rfl <;>
      rcases distinction.axis_cases right with rfl | rfl <;>
        simp [axisDiscreteMagnitude, distinction.axisFirst_ne_axisSecond,
          Ne.symm distinction.axisFirst_ne_axisSecond]

/-- The un-oriented magnitude survives simultaneous reversal of both poles. -/
theorem axisDiscreteMagnitude_reversalInvariant {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (left right : distinction.Axis) :
    distinction.axisDiscreteMagnitude
        (distinction.axisSwap left) (distinction.axisSwap right) =
      distinction.axisDiscreteMagnitude left right := by
  classical
  by_cases same : left = right
  · subst right
    simp
  · have swappedDifferent :
        distinction.axisSwap left ≠ distinction.axisSwap right := by
      intro swappedSame
      exact same (distinction.axisSwapEquiv.injective swappedSame)
    simp [axisDiscreteMagnitude, same, swappedDifferent]

/-! ## Exact magnitude ceiling of a two-point carrier -/

/-- Any symmetric magnitude on the generated axis is completely determined
off the diagonal by one value.  This is a classification theorem, not a choice
of units. -/
theorem symmetricMagnitude_offDiagonal
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (magnitude : distinction.Axis → distinction.Axis → Nat)
    (symmetric : ∀ left right, magnitude left right = magnitude right left)
    (left right : distinction.Axis)
    (different : left ≠ right) :
    magnitude left right =
      magnitude distinction.axisFirst distinction.axisSecond := by
  rcases distinction.axis_cases left with rfl | rfl <;>
    rcases distinction.axis_cases right with rfl | rfl
  · exact (different rfl).elim
  · rfl
  · rw [symmetric]
  · exact (different rfl).elim

/-- Consequently two distinct pairs cannot carry two different positive
magnitude grades on the generated axis. -/
theorem offDiagonalMagnitude_unique
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (magnitude : distinction.Axis → distinction.Axis → Nat)
    (symmetric : ∀ left right, magnitude left right = magnitude right left)
    {left right otherLeft otherRight : distinction.Axis}
    (different : left ≠ right)
    (otherDifferent : otherLeft ≠ otherRight) :
    magnitude left right = magnitude otherLeft otherRight := by
  rw [distinction.symmetricMagnitude_offDiagonal
      magnitude symmetric left right different,
    distinction.symmetricMagnitude_offDiagonal
      magnitude symmetric otherLeft otherRight otherDifferent]

/-! ## Strict betweenness and interpolation boundary -/

/-- The minimal strictness fragment expected of a strict betweenness law: its
middle point differs from both endpoints.  This is not yet a full betweenness
structure; no endpoint symmetry, order, transitivity, density or topology is
assumed. -/
def StrictBetweenLaw {Point : Type uCarrier}
    (Between : Point → Point → Point → Prop) : Prop :=
  ∀ {left middle right}, Between left middle right →
    middle ≠ left ∧ middle ≠ right

/-- The exact two-point generated axis admits no strict intermediate state,
for every proposed betweenness relation satisfying the minimal strictness law. -/
theorem generatedAxis_has_no_strict_between
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (Between : distinction.Axis → distinction.Axis → distinction.Axis → Prop)
    (strict : StrictBetweenLaw Between) :
    ¬ ∃ middle, Between distinction.axisFirst middle distinction.axisSecond := by
  rintro ⟨middle, between⟩
  rcases distinction.axis_cases middle with middleFirst | middleSecond
  · exact (strict between).1 middleFirst
  · exact (strict between).2 middleSecond

/-- A three-sample interpolation whose middle sample is new cannot live on the
generated axis.  This states the finite obstruction without calling the pair
an interval or importing real coordinates. -/
theorem generatedAxis_has_no_strict_threeSampleInterpolation
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (sample : Fin 3 → distinction.Axis)
    (starts : sample 0 = distinction.axisFirst)
    (ends : sample 2 = distinction.axisSecond) :
    ¬ (sample 1 ≠ sample 0 ∧ sample 1 ≠ sample 2) := by
  intro strictMiddle
  rcases distinction.axis_cases (sample 1) with middleFirst | middleSecond
  · exact strictMiddle.1 (middleFirst.trans starts.symm)
  · exact strictMiddle.2 (middleSecond.trans ends.symm)

/-- Any strict intermediate state between the primitive endpoints is
necessarily outside the distinguished pair.  Thus a third carrier point is a
necessary premise before strict betweenness can even occur. -/
theorem strictBetween_implies_outsidePoint
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (Between : Carrier → Carrier → Carrier → Prop)
    (strict : StrictBetweenLaw Between)
    {middle : Carrier}
    (between : Between distinction.first middle distinction.second) :
    Nonempty distinction.Outside :=
  ⟨⟨middle, (strict between).1, (strict between).2⟩⟩

/-! ## A third point is necessary but not sufficient -/

/-- The explicit three-point countermodel has a genuine primitive pair. -/
def finThreeEndpointDistinction : PrimitiveDistinction (Fin 3) where
  first := 0
  second := 2
  separated := by decide

/-- One relation satisfying the minimal strictness fragment on the same
three-point carrier. -/
def finThreeWitnessedBetween : Fin 3 → Fin 3 → Fin 3 → Prop :=
  fun left middle right => left = 0 ∧ middle = 1 ∧ right = 2

/-- The empty relation satisfies the minimal strictness fragment vacuously and
carries no betweenness evidence at all. -/
def finThreeEmptyBetween : Fin 3 → Fin 3 → Fin 3 → Prop :=
  fun _ _ _ => False

theorem finThreeWitnessedBetween_strict :
    StrictBetweenLaw finThreeWitnessedBetween := by
  rintro left middle right ⟨rfl, rfl, rfl⟩
  exact ⟨by decide, by decide⟩

theorem finThreeEmptyBetween_strict :
    StrictBetweenLaw finThreeEmptyBetween := by
  intro left middle right impossible
  change False at impossible
  exact impossible.elim

/-- A third point alone does not determine even the weak strictness-level
relation used here: the same carrier and primitive endpoints support both a
witnessed relation and the vacuous empty relation.  Stronger geometric
betweenness needs additional premises and a separate theorem slice. -/
theorem thirdPoint_does_not_determine_betweenness :
    (∃ middle,
      finThreeWitnessedBetween finThreeEndpointDistinction.first middle
        finThreeEndpointDistinction.second) ∧
    ¬ (∃ middle,
      finThreeEmptyBetween finThreeEndpointDistinction.first middle
        finThreeEndpointDistinction.second) := by
  constructor
  · exact ⟨1, rfl, rfl, rfl⟩
  · rintro ⟨middle, impossible⟩
    change False at impossible
    exact impossible

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
