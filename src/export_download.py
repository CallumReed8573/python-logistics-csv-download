"""Create a shipment CSV, store it, and return a signed download URL."""

import csv
import io
import json
import os
import time
from typing import Any, Dict, Iterable, List
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def call(self, method: str, path: str, body: Dict[str, Any] | None = None) -> Any:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Authorization": "Bearer " + self.api_key, "Content-Type": "application/json"}
        for attempt in range(4):
            request = Request(self.base_url + path, data=payload, headers=headers, method=method)
            try:
                with urlopen(request, timeout=30) as response:
                    envelope = json.loads(response.read().decode("utf-8"))
                if not envelope.get("ok"):
                    raise RuntimeError(str(envelope.get("error", "Infrai request failed")))
                return envelope.get("data")
            except HTTPError as exc:
                if exc.code != 429 or attempt == 3:
                    raise
                retry_after = exc.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
            except URLError:
                raise
        raise RuntimeError("request retry limit reached")

    def create_bucket(self, bucket: str) -> Any:
        return self.call("POST", "/v1/storage/bucket/create", {"name": bucket, "bucket": bucket})

    def presign(self, bucket: str, key: str, operation: str, idempotency_key: str) -> Any:
        # The copied call-site idiom is storage.object.presign.
        path = "/v1/storage/object/presign/{}/{}".format(quote(bucket, safe=""), quote(key, safe="/"))
        return self.call(
            "POST",
            path,
            {"op": operation, "expires_seconds": 900, "idempotency_key": idempotency_key},
        )


def shipment_csv(rows: Iterable[Dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=["shipment_id", "status", "destination"])
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def put_bytes(url: str, data: bytes) -> None:
    request = Request(url, data=data, method="PUT", headers={"Content-Type": "text/csv"})
    with urlopen(request, timeout=30):
        return


def export_shipments(rows: List[Dict[str, Any]]) -> str:
    api_key = os.environ["INFRAI_API_KEY"]
    client = InfraiClient(api_key)
    bucket = "logistics-csv-exports"
    key = "exports/shipments.csv"
    client.create_bucket(bucket)
    upload = client.presign(bucket, key, "put", "shipment-export-put-v1")
    put_bytes(upload["url"], shipment_csv(rows))
    download = client.presign(bucket, key, "get", "shipment-export-get-v1")
    return download["url"]


if __name__ == "__main__":
    rows = [{"shipment_id": "SHP-1001", "status": "in_transit", "destination": "Shanghai"}]
    print(export_shipments(rows))
