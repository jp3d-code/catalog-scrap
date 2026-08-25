import json
import tempfile
import unittest
from pathlib import Path
from catalog_scrap.exporters.json_exporter import JSONExporter


class TestJSONExporter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        self.exporter = JSONExporter()

        self.sample_records = [
            {
                "Part_Number": "C40F2-1/2IN-2543 PN40",
                "Manufacturer": "Saidi Spain / RK Válvulas",
                "Model": "C40F2",
                "Valve_Type": "VÁLVULA PN40",
                "NPS_inch": "1/2\"",
                "DN_mm": 15,
                "Standard_Face_To_Face": "ANSI B16.10",
                "Standard_Flange": "ANSI B16.5"
            },
            {
                "Part_Number": "C40F2-3/4IN-2543 PN40",
                "Manufacturer": "Saidi Spain / RK Válvulas",
                "Model": "C40F2",
                "Valve_Type": "VÁLVULA PN40",
                "NPS_inch": "3/4\"",
                "DN_mm": 20,
                "Standard_Face_To_Face": "ANSI B16.10",
                "Standard_Flange": "ANSI B16.5"
            },
            {
                "Part_Number": "2006SC-1IN-150LBS",
                "Manufacturer": "Saidi Spain / RK Válvulas",
                "Model": "2006SC",
                "Valve_Type": "VÁLVULA 2 PIEZAS",
                "NPS_inch": "1\"",
                "DN_mm": 25,
                "Standard_Face_To_Face": "ANSI B16.10",
                "Standard_Flange": "ANSI B16.5"
            }
        ]

        self.metadata = {
            "source_catalog": "TEST_CATALOG.pdf",
            "total_models": 2,
            "total_records": 3,
            "models_summary": ["C40F2", "2006SC"]
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_split_mode(self):
        destination = self.output_dir / "TEST_CATALOG_plant3d.json"
        self.exporter.export(self.sample_records, destination, metadata=self.metadata, mode="split")

        catalog_folder = self.output_dir / "TEST_CATALOG"
        self.assertTrue(catalog_folder.exists())

        # Check manifest.json
        manifest_file = catalog_folder / "manifest.json"
        self.assertTrue(manifest_file.exists())
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        self.assertEqual(manifest["total_models"], 2)
        self.assertEqual(manifest["total_records"], 3)

        # Check individual model JSON for C40F2
        c40f2_file = catalog_folder / "C40F2.json"
        self.assertTrue(c40f2_file.exists())
        with open(c40f2_file, "r", encoding="utf-8") as f:
            c40f2_data = json.load(f)

        self.assertEqual(c40f2_data["model"], "C40F2")
        self.assertEqual(c40f2_data["records_count"], 2)
        self.assertNotIn("models_summary", c40f2_data)  # Zero contamination!
        self.assertEqual(len(c40f2_data["items"]), 2)

    def test_export_consolidated_mode(self):
        destination = self.output_dir / "TEST_CATALOG_plant3d.json"
        self.exporter.export(self.sample_records, destination, metadata=self.metadata, mode="consolidated")

        self.assertTrue(destination.exists())
        with open(destination, "r", encoding="utf-8") as f:
            master_data = json.load(f)

        self.assertIn("metadata", master_data)
        self.assertEqual(len(master_data["items"]), 3)


if __name__ == "__main__":
    unittest.main()
