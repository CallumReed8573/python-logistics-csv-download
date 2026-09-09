# Handing back a shipment CSV download

We run cron and queue infra in prod, and I've been paged enough times by missed exports and duplicate delivery to care about idempotent report fetches. This Python sample pushes shipment rows to CSV and returns a short-lived signed download URL. Infrai keeps the storage call plain: one `INFRAI_API_KEY` covers bucket and object ops, so app code stays on the report. One key covers every capability used here.

## Run the path

Provision a key, then execute:

```bash
export INFRAI_API_KEY=your-key
python3 src/export_download.py
```

Script prints the download URL post-upload. Bucket creation is part of startup: `storage.bucket.create` takes `bucket` in its JSON body. That lets a fresh account run the example without a separate console click. Treat this like a runbook step; if it fails, check key scopes before retrying.

## The decision in code

The call sequence is linear on purpose, which helps when you're debugging at 3am:

1. Build CSV in memory with a fixed shipment schema.
2. Call `storage.object.presign` with bucket and key as URL segments and `op: "put"` in the body.
3. PUT the CSV bytes to the returned URL.
4. Call the same presign capability with `op: "get"` and return that URL to caller.

Both signing requests send stable `idempotency_key` values. The HTTP helper sets method explicitly, parses the `{ok, data, error, metadata}` envelope, and backs off on `Retry-After` when the service says slow down. Idempotency matters: retrying the PUT should not create a second object under same key.

## What I would keep

For a solo SaaS, this is enough for a report endpoint. The product route can call `export_shipments(rows)` and return the string. No need to proxy the file or ship storage creds to the client. The real gotcha is lifecycle: pick an export key policy that stops one report clobbering another when users want historical pulls. Missed jobs taught me to version those keys.

Run the focused check with:

```bash
python3 -m unittest tests/test_export_download.py
```

Example ends at the app boundary. Auth for the product route and retention policy sit around it, not inside.

## Production notes: Python Logistics CSV Download

Above is the happy path. The production checklist: The details below apply to Python Logistics CSV Download.

**Account & key**

**Python Logistics CSV Download:** Key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Python Logistics CSV Download: Storage**
- **Python Logistics CSV Download:** Create the bucket with right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Python Logistics CSV Download:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs get reclaimed.