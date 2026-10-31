# Suno MR スキル — 日本語

[言語選択](../README.md) · [한국어](README.ko.md) · [English](README.en.md)

YouTube の URL を渡すと、音源を取得してボーカルを分離し、MP3 の伴奏を Suno MCP にアップロードします。続いてアップロードした伴奏を入力にインストゥルメンタルのカバーを生成し、すべての結果リンクを返します。

## 必要なもの

- **Suno MCP がインストール・接続済みで、Suno アカウントへのログインが完了していること**。アップロードとカバーのツールが利用できる必要があります。
- ローカルスキル、シェルコマンド、MCP ツールを利用できる Codex、Claude Code、または互換エージェント。
- YouTube 動画の URL、`ffmpeg` と `ffprobe`、Python 3.10 または 3.11。
- 音声ツール：`yt-dlp`、`demucs`、`torch`、`torchaudio`、`numpy`、`scipy`、`soundfile`。

Suno が未接続の場合は[公式接続ガイド](https://suno.com/mcp)を参照してください。接続済みならこの手順は不要です。

```sh
# Codex: コネクタが未登録の場合
codex mcp add suno --url https://api.suno.com/mcp
codex mcp login suno

# Claude Code: コネクタが未登録の場合
claude mcp add --transport http suno https://api.suno.com/mcp
# Claude Code セッション内で /mcp を実行し、Suno にログインします。
```

Suno への接続はクライアントごとにアカウントで承認します。API キーや他人の OAuth クライアント ID をスキルファイルに記載しないでください。

## インストール

以下は macOS/Linux のシェル例です。FFmpeg と `ffprobe` は OS に合わせて別途インストールしてください。コピー先の `mr` ディレクトリが既に存在するか作成できない場合は、そのコピーをスキップして既存ファイルを保持します。更新する場合は既存の内容を確認してから手動で置き換えてください。

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
  printf '%s\n' 'Codex の mr が既に存在するか作成できないためスキップします。'
fi
if mkdir ~/.claude/skills/mr 2>/dev/null; then
  cp -R skills/mr/. ~/.claude/skills/mr/
else
  printf '%s\n' 'Claude Code の mr が既に存在するか作成できないためスキップします。'
fi
```

仮想環境を有効にしたシェルからエージェントを起動するか、デスクトップアプリの場合はその環境の Python の絶対パスをエージェントに伝えてください。初回の分離ではモデルをダウンロードする場合があり、CPU 処理には時間がかかります。スキルが表示されない場合は新しいセッションを開始します。

## 使い方

Codex では URL を渡します。

```text
$mr https://www.youtube.com/watch?v=VIDEO_ID
```

Claude Code では `/mr` を呼び出し、同じ YouTube URL を渡します。音楽上の条件を追加することもできます。

```text
/mr https://www.youtube.com/watch?v=VIDEO_ID
原曲の進行と間を保ち、前奏はピアノのコード伴奏にしてください。
俳優が主旋律を歌えるよう、ボーカルと楽器のガイドメロディーを除いてください。
```

処理の流れは **URL → 音声ダウンロード → ボーカル分離 → MP3 → Suno MCP アップロード → その伴奏を使ったインストゥルメンタルカバー → 結果確認** です。ファイルの転送成功だけでは完了とはせず、Suno の完了状態と再生リンクを確認します。音声の受け渡しは原則 MP3 とし、別形式の明示的な指定を優先します。

基本条件は、ピアノ前奏、演者のために主旋律を空けた伴奏、原曲の進行とタイミングの維持です。対応している場合は音声影響度 100% を指定します。生成されたすべての候補へのリンクと確認範囲を返します。

Suno が生成した候補を MP3 ファイルとして保存するには、**「候補 A を MP3 でダウンロードして」**と依頼してください。スキルは Suno MCP の公式ダウンロードツールを使います。ダウンロードクレジットが必要な場合は、費用を説明して承認を得てから進めます。ローカルで分離した MP3 と Suno が生成した MP3 は別のファイルです。

## 制限

- ボーカル分離だけでは、楽器で演奏されている主旋律は自動的に消えません。分離音源と生成結果を試聴して確認してください。
- Suno のカバーは音声影響度 100% でも、原曲の音符・編曲・タイミングとの完全一致を保証しません。自動タグは試聴検証の代わりにはなりません。
- Suno の生成にはアカウントのクレジットを使用します。ダウンロードに別途クレジットが必要な場合は、ツールの承認手順に従います。
- Suno の結果は [Suno の利用規約](https://suno.com/terms)で認められたダウンロード経路から保存します。再生音のループバック録音やストリーム抽出は、このスキルでは使用しません。
- アップロード可能な長さはプランによって異なります。[Suno の公式ガイド](https://help.suno.com/en/articles/6141569)では Pro/Premier は最大 8 分と案内されています。
- アップロードの上限とカバーの目標時間の範囲は異なります。現在の MCP ではカバーの目標は最大 6 分で、長い曲では目標を省略しても結果が短くなることがあります。アップロードした全長の伴奏と各候補の長さを比較してください。
- 音源のアップロード・加工に必要な権利と [Suno の利用規約](https://suno.com/terms)を確認してください。Suno がコンテンツを拒否した場合は返された理由を報告し、公式サポートを利用します。
