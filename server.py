import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.analyzer import Analyzer, MediaInfo
from core.downloader import Downloader
from services.format_service import FormatItem, parse_video_formats, parse_audio_formats

# Configuration
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="MediaFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_jobs: Dict[str, Dict[str, Any]] = {}
active_websockets: Dict[str, WebSocket] = {}

class AnalyzeRequest(BaseModel):
    url: str

class FormatItemModel(BaseModel):
    format_id: str
    label: str
    kind: str
    ext: str
    resolution: str = ""
    fps: int | None = None
    vcodec: str = ""
    acodec: str = ""
    abr: float | None = None
    filesize: int | None = None
    width: int = 0
    height: int = 0
    quality_sort: int = 0

class DownloadRequest(BaseModel):
    url: str
    format_item: FormatItemModel
    raw_formats: list[dict]
    is_audio_only: bool = False
    audio_format: str = "mp3"
    audio_bitrate: str = "192"

class CookieUpload(BaseModel):
    cookies_text: str

COOKIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")
COOKIE_FILE = Path(COOKIES_PATH)

@app.post("/api/cookies")
def upload_cookies(req: CookieUpload):
    """Save YouTube cookies (Netscape format) to enable authenticated downloads."""
    text = req.cookies_text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Le contenu des cookies est vide.")
    
    # Basic validation: check for tab-separated lines
    has_data = any(
        "\t" in line
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )
    if not has_data:
        raise HTTPException(
            status_code=400,
            detail="Format invalide. Utilisez le format Netscape (fichier cookies.txt exporté depuis votre navigateur)."
        )
    
    # Python's http.cookiejar (used by yt-dlp) silently ignores the file
    # if it doesn't start with the exact magic header comment.
    if not text.startswith("# Netscape HTTP Cookie File") and not text.startswith("# HTTP Cookie File"):
        text = "# Netscape HTTP Cookie File\n" + text
    
    COOKIE_FILE.write_text(text, encoding="utf-8")
    return {"success": True, "message": "Cookies enregistrés. Les téléchargements YouTube devraient fonctionner."}

@app.get("/api/cookies/status")
def cookies_status():
    """Check if valid cookies are configured."""
    has_cookies = os.path.exists(COOKIES_PATH) and os.path.getsize(COOKIES_PATH) > 0
    return {"has_cookies": has_cookies}

@app.delete("/api/cookies")
def delete_cookies():
    """Remove saved cookies."""
    if COOKIE_FILE.exists():
        COOKIE_FILE.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
    return {"success": True, "message": "Cookies supprimés."}

@app.post("/api/analyze")
def analyze_url(req: AnalyzeRequest):
    try:
        analyzer = Analyzer()
        media_info = analyzer.analyze(req.url)
        video_formats = parse_video_formats(media_info.formats)
        audio_formats = parse_audio_formats(media_info.formats)

        return {
            "success": True,
            "media": {
                "url": media_info.url,
                "title": media_info.title,
                "platform": media_info.platform,
                "uploader": media_info.uploader,
                "duration": media_info.duration,
                "duration_str": media_info.duration_str,
                "thumbnail_url": media_info.thumbnail_url,
                "webpage_url": media_info.webpage_url,
            },
            "video_formats": video_formats,
            "audio_formats": audio_formats,
            "raw_formats": media_info.formats
        }
    except Exception as e:
        msg = str(e)
        if "Failed to extract any player response" in msg:
            raise HTTPException(status_code=400, detail=(
                "Échec YouTube : yt-dlp ne parvient pas à extraire la réponse du player.\n"
                "Solutions : 1) Mettez à jour yt-dlp (pip install -U yt-dlp)\n"
                "2) Exportez vos cookies YouTube et placez-les dans cookies.txt\n"
                "3) Réessayez dans quelques minutes."
            ))
        raise HTTPException(status_code=400, detail=msg)

