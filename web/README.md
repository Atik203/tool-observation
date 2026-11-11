# ToolResult-800 web frontend

Next.js app for the ToolResult-800 home page and the 15-slide presentation.

## Live site

- Home: <https://tool-observation.vercel.app>
- Slides: <https://tool-observation.vercel.app/slide>
- Proposal: <https://tool-observation.vercel.app/proposal.pdf>

## Routes

| Route | Purpose |
|---|---|
| `/` | Research landing page: question, design, pilot evidence, limits |
| `/slide` | 16:9 projector-safe deck; keyboard and fullscreen |
| `/slide?slide=7` | Deep link to slide 7 |
| `/proposal.pdf` | Compiled proposal PDF |

## Local development

```powershell
cd G:\PROJECT\tool-observation\web
pnpm install
pnpm dev
```

Open <http://localhost:3000>.

## Build and lint

```powershell
pnpm lint
pnpm build
```

## Deployment

- Vercel project: `tool-observation` (personal scope)
- Root directory: `web`
- Production branch: `main`
- Auto-deploy: push to `main` creates a production deployment
- Manual deploy: `vercel deploy --prod --yes`

## Design

The home page uses the shared HaluRISC-style system (Newsreader, Instrument Sans, JetBrains Mono)
with a distinct **teal + copper + ink** palette. The slide deck is intentionally white and
projector-safe; it is scheduled for a later redesign.
