# Roost — Frontend

React client for **Roost**, an AI-assisted management system for
broiler (meat chicken) farms. Talks to the Django backend for auth,
farm records, and two real AI features: computer-vision chick counting
and a trained market price forecaster. The UI is role-aware — farm
owners see financials and staff management that employees don't.

**Tech stack:** React 19, Vite, Tailwind CSS, React Router, Axios,
Recharts.

## Design

A yellow-and-black palette: near-black (`ink`, `#1A1A18`) as the
dominant "chrome" — sidebar, primary buttons, headings, body text —
over a warm off-white page (`canvas`, `#FAFAF7`), with yellow
(`gold`, `#FFC800`) as the accent. Display type is **Fraunces** (a
warm, characterful serif, loaded from Google Fonts), body type is
**Inter**. An icon-in-a-colored-circle motif carries through the UI
(`IconBadge`).

Colors are defined once as Tailwind tokens in
[`tailwind.config.js`](tailwind.config.js) — components reference
`ink`/`gold`/`canvas` rather than raw hex, so the theme can be
retargeted from that one file.

**Contrast rule worth knowing before you use the accent:** `#FFC800`
on white is only ~1.6:1, so bright yellow works as a *background* on
light surfaces but never as a foreground. In practice:

| Surface | Use |
|---|---|
| Dark chrome (`bg-ink*`) | `text-gold` — ~12:1 |
| White card / `bg-canvas` | `text-gold-dark` (`#7A5E00`) — ~6:1 |
| Any yellow fill | `bg-gold` with `text-ink-darker` — ~12:1 |
| Hover on a yellow fill | `hover:bg-gold-deep` (`#E6B400`) |
| Pale yellow fill | `bg-gold-light` (`#FFEFB0`) + `text-gold-dark` — ~5.3:1 |

Yellow is the *accent*, not a second body color — it marks the active
nav item, the brand mark, the chatbot button and caution surfaces. The
black chrome does the structural work.

`rust` (`#C1440E`) and `mint` (`#1F8A5F`) are kept for danger and
success. They're status colors carrying meaning, not brand colors, so
they stay red and green — but only where they genuinely signal status
(trend up/down, acknowledged, forecast direction, success screens).
Decorative green was removed with the rest of the old theme.

Two places deliberately don't use the accent, and it's worth not
"fixing" them back:

- **Chick-counting detection boxes** ([ChickCounting.jsx](src/pages/ChickCounting.jsx))
  are black with a white halo, not yellow — broiler chicks are
  themselves yellow, so yellow boxes camouflage against the subject.
- **The forecast chart line** ([PricePrediction.jsx](src/pages/PricePrediction.jsx))
  is black with yellow data points, because a 2px `#FFC800` line on a
  white card is invisible.

## Running

```bash
npm ci
npm run dev -- --configLoader native   # http://localhost:5173
```

Set the API URL in `.env` (defaults to `http://localhost:8000`):
```
VITE_API_BASE_URL=http://localhost:8000
```

Needs the Django backend running — see [`../backend/README.md`](../backend/README.md).
No other services to start.

**Note on CORS**: the backend's `CORS_ALLOWED_ORIGINS` defaults to
allowing `localhost`/`127.0.0.1` on ports 3000 and 5173. If you access
the dev server via a different hostname or port, add it to
`CORS_ALLOWED_ORIGINS` in the backend's environment.

## Pages

| Route | Page | Notes |
|---|---|---|
| `/login` | Login | |
| `/register` | Register farm | creates farm + owner |
| `/dashboard` | Dashboard | role-aware (Owner sees price forecast + more) |
| `/batches` | Batches | list + create (create is Owner-only) |
| `/chick-counting` | Chick Counting | upload/drag an image, see count + bounding boxes drawn on the actual image (real Roboflow-hosted model) |
| `/price-prediction` | Price Forecast | **Owner only** — real LSTM+XGBoost forecast: chart, day-by-day breakdown with RSI/MACD/events, model accuracy |
| `/feed` | Feed & Inventory | stock levels + consumption log |
| `/health` | Vaccinations | schedule (Owner) + mark administered (anyone) |
| `/sales` | Sales | **Owner only** |
| `/alerts` | Alerts | filterable, acknowledgeable |
| `/employees` | Staff | **Owner only** — add/deactivate employee accounts |

A floating chatbot widget is available on every authenticated page,
bottom-right.

## Structure

```
src/
├── api/            one file per backend resource, thin wrappers around axios
├── components/     shared UI: Card, Button, Badge, IconBadge, Sidebar, AppShell, ChatbotWidget, ...
├── context/        AuthContext — session state, login/register/logout
├── pages/          one file per route
├── lib/utils.js    small formatting helpers (dates, initials, classnames)
└── App.jsx         route table
```

## Auth

JWT access/refresh tokens are kept in `localStorage`. `src/api/client.js`
attaches the access token to every request and, on a 401, transparently
refreshes it once and retries — if that also fails, it clears the
session and redirects to `/login`.

## Testing status

The production frontend build is checked with:

```bash
npm run build -- --configLoader native
```

Automated API regression tests live in the backend. They cover
authentication, roles, farm isolation, and inventory. Run the commands in
the [root README](../README.md#automated-checks). A browser end-to-end test
suite is not included; live Roboflow inference needs separate verification
with a configured key and a real image.
