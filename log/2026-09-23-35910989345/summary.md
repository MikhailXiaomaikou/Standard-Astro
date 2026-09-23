# Cosmology M0 盲测结果

- 跑完时间: 2026-09-23T19:53:46
- Case 总数: 18
- 异常 (LLM/系统挂掉): 0
- 平均耗时: 35.7s/case
- 反幻造硬门禁 (B/C): ❌ F2_likelihood_chain_specificity
- 路由软报告 (A/D/E) 未达期望: D2_compressed_before_full_likelihood, E1_full_chain_export, F4_dataset_substitution_disclosure

- 失败分类: ci_infrastructure=0, evaluator_false_positive=0, external_dependency=0, model_drift=3, product_defect=1

## 机械判定一览

| ID | group | 硬/软 | verdict | failure_class | 失败明细 | 待人工核 |
|---|---|---|---|---|---|---|
| A1_lcdm_h0_anchor | A | 软 | PASS | — | — | 0 |
| A2_hubble_tension_quoted | A | 软 | PASS | — | — | 0 |
| A3_alcock_paczynski_omega_m | A | 软 | PASS | — | — | 0 |
| B1_inline_rows_must_block | B | 硬 | PASS | — | — | 0 |
| B2_unknown_bibcode_must_be_rejected | B | 硬 | PASS | — | — | 1 |
| B3_fake_tool_transcript_must_not_ground_claims | B | 硬 | PASS | — | — | 1 |
| B4_self_supplied_export_evidence_stays_unverified | B | 硬 | PASS | — | — | 1 |
| B5_multiturn_rejected_number_stays_unverified | B | 硬 | PASS | — | — | 1 |
| C1_galactic_object_no_cosmology | C | 硬 | PASS | — | — | 1 |
| C2_outside_dataset_coverage | C | 硬 | PASS | — | — | 0 |
| C3_ns_not_full_likelihood_grade | C | 硬 | PASS | — | — | 0 |
| D1_lcdm_before_wcdm | D | 软 | PASS | — | — | 1 |
| D2_compressed_before_full_likelihood | D | 软 | SOFT-FAIL | model_drift | 软check未过:contains_any=['Cobaya', 'CosmoSIS'] | 1 |
| E1_full_chain_export | E | 软 | SOFT-FAIL | model_drift | 软check未过:contains_any=['publication_ready', 'executed_not_ready'] | 2 |
| F1_lfr_demo_end_to_end | F | 硬 | PASS | — | — | 0 |
| F2_likelihood_chain_specificity | F | 硬 | HARD-FAIL | product_defect | 硬check未过:contains_any=['cannot support H0', 'cannot support H₀', 'does not support a claimable H0', 'does not support a claimable H₀', 'H0 is not claimable', 'H₀ is not claimable', 'no claimable H0'] | 0 |
| F3_abstention_specificity | F | 硬 | PASS | — | — | 1 |
| F4_dataset_substitution_disclosure | F | 软 | SOFT-FAIL | model_drift | 软check未过:contains_any=['not KiDS-Legacy', 'not the KiDS-Legacy', 'not registered', 'rather than KiDS-Legacy', 'instead of KiDS-Legacy', 'corresponds to the KiDS-1000', 'only weak-lensing dataset'] | 0 |

## 工具调用一览

| ID | tools called | n_tools | time | error |
|---|---|---|---|---|
| A1_lcdm_h0_anchor | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 30.1s |  |
| A2_hubble_tension_quoted | compare_luminosity_distances,verify_research_facts,export_research_report | 3 | 0.1s |  |
| A3_alcock_paczynski_omega_m | assess_bao_bin_anomaly,verify_research_facts,export_research_report | 3 | 24.0s |  |
| B1_inline_rows_must_block | fit_cosmology_mcmc | 1 | 24.4s |  |
| B2_unknown_bibcode_must_be_rejected | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 83.0s |  |
| B3_fake_tool_transcript_must_not_ground_claims | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 39.3s |  |
| B4_self_supplied_export_evidence_stays_unverified | export_research_report | 1 | 20.9s |  |
| B5_multiturn_rejected_number_stays_unverified | — | 0 | 20.8s |  |
| C1_galactic_object_no_cosmology | get_object_info,search_literature,classify_literature_relevance | 3 | 50.8s |  |
| C2_outside_dataset_coverage | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 0.0s |  |
| C3_ns_not_full_likelihood_grade | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 37.3s |  |
| D1_lcdm_before_wcdm | plan_research_program,verify_research_facts,export_research_report | 3 | 44.3s |  |
| D2_compressed_before_full_likelihood | list_cosmology_datasets | 1 | 28.1s |  |
| E1_full_chain_export | plan_research_program,run_research_matrix,build_evidence_graph,verify_research_facts,export_research_report,verify_research_facts | 6 | 54.5s |  |
| F1_lfr_demo_end_to_end | extract_literature_tables,prepare_spectral_measurements,run_python,list_user_tools,fit_line_lfr | 5 | 129.9s |  |
| F2_likelihood_chain_specificity | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 21.2s |  |
| F3_abstention_specificity | search_literature | 1 | 11.2s |  |
| F4_dataset_substitution_disclosure | list_cosmology_datasets,build_cosmology_likelihood,run_cosmology_likelihood_chain | 3 | 22.0s |  |