# vocabulary — 词汇库

存放每个英语单词的结构化 JSON 词条文件。

| 文件 | 用途 |
|------|------|
| `index.json` | 总索引：记录每个词的状态、领域、来源、SRS 阶段 |
| `{word}.json` | 单个词条：释义、例句、词源、TTS 音频路径等 |

由 Edmund 负责查询和写入，Charlie 读取用于口语激活，Victoria 读取用于 SRS 复习调度。
