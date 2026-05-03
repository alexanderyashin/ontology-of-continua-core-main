# OC Core Text Fill Rules

Status: `OC_CORE_TEXT_FILL_RULES_READY`
Artifact hash: `d1578f20b493ac5e0cb3398e11a0befab20918db075aeb8ce101a932d67d902d`

## Standard Sources

- Nature Communications reporting standards and availability of data, materials, code and protocols: https://www.nature.com/ncomms/editorial-policies/reporting-standards
- ICMJE Recommendations: https://www.icmje.org/recommendations/
- Transparency and Openness Promotion Guidelines: https://incentivizingopen.org/projects2/transparency-and-openness-promotion-top-guidelines/

## Rule Groups

### positive_node_requirements
- Every generated section must declare audience, purpose, reader payoff, and relation to the surrounding argument.
- Every claim-bearing paragraph must bind to a claim boundary and at least one proof, evidence, source, example, or limitation route.
- Every artifact must expose source trace and verification rule before it can move to package assembly.

### prohibited_generation_patterns
- Do not transform raw ledgers into prose by dumping rows.
- Do not emit control-plane, approval-lock, or gate-jargon language into reader-facing artifacts.
- Do not emit stale version references, unsupported overclaims, broken links, bad encoding, duplicate boilerplate, or Markdown leakage.
- Do not emit a paragraph without reader payoff.

### artifact_readiness_predicates
- Title/frontmatter, audience contract, claim boundary, source trace, and artifact role must be present.
- A generated artifact must pass forbidden-term, stale-version, local-path, link, encoding, and repeated-boilerplate scans.
- A generated artifact must fail closed when required fill status remains not assessed for a promoted claim.
