"""Golden tests con tablas CRUDAS reales de pdfplumber (fixtures del PDF Saidi).

Reproducen los bugs detectados en el cruce PDF vs JSON (2026-09-14):
- Pag 25 (C15F2): celda DN fracturada en 2 ('...051 1' + '/2” 90 60.3')
  -> NPS 1/2" leido como 1", 3/4" como 3", 1.1/2" como 1", 2.1/2" como 1".
- Pag 11 (2006SC): codigo truncado a 5 digitos + dotted fractions
  -> 1.1/4" leido como 1/4", 1.1/2" como 1/2", 2.1/2" como 1/2".
- Pags 25/35: columna D = bore/paso, D1 = diametro de brida.
"""
import unittest

from catalog_scrap.parsers.saidi_rk2016 import SaidiRK2016Parser
from catalog_scrap.parsers.table import (
    classify_columns,
    repair_fractures,
    strip_product_code,
)

# Tabla 4 de la pag. 25 (tal cual la entrega pdfplumber)
P25_TABLE = [
    ['Código D', 'N D1 D2', 'D3', 'D', 'F', 'B', 'n-Ø', 'L', 'P', 'H', 'M', 'E', 'N', 'H1', 'H2', 'ISO 5211', 'Par (Nm)'],
    ['010104304270051 1', '/2” 90 60.3', '34.9', '14', '1.6', '9.9', '4-16', '108', '35.5', '90', '180', '8', 'M12 x 1.5', '8.5', '19', 'F03', '6.6'],
    ['010104304270052 3', '/4” 100 69.9', '43.0', '19', '1.6', '11.4', '4-16', '117', '35.5', '84', '180', '8', 'M12 x 1.5', '8.5', '19', 'F03', '6.6'],
    ['010104304270047', '1” 110 79.4', '50.8', '25', '1.6', '12.9', '4-16', '127', '46.5', '100', '180', '10', 'M14 x 1.5', '11', '23', 'F04', '8.8'],
    ['010104304270063 1.1', '/2” 125 98.5', '73', '38', '1.6', '15.9', '4-16', '165', '76.0', '126', '240', '13', 'M18 x 1.5', '11.5', '23.5', 'F05', '22'],
    ['010104304270026', '2” 152.5 120.6', '92', '50', '1.6', '19.0', '4-19', '178', '86.5', '150.5', '300', '16', 'Ø22', '24', '34', 'F07', '35'],
    ['- 2.1/', '2 ” 178 139.7', '104.8', '65', '1.6', '', '4-19', '190', '96.0', '150', '300', '', '', '', '', 'F07', ''],
    ['010104304270048', '3” 190 152.4', '127', '76', '1.6', '24', '4-19', '203', '112.0', '188.0', '400', '20', 'Ø27', '28', '41', 'F10', '114'],
    ['010104304270057', '4” 228.6 190.5', '157.2', '100', '1.6', '24', '8-19', '229', '128.5', '205', '400', '20', 'Ø27', '28.5', '41.5', 'F10', '150'],
    ['010104304270259', '6” 280 241.3', '216', '150', '1.6', '23.9', '8-22.2', '394', '180.0', '260', '600', '24', 'Ø35', '33.5', '48.5', 'F12', '240'],
]

P25_NPS = ['1/2"', '3/4"', '1"', '1 1/2"', '2"', '2 1/2"', '3"', '4"', '6"']
P25_L = [108.0, 117.0, 127.0, 165.0, 178.0, 190.0, 203.0, 229.0, 394.0]
P25_FLANGE = [90.0, 100.0, 110.0, 125.0, 152.5, 178.0, 190.0, 228.6, 280.0]
P25_BORE = [14.0, 19.0, 25.0, 38.0, 50.0, 65.0, 76.0, 100.0, 150.0]

# Tabla 2 de la pag. 11 (valvula roscada 2006SC)
P11_TABLE = [
    ['', 'd1', 'L', 'H', 'W'],
    ['90336 1/4” 8', '11.5', '50.0', '54', '101'],
    ['90338 3/8” 10', '12.5', '50.0', '54', '101'],
    ['90329 1/2” 15', '15', '59.0', '54', '101'],
    ['90339 3/4” 20', '20', '66.0', '63', '124'],
    ['90340 1” 25', '25', '75.5', '74', '124'],
    ['90341 1.1/4” 32', '32', '88.7', '80', '165'],
    ['90342 1.1/2” 40', '38', '98.5', '94', '165'],
    ['90343 2” 50', '50', '120.6', '103', '183'],
    ['90332 2.1/2” 65', '63', '146.5', '137', '248'],
    ['90324 3” 80', '76', '167.5', '148', '248'],
]

