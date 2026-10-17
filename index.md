---
layout: default
---

# Experiment Overview
Inspired by work on LLM interpretability, I investigate different types of attention heads to understand why repetition occurs in long video generation. The experiments reveal changes in head behavior over time. At this stage, I am not proposing a method, as the analysis provides indirect evidence and has not yet established a direct link to video quality. The next step is to connect these changes in head behavior directly to repetition in generated videos. 

Self-Forcing DMD · EMA · seed 0. Click an experiment title for methods, results, and figures.

| ID  | Experiment                                                         | Objective                                   | Hypothesis                                                          | Current Findings                                                        | Limitations                                        | Next Steps                                           |
| --- | ------------------------------------------------------------------ | ------------------------------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------- | ---------------------------------------------------- |
| Q01 | [Attention Preference Clustering](长视频生成实验/Q1：attn%20聚类研究.md)               | Profile head reading preferences            | Heads differ in what they attend to                                 | C0: history-focused, 202 heads; C1: current-block-focused, 158 heads    | No link to specific video failures yet             | Align with video failures and select candidates      |
| Q02 | [Retrieval-like Attention](长视频生成实验/Q2：Retrieval-like%20head%20探索.md)       | Track historical content matching over time | Historical queries can strengthen matching to corresponding content | 14 persistent B candidates; some heads enter or leave the candidate set | Uses query replacement; measures reading only      | Don't know, maybe build a deep link with repetition? |
| Q03 | [Clustering and Attention Cross-analysis](长视频生成实验/Q3：%20q1%2Cq2%20交叉对比.md) | Identify candidate cluster membership       | Different attention responses may favor different clusters          | Persistent B candidates: 10 in C0, 4 in C1                              | Results depend on grouping and selection criteria  | N/A                                                  |
| Q04 | [Head Output Dynamics](长视频生成实验/Q4%20探究head%20输出随着时间变化.md)                  | Locate output changes around video failures | Some heads change their output around failure onset                 | All chunks recorded; comparison with a single-prompt video is ongoing   | Output norm does not establish causal contribution | Add visualization for research                       |

