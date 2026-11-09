---
layout: default
title: "History-Dependent CA Query Intervention"
---

# History-Dependent CA Query Intervention

## 假设：
How history is incorporated into CA query inputs may affect text conditioning and event progression. 

### 预期结果

如果完整历史中包含对当前事件进度有帮助的信息，并且 cross-attn 通过查询输入实际利用了这些信息，那么缩短构造 query 时可读取的历史，可能影响其文本读取，并降低事件推进或连续性表现。 
## 实验

保留完整历史 self-attn 分支的主残差，用近期历史 self-attn 分支构造 cross-attn 的查询输入。它们是持续作用于生成轨迹的干预：启动后每个去噪 forward 和 clean-context refill 都生效，并作用于全部 30 层。

### Baseline 与干预公式

两条分支为：


$$
\begin{aligned}
Z_F &= U+g\odot\operatorname{self-attn}(\widetilde U;\mathrm{KV}_F),\\
Z_R &= U+g\odot\operatorname{self-attn}(\widetilde U;\mathrm{KV}_R).
\end{aligned}
$$


Baseline：cross-attn 用 $$Z_F$$ 构造 query，输出加回 $$Z_F$$：


$$
\boxed{T_{\mathrm{baseline}}=Z_F+\operatorname{cross-attn}\bigl(\mathrm{norm3}(Z_F),C\bigr).}
$$



干预：cross-attn 用 $$Z_R$$ 构造 query，输出仍加回 $$Z_F$$：


$$
\boxed{T_{\mathrm{recent}}=Z_F+\operatorname{cross-attn}\bigl(\mathrm{norm3}(Z_R),C\bigr).}
$$



$$U$$ 为当前表征，$$\widetilde U$$ 为归一化及时间调制后的输入，$$g$$ 为原生 gate，$$C$$ 为文本条件；$$F/R$$ 分别表示完整可见历史／近期历史，两者均包含当前块。
## 可视化结果

在a组，历史信息为保留 1 个历史 chunk 与完整当前块  用于cross-attn生成，发现效果和baseline（6个历史 chunk + 当前块，共7个 chunk）生成结果基本一致，b组 历史信息为保留 0 个历史 chunk 与完整当前块 

### 组 A · 15 秒
P0，seed 0，EMA 权重，缓存窗口 21 latent 帧；保留 1 个历史 chunk 与完整当前块，全部 30 层。前 5 秒生成结果一致，5s后修改为recent history cross-attn query 

<video controls preload="metadata" playsinline src="../assets/cross-attn/H1_history_evidence_20261108-run_a-paired-53cccff9b5.mp4">Your browser does not support this video. <a href="../assets/cross-attn/H1_history_evidence_20261108-run_a-paired-53cccff9b5.mp4">Download the video</a>.</video>


### 组 B · 30 秒

P0，seed 0，EMA 权重，缓存窗口 21 latent 帧；保留 0 个历史 chunk 与完整当前块，全部 30 层。在1s后开始recent history cross-attn query 


<video controls preload="metadata" playsinline src="../assets/cross-attn/H1_history_evidence_20261108-run_d-paired-8a4d33063a.mp4">Your browser does not support this video. <a href="../assets/cross-attn/H1_history_evidence_20261108-run_d-paired-8a4d33063a.mp4">Download the video</a>.</video>



## 初步结论：

对于cross-attn来说，


$$
\operatorname{cross-attn}\bigl(\mathrm{norm3}(Z_F),C\bigr).
$$




$$
\begin{aligned}
Z_F &= U+g\odot\operatorname{self-attn}(\widetilde U;\mathrm{KV}_F),\\
\end{aligned}
$$


保留1个历史chunk的kv cache 和baseline保留7个效果类似（a组），几种可能的假设：
- Cross-Attn 主要受当前输入U 影响，Self-Attn 的历史更新对 Cross-Attn 影响较弱
- 额外历史没有为 Self-Attn 提供多少新信息  
- 额外历史改变了 Self-Attn 和 Cross-Attn，但这些变化没有有效影响最终预测

不保留历史chunk反而有跳出重复的趋势，（b组）（why？）


下一步去看看是不是当前U影响很大，比如不加self-attn层的U 给cross-attn加入看看效果
