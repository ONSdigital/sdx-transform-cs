from decimal import Decimal
import json
import logging
import os

from structlog import wrap_logger

from transform.settings import (
    SDX_FTP_DATA_PATH,
    SDX_FTP_IMAGE_PATH,
    SDX_FTP_RECEIPT_PATH,
    SDX_RESPONSE_JSON_PATH,
)
from transform.transformers.cord.cord_formatter import CORDFormatter
from transform.transformers.survey import Survey
from transform.transformers.image_transformer import ImageTransformer
from transform.utilities.general import merge_dicts

logger = wrap_logger(logging.getLogger(__name__))


class EcommerceTransformer:
    """Perform the transforms and formatting for the MBS survey."""

    def __init__(self, response, seq_nr=0):

        self.response = response
        self.ids = Survey.identifiers(self.response, seq_nr=seq_nr, log=logger)

        survey_file = "./transform/surveys/{}.{}.json".format(
            self.ids.survey_id, self.ids.inst_id
        )

        with open(survey_file) as fp:
            logger.info("Loading {}".format(survey_file))
            self.survey = json.load(fp)

        self.image_transformer = ImageTransformer(
            logger,
            self.survey,
            self.response,
            sequence_no=self.ids.seq_nr,
            base_image_path=SDX_FTP_IMAGE_PATH,
        )

    def get_qcode(self, qcode):
        """ Return the value of a qcode, or if it isn't present, then return None
        """
        return self.response['data'].get(qcode, None)

    def yes_no_question(self, qcode):
        """ Handles optional Yes / No radio questions
        Gets the question value from the submission via qcode
        Returns '10' if value is "Yes", '01' if value is 'No' and '0' otherwise
        """
        value = self.get_qcode(qcode)
        return "10" if value == "Yes" else "01" if value == "No" else "0"

    def checkbox_question(self, qcode, dependant_qcode=None):
        """ Handles checkbox question type
        Returns a checked or unchecked value depending on whether the answer is present.
        Defaults to unchecked value.
        If qcode '010' is 'No' then it returns '0' as it's impossible to get to this question when that is true.
        If the dependant_qcode is 'No' then it returns '0' also as it wasn't possible to get to this question (which is
        different to it not being there because it was unchecked)
        """
        if self.get_qcode("010") == "No" or self.get_qcode(dependant_qcode) == "No":
            return "0"
        return "10" if self.get_qcode(qcode) is not None else "01"

    @staticmethod
    def convert_percentage(percentage):
        """ Converts a percentage with possible decimal places into a 0 padded string of length 4. The final string should
        represent 1 decimal place. All inputs will be rounded to 1 decimal place.

            e.g. 10 -> 0100, 0.1 -> 0001, 23.4 -> 0234, 29.949 -> 0299, 29.950 -> 0300

        """
        value = Decimal(percentage) * 10
        value = round(value)
        value = str(value).replace(".", "")
        return value.rjust(4, "0")

    def percentage_question(self, qcode):
        """
        Percentage type question. Will transform to a four digit answer
        If answer does not exist in submission, output will be '0'
        """
        value = self.get_qcode(qcode)

        if not value:
            return "0"

        return self.convert_percentage(value)

    def negative_playback_question(self, q_code, playback_q_code):
        """
        Transform a question that has its answer changed by the result of a negative playback page.
        :param q_code: The q_code of the question being transformed
        :param playback_q_code: The code from the negative playback page that affects the result of the q_code passed in.
        The regex form of this code would typically be 'd[0-9]+'.
        :returns: "10" if the q_code value in the response data has a true value.  "01" if the q_code response value is false
        BUT the playback_q_code response value is 'They're not used' or 'They weren’t experienced'.  Otherwise "0".

        Examples:
        self.response = {"123": "words", "d1": "They’re not used"}
        negative_playback_question("123", "d1") # "10"

        self.response = {"123": "words", "d1": "I don’t know what they are"}
        negative_playback_question("124", "d1") # "0"

        self.response = {"123": "words", "d1": "They’re not used"}
        negative_playback_question("124", "d1") # "01"

        self.response = {"123": "words", "d1": "They weren’t experienced"}
        negative_playback_question("123", "d1") # "10"
        """
        change_responses = ["They’re not used", "They weren’t experienced"]

        if self.get_qcode(q_code):
            return "10"
        if self.get_qcode(playback_q_code) in change_responses:
            return "01"

        return "0"

    def radio_question_option(self, qcode, answer_value, checked="1", unchecked="0"):
        """
        Since runner uses 1 qcode for all options, we need to seperate each answer option into a different qcode.
        qcode: The qcode for the radio question
        answer_value: The value of this answer option
        """
        qcode_value = self.get_qcode(qcode)

        # If the code isn't there, then default to '0' as we never got the chance to answer the question
        if not qcode_value:
            return "0"

        if qcode_value == answer_value:
            return checked

        return unchecked

    def use_of_computers(self):
        """
        Transform the 'Use of computers section'
        """
        answers = {
            "010": self.yes_no_question("010"),
            "023": self.percentage_question("023")
        }

        return answers

    def ict_specialists_and_skills(self):
        """Transforms the 'ICT specialists and skills' questions"""
        answers = {
            "154": self.yes_no_question("154"),
            "155": self.yes_no_question("155"),
            "156": self.yes_no_question("156"),
            "165": self.checkbox_question("165"),
            "316": self.checkbox_question("316"),
        }

        return answers

    def access_and_use_of_internet(self):
        """
        Transforms the 'Access and use of internet' questions

        Note: There are negative playback codes that are in the form 'd[0-9]+'.  Each of these affects a set of questions
        which are listed below
        d1 - Which features does the business' site have? - 147, 202, 203, 205, 332 and 414
        d2 - Which social media does <company> use for purposes other than posting paid averts? - 386, 387, 388, 389
        d3 - How does the business use social media? - 341, 342, 343, 344, 345, 346
        """
        answers = {
            "022": self.percentage_question("022"),
            "038": self.yes_no_question("038"),
            "080": self.yes_no_question("080"),
            "277": self.radio_question_option("r1", "Less than 2Mbps"),
            "278": self.radio_question_option("r1", "2Mbps or more, but less than 10Mbps"),
            "279": self.radio_question_option("r1", "10Mbps or more, but less than 30Mbps"),
            "280": self.radio_question_option("r1", "30Mbps or more, but less than 100Mbps"),
            "281": self.radio_question_option("r1", "100Mbps or more"),
            "320": self.percentage_question("320"),
            "356": self.yes_no_question("356"),
            "453": self.yes_no_question("453"),

            "147": self.negative_playback_question("147", "d1"),
            "202": self.negative_playback_question("202", "d1"),
            "203": self.negative_playback_question("203", "d1"),
            "205": self.negative_playback_question("205", "d1"),
            "332": self.negative_playback_question("332", "d1"),
            "414": self.negative_playback_question("414", "d1"),

            "386": self.negative_playback_question("386", "d2"),
            "387": self.negative_playback_question("387", "d2"),
            "388": self.negative_playback_question("388", "d2"),
            "389": self.negative_playback_question("389", "d2"),

            "341": self.negative_playback_question("341", "d3"),
            "342": self.negative_playback_question("342", "d3"),
            "343": self.negative_playback_question("343", "d3"),
            "344": self.negative_playback_question("344", "d3"),
            "345": self.negative_playback_question("345", "d3"),
            "346": self.negative_playback_question("346", "d3"),
        }

        return answers

    def sharing_of_info_electronically_within_business(self):
        """Transforms the 'Sharing of info electronically within the business' questions"""
        answers = {
            "190": self.yes_no_question("190"),
            "191": self.yes_no_question("191"),
            "197": self.yes_no_question("197")
        }
        return answers

    def ict_security(self):
        """
        Transforms the 'ICT Security' questions

        Note: There are negative playback codes that are in the form 'd[0-9]+'.  Each of these affects a set of questions
        which are listed below
        d4 - Which ICT security measures does <company> use? - 272, 482, 483, 484 and 485
        d5 - Which ICT security procedures does the business use? - 274, 275, 481, 486 and 487

        """
        answers = {
            "272": self.negative_playback_question("272", "d4"),
            "482": self.negative_playback_question("482", "d4"),
            "483": self.negative_playback_question("483", "d4"),
            "484": self.negative_playback_question("484", "d4"),
            "485": self.negative_playback_question("485", "d4"),

            "274": self.negative_playback_question("274", "d5"),
            "275": self.negative_playback_question("275", "d5"),
            "481": self.negative_playback_question("481", "d5"),
            "486": self.negative_playback_question("486", "d5"),
            "487": self.negative_playback_question("487", "d5"),

            "265": self.yes_no_question("265"),
            "266": self.yes_no_question("266"),
            "267": self.yes_no_question("267"),

            "415": self.radio_question_option("r3", "Within the last 12 months", checked="10", unchecked="01"),
            "416": self.radio_question_option("r3", "More than 12 months and up to 24 months ago", checked="10", unchecked="01"),
            "417": self.radio_question_option("r3", "More than 24 months ago", checked="10", unchecked="01"),
            "488": self.checkbox_question("488"),
            "489": self.checkbox_question("489"),
            "490": self.yes_no_question("490"),
            "491": self.yes_no_question("491"),
            "492": self.yes_no_question("492"),
            "493": self.yes_no_question("493"),
            "494": self.yes_no_question("494"),
        }
        return answers

    def e_commerce(self):
        """
        Transform the 'Ecommerce' questions

        Note: There are negative playback codes that are in the form 'd[0-9]+'.  Each of these affects a set of questions
        which are listed below
        d6 - During 2018, did the business experience any of the following difficulties
        when selling to other EU countries via a website or 'app'? - 462, 463, 464, 465 and 466

        """
        answers = {
            "234": self.yes_no_question("234"),
            "235": self.percentage_question("235"),
            "257": self.yes_no_question("257"),
            "258": self.percentage_question("258"),
            "310": self.checkbox_question("310", dependant_qcode="234"),
            "311": self.checkbox_question("311", dependant_qcode="234"),
            "312": self.checkbox_question("312", dependant_qcode="234"),
            "313": self.checkbox_question("313", dependant_qcode="257"),
            "314": self.checkbox_question("314", dependant_qcode="257"),
            "315": self.checkbox_question("315", dependant_qcode="257"),
            "348": self.percentage_question("348"),
            "349": self.percentage_question("349"),
            "458": self.checkbox_question("458", dependant_qcode="234"),
            "459": self.checkbox_question("459", dependant_qcode="234"),
            "460": self.percentage_question("460"),
            "461": self.percentage_question("461"),
            "462": self.negative_playback_question("462", "d6"),
            "463": self.negative_playback_question("463", "d6"),
            "464": self.negative_playback_question("464", "d6"),
            "465": self.negative_playback_question("465", "d6"),
            "466": self.negative_playback_question("466", "d6"),
        }

        return answers

    def transform(self):
        """Perform a transform on survey data."""

        # 001 is the 'has anything changed' question that doesn't appear in eq.
        transformed = {
            "001": "0",
            "500": "1" if self.get_qcode("500") else "0",
        }

        use_of_computers = self.use_of_computers()
        ict_specialists_and_skills = self.ict_specialists_and_skills()
        access_and_use_of_internet = self.access_and_use_of_internet()
        sharing_of_info_electronically_within_business = self.sharing_of_info_electronically_within_business()
        ict_security = self.ict_security()
        e_commerce = self.e_commerce()

        logger.info("Transforming data for {}".format(self.ids.ru_ref), tx_id=self.ids.tx_id,)

        sections_to_transform = [
            transformed, ict_specialists_and_skills, access_and_use_of_internet,
            sharing_of_info_electronically_within_business, ict_security, e_commerce,
            use_of_computers
        ]

        return merge_dicts(*sections_to_transform)

    def create_pck(self, transformed_data):
        """Return a pck file using provided data"""
        pck = CORDFormatter.get_pck(
            transformed_data,
            self.ids.survey_id,
            self.ids.ru_ref,
            self.ids.period,
        )
        return pck

    def create_idbr_receipt(self):
        """Return a idbr receipt file"""
        idbr = CORDFormatter.get_idbr(
            self.ids.survey_id,
            self.ids.ru_ref,
            self.ids.ru_check,
            self.ids.period,
        )
        return idbr

    def create_image_files(self, img_seq=None):
        """Creates image files and adds it to in-memory zip file"""
        self.image_transformer.get_zipped_images(img_seq)

    def create_zip(self, img_seq=None):
        """Perform transformation on the survey data
        and pack the output into a zip file exposed by the image transformer
        """
        bound_logger = logger.bind(ru_ref=self.ids.ru_ref, tx_id=self.ids.tx_id)
        bound_logger.info("Transforming data for processing")
        transformed_data = self.transform()
        bound_logger.info("Data successfully transformed")

        bound_logger.info("Creating PCK")
        pck_name = CORDFormatter.pck_name(self.ids.survey_id, self.ids.seq_nr)
        pck = self.create_pck(transformed_data)
        self.image_transformer.zip.append(os.path.join(SDX_FTP_DATA_PATH, pck_name), pck)
        bound_logger.info("Successfully created PCK")

        bound_logger.info("Creating IDBR receipt")
        idbr_name = CORDFormatter.idbr_name(self.ids.user_ts, self.ids.seq_nr)
        idbr = self.create_idbr_receipt()
        self.image_transformer.zip.append(os.path.join(SDX_FTP_RECEIPT_PATH, idbr_name), idbr)
        bound_logger.info("Successfully created IDBR receipt")

        bound_logger.info("Creating image files")
        self.create_image_files(img_seq)
        bound_logger.info("Successfully created image files")

        bound_logger.info("Adding json response to zip")
        response_json_name = CORDFormatter.response_json_name(self.ids.survey_id, self.ids.seq_nr)
        self.image_transformer.zip.append(os.path.join(SDX_RESPONSE_JSON_PATH, response_json_name), json.dumps(self.response))
        bound_logger.info("Sucessfully added json response to zip")
