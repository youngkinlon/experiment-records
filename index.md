---
layout: default
title: "Experiment Overview"
---

# Experiment Overview
## Experiment Self-Attn Head
Inspired by work on LLM interpretability, I investigate different types of attention heads to understand why repetition occurs in long video generation. The experiments reveal changes in head behavior over time. At this stage, I am not proposing a method, as the analysis provides indirect evidence and has not yet established a direct link to video quality. The next step is to connect these changes in head behavior directly to repetition in generated videos. 

Self-Forcing DMD · EMA · seed 0. Click an experiment title for methods, results, and figures.

| ID  | Experiment                                                         | Objective                                   | Hypothesis                                                          | Current Findings                                                        | Limitations                                        | Next Steps                                                   |
| --- | ------------------------------------------------------------------ | ------------------------------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------ |
| Q01 | [Attention Preference Clustering](%E9%95%BF%E8%A7%86%E9%A2%91%E7%94%9F%E6%88%90%E5%AE%9E%E9%AA%8C/Q1%EF%BC%9Aattn%20%E8%81%9A%E7%B1%BB%E7%A0%94%E7%A9%B6.html)               | Profile head reading preferences            | Heads differ in what they attend to                                 | C0: history-focused, 202 heads; C1: current-block-focused, 158 heads    | No link to specific video failures yet             | Relate head behavior to video failures and select candidates |
| Q02 | [Retrieval-like Attention](%E9%95%BF%E8%A7%86%E9%A2%91%E7%94%9F%E6%88%90%E5%AE%9E%E9%AA%8C/Q2%EF%BC%9ARetrieval-like%20head%20%E6%8E%A2%E7%B4%A2.html)       | Track historical content matching over time | Historical queries can strengthen matching to corresponding content | 14 persistent B candidates; some heads enter or leave the candidate set | Uses query replacement; measures reading only      | Explore a possible link to repetition                        |
| Q03 | [Clustering and Attention Cross-analysis](%E9%95%BF%E8%A7%86%E9%A2%91%E7%94%9F%E6%88%90%E5%AE%9E%E9%AA%8C/Q3%EF%BC%9A%20q1%2Cq2%20%E4%BA%A4%E5%8F%89%E5%AF%B9%E6%AF%94.html) | Identify candidate cluster membership       | Different attention responses may favor different clusters          | Persistent B candidates: 10 in C0, 4 in C1                              | Results depend on grouping and selection criteria  | N/A                                                          |
| Q04 | [Head Output Dynamics](%E9%95%BF%E8%A7%86%E9%A2%91%E7%94%9F%E6%88%90%E5%AE%9E%E9%AA%8C/Q4%20%E6%8E%A2%E7%A9%B6head%20%E8%BE%93%E5%87%BA%E9%9A%8F%E7%9D%80%E6%97%B6%E9%97%B4%E5%8F%98%E5%8C%96.html)                  | Locate output changes around video failures | Some heads change their output around failure onset                 | All chunks recorded; comparison with a single-prompt video is ongoing   | Output norm does not establish causal contribution | Add visualizations for further analysis                      |

These are diagnostic experiments focused on self-attention.

## Cross-Attention Experiments

| ID | Experiment | Hypothesis / Question | Setup and Comparison | Preliminary Results | Current Assessment / Limitations | Next Steps |
| --- | --- | --- | --- | --- | --- | --- |
| Q05 | [CA Residual Scaling](docs/Q05-ca-residual-scaling.html) | **H2:** Text conditioning may exert an overly strong relative influence in some long-rollout states.<br> | Increase or decrease cross-attention residual writes within specified time windows. Compare CA write magnitude relative to self-attention and the residual stream across early and late stages. | No consistent late-stage increase in relative CA write magnitude was observed in the tested sample. Neither increasing nor decreasing CA residual strength produced a clear improvement in video quality or continuity. | All layers were scaled together, so layer-specific effects were not isolated. Interventions on selected layers remain untested. | Explore self-attn–cross-attn write alignment; see Q06. |
| Q06 | [SA–CA Write Alignment over Time](docs/Q06-sa-ca-alignment.html) | The directional relationship between cross-attn and self-attn residual writes may change before video degradation or repetition. | Measure cosine similarity between their actual residual writes at the final layer and first denoising step. | We observed sharp drops in similarity before or at the onset of video degradation, followed by sharp rebounds. | The analysis focuses on one layer, while other layers behave differently. A more fundamental explanation may be needed. | Identify the underlying cause. |
| Q07 | [History-Dependent CA Query Intervention](docs/Q07-history-ca-query.html) | How history is incorporated into CA query inputs may affect text conditioning and event progression. | Retain the full-history self-attention main residual while constructing cross-attention query inputs from a branch with restricted history. | Keeping one past chunk produced similar qualitative behavior to baseline. Using only the current chunk in the query-construction branch showed a tentative tendency to escape repetitive motion. | The mechanism remains unresolved. | Identify the underlying cause. |

## Reference

[Self-Forcing inference 过程详解](docs/self-forcing-inference.html)

