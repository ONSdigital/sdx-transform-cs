import unittest

from transform.transformers.pck_transformer import PCKTransformer


class TestPckTransformer(unittest.TestCase):

    def test_get_cs_form_id_passes(self):
        survey = {'survey_id': '023'}
        response = {'collection': {'instrument_id': '0102'}}
        pck_transformer = PCKTransformer(survey, response)
        form_id = pck_transformer.get_cs_form_id()

        self.assertEqual(form_id, 'RSI5B', msg=None)

        survey = {'survey_id': '139'}
        response = {'collection': {'instrument_id': '0001'}}
        pck_transformer = PCKTransformer(survey, response)
        form_id = pck_transformer.get_cs_form_id()

        self.assertEqual(form_id, 'Q01B', msg=None)

        # QCAS
        survey = {'survey_id': '019'}
        response = {'collection': {'instrument_id': '0018'}}
        pck_transformer = PCKTransformer(survey, response)
        form_id = pck_transformer.get_cs_form_id()

        self.assertEqual(form_id, '0018', msg=None)

        survey = {'survey_id': '019'}
        response = {'collection': {'instrument_id': '0019'}}
        pck_transformer = PCKTransformer(survey, response)
        form_id = pck_transformer.get_cs_form_id()

        self.assertEqual(form_id, '0019', msg=None)

        survey = {'survey_id': '019'}
        response = {'collection': {'instrument_id': '0020'}}
        pck_transformer = PCKTransformer(survey, response)
        form_id = pck_transformer.get_cs_form_id()

        self.assertEqual(form_id, '0020', msg=None)

    def test_get_cs_form_id_invalid_survey(self):
        survey = {'survey_id': 23}
        response = {'collection': {'instrument_id': '0102'}}
        pck_transformer = PCKTransformer(survey, response)

        with self.assertLogs(level='ERROR') as cm:
            form_id = pck_transformer.get_cs_form_id()
            self.assertEqual(form_id, None)

            msg = "ERROR:transform.transformers.pck_transformer:Invalid survey id '23'"
            self.assertEqual(msg, cm.output[0])

    def test_get_cs_form_id_invalid_instrument(self):
        survey = {'survey_id': '023'}
        response = {'collection': {'instrument_id': '000'}}
        pck_transformer = PCKTransformer(survey, response)

        with self.assertLogs(level='ERROR') as cm:
            form_id = pck_transformer.get_cs_form_id()
            self.assertEqual(form_id, None)

            msg = "ERROR:transform.transformers.pck_transformer:Invalid instrument id '000'"
            self.assertEqual(msg, cm.output[0])

        # QCAS
        survey = {'survey_id': '019'}
        response = {'collection': {'instrument_id': '0021'}}
        pck_transformer = PCKTransformer(survey, response)

        with self.assertLogs(level='ERROR') as cm:
            form_id = pck_transformer.get_cs_form_id()
            self.assertEqual(form_id, None)

            msg = "ERROR:transform.transformers.pck_transformer:Invalid instrument id '0021'"
            self.assertEqual(msg, cm.output[0])

    def test_pck_transformer_cannot_change_the_data_it_is_passed(self):
        """Tests that pck does not modify the data it is passed.
        Without the deep copy pck integer rounding will apply to the passed in data
        and hence get displayed in images"""

        survey = {'survey_id': '023'}
        response = {'collection': {'instrument_id': '000'}, 'data': {'item1': 'value1'}}
        pck_transformer = PCKTransformer(survey, response)
        pck_transformer.data['item1'] = 'new value'
        self.assertEquals(response['data']['item1'], 'value1')

    def test_pck_transformer_discards_qcas_confirmation_question(self):
        """
        For QCAS, the questions 'd681' and 'd12' does not need to be transformed,
        hence can be deleted.
        """
        survey = {'survey_id': '019'}
        response = {'collection': {'instrument_id': '000'}, 'data': {'681': '100', 'd681': 'Yes', 'd12': 'Yes'}}
        pck_transformer = PCKTransformer(survey, response)

        self.assertEquals(pck_transformer.data, {'681': '100', 'd681': 'Yes', 'd12': 'Yes'})

        pck_transformer.evaluate_confirmation_questions()

        self.assertEquals(pck_transformer.data, {'681': '100'})

    def test_pck_transformer_parse_negative_values(self):
        """If any values in the survey are negative, they should be replaced with an all 9's string that is 11 characters long
        """
        survey = {'survey_id': '019'}
        response = {'collection': {'instrument_id': '000'},
                    'data': {'681': '-100', '703': '-1234', '704': '-12345', '707': '-123456', '708': '-0', '709': '1234', '710': '-123word'}}
        pck_transformer = PCKTransformer(survey, response)
        self.assertEquals(pck_transformer.data, {
            '681': '-100',
            '703': '-1234',
            '704': '-12345',
            '707': '-123456',
            '708': '-0',
            '709': '1234',
            '710': '-123word'})

        pck_transformer.parse_negative_values()
        self.assertEquals(pck_transformer.data, {
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
        self.assertEquals(pck_transformer.data, {
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
        self.assertEquals(pck_transformer.data, {
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

        pck_transformer.round_currency_values()

        self.assertEquals(pck_transformer.data['689'], '0')
        self.assertEquals(pck_transformer.data['696'], '1')
        self.assertEquals(pck_transformer.data['704'], '12')
        self.assertEquals(pck_transformer.data['708'], '12346')
        self.assertEquals(pck_transformer.data['710'], '-0')
        self.assertEquals(pck_transformer.data['712'], '-12')

        pck_transformer.calculate_total_playback()

        # Total value of acquisitions questions for only machinery and equipments section
        self.assertEquals(pck_transformer.data['714'], '12')

        # Total value of disposals questions for only machinery and equipments section
        self.assertEquals(pck_transformer.data['715'], '12347')

        # Total value of all acquisitions questions
        self.assertEquals(pck_transformer.data['692'], '11')

        # Total value of all disposals questions (same as '715' since constructions section and minerals sections does not have disposals question)
        self.assertEquals(pck_transformer.data['693'], '12347')
