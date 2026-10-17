假设：不同 attention head 对当前生成块、近邻历史和较远历史具有不同的读取偏好。长视频中的人物静止或重复，可能与部分 head 的历史读取方式有关 

思路： 先建立每个 head 的“注意力读取画像”，通过无监督聚类寻找相似的读取模式，再检查分组是否在不同 prompt 子集上保持稳定，为后续机制实验提供候选。

**具体做法：**

1. 固定 Self-Forcing DMD 的 EMA 权重，对同一组 10 个 prompt，使用 seed 0 分别生成约 15 秒、30 秒视频。
2. 观察全部 **30 层 × 12 个 head，共 360 个 head**。记录第一去噪步的注意力，每个 latent 帧抽样两个空间 query，使用完整可见 key 计算 attention。当时使用 21 帧局部缓存、1 帧 sink。
3. 对某个 head，定义 query q 对 key k 的注意力为：


$$
a_{qk}
=\frac{\exp\left(Q_q^\top K_k/\sqrt{d_h}\right)}
{\sum_{j\in\mathcal K}\exp\left(Q_q^\top K_j/\sqrt{d_h}\right)}.
$$

4. 将同一 latent 帧的 key 权重相加，再对抽样 query 取平均，得到逐帧注意力质量：   

$$
m_f=\frac{1}{|\mathcal Q|}
\sum_{q\in\mathcal Q}
\sum_{\substack{k\in\mathcal K\\\operatorname{frame}(k)=f}}a_{qk},
\qquad \sum_f m_f=1.
$$

其中，抽样 query 集合与实际可见缓存的 key 集合分别记为：
$$
\mathcal Q=\{\text{抽样 query}\},
\qquad
\mathcal K=\{\text{实际可见 key}\}.
$$
5. 为每个 head 提取五个特征。历史 sink 帧、当前生成块、**除 sink 外的全部可见历史帧**，以及最近三个历史 latent 帧，分别记为：
$$
\begin{aligned}
\mathcal S&=\{\text{历史 sink 帧}\},\\
\mathcal C&=\{\text{当前生成块的帧}\},\\
\mathcal M&=\{\text{除 sink 外的全部可见历史帧}\},\\
\mathcal R&=\{\text{最近三个非 sink 历史 latent 帧}\}\subseteq\mathcal M.
\end{aligned}
$$

| 特征             | 记号  |
| -------------- | --- |
| 历史 sink 注意力    | x₁  |
| 当前块注意力         | x₂  |
| 历史质量加权分散程度     | x₃  |
| 最近三个历史帧注意力     | x₄  |
| 归一化 token 注意力熵 | x₅  |

对应公式为：
$$
\begin{aligned}
x_1&=\sum_{f\in\mathcal S}m_f,\\[4pt]
x_2&=\sum_{f\in\mathcal C}m_f,\\[4pt]
x_3&=
\begin{cases}
M_{\mathcal M}\displaystyle\frac{-\sum_{f\in\mathcal M}p_f\log p_f}{\log|\mathcal M|},
&M_{\mathcal M}>0,\ |\mathcal M|>1,\\[4pt]
0,&\text{其他情况},
\end{cases}\\[6pt]
x_4&=\sum_{f\in\mathcal R}m_f,\\[4pt]
x_5&=\frac{1}{|\mathcal Q|}\sum_{q\in\mathcal Q}
\frac{-\sum_{k\in\mathcal K}a_{qk}\log a_{qk}}{\log|\mathcal K|}.
\end{aligned}
$$

其中：

$$
M_{\mathcal M}=\sum_{f\in\mathcal M}m_f,
\qquad
p_f=\frac{m_f}{M_{\mathcal M}}\quad(M_{\mathcal M}>0).
$$

当历史质量为零，或历史帧数不超过一帧时，历史质量加权分散程度取零。质量加权可以避免将“只分配了很少注意力、但分布均匀”的 head 误判为大量分散读取历史。
    
6. 使用 **30 秒视频中 5 秒之后、可见 key 数量匹配的区间**拟合聚类。先在各 prompt 内对时间平均，再对 10 个 prompt 等权平均：
    

$$
\bar{\mathbf x}_i
=\frac{1}{10}\sum_{p=1}^{10}
\left(
\frac{1}{|\mathcal T_p|}\sum_{t\in\mathcal T_p}\mathbf x_{i,p,t}
\right).
$$

其中，i 表示一个具体的 layer/head；第 p 个 prompt 满足筛选条件的观测时间集合记为：

$$
\mathcal T_p=\{\text{第 p 个 prompt 满足筛选条件的观测时间}\}.
$$
    
7. 对五个特征分别在全部 360 个 head 间进行标准化：

$$
z_{ij}=\frac{\bar x_{ij}-\mu_j}{\sigma_j}.
$$

近零标准差维度的尺度按代码置为 1。随后使用 k-means++ 初始化并求解二簇聚类：

$$
\min_{\{\boldsymbol\mu_c\},\{c_i\}}
\sum_{i=1}^{360}\left\|\mathbf z_i-\boldsymbol\mu_{c_i}\right\|_2^2,
\qquad c_i\in\{0,1\}.
$$

**聚类在五维标准化特征上完成。**
    
8. 对最终二簇分组进行 30 次 prompt bootstrap，以及 30 次随机 5/5 prompt 分半重聚类。所有重聚类共用原校准集的标准化尺度，使用调整兰德指数（ARI）衡量一致性：

$$
S_{\mathrm{bootstrap}}
=\operatorname{median}_{b=1,\ldots,30}
\operatorname{ARI}\bigl(\mathbf c,\mathbf c^{(b)}\bigr).
$$
$$
S_{\mathrm{split}}
=\operatorname{median}_{b=1,\ldots,30}
\operatorname{ARI}\bigl(
\mathbf c_{\mathrm{left}}^{(b)},\mathbf c_{\mathrm{right}}^{(b)}
\bigr).
$$

ARI 越接近 1，表示两次分组越一致。
    

**结果：**

各簇的当前块平均注意力为：

$$
\overline M_{\mathrm{current}}^{(c)}
=\frac{1}{N_c}\sum_{i:c_i=c}\bar x_{i,2},
\qquad
N_c=\sum_{i=1}^{360}\mathbf 1[c_i=c].
$$

| 分组        | head 数量 | 当前块平均注意力 | 主要特点               |
| --------- | ------- | -------- | ------------------ |
| C0：偏历史读取  | 202     | 23.30%   | 相对更多读取可见历史，历史读取更分散 |
| C1：偏当前块读取 | 158     | 80.20%   | 注意力主要集中于当前生成块      |

稳定性结果为：

$$
S_{\mathrm{bootstrap}}=0.945,
\qquad S_{\mathrm{split}}=0.90.
$$

  

![](Pasted%20image%2020261017183154.png)
缺陷：

未与具体失败对应 人物静止、动作重复、外观漂移和背景运动尚未分别对应，间接研究方法只能说 
