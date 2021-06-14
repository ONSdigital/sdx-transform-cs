import json

import pytest
import yaml

from transform.transformers.cord import EcommerceTransformer, Ecommerce2019Transformer


def get_transformer(data):
    base_submission = {
        'metadata': {
            'user_id': 'K5O86M2NU1',
            'ru_ref': '12346789012A'
        },
        'origin': 'uk.gov.ons.edc.eq',
        'survey_id': '187',
        'tx_id': '40e659ec-013f-4888-9a31-ec1e0ad37888',
        'case_id': 'd9e9ce29-d755-4370-b96c-6c4176b722d1',
        'submitted_at': '2017-03-01T14:25:46.101447+00:00',
        'collection': {
            'period': '201605',
            'exercise_sid': '82R1VDWN74',
            'instrument_id': '0051'
        },
        'type': 'uk.gov.ons.edc.eq:surveyresponse',
        'version': '0.0.1',
    }

    base_submission.update(data)

    transformer = EcommerceTransformer(base_submission)

    return transformer


def get_2019transformer(data):
    base_submission = {
        'metadata': {
            'user_id': 'K5O86M2NU1',
            'ru_ref': '12346789012A'
        },
        'origin': 'uk.gov.ons.edc.eq',
        'survey_id': '187',
        'tx_id': '40e659ec-013f-4888-9a31-ec1e0ad37888',
        'case_id': 'd9e9ce29-d755-4370-b96c-6c4176b722d1',
        'submitted_at': '2017-03-01T14:25:46.101447+00:00',
        'collection': {
            'period': '2019',
            'exercise_sid': '82R1VDWN74',
            'instrument_id': '0001'
        },
        'type': 'uk.gov.ons.edc.eq:surveyresponse',
        'version': '0.0.1',
    }

    base_submission.update(data)

    transformer = Ecommerce2019Transformer(base_submission)

    return transformer


class TestExampleSubmission:
    with open('tests/replies/eq-ecommerce-test-submission.json', 'r') as fp:
        response = json.load(fp)

    transformer = EcommerceTransformer(response)
    transformed_data = transformer.transform()

    def test_submission_output(self):
        with open('tests/replies/eq-ecommerce-expected-output.yaml', 'r') as fp:
            expected_output = yaml.load(fp, Loader=yaml.FullLoader)

        assert self.transformed_data == expected_output

    def test_dummy_qcodes_not_in_output(self):
        pck = self.transformer.create_pck()
        assert pck


