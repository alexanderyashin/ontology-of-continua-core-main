import OCMinimalObligationSpine.SameCarrierRepair

namespace OCMinimalObligationSpine

universe uCandidate

/--
A typed policy saying which already certified distinctions are active demands.
Activity is supplied by the caller; this formal layer does not manufacture a
demand from the mere existence of a distinction.
-/
abbrev ActiveDemand (K : CurrentK) := TrajectoryDistinction K -> Prop

/--
Pressure relative to an explicit repair-search scope: the distinction is
currently demanded, current K does not express it, and no admissible
architecture-preserving repair exists inside that declared scope.
-/
def IrreduciblePressureWithin
    {K : CurrentK}
    (search : RepairSearchClass.{uCandidate} K)
    (activeDemand : ActiveDemand K)
    (d : TrajectoryDistinction K) : Prop :=
  activeDemand d /\
    Not (Expresses K d) /\
      Not (RepairableWithin search d)

theorem irreduciblePressureWithin_intro
    {K : CurrentK}
    (search : RepairSearchClass.{uCandidate} K)
    (activeDemand : ActiveDemand K)
    (d : TrajectoryDistinction K)
    (demandIsActive : activeDemand d)
    (notExpressed : Not (Expresses K d))
    (notRepairable : Not (RepairableWithin search d)) :
    IrreduciblePressureWithin search activeDemand d := by
  exact ⟨demandIsActive, notExpressed, notRepairable⟩

theorem irreduciblePressureWithin_activeDemand
    {K : CurrentK}
    {search : RepairSearchClass.{uCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    (pressure : IrreduciblePressureWithin search activeDemand d) :
    activeDemand d :=
  pressure.1

theorem irreduciblePressureWithin_not_expresses
    {K : CurrentK}
    {search : RepairSearchClass.{uCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    (pressure : IrreduciblePressureWithin search activeDemand d) :
    Not (Expresses K d) :=
  pressure.2.1

theorem irreduciblePressureWithin_not_repairableWithin
    {K : CurrentK}
    {search : RepairSearchClass.{uCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    (pressure : IrreduciblePressureWithin search activeDemand d) :
    Not (RepairableWithin search d) :=
  pressure.2.2

theorem irreduciblePressureWithin_elim
    {K : CurrentK}
    {search : RepairSearchClass.{uCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {Conclusion : Prop}
    (pressure : IrreduciblePressureWithin search activeDemand d)
    (eliminate :
      activeDemand d ->
        Not (Expresses K d) ->
          Not (RepairableWithin search d) ->
            Conclusion) :
    Conclusion := by
  exact eliminate pressure.1 pressure.2.1 pressure.2.2

/-- A valid repair witness in the declared class contradicts pressure there. -/
theorem repairable_blocks_pressure
    {K : CurrentK}
    (search : RepairSearchClass.{uCandidate} K)
    (activeDemand : ActiveDemand K)
    (d : TrajectoryDistinction K)
    (repairable : RepairableWithin search d) :
    Not (IrreduciblePressureWithin search activeDemand d) := by
  intro pressure
  exact pressure.2.2 repairable

/-- Exact declared semantics already expresses every certified distinction. -/
theorem exact_declared_semantics_blocks_pressure
    {K : CurrentK}
    (search : RepairSearchClass.{uCandidate} K)
    (activeDemand : ActiveDemand K)
    (d : TrajectoryDistinction K)
    (exactSemantics : HasExactDeclaredSemantics K) :
    Not (IrreduciblePressureWithin search activeDemand d) := by
  intro pressure
  exact pressure.2.1
    (exact_declared_semantics_expresses K exactSemantics d)

/--
Backward scientific feedback: scoped pressure refutes exactness of the
particular decoder and encoded transition declared by current K.
-/
theorem irreduciblePressureWithin_refutes_exact_declared_semantics
    {K : CurrentK}
    {search : RepairSearchClass.{uCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    (pressure : IrreduciblePressureWithin search activeDemand d) :
    Not (HasExactDeclaredSemantics K) := by
  exact unexpressed_distinction_refutes_exact_declared_semantics
    K d pressure.2.1

end OCMinimalObligationSpine