P11_NPS = ['1/4"', '3/8"', '1/2"', '3/4"', '1"', '1 1/4"', '1 1/2"', '2"', '2 1/2"', '3"']
P11_L = [50.0, 50.0, 59.0, 66.0, 75.5, 88.7, 98.5, 120.6, 146.5, 167.5]

# Tabla 4 de la pag. 35 (cabecera limpia: D = bore, D1 = brida)
P35_TABLE = [
    ['Código', 'DN D', 'D1', 'D2', 'D3', 'F', 'B', 'n-Ø', 'L', 'P', 'H', 'M', 'N', 'E', 'H1', 'H2', 'ISO 5211', 'Par (Nm)'],
    ['010104304270248', '1/2” 14', '95', '66.7', '34.9', '2', '12.7', '4-16', '140', '33.5', '90', '180', 'M12 x 1.5', '8', '8.5', '19', 'F03', '8.8'],
    ['010104304270249', '3/4” 19', '115', '82.6', '42.9', '2', '14.3', '4-19', '152', '35.5', '85', '180', 'M12 x 1.5', '8', '8.5', '19', 'F03', '8.8'],
    ['010104304270250', '1” 25', '125', '88.9', '50.8', '2', '15.9', '4-19', '165', '46.5', '100', '180', 'M14 x 1.5', '10', '11.0', '23', 'F04', '11.0'],
    ['010104304270251 1', '.1/2” 38', '155', '114.3', '73.0', '2', '19.1', '4-22.2', '190', '76.0', '126', '240', 'M18 x 1.5', '13', '11.5', '23.5', 'F05', '27.5'],
]


class TestStripProductCode(unittest.TestCase):
    def test_full_code(self):
        self.assertEqual(strip_product_code('010104304270051 1/2”'), '1/2”')

    def test_truncated_code(self):
        # Pag. 11: pdfplumber recorta el codigo a 5 digitos
        self.assertEqual(strip_product_code('90341 1.1/4” 32'), '1.1/4” 32')

    def test_dash_placeholder(self):
        self.assertEqual(strip_product_code('- 2.1/'), '2.1/')


class TestRepairFractures(unittest.TestCase):
    def test_split_fraction_rejoined(self):
        row = ['010104304270051 1', '/2” 90 60.3', '34.9']
        repaired = repair_fractures(row)
        self.assertEqual(len(repaired), 3)
        self.assertIn('1/2', repaired[0].replace(' ', ''))

    def test_dotted_split_rejoined(self):
        row = ['010104304270063 1.1', '/2” 125 98.5', '73']
        repaired = repair_fractures(row)
        self.assertIn('1.1/2', repaired[0].replace(' ', ''))

    def test_dash_split_rejoined(self):
        row = ['- 2.1/', '2 ” 178 139.7', '104.8']
        repaired = repair_fractures(row)
        self.assertIn('2.1/2', repaired[0].replace(' ', ''))

    def test_adjacent_numbers_not_joined(self):
        # Columnas numericas legitimas no deben fusionarse
        row = ['1/2” 14', '95', '66.7']
        self.assertEqual(repair_fractures(row), row)


class TestClassifyColumns(unittest.TestCase):
    def test_p25_fractured_header(self):
        cmap = classify_columns(P25_TABLE[0])
        self.assertEqual(cmap.get('length'), 7)
        self.assertEqual(cmap.get('d'), 3)

    def test_p35_clean_header(self):
        # 'DN D' fusionados: size=1, sin columna 'd' separada, D1=brida en 2
        cmap = classify_columns(P35_TABLE[0])
        self.assertEqual(cmap.get('size'), 1)
        self.assertEqual(cmap.get('d1'), 2)
        self.assertEqual(cmap.get('length'), 8)


class TestGoldenSaidiPage25(unittest.TestCase):
    def setUp(self):
        self.parser = SaidiRK2016Parser()
        self.dims = self.parser._extract_dimensions(
            [P25_TABLE], fig_model='C15F2',
            valve_type='Válvula 150LBS Paso Total Y Cuerpo De 2 Piezas',
        )

    def test_nps_series(self):
        self.assertEqual([d.nps for d in self.dims], P25_NPS)

    def test_face_to_face_values(self):
        self.assertEqual([d.l_150 for d in self.dims], P25_L)

    def test_flange_vs_bore(self):
        for d, flange, bore in zip(self.dims, P25_FLANGE, P25_BORE):
            self.assertAlmostEqual(d.extra_dimensions.get('d_flange_mm', 0.0), flange)
            self.assertAlmostEqual(d.extra_dimensions.get('d_bore_mm', 0.0), bore)