async def process_download(job_id: str, req: DownloadRequest):
    downloader = Downloader(
        embed_metadata=True,
        download_thumbnail=True,
        download_subtitles=False,
        overwrite=True
    )
    
    active_jobs[job_id]["downloader"] = downloader
    
    def on_progress(pct: float, downloaded: int, total: int | None, speed: float | None, eta: float | None):
        loop = active_jobs[job_id].get("loop")
        if loop and not loop.is_closed():
            payload = {
                "type": "progress",
                "percent": pct,
                "downloaded": downloaded,
                "total": total,
                "speed": speed,
                "eta": eta
            }
            asyncio.run_coroutine_threadsafe(broadcast_status(job_id, payload), loop)

    def on_status(msg: str):
        loop = active_jobs[job_id].get("loop")
        if loop and not loop.is_closed():
            payload = {"type": "status", "message": msg}
            asyncio.run_coroutine_threadsafe(broadcast_status(job_id, payload), loop)

    try:
        f_item = FormatItem(**req.format_item.model_dump())
        
        # Determine loop context
        loop = asyncio.get_running_loop()
        active_jobs[job_id]["loop"] = loop

        if req.is_audio_only:
             final_path = await asyncio.to_thread(
                 downloader.download_audio,
                 req.url,
                 req.audio_format,
                 req.audio_bitrate,
                 f_item,
                 str(DOWNLOAD_DIR),
                 on_progress,
                 on_status
             )
        else:
            final_path = await asyncio.to_thread(
                 downloader.download_video,
                 req.url,
                 f_item,
                 str(DOWNLOAD_DIR),
                 req.raw_formats,
                 on_progress,
                 on_status
             )
             
        active_jobs[job_id]["status"] = "completed"
        active_jobs[job_id]["file_path"] = str(final_path)
        
        if loop and not loop.is_closed():
             asyncio.run_coroutine_threadsafe(broadcast_status(job_id, {
                 "type": "completed",
                 "file_path": str(final_path),
                 "job_id": job_id
             }), loop)

    except Exception as e:
        msg = str(e)
        if "Failed to extract any player response" in msg:
            msg = (
                "Échec YouTube : yt-dlp ne parvient pas à extraire la réponse du player.\n"
                "Solutions : 1) Mettez à jour yt-dlp (pip install -U yt-dlp)\n"
                "2) Exportez vos cookies YouTube et placez-les dans cookies.txt\n"
                "3) Réessayez dans quelques minutes."
            )
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["error"] = msg
        loop = active_jobs[job_id].get("loop")
        if loop and not loop.is_closed():
             asyncio.run_coroutine_threadsafe(broadcast_status(job_id, {
                 "type": "error",
                 "message": msg
             }), loop)

async def broadcast_status(job_id: str, data: dict):
    ws = active_websockets.get(job_id)
    if ws:
        try:
            await ws.send_json(data)
        except Exception:
            pass

@app.post("/api/download")
async def start_download(req: DownloadRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    active_jobs[job_id] = {
        "status": "starting",
        "file_path": None,
        "error": None
    }
    background_tasks.add_task(process_download, job_id, req)
    return {"job_id": job_id}

@app.websocket("/ws/download/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    active_websockets[job_id] = websocket
    
    # Send current status immediately
    job = active_jobs.get(job_id)
    if job:
        if job["status"] == "completed":
            await websocket.send_json({"type": "completed", "file_path": job["file_path"], "job_id": job_id})
        elif job["status"] == "failed":
            await websocket.send_json({"type": "error", "message": job["error"]})
        else:
             await websocket.send_json({"type": "status", "message": "Connecté au suivi de téléchargement"})
             
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if job_id in active_websockets:
            del active_websockets[job_id]

@app.get("/api/files/{job_id}")
def get_file(job_id: str):
    job = active_jobs.get(job_id)
    if not job or not job.get("file_path"):
         raise HTTPException(status_code=404, detail="File not found or download not finished")
    
    file_path = Path(job["file_path"])
    if not file_path.exists():
         raise HTTPException(status_code=404, detail="File deleted or moved")

    return FileResponse(path=file_path, filename=file_path.name, media_type='application/octet-stream')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
