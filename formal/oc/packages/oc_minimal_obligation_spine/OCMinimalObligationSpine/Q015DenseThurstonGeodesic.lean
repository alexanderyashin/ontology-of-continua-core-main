namespace OCMinimalObligationSpine

universe u

/-!
Q015 dense Thurston-geodesic terminal gate.

The frozen AIM target is:

  Is there a dense Thurston geodesic in moduli space?

This file keeps that target intact.  Dense Teichmuller geodesics, dense
grafting rays, asymptoticity statements and generic successor rays are useful
research evidence only after an explicit promotion theorem proves that the
same ray is a Thurston geodesic in the relevant moduli-space projection.
-/

/--
Typed domain for the Q015 target.

`Ray` is deliberately abstract.  The point of this gate is not to encode all of
Teichmuller theory in one file; it is to prevent the release machine from
counting an adjacent dense ray structure as the exact Thurston-geodesic target
without a promotion payload.
-/
structure Q015DenseThurstonGeodesicDomain where
  Ray : Type u
  thurstonGeodesic : Ray → Prop
  denseProjectionToModuli : Ray → Prop
  graftingRay : Ray → Prop
  teichmullerComparisonRay : Ray → Prop
  asymptoticToDenseTeichmullerGeodesic : Ray → Prop

/-- The full frozen Q015 target. -/
def Q015FullPositiveTarget (D : Q015DenseThurstonGeodesicDomain.{u}) : Prop :=
  ∃ γ : D.Ray,
    D.thurstonGeodesic γ ∧
    D.denseProjectionToModuli γ

/-- Direct construction payload for the exact Q015 target. -/
structure Q015DirectPositiveConstruction
    (D : Q015DenseThurstonGeodesicDomain.{u}) where
  γ : D.Ray
  thurston_geodesic : D.thurstonGeodesic γ
  dense_projection : D.denseProjectionToModuli γ

/-- A direct dense Thurston geodesic closes the full Q015 positive target. -/
theorem q015_full_target_of_direct_positive_construction
    {D : Q015DenseThurstonGeodesicDomain.{u}}
    (C : Q015DirectPositiveConstruction D) :
    Q015FullPositiveTarget D := by
  exact ⟨C.γ, C.thurston_geodesic, C.dense_projection⟩

/-- Direct obstruction payload for a negative answer to the exact Q015 target. -/
structure Q015DirectObstruction
    (D : Q015DenseThurstonGeodesicDomain.{u}) where
  no_dense_thurston_geodesic :
    ∀ γ : D.Ray,
      D.thurstonGeodesic γ →
      ¬ D.denseProjectionToModuli γ

/-- A direct obstruction refutes the full Q015 positive target. -/
theorem q015_no_full_target_of_direct_obstruction
    {D : Q015DenseThurstonGeodesicDomain.{u}}
    (O : Q015DirectObstruction D) :
    ¬ Q015FullPositiveTarget D := by
  intro h
  rcases h with ⟨γ, h_thurston, h_dense⟩
  exact O.no_dense_thurston_geodesic γ h_thurston h_dense

/--
Dense grafting-ray successor evidence.

This records the known successor shape without promoting it to Q015.  It
becomes terminal only after a separate proof that the exact ray is also a
Thurston geodesic in the target sense.
-/
structure Q015DenseGraftingRaySuccessor
    (D : Q015DenseThurstonGeodesicDomain.{u}) where
  γ : D.Ray
  grafting_ray : D.graftingRay γ
  dense_projection : D.denseProjectionToModuli γ

/--
Promotion data from a dense grafting ray to the exact Thurston-geodesic target.

The promotion is intentionally explicit: density alone is not enough; the same
ray must be certified as a Thurston geodesic.
-/
structure Q015GraftingRayPromotionPayload
    (D : Q015DenseThurstonGeodesicDomain.{u})
    (G : Q015DenseGraftingRaySuccessor D) where
  grafting_ray_is_thurston_geodesic : D.thurstonGeodesic G.γ

/-- A promoted dense grafting ray is a direct Q015 positive construction. -/
def q015_direct_positive_construction_of_promoted_grafting_ray
    {D : Q015DenseThurstonGeodesicDomain.{u}}
    (G : Q015DenseGraftingRaySuccessor D)
    (P : Q015GraftingRayPromotionPayload D G) :
    Q015DirectPositiveConstruction D :=
  { γ := G.γ
    thurston_geodesic := P.grafting_ray_is_thurston_geodesic
    dense_projection := G.dense_projection }

/-- A promoted dense grafting ray proves the full Q015 target. -/
theorem q015_full_target_of_promoted_grafting_ray
    {D : Q015DenseThurstonGeodesicDomain.{u}}
    (G : Q015DenseGraftingRaySuccessor D)
    (P : Q015GraftingRayPromotionPayload D G) :
    Q015FullPositiveTarget D :=
  q015_full_target_of_direct_positive_construction
    (q015_direct_positive_construction_of_promoted_grafting_ray G P)

/--
Dense Teichmuller comparison evidence.

Masur-style comparison or asymptoticity evidence is a source anchor for a
research route.  It is not a Q015 closure unless an explicit transfer theorem
certifies the same ray as a dense Thurston geodesic.
-/
structure Q015TeichmullerComparisonEvidence
    (D : Q015DenseThurstonGeodesicDomain.{u}) where
  γ : D.Ray
  comparison_ray : D.teichmullerComparisonRay γ
  asymptotic_to_dense_teichmuller_geodesic :
    D.asymptoticToDenseTeichmullerGeodesic γ
  dense_projection : D.denseProjectionToModuli γ

/-- Transfer payload from Teichmuller comparison evidence to Q015. -/
structure Q015TeichmullerToThurstonTransferPayload
    (D : Q015DenseThurstonGeodesicDomain.{u})
    (T : Q015TeichmullerComparisonEvidence D) where
  comparison_ray_is_thurston_geodesic : D.thurstonGeodesic T.γ

/-- A transferred Teichmuller comparison ray is a direct Q015 construction. -/
def q015_direct_positive_construction_of_teichmuller_transfer
    {D : Q015DenseThurstonGeodesicDomain.{u}}
    (T : Q015TeichmullerComparisonEvidence D)
    (P : Q015TeichmullerToThurstonTransferPayload D T) :
    Q015DirectPositiveConstruction D :=
  { γ := T.γ
    thurston_geodesic := P.comparison_ray_is_thurston_geodesic
    dense_projection := T.dense_projection }

/--
The terminal payload is exactly one of the two honest Q015 routes: construct a
dense Thurston geodesic, or prove a full obstruction.
-/
def Q015TerminalPayload (D : Q015DenseThurstonGeodesicDomain.{u}) : Prop :=
  Nonempty (Q015DirectPositiveConstruction D) ∨
  Nonempty (Q015DirectObstruction D)

/-- The terminal payload decides the full frozen Q015 target without lowering it. -/
theorem q015_full_target_decided_by_terminal_payload
    {D : Q015DenseThurstonGeodesicDomain.{u}}
    (P : Q015TerminalPayload D) :
    Q015FullPositiveTarget D ∨ ¬ Q015FullPositiveTarget D := by
  rcases P with h_positive | h_negative
  · rcases h_positive with ⟨C⟩
    exact Or.inl (q015_full_target_of_direct_positive_construction C)
  · rcases h_negative with ⟨O⟩
    exact Or.inr (q015_no_full_target_of_direct_obstruction O)

end OCMinimalObligationSpine