class TestGoldenSaidiPage11(unittest.TestCase):
    def setUp(self):
        self.parser = SaidiRK2016Parser()
        self.dims = self.parser._extract_dimensions(
            [P11_TABLE], fig_model='2006SC',
            valve_type='Válvula 1000WOG (PN 63) Paso Total Y Cuerpo De 2 Piezas',
        )

    def test_nps_series_includes_dotted(self):
        self.assertEqual([d.nps for d in self.dims], P11_NPS)

    def test_no_rows_lost(self):
        self.assertEqual(len(self.dims), 10)

    def test_face_to_face_values(self):
        self.assertEqual([d.l_150 for d in self.dims], P11_L)


class TestGoldenSaidiPage35(unittest.TestCase):
    def setUp(self):
        self.parser = SaidiRK2016Parser()
        self.dims = self.parser._extract_dimensions(
            [P35_TABLE], fig_model='S30F2',
            valve_type='Válvula 300LBS Paso Total Y Cuerpo De 2 Piezas',
        )

    def test_nps_series(self):
        self.assertEqual([d.nps for d in self.dims], ['1/2"', '3/4"', '1"', '1 1/2"'])

    def test_d1_is_flange_d_is_bore(self):
        self.assertEqual(
            [d.extra_dimensions.get('d_flange_mm') for d in self.dims],
            [95.0, 115.0, 125.0, 155.0],
        )
        self.assertEqual(
            [d.extra_dimensions.get('d_bore_mm') for d in self.dims],
            [14.0, 19.0, 25.0, 38.0],
        )


# Tabla 4 de la pag. 4: columna agrupada 'L P H' (el primer token es L)
P4_TABLE = [
    ['Código', 'DN', 'D1', 'D2', 'D3', 'D', 'D0', 'F', 'B', 'n-Ø', 'L P H', 'M N', 'E', 'H1', 'H2', 'ISO 5211', 'Par (Nm)'],
    ['010104304270273', '3”', '210', '168.3', '127.0', '76', '51', '6.4', '32 8', '-22.2', '356 77 15', '1 34.0 M22', '12', '27', '35', 'F07', '138'],
    ['010104304270274', '4”', '273', '215.9', '157.2', '101', '76', '6.4', '38', '8-25', '432 106 20', '4 367 M30', '20', '49', '59.5', 'F10', '293'],
]


class TestGoldenSaidiPage4GroupedL(unittest.TestCase):
    def setUp(self):
        self.parser = SaidiRK2016Parser()
        self.dims = self.parser._extract_dimensions(
            [P4_TABLE], fig_model='C60F2RB',
            valve_type='Válvula 600LBS Paso Reducido Y Cuerpo De 1 Pieza',
        )

    def test_grouped_length(self):
        self.assertEqual([d.nps for d in self.dims], ['3"', '4"'])
        self.assertEqual([d.l_150 for d in self.dims], [356.0, 432.0])

    def test_flange_from_d1(self):
        self.assertEqual(
            [d.extra_dimensions.get('d_flange_mm') for d in self.dims],
            [210.0, 273.0],
        )


# Tabla 5 de la pag. 6: columna L fracturada ('5 90') -> fila descartada
P6_GARBAGE_TABLE = [
    ['Código', 'NPS', 'Port', 'L', 'H', 'P'],
    ['010104304270226', '1/2”', '12.', '5 90', '85\n90\n100', '150'],
    ['010104304270227', '3/4”', '1', '9 110', '', ''],
]


class TestStrictLength(unittest.TestCase):
    def test_fractured_L_resolved_by_band(self):
        # '5 90' en 1/2" (DN15): 90 es plausible (6xDN), 5 no.
        # Son duplicados de la tabla limpia (dedup aguas abajo por Part_Number).
        parser = SaidiRK2016Parser()
        dims = parser._extract_dimensions(
            [P6_GARBAGE_TABLE], fig_model='S800NPT',
            valve_type='Válvula 800LBS Paso Total Y Cuerpo De 1 Pieza',
        )
        self.assertEqual(
            [(d.nps, d.l_150) for d in dims],
            [('1/2"', 90.0), ('3/4"', 110.0)],
        )


