
参考论文：Interpretability in the Wild: a Circuit for Indirect Object Identification in GPT-2 small 

根据 self-forcing代码：某个 Head 对 residual stream 的贡献 
![](Pasted%20image%2020261017184247.png)

**假设：**

不同 attention head 向 residual stream 写入的信息规模不同，其绝对输出规模和相对占比可能随着视频生成时间发生变化。  


**实验目的：**

观察各 head 在长视频生成中的输出动态，区分哪些 head 持续较强、随时间增强或减弱

1. 固定 Self-Forcing DMD 的 EMA 权重，对之前的 **5 个 prompt**，使用 **seed 0**，各生成一条约 30 秒的视频。
    
2. 沿用 **21 latent 帧滚动缓存、sink=0**，在每个时间段对应生成块的**第一去噪步**进行观测。
    
3. 使用原生 Q，观察全部 **30 层 × 12 heads，共 360 个 head**；每个 latent 帧均匀抽样 8 个空间 query。
    
4. 记录模型实际 attention 输出，按 head 拆分输出投影，再乘 self-attention gate，计算实际写入残差流的向量。
    
5. 在各时间点分别对五个 prompt 等权汇总，并按同一个 prompt 配对比较时间变化。


  结果：取5s输出强度当作baseline，分析15s，30s 
  
![](https://acnz6psqyqe6.feishu.cn/space/api/box/stream/download/asynccode/?code=ZTczMWM2Y2Y2NjBmMGZkMTJhMzBkMGUxYzNiMjU1NDBfSE1rWHpwU1lrcnBtVkJkZ2dRYWRBWkNjUG5nY3hxcHpfVG9rZW46U2hwT2I4Rkd4b0tIR094ZnZrVmNEV0pwbkRjXzE3OTIyNDA1NDc6MTc5MjI0NDE0N19WNA&add_watermark=true&scene_type=CCM)

和Q1聚类实验结果：

|   |   |   |   |   |
|---|---|---|---|---|
|分组|head 数量占比|5 秒输出范数占比|15 秒|30 秒|
|C0：偏历史读取|56.11%|51.08%|52.32%|52.94%|
|C1：偏当前块读取|43.89%|48.92%|47.68%|47.06%|

发现C0 正在逐步上升，且跨prompt稳定，


和Q2对比：

响应与输出共同增强的 heads

|   |   |   |   |
|---|---|---|---|
|类型|数量|C0|C1|
|retrieval-like head|5|L6 H4、L6 H8、L10 H5、L21 H6、L25 H2|无|
|induction-like head|3|L21 H5、L28 H3|L27 H10| 



存在**早期未达标、后期达标，且输出范数增强**的 head：

| 类型             | Head          | 聚类  |
| -------------- | ------------- | --- |
| retrieval-like | L6 H4、L10 H5  | C0  |
| induction-like | L21 H5、L28 H3 | C0  |
| induction-like | L27 H10       | C1  |

### 单prompt 对应分析：ongoing

