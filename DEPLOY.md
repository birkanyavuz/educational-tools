# Deploy — live topology (verified Nov 11, 2026)

## What actually serves the site
- Vercel project `educational-tools`, repo `birkanyavuz/educational-tools`, branch `main`, Root Directory `./` (repo root), Framework Other, no build command.
- Exactly ONE serverless function: `/api/index`, built from the repo-root file `api/index.py`. `vercel.json` at the repo root rewrites `/(.*)` to `/api/index`, so the one function serves every route (`/mcp`, `/api/*`, `/health`, `/.well-known/*`).
- Static files (`agent-card.json`, `llms-full.txt`, `README.md`, `catalog.json`, `datasets.json`) are served from the repo root.
- A push to `main` auto-deploys in seconds (8s builds observed). Verify live after every release with your own reads: MCP `initialize` serverInfo version, `/health`, and a real tool call — never trust the dashboard's "Ready" alone.

## The four server copies — keep them byte-identical on EVERY release
1. `api/index.py` — THE LIVE ONE. This is what Vercel builds. Forgetting it leaves the live server on the old version while everything else says the new one.
2. `deploy-vercel/api/index.py` — legacy copy, NEVER executed. Kept in sync only so no one mistakes it for the deploy file again.
3. `public_server.py` — standalone server for local tests (`test_tools_call.py` runs this one).
4. `server_v2.py` — second standalone copy, same content.

LESSON (v1.7.4, Nov 11, 2026): the release shipped `datasets.json`, `server_v2.py`, `public_server.py`, `deploy-vercel/api/index.py` and the docs — but NOT root `api/index.py`, because the local hub had no `api/` directory and no `vercel.json` (the hub was a partial mirror of the repo). The dashboard showed the deployment Ready and the static files showed 1.7.4, but the live function stayed on 1.7.3 for over an hour until a deployment inspection found the second copy. The local hub now mirrors the repo (`api/index.py`, `vercel.json` included); if a file exists on GitHub but not in the hub, the release checklist is incomplete.

## Release checklist
- Bump the version in all four server copies + `agent-card.json` + `server.json` + `registry-server.json` + README + `llms-full.txt` + HF card.
- Upload every changed file to GitHub, INCLUDING root `api/index.py`.
- Verify live yourself: `initialize` version, `/health`, one real `tools/call` proving the new behavior.
- Pin the README release-commit line to the final release HEAD, then upload the pinned README.
- Registry publish is a separate step (mcp-publisher login); if it fails, retry at a later round, never by hammering.

## What only Birkan can do (identity steps)
1. GitHub account in his own name — signup form, secure password via Secure Vault, and the email verification code sent to his inbox. Use the existing GitHub account birkanyavuz, repo github.com/birkanyavuz/educational-tools, registry name io.github.birkanyavuz/educational-tools. Do not create a conmordak GitHub account and do not rename the birkanyavuz account. (Username decision, Oct 29, 2026: Birkan said "forget about conmordak" for this GitHub project.)
2. If hosting asks for payment / phone verification, approve that himself — Muse will not enter payment details without his explicit approval for that specific charge.