# Fila de la pag. 26: cabecera fusionada Peso+ISO+Par ('F25 510 248'
# = ISO F25 + par 510 + peso 248kg). first_float daria 25.0 (falso).
P26_TABLE = [
    ['Código', 'DN', 'D1', 'D2', 'D3', 'D', 'F', 'E', 'n - Ø', 'L', 'P', 'H', 'n1 - Ø1', 'Peso\nISO 5211 Par (N', 'K ØG ØJ ØC n2 - Ø2', 'A', 'B'],
    ['010104304270059', '8”', '343', '298.3', '270', '200', '1.6', '28.6', '8-22.2', '457', '233.5', '302.5', '8-18', 'F25 510 248', '22.5 254 200 45 4-10', '12', '38'],
]


class TestFusedPesoIsoPar(unittest.TestCase):
    def test_weight_is_last_token_iso_recovered(self):
        parser = SaidiRK2016Parser()
        dims = parser._extract_dimensions(
            [P26_TABLE], fig_model='C15F2',
            valve_type='Válvula 150LBS Paso Total Y Cuerpo De 2 Piezas',
        )
        self.assertEqual(len(dims), 1)
        self.assertEqual(dims[0].weight_150, 248.0)
        self.assertEqual(dims[0].iso_flange, 'F25')

    def test_trailing_orphan_digit_ignored(self):
        # Pag. 30: 'F25 510 248 2' + '2.5 ...' -> el '2' final es huerfano
        # de la columna K ('22.5'); el peso real es 248.
        parser = SaidiRK2016Parser()
        dims = parser._extract_dimensions(
            [[P26_TABLE[0],
              ['010104304270035', '8”', '343', '298.3', '270', '200', '1.6', '28.6', '8-22.2', '457', '233.5', '302.5', '8-18', 'F25 510 248 2', '2.5 254 200 45 4-10', '12', '38']]],
            fig_model='S15F2',
            valve_type='Válvula 150LBS Paso Total Y Cuerpo De 2 Piezas',
        )
        self.assertEqual(len(dims), 1)
        self.assertEqual(dims[0].weight_150, 248.0)


# Fila de la pag. 27: resto de codigo '0039' antes de la talla y D1
P27_TABLE = [
    ['Código', 'DN D1 D2', 'D3 D F E n - Ø', 'L', 'P', 'H', 'n1 - Ø1', 'ISO 5211', 'Par (Nm)', 'Peso (kg)', 'K', 'ØG', 'ØC', 'A', 'B'],
    ['01010430427', '0039 10” 405 362.0', '323.8 254 1.6 28.9 12-', '533', '282.0', '437', '4-17', 'F14', '2000', '405', '45', '140', '55', '18', '46'],
]


class TestGoldenSaidiPage27(unittest.TestCase):
    def test_code_remnant_before_size(self):
        parser = SaidiRK2016Parser()
        dims = parser._extract_dimensions(
            [P27_TABLE], fig_model='C15F2',
            valve_type='Válvula 150LBS Paso Total Y Cuerpo De 2 Piezas',
        )
        self.assertEqual(len(dims), 1)
        self.assertEqual(dims[0].nps, '10"')
        self.assertEqual(dims[0].l_150, 533.0)
        self.assertEqual(dims[0].extra_dimensions.get('d_flange_mm'), 405.0)


# Pags. tipo 21: tallas solo en DN-mm ('15' sin comilla) -> dialecto DN:
# entero desnudo 1-3 digitos presente en la tabla DN (nunca pulgadas).
P21_TABLE = [
    ['Código DN', 'D1 D2', 'D3', 'D', 'F', 'B', 'n-Ø', 'L', 'P H', 'M', 'N', 'E', 'H1', 'H2', 'ISO 5211', 'Par (Nm)'],
    ['010104304270029 15', '95 65', '45', '14', '2', '14', '4-14', '115 3', '5.5 90', '180', 'M12 x 1.5', '8', '8.5', '19', 'F03', '8.8'],
    ['010104304270019 20', '105 75', '58', '19', '2', '16', '4-14', '120 3', '5.5 87.5', '180', 'M12 x 1.5', '8', '8.5', '19', 'F03', '16'],
]


class TestDnMmDialect(unittest.TestCase):
    def test_bare_dn_sizes(self):
        parser = SaidiRK2016Parser()
        dims = parser._extract_dimensions(
            [P21_TABLE], fig_model='C40F2',
            valve_type='Válvula 400LBS Paso Total Y Cuerpo De 2 Piezas',
        )
        self.assertEqual(
            [(d.nps, d.l_150) for d in dims],
            [('1/2"', 115.0), ('3/4"', 120.0)],
        )
        self.assertEqual(
            [d.extra_dimensions.get('d_flange_mm') for d in dims],
            [95.0, 105.0],
        )

    def test_bare_dn_helper(self):
        from catalog_scrap.parsers.table import parse_bare_dn
        self.assertEqual(
            parse_bare_dn('65'), {"nps": '2 1/2"', "dn": 65, "dec_in": 2.559},
        )
        self.assertIsNone(parse_bare_dn('0039'))  # resto de codigo
        self.assertIsNone(parse_bare_dn('90336'))  # codigo truncado
        self.assertIsNone(parse_bare_dn('1/2”'))  # no es desnudo


