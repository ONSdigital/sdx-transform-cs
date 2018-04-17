import datetime
import json
import unittest
from collections import OrderedDict, defaultdict

import pkg_resources

from transform.transformers.cs_formatter import CSFormatter
from transform.transformers import MBSTransformer
from transform.transformers.survey import Survey


class LogicTests(unittest.TestCase):

    response = {
        "origin": "uk.gov.ons.edc.eq",
        "survey_id": "134",
        "tx_id": "40e659ec-013f-4993-9a31-ec1e0ad37888",
        "data": {
            "11": "13/02/2017",
            "12": "14/03/2018",
            "146a": "Yes",
            "146b": "In-store / online promotions",
            "146c": "Special events (e.g. sporting events)",
            "146d": "Calendar events (e.g. Christmas, Easter, Bank Holiday)",
            "146e": "Weather",
            "146f": "Store closures",
            "146g": "Store openings",
            "146h": "Other",
            "40": "100234",
            "49": "150000",
            "90": "2900",
            "50": "12",
            "51": "1",
            "52": "2",
            "53": "3",
            "54": "4",
        },
        "type": "uk.gov.ons.edc.eq:surveyresponse",
        "version": "0.0.1",
        "metadata": {
            "user_id": "K5O86M2NU1",
            "ru_ref": "12346789012A"
        },
        "submitted_at": "2017-03-01T14:25:46.101447+00:00",
        "collection": {
            "period": "201605",
            "exercise_sid": "82R1VDWN74",
            "instrument_id": "0005"
        }
    }

    mbs_transformer = MBSTransformer(response)
    transformed_data = mbs_transformer.transform()

    def test_reporting_period_from(self):
        """
        QId 11 specifies the date the reporting period starts.
        """
        self.assertEqual(13, self.transformed_data['11'].day)
        self.assertEqual(2, self.transformed_data['11'].month)
        self.assertEqual(2017, self.transformed_data['11'].year)

    def test_reporting_period_to(self):
        """
        QId 12 specifies the date the reporting period ends.
        """
        self.assertEqual(13, self.transformed_data['11'].day)
        self.assertEqual(2, self.transformed_data['11'].month)
        self.assertEqual(2017, self.transformed_data['11'].year)

    def test_turnover_radio(self):
        """
        QId 146a contributes to 146.
        """
        self.assertEqual(self.transformed_data['146'], 1)

        no_turnover_response = dict.copy(self.response)
        no_turnover_response['data']['146a'] = 'No'
        no_turnover_transformed = MBSTransformer(no_turnover_response).transform()

        self.assertEqual(no_turnover_transformed['146'], 2)

    def test_turnover_excluding_vat(self):
        """
        QId 40 returns an integer.
        """
        self.assertEqual(self.transformed_data['40'], 100000)

    def test_turnover_excluding_vat_default(self):
        """
        QId 40 returns an integer.
        """
        _, funct = MBSTransformer.ops()["40"]
        return_value = funct("40", {}, 0)
        self.assertEqual(return_value, 0)

    def test_value_of_exports(self):
        """
        QId 49 returns an integer.
        """

        _, funct = MBSTransformer.ops()["49"]
        return_value = funct("49", {"49": "150000"}, 0)
        self.assertEqual(return_value, 49)

    def test_value_of_exports_default(self):
        """
        QId 49 defaults to 0.
        """

        _, funct = MBSTransformer.ops()["49"]
        return_value = funct("49", {}, 0)
        self.assertEqual(return_value, 0)

    def test_value_of_excise_duty(self):
        """
        QId 90 returns an integer.
        """

        _, funct = MBSTransformer.ops()["90"]
        return_value = funct("90", {"90": "2900"}, 0)
        self.assertEqual(return_value, 2900)

    def test_value_of_excise_duty_default(self):
        """
        QId 90 defaults to 0.
        """

        _, funct = MBSTransformer.ops()["90"]
        return_value = funct("90", {}, 0)
        self.assertEqual(return_value, 0)

    def test_value_number_of_employees(self):
        """
        QId 50 returns an integer.
        """

        _, funct = MBSTransformer.ops()["50"]
        return_value = funct("50", {"50", "12"}, 0)
        self.assertEqual(return_value, 12)

    def test_value_number_of_employees_default(self):
        """
        QId 50 defaults to 0.
        """

        _, funct = MBSTransformer.ops()["50"]
        return_value = funct("50", {}, 0)
        self.assertEqual(return_value, 0)

    def test_value_male_number_of_employees_more_than_30hrs_week(self):
        """
        QId 51 returns an integer.
        """

        _, funct = MBSTransformer.ops()["51"]
        return_value = funct("51", {"51": "1"}, 0)
        self.assertEqual(return_value, 1)

    def test_value_male_number_of_employees_more_than_30hrs_week_deefault(self):
        """
        QId 51 defaults to 0.
        """

        _, funct = MBSTransformer.ops()["51"]
        return_value = funct("51", {}, 0)
        self.assertEqual(return_value, 0)

    def test_value_male_number_of_employees_less_than_30hrs_week(self):
        """
        QId 52 returns an integer.
        """

        _, funct = MBSTransformer.ops()["52"]
        return_value = funct("52", {"52": "2"}, 0)
        self.assertEqual(return_value, 2)

    def test_value_male_number_of_employees_less_than_30hrs_week_default(self):
        """
        QId 52 defaults to 0.
        """

        _, funct = MBSTransformer.ops()["52"]
        return_value = funct("52", {}, 0)
        self.assertEqual(return_value, 0)

    def test_value_female_number_of_employees_more_than_30hrs_week(self):
        """
        QId 53 returns an integer.
        """

        _, funct = MBSTransformer.ops()["53"]
        return_value = funct("53", {"53": "3"}, 0)
        self.assertEqual(return_value, 3)

    def test_value_female_number_of_employees_more_than_30hrs_week_default(self):
        """
        QId 53 defaults to 0.
        """

        _, funct = MBSTransformer.ops()["53"]
        return_value = funct("53", {}, 0)
        self.assertEqual(return_value, 3)

    def test_value_female_number_of_employees_less_than_30hrs_week(self):
        """
        QId 54 returns an integer.
        """

        _, funct = MBSTransformer.ops()["54"]
        return_value = funct("54", {"54": "4"}, 0)
        self.assertEqual(return_value, 4)

    def test_value_female_number_of_employees_less_than_30hrs_week_default(self):
        """
        QId 54 defaults to 0.
        """

        _, funct = MBSTransformer.ops()["54"]
        return_value = funct("54", {}, 0)
        self.assertEqual(return_value, 0)


