# briefings — 新闻简报

存放 Beatrice 每日抓取的新闻简报和外刊原文。

| 文件/目录 | 用途 |
|-----------|------|
| `YYYY-MM-DD-briefing.md` | 晨间简报（AI 摘要 + 关键词） |
| `YYYY-MM-DD-fulltext.md` | 当日外刊原文（每日轮换一类） |
| `YYYY-MM-DD-sources.md` | 当日抓取的来源记录 |
| `screenshots/` | Playwright 浏览器截图存证 |

由 Beatrice 在每日凌晨 Cron 触发时生成，用户早上通过 `/briefing` 收听。
