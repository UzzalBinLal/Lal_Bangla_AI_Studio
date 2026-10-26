import os
import re
import shutil
import asyncio
import tempfile
import subprocess
from pathlib import Path

import edge_tts
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from starlette.background import BackgroundTask
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Lal Bangla AI Video Studio")

VOICES = {
    "male": "bn-BD-PradeepNeural",
    "female": "bn-BD-NabanitaNeural",
}

MAX_UPLOAD = 500 * 1024 * 1024


@app.get("/")
async def home():
    index = BASE_DIR / "index.html"
    if not index.exists():
        return JSONResponse(
            {"message": "Lal Bangla AI Video Studio server is running."}
        )
    return FileResponse(index)


@app.get("/health")
async def health():
    return {"status": "ok", "app": "Lal Bangla AI Video Studio"}


@app.get("/api/voices")
async def voices():
    return {
        "voices": [
            {"id": "male", "name": "বাংলা পুরুষ কণ্ঠ"},
            {"id": "female", "name": "বাংলা নারী কণ্ঠ"},
        ]
    }


def run_command(command):
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=1800,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2500:])
    return result


def make_srt(script, duration, output_path):
    sentences = [
        item.strip()
        for item in re.split(r"(?<=[।.!?])\s*", script)
        if item.strip()
    ]

    if not sentences:
        sentences = [script.strip()]

    sentences = [
        sentences[i] if len(sentences[i]) <= 90
        else sentences[i][:90]
        for i in range(len(sentences))
    ]

    if not sentences or not any(sentences):
        raise ValueError("স্ক্রিপ্ট লিখুন।")

    weights = [max(len(s), 1) for s in sentences]
    total_weight = sum(weights)
    current = 0.0
    blocks = []

    for sentence, weight in zip(sentences, weights):
        start = current
        current += duration * weight / total_weight
        end = min(current, duration)

        def timestamp(seconds):
            milliseconds = int(seconds * 1000)
            hours = milliseconds // 3600000
            minutes = (milliseconds % 3600000) // 60000
            secs = (milliseconds % 60000) // 1000
            millis = milliseconds % 1000
            return (
                f"{hours:02}:{minutes:02}:"
                f"{secs:02},{millis:03}"
            )

        blocks.append(
            f"{len(blocks) + 1}\n"
            f"{timestamp(start)} --> {timestamp(end)}\n"
            f"{sentence}\n"
        )

    output_path.write_text("\n".join(blocks), encoding="utf-8-sig")


@app.post("/api/render")
async def render_video(
    video: UploadFile = File(...),
    script: str = Form(...),
    voice: str = Form("female"),
    ratio: str = Form("9:16"),
    keep_original_audio: str = Form("false"),
):
    if not script.strip():
        raise HTTPException(400, "আগে বাংলা স্ক্রিপ্ট লিখুন।")

    if voice not in VOICES:
        voice = "female"

    if ratio not in ("9:16", "16:9", "1:1"):
        ratio = "9:16"

    if not video.filename:
        raise HTTPException(400, "একটি ভিডিও নির্বাচন করুন।")

    workdir = Path(tempfile.mkdtemp(prefix="lalstudio_"))

    try:
        input_path = workdir / "input_video"
        audio_path = workdir / "voice.mp3"
        srt_path = workdir / "captions.srt"
        output_path = workdir / "lal_bangla_video.mp4"

        size = 0
        with input_path.open("wb") as destination:
            while True:
                chunk = await video.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD:
                    raise HTTPException(
                        413, "ভিডিওটি 500 MB-এর বেশি।"
                    )
                destination.write(chunk)

        if size == 0:
            raise HTTPException(400, "ভিডিও ফাইলটি খালি।")

        try:
            run_command([
                "ffmpeg", "-v", "error", "-i", str(input_path),
                "-f", "null", "-"
            ])
        except Exception:
            raise HTTPException(
                400, "ভিডিওটি পড়া যাচ্ছে না। অন্য ভিডিও চেষ্টা করুন।"
            )

        communicate = edge_tts.Communicate(
            text=script.strip(),
            voice=VOICES[voice],
        )
        await communicate.save(str(audio_path))

        probe = run_command([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(input_path),
        ])
        duration = float(probe.stdout.strip())

        if duration <= 0:
            raise HTTPException(400, "ভিডিওর দৈর্ঘ্য পাওয়া যায়নি।")

        make_srt(script.strip(), duration, srt_path)

        dimensions = {
            "9:16": (720, 1280),
            "16:9": (1280, 720),
            "1:1": (720, 720),
        }
        width, height = dimensions[ratio]

        filter_video = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
            "setsar=1"
        )

        keep_audio = keep_original_audio.lower() in (
            "true", "1", "yes", "on"
        )

        command = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-i", str(audio_path),
            "-i", str(srt_path),
            "-vf", filter_video,
            "-map", "0:v:0",
        ]

        if keep_audio:
            command += [
                "-filter_complex",
                "[0:a]volume=0.20[original];"
                "[1:a]volume=1.0[voice];"
                "[original][voice]amix=inputs=2:duration=first:dropout_transition=2[a]",
                "-map", "[a]",
            ]
        else:
                    command += [
            "-map", "2:0",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-c:s", "mov_text",
            "-t", str(duration),
            "-movflags", "+faststart",
            str(output_path),
        ]
        try:
            run_command(command)
        except Exception as exc:
            raise HTTPException(
                500,
                "ভিডিও তৈরি হয়নি। সার্ভারে FFmpeg ও প্রয়োজনীয় কোডেক "
                "সঠিকভাবে ইনস্টল আছে কি না পরীক্ষা করুন."
            ) from exc

        return FileResponse(
            path=output_path,
            media_type="video/mp4",
            filename="Lal_Bangla_AI_Video.mp4",
            background=BackgroundTask(
                shutil.rmtree, workdir, ignore_errors=True
            ),
        )

    except HTTPException:
        shutil.rmtree(workdir, ignore_errors=True)
        raise
    except Exception as exc:
        shutil.rmtree(workdir, ignore_errors=True)
        raise HTTPException(
            500, f"সার্ভারে সমস্যা হয়েছে: {str(exc)[:300]}"
        ) from exc
    finally:
        await video.close()


# নিজের ল্যাপটপে চালাতে:
# python -m uvicorn server:app --host 0.0.0.0 --port 8000
