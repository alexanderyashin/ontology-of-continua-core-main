import OCKIndividuationMSpaceComposition.SymmetryDistinctionAffineDimension
import Mathlib.Tactic.Linarith

namespace OCKIndividuationMSpaceComposition

universe uScalar uCarrier

namespace PrimitiveDistinction

/-!
# Ordered interpolation and the midpoint coaxis

The previous module proves that a primitive distinction in a supplied linear
realization generates one direction.  This module adds the strictly stronger
premise that the scalar field is linearly ordered.  The parameter line then
has orientation, magnitude and dense algebraic interpolation.

Endpoint reversal acts by `t ↦ 1 - t`.  It reverses parameter order, preserves
absolute magnitude, and has the unique fixed parameter `1 / 2`.  This gives a
precise affine meaning to the intuition that the distinction is an "axis of
its axis": the unordered direction is invariant, either orientation may be
chosen, and the midpoint is fixed by exchanging the poles.

No completeness or continuum theorem is claimed.  A linearly ordered field
supplies dense algebraic interpolation, but completeness remains an additional
topological/order-theoretic premise.
-/

section OrderedAffineRealization

variable {K : Type uScalar} {V : Type uCarrier}
  [Field K] [LinearOrder K] [IsStrictOrderedRing K]
  [AddCommGroup V] [Module K V]

/-- Reversal of the affine parameter induced by exchanging the endpoints. -/
def parameterReflection (t : K) : K := 1 - t

omit [LinearOrder K] [IsStrictOrderedRing K] in
@[simp] theorem parameterReflection_zero : parameterReflection (0 : K) = 1 := by
  simp [parameterReflection]

omit [LinearOrder K] [IsStrictOrderedRing K] in
@[simp] theorem parameterReflection_one : parameterReflection (1 : K) = 0 := by
  simp [parameterReflection]

omit [LinearOrder K] [IsStrictOrderedRing K] in
/-- Parameter reflection is an involution. -/
theorem parameterReflection_involutive (t : K) :
    parameterReflection (parameterReflection t) = t := by
  simp [parameterReflection]

/-- Reversal exchanges parameter orientation. -/
theorem parameterReflection_strictAnti {s t : K} :
    parameterReflection s < parameterReflection t ↔ t < s := by
  simp [parameterReflection]

/-- The midpoint is the unique parameter fixed by endpoint reversal. -/
theorem parameterReflection_fixed_iff (t : K) :
    parameterReflection t = t ↔ t = (1 / 2 : K) := by
  constructor <;> intro hypothesis
  · dsimp [parameterReflection] at hypothesis
    linarith
  · subst t
    norm_num [parameterReflection]

/-- The affine midpoint selected by the supplied linear realization. -/
def affineMidpoint (distinction : PrimitiveDistinction V) : V :=
  affineAxisPoint distinction (1 / 2 : K)

/-- In an ordered-field realization the affine midpoint is a genuine ambient
point outside the original two-point axis. -/
theorem affineMidpoint_outside (distinction : PrimitiveDistinction V) :
    affineMidpoint (K := K) distinction ≠ distinction.first ∧
      affineMidpoint (K := K) distinction ≠ distinction.second := by
  apply affineAxisPoint_outside (K := K) distinction <;> norm_num

/-- Exchanging the endpoint labels leaves the affine midpoint fixed. -/
theorem reverseLabels_affineMidpoint
    (distinction : PrimitiveDistinction V) :
    affineMidpoint (K := K) distinction.reverseLabels =
      affineMidpoint (K := K) distinction := by
  rw [affineMidpoint, affineMidpoint, reverseLabels_affineAxisPoint]
  norm_num

/-- The midpoint is the only equal-parameter affine point left unchanged when
the displayed endpoint labels are exchanged. -/
theorem reverseLabels_affineAxisPoint_fixed_iff
    (distinction : PrimitiveDistinction V) (t : K) :
    distinction.reverseLabels.affineAxisPoint t =
        distinction.affineAxisPoint t ↔
      t = (1 / 2 : K) := by
  rw [reverseLabels_affineAxisPoint]
  constructor
  · intro equality
    have parameterEquality : 1 - t = t :=
      affineAxisPoint_injective (K := K) distinction equality
    exact (parameterReflection_fixed_iff t).1 parameterEquality
  · intro midpoint
    subst t
    norm_num

/-- Absolute scalar separation of two affine parameters. -/
def parameterMagnitude (s t : K) : K := |s - t|

omit [IsStrictOrderedRing K] in
/-- Endpoint reversal preserves un-oriented parameter magnitude. -/
theorem parameterMagnitude_reflectionInvariant (s t : K) :
    parameterMagnitude (parameterReflection s) (parameterReflection t) =
      parameterMagnitude s t := by
  have difference :
      parameterReflection s - parameterReflection t = -(s - t) := by
    simp [parameterReflection]
  rw [parameterMagnitude, parameterMagnitude, difference, abs_neg]

/-- Strict parameter betweenness, independent of which endpoint is displayed
first. -/
def StrictParameterBetween (left middle right : K) : Prop :=
  (left < middle ∧ middle < right) ∨
    (right < middle ∧ middle < left)

/-- Reflection preserves strict betweenness while reversing orientation. -/
theorem strictParameterBetween_reflectionInvariant
    (left middle right : K) :
    StrictParameterBetween (parameterReflection left)
        (parameterReflection middle) (parameterReflection right) ↔
      StrictParameterBetween left middle right := by
  simp only [StrictParameterBetween, parameterReflection_strictAnti]
  tauto

/-- The canonical midpoint lies strictly between the endpoint parameters. -/
theorem half_strictParameterBetween_zero_one :
    StrictParameterBetween (0 : K) (1 / 2 : K) 1 := by
  left
  constructor <;> norm_num

/-- Algebraic midpoint interpolation between arbitrary parameters. -/
def interpolateParameter (left right : K) : K :=
  (left + right) / 2

/-- Every ordered pair has a strictly intermediate algebraic midpoint. -/
theorem interpolateParameter_strictBetween {left right : K}
    (ordered : left < right) :
    left < interpolateParameter left right ∧
      interpolateParameter left right < right := by
  constructor <;> dsimp [interpolateParameter] <;> linarith

/-- Interpolation commutes with endpoint reversal. -/
theorem interpolateParameter_reflection
    (left right : K) :
    parameterReflection (interpolateParameter left right) =
      interpolateParameter (parameterReflection left)
        (parameterReflection right) := by
  simp [parameterReflection, interpolateParameter]
  ring

end OrderedAffineRealization

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
