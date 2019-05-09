import unittest

from transform.transformers.common_software import PCKTransformer


class TestPckTransformer(unittest.TestCase):

    def test_get_cs_form_id_passes(self):
        scenarios = [
            ('023', '0102', 'RSI5B'),
            ('139', '0001', 'Q01B'),
            ('019', '0018', '0018'),
            ('019', '0019', '0019'),
            ('019', '0020', '0020')
        ]
        for survey_id, instrument_id, expected_form_id in scenarios:
            survey = {'survey_id': survey_id}
            response = {'collection': {'instrument_id': instrument_id}}
            pck_transformer = PCKTransformer(survey, response)
            form_id = pck_transformer.get_cs_form_id()

            assert form_id == expected_form_id

    def test_get_cs_form_id_invalid_survey(self):
        survey = {'survey_id': 23}
        response = {'collection': {'instrument_id': '0102'}}
        pck_transformer = PCKTransformer(survey, response)

        with self.assertLogs(level='ERROR') as cm:
            form_id = pck_transformer.get_cs_form_id()
            self.assertEqual(form_id, None)

            msg = "ERROR:transform.transformers.common_software.pck_transformer:survey_id=23 event='Invalid survey id'"
            self.assertEqual(msg, cm.output[0])

    def test_get_cs_form_id_invalid_instrument(self):
        survey = {'survey_id': '023'}
        response = {'collection': {'instrument_id': '000'}}
        pck_transformer = PCKTransformer(survey, response)

        with self.assertLogs(level='ERROR') as cm:
            form_id = pck_transformer.get_cs_form_id()
            self.assertEqual(form_id, None)

            msg = "ERROR:transform.transformers.common_software.pck_transformer:instrument_id='000' event='Invalid instrument id'"
            self.assertEqual(msg, cm.output[0])

        # QCAS
        survey = {'survey_id': '019'}
        response = {'collection': {'instrument_id': '0021'}}
        pck_transformer = PCKTransformer(survey, response)

        with self.assertLogs(level='ERROR') as cm:
            form_id = pck_transformer.get_cs_form_id()
            self.assertEqual(form_id, None)

            msg = "ERROR:transform.transformers.common_software.pck_transformer:instrument_id='0021' event='Invalid instrument id'"
            self.assertEqual(msg, cm.output[0])

    def test_pck_transformer_cannot_change_the_data_it_is_passed(self):
        """Tests that pck does not modify the data it is passed.
        Without the deep copy pck integer rounding will apply to the passed in data
        and hence get displayed in images"""

        survey = {'survey_id': '023'}
        response = {'collection': {'instrument_id': '000'}, 'data': {'item1': 'value1'}}
        pck_transformer = PCKTransformer(survey, response)
        pck_transformer.data['item1'] = 'new value'
        assert response['data']['item1'] == 'value1'

    def test_pck_transformer_discards_qcas_confirmation_question(self):
        """
        For QCAS, the questions 'd681' and 'd12' does not need to be transformed,
        hence can be deleted.
        """
        survey = {'survey_id': '019'}
        response = {'collection': {'instrument_id': '000'}, 'data': {'681': '100', 'd681': 'Yes', 'd12': 'Yes'}}
        pck_transformer = PCKTransformer(survey, response)

        assert pck_transformer.data == {'681': '100', 'd681': 'Yes', 'd12': 'Yes'}

        pck_transformer.evaluate_confirmation_questions()

        assert pck_transformer.data == {'681': '100'}

    @staticmethod
    def test_pck_transformer_parse_estimation_question():
        """
        For QSI (Stocks), qcode 15 needs to converted from Yes/No to 1/0 for the pck.
        """
        survey = {'survey_id': '017'}

        # qcode 15 = Yes case
        response = {'collection': {'instrument_id': '0001'}, 'data': {'15': 'Yes', '146': 'Comment question', '139': '13900'}}
        pck_transformer = PCKTransformer(survey, response)
        assert pck_transformer.data == {'15': 'Yes', '146': 'Comment question', '139': '13900'}
        pck_transformer.parse_estimation_question()
        assert pck_transformer.data == {'15': '1', '146': 'Comment question', '139': '13900'}

        # qcode 15 = No case
        response = {'collection': {'instrument_id': '0001'}, 'data': {'15': 'No', '146': 'Comment question', '139': '13900'}}
        pck_transformer = PCKTransformer(survey, response)
        assert pck_transformer.data == {'15': 'No', '146': 'Comment question', '139': '13900'}
        pck_transformer.parse_estimation_question()
        assert pck_transformer.data == {'15': '0', '146': 'Comment question', '139': '13900'}

    def test_pck_transformer_parse_negative_values(self):
        """If any values in the survey are negative, they should be replaced with an all 9's string that is 11 characters long
        """
        survey = {'survey_id': '019'}
        response = {'collection': {'instrument_id': '000'},
                    'data': {'681': '-100', '703': '-1234', '704': '-12345', '707': '-123456', '708': '-0', '709': '1234', '710': '-123word'}}
        pck_transformer = PCKTransformer(survey, response)
        self.assertEqual(pck_transformer.data, {
            '681': '-100',
            '703': '-1234',
            '704': '-12345',
            '707': '-123456',
            '708': '-0',
            '709': '1234',
            '710': '-123word'})

        pck_transformer.parse_negative_values()
        self.assertEqual(pck_transformer.data, {
            '681': '99999999999',
            '703': '99999999999',
            '704': '99999999999',
            '707': '99999999999',
            '708': '99999999999',
            '709': '1234',
            '710': '-123word'})

    def test_pck_transformer_preprocess_comments(self):
        """Tests 2 things.  First, if every comment question (147 and all 146x) is present and 146 IS NOT in the data, then 146 is added.
        Second, all of the comment questions are removed from the submission as they're not put into the pck file.
        """
        survey = {'survey_id': '019'}
        response = {'collection': {'instrument_id': '000'},
                    'data': {
                        "11": "03/07/2018",
                        "12": "01/10/2018",
                        "681": "123456.78",
                        "146a": "Yes",
                        "146b": "Start or end of a long term project",
                        "146c": "Site changes, for example, openings, closures, refurbishments or upgrades",
                        "146d": "End of accounting period or financial year",
                        "146e": "Normal movement for time of year",
                        "146f": "Change of business structure, merger, or takeover",
                        "146g": "One off or unusual investment",
                        "146h": "Introduction / removal of new legislation / incentive",
                        "146i": "Availability of credit",
                        "146j": "Overspend during the previous quarter",
                        "146k": "Other",
                        '147': "Yes",
                        'd12': 'Yes'}}

        pck_transformer = PCKTransformer(survey, response)
        self.assertEqual(pck_transformer.data, {
            "11": "03/07/2018",
            "12": "01/10/2018",
            "681": "123456.78",
            "146a": "Yes",
            "146b": "Start or end of a long term project",
            "146c": "Site changes, for example, openings, closures, refurbishments or upgrades",
            "146d": "End of accounting period or financial year",
            "146e": "Normal movement for time of year",
            "146f": "Change of business structure, merger, or takeover",
            "146g": "One off or unusual investment",
            "146h": "Introduction / removal of new legislation / incentive",
            "146i": "Availability of credit",
            "146j": "Overspend during the previous quarter",
            "146k": "Other",
            '147': "Yes",
            'd12': 'Yes'})

        pck_transformer.preprocess_comments()
        self.assertEqual(pck_transformer.data, {
            "11": "03/07/2018",
            "12": "01/10/2018",
            "146": 1,
            "681": "123456.78",
            'd12': 'Yes'})

    def test_pck_transformer_calculates_total_playback_qcas(self):
        """
        For QCAS, downstream needs the calculated values for both acquisitions
        and proceeds from disposals to be sent in the PCK.
        """
        survey = {'survey_id': '019'}
        response = {
            "collection": {
                "instrument_id": "0020"
            },
            "data": {
                "11": "03/07/2018",
                "12": "01/10/2018",
                "146": "A lot of changes.",

                # Disposals
                "689": "499",
                "696": "500",
                "704": "12345.67",
                "708": "12345500",
                "710": "-499",
                "712": "-12345.67",

                # Construction
                "681": "1000",

                # Acquisitions
                "688": "1500",
                "695": "1500",
                "703": "1500",
                "707": "1500",
                "709": "1500",
                "711": "1500",

                # Mineral
                "697": "-1500",

                "146a": "Yes",
                "146b": "Start or end of a long term project",
                "146c": "Site changes, for example, openings, closures, refurbishments or upgrades",
                "146d": "End of accounting period or financial year",
                "146e": "Normal movement for time of year",
                "146f": "Change of business structure, merger, or takeover",
                "146g": "One off or unusual investment",
                "146h": "Introduction / removal of new legislation / incentive",
                "146i": "Availability of credit",
                "146j": "Overspend during the previous quarter",
                "146k": "Other",
                "d12": "Yes",
                "d681": "Yes"
            }
        }

        pck_transformer = PCKTransformer(survey, response)

        pck_transformer.round_numeric_values()

        assert pck_transformer.data['689'] == '0'
        assert pck_transformer.data['696'] == '1'
        assert pck_transformer.data['704'] == '12'
        assert pck_transformer.data['708'] == '12346'
        assert pck_transformer.data['710'] == '-0'
        assert pck_transformer.data['712'] == '-12'

        pck_transformer.calculate_total_playback()

        # Total value of acquisitions questions for only machinery and equipments section
        assert pck_transformer.data['714'] == '12'

        # Total value of disposals questions for only machinery and equipments section
        assert pck_transformer.data['715'] == '12347'

        # Total value of all acquisitions questions
        assert pck_transformer.data['692'] == '11'

        # Total value of all disposals questions (same as '715' since constructions section and minerals sections does not have disposals question)
        assert pck_transformer.data['693'] == '12347'

    @staticmethod
    def test_pck_transformer_calculates_total_playback_qsi():
        """
        For QSI (Stocks), downstream needs to calculate the start and end of period totals.
        The fields that are added together are defined in a dictionary in the pck_transformer
        """
        scenarios = ["0001", "0002"]
        for form_type in scenarios:
            survey = {'survey_id': "017"}
            response = {
                "collection": {
                    "instrument_id": form_type
                },
                "data": {
                    "15": "Yes",
                    "139": "7300",
                    "140": "7680",
                    "144": "2000",
                    "145": "2205",
                    "146": "A lot of changes.",
                    "149": "1800",
                    "150": "12205",
                }
            }

            pck_transformer = PCKTransformer(survey, response)
            pck_transformer.calculate_total_playback()

            assert pck_transformer.data == {
                '15': "Yes",
                '65': '11100',
                '66': '22090',
                '139': '7300',
                '140': '7680',
                '144': '2000',
                '145': '2205',
                '146': 'A lot of changes.',
                '149': '1800',
                '150': '12205'
            }

    def test_pck_transformer_total_playback_qsi_missing_data_from_mapping(self):
        """
        For QSI (Stocks), downstream needs to calculate the start and end of period totals.
        It does this with a mapping in the pck_transformer.  If a new formtype is added but it's not
        added to the mapping or a 'start' or 'end' key isn't present then a KeyError exception is thrown.
        """

        scenarios = ["9999", "0033"]
        for form_type in scenarios:
            survey = {'survey_id': "017"}
            response = {
                "collection": {
                    "instrument_id": form_type
                },
                "data": {
                    "15": "Yes",
                    "139": "7300",
                    "140": "7680",
                    "144": "2000",
                    "145": "2205",
                    "146": "A lot of changes.",
                    "149": "1800",
                    "150": "12205",
                }
            }

            pck_transformer = PCKTransformer(survey, response)
            pck_transformer.qsi_questions = {
                "0033": {
                    "end": ['140', '145', '150']
                }
            }
            with self.assertRaises(KeyError):
                pck_transformer.calculate_total_playback()

    @staticmethod
    def test_pck_transformer_round_numeric_values_qpses():
        """
        For QPSES, a number of values require rounding before being sent downstream.  These should round up on a .5 answer.
        """
        scenarios = ["160", "165", "169"]
        for survey_id in scenarios:
            survey = {'survey_id': survey_id}
            response = {
                "collection": {
                    "instrument_id": "0020"
                },
                "data": {
                    "60": 50.5,
                    "561": 50.3,
                    "562": 74.49,
                    "661": 80.1,
                    "662": 34.8,
                    "146": "A lot of changes.",
                }
            }

            pck_transformer = PCKTransformer(survey, response)
            pck_transformer.round_numeric_values()

            assert pck_transformer.data == {
                '60': '51',
                '146': 'A lot of changes.',
                '561': '50',
                '562': '74',
                '661': '80',
                '662': '35'
            }

    def test_pck_transformer_round_numeric_values_qsi(self):
        """
        For QSI (Stocks), a number of values require rounding before being sent downstream. These should
        be rounded to the nearest thousand.
        For example:
            - 12100 -> 12000
            - 12500 -> 13000
            - 12501 -> 13000
        """
        scenarios = ["0001", "0002"]
        for form_type in scenarios:
            survey = {'survey_id': "017"}
            response = {
                "collection": {
                    "instrument_id": form_type
                },
                "data": {
                    "15": "Yes",
                    "65": "311500",
                    "66": "313103",
                    "139": "7300",
                    "140": "7680",
                    "144": "2000",
                    "145": "2205",
                    "146": "A lot of changes.",
                    "149": "1800",
                    "150": "12205",
                }
            }

            pck_transformer = PCKTransformer(survey, response)
            pck_transformer.round_numeric_values()

            assert pck_transformer.data == {
                '15': "Yes",
                '65': '312000',
                '66': '313000',
                '139': '7000',
                '140': '8000',
                '144': '2000',
                '145': '2000',
                '146': 'A lot of changes.',
                '149': '2000',
                '150': '12000'
            }
