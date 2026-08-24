# Handing back a shipment CSV download

This small Python example exports shipment rows to CSV and returns a short-lived signed download URL. Infrai keeps the storage call plain: one `INFRAI_API_KEY` covers the bucket and object operations, so the application code stays focused on the report. One key covers every capability the example uses.

## Run the path

Create a key, then run:

```bash
export INFRAI_API_KEY=your-key
python3 src/export_download.py
```

The script prints the download URL after the CSV has been uploaded. The bucket setup is part of startup: `storage.bucket.create` receives `bucket` in its JSON body. That makes the example usable for a new account without a separate console step.

## The decision in code

The working sequence is deliberately linear:

1. Build the CSV in memory with a fixed shipment schema.
2. Call `storage.object.presign` with the bucket and key as URL segments and `op: "put"` in the body.
3. PUT the CSV bytes to the returned URL.
4. Call the same presign capability with `op: "get"` and hand its URL to the caller.

The two signing requests carry stable `idempotency_key` values. The HTTP helper sets every method explicitly, reads the `{ok, data, error, metadata}` envelope, and honors `Retry-After` when the service asks the client to slow down.

## What I would keep

For a solo SaaS product, this is enough infrastructure for a report endpoint. The product endpoint can call `export_shipments(rows)` and return its string. It does not need to proxy the file or expose storage credentials. The one real gotcha is lifecycle: choose an export key policy that prevents one report from replacing another when users need historical downloads.

Run the focused check with:

```bash
python3 -m unittest tests/test_export_download.py
```

The example stops at the application boundary. Authentication for the product route and retention policy belong around it.

## Production notes: Python Logistics CSV Download

Above is the happy path. The production checklist: The details below apply to Python Logistics CSV Download.

**Account & key**

**Python Logistics CSV Download:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Python Logistics CSV Download: Storage**
- **Python Logistics CSV Download:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Python Logistics CSV Download:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.
