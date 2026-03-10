#!/usr/bin/env python3
"""AI Server Dashboard — FastAPI backend."""

import asyncio
import json
from pathlib import Path

import docker
import httpx
import psutil
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="AI Dashboard")

STATIC_DIR = Path(__file__).parent / "static"

SERVICES = [
    {
        "id": "open-webui",
        "name": "Open WebUI",
        "desc": "Чат с LLM",
        "port": 3443,
        "https": True,
        "link_port": 3443,
        "link_https": True,
        "icon": "chat",
        "container": "open-webui",
    },
    {
        "id": "voice-assistant",
        "name": "Голосовой ассистент",
        "desc": "Голосовой чат с ИИ",
        "port": 3444,
        "https": True,
        "link_port": 3444,
        "link_https": True,
        "icon": "mic",
        "container": "voice-assistant",
    },
    {
        "id": "comfyui",
        "name": "ComfyUI",
        "desc": "Генерация изображений",
        "port": 8188,
        "https": False,
        "link_port": 8188,
        "link_https": False,
        "icon": "image",
        "container": "comfyui",
    },
    {
        "id": "perplexica",
        "name": "Perplexica",
        "desc": "ИИ-поиск в интернете",
        "port": 3001,
        "https": False,
        "link_port": 3001,
        "link_https": False,
        "icon": "search",
        "container": "perplexica-perplexica-1",
    },
    {
        "id": "ollama",
        "name": "Ollama",
        "desc": "LLM бэкенд (API)",
        "port": 11434,
        "https": False,
        "link_port": 11434,
        "link_https": False,
        "icon": "brain",
        "container": "ollama",
    },
    {
        "id": "whisper",
        "name": "Whisper STT",
        "desc": "Распознавание речи",
        "port": 9000,
        "https": False,
        "link_port": 9000,
        "link_https": False,
        "icon": "hearing",
        "container": "whisper",
    },
    {
        "id": "openedai-speech",
        "name": "OpenedAI Speech",
        "desc": "Синтез речи (TTS)",
        "port": 8100,
        "https": False,
        "link_port": 8100,
        "link_https": False,
        "icon": "volume_up",
        "container": "openedai-speech",
    },
    {
        "id": "fish-speech",
        "name": "Fish Speech",
        "desc": "Продвинутый TTS / клонирование голоса",
        "port": 8200,
        "https": False,
        "link_port": 8200,
        "link_https": False,
        "icon": "graphic_eq",
        "container": "fish-speech",
    },
    {
        "id": "moshi",
        "name": "Moshi",
        "desc": "Голосовой диалог (realtime)",
        "port": 8998,
        "https": False,
        "link_port": 8998,
        "link_https": False,
        "icon": "record_voice_over",
        "container": "moshi",
    },
]


# ── GPU ──────────────────────────────────────────────────────────
@app.get("/api/gpu")
async def gpu_info():
    try:
        proc = await asyncio.create_subprocess_exec(
            "nvidia-smi",
            "--query-gpu=name,memory.used,memory.total,memory.free,temperature.gpu,utilization.gpu,power.draw,power.limit,driver_version",
            "--format=csv,noheader,nounits",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        parts = [p.strip() for p in stdout.decode().strip().split(",")]
        return {
            "name": parts[0],
            "vram_used": int(parts[1]),
            "vram_total": int(parts[2]),
            "vram_free": int(parts[3]),
            "temp": int(parts[4]),
            "util": int(parts[5]),
            "power_draw": float(parts[6]),
            "power_limit": float(parts[7]),
            "driver": parts[8],
        }
    except Exception as e:
        return {"error": str(e)}


# ── System ───────────────────────────────────────────────────────
@app.get("/api/system")
async def system_info():
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "cpu_count": psutil.cpu_count(),
        "ram_used": mem.used,
        "ram_total": mem.total,
        "ram_percent": mem.percent,
        "disk_used": disk.used,
        "disk_total": disk.total,
        "disk_percent": disk.percent,
    }


# ── Docker containers ────────────────────────────────────────────
@app.get("/api/containers")
async def containers():
    try:
        client = docker.from_env()
        result = []
        for c in client.containers.list(all=True):
            result.append(
                {
                    "name": c.name,
                    "status": c.status,
                    "image": c.image.tags[0] if c.image.tags else str(c.image.short_id),
                    "uptime": c.attrs["State"].get("StartedAt", ""),
                }
            )
        return sorted(result, key=lambda x: x["name"])
    except Exception as e:
        return {"error": str(e)}


# ── Service health ───────────────────────────────────────────────
@app.get("/api/services")
async def services_status():
    async def probe(svc):
        proto = "https" if svc["https"] else "http"
        url = f"{proto}://localhost:{svc['port']}"
        try:
            async with httpx.AsyncClient(verify=False, timeout=3) as client:
                r = await client.get(url)
                online = r.status_code < 500
        except Exception:
            online = False
        return {**svc, "online": online}

    results = await asyncio.gather(*(probe(s) for s in SERVICES))
    return list(results)


# ── Ollama models ────────────────────────────────────────────────
@app.get("/api/ollama/models")
async def ollama_models():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get("http://localhost:11434/api/tags")
            return r.json()
    except Exception as e:
        return {"error": str(e)}


class PullRequest(BaseModel):
    name: str


@app.post("/api/ollama/pull")
async def ollama_pull(req: PullRequest):
    async def stream():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                "http://localhost:11434/api/pull",
                json={"name": req.name},
            ) as r:
                async for line in r.aiter_lines():
                    if line.strip():
                        yield f"data: {line}\n\n"
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


class DeleteRequest(BaseModel):
    name: str


@app.post("/api/ollama/delete")
async def ollama_delete(req: DeleteRequest):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.request(
                "DELETE",
                "http://localhost:11434/api/delete",
                json={"name": req.name},
            )
            return {"status": "ok" if r.status_code == 200 else "error", "code": r.status_code}
    except Exception as e:
        return {"error": str(e)}


# ── Docker control ───────────────────────────────────────────────
@app.post("/api/containers/{name}/restart")
async def restart_container(name: str):
    try:
        client = docker.from_env()
        c = client.containers.get(name)
        c.restart(timeout=30)
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/containers/{name}/stop")
async def stop_container(name: str):
    try:
        client = docker.from_env()
        c = client.containers.get(name)
        c.stop(timeout=30)
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/containers/{name}/start")
async def start_container(name: str):
    try:
        client = docker.from_env()
        c = client.containers.get(name)
        c.start()
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}


# ── Static / SPA ─────────────────────────────────────────────────
@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