# Tabla 3 de la pag. 17 (C16F2 PN16): dialecto DN + '190 1' por banda
P17_TABLE = [
    ['Código DN', 'D1 D2 D3', 'D', 'F', 'B', 'n-Ø', 'L', 'P', 'H', 'M', 'N', 'E', 'H1', 'H2', 'ISO 5211', 'Par (Nm)'],
    ['010104304270085 65', '185 145 122', '64', '3', '15', '4-18', '170', '96', '166.0', '300', 'Ø 22', '16', '24', '34', 'F07', '75'],
    ['010104304270084 80', '200 160 138', '76', '3', '24', '8-18', '180', '112', '189.0', '400', 'Ø 27', '20', '29', '42', 'F10', '66'],
    ['010104304270055 100', '220 180 158', '100', '3', '20', '8-18', '190 1', '28.5', '205.0', '400', 'Ø 27', '20', '28.5', '41.5', 'F10', '150'],
]


class TestGoldenSaidiPage17(unittest.TestCase):
    def setUp(self):
        self.parser = SaidiRK2016Parser()
        self.dims = self.parser._extract_dimensions(
            [P17_TABLE], fig_model='C16F2',
            valve_type='Válvula PN16 Paso Total Y Cuerpo De 2 Piezas',
        )

    def test_dn_series(self):
        self.assertEqual(
            [(d.nps, d.l_150) for d in self.dims],
            [('2 1/2"', 170.0), ('3"', 180.0), ('4"', 190.0)],
        )

    def test_flange_exact_pn16(self):
        self.assertEqual(
            [d.extra_dimensions.get('d_flange_mm') for d in self.dims],
            [185.0, 200.0, 220.0],
        )


# Tabla 3 de la pag. 19 (S16F2 PN16): D1 fracturado en dos celdas
# ('65 18' + '5 145' -> D1=185). Solo se une con fragmentos cortos y
# resultado fisicamente coherente (brida > bore).
P19_TABLE = [
    ['Código', 'DN D1', 'D2', 'D3', 'D', 'F', 'B', 'n-Ø', 'L', 'P', 'H', 'M', 'N', 'E', 'H1', 'H2', 'ISO 5211', 'Par (Nm)'],
    ['010104304270032', '65 18', '5 145', '122', '64', '3', '15', '4-18', '170', '96', '166', '300', 'Ø22', '16', '24', '34', 'F07', '75'],
    ['010104304270027', '80 20', '0 160', '138', '76', '3', '20', '8-18', '180', '112', '189', '400', 'Ø27', '20', '29', '42', 'F10', '66'],
    ['010104304270028', '100 22', '0 180', '158', '100', '3', '20', '8-18', '190', '128.5', '205', '400', 'Ø27', '20', '28.5', '41.5', 'F10', '150'],
    ['010104304270021', '125 25', '0 210', '188', '125', '3', '19', '8-18', '325', '147', '226', '500', 'Ø27', '20', '29', '44', 'F10', '200'],
    ['010104304270031', '150 28', '5 240', '212', '150', '3', '22', '8-22', '350', '180', '260', '600', 'Ø35', '24', '33.5', '48.5', 'F12', '410'],
]


class TestGoldenSaidiPage19(unittest.TestCase):
    def setUp(self):
        self.parser = SaidiRK2016Parser()
        self.dims = self.parser._extract_dimensions(
            [P19_TABLE], fig_model='S16F2',
            valve_type='Válvula PN16 Paso Total Y Cuerpo De 2 Piezas',
        )

    def test_split_d1_rejoined(self):
        self.assertEqual(
            [(d.nps, d.l_150) for d in self.dims],
            [('2 1/2"', 170.0), ('3"', 180.0), ('4"', 190.0),
             ('5"', 325.0), ('6"', 350.0)],
        )
        self.assertEqual(
            [d.extra_dimensions.get('d_flange_mm') for d in self.dims],
            [185.0, 200.0, 220.0, 250.0, 285.0],
        )


if __name__ == '__main__':
    unittest.main()
