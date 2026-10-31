# Suno MR 스킬 — 한국어

[언어 선택](../README.md) · [English](README.en.md) · [日本語](README.ja.md)

유튜브 URL을 입력하면 원곡의 오디오를 가져와 보컬을 분리하고, MP3 반주를 Suno MCP에 업로드합니다. 이어서 업로드된 반주를 입력으로 Suno 커버를 생성하고 모든 결과 링크를 제공합니다.

## 준비물

- **Suno MCP가 설치·연결되어 있고 Suno 계정 로그인이 완료된 상태**여야 합니다. MCP에서 업로드·커버 도구를 사용할 수 있어야 합니다.
- 로컬 스킬, 셸 명령과 MCP 도구를 실행할 수 있는 Codex, Claude Code 또는 호환 에이전트.
- 유튜브 영상 URL, `ffmpeg`와 `ffprobe`, Python 3.10 또는 3.11.
- 오디오 도구: `yt-dlp`, `demucs`, `torch`, `torchaudio`, `numpy`, `scipy`, `soundfile`.

Suno에 아직 연결하지 않았다면 [공식 연결 안내](https://suno.com/mcp)를 참고하세요. 이미 연결돼 있다면 이 단계는 건너뜁니다.

```sh
# Codex: 아직 등록되지 않은 경우
codex mcp add suno --url https://api.suno.com/mcp
codex mcp login suno

# Claude Code: 아직 등록되지 않은 경우
claude mcp add --transport http suno https://api.suno.com/mcp
# Claude Code 세션에서 /mcp를 실행해 Suno에 로그인합니다.
```

Suno MCP 연결은 각 클라이언트의 Suno 계정 승인으로 이뤄집니다. API 키나 다른 사람의 OAuth 클라이언트 ID를 스킬 파일에 넣지 마세요.

## 설치

아래 명령은 macOS/Linux 셸 예시입니다. FFmpeg와 `ffprobe`는 운영체제에 맞게 별도로 설치합니다. 대상 `mr` 디렉터리가 이미 있거나 생성할 수 없으면 해당 복사를 건너뛰어 기존 파일을 보존합니다. 업데이트하려면 기존 내용을 검토한 뒤 직접 교체하세요.

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
  printf '%s\n' 'Codex mr이 이미 있거나 생성할 수 없어 건너뜁니다.'
fi
if mkdir ~/.claude/skills/mr 2>/dev/null; then
  cp -R skills/mr/. ~/.claude/skills/mr/
else
  printf '%s\n' 'Claude Code mr이 이미 있거나 생성할 수 없어 건너뜁니다.'
fi
```

가상환경이 활성화된 셸에서 에이전트를 실행하거나, 데스크톱 앱에서 사용할 경우 에이전트에게 해당 가상환경의 Python 경로를 알려주세요. 첫 분리 때 모델 가중치를 내려받으며, CPU에서는 시간이 걸릴 수 있습니다. 스킬이 목록에 나타나지 않으면 새 세션을 시작합니다.

## 사용

Codex에서 다음처럼 요청합니다.

```text
$mr https://www.youtube.com/watch?v=VIDEO_ID
```

Claude Code에서는 `/mr`을 호출하고 같은 유튜브 URL을 전달합니다. URL 외의 세부 설정은 요청에 맞게 추가할 수 있습니다.

```text
/mr https://www.youtube.com/watch?v=VIDEO_ID
원곡의 진행과 호흡을 유지하고, 전주는 피아노 코드 반주로 해줘.
배우가 멜로디를 부를 수 있게 보컬과 악기 가이드 멜로디는 빼줘.
```

스킬은 **URL → 오디오 다운로드 → 보컬 분리 → MP3 → Suno MCP 업로드 → 무보컬 입력의 인스트루멘털 커버 → 결과 확인** 순서로 진행합니다. 업로드는 전송 성공만으로 완료된 것이 아니며, Suno에서 완료 상태와 재생 링크가 확인돼야 합니다. 오디오를 주고받을 때는 기본적으로 MP3를 사용하고, 다른 형식을 명시하면 그 요청을 우선합니다.

기본 조건은 피아노 전주, 배우가 부를 멜로디 자리를 비워 둔 반주, 원곡 진행과 타이밍 최대 보존입니다. 지원되는 경우 원본 영향도 100%를 요청합니다. 생성된 모든 시안의 링크와 검증 범위를 함께 제공합니다.

Suno에서 생성한 시안을 MP3 파일로 받으려면 **“시안 A를 MP3로 다운로드해 줘”**라고 요청하세요. 스킬이 Suno MCP의 공식 다운로드 도구를 사용합니다. 다운로드 크레딧이 필요한 경우 비용을 먼저 알리고 승인을 받은 후 진행합니다. 로컬에서 분리한 MP3와 Suno가 생성한 MP3는 각각 다른 파일입니다.

## 알아둘 점

- 보컬 분리만으로 피아노나 다른 악기가 연주하는 주선율까지 자동으로 제거되지는 않습니다. 분리본과 생성 결과를 청취해 확인해야 합니다.
- Suno 커버와 원본 영향도 100%는 원곡의 음표·편곡·타이밍이 완전히 같다는 보장이 아닙니다. 자동 태그는 실제 청취 검증을 대신하지 않습니다.
- Suno 생성에는 계정 크레딧이 사용됩니다. 다운로드가 별도 크레딧을 요구하면 도구의 승인 절차를 따릅니다.
- Suno 결과를 저장할 때는 [Suno 이용약관](https://suno.com/terms)의 승인된 다운로드 경로를 사용합니다. 재생 음원을 루프백 녹음하거나 스트림을 추출하는 방법은 이 스킬에서 사용하지 않습니다.
- 업로드 길이는 플랜에 따라 제한됩니다. [Suno 공식 안내](https://help.suno.com/en/articles/6141569)는 Pro/Premier에서 최대 8분을 안내합니다.
- 업로드·가공에 필요한 권한과 [Suno 이용약관](https://suno.com/terms)을 확인하세요. Suno가 콘텐츠를 차단하면 반환된 사유를 보고하고 공식 지원 경로를 이용합니다.
