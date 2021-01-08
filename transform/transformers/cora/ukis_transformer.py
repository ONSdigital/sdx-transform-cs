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

    def yes_no_question(self, qcode, yes_value="1", no_value=""):
        """ Handles Yes / No radio questions.  The Yes/No is case-insensitive.
        :param qcode: The qcode to search for form the response
        :param yes_value: What should be returned if the answer value is 'Yes' (defaults to '1')
        :param no_value: What should be returned if the answer value is 'No' (defaults to an empty string)
        :returns: '1' or None (if the return values haven't been modified).  If the answer isn't either 'Yes' or 'No'
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
            return "1000"
        if answer == "40-90%":
            return "0100"
        if answer == "less than 40%":
            return "0010"
        if answer == "none":
            return "0001"
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

    # def general_business_information(self):
    #     """Transforms the 'General business information' questions"""
    #     answers = {
    #         "0210": self.checkbox_question("0210"),
    #         "0220": self.checkbox_question("0220"),
    #         "0230": self.checkbox_question("0230"),
    #         "0240": self.checkbox_question("0240"),
    #         "0410": self.checkbox_question("0410"),
    #         "0420": self.checkbox_question("0420"),
    #         "0430": self.checkbox_question("0430"),
    #         "0440": self.checkbox_question("0440"),
    #
    #     }
    #
    #     return answers

    def business_strategy_and_practices(self):
        """Transforms the 'Business strategy and practices' questions"""
        answers = {
            "2310": self.checkbox_question("2310", catchall="d1"),
            "2320": self.checkbox_question("2320", catchall="d1"),
            "2330": self.checkbox_question("2330", catchall="d1"),
            "2340": self.checkbox_question("2340", catchall="d1"),
            "2350": self.checkbox_question("2350", catchall="d1"),
            "2360": self.checkbox_question("2360", catchall="d1"),
            "2370": self.checkbox_question("2370", catchall="d1"),
            "2380": self.checkbox_question("2380")
        }

        return answers

    def innovation_investment(self):
        """Transforms the 'Innovation investment' questions"""
        answers = {
            "1310": self.yes_no_question("1310", yes_value="10", no_value="01"),
            "2675": self.checkbox_question("2675"),
            "2676": self.checkbox_question("2676"),
            "2677": self.checkbox_question("2677"),
            "1410": self.round_and_divide_by_one_thousand(self.get_qcode("1410")),
            "1320": self.yes_no_question("1320", yes_value="10", no_value="01"),
            "1420": self.round_and_divide_by_one_thousand(self.get_qcode("1420")),
            "1330": self.yes_no_question("1330", yes_value="10", no_value="01"),
            "1331": self.checkbox_question("1331"),
            "1332": self.checkbox_question("1332"),
            "1333": self.checkbox_question("1333"),
            "1430": self.round_and_divide_by_one_thousand(self.get_qcode("1430")),
            "1340": self.yes_no_question("1340", yes_value="10", no_value="01"),
            "1440": self.round_and_divide_by_one_thousand(self.get_qcode("1440")),
            "1350": self.yes_no_question("1350", yes_value="10", no_value="01"),
            "1450": self.round_and_divide_by_one_thousand(self.get_qcode("1450")),
            "1360": self.yes_no_question("1360", yes_value="10", no_value="01"),
            "1460": self.round_and_divide_by_one_thousand(self.get_qcode("1460")),
            "1370": self.yes_no_question("1370", yes_value="10", no_value="01"),
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
            "0510": self.yes_no_question("0510", yes_value="10", no_value="01"),
            "0610": self.checkbox_question("0610"),
            "0620": self.checkbox_question("0620"),
            "0520": self.yes_no_question("0520", yes_value="10", no_value="01"),
            "0601": self.checkbox_question("0601"),
            "0602": self.checkbox_question("0602"),
            "0710": self.yes_no_question("0710", yes_value="10", no_value="01"),
            "0720": self.yes_no_question("0720", yes_value="10", no_value="01"),
        }

        return answers

    def process_innovation(self):
        """Transforms the 'Process innovation' questions"""
        answers = {
            "0900": self.yes_no_question("0900", yes_value="10", no_value="01"),
            "1010": self.checkbox_question("1010"),
            "1020": self.checkbox_question("1020"),
        }

        return answers

    def constraints_on_innovation(self):
        """Transforms the 'Process innovation' questions"""
        answers = {
            "1510": self.checkbox_question("1510", catchall="d2"),
            "1520": self.checkbox_question("1520", catchall="d2"),
            "1530": self.checkbox_question("1530", catchall="d2"),
            "1540": self.checkbox_question("1540", catchall="d2"),
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
            "1811": self.checkbox_question("1811", checked="10", unchecked="01", dependent_qcodes=["1811", "1812", "1813", "1814"], catchall="d3"),
            "1812": self.checkbox_question("1812", checked="10", unchecked="01", dependent_qcodes=["1811", "1812", "1813", "1814"], catchall="d3"),
            "1813": self.checkbox_question("1813", checked="10", unchecked="01", dependent_qcodes=["1811", "1812", "1813", "1814"], catchall="d3"),
            "1814": self.checkbox_question("1814", checked="10", unchecked="01", dependent_qcodes=["1811", "1812", "1813", "1814"], catchall="d3"),
            "1821": self.checkbox_question("1821", checked="10", unchecked="01", dependent_qcodes=["1821", "1822", "1823", "1824"], catchall="d4"),
            "1822": self.checkbox_question("1822", checked="10", unchecked="01", dependent_qcodes=["1821", "1822", "1823", "1824"], catchall="d4"),
            "1823": self.checkbox_question("1823", checked="10", unchecked="01", dependent_qcodes=["1821", "1822", "1823", "1824"], catchall="d4"),
            "1824": self.checkbox_question("1824", checked="10", unchecked="01", dependent_qcodes=["1821", "1822", "1823", "1824"], catchall="d4"),
            "1881": self.checkbox_question("1881", checked="10", unchecked="01", dependent_qcodes=["1881", "1882", "1883", "1884"], catchall="d5"),
            "1882": self.checkbox_question("1882", checked="10", unchecked="01", dependent_qcodes=["1881", "1882", "1883", "1884"], catchall="d5"),
            "1883": self.checkbox_question("1883", checked="10", unchecked="01", dependent_qcodes=["1881", "1882", "1883", "1884"], catchall="d5"),
            "1884": self.checkbox_question("1884", checked="10", unchecked="01", dependent_qcodes=["1881", "1882", "1883", "1884"], catchall="d5"),
            "1891": self.checkbox_question("1891", checked="10", unchecked="01", dependent_qcodes=["1891", "1892", "1893", "1894"], catchall="d6"),
            "1892": self.checkbox_question("1892", checked="10", unchecked="01", dependent_qcodes=["1891", "1892", "1893", "1894"], catchall="d6"),
            "1893": self.checkbox_question("1893", checked="10", unchecked="01", dependent_qcodes=["1891", "1892", "1893", "1894"], catchall="d6"),
            "1894": self.checkbox_question("1894", checked="10", unchecked="01", dependent_qcodes=["1891", "1892", "1893", "1894"], catchall="d6"),
            "1841": self.checkbox_question("1841", checked="10", unchecked="01", dependent_qcodes=["1841", "1842", "1843", "1844"], catchall="d7"),
            "1842": self.checkbox_question("1842", checked="10", unchecked="01", dependent_qcodes=["1841", "1842", "1843", "1844"], catchall="d7"),
            "1843": self.checkbox_question("1843", checked="10", unchecked="01", dependent_qcodes=["1841", "1842", "1843", "1844"], catchall="d7"),
            "1844": self.checkbox_question("1844", checked="10", unchecked="01", dependent_qcodes=["1841", "1842", "1843", "1844"], catchall="d7"),
            "1851": self.checkbox_question("1851", checked="10", unchecked="01", dependent_qcodes=["1851", "1852", "1853", "1854"], catchall="d8"),
            "1852": self.checkbox_question("1852", checked="10", unchecked="01", dependent_qcodes=["1851", "1852", "1853", "1854"], catchall="d8"),
            "1853": self.checkbox_question("1853", checked="10", unchecked="01", dependent_qcodes=["1851", "1852", "1853", "1854"], catchall="d8"),
            "1854": self.checkbox_question("1854", checked="10", unchecked="01", dependent_qcodes=["1851", "1852", "1853", "1854"], catchall="d8"),
            "1861": self.checkbox_question("1861", checked="10", unchecked="01", dependent_qcodes=["1861", "1862", "1863", "1864"], catchall="d9"),
            "1862": self.checkbox_question("1862", checked="10", unchecked="01", dependent_qcodes=["1861", "1862", "1863", "1864"], catchall="d9"),
            "1863": self.checkbox_question("1863", checked="10", unchecked="01", dependent_qcodes=["1861", "1862", "1863", "1864"], catchall="d9"),
            "1864": self.checkbox_question("1864", checked="10", unchecked="01", dependent_qcodes=["1861", "1862", "1863", "1864"], catchall="d9"),
            "1871": self.checkbox_question("1871", checked="10", unchecked="01", dependent_qcodes=["1871", "1872", "1873", "1874"], catchall="d10"),
            "1872": self.checkbox_question("1872", checked="10", unchecked="01", dependent_qcodes=["1871", "1872", "1873", "1874"], catchall="d10"),
            "1873": self.checkbox_question("1873", checked="10", unchecked="01", dependent_qcodes=["1871", "1872", "1873", "1874"], catchall="d10"),
            "1874": self.checkbox_question("1874", checked="10", unchecked="01", dependent_qcodes=["1871", "1872", "1873", "1874"], catchall="d10"),
            "1875": self.checkbox_question("1875", checked="10", unchecked="01", dependent_qcodes=["1875", "1876", "1877", "1878"], catchall="d11"),
            "1876": self.checkbox_question("1876", checked="10", unchecked="01", dependent_qcodes=["1875", "1876", "1877", "1878"], catchall="d11"),
            "1877": self.checkbox_question("1877", checked="10", unchecked="01", dependent_qcodes=["1875", "1876", "1877", "1878"], catchall="d11"),
            "1878": self.checkbox_question("1878", checked="10", unchecked="01", dependent_qcodes=["1875", "1876", "1877", "1878"], catchall="d11"),
            "1879": self.checkbox_question("1879", checked="10", unchecked="01", dependent_qcodes=["1879", "1880", "1885", "1886"], catchall="d12"),
            "1880": self.checkbox_question("1880", checked="10", unchecked="01", dependent_qcodes=["1879", "1880", "1885", "1886"], catchall="d12"),
            "1885": self.checkbox_question("1885", checked="10", unchecked="01", dependent_qcodes=["1879", "1880", "1885", "1886"], catchall="d12"),
            "1886": self.checkbox_question("1886", checked="10", unchecked="01", dependent_qcodes=["1879", "1880", "1885", "1886"], catchall="d12"),
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
            "2674": self.checkbox_question("2674"),
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
            "2900": self.yes_no_question("2900", yes_value="10", no_value="01"),
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
