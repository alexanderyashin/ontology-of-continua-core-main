# OC Core 1.3 | Supplementary Appendix

## Source-audit appendix with support-status table
- Primary PDF: Ontology of Continua — Core 1.2
- Version label: Version 1.2 — December 11, 2025
- Public tag: v1.2.1

## Exact Revised Main Result
- Theorem A (source-audited post-collapse identity classification): Within the surviving source-native OC Core kernel, once a continuum loses every admissible realization, the original continuum is dead, any surviving post-collapse structure is residue rather than a still-live instance of that continuum, and any later live continuum grounded in that residue is rebirth rather than persistence of the original one.

## Exact Positive Source Statements
- Definition 12.1 (Collapse): A continuum K collapses at time t* if the admissible state space becomes empty, continuumness decays to zero, and every candidate configuration violates at least one existence or stability threshold.
- Definition 12.3 (Internal collapse): Internal collapse occurs when collapse is caused solely by the internal evolution operator E = (F, G, H, Q, R, S, U) acting on K while the embedding space M remains structurally static over the relevant interval.
- Definition 12.4 (External collapse): External collapse occurs when the embedding space M changes so that no configuration of K remains compatible with the new constraints, even though the prior internal evolution stayed within the previously admissible region.
- Definition 12.5 (Residue): The residue of a collapsed continuum K is the set of structures in the embedding space that remain after `Ω(K)=∅`; residues may persist without preserving the original live identity.
- Definition 12.6 (Rebirth): A rebirth event occurs when, after the collapse of K, a new continuum K' appears while `Ω(K)=∅` and `k(K,t)=0`, inherits at least one structural element from residue, and satisfies the birth conditions for some level.
- Axiom 3.2 (Death condition): A continuum dies at time t* when Omega(K(t*)) = empty; after death the operators F, G, H, Q, R, S, and U are no longer defined for that continuum.
- Axiom 3.3 (Irreversibility of death): No operator acting within the same level can restore a dead continuum; any new live continuum is considered a new entity.

## Derived Lemma Spine
- Lemma 1 (Collapse entails death): If the admissible state space becomes empty, the original continuum is dead and cannot lawfully persist as a live continuum. Support: SOURCE_THEOREM_3_DEATH, 3.2, 12.1, 12.3, 12.4
- Lemma 2 (Post-collapse trace is residue): After collapse, any surviving structure is residue rather than a still-live instance of the original continuum. Support: SOURCE_THEOREM_3_DEATH, 3.2, 12.1, 12.3, 12.4, 12.5
- Lemma 3 (Later live continuum is rebirth): Any later live continuum grounded in residue is rebirth of a new continuum rather than persistence of the original one. Support: SOURCE_COROLLARY_3_2_IRREVERSIBILITY, 3.3, 12.5, 12.6