class BatchFileTests(unittest.TestCase):

    def test_pck_no_defaults(self):
        src = pkg_resources.resource_string(__name__, "replies/eq-mbs.json")
        reply = json.loads(src.decode("utf-8"))
        reply["tx_id"] = "8b85f822-f6fe-4f23-b97d-dc48291cf6dc"
        reply["survey_id"] = "009"
        reply["collection"]["period"] = "1704"
        reply["metadata"]["ru_ref"] = "49900108249D"
        ids = Survey.identifiers(reply, batch_nr=3866, seq_nr=0)
        data = MBSTransformer.transform(
            OrderedDict([("11", "13/02/2017"), ("12", "14/03/2018")])
        )

        return_value = CSFormatter._pck_lines(data, **ids._asdict())

        self.assertEqual(
            [
                "FV          ",
                "0005:49900001225C:201708",
                "0011 00000210616",
                "0012 00000210617",
                "0146 00000000002",
            ],
            return_value,
        )

    def test_form_header_codes(self):
        """
        This test tries to capture some information from the spec document.
        There seems to be a many:many mapping between cs_form and idbr_form codes.
        """
        test_inputs = defaultdict(list)
        for cs_form, *others in [
            ("MB01B", "49900009503", "A", 1704),
            ("MB01B", "49900107674", "C", 1704),
            ("MB15B", "49900108249", "D", 1704),
            ("T111G", "49900149151", "F", 1704),
            ("MB15B", "49900174681", "F", 1704),
            ("MB51B", "49900197962", "J", 1703),
            ("MB51B", "49900208075", "D", 1703),
            ("T111G", "49900216467", "H", 1704),
            ("T106G", "49900230086", "L", 1704),
            ("T111G", "49900243888", "T", 1704),
            ("MB01B", "49900311684", "J", 1704),
            ("T111G", "49901830949", "A", 1704),
            ("MB51B", "49902032365", "C", 1703),
            ("MB01B", "49902032365", "C", 1704),
            ("MB51B", "49902102007", "S", 1703),
            ("T117G", "49903538593", "A", 1704),
            ("MB01B", "49903717764", "S", 1703),
            ("MB01B", "49905286003", "B", 1704),
            ("MB01B", "49905464008", "D", 1701),
            ("MB01B", "49905464008", "D", 1702),
            ("MB01B", "49905988420", "T", 1704),
            ("MB51B", "49907127483", "L", 1703),
            ("T111G", "49907288956", "K", 1704),
            ("T117G", "49907524164", "H", 1704),
            ("MB01B", "49908076620", "K", 1704),
            ("T111G", "49908090280", "C", 1704),
            ("T111G", "49909394549", "D", 1704),
            ("T111G", "49909906097", "D", 1704),
            ("T161G", "49909918211", "C", 1703),
            ("T111G", "49910131935", "B", 1702),
            ("T161G", "49910131935", "B", 1703),
            ("T161G", "49910131935", "B", 1703),
            ("MB01B", "50000036184", "B", 1704),
        ]:
            test_inputs[cs_form].append(others)

        form_map = defaultdict(list)
        for idbr_form, cs_form in [
            ("0201", "MB01A"),
            ("0202", "MB01A"),
            ("0201", "MB01B"),
            ("0202", "MB01B"),
            ("0203", "MB03A"),
            ("0204", "MB03A"),
            ("0203", "MB03B"),
            ("0204", "MB03B"),
            ("0215", "MB15A"),
            ("0216", "MB15A"),
            ("0205", "MB15B"),
            ("0215", "MB15B"),
            ("0216", "MB15B"),
            ("0227", "MB27A"),
            ("0228", "MB27A"),
            ("0207", "MB27B"),
            ("0227", "MB27B"),
            ("0228", "MB27B"),
            ("0231", "MB31A"),
            ("0232", "MB31A"),
            ("0233", "MB31A"),
            ("0234", "MB31A"),
            ("0231", "MB31B"),
            ("0232", "MB31B"),
            ("0233", "MB31B"),
            ("0234", "MB31B"),
            ("0251", "MB51A"),
            ("0251", "MB51B"),
            ("0253", "MB53A"),
            ("0253", "MB53B"),
            ("0265", "MB65A"),
            ("0255", "MB65B"),
            ("0265", "MB65B"),
            ("0277", "MB77A"),
            ("0257", "MB77B"),
            ("0277", "MB77B"),
            ("0281", "MB81A"),
            ("0281", "MB81B"),
            ("0001", "T01E"),
            ("0002", "T01E"),
            ("0003", "T03E"),
            ("0004", "T03E"),
            ("0007", "T03E"),
            ("0005", "T05E"),
            ("0006", "T05E"),
            ("0009", "T09E"),
            ("0010", "T09E"),
            ("0102", "T102E"),
            ("0106", "T106E"),
            ("0106", "T106F"),
            ("0106", "T106G"),
            ("0111", "T111E"),
            ("0111", "T111F"),
            ("0111", "T111G"),
            ("0117", "T117E"),
            ("0117", "T117F"),
            ("0117", "T117G"),
            ("0121", "T121E"),
            ("0123", "T123E"),
            ("0123", "T123F"),
            ("0123", "T123G"),
            ("0011", "T12E"),
            ("0012", "T12E"),
            ("0013", "T13E"),
            ("0014", "T13E"),
            ("0152", "T152E"),
            ("0156", "T156E"),
            ("0156", "T156F"),
            ("0156", "T156G"),
            ("0158", "T158E"),
            ("0158", "T158F"),
            ("0158", "T158G"),
            ("0161", "T161E"),
            ("0161", "T161F"),
            ("0161", "T161G"),
            ("0167", "T167E"),
            ("0167", "T167F"),
            ("0167", "T167G"),
            ("0016", "T16E"),
            ("0017", "T16E"),
            ("0173", "T173E"),
            ("0173", "T173F"),
            ("0173", "T173G"),
            ("0020", "T20E"),
            ("0021", "T20E"),
            ("0022", "T22E"),
            ("0023", "T22E"),
            ("0024", "T24E"),
            ("0025", "T24E"),
            ("0051", "T51E"),
            ("0052", "T51E"),
            ("0053", "T53E"),
            ("0054", "T53E"),
            ("0057", "T53E"),
            ("0054", "T54E"),
            ("0058", "T54E"),
            ("0055", "T55E"),
            ("0056", "T55E"),
            ("0059", "T59E"),
            ("0060", "T59E"),
            ("0061", "T62E"),
            ("0062", "T62E"),
            ("0063", "T63E"),
            ("0064", "T63E"),
            ("0066", "T66E"),
            ("0067", "T66E"),
            ("0070", "T70E"),
            ("0071", "T70E"),
            ("0072", "T72E"),
            ("0073", "T72E"),
            ("0074", "T74E"),
            ("0075", "T74E"),
            ("0817", "T817E"),
            ("0817", "T817F"),
            ("0817", "T817G"),
            ("0823", "T823E"),
            ("0823", "T823F"),
            ("0823", "T823G"),
            ("0867", "T867E"),
            ("0867", "T867F"),
            ("0867", "T867G"),
            ("0873", "T873E"),
            ("0873", "T873F"),
            ("0873", "T873G"),
            ("0916", "T916E"),
            ("0917", "T916E"),
            ("0922", "T922E"),
            ("0923", "T922E"),
            ("0966", "T966E"),
            ("0967", "T966E"),
            ("0972", "T972E"),
            ("0973", "T972E"),
        ]:
            form_map[cs_form].append(idbr_form)

        for cs_form, values in test_inputs.items():
            for ru_ref, check, period in values:
                for idbr_form in form_map[cs_form]:
                    with self.subTest(cs_form=cs_form, idbr_form=idbr_form):
                        expected = ":".join((cs_form, ru_ref + check, str(period)))
                        return_value = CSFormatter._pck_form_header(
                            idbr_form, ru_ref, check, period
                        )
                        self.assertEqual(expected, return_value)
