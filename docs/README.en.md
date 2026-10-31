# Suno MR Skill — English

[Choose language](../README.md) · [한국어](README.ko.md) · [日本語](README.ja.md)

Give the agent a YouTube URL. It obtains the audio, separates the vocals, and uploads an MP3 accompaniment through Suno MCP. It then uses the uploaded accompaniment to request an instrumental cover and returns every generated link.

## Requirements

- **Suno MCP must already be installed, connected, and signed in to a Suno account**, with upload and cover tools available.
- Codex, Claude Code, or another agent host that can load local skills, run shell commands, and call MCP tools.
- A YouTube video URL, `ffmpeg` and `ffprobe`, and Python 3.10 or 3.11.
- Audio tools: `yt-dlp`, `demucs`, `torch`, `torchaudio`, `numpy`, `scipy`, and `soundfile`.

If Suno is not connected yet, follow [Suno's setup guide](https://suno.com/mcp). Skip this step when it is already connected.

```sh
# Codex: only if the connector is not registered yet
codex mcp add suno --url https://api.suno.com/mcp
codex mcp login suno

# Claude Code: only if the connector is not registered yet
claude mcp add --transport http suno https://api.suno.com/mcp
# Run /mcp in a Claude Code session to sign in to Suno.
```

Each client authorizes its own Suno connection. Do not put API keys or another user's OAuth client ID in the skill files.

## Install

These commands are for a macOS/Linux shell. Install FFmpeg and `ffprobe` separately for your operating system. If a target `mr` directory already exists or cannot be created, the corresponding copy is skipped and existing files are preserved. To update an existing skill, review it before replacing it yourself.

```sh
git clone https://github.com/kaura24/suno-mr-skill.git
cd suno-mr-skill

python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install 'yt-dlp' 'numpy<2' 'torch==2.2.2' 'torchaudio==2.2.2' 'demucs==4.0.1' scipy soundfile

mkdir -p ~/.codex/skills ~/.claude/skills
if mkdir ~/.codex/skills/mr 2>/dev/null; then
  cp -R skills/mr/. ~/.codex/skills/mr/
else
  printf '%s\n' 'Codex mr already exists or cannot be created; skipping.'
fi
if mkdir ~/.claude/skills/mr 2>/dev/null; then
  cp -R skills/mr/. ~/.claude/skills/mr/
else
  printf '%s\n' 'Claude Code mr already exists or cannot be created; skipping.'
fi
```

Start the agent from the activated environment, or tell a desktop agent the absolute path to that environment's Python interpreter. The first separation may download model weights; CPU processing can take time. Start a new session if the skill does not appear.

## Use

In Codex, provide the URL:

```text
$mr https://www.youtube.com/watch?v=VIDEO_ID
```

In Claude Code, invoke `/mr` and provide the same YouTube URL. You may add specific musical requirements:

```text
/mr https://www.youtube.com/watch?v=VIDEO_ID
Keep the original progression and phrasing. Use piano chords in the intro.
Remove the vocals and instrumental guide melody so an actor can sing the lead.
```

The pipeline is **URL → audio download → vocal separation → MP3 → Suno MCP upload → instrumental cover using that accompaniment → result checks**. A successful file transfer is not enough: the agent waits for Suno's completed status and a playable link. Audio is exchanged as MP3 by default; an explicit request for another format takes precedence.

Defaults are a piano intro, an empty melodic lead for the performer, and preservation of the source progression and timing as closely as possible. Where supported, the agent requests 100% audio influence. It returns links for all generated takes and states what was checked.

## Limits

- Vocal separation alone does not remove a lead melody already played by an instrument. Listen to the separated track and generated results.
- A Suno cover, even at 100% audio influence, is not guaranteed to reproduce the original notes, arrangement, or timing exactly. Automated tags are not a substitute for listening.
- Suno generation uses account credits. If a download requires a separate credit, follow the tool's approval flow.
- Upload duration depends on the plan. [Suno's official guide](https://help.suno.com/en/articles/6141569) states up to eight minutes on Pro/Premier.
- Ensure you have the rights needed to upload and modify the source and comply with [Suno's terms](https://suno.com/terms). If Suno blocks content, report the returned reason and use its official support path.
