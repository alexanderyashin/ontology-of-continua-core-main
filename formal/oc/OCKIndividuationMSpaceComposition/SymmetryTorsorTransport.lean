import OCKIndividuationMSpaceComposition.SymmetryObservableDichotomy

namespace OCKIndividuationMSpaceComposition

universe uSource uSourceAxis uSourceIdentity
  uTarget uTargetAxis uTargetIdentity

/-!
# Equivariant transport between R3 torsors

An equivariant map between two free transitive C₂ torsors is automatically a
bijection.  It is completely determined by the image of one source basepoint.
After choosing one target basepoint there are exactly two such maps, exchanged
by target reversal.

The torsor structure is therefore canonically transportable up to a unique
global sign reversal, while no pointed orientation is selected canonically.
-/

/-- A map between R3 carriers which intertwines their reversals. -/
structure R3EquivariantMap
    {Source : Type uSource} {SourceAxis : Type uSourceAxis}
    {SourceIdentity : Type uSourceIdentity}
    {Target : Type uTarget} {TargetAxis : Type uTargetAxis}
    {TargetIdentity : Type uTargetIdentity}
    (source : R3C2OrientationTorsorInterface
      Source SourceAxis SourceIdentity)
    (target : R3C2OrientationTorsorInterface
      Target TargetAxis TargetIdentity) where
  toFun : Source → Target
  equivariant : ∀ orientation,
    toFun (source.reverse orientation) = target.reverse (toFun orientation)

instance
    {Source : Type uSource} {SourceAxis : Type uSourceAxis}
    {SourceIdentity : Type uSourceIdentity}
    {Target : Type uTarget} {TargetAxis : Type uTargetAxis}
    {TargetIdentity : Type uTargetIdentity}
    {source : R3C2OrientationTorsorInterface
      Source SourceAxis SourceIdentity}
    {target : R3C2OrientationTorsorInterface
      Target TargetAxis TargetIdentity} :
    CoeFun (R3EquivariantMap source target) (fun _ => Source → Target) :=
  ⟨R3EquivariantMap.toFun⟩

/-- Equivariance and target freeness force injectivity. -/
theorem r3EquivariantMap_injective
    {Source : Type uSource} {SourceAxis : Type uSourceAxis}
    {SourceIdentity : Type uSourceIdentity}
    {Target : Type uTarget} {TargetAxis : Type uTargetAxis}
    {TargetIdentity : Type uTargetIdentity}
    {source : R3C2OrientationTorsorInterface
      Source SourceAxis SourceIdentity}
    {target : R3C2OrientationTorsorInterface
      Target TargetAxis TargetIdentity}
    (map : R3EquivariantMap source target) :
    Function.Injective map := by
  intro left right equality
  rcases source.pairTransitive left right with same | partner
  · exact same.symm
  · subst right
    exfalso
    exact target.reverseFree (map left)
      ((map.equivariant left).symm.trans equality.symm)

/-- Pair transitivity in the target forces surjectivity. -/
theorem r3EquivariantMap_surjective
    {Source : Type uSource} {SourceAxis : Type uSourceAxis}
    {SourceIdentity : Type uSourceIdentity}
    {Target : Type uTarget} {TargetAxis : Type uTargetAxis}
    {TargetIdentity : Type uTargetIdentity}
    {source : R3C2OrientationTorsorInterface
      Source SourceAxis SourceIdentity}
    {target : R3C2OrientationTorsorInterface
      Target TargetAxis TargetIdentity}
    (map : R3EquivariantMap source target) (sourceBase : Source) :
    Function.Surjective map := by
  intro targetPoint
  rcases target.pairTransitive (map sourceBase) targetPoint with same | partner
  · exact ⟨sourceBase, same.symm⟩
  · refine ⟨source.reverse sourceBase, ?_⟩
    calc
      map (source.reverse sourceBase) = target.reverse (map sourceBase) :=
        map.equivariant sourceBase
      _ = targetPoint := partner.symm

