import decimal
import logging
from decimal import Decimal, ROUND_HALF_UP

from structlog import wrap_logger

from transform.transformers.cora.cora_formatter import CORAFormatter
from transform.transformers.survey_transformer import SurveyTransformer

logger = wrap_logger(logging.getLogger(__name__))


class UKISTransformer(SurveyTransformer):
    """Perform the transforms and formatting for the UKIS survey."""

    def __init__(self, response, seq_nr=0):
        super().__init__(response, seq_nr)

    def get_qcode(self, qcode, lowercase=False, not_found_value=None):
        """ Return the value of a qcode from the 'data' key of the response.
        :param qcode: The dictionary key to search on
        :param lowercase: Boolean to determine if the value should be lowercased before returned (defaults to False)
        :param not_found_value: What should be returned if the qcode isn't found (defaults to None)
        :returns: The value of the qcode if present in the dictionary.  None otherwise.
        """
        value = self.response['data'].get(qcode, not_found_value)
        if lowercase:
            if isinstance(value, str):
                value = value.lower()
        return value

    def yes_no_question(self, qcode, yes_value="10", no_value="01"):
        """ Handles Yes / No radio questions.  The Yes/No is case-insensitive.
        :param qcode: The qcode to search for form the response
        :param yes_value: What should be returned if the answer value is 'Yes' (defaults to '10')
        :param no_value: What should be returned if the answer value is 'No' (defaults to '01')
        :returns: '10' or '01' (if the return values haven't been modified).  If the answer isn't either 'Yes' or 'No'
        then an empty string is returned.
        """
        answer = self.get_qcode(qcode, lowercase=True)
        if answer:
            if "yes" in answer:
                return yes_value
            elif "no" in answer:
                return no_value
        return ""

    def checkbox_question(self, qcode, catchall=None, dependent_qcodes=None, checked="1", unchecked=""):
        """ Handles checkbox question type.
        :param qcode: The qcode to search for form the response
        :param catchall: An optional code that, if present, will return the unchecked value
        :param dependent_qcodes: A list of qcodes which, if all aren't present, will return None.  Should be used with
        a defined checked and unchecked value as the default unchecked value is also None.
        :param checked: What should be returned if the qcode is present (defaults to '1')
        :param unchecked: What should be returned if the qcode is present (defaults to an empty string)
        :returns: '1' or an empty string (if the return values haven't been modified) whether the qcode value is present.
        """

        if self.get_qcode(catchall):
            return unchecked
        if dependent_qcodes:
            if all(self.get_qcode(code) is None for code in dependent_qcodes):
                return ""

        return checked if self.get_qcode(qcode) is not None else unchecked

    def importance_question(self, qcode):
        """ Handles the importance radio questions.  The answers checked are case-insensitive.
        :param qcode: The qcode to search for form the response
        :returns: '1000', '0100', '0010' , '0001' or an empty string depending on the answer.
        """
        answer = self.get_qcode(qcode, lowercase=True)
        if answer == "high importance":
            return "1000"
        if answer == "medium importance":
            return "0100"
        if answer == "low importance":
            return "0010"
        if answer == "not important":
            return "0001"
        return ""

    def percentage_question(self, qcode):
        """ Handles the percentage radio questions.  The answers checked are case-insensitive.
        :param qcode: The qcode to search for form the response
        :returns: '1000', '0100', '0010' , '0001' or an empty string depending on the answer.
        """
        answer = self.get_qcode(qcode, lowercase=True)
        if answer == "over 90%":
            return "0001"
        if answer == "40-90%":
            return "0010"
        if answer == "less than 40%":
            return "0011"
        if answer == "none":
            return "0100"
        return ""

    @staticmethod
    def round_and_divide_by_one_thousand(value):
        """Rounding is done on a ROUND_HALF_UP basis and values are divided by 1000 for the pck"""
        try:
            # Set the rounding context for Decimal objects to ROUND_HALF_UP
            decimal.getcontext().rounding = ROUND_HALF_UP
            return Decimal(round(Decimal(float(value))) / 1000).quantize(1)

        except TypeError:
            logger.info("Tried to quantize a NoneType object. Returning an empty string")
            return ''

    def business_strategy_and_practices(self):
        """Transforms the 'Business strategy and practices' questions"""
        answers = {
            "2310": self.checkbox_question("2310"),
            "2320": self.checkbox_question("2320"),
            "2330": self.checkbox_question("2330"),
            "2340": self.checkbox_question("2340"),
            "2350": self.checkbox_question("2350"),
            "2360": self.checkbox_question("2360"),
            "2370": self.checkbox_question("2370"),
            "2380": self.checkbox_question("2380")
        }

        return answers

    def innovation_investment(self):
        """Transforms the 'Innovation investment' questions"""
        answers = {
            "1310": self.yes_no_question("1310"),
            "2675": self.checkbox_question("2675"),
            "2676": self.checkbox_question("2676"),
            "2677": self.checkbox_question("2677"),
            "1410": self.round_and_divide_by_one_thousand(self.get_qcode("1410")),
            "1320": self.yes_no_question("1320"),
            "1420": self.round_and_divide_by_one_thousand(self.get_qcode("1420")),
            "1330": self.yes_no_question("1330"),
            "1331": self.checkbox_question("1331"),
            "1332": self.checkbox_question("1332"),
            "1333": self.checkbox_question("1333"),
            "1430": self.round_and_divide_by_one_thousand(self.get_qcode("1430")),
            "1340": self.yes_no_question("1340"),
            "1440": self.round_and_divide_by_one_thousand(self.get_qcode("1440")),
            "1350": self.yes_no_question("1350"),
            "1450": self.round_and_divide_by_one_thousand(self.get_qcode("1450")),
            "1360": self.yes_no_question("1360"),
            "1460": self.round_and_divide_by_one_thousand(self.get_qcode("1460")),
            "1370": self.yes_no_question("1370"),
            "1371": self.checkbox_question("1371"),
            "1372": self.checkbox_question("1372"),
            "1373": self.checkbox_question("1373"),
            "1374": self.checkbox_question("1374"),
            "1470": self.round_and_divide_by_one_thousand(self.get_qcode("1470")),
        }

        return answers

    def goods_and_services_innovation(self):
        """Transforms the 'Goods and services innovation' questions"""
        answers = {
            "0510": self.yes_no_question("0510"),
            "0610": self.checkbox_question("0610"),
            "0620": self.checkbox_question("0620"),
            "0520": self.yes_no_question("0520"),
            "0601": self.checkbox_question("0601"),
            "0602": self.checkbox_question("0602"),
            "0710": self.yes_no_question("0710"),
            "0720": self.yes_no_question("0720"),
        }

        return answers

    def process_innovation(self):
        """Transforms the 'Process innovation' questions"""
        answers = {
            "0900": self.yes_no_question("0900"),
            "1010": self.checkbox_question("1010"),
            "1020": self.checkbox_question("1020"),
        }

        return answers

    def constraints_on_innovation(self):
        """Transforms the 'Process innovation' questions"""
        answers = {
            "1510": self.checkbox_question("1510"),
            "1520": self.checkbox_question("1520"),
            "1530": self.checkbox_question("1530"),
            "1540": self.checkbox_question("1540"),
            "2657": self.importance_question("2657"),
            "2658": self.importance_question("2658"),
            "2659": self.importance_question("2659"),
            "2660": self.importance_question("2660"),
            "2661": self.importance_question("2661"),
            "2662": self.importance_question("2662"),
            "2663": self.importance_question("2663"),
            "2664": self.importance_question("2664"),
            "2665": self.importance_question("2665"),
            "2666": self.importance_question("2666"),
            "2667": self.importance_question("2667"),
            "2678": self.importance_question("2678"),
            "2680": self.importance_question("2680"),
            "2011": self.checkbox_question("2011"),
            "2020": self.checkbox_question("2020"),
            "2030": self.checkbox_question("2030"),
            "2040": self.checkbox_question("2040"),
        }

        return answers

    def factors_affecting_innovation(self):
        """Transforms the 'Process innovation' questions"""
        answers = {
            "1210": self.importance_question("1210"),
            "1211": self.importance_question("1211"),
            "1220": self.importance_question("1220"),
            "1230": self.importance_question("1230"),
            "1240": self.importance_question("1240"),
            "1250": self.importance_question("1250"),
            "1290": self.importance_question("1290"),
            "1260": self.importance_question("1260"),
            "1270": self.importance_question("1270"),
            "1212": self.importance_question("1212"),
            "1213": self.importance_question("1213"),
            "1280": self.importance_question("1280"),
            "1281": self.importance_question("1281"),
        }

        return answers

    def information_needed_for_innovation(self):
        """Transforms the 'Information needed for innovation' questions"""
        answers = {
            "1601": self.importance_question("1601"),
            "1620": self.importance_question("1620"),
            "1632": self.importance_question("1632"),
            "1631": self.importance_question("1631"),
            "1640": self.importance_question("1640"),
            "1650": self.importance_question("1650"),
            "1660": self.importance_question("1660"),
            "1670": self.importance_question("1670"),
            "1680": self.importance_question("1680"),
            "1610": self.importance_question("1610"),
            "1611": self.importance_question("1611"),
            "1690": self.importance_question("1690"),
            "1691": self.importance_question("1691")
        }

        return answers

    def cooperation_on_innovation(self):
        """Transforms the 'Co-operation on innovation' questions"""
        answers = {
            "1811": self.checkbox_question("1811"),
            "1812": self.checkbox_question("1812"),
            "1813": self.checkbox_question("1813"),
            "1814": self.checkbox_question("1814"),
            "1821": self.checkbox_question("1821"),
            "1822": self.checkbox_question("1822"),
            "1823": self.checkbox_question("1823"),
            "1824": self.checkbox_question("1824"),
            "1881": self.checkbox_question("1881"),
            "1882": self.checkbox_question("1882"),
            "1883": self.checkbox_question("1883"),
            "1884": self.checkbox_question("1884"),
            "1891": self.checkbox_question("1891"),
            "1892": self.checkbox_question("1892"),
            "1893": self.checkbox_question("1893"),
            "1894": self.checkbox_question("1894"),
            "1841": self.checkbox_question("1841"),
            "1842": self.checkbox_question("1842"),
            "1843": self.checkbox_question("1843"),
            "1844": self.checkbox_question("1844"),
            "1851": self.checkbox_question("1851"),
            "1852": self.checkbox_question("1852"),
            "1853": self.checkbox_question("1853"),
            "1854": self.checkbox_question("1854"),
            "1861": self.checkbox_question("1861"),
            "1862": self.checkbox_question("1862"),
            "1863": self.checkbox_question("1863"),
            "1864": self.checkbox_question("1864"),
            "1871": self.checkbox_question("1871"),
            "1872": self.checkbox_question("1872"),
            "1873": self.checkbox_question("1873"),
            "1874": self.checkbox_question("1874"),
            "1875": self.checkbox_question("1875"),
            "1876": self.checkbox_question("1876"),
            "1877": self.checkbox_question("1877"),
            "1878": self.checkbox_question("1878"),
            "1879": self.checkbox_question("1879"),
            "1880": self.checkbox_question("1880"),
            "1885": self.checkbox_question("1885"),
            "1886": self.checkbox_question("1886"),
            "2650": self.percentage_question("2650"),
            "2651": self.percentage_question("2651"),
            "2652": self.percentage_question("2652"),
            "2653": self.percentage_question("2653"),
            "2654": self.percentage_question("2654"),
            "2655": self.percentage_question("2655"),
            "2656": self.percentage_question("2656"),
        }

        return answers

    def public_financial_support_for_innovation(self):
        """Transforms the 'Public financial support for innovation' questions"""
        answers = {
            "2668": self.checkbox_question("2668"),
            "2669": self.checkbox_question("2669"),
            "2670": self.checkbox_question("2670"),
            "2671": self.checkbox_question("2671"),
            "2672": self.checkbox_question("2672"),
            "2673": self.checkbox_question("2673"),
            "2679": self.checkbox_question("2679"),
            "2674": self.checkbox_question("2674")
        }

        return answers

    def turnover_and_exports(self):
        """Transforms the 'Public financial support for innovation' questions"""
        answers = {
            "2410": self.round_and_divide_by_one_thousand(self.get_qcode("2410")),
            "2420": self.round_and_divide_by_one_thousand(self.get_qcode("2420")),
            "0810": self.get_qcode("0810", not_found_value=''),
            "0820": self.get_qcode("0820", not_found_value=''),
            "0830": self.get_qcode("0830", not_found_value=''),
            "0840": self.get_qcode("0840", not_found_value=''),
            "2440": self.round_and_divide_by_one_thousand(self.get_qcode("2440")),
        }

        return answers

    def employees_and_skills(self):
        """Transforms the 'Employees and skills' questions"""
        answers = {
            "2510": self.get_qcode("2510", not_found_value=''),
            "2520": self.get_qcode("2520", not_found_value=''),
            "2610": self.get_qcode("2610", not_found_value=''),
            "2620": self.get_qcode("2620", not_found_value=''),
            "2631": self.checkbox_question("2631"),
            "2632": self.checkbox_question("2632"),
            "2633": self.checkbox_question("2633"),
            "2634": self.checkbox_question("2634"),
            "2635": self.checkbox_question("2635"),
            "2636": self.checkbox_question("2636"),
            "2637": self.checkbox_question("2637"),
        }

        return answers

    def transform(self):
        """Perform a transform on survey data."""

        transformed = {
            "0001": '0',
            "0002": '0',
            "0003": '0',
            "2700": "1" if self.get_qcode("2700") else "0",  # 2700 is the additional comments question.
            "2801": self.get_qcode("2801", not_found_value=''),
            "2800": self.get_qcode("2800", not_found_value=''),
            "2900": self.yes_no_question("2900"),
        }

        # general_business_information = self.general_business_information()
        business_strategy_and_practices = self.business_strategy_and_practices()
        innovation_investment = self.innovation_investment()
        goods_and_services_innovation = self.goods_and_services_innovation()
        process_innovation = self.process_innovation()
        constraints_on_innovation = self.constraints_on_innovation()
        factors_affecting_innovation = self.factors_affecting_innovation()
        information_needed_for_innovation = self.information_needed_for_innovation()
        cooperation_on_innovation = self.cooperation_on_innovation()
        public_financial_support_for_innovation = self.public_financial_support_for_innovation()
        turnover_and_exports = self.turnover_and_exports()
        employees_and_skills = self.employees_and_skills()

        logger.info(f"Transforming data for {self.ids.ru_ref}", tx_id=self.ids.tx_id)

        return {**transformed,  # Merge Dictionaries
                **business_strategy_and_practices,
                **innovation_investment, **goods_and_services_innovation,
                **process_innovation, **constraints_on_innovation,
                **factors_affecting_innovation, **information_needed_for_innovation,
                **cooperation_on_innovation, **public_financial_support_for_innovation,
                **turnover_and_exports, **employees_and_skills}

    def _create_pck(self, transformed_data):
        """Return a pck file using provided data"""
        pck = CORAFormatter.get_pck(
            transformed_data,
            self.ids.survey_id,
            self.ids.ru_ref,
            "1",
            self.ids.period,
            "0",
        )
        return pck

    def create_pck(self):
        bound_logger = logger.bind(ru_ref=self.ids.ru_ref, tx_id=self.ids.tx_id)
        bound_logger.info("Transforming data for processing")
        transformed_data = self.transform()
        bound_logger.info("Data successfully transformed")
        pck_name = CORAFormatter.pck_name(self.ids.survey_id, self.ids.tx_id)
        pck = self._create_pck(transformed_data)
        return pck_name, pck
