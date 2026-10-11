namespace OCMinimalObligationSpine

universe u

/-!
Q035 cohomogeneity-one nonnegative-curvature classification gate.

The AIM target is a full classification problem:

  Classify cohomogeneity-one manifolds with `sec ≥ 0` and at least one
  totally geodesic principal orbit.

This file keeps that target intact.  A normal-homogeneous principal-orbit
collar classification is useful only as a source slice.  It closes the frozen
Q035 problem only after a coverage/reduction theorem proves that every admitted
Q035 candidate lies in that slice, and after the slice atlas is both sound and
complete for the frozen target.
-/

/-- Predicate bundle for an encoded Q035 classification domain. -/
structure Q035CohomogeneityOneDomain where
  Candidate : Type u
  AtlasEntry : Type u
  cohomogeneityOneManifold : Candidate → Prop
  secNonnegative : Candidate → Prop
  hasTotallyGeodesicPrincipalOrbit : Candidate → Prop
  classifiedByAtlasEntry : Candidate → AtlasEntry → Prop

/-- The frozen Q035 target: every admitted candidate is classified by the atlas. -/
def Q035FullClassificationTarget
    (D : Q035CohomogeneityOneDomain.{u}) : Prop :=
  ∀ M : D.Candidate,
    D.cohomogeneityOneManifold M →
    D.secNonnegative M →
    D.hasTotallyGeodesicPrincipalOrbit M →
    ∃ A : D.AtlasEntry, D.classifiedByAtlasEntry M A

/-- Direct full classification payload for Q035. -/
structure Q035DirectClassificationPackage
    (D : Q035CohomogeneityOneDomain.{u}) where
  classify :
    ∀ M : D.Candidate,
      D.cohomogeneityOneManifold M →
      D.secNonnegative M →
      D.hasTotallyGeodesicPrincipalOrbit M →
      ∃ A : D.AtlasEntry, D.classifiedByAtlasEntry M A

/-- A direct classification package closes the frozen Q035 target. -/
theorem q035_full_target_of_direct_classification_package
    {D : Q035CohomogeneityOneDomain.{u}}
    (P : Q035DirectClassificationPackage D) :
    Q035FullClassificationTarget D := by
  intro M h_cohom h_sec h_tg
  exact P.classify M h_cohom h_sec h_tg

/--
Counterexample to a proposed Q035 atlas.

This refutes a particular attempted classification atlas; it is not itself a
complete classification of the problem.  It is nevertheless terminal negative
evidence against any release claim that the attempted atlas covers Q035.
-/
def Q035AtlasCounterexample (D : Q035CohomogeneityOneDomain.{u}) : Prop :=
  ∃ M : D.Candidate,
    D.cohomogeneityOneManifold M ∧
    D.secNonnegative M ∧
    D.hasTotallyGeodesicPrincipalOrbit M ∧
    ¬ ∃ A : D.AtlasEntry, D.classifiedByAtlasEntry M A

/-- An atlas counterexample refutes the proposed full classification target. -/
theorem q035_atlas_counterexample_refutes_full_classification_target
    {D : Q035CohomogeneityOneDomain.{u}}
    (C : Q035AtlasCounterexample D) :
    ¬ Q035FullClassificationTarget D := by
  intro h_full
  rcases C with ⟨M, h_cohom, h_sec, h_tg, h_not_classified⟩
  exact h_not_classified (h_full M h_cohom h_sec h_tg)

/--
Normal-homogeneous collar source-slice data.

The screened literature route classifies a stricter slice where the relevant
principal orbit/collar is normal homogeneous.  That slice is valuable, but it
does not close Q035 unless a coverage theorem proves the frozen target reduces
to the slice.
-/
structure Q035NormalHomogeneousCollarSlice
    (D : Q035CohomogeneityOneDomain.{u}) where
  normalHomogeneousCollarCandidate : D.Candidate → Prop
  slice_classify :
    ∀ M : D.Candidate,
      D.cohomogeneityOneManifold M →
      D.secNonnegative M →
      D.hasTotallyGeodesicPrincipalOrbit M →
      normalHomogeneousCollarCandidate M →
      ∃ A : D.AtlasEntry, D.classifiedByAtlasEntry M A

