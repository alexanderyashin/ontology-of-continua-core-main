namespace OCMinimalObligationSpine

universe u

/-!
Q054_05 André/Yan supercharacter-theory characterization gate.

The frozen problem asks to characterize the André/Yan supercharacter theory
"along the lines of the previous problem".  This gate keeps both parts of the
target: the André/Yan object itself and the required characterization style
inherited from the previous problem.  A basic-pair, cluster, or general
algebra-group structural description is evidence only after it is proved to be
complete, equivalent, and in the required style.
-/

/-- Abstract domain for André/Yan supercharacter-theory characterization. -/
structure Q05405SupercharacterDomain where
  CandidateTheory : Type u
  andreYanSupercharacterTheory : CandidateTheory → Prop
  previousProblemStyleCharacterization : CandidateTheory → Prop
  basicPairClusterStructure : CandidateTheory → Prop
  generalAlgebraGroupExtension : CandidateTheory → Prop
  completeEquivalentCharacterization : CandidateTheory → Prop

/--
The full frozen target: an André/Yan supercharacter theory equipped with a
complete equivalent characterization in the style demanded by the previous
problem.
-/
def Q05405FullCharacterizationTarget
    (D : Q05405SupercharacterDomain.{u}) : Prop :=
  ∃ T : D.CandidateTheory,
    D.andreYanSupercharacterTheory T ∧
    D.previousProblemStyleCharacterization T ∧
    D.completeEquivalentCharacterization T

/-- Direct positive payload for the full characterization target. -/
structure Q05405DirectCharacterizationPackage
    (D : Q05405SupercharacterDomain.{u}) where
  T : D.CandidateTheory
  andre_yan_theory : D.andreYanSupercharacterTheory T
  previous_problem_style : D.previousProblemStyleCharacterization T
  complete_equivalent_characterization : D.completeEquivalentCharacterization T

/-- A direct characterization package proves the full target. -/
theorem q05405_full_target_of_direct_characterization_package
    {D : Q05405SupercharacterDomain.{u}}
    (P : Q05405DirectCharacterizationPackage D) :
    Q05405FullCharacterizationTarget D := by
  exact
    ⟨P.T, P.andre_yan_theory, P.previous_problem_style,
      P.complete_equivalent_characterization⟩

/--
Basic-pair/cluster successor evidence.

This is the currently recorded successor/context lane.  It is not terminal
until promoted to a complete equivalent characterization in the required style.
-/
structure Q05405BasicPairClusterSuccessor
    (D : Q05405SupercharacterDomain.{u}) where
  T : D.CandidateTheory
  andre_yan_theory : D.andreYanSupercharacterTheory T
  basic_pair_cluster_structure : D.basicPairClusterStructure T

/-- Promotion payload from the basic-pair/cluster lane to the full target. -/
structure Q05405BasicPairClusterPromotionPayload
    (D : Q05405SupercharacterDomain.{u})
    (S : Q05405BasicPairClusterSuccessor D) where
  previous_problem_style : D.previousProblemStyleCharacterization S.T
  complete_equivalent_characterization :
    D.completeEquivalentCharacterization S.T

/-- A promoted basic-pair/cluster package becomes a direct characterization. -/
def q05405_direct_characterization_of_promoted_basic_pair_cluster
    {D : Q05405SupercharacterDomain.{u}}
    (S : Q05405BasicPairClusterSuccessor D)
    (P : Q05405BasicPairClusterPromotionPayload D S) :
    Q05405DirectCharacterizationPackage D :=
  { T := S.T
    andre_yan_theory := S.andre_yan_theory
    previous_problem_style := P.previous_problem_style
    complete_equivalent_characterization :=
      P.complete_equivalent_characterization }

/-- General algebra-group extension evidence is non-terminal without promotion. -/
structure Q05405GeneralAlgebraGroupExtensionEvidence
    (D : Q05405SupercharacterDomain.{u}) where
  T : D.CandidateTheory
  algebra_group_extension : D.generalAlgebraGroupExtension T

/-- Direct obstruction payload for a negative answer to the frozen target. -/
structure Q05405DirectObstruction
    (D : Q05405SupercharacterDomain.{u}) where
  no_full_characterization :
    ¬ Q05405FullCharacterizationTarget D

/-- A direct obstruction refutes the full characterization target. -/
theorem q05405_no_full_target_of_direct_obstruction
    {D : Q05405SupercharacterDomain.{u}}
    (O : Q05405DirectObstruction D) :
    ¬ Q05405FullCharacterizationTarget D := by
  exact O.no_full_characterization

/-- The terminal payload is a positive characterization or a direct obstruction. -/
def Q05405TerminalPayload (D : Q05405SupercharacterDomain.{u}) : Prop :=
  Nonempty (Q05405DirectCharacterizationPackage D) ∨
  Nonempty (Q05405DirectObstruction D)

/-- The terminal payload decides the full frozen Q054_05 target. -/
theorem q05405_full_target_decided_by_terminal_payload
    {D : Q05405SupercharacterDomain.{u}}
    (P : Q05405TerminalPayload D) :
    Q05405FullCharacterizationTarget D ∨
      ¬ Q05405FullCharacterizationTarget D := by
  rcases P with h_positive | h_negative
  · rcases h_positive with ⟨C⟩
    exact Or.inl (q05405_full_target_of_direct_characterization_package C)
  · rcases h_negative with ⟨O⟩
    exact Or.inr (q05405_no_full_target_of_direct_obstruction O)

end OCMinimalObligationSpine
