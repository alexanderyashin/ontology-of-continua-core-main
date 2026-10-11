import OCKIndividuationMSpaceComposition.ContextIndexedSymmetry
import Mathlib.Algebra.Order.Ring.Abs
import Mathlib.Data.Fintype.Basic
import Mathlib.Data.Rat.Defs
import Mathlib.Algebra.Order.BigOperators.Group.Finset

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

universe uObject uTest uOutcome uCoarseTest uFineTest

/-!
# Finite structural identifiability under bounded discrepancy

This module separates three claims which are often conflated.

* A finite typed test family induces an exact observational equivalence and an
  executable natural-number mismatch count.
* Exact separation makes the observation map injective and its exact fibres
  singleton.
* Given a declared rational discrepancy geometry, pairwise margin strictly
  greater than twice a deterministic error bound yields unique recovery.

The last result is a finite structural robustness theorem.  It contains no
sampling model, estimator, probability law, asymptotic limit, or statistical
consistency claim.  Such claims require an additional empirical theory.
-/

/-- A family of typed tests with one declared outcome for each object and test. -/
structure FiniteTypedTestFamily
    (Object : Type uObject)
    (Test : Type uTest)
    (Outcome : Type uOutcome) where
  observe : Object → Test → Outcome

/-- The complete typed observation signature of an object. -/
def FiniteTypedTestFamily.signature
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    (family : FiniteTypedTestFamily Object Test Outcome) :
    Object → (Test → Outcome) :=
  family.observe

/-- Exact observational equivalence under every declared test. -/
def ExactTestEquivalent
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    (family : FiniteTypedTestFamily Object Test Outcome)
    (left right : Object) : Prop :=
  ∀ test, family.observe left test = family.observe right test

/-- Distinct objects are separated by at least one declared typed test. -/
def ExactTestSeparation
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    (family : FiniteTypedTestFamily Object Test Outcome) : Prop :=
  ∀ ⦃left right⦄, left ≠ right →
    ∃ test, family.observe left test ≠ family.observe right test

/-- Exact separation is sufficient for injectivity of the complete signature. -/
theorem exactTestSeparation_implies_signature_injective
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    {family : FiniteTypedTestFamily Object Test Outcome}
    (separates : ExactTestSeparation family) :
    Function.Injective family.signature := by
  intro left right equalSignatures
  by_contra distinct
  rcases separates distinct with ⟨test, differs⟩
  exact differs (congrFun equalSignatures test)

/-- Under exact separation, observational equivalence is object equality. -/
theorem exactTestEquivalent_iff_eq_of_separation
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    {family : FiniteTypedTestFamily Object Test Outcome}
    (separates : ExactTestSeparation family)
    (left right : Object) :
    ExactTestEquivalent family left right ↔ left = right := by
  constructor
  · intro equivalent
    apply exactTestSeparation_implies_signature_injective separates
    funext test
    exact equivalent test
  · intro equalObjects
    subst right
    intro test
    rfl

/-- Every exact observation fibre is a singleton when tests separate objects. -/
theorem exactTestSeparation_unique_observation_class
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    {family : FiniteTypedTestFamily Object Test Outcome}
    (separates : ExactTestSeparation family)
    (object : Object) :
    ∃! candidate : Object,
      family.signature candidate = family.signature object := by
  refine ⟨object, rfl, ?_⟩
  intro candidate sameSignature
  exact exactTestSeparation_implies_signature_injective separates sameSignature

/-!
## Natural-number mismatch discrepancy
-/

/-- The number of finite tests on which two objects have unequal outcomes. -/
def natTestDiscrepancy
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    [Fintype Test]
    [DecidableEq Outcome]
    (family : FiniteTypedTestFamily Object Test Outcome)
    (left right : Object) : Nat :=
  (Finset.univ.filter fun test =>
    family.observe left test ≠ family.observe right test).card

