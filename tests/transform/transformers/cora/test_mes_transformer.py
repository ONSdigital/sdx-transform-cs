import unittest
from transform.transformers.cora.mes_transformer import MESTransformer


def get_transformer(data=None):
    if data is None:
        data = {}
    submission = {
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
        'data': data
    }

    transformer = MESTransformer(submission)
    return transformer


class TestMesTransformer(unittest.TestCase):

    def test_no_transform(self):
        transformer = get_transformer({'1171': '123'})
        expected = '092:12346789012:1:201605:00000:1171:123'
        self.assertEqual(expected, transformer.create_pck()[1])

    def test_cb1(self):
        transformer = get_transformer({'1208': 'e'})
        expected = '092:12346789012:1:201605:00000:1208:0101'
        self.assertEqual(expected, transformer.create_pck()[1])

    def test_cb2(self):
        transformer = get_transformer({'1174': 'a'})
        expected = '092:12346789012:1:201605:00000:1174:1000'
        self.assertEqual(expected, transformer.create_pck()[1])

    def test_cb3(self):
        transformer = get_transformer({'1020': 'c'})
        expected = '092:12346789012:1:201605:00000:1020:00100'
        self.assertEqual(expected, transformer.create_pck()[1])

    def test_pounds_thousands(self):
        transformer = get_transformer({'1086': '5500'})
        expected = '092:12346789012:1:201605:00000:1086:5500'
        self.assertEqual(expected, transformer.create_pck()[1])

    def test_comments(self):
        transformer = get_transformer({'1163': 'my comment'})
        expected = '092:12346789012:1:201605:00000:1163:1'
        self.assertEqual(expected, transformer.create_pck()[1])

    def test_receipt(self):
        transformer = get_transformer()
        name, receipt = transformer.create_receipt()
        self.assertEqual('12346789012:A:092:201605', receipt)
