namespace OCMinimalObligationSpine.K2SpotOnAuditedReanalysisCertificate

/-!
# Exact certificate for the audited Spot-On reanalysis

This file certifies the finite arithmetic projection emitted by the deterministic
Python replay.  It does not prove that the statistical design is universally
valid, does not turn four replicate days into five-sigma evidence, and does not
close K2 or Ontology of Continua.  The public verifier separately recomputes the
JSON hash, dataset identity, protocol hash, and this Lean source.
-/

structure AuditedReanalysisCertificate where
  datasetMd5 : String
  protocolSha256 : String
  resultSha256 : String
  independentReplicateDayTotal : Nat
  positiveDayTotal : Nat
  exactSignPValueNumerator : Nat
  exactSignPValueDenominator : Nat
  day1ImprovementPicoUm4 : Int
  day2ImprovementPicoUm4 : Int
  day3ImprovementPicoUm4 : Int
  day4ImprovementPicoUm4 : Int
  fiveSigmaClaimAllowed : Bool
  claimClosureAllowed : Bool

def spotOnAuditedReanalysisCertificate : AuditedReanalysisCertificate where
  datasetMd5 := "a7c63635214bfa786cffda49d1a71f0f"
  protocolSha256 := "4e77008bb11dc6d59aa8de257a1e475af093c99b372f5fc692263502a3e74d6a"
  resultSha256 := "c9a1c379be3a3fef1a3cc8e7d93f259950bf42885c7cf79b2bc8513516cee473"
  independentReplicateDayTotal := 4
  positiveDayTotal := 4
  exactSignPValueNumerator := 1
  exactSignPValueDenominator := 8
  day1ImprovementPicoUm4 := 493870376
  day2ImprovementPicoUm4 := 347946783
  day3ImprovementPicoUm4 := 414731139
  day4ImprovementPicoUm4 := 454159485
  fiveSigmaClaimAllowed := false
  claimClosureAllowed := false

theorem four_independent_days_recorded :
    spotOnAuditedReanalysisCertificate.independentReplicateDayTotal = 4 := by
  rfl

theorem all_four_day_level_improvements_are_positive :
    0 < spotOnAuditedReanalysisCertificate.day1ImprovementPicoUm4 ∧
    0 < spotOnAuditedReanalysisCertificate.day2ImprovementPicoUm4 ∧
    0 < spotOnAuditedReanalysisCertificate.day3ImprovementPicoUm4 ∧
    0 < spotOnAuditedReanalysisCertificate.day4ImprovementPicoUm4 := by
  decide

theorem exact_four_of_four_sign_p_value_is_one_eighth :
    spotOnAuditedReanalysisCertificate.exactSignPValueNumerator = 1 ∧
    spotOnAuditedReanalysisCertificate.exactSignPValueDenominator = 8 := by
  exact ⟨rfl, rfl⟩

theorem audited_reanalysis_does_not_authorize_claim_closure :
    spotOnAuditedReanalysisCertificate.fiveSigmaClaimAllowed = false ∧
    spotOnAuditedReanalysisCertificate.claimClosureAllowed = false := by
  exact ⟨rfl, rfl⟩

end OCMinimalObligationSpine.K2SpotOnAuditedReanalysisCertificate