## Positive Support Table
| claim_ref | class | title | final_status | proof_status | terminal_fate | pdf_witness | public_tex_witness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ROOT_PRINCIPLE | THEOREM | Theorem A (source-audited post-collapse identity classification) | REVISED_AND_PROVED | PASS | REVISED_AND_PROVED | Composite PDF witness: Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.563 l.12; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.563 l.18; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.596 l.20; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.596 l.26; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.63 l.18; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.64 l.7; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.64 l.16; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.65 l.43; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.66 l.16 | Composite public TeX witness: GitHub tag v1.2.1 (2c61b78): content/04_results.tex; GitHub tag v1.2.1 (2c61b78): appendix/B_axioms_full.tex; GitHub tag v1.2.1 (2c61b78): content/12_collapse_rebirth.tex |
| LEMMA_01_COLLAPSE_ENTAILS_DEATH | LEMMA | Lemma 1 (Collapse entails death) | REVISED_AND_PROVED | PASS | REVISED_AND_PROVED | Composite PDF witness: Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.563 l.12; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.596 l.20; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.63 l.18; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.64 l.7; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.64 l.16 | Composite public TeX witness: GitHub tag v1.2.1 (2c61b78): content/04_results.tex; GitHub tag v1.2.1 (2c61b78): appendix/B_axioms_full.tex; GitHub tag v1.2.1 (2c61b78): content/12_collapse_rebirth.tex |
| LEMMA_02_POST_COLLAPSE_TRACE_IS_RESIDUE | LEMMA | Lemma 2 (Post-collapse trace is residue) | REVISED_AND_PROVED | PASS | REVISED_AND_PROVED | Composite PDF witness: Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.563 l.12; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.596 l.20; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.63 l.18; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.64 l.7; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.64 l.16; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.65 l.43 | Composite public TeX witness: GitHub tag v1.2.1 (2c61b78): content/04_results.tex; GitHub tag v1.2.1 (2c61b78): appendix/B_axioms_full.tex; GitHub tag v1.2.1 (2c61b78): content/12_collapse_rebirth.tex |
| LEMMA_03_LATER_LIVE_CONTINUUM_IS_REBIRTH | LEMMA | Lemma 3 (Later live continuum is rebirth) | REVISED_AND_PROVED | PASS | REVISED_AND_PROVED | Composite PDF witness: Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.563 l.18; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.596 l.26; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.65 l.43; Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.66 l.16 | Composite public TeX witness: GitHub tag v1.2.1 (2c61b78): content/04_results.tex; GitHub tag v1.2.1 (2c61b78): appendix/B_axioms_full.tex; GitHub tag v1.2.1 (2c61b78): content/12_collapse_rebirth.tex |
| 12.1 | DEFINITION | Definition 12.1 (Collapse) | STATED_AS_DEFINITION | NOT_APPLICABLE_STIPULATION | PROVED_AS_STATED |  | GitHub tag v1.2.1 (2c61b78): content/12_collapse_rebirth.tex |
| 12.3 | DEFINITION | Definition 12.3 (Internal collapse) | STATED_AS_DEFINITION | NOT_APPLICABLE_STIPULATION | PROVED_AS_STATED |  | GitHub tag v1.2.1 (2c61b78): content/12_collapse_rebirth.tex |
| 12.4 | DEFINITION | Definition 12.4 (External collapse) | STATED_AS_DEFINITION | NOT_APPLICABLE_STIPULATION | PROVED_AS_STATED |  | GitHub tag v1.2.1 (2c61b78): content/12_collapse_rebirth.tex |
| 12.5 | DEFINITION | Definition 12.5 (Residue) | STATED_AS_DEFINITION | NOT_APPLICABLE_STIPULATION | PROVED_AS_STATED |  | GitHub tag v1.2.1 (2c61b78): content/12_collapse_rebirth.tex |
| 12.6 | DEFINITION | Definition 12.6 (Rebirth) | STATED_AS_DEFINITION | NOT_APPLICABLE_STIPULATION | PROVED_AS_STATED |  | GitHub tag v1.2.1 (2c61b78): content/12_collapse_rebirth.tex |
| 3.2 | AXIOM | Axiom 3.2 (Death condition) | STATED_AS_AXIOM | NOT_APPLICABLE_STIPULATION | PROVED_AS_STATED |  | GitHub tag v1.2.1 (2c61b78): appendix/B_axioms_full.tex |
| 3.3 | AXIOM | Axiom 3.3 (Irreversibility of death) | STATED_AS_AXIOM | NOT_APPLICABLE_STIPULATION | PROVED_AS_STATED |  | GitHub tag v1.2.1 (2c61b78): appendix/B_axioms_full.tex |
| SOURCE_THEOREM_3_DEATH | THEOREM | Source Theorem 3 (Death through boundary and embedding collapse) | PROVED_AS_STATED | PASS | PROVED_AS_STATED | Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.563 l.12 | GitHub tag v1.2.1 (2c61b78): content/04_results.tex |
| SOURCE_COROLLARY_3_2_IRREVERSIBILITY | COROLLARY | Source Corollary 3.2 (Irreversibility of death) | PROVED_AS_STATED | PASS | PROVED_AS_STATED | Core 1.2 PDF (Zenodo DOI 10.5281/zenodo.17903912), p.563 l.18 | GitHub tag v1.2.1 (2c61b78): content/04_results.tex |

