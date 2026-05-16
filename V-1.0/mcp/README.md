# mcp — MCP 服务器代码

存放 MCP（Model Context Protocol）服务器的 Python/JS 源码。

| 文件 | 用途 |
|------|------|
| `edge_tts_server.py` | TTS 发音引擎（4 种音色：Victoria/Edmund/Charlie/Beatrice） |

MCP Server 通过 stdio 与 Claude Code 通信，注册在 `settings.json` 的 `mcpServers` 中。