class TestTransformerUnits:
    default_data = {'data': {'010': 'Yes',
                             '023': '10.98',
                             '154': 'No',
                             '165': 'Training for ICT or IT specialists',
                             '316': 'Training for other employees',
                             '155': 'Yes',
                             '156': 'No',
                             '038': 'Yes',
                             '022': '20.21',
                             '356': 'Yes',
                             'r1': '30Mbps or more, but less than 100Mbps',
                             '453': 'Yes',
                             '320': '11.21',
                             '080': 'Yes',
                             '203': 'Online ordering or reservation / booking',
                             'd1': "I don't know what they are",
                             '386': 'Social Networks',
                             'd2': "I don't know what they are",
                             '346': 'Exchange views opinions or knowledge within this business',
                             'd3': "I don't know what they are",
                             '190': 'Yes',
                             '191': 'Yes',
                             '197': 'Yes',
                             '272': 'Strong password authentication',
                             '482': 'User identification and authentication via biometric methods implemented in the business',
                             '483': 'Encryption techniques for data, documents or email',
                             '484': 'Access control to business network',
                             '485': 'VPN (Virtual Private Network)',
                             '481': 'Keeping the software up to date',
                             '487': 'ICT security tests',
                             'd5': "They're not used",
                             '266': 'No',
                             '265': 'No',
                             '267': 'Yes',
                             '488': 'Own employees',
                             '490': 'No',
                             'r3': 'Within the last 12 months',
                             '491': 'Yes',
                             '492': 'No',
                             '493': 'Yes',
                             '494': 'Yes',
                             '234': 'Yes',
                             '235': '0.8',
                             '348': '23.1',
                             '349': '76.9',
                             '458': "Via this business own website or 'app'",
                             '459': "Via an e-commerce market place website or 'app' used by several businesses for trading product",
                             '460': '10',
                             '461': '90',
                             '310': 'UK',
                             '311': 'Other EU Countries',
                             '312': 'Rest of the world',
                             '466': 'Restrictions from business partners to sell to certain EU countries',
                             'd6': "They weren't experienced",
                             '257': 'No'}}

    @pytest.mark.parametrize('percentage_input, expected', [
        ('0.1', '0001'),
        ('0.9', '0009'),
        ('0.99', '0010'),
        ('1.11', '0011'),
        ('11.12', '0111'),
        ('99.9', '0999'),
        ('99.99', '1000'),
        ('0', '0000')
    ])
    def test_convert_percentage(self, percentage_input, expected):
        assert EcommerceTransformer.convert_percentage(percentage_input) == expected

    def test_get_qcode(self):
        """Tests the get_qcode function."""
        transformer = get_transformer({'data': {'123': 123}})

        assert transformer.get_qcode('123') == 123
        assert transformer.get_qcode(123) is None

    @pytest.mark.parametrize('qcode, expected_output', [
        ('1', '10'),
        ('2', '01'),
        ('3', '00'),
        ('500', '00')
    ])
    def test_yes_no_question(self, qcode, expected_output):
        data = {
            'data': {
                '1': 'Yes',
                '2': 'No',
                '3': 'Maybe'
            }
        }

        transformer = get_transformer(data)

        assert transformer.yes_no_question(qcode) == expected_output

    @pytest.mark.parametrize('qcode, playback_qcode, expected_output', [
        ('1', 'd1', '10'),
        ('2', 'd1', '10'),
        ('100', 'd1', '01'),
        ('100', 'd2', '00'),
        ('100', 'd3', '01'),
    ])
    def test_negative_playback(self, qcode, playback_qcode, expected_output):
        data = {
            'data': {
                '1': 'Yes',
                '2': 'No',
                'd1': 'They’re not used',
                'd2': 'I don’t know what they are',
                'd3': 'They weren’t experienced',
                '3': 'extra'
            }
        }

        transformer = get_transformer(data)

        assert transformer.negative_playback_question(qcode, playback_qcode) == expected_output

    @pytest.mark.parametrize('qcode, answer_value, expected_output', [
        ('r1', 'Something else', '1'),
        ('r1', 'Not something else', '0'),
        ('r2', 'Not something else', '0'),
    ])
    def test_radio_question_option(self, qcode, answer_value, expected_output):
        data = {
            'data': {
                '1': 'Something Something',
                'r1': 'Something else'
            }
        }

        transformer = get_transformer(data)

        assert transformer.radio_question_option(qcode, answer_value) == expected_output

    @pytest.mark.parametrize('qcode, answer_value, checked, unchecked, unanswered, expected_output', [
        ('r1', 'Something else', '10', '01', '00', '10'),
        ('r1', 'Not something else', '10', '01', '00', '01'),
        ('r2', 'Not something else', '10', '01', '00', '00'),
    ])
    def test_radio_question_option_with_custom_checked_and_unchecked(self, qcode, answer_value, checked, unchecked, unanswered, expected_output):
        data = {
            'data': {
                '1': 'Something Something',
                'r1': 'Something else'
            }
        }

        transformer = get_transformer(data)

        assert transformer.radio_question_option(qcode, answer_value, checked=checked, unchecked=unchecked, unanswered=unanswered) == expected_output

    @pytest.mark.parametrize('qcode, expected_output', [
        ('1', '10'),
        ('1', '10'),
        ('2', '10'),
        ('3', '01'),
    ])
    def test_checkbox_question_without_dependant_qcode(self, qcode, expected_output):
        data = {
            'data': {
                '1': 'Option number 1',
                '2': 'Option number 2'
            }
        }

        transformer = get_transformer(data)

        assert transformer.checkbox_question(qcode) == expected_output

    @pytest.mark.parametrize('qcode, dependant_qcode, expected_output', [
        ('1', '10', '00'),
        ('1', '100', '10'),
        ('1', '101', '00'),
        ('2', '10', '00'),
        ('2', '100', '10'),
        ('2', '101', '00'),
        ('3', '10', '00'),
        ('3', '100', '01'),
        ('3', '101', '00'),
    ])
    def test_checkbox_question_with_dependant_qcode(self, qcode, dependant_qcode, expected_output):
        data = {
            'data': {
                '1': 'Option number 1',
                '2': 'Option number 2',
                '10': 'No',
                '100': "Yes",
                '101': "No"
            }
        }

        transformer = get_transformer(data)

        assert transformer.checkbox_question(qcode, dependant_qcode) == expected_output

    @pytest.mark.parametrize('data, qcode, related_qcode, dependant_qcodes, expected_output', [
        ({'505': 'UK'}, '507', '505', ['505', '506'], '1000'),
        ({'506': 'Europe'}, '507', '505', ['505', '506'], '0'),
        ({'505': 'UK', '506': 'Europe', '507': "10.2", '508': '89.8'}, '507', '505', ['505', '506'], '0102'),
        ({'505': 'UK', '506': 'Europe', '507': '0', '508': '100.0'}, '507', '505', ['505', '506'], '0000'),
    ])
    def test_percentage_question_with_dependancies(self, data, qcode, related_qcode, dependant_qcodes, expected_output):
        data = {
            'data': data
        }

        transformer = get_2019transformer(data)

        assert transformer.percentage_question_with_dependancies(qcode, related_qcode, dependant_qcodes) == expected_output

    def test_pck_file(self):
        transformer = get_transformer(self.default_data)
        pck = transformer.create_pck()
        assert pck

    def test_idbr_receipt(self):
        """Tests the content of the idbr receipt is as expected"""
        transformer = get_transformer(self.default_data)
        name, idbr = transformer.create_receipt()
        assert idbr == '12346789012:A:187:201605'

    def test_create_zip(self):
        """Tests the filenames in the created zip are the ones we're expecting"""

        with open('tests/replies/eq-ecommerce-test-submission.json', 'r') as fp:
            response = json.load(fp)

        transformer = get_transformer(response)

        transformer.get_zip()
        actual = transformer.image_transformer.zip.get_filenames()

        expected = [
            'EDC_QData/187_40e659ec013f4888',
            'EDC_QReceipts/REC0103_40e659ec013f4888.DAT',
            'EDC_QImages/Images/S40e659ec013f4888_1.JPG',
            'EDC_QImages/Images/S40e659ec013f4888_2.JPG',
            'EDC_QImages/Images/S40e659ec013f4888_3.JPG',
            'EDC_QImages/Images/S40e659ec013f4888_4.JPG',
            'EDC_QImages/Images/S40e659ec013f4888_5.JPG',
            'EDC_QImages/Images/S40e659ec013f4888_6.JPG',
            'EDC_QImages/Images/S40e659ec013f4888_7.JPG',
            'EDC_QImages/Images/S40e659ec013f4888_8.JPG',
            'EDC_QImages/Index/EDC_187_20170301_40e659ec013f4888.csv',
            'EDC_QJson/187_40e659ec013f4888.json'
        ]
        assert expected == actual