## Extended theorem-ladder provenance notes
| lemma_id | support_claim_refs | final_statement |
| --- | --- | --- |
| LEMMA_01_COLLAPSE_ENTAILS_DEATH | SOURCE_THEOREM_3_DEATH, 3.2, 12.1, 12.3, 12.4 | If the admissible state space becomes empty, the original continuum is dead and cannot lawfully persist as a live continuum. |
| LEMMA_02_POST_COLLAPSE_TRACE_IS_RESIDUE | SOURCE_THEOREM_3_DEATH, 3.2, 12.1, 12.3, 12.4, 12.5 | After collapse, any surviving structure is residue rather than a still-live instance of the original continuum. |
| LEMMA_03_LATER_LIVE_CONTINUUM_IS_REBIRTH | SOURCE_COROLLARY_3_2_IRREVERSIBILITY, 3.3, 12.5, 12.6 | Any later live continuum grounded in residue is rebirth of a new continuum rather than persistence of the original one. |

## Proof-Summary Metrics
- Positive support rows: 13
- Positive flagship results: 3
- Positive theorem rows: 2
- Positive lemma rows: 3
- Positive axiom rows: 2
- Positive definition rows: 5

## Excluded Claim Boundary
### Appendix-only rows
- None in the current article set; inherited theorem families outside the main theorem chain are excluded rather than retained as appendix-only support.
### Excluded rows
- 1 | Theorem 1 (Monotonicity of dimensionality) | EXCLUDED_FROM_FLAGSHIP_BODY
- 2 | Theorem 2 (Impossibility of spontaneous dimension creation) | EXCLUDED_FROM_FLAGSHIP_BODY
- 3 | Legacy alias 3 (historical downstream label for Source Theorem 3; excluded from the flagship body in alias form) | EXCLUDED_FROM_FLAGSHIP_BODY
- 4 | Theorem 4 (Impossibility of evolution outside the embedding space) | EXCLUDED_FROM_FLAGSHIP_BODY
- 6 | Theorem 6 (Structural tension and phase transitions) | EXCLUDED_FROM_FLAGSHIP_BODY
- 6.1 | Corollary 6.1 (Threshold-governed qualitative change) | EXCLUDED_FROM_FLAGSHIP_BODY
- 10 | Theorem 10 (Monotonic growth of embedding spaces) | EXCLUDED_FROM_FLAGSHIP_BODY
- 11 | Theorem 11 (Threshold-expressivity incompatibility) | EXCLUDED_FROM_FLAGSHIP_BODY
- 12 | Theorem 12 (Incompleteness of embedding spaces) | EXCLUDED_FROM_FLAGSHIP_BODY

## Cross-domain projection atlas with explicit nonclaim boundaries
- OC Core 1.3 flagship foundations paper | current flagship manuscript | flagship route for the foundations article
- Legacy Zenodo preprint uplift program | legacy-publication upgrade lane | discipline-aligned preprint and journal route
- Mathematics family repackaging program | question-to-theorem family regrouping | theorem and foundations journal route
- K0-K12 domain-family publication atlas | cross-domain projection program | foundations and cross-domain theory route

## Companion materials map
- Source witness matrix.
- Theorem-support revalidation dossier.
- Chronology and collision dossier.
- Tier 1 binding atlas.
- Cross-domain projection atlas.

## Figure provenance and caption notes
- FIG_01_ROOT_LAW_GRAMMAR: Root-law grammar for the main article: once contradiction management under the current embedding and threshold regime leaves no nonempty admissible realization, the lawful state is collapse; residue may persist; any later admissible continuation is rebirth rather than persistence of the original continuum.
- FIG_02_THEOREM_LADDER_AND_FATE: Support-status overview for the flagship route. Only surviving, dependency-exact source rows feed the main article; inherited theorem families outside that theorem chain are kept in the excluded set of the current article set.
- TABLE_01_CROSS_DOMAIN_PROJECTION_MAP: Bounded scientific projection map linking the proved OC Core flagship kernel to mathematics, ESTRA extensions, domain projections, and later domain families without claiming current theorem closure outside the flagship scope.

## Editorial Use Note
This appendix reproduces the exact load-bearing source statements, the revised main result, and the derived lemma spine used by the article so that external review can audit the proof materials without consulting hidden internal ledgers.