/--
Coverage payload required before the normal-homogeneous collar slice may be
promoted to the full Q035 classification target.
-/
structure Q035NormalHomogeneousCollarCoverage
    (D : Q035CohomogeneityOneDomain.{u})
    (S : Q035NormalHomogeneousCollarSlice D) where
  every_admitted_candidate_in_slice :
    ∀ M : D.Candidate,
      D.cohomogeneityOneManifold M →
      D.secNonnegative M →
      D.hasTotallyGeodesicPrincipalOrbit M →
      S.normalHomogeneousCollarCandidate M

/--
The normal-homogeneous collar classification slice closes Q035 only after the
coverage payload proves that every frozen-domain candidate belongs to that
slice.
-/
theorem q035_full_target_of_normal_homogeneous_collar_coverage
    {D : Q035CohomogeneityOneDomain.{u}}
    (S : Q035NormalHomogeneousCollarSlice D)
    (C : Q035NormalHomogeneousCollarCoverage D S) :
    Q035FullClassificationTarget D := by
  intro M h_cohom h_sec h_tg
  exact S.slice_classify M h_cohom h_sec h_tg
    (C.every_admitted_candidate_in_slice M h_cohom h_sec h_tg)

/--
Residual witness showing that a candidate is in the frozen Q035 target but
outside the normal-homogeneous collar slice.  Such a witness blocks promotion
of the slice atlas to the full Q035 target.
-/
def Q035OutsideNormalHomogeneousSliceWitness
    (D : Q035CohomogeneityOneDomain.{u})
    (S : Q035NormalHomogeneousCollarSlice D) : Prop :=
  ∃ M : D.Candidate,
    D.cohomogeneityOneManifold M ∧
    D.secNonnegative M ∧
    D.hasTotallyGeodesicPrincipalOrbit M ∧
    ¬ S.normalHomogeneousCollarCandidate M

/-- A residual outside-slice witness refutes the slice coverage payload. -/
theorem q035_outside_slice_witness_refutes_collar_coverage
    {D : Q035CohomogeneityOneDomain.{u}}
    {S : Q035NormalHomogeneousCollarSlice D}
    (W : Q035OutsideNormalHomogeneousSliceWitness D S) :
    ¬ Q035NormalHomogeneousCollarCoverage D S := by
  intro C
  rcases W with ⟨M, h_cohom, h_sec, h_tg, h_not_slice⟩
  exact h_not_slice
    (C.every_admitted_candidate_in_slice M h_cohom h_sec h_tg)

/--
The next honest Q035 payload is either a direct full classification package, or
a source-slice classification together with the coverage theorem needed to
promote it to the frozen domain.
-/
def Q035TerminalClassificationPayload
    (D : Q035CohomogeneityOneDomain.{u}) : Prop :=
  Nonempty (Q035DirectClassificationPackage D) ∨
  ∃ S : Q035NormalHomogeneousCollarSlice D,
    Nonempty (Q035NormalHomogeneousCollarCoverage D S)

/-- Any terminal positive Q035 classification payload closes the full target. -/
theorem q035_full_target_of_terminal_classification_payload
    {D : Q035CohomogeneityOneDomain.{u}}
    (P : Q035TerminalClassificationPayload D) :
    Q035FullClassificationTarget D := by
  rcases P with h_direct | h_slice
  · rcases h_direct with ⟨C⟩
    exact q035_full_target_of_direct_classification_package C
  · rcases h_slice with ⟨S, h_coverage⟩
    rcases h_coverage with ⟨C⟩
    exact q035_full_target_of_normal_homogeneous_collar_coverage S C

/--
The honest terminal negative payload for Q035 is a verified counterexample to a
proposed full atlas.  Outside-slice witnesses are negative only for the slice
promotion route; they do not refute the full classification target by
themselves.
-/
def Q035TerminalNegativePayload
    (D : Q035CohomogeneityOneDomain.{u}) : Prop :=
  Q035AtlasCounterexample D

/-- Any terminal negative Q035 payload refutes the full target. -/
theorem q035_not_full_target_of_terminal_negative_payload
    {D : Q035CohomogeneityOneDomain.{u}}
    (N : Q035TerminalNegativePayload D) :
    ¬ Q035FullClassificationTarget D := by
  exact q035_atlas_counterexample_refutes_full_classification_target N

end OCMinimalObligationSpine
