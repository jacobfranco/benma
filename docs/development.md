# Local development

## Prerequisites

- Python 3.12 and `uv`
- Node.js 22 and npm
- Docker with Compose
- FFmpeg and FFprobe on `PATH`
- Expo Go or a development build on a phone/simulator

## One-time setup

```bash
cp services/api/.env.example services/api/.env
make benchmark-sync
make api-sync
make mobile-sync
```

The example configuration deliberately selects replay providers. Replay responses are always
marked `synthetic_replay` in persistence, API output, and learner-visible screens.

## Run the stack

Start PostgreSQL and migrate it:

```bash
make api-db-up
make api-migrate
```

Start the API from a second terminal:

```bash
make api-dev
```

Start Expo from a third terminal. A physical device cannot reach the computer through
`127.0.0.1`, so use the computer's LAN address:

```bash
EXPO_PUBLIC_BENMA_API_URL=http://192.168.1.50:8000 make mobile-dev
```

The firewall must allow TCP port 8000 from the local network. Confirm
`http://YOUR_LAN_IP:8000/health` is reachable from the phone before debugging Expo.

## Development account and data

The app calls `POST /v1/dev/auth` with a phone number. This endpoint exists only when
`BENMA_DEV_AUTH_ENABLED=true`, and configuration validation forbids that setting in production.
To pre-create a development account and several targets:

```bash
make api-seed
```

The script prints a newly created session token once for local debugging. It never creates fake
perception or assessment rows.

## Live providers

Select live providers only intentionally in `services/api/.env`:

```dotenv
BENMA_PERCEPTION_PROVIDER=openai
BENMA_OPENAI_API_KEY=...
BENMA_ASSESSMENT_PROVIDER=azure
BENMA_AZURE_SPEECH_KEY=...
BENMA_AZURE_SPEECH_REGION=...
```

Missing credentials cause startup validation to fail. Provider calls remain server-side. No
credential may use an `EXPO_PUBLIC_` variable.

## Contract changes

After changing a FastAPI request or response model, run:

```bash
make openapi
make mobile-check
```

Commit both `apps/mobile/src/api/openapi.json` and
`apps/mobile/src/api/openapi.generated.ts`. Do not edit the generated TypeScript file manually.

## Stop local infrastructure

```bash
make api-db-down
```
