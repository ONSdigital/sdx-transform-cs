import itertools
import json

import pytest

from transform.transformers.transform_selector import get_transformer


class TestExampleSubmission:

    @pytest.fixture
    def submission(self):
        with open('tests/replies/eq-ecommerce-test-submission.json', 'r') as fp:
            response = json.load(fp)
        return response

    def test_create_zip(self, submission):
        """Tests the filenames in the created zip are the ones we're expecting"""
        transformer = get_transformer(submission)

        transformer.get_zip(img_seq=itertools.count())
        actual = transformer.image_transformer.zip.get_filenames()

        expected = [
            'EDC_QData/187_0000',
            'EDC_QReceipts/REC0103_0000.DAT',
            'EDC_QImages/Images/S000000000.JPG',
            'EDC_QImages/Images/S000000001.JPG',
            'EDC_QImages/Images/S000000002.JPG',
            'EDC_QImages/Images/S000000003.JPG',
            'EDC_QImages/Images/S000000004.JPG',
            'EDC_QImages/Images/S000000005.JPG',
            'EDC_QImages/Images/S000000006.JPG',
            'EDC_QImages/Images/S000000007.JPG',
            'EDC_QImages/Index/EDC_187_20170301_0000.csv',
            'EDC_QJson/187_0000.json'
        ]
        assert expected == actual
