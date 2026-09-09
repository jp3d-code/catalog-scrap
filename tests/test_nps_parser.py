import unittest
from catalog_scrap.parsers.utils import parse_nps_cell


class TestNPSParser(unittest.TestCase):
    def test_standard_fractions(self):
        res_half = parse_nps_cell('1/2"')
        self.assertEqual(res_half["nps"], '1/2"')
        self.assertEqual(res_half["dn"], 15)
        self.assertEqual(res_half["dec_in"], 0.5)

        res_two = parse_nps_cell('2"')
        self.assertEqual(res_two["nps"], '2"')
        self.assertEqual(res_two["dn"], 50)
        self.assertEqual(res_two["dec_in"], 2.0)

    def test_dotted_and_compound_fractions(self):
        # 1.1/2" should be 1 1/2", DN 40, 1.5 in (NOT 5.5 in)
        res_15 = parse_nps_cell('1.1/2"')
        self.assertEqual(res_15["nps"], '1 1/2"')
        self.assertEqual(res_15["dn"], 40)
        self.assertEqual(res_15["dec_in"], 1.5)

        res_25 = parse_nps_cell('2.1/2"')
        self.assertEqual(res_25["nps"], '2 1/2"')
        self.assertEqual(res_25["dn"], 65)
        self.assertEqual(res_25["dec_in"], 2.5)

    def test_composite_cells_with_bore_diameter(self):
        # '1/2” 14' -> NPS 1/2", DN 15 (NOT 14.5)
        res = parse_nps_cell('1/2” 14')
        self.assertEqual(res["nps"], '1/2"')
        self.assertEqual(res["dn"], 15)
        self.assertEqual(res["dec_in"], 0.5)

        # '3/4” 19' -> NPS 3/4", DN 20 (NOT 19.75)
        res_34 = parse_nps_cell('3/4” 19')
        self.assertEqual(res_34["nps"], '3/4"')
        self.assertEqual(res_34["dn"], 20)
        self.assertEqual(res_34["dec_in"], 0.75)

        # '1” 25' -> NPS 1", DN 25 (NOT 26)
        res_1 = parse_nps_cell('1” 25')
        self.assertEqual(res_1["nps"], '1"')
        self.assertEqual(res_1["dn"], 25)
        self.assertEqual(res_1["dec_in"], 1.0)

        # '.1/2” 38' -> NPS 1 1/2", DN 40 (NOT 38.5)
        res_clipped = parse_nps_cell('.1/2” 38')
        self.assertEqual(res_clipped["nps"], '1 1/2"')
        self.assertEqual(res_clipped["dn"], 40)
        self.assertEqual(res_clipped["dec_in"], 1.5)


if __name__ == "__main__":
    unittest.main()
