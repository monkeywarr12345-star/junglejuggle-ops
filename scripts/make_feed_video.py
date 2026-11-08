#!/usr/bin/env python3
"""Give a feed carousel background music: each rendered card becomes a short 4:5 video slide.

Usage: python scripts/make_feed_video.py content/<id>.json media/<id>
Reads media/<id>/01.jpg, 02.jpg ... and writes media/<id>/v01.mp4, v02.mp4 ... (1080x1350, SLIDE_SEC each).
One track is chosen for the whole post and split across the slides in order, so swiping feels continuous.
Music comes from the card spec's "music" (same options as make_reel.py, default {"auto": "upbeat"});
the CC credit line is written to media/<id>/music_credit.txt and must go into the caption.
Prints the queue "items" list to use: [{"video": "media/<id>/v01.mp4"}, ...].
The Instagram API cannot attach Instagram's own music library to posts, so this is how feed posts get sound.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLIDE_SEC = 7.0


def main(spec_path, media_dir):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    media = Path(media_dir)
    images = sorted(media.glob("[0-9][0-9].jpg"))
    if len(images) < 2:
        raise SystemExit(f"need at least 2 rendered cards in {media}")
    total = SLIDE_SEC * len(images)
    sys.path.insert(0, str(ROOT / "scripts"))
    import make_reel  # same music selection and rotation as reels
    with tempfile.TemporaryDirectory() as tmp:
        audio_in = make_reel.pick_audio({**spec, "music": spec.get("music", {"auto": "upbeat"})}, media / "x.mp4", total, tmp)
        bed = Path(tmp) / "bed.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *audio_in, "-t", f"{total:.2f}",
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2", str(bed)], check=True)
        items = []
        for i, img in enumerate(images):
            out = media / f"v{i + 1:02d}.mp4"
            start = i * SLIDE_SEC
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", str(img),
                "-ss", f"{start:.2f}", "-t", f"{SLIDE_SEC:.2f}", "-i", str(bed),
                "-vf", "scale=1080:1350,format=yuv420p", "-af", f"afade=t=in:d=0.15,afade=t=out:st={SLIDE_SEC - 0.25:.2f}:d=0.25",
                "-t", f"{SLIDE_SEC:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out)], check=True)
            items.append({"video": str(out.relative_to(ROOT))})
    print(json.dumps(items, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