/-- Every equivariant map is an equivalence. -/
noncomputable def r3EquivariantMapEquiv
    {Source : Type uSource} {SourceAxis : Type uSourceAxis}
    {SourceIdentity : Type uSourceIdentity}
    {Target : Type uTarget} {TargetAxis : Type uTargetAxis}
    {TargetIdentity : Type uTargetIdentity}
    {source : R3C2OrientationTorsorInterface
      Source SourceAxis SourceIdentity}
    {target : R3C2OrientationTorsorInterface
      Target TargetAxis TargetIdentity}
    (map : R3EquivariantMap source target) (sourceBase : Source) :
    Source ≃ Target :=
  Equiv.ofBijective map
    ⟨r3EquivariantMap_injective map,
      r3EquivariantMap_surjective map sourceBase⟩

/-- An equivariant map is determined by the image of one source basepoint. -/
theorem r3EquivariantMap_ext_at_base
    {Source : Type uSource} {SourceAxis : Type uSourceAxis}
    {SourceIdentity : Type uSourceIdentity}
    {Target : Type uTarget} {TargetAxis : Type uTargetAxis}
    {TargetIdentity : Type uTargetIdentity}
    {source : R3C2OrientationTorsorInterface
      Source SourceAxis SourceIdentity}
    {target : R3C2OrientationTorsorInterface
      Target TargetAxis TargetIdentity}
    (sourceBase : Source) (first second : R3EquivariantMap source target)
    (atBase : first sourceBase = second sourceBase) :
    first = second := by
  cases first with
  | mk first firstEquivariant =>
      cases second with
      | mk second secondEquivariant =>
          congr
          funext orientation
          rcases source.pairTransitive sourceBase orientation with same | partner
          · subst orientation
            exact atBase
          · subst orientation
            calc
              first (source.reverse sourceBase) =
                  target.reverse (first sourceBase) :=
                firstEquivariant sourceBase
              _ = target.reverse (second sourceBase) :=
                congrArg target.reverse atBase
              _ = second (source.reverse sourceBase) :=
                (secondEquivariant sourceBase).symm

/-- Coordinates produce an explicit equivalence sending the selected source
basepoint to the selected target basepoint. -/
noncomputable def r3PointedEquivariantEquiv
    {Source : Type uSource} {SourceAxis : Type uSourceAxis}
    {SourceIdentity : Type uSourceIdentity}
    {Target : Type uTarget} {TargetAxis : Type uTargetAxis}
    {TargetIdentity : Type uTargetIdentity}
    (source : R3C2OrientationTorsorInterface
      Source SourceAxis SourceIdentity)
    (target : R3C2OrientationTorsorInterface
      Target TargetAxis TargetIdentity)
    (sourceBase : Source) (targetBase : Target) : Source ≃ Target :=
  (r3OrientationEquivBool source sourceBase).trans
    (r3OrientationEquivBool target targetBase).symm

@[simp] theorem r3PointedEquivariantEquiv_base
    {Source : Type uSource} {SourceAxis : Type uSourceAxis}
    {SourceIdentity : Type uSourceIdentity}
    {Target : Type uTarget} {TargetAxis : Type uTargetAxis}
    {TargetIdentity : Type uTargetIdentity}
    (source : R3C2OrientationTorsorInterface
      Source SourceAxis SourceIdentity)
    (target : R3C2OrientationTorsorInterface
      Target TargetAxis TargetIdentity)
    (sourceBase : Source) (targetBase : Target) :
    r3PointedEquivariantEquiv source target sourceBase targetBase sourceBase =
      targetBase := by
  have inverseAtBase :=
    (r3OrientationEquivBool target targetBase).symm_apply_apply targetBase
  simpa [r3PointedEquivariantEquiv] using inverseAtBase

