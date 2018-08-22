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
