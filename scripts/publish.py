"""Publish the next matter-file episode.

Reads episodes/index.json (main branch), keeps state in site/state.json
(gh-pages branch), synthesizes the next script with edge-tts in a rotating
English accent, keeps only the newest KEEP episodes and rewrites feed.xml.
"""
import asyncio
import datetime as dt
import email.utils
import html
import json
import os
import pathlib
import sys

import edge_tts
from mutagen.mp3 import MP3

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = pathlib.Path(os.environ.get("SITE_DIR", ROOT / "site"))
BASE_URL = os.environ["BASE_URL"].rstrip("/")  # e.g. https://user.github.io/repo
KEEP = int(os.environ.get("KEEP_EPISODES", "7"))
RATE = os.environ.get("TTS_RATE", "+0%")
FEED_TITLE = "Matter File Daily"
FEED_DESC = "One topic a day from the WUDC matter file, read in a different English accent each episode."

# (voice, narrator, where the accent is from) - rotates every episode
VOICES = [
    ("en-GB-RyanNeural", "Ryan", "England"),
    ("en-US-AriaNeural", "Aria", "the United States"),
    ("en-AU-NatashaNeural", "Natasha", "Australia"),
    ("en-IE-ConnorNeural", "Connor", "Ireland"),
    ("en-IN-NeerjaNeural", "Neerja", "India"),
    ("en-ZA-LukeNeural", "Luke", "South Africa"),
    ("en-CA-ClaraNeural", "Clara", "Canada"),
    ("en-NZ-MitchellNeural", "Mitchell", "New Zealand"),
    ("en-SG-LunaNeural", "Luna", "Singapore"),
    ("en-KE-ChilembaNeural", "Chilemba", "Kenya"),
    ("en-NG-EzinneNeural", "Ezinne", "Nigeria"),
    ("en-PH-JamesNeural", "James", "the Philippines"),
    ("en-GB-SoniaNeural", "Sonia", "England"),
    ("en-US-GuyNeural", "Guy", "the United States"),
    ("en-AU-WilliamNeural", "William", "Australia"),
    ("en-IE-EmilyNeural", "Emily", "Ireland"),
    ("en-IN-PrabhatNeural", "Prabhat", "India"),
    ("en-ZA-LeahNeural", "Leah", "South Africa"),
    ("en-CA-LiamNeural", "Liam", "Canada"),
    ("en-NZ-MollyNeural", "Molly", "New Zealand"),
    ("en-SG-WayneNeural", "Wayne", "Singapore"),
    ("en-KE-AsiliaNeural", "Asilia", "Kenya"),
    ("en-NG-AbeoNeural", "Abeo", "Nigeria"),
    ("en-PH-RosaNeural", "Rosa", "the Philippines"),
]
FALLBACK = ("en-GB-SoniaNeural", "Sonia", "England")


def load_state():
    path = SITE / "state.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"next": 1, "published": []}


async def pick_voice(n):
    available = {v["ShortName"] for v in await edge_tts.list_voices()}
    voice = VOICES[(n - 1) % len(VOICES)]
    return voice if voice[0] in available else FALLBACK


async def synth(text, voice, out):
    await edge_tts.Communicate(text, voice, rate=RATE).save(str(out))


def write_feed(state):
    now = email.utils.format_datetime(dt.datetime.now(dt.timezone.utc))
    items = []
    for ep in reversed(state["published"]):
        desc = f"Narrated by {ep['narrator']} ({ep['accent']})."
        if ep["subtopics"]:
            desc += " Subtopics: " + ", ".join(ep["subtopics"]) + "."
        url = f"{BASE_URL}/audio/{ep['file']}"
        items.append(f"""    <item>
      <title>{html.escape(f"{ep['n']:03d}. {ep['title']}")}</title>
      <description>{html.escape(desc)}</description>
      <guid isPermaLink="false">matter-file-{ep['n']:03d}</guid>
      <pubDate>{ep['pubDate']}</pubDate>
      <enclosure url="{html.escape(url)}" length="{ep['bytes']}" type="audio/mpeg"/>
      <itunes:duration>{ep['seconds']}</itunes:duration>
      <itunes:episode>{ep['n']}</itunes:episode>
    </item>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{FEED_TITLE}</title>
    <link>{BASE_URL}/</link>
    <description>{FEED_DESC}</description>
    <language>en</language>
    <lastBuildDate>{now}</lastBuildDate>
    <itunes:author>Matter File Daily</itunes:author>
    <itunes:image href="{BASE_URL}/cover.png"/>
    <itunes:explicit>false</itunes:explicit>
    <itunes:block>Yes</itunes:block>
{chr(10).join(items)}
  </channel>
</rss>
"""
    (SITE / "feed.xml").write_text(feed)


def main():
    index = json.loads((ROOT / "episodes" / "index.json").read_text())
    state = load_state()
    n = state["next"]
    if n > len(index):
        print("All episodes already published.")
        write_feed(state)
        return
    ep = index[n - 1]
    voice, narrator, accent = asyncio.run(pick_voice(n))
    script = (ROOT / ep["file"]).read_text()
    first, rest = script.split("\n", 1)
    text = f"{first}\nToday's narrator is {narrator}, from {accent}.\n{rest}"

    (SITE / "audio").mkdir(parents=True, exist_ok=True)
    fname = f"{n:03d}.mp3"
    out = SITE / "audio" / fname
    asyncio.run(synth(text, voice, out))

    state["published"].append({
        "n": n, "title": ep["title"], "subtopics": ep["subtopics"], "file": fname,
        "narrator": narrator, "accent": accent, "voice": voice,
        "bytes": out.stat().st_size, "seconds": int(MP3(out).info.length),
        "pubDate": email.utils.format_datetime(dt.datetime.now(dt.timezone.utc)),
    })
    # rolling window: old audio leaves the server (and Pocket Casts) automatically
    while len(state["published"]) > KEEP:
        old = state["published"].pop(0)
        (SITE / "audio" / old["file"]).unlink(missing_ok=True)
    state["next"] = n + 1
    (SITE / "state.json").write_text(json.dumps(state, indent=1, ensure_ascii=False))
    write_feed(state)
    print(f"Published episode {n}: {ep['title']} ({voice}, {state['published'][-1]['seconds']}s)")


if __name__ == "__main__":
    sys.exit(main())
