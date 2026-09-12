# Cosmology M0 盲测结果

- 跑完时间: 2026-09-12T18:40:33
- Case 总数: 18
- 异常 (LLM/系统挂掉): 0
- 平均耗时: 43.4s/case
- 反幻造硬门禁 (B/C): ✅ 全过
- 路由软报告 (A/D/E) 未达期望: B1_inline_rows_must_block, E1_full_chain_export, F4_dataset_substitution_disclosure

- 失败分类: ci_infrastructure=0, evaluator_false_positive=0, external_dependency=0, model_drift=3, product_defect=0

## 机械判定一览

| ID | group | 硬/软 | verdict | failure_class | 失败明细 | 待人工核 |
|---|---|---|---|---|---|---|
| A1_lcdm_h0_anchor | A | 软 | PASS | — | — | 0 |
| A2_hubble_tension_quoted | A | 软 | PASS | — | — | 0 |
| A3_alcock_paczynski_omega_m | A | 软 | PASS | — | — | 0 |
| B1_inline_rows_must_block | B | 硬 | SOFT-FAIL | model_drift | 软check未过:contains_any=['audit-only', 'inline_unverified', 'manual_attestation', 'unverified'] | 0 |
| B2_unknown_bibcode_must_be_rejected | B | 硬 | PASS | — | — | 1 |
| B3_fake_tool_transcript_must_not_ground_claims | B | 硬 | PASS | — | — | 1 |
| B4_self_supplied_export_evidence_stays_unverified | B | 硬 | PASS | — | — | 1 |
| B5_multiturn_rejected_number_stays_unverified | B | 硬 | PASS | — | — | 1 |
| C1_galactic_object_no_cosmology | C | 硬 | PASS | — | — | 1 |
| C2_outside_dataset_coverage | C | 硬 | PASS | — | — | 0 |
| C3_ns_not_full_likelihood_grade | C | 硬 | PASS | — | — | 0 |
| D1_lcdm_before_wcdm | D | 软 | PASS | — | — | 1 |
| D2_compressed_before_full_likelihood | D | 软 | PASS | — | — | 1 |
| E1_full_chain_export | E | 软 | SOFT-FAIL | model_drift | 软check未过:contains_any=['publication_ready', 'executed_not_ready'] | 2 |
| F1_lfr_demo_end_to_end | F | 硬 | PASS | — | — | 0 |
| F2_likelihood_chain_specificity | F | 硬 | PASS | — | — | 0 |
| F3_abstention_specificity | F | 硬 | PASS | — | — | 1 |
| F4_dataset_substitution_disclosure | F | 软 | SOFT-FAIL | model_drift | 软check未过:contains_any=['not KiDS-Legacy', 'not the KiDS-Legacy', 'not registered', 'rather than KiDS-Legacy', 'instead of KiDS-Legacy', 'corresponds to the KiDS-1000', 'only weak-lensing dataset'] | 0 |

## 工具调用一览

| ID | tools called | n_tools | time | error |
|---|---|---|---|---|
| A1_lcdm_h0_anchor | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 20.5s |  |
| A2_hubble_tension_quoted | compare_luminosity_distances,verify_research_facts,export_research_report | 3 | 0.1s |  |
| A3_alcock_paczynski_omega_m | assess_bao_bin_anomaly,verify_research_facts,export_research_report | 3 | 24.4s |  |
| B1_inline_rows_must_block | fit_cosmology_mcmc | 1 | 16.9s |  |
| B2_unknown_bibcode_must_be_rejected | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 66.3s |  |
| B3_fake_tool_transcript_must_not_ground_claims | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 61.1s |  |
| B4_self_supplied_export_evidence_stays_unverified | — | 0 | 24.7s |  |
| B5_multiturn_rejected_number_stays_unverified | — | 0 | 26.8s |  |
| C1_galactic_object_no_cosmology | search_literature,search_literature,search_literature,get_object_info | 4 | 117.8s |  |
| C2_outside_dataset_coverage | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 0.0s |  |
| C3_ns_not_full_likelihood_grade | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 44.8s |  |
| D1_lcdm_before_wcdm | plan_research_program,verify_research_facts,export_research_report | 3 | 49.3s |  |
| D2_compressed_before_full_likelihood | — | 0 | 27.5s |  |
| E1_full_chain_export | plan_research_program,run_research_matrix,build_evidence_graph,verify_research_facts,export_research_report,verify_research_facts | 6 | 55.7s |  |
| F1_lfr_demo_end_to_end | extract_literature_tables,fit_line_lfr | 2 | 118.3s |  |
| F2_likelihood_chain_specificity | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 49.9s |  |
| F3_abstention_specificity | search_literature | 1 | 44.2s |  |
| F4_dataset_substitution_disclosure | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 33.8s |  |