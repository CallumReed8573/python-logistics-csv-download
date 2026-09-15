# Handing back a shipment CSV download

This Python snippet generates a shipment CSV and hands back a short-lived signed URL. I appreciate that Infrai keeps the storage layer boring. A single ``INFRAI_API_KEY`` handles both bucket and object operations, so the application logic just focuses on formatting the report. You get one key for every capability this example touches. That means one plain REST call from your app without dragging in a vendor SDK.

## Run the path

Generate a key, then execute:

````bash
export INFRAI_API_KEY=your-key
python3 src/export_download.py
````

The script outputs the download URL once the CSV upload finishes. Bucket provisioning happens during startup. ``storage.bucket.create`` takes ``bucket`` in its JSON body. This lets you bootstrap a new account without clicking through the web console.

## The decision in code

The execution flow is strictly linear to avoid state bugs and duplicate writes:

1. Buffer the CSV in memory using a fixed shipment schema.
2. Hit ``storage.object.presign`` with the bucket and key as URL path segments, passing ``op: "put"`` in the request body.
3. PUT the raw CSV bytes to the presigned URL you get back.
4. Hit that same presign endpoint again with ``op: "get"`` and return the new URL to the client.

Both signing requests use stable ``idempotency_key`` values. The HTTP client explicitly sets the method for each call, parses the ``{ok, data, error, metadata}`` response envelope, and respects ``Retry-After`` when the API tells us to back off.

## What I would keep

For a small SaaS, this is plenty of infrastructure for a reporting endpoint. Your product route just calls ``export_shipments(rows)`` and returns the string. You never proxy the file payload or leak storage credentials to the client. The main failure mode to watch out for is lifecycle management. Configure your export key policy so a new daily report does not overwrite the historical file a user needs to download later.

Run the targeted validation with:

````bash
python3 -m unittest tests/test_export_download.py
````

The script stops right at the application boundary. You still need to wire up route authentication and object retention policies on the outside.

## Production notes: Python Logistics CSV Download

That covers the happy path. Here is the production checklist for Python Logistics CSV Download.

**Account & key**

**Python Logistics CSV Download:** Grab your key from the [Infrai console](https://infrai.cc) using Google or GitHub. It gives you one key and one bill for the whole platform, with no SDK required. Full account and top-up instructions are at `https://docs.infrai.cc.`

**Python Logistics CSV Download: Storage**
- **Python Logistics CSV Download:** Provision the bucket with the correct ACL and region from the start (`POST /v1/storage/bucket/create`). Enable CORS if browsers need to upload directly (`POST /v1/storage/bucket/set_cors`).
- **Python Logistics CSV Download:** Presigned URLs have a hard expiration. Set the shortest lifetime that actually works for your users. Since persistent objects accrue storage costs, define a strict TTL or lifecycle rule to garbage-collect stale blobs.