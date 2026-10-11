namespace OCMinimalObligationSpine

inductive RouteDecision where
  | noPressure
  | sameKRepairFirst
  | pressureCurrentK
  | minimalAdmissibleAxisCandidate
  | collapseCandidate
  | blockedUndetermined
  | invalidBareDifferencePressureClaim
  | invalidMSpaceCreatedPressureClaim
  | invalidInadmissibleAxisClaim
  | invalidNonminimalAxisClaim
  | invalidLowerKUnboundAxisClaim
  | invalidPublicTheoremClaim
  deriving DecidableEq, Repr

structure OCObligationAudit where
  hasDifference : Bool
  activeDemand : Bool
  expressibleInCurrentK : Bool
  sameKRepairable : Bool
  mSpaceFilterPresent : Bool
  selectedAdmissible : Bool
  selectedResolvesPressure : Bool
  selectedMinimal : Bool
  lowerKConstraintsBound : Bool
  projectionLossWitness : Bool
  collapseAllowed : Bool
  claimsPressureFromBareDifference : Bool
  claimsMSpaceCreatesPressure : Bool
  claimsAxisFromBareDifference : Bool
  claimsPublicTheorem : Bool
  deriving DecidableEq, Repr

def Expressible (a : OCObligationAudit) : Bool :=
  a.expressibleInCurrentK

def SameKRepairable (a : OCObligationAudit) : Bool :=
  a.sameKRepairable

def Pressure (a : OCObligationAudit) : Bool :=
  a.activeDemand && !Expressible a && !SameKRepairable a

def MAdmissibleRoute (a : OCObligationAudit) : Bool :=
  Pressure a &&
    a.mSpaceFilterPresent &&
    a.selectedAdmissible &&
    a.selectedResolvesPressure &&
    a.selectedMinimal &&
    a.lowerKConstraintsBound &&
    a.projectionLossWitness

def decideRoute (a : OCObligationAudit) : RouteDecision :=
  if a.claimsPublicTheorem then
    RouteDecision.invalidPublicTheoremClaim
  else if a.claimsMSpaceCreatesPressure && !Pressure a then
    RouteDecision.invalidMSpaceCreatedPressureClaim
  else if a.claimsPressureFromBareDifference && !Pressure a then
    RouteDecision.invalidBareDifferencePressureClaim
  else if a.claimsAxisFromBareDifference && !Pressure a then
    RouteDecision.invalidBareDifferencePressureClaim
  else if SameKRepairable a then
    RouteDecision.sameKRepairFirst
  else if !Pressure a then
    RouteDecision.noPressure
  else if a.selectedResolvesPressure && !a.selectedAdmissible then
    RouteDecision.invalidInadmissibleAxisClaim
  else if a.selectedAdmissible && a.selectedResolvesPressure && !a.selectedMinimal then
    RouteDecision.invalidNonminimalAxisClaim
  else if a.selectedAdmissible && a.selectedResolvesPressure && !a.lowerKConstraintsBound then
    RouteDecision.invalidLowerKUnboundAxisClaim
  else if MAdmissibleRoute a then
    RouteDecision.minimalAdmissibleAxisCandidate
  else if a.collapseAllowed then
    RouteDecision.collapseCandidate
  else
    RouteDecision.blockedUndetermined

def bareDifferencePressureClaim : OCObligationAudit :=
  { hasDifference := true, activeDemand := false, expressibleInCurrentK := false,
    sameKRepairable := false, mSpaceFilterPresent := false, selectedAdmissible := false,
    selectedResolvesPressure := false, selectedMinimal := false, lowerKConstraintsBound := false,
    projectionLossWitness := false, collapseAllowed := false,
    claimsPressureFromBareDifference := true, claimsMSpaceCreatesPressure := false,
    claimsAxisFromBareDifference := false, claimsPublicTheorem := false }

def expressibleDifference : OCObligationAudit :=
  { hasDifference := true, activeDemand := true, expressibleInCurrentK := true,
    sameKRepairable := false, mSpaceFilterPresent := false, selectedAdmissible := false,
    selectedResolvesPressure := false, selectedMinimal := false, lowerKConstraintsBound := false,
    projectionLossWitness := false, collapseAllowed := false,
    claimsPressureFromBareDifference := false, claimsMSpaceCreatesPressure := false,
    claimsAxisFromBareDifference := false, claimsPublicTheorem := false }

def inactiveDifference : OCObligationAudit :=
  { hasDifference := true, activeDemand := false, expressibleInCurrentK := false,
    sameKRepairable := false, mSpaceFilterPresent := false, selectedAdmissible := false,
    selectedResolvesPressure := false, selectedMinimal := false, lowerKConstraintsBound := false,
    projectionLossWitness := false, collapseAllowed := false,
    claimsPressureFromBareDifference := false, claimsMSpaceCreatesPressure := false,
    claimsAxisFromBareDifference := false, claimsPublicTheorem := false }

