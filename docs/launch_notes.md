# Launch notes

## Current readiness

The Microsoft Financial Intelligence Platform is portfolio-ready as a locally runnable, tested project. It is not represented as a production service, a Microsoft-endorsed product, or a live Azure AI deployment.

## Implemented capabilities

- SEC Company Facts ingestion and raw-data retention.
- Fiscal-period transformation with corrected comparative-observation selection.
- Validated Q4 derivation from full-year and nine-month observations.
- SQLite storage and reusable SQL analytics views.
- Approved CSV exports for application and reporting use.
- Three-page Streamlit primary interface.
- Complementary Power BI report.
- Deterministic executive insight fallback.
- Generic reporting-period grounding with annual look-ahead protection.
- FY2026 Q4 approved business-driver packet and derived segment rankings.
- Strict executive-briefing schemas and claim/source validation.
- Atomic saved-briefing persistence and load-time revalidation.
- Azure OpenAI v1 adapter with explicit timeout, disabled retries, and structured output.
- Explicit offline CLI with dry-run, replacement protection, and isolated output directories.
- Secret-free GitHub Actions test workflow.

## Validation status

Final Phase 5 verification passes **86 tests**. Tests cover fiscal periods, grounding, annual leakage prevention, business-driver reconciliation, schemas, financial and business claims, prompts, provider injection, storage, display selection, mocked Azure behavior, CLI exit paths, and Streamlit’s no-Azure rendering boundary.

No live Azure request is part of the test suite or CI.

## Known limitations

- Live Azure generation awaits a compatible deployment and available quota.
- No real AI-generated briefing is committed or claimed as generated successfully.
- Only FY2026 Q4 has an approved business-driver packet.
- SEC accession-level citations are not exposed through the approved analytics layer.
- User research is planned but not completed.
- No production hosting, monitoring, scheduled generation, approval interface, authentication, or service-level objective exists.
- The platform covers Microsoft only and provides no forecasts, valuation, peer benchmarking, or investment advice.

## Launch checklist

- [x] Approved financial exports load successfully.
- [x] Streamlit renders all three pages without application errors.
- [x] Power BI report artifact exists.
- [x] Grounding and briefing schemas reject unsupported content.
- [x] Deterministic fallback remains available.
- [x] Azure adapter is isolated from page rendering.
- [x] CLI dry-run performs no request or write.
- [x] Generated briefing JSON is ignored by Git.
- [x] Tests and compilation run in CI without secrets.
- [ ] Configure a compatible Azure deployment and confirm quota.
- [ ] Run one authorized live generation outside Streamlit.
- [ ] Verify the saved briefing reloads and displays correctly.
- [ ] Conduct planned user-research sessions.
- [ ] Resolve critical usability findings before a broader launch claim.
- [ ] Define deployment, monitoring, and operational ownership if hosting publicly.

## User-testing checklist

- [ ] Recruit the four proposed participant profiles.
- [ ] Confirm consent and privacy handling.
- [ ] Prepare deterministic and validated-AI conditions without fabricated content.
- [ ] Counterbalance condition order.
- [ ] Measure time, accuracy, confidence, confusion, source usage, and trust.
- [ ] Separate observation from interpretation in findings.
- [ ] Avoid presenting participation as Microsoft or UTEP endorsement.
- [ ] Publish only real aggregated findings with participant count and method.

## Criteria for calling Azure AI “live”

All criteria must be met:

1. Required environment variables are configured through an approved secret-management process.
2. The named Azure deployment supports the Responses API and structured output.
3. Sufficient quota is available.
4. A real CLI request completes successfully without exposing secrets.
5. Output passes complete local schema, period, figure, source, and driver validation.
6. The briefing is saved atomically and revalidates on load.
7. Streamlit displays the saved artifact with the AI-generated label while remaining request-free.
8. The generation event and approved output are reviewed according to the intended operating process.

Until then, documentation must describe Azure generation as implemented but pending deployment/quota validation.

## Criteria for merging into `main`

- [ ] Pull request review confirms no financial, ETL, SQL, or runtime behavior regression.
- [ ] GitHub Actions passes compilation and all tests.
- [ ] No credentials, prompts, raw model responses, or generated production briefing are in the diff.
- [ ] Documentation accurately distinguishes implemented, validated, and pending capabilities.
- [ ] Streamlit fallback behavior is manually spot-checked.
- [ ] Azure generation remains CLI-only.
- [ ] Any requested reviewer changes are resolved.

Live Azure quota is not required to merge the tested infrastructure, provided the limitation remains explicit and the application continues to fall back deterministically.