/-- Zero mismatch is exactly equality under every finite typed test. -/
theorem natTestDiscrepancy_eq_zero_iff
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    [Fintype Test]
    [DecidableEq Outcome]
    (family : FiniteTypedTestFamily Object Test Outcome)
    (left right : Object) :
    natTestDiscrepancy family left right = 0 ↔
      ExactTestEquivalent family left right := by
  simp [natTestDiscrepancy, ExactTestEquivalent]

/-- Exact separation makes zero natural discrepancy equivalent to identity. -/
theorem natTestDiscrepancy_eq_zero_iff_eq_of_separation
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    [Fintype Test]
    [DecidableEq Outcome]
    {family : FiniteTypedTestFamily Object Test Outcome}
    (separates : ExactTestSeparation family)
    (left right : Object) :
    natTestDiscrepancy family left right = 0 ↔ left = right := by
  rw [natTestDiscrepancy_eq_zero_iff]
  exact exactTestEquivalent_iff_eq_of_separation separates left right

/-!
## Declared rational discrepancy geometry

Outcomes need not be numeric.  A domain supplies a rational-valued local
discrepancy and its metric laws; the finite global discrepancy is their sum.
-/

/-- A rational-valued discrepancy contract on one typed test outcome. -/
structure RatOutcomeDiscrepancy (Outcome : Type uOutcome) where
  distance : Outcome → Outcome → ℚ
  nonnegative : ∀ left right, 0 ≤ distance left right
  self_zero : ∀ value, distance value value = 0
  symmetric : ∀ left right, distance left right = distance right left
  triangle : ∀ first middle last,
    distance first last ≤ distance first middle + distance middle last
  zero_implies_eq : ∀ {left right}, distance left right = 0 → left = right

/-- Sum of local rational discrepancies over a finite typed test family. -/
def ratSignatureDiscrepancy
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    [Fintype Test]
    (geometry : RatOutcomeDiscrepancy Outcome)
    (left right : Test → Outcome) : ℚ :=
  ∑ test, geometry.distance (left test) (right test)

/-- Rational discrepancy between the canonical signatures of two objects. -/
def ratObjectDiscrepancy
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    [Fintype Test]
    (geometry : RatOutcomeDiscrepancy Outcome)
    (family : FiniteTypedTestFamily Object Test Outcome)
    (left right : Object) : ℚ :=
  ratSignatureDiscrepancy geometry (family.signature left) (family.signature right)

theorem ratSignatureDiscrepancy_nonnegative
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    [Fintype Test]
    (geometry : RatOutcomeDiscrepancy Outcome)
    (left right : Test → Outcome) :
    0 ≤ ratSignatureDiscrepancy geometry left right := by
  exact Finset.sum_nonneg fun test _ =>
    geometry.nonnegative (left test) (right test)

theorem ratSignatureDiscrepancy_self
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    [Fintype Test]
    (geometry : RatOutcomeDiscrepancy Outcome)
    (signature : Test → Outcome) :
    ratSignatureDiscrepancy geometry signature signature = 0 := by
  simp [ratSignatureDiscrepancy, geometry.self_zero]

theorem ratSignatureDiscrepancy_symm
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    [Fintype Test]
    (geometry : RatOutcomeDiscrepancy Outcome)
    (left right : Test → Outcome) :
    ratSignatureDiscrepancy geometry left right =
      ratSignatureDiscrepancy geometry right left := by
  apply Finset.sum_congr rfl
  intro test _
  exact geometry.symmetric (left test) (right test)

