# AI新闻速递 — 2026-09-10 晚间

> 生成时间：2026-09-10 22:19 (Asia/Shanghai)
> 来源：kimi_search 全网搜索

---

## 1. 具身ICL成创业新赛道：Skild AI S1让机器人看一遍就会新任务

- **来源**：量子位
- **链接**：<https://www.qbitai.com/2026/09/484897.html>
- **摘要**：Skild AI 发布机器人基础模型 S1，只需给机器人看一遍任务演示视频，无需微调即可尝试完成未训练过的新任务，任务时长可达10分钟、包含几十个步骤。测试显示，在未见过的任务上，加入视频 context 后的表现比纯语言指令提升约7倍，且数据规模越大 ICL 优势越明显。同期 Generalist AI 的 GEN-1.5 同样主打 One-Shot 模仿学习，支持人类示范到机器人执行与 Sim-to-Real 迁移。背景是李飞飞、Jim Fan 等7月提出的 RoboTTT 首次系统地把"上下文 scaling"搬到机器人视觉运动策略。具身上下文是每秒几十帧视觉加本体状态和动作序列，信息量远超文本，如何高效压缩与利用长多模态 context 成为新 Scaling 方向，国内已有可可矩阵等创业公司专门押注。

---

## 2. Phi-WM ActEffect：世界模型训练完就"退场"，机器人反而更能干

- **来源**：量子位 / 亿欧 / 雷峰网
- **链接**：<https://www.qbitai.com/2026/09/484611.html>
- **摘要**：光象科技联合清华大学李升波教授课题组发布物理原生世界模型 Phi-WM 1.0 ActEffect，核心思路一反常态：世界模型只存在于训练阶段，专门检查机器人提出的动作会造成什么后果并给出优化反馈，训练完成后直接退出部署链路，执行时不再展开未来预测、不搜索候选动作，从而显著降低时延、算力和成本。方法上让策略产出前馈、MIP 粗提案、精修动作三版完整候选，由受控世界模型分别预测后果再择优。在 LIBERO 基准上平均成功率达 98.8%，加入七类分布偏移的 LIBERO-PLUS 达 80.3%，29 维动作空间的 RoboCasa-GR1 达 67.5%。这为工业场景"训练用重模型、部署用轻策略"提供了可落地的新范式，已在汽车制造等真实产线验证。

---

## 3. OpenAI、Anthropic、Google 三大 AI 服务 9月3日同时宕机

- **来源**：Foxxe Labs / Daily LLM News
- **链接**：<https://foxxelabs.ie/news/openai-anthropic-and-google-all-report-major-ai-service-disruptions-on-september-3-2026/>
- **摘要**：9月3日，OpenAI（ChatGPT、Codex）、Anthropic（Claude Sonnet 5）和 Google（Gemini）三家主要 AI 提供商在同一时段内相继报告服务中断，影响消费者界面、开发者 API、图像生成工具和账户创建流程。OpenAI 于 UTC 10:58 发现问题，工程师在约24分钟内缓解，11:22 恢复；Anthropic 的故障持续约25分钟；Google Gemini 则耗时约2小时才完全解决。事件引发了对 AI 行业基础设施集中化风险的广泛讨论——尽管各家 2026 年可用性均在 99.9% 以上，但提示词在不同模型间往往无法产生等效输出，真正的多提供商冗余需要远超"多备一个 API Key"的工程投入。

---

*本文件由 OpenClaw 自动生成，每日定时推送。*