/-- The coordinate-built equivalence intertwines reversal. -/
theorem r3PointedEquivariantEquiv_reversal
    {Source : Type uSource} {SourceAxis : Type uSourceAxis}
    {SourceIdentity : Type uSourceIdentity}
    {Target : Type uTarget} {TargetAxis : Type uTargetAxis}
    {TargetIdentity : Type uTargetIdentity}
    (source : R3C2OrientationTorsorInterface
      Source SourceAxis SourceIdentity)
    (target : R3C2OrientationTorsorInterface
      Target TargetAxis TargetIdentity)
    (sourceBase : Source) (targetBase : Target) (orientation : Source) :
    r3PointedEquivariantEquiv source target sourceBase targetBase
        (source.reverse orientation) =
      target.reverse
        (r3PointedEquivariantEquiv source target sourceBase targetBase
          orientation) := by
  apply (r3OrientationEquivBool target targetBase).injective
  simp [r3PointedEquivariantEquiv, r3OrientationEquivBool_reverse]

/-- Package the pointed equivalence as an equivariant map. -/
noncomputable def r3PointedEquivariantMap
    {Source : Type uSource} {SourceAxis : Type uSourceAxis}
    {SourceIdentity : Type uSourceIdentity}
    {Target : Type uTarget} {TargetAxis : Type uTargetAxis}
    {TargetIdentity : Type uTargetIdentity}
    (source : R3C2OrientationTorsorInterface
      Source SourceAxis SourceIdentity)
    (target : R3C2OrientationTorsorInterface
      Target TargetAxis TargetIdentity)
    (sourceBase : Source) (targetBase : Target) :
    R3EquivariantMap source target where
  toFun := r3PointedEquivariantEquiv source target sourceBase targetBase
  equivariant := r3PointedEquivariantEquiv_reversal
    source target sourceBase targetBase

/-- Relative to a target basepoint, every equivariant map is exactly one of
the two pointed transports. -/
theorem r3EquivariantMap_eq_first_or_reversed_transport
    {Source : Type uSource} {SourceAxis : Type uSourceAxis}
    {SourceIdentity : Type uSourceIdentity}
    {Target : Type uTarget} {TargetAxis : Type uTargetAxis}
    {TargetIdentity : Type uTargetIdentity}
    {source : R3C2OrientationTorsorInterface
      Source SourceAxis SourceIdentity}
    {target : R3C2OrientationTorsorInterface
      Target TargetAxis TargetIdentity}
    (sourceBase : Source) (targetBase : Target)
    (map : R3EquivariantMap source target) :
    map = r3PointedEquivariantMap source target sourceBase targetBase ∨
      map = r3PointedEquivariantMap source target sourceBase
        (target.reverse targetBase) := by
  rcases target.pairTransitive targetBase (map sourceBase) with same | partner
  · left
    apply r3EquivariantMap_ext_at_base sourceBase
    change map.toFun sourceBase =
      r3PointedEquivariantEquiv source target sourceBase targetBase sourceBase
    rw [r3PointedEquivariantEquiv_base]
    exact same
  · right
    apply r3EquivariantMap_ext_at_base sourceBase
    change map.toFun sourceBase =
      r3PointedEquivariantEquiv source target sourceBase
        (target.reverse targetBase) sourceBase
    rw [r3PointedEquivariantEquiv_base]
    exact partner

/-- The two pointed transports are distinct. -/
theorem r3PointedEquivariantMap_ne_reversed
    {Source : Type uSource} {SourceAxis : Type uSourceAxis}
    {SourceIdentity : Type uSourceIdentity}
    {Target : Type uTarget} {TargetAxis : Type uTargetAxis}
    {TargetIdentity : Type uTargetIdentity}
    (source : R3C2OrientationTorsorInterface
      Source SourceAxis SourceIdentity)
    (target : R3C2OrientationTorsorInterface
      Target TargetAxis TargetIdentity)
    (sourceBase : Source) (targetBase : Target) :
    r3PointedEquivariantMap source target sourceBase targetBase ≠
      r3PointedEquivariantMap source target sourceBase
        (target.reverse targetBase) := by
  intro equality
  have atBase := congrArg
    (fun map : R3EquivariantMap source target => map sourceBase) equality
  simp [r3PointedEquivariantMap] at atBase
  exact target.reverseFree targetBase atBase.symm

end OCKIndividuationMSpaceComposition