theorem ratSignatureDiscrepancy_triangle
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    [Fintype Test]
    (geometry : RatOutcomeDiscrepancy Outcome)
    (first middle last : Test → Outcome) :
    ratSignatureDiscrepancy geometry first last ≤
      ratSignatureDiscrepancy geometry first middle +
        ratSignatureDiscrepancy geometry middle last := by
  calc
    ratSignatureDiscrepancy geometry first last =
        ∑ test, geometry.distance (first test) (last test) := rfl
    _ ≤ ∑ test,
        (geometry.distance (first test) (middle test) +
          geometry.distance (middle test) (last test)) :=
      Finset.sum_le_sum fun test _ =>
        geometry.triangle (first test) (middle test) (last test)
    _ = ratSignatureDiscrepancy geometry first middle +
          ratSignatureDiscrepancy geometry middle last := by
      rw [Finset.sum_add_distrib]
      change ratSignatureDiscrepancy geometry first middle +
        ratSignatureDiscrepancy geometry middle last = _
      rfl

/-- A uniform lower bound on rational discrepancy of distinct objects. -/
def RatSeparationMargin
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    [Fintype Test]
    (geometry : RatOutcomeDiscrepancy Outcome)
    (family : FiniteTypedTestFamily Object Test Outcome)
    (margin : ℚ) : Prop :=
  ∀ ⦃left right⦄, left ≠ right →
    margin ≤ ratObjectDiscrepancy geometry family left right

/-- A measured signature is within a declared deterministic rational error. -/
def SignatureWithinRatError
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    [Fintype Test]
    (geometry : RatOutcomeDiscrepancy Outcome)
    (family : FiniteTypedTestFamily Object Test Outcome)
    (object : Object)
    (measured : Test → Outcome)
    (error : ℚ) : Prop :=
  ratSignatureDiscrepancy geometry (family.signature object) measured ≤ error

/--
If distinct object signatures are separated by margin greater than twice the
declared error, no measured signature can be compatible with two objects.
-/
theorem margin_gt_twice_error_implies_unique_recovery
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    [Fintype Test]
    {geometry : RatOutcomeDiscrepancy Outcome}
    {family : FiniteTypedTestFamily Object Test Outcome}
    {margin error : ℚ}
    (separated : RatSeparationMargin geometry family margin)
    (strictGap : 2 * error < margin)
    {measured : Test → Outcome}
    {first second : Object}
    (firstCompatible :
      SignatureWithinRatError geometry family first measured error)
    (secondCompatible :
      SignatureWithinRatError geometry family second measured error) :
    first = second := by
  by_contra distinct
  have marginLower :
      margin ≤ ratObjectDiscrepancy geometry family first second :=
    separated distinct
  have measuredSecond :
      ratSignatureDiscrepancy geometry measured (family.signature second) ≤
        error := by
    rw [ratSignatureDiscrepancy_symm]
    exact secondCompatible
  have distanceUpper :
      ratObjectDiscrepancy geometry family first second ≤ error + error := by
    exact le_trans
      (ratSignatureDiscrepancy_triangle geometry
        (family.signature first) measured (family.signature second))
      (add_le_add firstCompatible measuredSecond)
  have impossible : margin ≤ 2 * error := by
    simpa [two_mul] using le_trans marginLower distanceUpper
  exact (not_le_of_gt strictGap) impossible

/-!
## Aliasing and the limit of observation-only recovery
-/

/-- Two distinct objects have exactly the same complete test signature. -/
def ExactObservationAlias
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    (family : FiniteTypedTestFamily Object Test Outcome) : Prop :=
  ∃ left right, left ≠ right ∧
    family.signature left = family.signature right

/-- An exact alias refutes injectivity of the observation map. -/
theorem exactObservationAlias_refutes_signature_injective
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    {family : FiniteTypedTestFamily Object Test Outcome}
    (aliasWitness : ExactObservationAlias family) :
    ¬ Function.Injective family.signature := by
  intro injective
  rcases aliasWitness with ⟨left, right, distinct, sameSignature⟩
  exact distinct (injective sameSignature)