def sameKRepairCase : OCObligationAudit :=
  { hasDifference := true, activeDemand := true, expressibleInCurrentK := false,
    sameKRepairable := true, mSpaceFilterPresent := false, selectedAdmissible := false,
    selectedResolvesPressure := false, selectedMinimal := false, lowerKConstraintsBound := false,
    projectionLossWitness := false, collapseAllowed := false,
    claimsPressureFromBareDifference := false, claimsMSpaceCreatesPressure := false,
    claimsAxisFromBareDifference := false, claimsPublicTheorem := false }

def pressureOnly : OCObligationAudit :=
  { hasDifference := true, activeDemand := true, expressibleInCurrentK := false,
    sameKRepairable := false, mSpaceFilterPresent := false, selectedAdmissible := false,
    selectedResolvesPressure := false, selectedMinimal := false, lowerKConstraintsBound := false,
    projectionLossWitness := false, collapseAllowed := false,
    claimsPressureFromBareDifference := false, claimsMSpaceCreatesPressure := false,
    claimsAxisFromBareDifference := false, claimsPublicTheorem := false }

def mSpaceCreatedPressureClaim : OCObligationAudit :=
  { hasDifference := true, activeDemand := true, expressibleInCurrentK := true,
    sameKRepairable := false, mSpaceFilterPresent := true, selectedAdmissible := true,
    selectedResolvesPressure := true, selectedMinimal := true, lowerKConstraintsBound := true,
    projectionLossWitness := true, collapseAllowed := false,
    claimsPressureFromBareDifference := false, claimsMSpaceCreatesPressure := true,
    claimsAxisFromBareDifference := false, claimsPublicTheorem := false }

def inadmissibleAxisClaim : OCObligationAudit :=
  { hasDifference := true, activeDemand := true, expressibleInCurrentK := false,
    sameKRepairable := false, mSpaceFilterPresent := true, selectedAdmissible := false,
    selectedResolvesPressure := true, selectedMinimal := true, lowerKConstraintsBound := true,
    projectionLossWitness := true, collapseAllowed := false,
    claimsPressureFromBareDifference := false, claimsMSpaceCreatesPressure := false,
    claimsAxisFromBareDifference := false, claimsPublicTheorem := false }

def nonminimalAxisClaim : OCObligationAudit :=
  { hasDifference := true, activeDemand := true, expressibleInCurrentK := false,
    sameKRepairable := false, mSpaceFilterPresent := true, selectedAdmissible := true,
    selectedResolvesPressure := true, selectedMinimal := false, lowerKConstraintsBound := true,
    projectionLossWitness := true, collapseAllowed := false,
    claimsPressureFromBareDifference := false, claimsMSpaceCreatesPressure := false,
    claimsAxisFromBareDifference := false, claimsPublicTheorem := false }

def lowerKUnboundAxisClaim : OCObligationAudit :=
  { hasDifference := true, activeDemand := true, expressibleInCurrentK := false,
    sameKRepairable := false, mSpaceFilterPresent := true, selectedAdmissible := true,
    selectedResolvesPressure := true, selectedMinimal := true, lowerKConstraintsBound := false,
    projectionLossWitness := true, collapseAllowed := false,
    claimsPressureFromBareDifference := false, claimsMSpaceCreatesPressure := false,
    claimsAxisFromBareDifference := false, claimsPublicTheorem := false }

def minimalAdmissibleAxisCandidate : OCObligationAudit :=
  { hasDifference := true, activeDemand := true, expressibleInCurrentK := false,
    sameKRepairable := false, mSpaceFilterPresent := true, selectedAdmissible := true,
    selectedResolvesPressure := true, selectedMinimal := true, lowerKConstraintsBound := true,
    projectionLossWitness := true, collapseAllowed := false,
    claimsPressureFromBareDifference := false, claimsMSpaceCreatesPressure := false,
    claimsAxisFromBareDifference := false, claimsPublicTheorem := false }

def collapseCase : OCObligationAudit :=
  { hasDifference := true, activeDemand := true, expressibleInCurrentK := false,
    sameKRepairable := false, mSpaceFilterPresent := false, selectedAdmissible := false,
    selectedResolvesPressure := false, selectedMinimal := false, lowerKConstraintsBound := false,
    projectionLossWitness := false, collapseAllowed := true,
    claimsPressureFromBareDifference := false, claimsMSpaceCreatesPressure := false,
    claimsAxisFromBareDifference := false, claimsPublicTheorem := false }

def publicTheoremClaim : OCObligationAudit :=
  { hasDifference := true, activeDemand := true, expressibleInCurrentK := false,
    sameKRepairable := false, mSpaceFilterPresent := true, selectedAdmissible := true,
    selectedResolvesPressure := true, selectedMinimal := true, lowerKConstraintsBound := true,
    projectionLossWitness := true, collapseAllowed := false,
    claimsPressureFromBareDifference := false, claimsMSpaceCreatesPressure := false,
    claimsAxisFromBareDifference := false, claimsPublicTheorem := true }

