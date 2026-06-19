# Engram MAP: Sovereign Agent Audit in a Box

This is the 7-day, $0-spend smoke test for Engram.

It proves one paid use case: local AI agents audit sensitive contracts without leaking data. The implementation is deliberately small: one sequential Python script presents as three agents and outputs redacted text, findings, an audit log, a summary, and a fake ZK proof hash.

## What Is Included

- `audit_pipeline.py`: `ingest_pdf -> redact_pii -> flag_anomaly -> generate_summary`.
- `run_audit.sh`: one command to start Qdrant, run the audit, and serve the dashboard.
- `docker-compose.yml`: Qdrant only, reusing the existing local Docker posture.
- `dashboard/index.html`: local dashboard at `http://localhost:8000/dashboard/`.
- `landing/index.html`: static landing page for Vercel or Framer.
- `installer/package_mac_dmg.sh`: builds a DMG using macOS `hdiutil`.
- `outreach/linkedin.md`: templates for 3-5 paid pilot commitments.

## Prerequisites

- macOS
- Docker Desktop
- Python 3.11+
- Optional: Ollama with `llama3.1:latest`

The pipeline has a deterministic fallback summary, so Ollama is useful but not required for the smoke test.

## Run The Audit

```bash
cd map/sovereign-agent-audit
cp sample_contract.txt input/
./run_audit.sh
```

Then open:

```text
http://localhost:8000/dashboard/
```

Outputs are written to:

```text
outputs/latest/summary.txt
outputs/latest/audit_log.jsonl
outputs/latest/proof.json
outputs/latest/redacted/
```

## Pilot Demo Script

1. Show `input/` with 10-50 PDFs.
2. Run `./run_audit.sh`.
3. Open the dashboard.
4. Show Planner, Redactor, and Auditor logs.
5. Click `Verify proof hash`.
6. Open `outputs/latest/summary.txt`.
7. Ask for a $1K paid pilot via Wise invoice.

## Record The 2-Minute Demo

Use QuickTime Player:

1. File -> New Screen Recording.
2. Record the flow above.
3. Export as `demo.mp4`.
4. Upload to Vercel static assets, Framer, Loom, or YouTube unlisted.
5. Replace the demo placeholder in `landing/index.html` with:

```html
<video controls playsinline poster="poster.png">
  <source src="demo.mp4" type="video/mp4">
</video>
```

## Build The Mac DMG

```bash
cd map/sovereign-agent-audit
./installer/package_mac_dmg.sh
```

The DMG is created at:

```text
dist/Engram-Sovereign-Agent-Audit.dmg
```

## Deploy The Landing Page

Vercel static deploy:

```bash
cd map/sovereign-agent-audit/landing
vercel --prod
```

Framer:

- Create a one-page site.
- Recreate the headline, sections, pricing, and CTA from `landing/index.html`.
- Embed or link the 2-minute demo.
- CTA text: `Pre-pay $1K pilot via Wise invoice`.

## Friday Ship Checklist

- Day 1: Pipeline, dashboard, proof hash, sample contract.
- Day 2: DMG packaging and founder demo script.
- Day 3: Record 2-minute demo.
- Day 4: Publish landing page.
- Day 5: Send 100 LinkedIn messages to law firms and healthcare admins.
- Day 6: Post Show HN and Product Hunt teaser.
- Day 7: Close 3-5 Wise invoice pre-pays.

## Explicit Non-Goals

- No real ZK proof.
- No MCP server.
- No Next.js backend.
- No Stripe.
- No native binary.
- No enterprise SSO.
- No multi-agent framework.
- No new infrastructure.