/-- No signature-only function can recover every object across an exact alias. -/
theorem exactObservationAlias_no_observation_only_recovery
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    {family : FiniteTypedTestFamily Object Test Outcome}
    (aliasWitness : ExactObservationAlias family) :
    ¬ ∃ recover : (Test → Outcome) → Object,
      Function.LeftInverse recover family.signature := by
  rintro ⟨recover, recovers⟩
  rcases aliasWitness with ⟨left, right, distinct, sameSignature⟩
  have sameRecovered := congrArg recover sameSignature
  rw [recovers left, recovers right] at sameRecovered
  exact distinct sameRecovered

/-- Explicit finite alias: no unit-valued test distinguishes Boolean objects. -/
def boolUnitAliasedTests : FiniteTypedTestFamily Bool Unit Unit where
  observe := fun _ _ => ()

theorem boolUnitAliasedTests_has_exact_alias :
    ExactObservationAlias boolUnitAliasedTests := by
  exact ⟨false, true, Bool.false_ne_true, rfl⟩

theorem boolUnitAliasedTests_no_observation_only_recovery :
    ¬ ∃ recover : (Unit → Unit) → Bool,
      Function.LeftInverse recover boolUnitAliasedTests.signature := by
  exact exactObservationAlias_no_observation_only_recovery
    boolUnitAliasedTests_has_exact_alias

/-!
## Test refinement shrinks the allowed identity relation
-/

/-- Fine tests contain a typed copy of every coarse test and preserve outcomes. -/
structure FiniteTestRefinement
    {Object : Type uObject}
    {CoarseTest : Type uCoarseTest}
    {FineTest : Type uFineTest}
    {Outcome : Type uOutcome}
    (coarse : FiniteTypedTestFamily Object CoarseTest Outcome)
    (fine : FiniteTypedTestFamily Object FineTest Outcome) where
  coarseTest : CoarseTest → FineTest
  preserves : ∀ object test,
    fine.observe object (coarseTest test) = coarse.observe object test

/-- Candidate identity allowed by a test family is equality of all outcomes. -/
def TestAllowedIdentity
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    (family : FiniteTypedTestFamily Object Test Outcome)
    (left right : Object) : Prop :=
  ExactTestEquivalent family left right

/-- Every identity allowed by fine tests is allowed by their coarse restriction. -/
theorem test_refinement_shrinks_allowed_identity
    {Object : Type uObject}
    {CoarseTest : Type uCoarseTest}
    {FineTest : Type uFineTest}
    {Outcome : Type uOutcome}
    {coarse : FiniteTypedTestFamily Object CoarseTest Outcome}
    {fine : FiniteTypedTestFamily Object FineTest Outcome}
    (refinement : FiniteTestRefinement coarse fine)
    {left right : Object}
    (fineAllows : TestAllowedIdentity fine left right) :
    TestAllowedIdentity coarse left right := by
  intro coarseTest
  rw [← refinement.preserves left coarseTest,
    ← refinement.preserves right coarseTest]
  exact fineAllows (refinement.coarseTest coarseTest)

/-- Exact separation of fine tests need not be inherited by the coarse tests. -/
def boolCoarseTests : FiniteTypedTestFamily Bool Unit Bool where
  observe := fun _ _ => false

def boolFineTests : FiniteTypedTestFamily Bool Bool Bool where
  observe := fun object test => if test then object else false

def boolFineRefinesCoarse : FiniteTestRefinement boolCoarseTests boolFineTests where
  coarseTest := fun _ => false
  preserves := by intro object test; cases test; rfl

theorem boolFineTests_separate : ExactTestSeparation boolFineTests := by
  intro left right distinct
  exact ⟨true, distinct⟩

theorem boolCoarseTests_have_exact_alias :
    ExactObservationAlias boolCoarseTests := by
  exact ⟨false, true, Bool.false_ne_true, rfl⟩

theorem coarse_tests_can_alias_while_fine_tests_separate :
    ExactObservationAlias boolCoarseTests ∧
      ExactTestSeparation boolFineTests :=
  ⟨boolCoarseTests_have_exact_alias, boolFineTests_separate⟩

end OCKIndividuationMSpaceComposition
