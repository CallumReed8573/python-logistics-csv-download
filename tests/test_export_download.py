import unittest

from src.export_download import shipment_csv


class ShipmentCsvTest(unittest.TestCase):
    def test_writes_stable_columns(self) -> None:
        result = shipment_csv([{"shipment_id": "S1", "status": "delivered", "destination": "Ningbo"}])
        self.assertEqual(
            result.decode("utf-8"),
            "shipment_id,status,destination\r\nS1,delivered,Ningbo\r\n",
        )


if __name__ == "__main__":
    unittest.main()
