# Deploy — ready to push, not yet deployed

## What Muse already did (no user action needed)
- public_server.py: A2A card, /a2a, /mcp, /health, SQLite call log. Python stdlib only, no dependencies.
- catalog.json: Sight Words, Grade 1, Reading, creator Birkan Yavuz.
- agent-card.json, registry-server.json: drafts for A2A discovery and MCP registry.
- test_public_server.py: local test passed, 4 calls logged.

## What Muse can do next, alone, once a hosting account exists
- Create the repo, push all files above, set the public URL in agent-card.json (replace example.invalid), run the server with HOST=0.0.0.0 PORT=$PORT, test the public URL the same way as the local test, submit registry metadata.

## What only Birkan can do (identity steps, ~5 minutes total)
1. Create / confirm a GitHub account in his own name — signup form, secure password via Secure Vault, and the email verification code sent to his inbox. Muse cannot verify an email sent to Birkan, cannot agree to terms as Birkan, and cannot solve a CAPTCHA / phone check if GitHub shows one.
2. If hosting asks for payment / phone verification, approve that himself — Muse will not enter payment details without his explicit approval for that specific charge.
3. Username decision, Oct 29, 2026: Birkan said "forget about conmordak" for this GitHub project and signed in with birkanyavuz@gmail.com — use the existing GitHub account birkanyavuz, repo github.com/birkanyavuz/educational-tools, registry name io.github.birkanyavuz.educational-tools. Do not create a conmordak GitHub account and do not rename the birkanyavuz account.

That is it. Everything else — code, card, registry file, README, deploy config, testing, logging — is Muse's job, and most of it is already done in this folder.
