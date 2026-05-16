"""
edge-tts MCP Server — 英语学习系统 TTS 发音引擎 (Windows 兼容版)

4 种音色:
  - victoria (en-GB-SoniaNeural)  英音女声 · 温暖 — 主控 Victoria
  - edmund   (en-GB-RyanNeural)   英音男声 · 学者 — 词汇管家 Edmund
  - charlie  (en-US-JennyNeural)  美音女声 · 友好 — 口语伙伴 Charlie
  - beatrice (en-GB-LibbyNeural)  英音女声 · 播报 — 新闻播报 Beatrice

MCP 协议: JSON-RPC 2.0 over stdio
"""
import asyncio
import json
import subprocess
import sys
import tempfile
import threading

import edge_tts

VOICES = {
    "victoria": "en-GB-SoniaNeural",
    "edmund": "en-GB-RyanNeural",
    "charlie": "en-US-JennyNeural",
    "beatrice": "en-GB-LibbyNeural",
}

TOOL_SPEC = {
    "name": "speak",
    "description": "朗读指定文本，支持 4 种角色音色和慢速/正常语速",
    "inputSchema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "要朗读的英文文本",
            },
            "voice": {
                "type": "string",
                "enum": list(VOICES.keys()),
                "description": "角色音色: victoria/edmund/charlie/beatrice",
                "default": "victoria",
            },
            "speed": {
                "type": "string",
                "enum": ["slow", "normal"],
                "description": "语速: slow 慢速 (-20%) / normal 正常",
                "default": "normal",
            },
        },
        "required": ["text"],
    },
}


async def speak(text: str, voice: str = "victoria", speed: str = "normal") -> dict:
    voice_id = VOICES.get(voice, VOICES["victoria"])
    rate = "-20%" if speed == "slow" else "+0%"
    communicate = edge_tts.Communicate(text, voice_id, rate=rate)
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    await communicate.save(tmp.name)
    subprocess.Popen(
        ["powershell", "-c", f"Start-Process '{tmp.name}'"],
        stdout=subprocess.DONT_INHERIT,
        stderr=subprocess.DONT_INHERIT,
    )
    return {"status": "played", "voice": voice, "file": tmp.name}


def send_msg(writer, msg: dict):
    line = json.dumps(msg, ensure_ascii=False) + "\n"
    writer.write(line.encode("utf-8"))
    writer.flush()


def handle_msg(msg: dict) -> dict | None:
    msg_id = msg.get("id")
    method = msg.get("method", "")
    params = msg.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "edge-tts", "version": "1.0.0"},
            },
        }
    elif method == "notifications/initialized":
        return None
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": [TOOL_SPEC]},
        }
    elif method == "tools/call":
        args = params.get("arguments", {})
        try:
            result = asyncio.run(speak(
                text=args.get("text", ""),
                voice=args.get("voice", "victoria"),
                speed=args.get("speed", "normal"),
            ))
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False),
                        }
                    ]
                },
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32603, "message": str(e)},
            }
    else:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }


def main():
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer

    while True:
        line = stdin.readline()
        if not line:
            break
        msg = json.loads(line.decode("utf-8").strip())
        response = handle_msg(msg)
        if response:
            send_msg(stdout, response)


if __name__ == "__main__":
    main()
