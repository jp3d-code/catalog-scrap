import unittest
from pathlib import Path
from catalog_scrap.loaders import PdfLoader
from catalog_scrap.parsers.klinger_k200 import KlingerK200Parser
from catalog_scrap.transformers import Plant3DTransformer


class TestSpecificExtraction(unittest.TestCase):
    """Test detailed specific component extraction for INTEC K200."""

    @classmethod
    def setUpClass(cls):
        cls.pdf_path = Path("docs/specifications/INTEC-K200-NPS1-24inch-eng.pdf")
        if not cls.pdf_path.exists():
            raise unittest.SkipTest(f"PDF not found at {cls.pdf_path}")
        loader = PdfLoader()
        with loader.load(cls.pdf_path) as pdf_handle:
            parser = KlingerK200Parser()
            cls.items = parser.parse(pdf_handle)
        cls.item = cls.items[0]

    def test_dimensions_row_count(self):
        # Must extract all 9 nominal sizes (1/2" through 4")
        self.assertEqual(len(self.item.dimensions), 9)

    def test_first_row_half_inch(self):
        # Row 0: 1/2" (DN15)
        d0 = self.item.dimensions[0]
        self.assertEqual(d0.nps, '1/2"')
        self.assertEqual(d0.dn, 15)
        self.assertEqual(d0.h, 95.0)
        self.assertEqual(d0.l1, 160.0)
        self.assertEqual(d0.l_150, 108.0)
        self.assertEqual(d0.l_300, 140.0)
        self.assertEqual(d0.d_150, 89.0)
        self.assertEqual(d0.d_300, 95.0)
        self.assertEqual(d0.e, 39.5)
        self.assertEqual(d0.iso_flange, "F05")
        self.assertEqual(d0.torque_150, 9.0)
        self.assertEqual(d0.torque_300, 10.0)
        self.assertEqual(d0.weight_150, 2.1)
        self.assertEqual(d0.weight_300, 2.9)

    def test_last_row_four_inch(self):
        # Row 8: 4" (DN100)
        d8 = self.item.dimensions[8]
        self.assertEqual(d8.nps, '4"')
        self.assertEqual(d8.dn, 100)
        self.assertEqual(d8.h, 215.0)
        self.assertEqual(d8.l1, 500.0)
        self.assertEqual(d8.l_150, 229.0)
        self.assertEqual(d8.l_300, 305.0)
        self.assertEqual(d8.d_150, 229.0)
        self.assertEqual(d8.d_300, 254.0)
        self.assertEqual(d8.e, 120.5)
        self.assertEqual(d8.iso_flange, "F10")
        self.assertEqual(d8.torque_150, 170.0)
        self.assertEqual(d8.torque_300, 333.0)
        self.assertEqual(d8.weight_150, 35.0)
        self.assertEqual(d8.weight_300, 47.0)

    def test_parts_list_extracted(self):
        self.assertGreaterEqual(len(self.item.parts_list), 16)
        part_names = [p["part"] for p in self.item.parts_list]
        self.assertIn("body", part_names)
        self.assertIn("ball", part_names)
        self.assertIn("stem", part_names)
        self.assertIn("lever", part_names)

    def test_plant3d_transformation_detailed(self):
        transformer = Plant3DTransformer()
        records = transformer.transform([self.item])
        # 9 sizes * 2 classes = 18 records
        self.assertEqual(len(records), 18)
        # Verify dual-class records created with individual dimensions
        rec_150 = next(r for r in records if r["Part_Number"] == "INTEC-K200-1-2IN-150LBS")
        rec_300 = next(r for r in records if r["Part_Number"] == "INTEC-K200-1-2IN-300LBS")
        self.assertEqual(rec_150["L_mm"], 108.0)
        self.assertEqual(rec_150["D_flange_mm"], 89.0)
        self.assertEqual(rec_150["D_bore_mm"], 0.0)
        self.assertEqual(rec_150["Torque_Nm"], 9.0)
        self.assertEqual(rec_300["L_mm"], 140.0)
        self.assertEqual(rec_300["D_flange_mm"], 95.0)
        self.assertEqual(rec_300["Torque_Nm"], 10.0)

    def test_k200_uses_high_fidelity_template(self):
        transformer = Plant3DTransformer()
        records = transformer.transform([self.item])
        templates = {r["Geometry_Template"] for r in records}
        self.assertEqual(templates, {"INTEC_K200_BALL_VALVE"})

    def test_records_carry_provenance(self):
        transformer = Plant3DTransformer()
        records = transformer.transform([self.item])
        for r in records:
            self.assertIn("Source_PDF", r)
            self.assertIn("Page_Number", r)
            self.assertIn("Row_Index", r)
            self.assertGreater(r["Row_Index"], 0)


if __name__ == "__main__":
    unittest.main()