theorem bare_difference_is_not_pressure :
    decideRoute bareDifferencePressureClaim = RouteDecision.invalidBareDifferencePressureClaim := by
  rfl

theorem inactive_difference_has_no_pressure :
    decideRoute inactiveDifference = RouteDecision.noPressure := by
  rfl

theorem expressible_current_k_blocks_pressure :
    decideRoute expressibleDifference = RouteDecision.noPressure := by
  rfl

theorem same_k_repair_blocks_growth :
    decideRoute sameKRepairCase = RouteDecision.sameKRepairFirst := by
  rfl

theorem pressure_is_current_k_before_m_space :
    decideRoute pressureOnly = RouteDecision.blockedUndetermined := by
  rfl

theorem m_space_cannot_create_pressure :
    decideRoute mSpaceCreatedPressureClaim = RouteDecision.invalidMSpaceCreatedPressureClaim := by
  rfl

theorem inadmissible_axis_claim_is_invalid :
    decideRoute inadmissibleAxisClaim = RouteDecision.invalidInadmissibleAxisClaim := by
  rfl

theorem nonminimal_axis_claim_is_invalid :
    decideRoute nonminimalAxisClaim = RouteDecision.invalidNonminimalAxisClaim := by
  rfl

theorem lower_k_unbound_axis_claim_is_invalid :
    decideRoute lowerKUnboundAxisClaim = RouteDecision.invalidLowerKUnboundAxisClaim := by
  rfl

theorem minimal_admissible_axis_is_only_candidate :
    decideRoute minimalAdmissibleAxisCandidate = RouteDecision.minimalAdmissibleAxisCandidate := by
  rfl

theorem collapse_requires_pressure_but_no_admissible_growth :
    decideRoute collapseCase = RouteDecision.collapseCandidate := by
  rfl

theorem public_theorem_claim_is_invalid :
    decideRoute publicTheoremClaim = RouteDecision.invalidPublicTheoremClaim := by
  rfl

/--
Publication-facing closure package for the minimal obligation spine decision
table.  The numeric replay may be counted as a release artifact only when it
matches this complete Lean table rather than merely producing green Python
rows.
-/
structure MinimalSpineDecisionTablePublicationPackage : Prop where
  bare_difference_rejected :
    decideRoute bareDifferencePressureClaim =
      RouteDecision.invalidBareDifferencePressureClaim
  inactive_difference_has_no_pressure :
    decideRoute inactiveDifference = RouteDecision.noPressure
  expressible_current_k_blocks_pressure :
    decideRoute expressibleDifference = RouteDecision.noPressure
  same_k_repair_blocks_growth :
    decideRoute sameKRepairCase = RouteDecision.sameKRepairFirst
  pressure_only_blocks_as_undetermined :
    decideRoute pressureOnly = RouteDecision.blockedUndetermined
  m_space_created_pressure_rejected :
    decideRoute mSpaceCreatedPressureClaim =
      RouteDecision.invalidMSpaceCreatedPressureClaim
  inadmissible_axis_rejected :
    decideRoute inadmissibleAxisClaim =
      RouteDecision.invalidInadmissibleAxisClaim
  nonminimal_axis_rejected :
    decideRoute nonminimalAxisClaim =
      RouteDecision.invalidNonminimalAxisClaim
  lower_k_unbound_axis_rejected :
    decideRoute lowerKUnboundAxisClaim =
      RouteDecision.invalidLowerKUnboundAxisClaim
  minimal_axis_admitted :
    decideRoute minimalAdmissibleAxisCandidate =
      RouteDecision.minimalAdmissibleAxisCandidate
  collapse_candidate_retained :
    decideRoute collapseCase = RouteDecision.collapseCandidate
  public_theorem_overclaim_rejected :
    decideRoute publicTheoremClaim =
      RouteDecision.invalidPublicTheoremClaim

/-- The complete minimal-spine decision table is closed for publication. -/
theorem minimal_spine_decision_table_publication_package_closed :
    MinimalSpineDecisionTablePublicationPackage := by
  exact {
    bare_difference_rejected := bare_difference_is_not_pressure
    inactive_difference_has_no_pressure := inactive_difference_has_no_pressure
    expressible_current_k_blocks_pressure := expressible_current_k_blocks_pressure
    same_k_repair_blocks_growth := same_k_repair_blocks_growth
    pressure_only_blocks_as_undetermined := pressure_is_current_k_before_m_space
    m_space_created_pressure_rejected := m_space_cannot_create_pressure
    inadmissible_axis_rejected := inadmissible_axis_claim_is_invalid
    nonminimal_axis_rejected := nonminimal_axis_claim_is_invalid
    lower_k_unbound_axis_rejected := lower_k_unbound_axis_claim_is_invalid
    minimal_axis_admitted := minimal_admissible_axis_is_only_candidate
    collapse_candidate_retained := collapse_requires_pressure_but_no_admissible_growth
    public_theorem_overclaim_rejected := public_theorem_claim_is_invalid
  }

end OCMinimalObligationSpine
