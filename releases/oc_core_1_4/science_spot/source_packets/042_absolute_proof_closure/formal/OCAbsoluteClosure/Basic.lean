namespace OCAbsoluteClosure

inductive TerminalStatus where
  | provedClosedWithProofs
  | refutedWithCounterproof
  | refutedRepairedAndProvedWithProofs
deriving DecidableEq, Repr

structure ClaimGate where
  exactStatement : Bool
  proofOrCounterproof : Bool
  artifactRef : Bool
  falsifier : Bool
  dependencyClosure : Bool
  verification : Bool
deriving DecidableEq, Repr

def claimClosed (g : ClaimGate) : Bool :=
  g.exactStatement &&
  g.proofOrCounterproof &&
  g.artifactRef &&
  g.falsifier &&
  g.dependencyClosure &&
  g.verification

theorem closed_has_statement (g : ClaimGate) (h : claimClosed g = true) :
    g.exactStatement = true := by
  unfold claimClosed at h
  cases g.exactStatement <;> simp at h

theorem closed_has_proof (g : ClaimGate) (h : claimClosed g = true) :
    g.proofOrCounterproof = true := by
  unfold claimClosed at h
  cases g.exactStatement <;> cases g.proofOrCounterproof <;> simp at h

theorem closed_has_artifact (g : ClaimGate) (h : claimClosed g = true) :
    g.artifactRef = true := by
  unfold claimClosed at h
  cases g.exactStatement <;> cases g.proofOrCounterproof <;> cases g.artifactRef <;> simp at h

theorem closed_has_falsifier (g : ClaimGate) (h : claimClosed g = true) :
    g.falsifier = true := by
  unfold claimClosed at h
  cases g.exactStatement <;> cases g.proofOrCounterproof <;> cases g.artifactRef <;> cases g.falsifier <;> simp at h

theorem closed_has_dependencies (g : ClaimGate) (h : claimClosed g = true) :
    g.dependencyClosure = true := by
  unfold claimClosed at h
  cases g.exactStatement <;> cases g.proofOrCounterproof <;> cases g.artifactRef <;> cases g.falsifier <;> cases g.dependencyClosure <;> simp at h

theorem closed_has_verification (g : ClaimGate) (h : claimClosed g = true) :
    g.verification = true := by
  unfold claimClosed at h
  cases g.exactStatement <;> cases g.proofOrCounterproof <;> cases g.artifactRef <;> cases g.falsifier <;> cases g.dependencyClosure <;> cases g.verification <;> simp at h

structure EmpiricalLedger where
  empiricalRows : Nat
  nonEmpiricalRows : Nat
deriving DecidableEq, Repr

def allRowsEmpirical (l : EmpiricalLedger) : Prop :=
  l.nonEmpiricalRows = 0

theorem nonempirical_row_refutes_all_empirical (l : EmpiricalLedger)
    (h : 0 < l.nonEmpiricalRows) : ¬ allRowsEmpirical l := by
  intro hall
  unfold allRowsEmpirical at hall
  omega

structure RepairGate where
  oldClaimGuard : Bool
  repairedStatement : Bool
  repairedProof : Bool
deriving DecidableEq, Repr

def repairedClosed (g : RepairGate) : Bool :=
  g.oldClaimGuard && g.repairedStatement && g.repairedProof

theorem repaired_has_guard (g : RepairGate) (h : repairedClosed g = true) :
    g.oldClaimGuard = true := by
  unfold repairedClosed at h
  cases g.oldClaimGuard <;> simp at h

end OCAbsoluteClosure
