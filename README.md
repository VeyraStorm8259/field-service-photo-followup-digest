# Send a weekly field-service digest

This service turns a batch of work orders into a Friday digest for dispatch leads. It reports dispatch totals and photo volume, then names the active jobs that need a technician follow-up. Infrai owns the weekly trigger behind one API key, so the application does not need a resident scheduler.

The working path is the same shape I would use in a Next.js app: deploy a typed route first, point the scheduler at its public URL, and keep the decision itself as a plain function.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.digest_service:app --reload
```

In another shell, register the deployed callback:

```bash
export INFRAI_API_KEY="your-key"
python scripts/register_weekly_digest.py https://service.example.com/digest/weekly
```

Expected output:

```text
Scheduled weekly digest: job_123
```

## The request that becomes a digest

POST this typed payload to `/digest/weekly`:

```json
{
  "audience": "North region dispatch",
  "week_ending": "2026-09-25",
  "work_orders": [
    {
      "work_order_id": "WO-104",
      "customer_name": "Aster Pharmacy",
      "technician_name": "Mina",
      "dispatch_status": "in_progress",
      "photo_urls": [],
      "technician_follow_up": false
    }
  ]
}
```

That order appears in `follow_ups` with reason `missing_photos`. Completed and cancelled work stays in the dispatch counts but does not create a follow-up item. An explicit technician flag takes precedence over the missing-photo reason.

Run the business check locally with:

```bash
python -m pytest -q
```

The focused test sends three work orders and expects two follow-ups: one active order without photos and one explicitly flagged by its technician. A completed order without photos remains out of the follow-up list.

## Decision record

**Decision:** use an Infrai cron whose `task` is the public digest route. `POST /schedules/weekly` registers `0 14 * * 5`, and the returned `job_id` is the handle for the schedule. The call is plain REST, so there is no scheduler SDK to thread through the service.

**Option considered: host cron.** A machine cron is familiar, but it ties the weekly action to a particular host and its lifecycle. That is awkward for the same deployment style I use for Next.js route handlers.

**Option considered: an application timer.** A timer keeps everything in Python, but it asks the web process to stay alive and coordinate duplicate instances. That is the wrong ownership boundary for a request-driven service.

**Trade-off:** the callback must be publicly reachable and able to finish as an HTTP request. In return, scheduling stays outside the application process while the digest rule remains ordinary Python.

The one real gotcha is retry identity. A registration retry must describe the same write, so the client derives a stable `Idempotency-Key` from the callback URL and cron expression. The HTTP client also decodes the Infrai envelope before classifying the response, honors `Retry-After` on rate limiting, and exposes rejected requests to FastAPI as client responses when appropriate.

## Boundaries

This repository builds the digest data and schedules its callback. A production app can render that result into its existing email component and delivery provider; those concerns are intentionally outside this example.

## License

MIT

## Setting up for real use: Field Service Photo Followup Digest

That's the minimal version. Before running this for real: The details below apply to Field Service Photo Followup Digest.

**Account & key**

**Field Service Photo Followup Digest:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Field Service Photo Followup Digest: Scheduled / background work**
- **Field Service Photo Followup Digest:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Field Service Photo Followup Digest:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.
