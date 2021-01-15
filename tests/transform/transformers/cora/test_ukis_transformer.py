import itertools
import json

import pytest

from transform.transformers.cora import UKISTransformer


def get_transformer(data):
    base_submission = {
        'metadata': {
            'user_id': 'K5O86M2NU1',
            'ru_ref': '12346789012A'
        },
        'origin': 'uk.gov.ons.edc.eq',
        'survey_id': '144',
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

    transformer = UKISTransformer(base_submission)

    return transformer


class TestTransformerUnits:
    data = open("./tests/pck/cora/144.0001.json").read()
    default_data = json.loads(data)

    @pytest.mark.parametrize('qcode, expected_output', [
        ('1', '0001'),
        ('2', '0010'),
        ('3', '0011'),
        ('4', '0100'),
        ('5', ''),
        ('6', '0001'),
        ('7', '0011'),
        ('8', '0100'),
        ('100', ''),
    ])
    def test_percentage_question(self, qcode, expected_output):
        """Tests percentage_question function.  This function is meant to be case-insensitive which is why
        later test cases mix the case to ensure this functionality works"""
        data = {
            'data': {
                '1': 'Over 90%',
                '2': '40-90%',
                '3': 'Less than 40%',
                '4': 'None',
                '5': 'unexpected',
                '6': 'over 90%',
                '7': 'less THAN 40%',
                '8': 'NoNe'
            }
        }

        transformer = get_transformer(data)

        assert transformer.percentage_question(qcode) == expected_output

    @staticmethod
    def test_get_qcode():
        """Tests the get_qcode function."""
        transformer = get_transformer({'data': {'123': 123, '456': 'This is a String'}})

        assert transformer.get_qcode('123') == 123
        assert transformer.get_qcode(123) is None
        assert transformer.get_qcode('123', not_found_value='') == 123
        assert transformer.get_qcode('456') == 'This is a String'
        assert transformer.get_qcode('456', lowercase=True) == 'this is a string'
        assert transformer.get_qcode('456', lowercase=True, not_found_value='') == 'this is a string'
        assert transformer.get_qcode('789') is None
        assert transformer.get_qcode('789', not_found_value='') == ''
        assert transformer.get_qcode('789', lowercase=True) is None

    @pytest.mark.parametrize('qcode, expected_output', [
        ('1', '10'),
        ('2', '01'),
        ('500', '')
    ])
    def test_yes_no_question(self, qcode, expected_output):
        """Tests the yes_no_question function without modifying the yes/no return values"""
        data = {
            'data': {
                '1': 'Yes',
                '2': 'No'
            }
        }

        transformer = get_transformer(data)

        assert transformer.yes_no_question(qcode) == expected_output

    @pytest.mark.parametrize('qcode, yes_value, no_value, expected_output', [
        ('1', '10', '01', '10'),
        ('2', '10', '01', '01'),
        ('500', '10', '01', '')
    ])
    def test_yes_no_question_with_custom_return_values(self, qcode, yes_value, no_value, expected_output):
        """Tests the yes_no_question function with modified yes/no return values"""
        data = {
            'data': {
                '1': 'Yes',
                '2': 'No'
            }
        }

        transformer = get_transformer(data)

        assert transformer.yes_no_question(qcode, yes_value=yes_value, no_value=no_value) == expected_output

    @pytest.mark.parametrize('qcode, expected_output', [
        ('1', '1'),
        ('2', '1'),
        ('3', ''),
    ])
    def test_checkbox_question(self, qcode, expected_output):
        data = {
            'data': {
                '1': 'Option number 1',
                '2': 'Option number 2'
            }
        }

        transformer = get_transformer(data)

        assert transformer.checkbox_question(qcode) == expected_output

    @pytest.mark.parametrize('qcode, dependant_qcodes, expected_output', [
        ('1', ['1', '2', '3', '4'], '10'),
        ('2', ['1', '2', '3', '4'], '10'),
        ('2', ['2', '3', '4'], '10'),
        ('3', ['1', '2', '3', '4'], '01'),
        ('3', ['3', '4'], ''),
        ('4', ['1', '2', '3', '4'], '01'),
        ('4', ['3', '4'], '')
    ])
    def test_checkbox_question_with_dependant_qcode_and_custom_return_values(self, qcode, dependant_qcodes,
                                                                             expected_output):
        """Tests the checkbox_question function.  Normally there would be separate tests for both the dependant_qcodes and the modified
        return values, but it's easier to highlight what the dependant_qcodes are checking this way.  Without this, both empty qcodes and
        sets of dependant_qcodes would both return None."""
        data = {
            'data': {
                '1': 'Option number 1',
                '2': 'Option number 2',
            }
        }

        transformer = get_transformer(data)

        assert transformer.checkbox_question(qcode, dependent_qcodes=dependant_qcodes, checked="10",
                                             unchecked="01") == expected_output

    def test_pck_file(self):
        transformer = get_transformer(self.default_data)
        pck = transformer.create_pck()
        assert pck

    def test_idbr_receipt(self):
        transformer = get_transformer(self.default_data)
        name, idbr = transformer.create_receipt()
        assert idbr == '13141978737:G:144:201605'

    def test_create_zip(self):
        transformer = get_transformer(self.default_data)

        transformer.get_zip(img_seq=itertools.count())
        actual = transformer.image_transformer.zip.get_filenames()

        expected = [
            'EDC_QData/144_16328a9912994f09',
            'EDC_QReceipts/REC1501_16328a9912994f09.DAT',
            'EDC_QImages/Images/S16328a9912994f09_1.JPG',
            'EDC_QImages/Images/S16328a9912994f09_2.JPG',
            'EDC_QImages/Images/S16328a9912994f09_3.JPG',
            'EDC_QImages/Images/S16328a9912994f09_4.JPG',
            'EDC_QImages/Images/S16328a9912994f09_5.JPG',
            'EDC_QImages/Images/S16328a9912994f09_6.JPG',
            'EDC_QImages/Images/S16328a9912994f09_7.JPG',
            'EDC_QImages/Images/S16328a9912994f09_8.JPG',
            'EDC_QImages/Images/S16328a9912994f09_9.JPG',
            'EDC_QImages/Images/S16328a9912994f09_10.JPG',
            'EDC_QImages/Images/S16328a9912994f09_11.JPG',
            'EDC_QImages/Images/S16328a9912994f09_12.JPG',
            'EDC_QImages/Images/S16328a9912994f09_13.JPG',
            'EDC_QImages/Images/S16328a9912994f09_14.JPG',
            'EDC_QImages/Index/EDC_144_20210115_16328a9912994f09.csv',
            'EDC_QJson/144_16328a9912994f09.json'
        ]
        assert expected == actual
