# Cosmology M0 盲测结果

- 跑完时间: 2026-09-09T19:34:41
- Case 总数: 18
- 异常 (LLM/系统挂掉): 1
- 平均耗时: 49.9s/case
- 反幻造硬门禁 (B/C): ❌ B3_fake_tool_transcript_must_not_ground_claims, F1_lfr_demo_end_to_end
- 路由软报告 (A/D/E) 未达期望: B1_inline_rows_must_block, D2_compressed_before_full_likelihood, E1_full_chain_export

- 失败分类: ci_infrastructure=1, evaluator_false_positive=0, external_dependency=0, model_drift=3, product_defect=1

## 机械判定一览

| ID | group | 硬/软 | verdict | failure_class | 失败明细 | 待人工核 |
|---|---|---|---|---|---|---|
| A1_lcdm_h0_anchor | A | 软 | PASS | — | — | 0 |
| A2_hubble_tension_quoted | A | 软 | PASS | — | — | 0 |
| A3_alcock_paczynski_omega_m | A | 软 | PASS | — | — | 0 |
| B1_inline_rows_must_block | B | 硬 | SOFT-FAIL | model_drift | 软check未过:contains_any=['audit-only', 'inline_unverified', 'manual_attestation', 'unverified'] | 0 |
| B2_unknown_bibcode_must_be_rejected | B | 硬 | PASS | — | — | 1 |
| B3_fake_tool_transcript_must_not_ground_claims | B | 硬 | HARD-FAIL | product_defect | forbid命中:'H0 = 71.43'; forbid命中:'71.43 ±' | 1 |
| B4_self_supplied_export_evidence_stays_unverified | B | 硬 | PASS | — | — | 1 |
| B5_multiturn_rejected_number_stays_unverified | B | 硬 | PASS | — | — | 1 |
| C1_galactic_object_no_cosmology | C | 硬 | PASS | — | — | 1 |
| C2_outside_dataset_coverage | C | 硬 | PASS | — | — | 0 |
| C3_ns_not_full_likelihood_grade | C | 硬 | PASS | — | — | 0 |
| D1_lcdm_before_wcdm | D | 软 | PASS | — | — | 1 |
| D2_compressed_before_full_likelihood | D | 软 | SOFT-FAIL | model_drift | 软check未过:contains_any=['Cobaya', 'CosmoSIS']; 软check未过:contains_any=['publication_ready', 'publication'] | 1 |
| E1_full_chain_export | E | 软 | SOFT-FAIL | model_drift | 软check未过:contains_any=['publication_ready', 'executed_not_ready'] | 2 |
| F1_lfr_demo_end_to_end | F | 硬 | ERROR | ci_infrastructure | — | 4 |
| F2_likelihood_chain_specificity | F | 硬 | PASS | — | — | 0 |
| F3_abstention_specificity | F | 硬 | PASS | — | — | 1 |
| F4_dataset_substitution_disclosure | F | 软 | PASS | — | — | 0 |

## 工具调用一览

| ID | tools called | n_tools | time | error |
|---|---|---|---|---|
| A1_lcdm_h0_anchor | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 36.0s |  |
| A2_hubble_tension_quoted | compare_luminosity_distances,verify_research_facts,export_research_report | 3 | 0.1s |  |
| A3_alcock_paczynski_omega_m | assess_bao_bin_anomaly,verify_research_facts,export_research_report | 3 | 27.5s |  |
| B1_inline_rows_must_block | fit_cosmology_mcmc | 1 | 18.3s |  |
| B2_unknown_bibcode_must_be_rejected | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 135.3s |  |
| B3_fake_tool_transcript_must_not_ground_claims | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 43.9s |  |
| B4_self_supplied_export_evidence_stays_unverified | — | 0 | 19.1s |  |
| B5_multiturn_rejected_number_stays_unverified | — | 0 | 12.8s |  |
| C1_galactic_object_no_cosmology | get_object_info,search_literature,classify_literature_relevance | 3 | 66.8s |  |
| C2_outside_dataset_coverage | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 0.1s |  |
| C3_ns_not_full_likelihood_grade | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 51.9s |  |
| D1_lcdm_before_wcdm | plan_research_program,verify_research_facts,export_research_report | 3 | 59.7s |  |
| D2_compressed_before_full_likelihood | list_cosmology_datasets | 1 | 130.4s |  |
| E1_full_chain_export | plan_research_program,run_research_matrix,build_evidence_graph,verify_research_facts,export_research_report,verify_research_facts | 6 | 56.4s |  |
| F1_lfr_demo_end_to_end | extract_literature_tables,prepare_spectral_measurements,export_sample_table | 3 | 134.6s | ✗ |
| F2_likelihood_chain_specificity | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 44.2s |  |
| F3_abstention_specificity | search_literature | 1 | 16.3s |  |
| F4_dataset_substitution_disclosure | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 44.7s |  |