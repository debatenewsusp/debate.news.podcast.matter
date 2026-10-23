# Matter File Daily

Podcast privado: um tópico do *Vietnam WUDC Matter File* por dia, na ordem do arquivo, cada episódio lido num sotaque de inglês diferente.

## Como funciona

- `episodes/` tem os 148 roteiros já prontos para fala (`001.txt` a `148.txt`) e o `index.json` com títulos e subtópicos.
- `.github/workflows/daily-episode.yml` roda todo dia às 05:41 (horário de São Paulo), ou na hora pelo botão **Run workflow** na aba Actions.
- `scripts/publish.py` pega o próximo roteiro, gera o mp3 com `edge-tts` (gratuito), atualiza o `feed.xml` e mantém só os 7 episódios mais recentes.
- O site (feed + áudios) fica na branch `gh-pages`, reescrita do zero a cada publicação, então o repositório não cresce.

## Feed para o Pocket Casts

`https://debatenewsusp.github.io/debate.news.podcast.matter/feed.xml`

## Ajustes rápidos

- Horário: mude a linha `cron` no workflow (está em UTC).
- Velocidade da voz: adicione `TTS_RATE: "+10%"` no passo *Generate next episode*.
- Quantos episódios ficam no feed: `KEEP_EPISODES`.
- Voltar para um episódio: edite `next` em `state.json` na branch `gh-pages`.
