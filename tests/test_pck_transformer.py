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

    def test_pck_transformer_cannot_change_the_data_it_is_passed(self):
        """Tests that pck does not modify the data it is passed.
        Without the deep copy pck integer rounding will apply to the passed in data
        and hence get displayed in images"""

        survey = {'survey_id': '023'}
        response = {'collection': {'instrument_id': '000'}, 'data': {'item1': 'value1'}}
        pck_transformer = PCKTransformer(survey, response)
        pck_transformer.data['item1'] = 'new value'
        self.assertEquals(response['data']['item1'], 'value1')
