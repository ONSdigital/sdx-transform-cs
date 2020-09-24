import unittest
from transform.transformers.cora.mes_transformer import MESTransformer


def get_transformer(data):
    base_submission = {
        'metadata': {
            'user_id': 'K5O86M2NU1',
            'ru_ref': '12346789012A'
        },
        'origin': 'uk.gov.ons.edc.eq',
        'survey_id': '092',
        'tx_id': '40e659ec-013f-4888-9a31-ec1e0ad37888',
        'case_id': 'd9e9ce29-d755-4370-b96c-6c4176b722d1',
        'submitted_at': '2017-03-01T14:25:46.101447+00:00',
        'collection': {
            'period': '201605',
            'exercise_sid': '82R1VDWN74',
            'instrument_id': '0001'
        },
        'type': 'uk.gov.ons.edc.eq:surveyresponse',
        'version': '0.0.1',
    }

    base_submission.update(data)
    transformer = MESTransformer(base_submission)
    return transformer


class TestMesTransformer(unittest.TestCase):

    def test_mes_pck(self):
        d = {
            'data': {
                '1208': 'b'
            }
        }

        transformer = get_transformer(d)

        expected = "092:12346789012:1:201605:00000:1208:0010"

        self.assertEqual(expected, transformer.create_pck()[1])
