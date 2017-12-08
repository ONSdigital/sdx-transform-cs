import datetime
import json
import unittest
from collections import OrderedDict

from transform.transformers.cs_formatter import CSFormatter
from transform.transformers.survey import Survey


class BatchFileTests(unittest.TestCase):

    def setUp(self):
        with open("./tests/data/eq-mwss.json", encoding="utf-8") as fh:
            self.src = fh.read()
            self.reply = json.loads(self.src)

    def test_pck_form_header(self):
        form_id = 5
        ru_ref = 49900001225
        check = "C"
        period = "200911"
        rv = CSFormatter._pck_form_header(form_id, ru_ref, check, period)
        self.assertEqual("0005:49900001225C:200911", rv)

    def test_pck_lines(self):
        inst_id = "0005"
        ru_ref = 49900001225
        check = "C"
        period = "200911"
        data = OrderedDict([
            ("0001", 2),
            ("0140", 124),
            ("0151", 217222)
        ])
        self.assertTrue(isinstance(val, int) for val in data.values())
        rv = CSFormatter._pck_lines(data, inst_id, ru_ref, check, period)
        self.assertEqual([
            "FV          ",
            "0005:49900001225C:200911",
            "0001 00000000002",
            "0140 00000000124",
            "0151 00000217222",
        ], rv)

    def test_idbr_receipt(self):
        self.reply["tx_id"] = "27923934-62de-475c-bc01-433c09fd38b8"
        ids = Survey.identifiers(self.reply, batch_nr=3866)
        id_dict = ids._asdict()
        rv = CSFormatter._idbr_receipt(id_dict["survey_id"], id_dict["ru_ref"], id_dict["ru_check"],
                                       id_dict["period"])
        self.assertEqual("12346789012:A:134:201605", rv)

    def test_identifiers(self):
        self.reply["tx_id"] = "27923934-62de-475c-bc01-433c09fd38b8"
        self.reply["collection"]["period"] = "200911"
        ids = Survey.identifiers(self.reply)
        self.assertIsInstance(ids, Survey.Identifiers)
        self.assertEqual(0, ids.batch_nr)
        self.assertEqual(0, ids.seq_nr)
        self.assertEqual(self.reply["tx_id"], ids.tx_id)
        self.assertEqual(datetime.date.today(), ids.ts.date())
        self.assertEqual("134", ids.survey_id)
        self.assertEqual("K5O86M2NU1", ids.user_id)
        self.assertEqual("12346789012", ids.ru_ref)
        self.assertEqual("A", ids.ru_check)
        self.assertEqual("200911", ids.period)

    def test_pck_from_transformed_data(self):
        self.reply["tx_id"] = "27923934-62de-475c-bc01-433c09fd38b8"
        self.reply["survey_id"] = "134"
        self.reply["collection"]["period"] = "200911"
        self.reply["metadata"]["ru_ref"] = "49900001225C"
        self.reply["data"] = OrderedDict([
            ("0001", 2),
            ("0140", 124),
            ("0151", 217222)
        ])
        ids = Survey.identifiers(self.reply, batch_nr=3866)
        id_dict = ids._asdict()
        rv = CSFormatter._pck_lines(self.reply["data"], id_dict["inst_id"], id_dict["ru_ref"], id_dict["ru_check"],
                                    id_dict["period"])
        self.assertEqual([
            "FV          ",
            "0005:49900001225C:200911",
            "0001 00000000002",
            "0140 00000000124",
            "0151 00000217222",
        ], rv)
