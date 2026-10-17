###  Motivation

假设：基于llm 论文对于head的功能研究 ，我们判断是否存在类似的head

参考1： retrieve heads： [《Retrieval Head Mechanistically Explains Long-Context Factuality》](https://proceedings.iclr.cc/paper_files/paper/2025/file/9b77f07301b1ef1fe810aae96c12cb7b-Paper-Conference.pdf)

参考2：Induction heads：[《In-context Learning and Induction Heads》](https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/) 

我们这里主要研究的head是读取行为，由于我们缺少具有明确检索答案的任务 （llm 存在此任务所以 验证性较强）。下一步可以去研究 不同head输出占比随着时间的变化 

### 实验假设

由于我们研究的是读取行为，
根据retrieve heads 和 Induction heads的定义，
- retrieve heads 认为 存在部分head具有retrieve 能力，能够根据当前任务，从长上下文中定位并提取相关信息 ，
- induction heads 认为部分head 能够识别历史上下文中出现过的序列模式 ，即当出现 A-B-C-D 时候，后期又出现B ，在论文定义中induction heads 会更多注意 C ，然后提高 C 的预测概率 

### 实验设计：

动机：由于我们没有固定的答案来验证，我的想法是将当前帧的query 换成某历史帧（定义成a）保留的query，然后我认为当替换后看帧a attn比例大幅增大，我们认为这类head 可能是存在retrieve类似的行为 (不过这里很难去和重复直接联系起来（这里感觉还需要更加巧妙的实验）) 。 定义为 retrieve-like head 

然后对于当替换后看帧a后一帧 帧b 的attn 比例大幅增大，我们认为这类head可能类似于 induction类似行为 （也很难和重复直接联系起来 ） 定义为  induction-like head 

同时观察是否存在替换后减小对帧a关注的 head，（是否可能可以抑制复制情况也就是重复情况出现）

**生成与保存历史 Q** 对 5 个 prompt，固定 seed 生成视频，在 **5、15，30 秒附近**设置观测点。每个观测点将最近四个历史块记为 A、B、C、D，保存 B 在干净回填时抽样记录的 Q。

**第一去噪步进行诊断** 在 D 后启动当前块，仅观察第一去噪步：

$$
t=100
$$

同一观测点固定 noisy input、timestep 和可见 K，每层每头分别计算：

- 原始：

$$
A_{\mathrm{native}}=\operatorname{softmax}\!\left(\frac{Q_{\mathrm{current}}K_{\mathrm{visible}}^{\top}}{\sqrt{d_h}}\right)
$$

- 替换为：

$$
A_{\mathrm{donor}}=\operatorname{softmax}\!\left(\frac{Q_B^{\mathrm{aligned}}K_{\mathrm{visible}}^{\top}}{\sqrt{d_h}}\right)
$$

历史 B 的 Q 使用当前块的位置编码；两种计算使用同一份可见 K，softmax 沿 key 维度归一化。

**统计目标匹配行为** 按历史块汇总 attention，比较替换前后：

- 对 B 的 attention 是否增加或者减小；
- 对c的attention 是否有增加 或者减小 
  
| 筛选门槛                  | 5 秒 | 15 秒 | 30 秒 | 三个时间持续达标 |
| --------------------- | --- | ---- | ---- | -------- |
| retrival-like head 个数 | 32  | 38   | 25   | 14       |

#### 结果：

##### retrieve-like head

![](Pasted%20image%2020261017175857.png)


5个 prompt普遍在10-15s 出现了重复的现象，漂移现象会稍微晚一点点，
15s，retrieval head 增多 ，30s 后又下降 

出现了部分head 早期有retrieve-like head 行为，后期减弱或者消失

也有 早期head 没有该行为，后期浮现retrieve-like head 行为  

其中 **L17 H9、L20 H4、L28 H9** 是先在 5→15 秒退出，又在 15→30 秒重新达标的  


问题：部分head 行为更替可能属于正常的，不过由于后期确实视频质量下降肯定存在不正常的视频在这里 

##### induction-like head

受 LLM 中 induction heads 的启发，我们进一步观察：**替换为历史 B 的 query 后，是否有 head 增加对 B 后继块 C 的关注。** 

| 指标           | 5 秒 | 15 秒 | 30 秒 | 三个时间均达标 |
| ------------ | --- | ---- | ---- | ------- |
| 后继 C  匹配候选数量 | 10  | 7    | 1    | 0       |

虽然这个实验 意义不明，llm 是用作可解释工作 ，不过这里明显随着时间在下降，后续可能有用 

##### 对b的权重下降的head

同一时刻，替换 Q 后对 B 的关注低于原生 Q 

| 判据               | 5 秒 | 15 秒 | 30 秒 | 三时间共同 |
| ---------------- | --- | ---- | ---- | ----- |
| 五个 prompt 替换后均减少 | 13  | 18   | 17   | 12    |

![](Pasted%20image%2020261017182229.png)

主要解决问题是 排查替换完q后每个head由于内部某种bug全部上升，不过这类head感觉还是挺有价值的，

基本趋势都是增加后稳定，值得注意的是 5s 的 head 在30s都被保留 

#### 局限

只研究了读取历史问题，并且有些head 可能会协同工作，
