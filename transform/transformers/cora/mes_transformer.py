import logging

from structlog import wrap_logger

from transform.transformers.cora.cora_formatter import CORAFormatter
from transform.transformers.survey_transformer import SurveyTransformer

logger = wrap_logger(logging.getLogger(__name__))

transforms = {
    '1171': 'None',
    '1203': 'None',
    '1159': 'None',
    '1208': {'None': '0001', 'Fewer than 20%': '0010', '20 to 49%': '0011', '50 to 80%': '0100',
             'More than 80%': '0101', 'All': '0110'},
    '1207': {'None': '0001', 'Fewer than 20%': '0010', '20 to 49%': '0011', '50 to 80%': '0100',
             'More than 80%': '0101', 'All': '0110'},
    '1174': {'The owner founded it': '1000', 'A relative of the founder owned it': '0100',
             'A family not related to the founder owned it': '0010', 'Not a family-owned business': '0001'},
    '1206': {'Yes': '10', 'No': '01'},
    '1001': {'We resolved the problems but did not take further action': '1000',
             'We resolved the problems and took action to try to ensure they do not happen again': '0100',
             'We resolved the problems and had a continuous improvement process to anticipate similar problems in advance': '0010',
             'No action was taken': '0001'},
    '1172': {'We resolve the problems but do not take further action': '1000',
             'We resolve the problems and take action to try to ensure they do not happen again': '0100',
             'We resolve the problems and have a continuous improvement process to anticipate similar problems in advance': '0010',
             'No action is taken': '0001'},
    '1005': {'1-2 key performance indicators': '1000', '3-9 key performance indicators': '0100',
             '10 or more key performance indicators': '0010', 'No key performance indicators': '0001'},
    '1211': {'Annually': '0001', 'Quarterly': '0010', 'Monthly': '0011', 'Weekly': '0100', 'Daily': '0101',
             'Hourly or more frequently': '0110', 'Never': '0111'},
    '1210': {'Annually': '0001', 'Quarterly': '0010', 'Monthly': '0011', 'Weekly': '0100', 'Daily': '0101',
             'Hourly or more frequently': '0110', 'Never': '0111'},
    '1173': {'1-2 key performance indicators': '1000', '3-9 key performance indicators': '0100',
             '10 or more key performance indicators': '0010', 'No key performance indicators': '0001'},
    '1175': {'Annually': '0001', 'Quarterly': '0010', 'Monthly': '0011', 'Weekly': '0100', 'Daily': '0101',
             'Hourly or more frequently': '0110', 'Never': '0111'},
    '1205': {'Annually': '0001', 'Quarterly': '0010', 'Monthly': '0011', 'Weekly': '0100', 'Daily': '0101',
             'Hourly or more frequently': '0110', 'Never': '0111'},
    '1016': {'Main timeframe was less than one year': '1000', 'Main timeframe was one year or more': '0100',
             'Combination of timeframes of less than and more than a year': '0010', 'There were no targets': '0001'},
    '1020': {'Very easy': '10000', 'Quite easy': '01000', 'Neither easy nor difficult': '00100',
             'Quite difficult': '00010', 'Very difficult': '00001'},
    '1230': {'All': '1000', 'Most': '0100', 'Some': '0010', 'None': '0001'},
    '1229': {'All': '1000', 'Most': '0100', 'Some': '0010', 'None': '0001'},
    '1176': {'Main timeframe is less than one year': '1000', 'Main timeframe is one year or more': '0100',
             'Combination of timeframes of less than and more than a year': '0010', 'There are no targets': '0001'},
    '1177': {'Very easy': '10000', 'Quite easy': '01000', 'Neither easy nor difficult': '00100',
             'Quite difficult': '00010', 'Very difficult': '00001'},
    '1178': {'All': '1000', 'Most': '0100', 'Some': '0010', 'None': '0001'},
    '1179': {'All': '1000', 'Most': '0100', 'Some': '0010', 'None': '0001'},
    '1231': {'Their own performance as measured by targets': '0001',
             "Their team's or shift's performance as measured by targets": '0010',
             "Their site's performance as measured by targets": '0011',
             "The business's performance as measured by targets": '0100',
             'Performance bonuses were not related to targets': '0101', 'No performance bonuses': '0110'},
    '1232': {'Their own performance as measured by targets': '0001',
             "Their team's or shift's performance as measured by targets": '0010',
             "Their site's performance as measured by targets": '0011',
             "The business's performance as measured by targets": '0100',
             'Performance bonuses were not related to targets': '0101', 'There are no performance bonuses': '0110'},
    '1233': {'Their own performance as measured by targets': '0001',
             "Their team's or shift's performance as measured by targets": '0010',
             "Their site's performance as measured by targets": '0011',
             "The business's performance as measured by targets": '0100',
             'Performance bonuses were not related to targets': '0101', 'There were no performance bonuses': '0110'},
    '1234': {'Their own performance as measured by targets': '0001',
             "Their team's or shift's performance as measured by targets": '0010',
             "Their site's performance as measured by targets": '0011',
             "The business's performance as measured by targets": '0100',
             'Performance bonuses were not related to targets': '0101', 'There are no performance bonuses': '0110'},
    '1235': {'Based solely on performance or ability': '1000',
             'Based partly on performance or ability, and partly on other factors': '0100',
             'Based mainly on factors other than performance or ability': '0010', 'No managers were promoted': '0001'},
    '1236': {'Based solely on performance or ability': '1000',
             'Based partly on performance or ability, and partly on other factors': '0100',
             'Based mainly on factors other than performance or ability': '0010', 'No managers are promoted': '0001'},
    '1237': {'Based solely on performance or ability': '1000',
             'Based partly on performance or ability, and partly on other factors': '0100',
             'Based mainly on factors other than performance or ability': '0010',
             'No non-managers were promoted': '0001'},
    '1238': {'Based solely on performance or ability': '1000',
             'Based partly on performance or ability, and partly on other factors': '0100',
             'Based mainly on factors other than performance or ability': '0010',
             'No non-managers are promoted': '0001'},
    '1180': {'Less than a day': '10000', '1 day': '01000', '2 to 4 days': '00100', '5 to 10 days': '00010',
             'More than 10 days': '00001'},
    '1181': {'Less than a day': '10000', '1 day': '01000', '2 to 4 days': '00100', '5 to 10 days': '00010',
             'More than 10 days': '00001'},
    '1182': {'Less than a day': '10000', '1 day': '01000', '2 to 4 days': '00100', '5 to 10 days': '00010',
             'More than 10 days': '00001'},
    '1183': {'Less than a day': '10000', '1 day': '01000', '2 to 4 days': '00100', '5 to 10 days': '00010',
             'More than 10 days': '00001'},
    '1184': {'Within 6 months of identifying under-performance': '1000',
             'After 6 months of identifying under-performance': '0100',
             'No action was taken to address under-performance': '0010',
             'There was no under-performance': '0001'},
    '1185': {'Within 6 months of identifying under-performance': '1000',
             'After 6 months of identifying under-performance': '0100',
             'No action was taken to address under-performance': '0010',
             'There was no under-performance': '0001'},
    '1186': {'Within 6 months of identifying under-performance': '1000',
             'After 6 months of identifying under-performance': '0100',
             'No action was taken to address under-performance': '0010',
             'There was no under-performance': '0001'},
    '1187': {'Within 6 months of identifying under-performance': '1000',
             'After 6 months of identifying under-performance': '0100',
             'No action was taken to address under-performance': '0010',
             'There was no under-performance': '0001'},
    '1280': 'None',
    '1281': 'None',
    '1282': 'None',
    '1283': 'None',
    '1284': 'None',
    '1285': 'None',
    '1188': {'Yes': '10', 'No': '01'},
    '1166': {'Only at individual sites': '1000', 'Only at headquarters': '0100',
             'Both at individual sites and at headquarters': '0010',
             'Other': '0001'},
    '1189': {'Only at individual sites': '1000', 'Only at headquarters': '0100',
             'Both at individual sites and at headquarters': '0010', 'Other': '0001'},
    '1170': {'Under £1000': '10000', '£1000 to £9999': '01000', '£10,000 to £99,999': '00100',
             '£100,000 to £999,999': '00010', '£1 million or more': '00001'},
    '1164': 'None',
    '1165': 'None',
    '1086': 'None',
    '1087': 'None',
    '1191': 'None',
    '1192': 'None',
    '1286': {'Turnover in 2020 is higher than expected': '1'},
    '1287': {'Turnover in 2020 is lower than expected': '1'},
    '1288': {
        'Turnover derived from some types of product or activities is higher than expected while others lower than expected': '1'},
    '1289': {'Turnover derived from types of product or service not expected at the start of 2020': '1'},
    '1290': {'Turnover in 2020 is as expected': '1'}, '1193': 'None', '1194': 'None', '1088': {'': "£'000"},
    '1090': 'None',
    '1092': 'None',
    '1094': 'None',
    '1096': 'None',
    '1089': 'None',
    '1091': 'None',
    '1093': 'None',
    '1095': 'None',
    '1097': 'None',
    '1099': 'None',
    '1100': 'None',
    '1195': 'None',
    '1198': 'None',
    '1291': {'We used some new domestic suppliers': '1'},
    '1292': {'We stopped using some domestic suppliers': '1'},
    '1293': {'We used some new international suppliers': '1'},
    '1294': {'We stopped using some international suppliers': '1'},
    '1295': {'We did not change our suppliers': '1'},
    '1296': {'Previous suppliers were operational, but unable to fulfil our requirements': '1'},
    '1297': {'Logistical problems with previous suppliers': '1'},
    '1298': {'Previous suppliers were temporarily closed or out of business': '1'},
    '1299': {'New suppliers were more price competitive': '1'},
    '1300': {'New suppliers offered superior products or service': '1'},
    '1301': {'Product requirements changed': '1'},
    '1302': {'Other': '1'},
    '1303': {'Large positive impacts': '10000',
             'Small positive impacts': '01000',
             'Minimal or no impacts': '00100',
             'Small negative impacts': '00010',
             'Large negative impacts': '00001'},
    '1125': 'None',
    '1126': 'None',
    '1308': {'Capital expenditure in 2020 is higher than expected': '1'},
    '1309': {'Capital expenditure in 2020 is lower than expected': '1'},
    '1310': {'Expenditure on some types of capital increased while others decreased': '1'},
    '1311': {'Capital expenditure projects cancelled': '1'},
    '1312': {'Capital expenditure in types and activities new to the business': '1'},
    '1313': {'Capital expenditure did not change': '1'},
    '1201': 'None',
    '1202': 'None',
    '1114': 'None',
    '1116': 'None',
    '1118': 'None',
    '1120': 'None',
    '1122': 'None',
    '1115': 'None',
    '1117': 'None',
    '1119': 'None',
    '1121': 'None',
    '1123': 'None',
    '1138': 'None',
    '1139': 'None',
    '1140': 'None',
    '1141': 'None',
    '1142': 'None',
    '1143': 'None',
    '1144': 'None',
    '1190': {'Yes, I would like to receive feedback': '10', 'No, I would prefer not to receive feedback': '01'},
    '1149': 'None',
    '1150': 'None',
    '1163': {'': '1'}
}


class MESTransformer(SurveyTransformer):
    """Perform the transforms and formatting for the MES survey."""

    instance = '00000'
    page = '1'

    def __init__(self, response, seq_nr=0):
        super().__init__(response, seq_nr)

    def transform(self):
        result = {}
        for q_code, tran in transforms.items():
            value = self.response['data'].get(q_code)
            if value is None:
                t = ''
            else:
                if tran == 'None':
                    t = value
                else:
                    t = tran.get(value) or ''

            result[q_code] = t

        return result

    def _create_pck(self, transformed_data):
        """Return a pck file using provided data"""
        pck = CORAFormatter.get_pck(
            transformed_data,
            self.ids.survey_id,
            self.ids.ru_ref,
            self.page,
            self.ids.period,
            self.instance,
        )
        return pck

    def create_pck(self):
        bound_logger = logger.bind(ru_ref=self.ids.ru_ref, tx_id=self.ids.tx_id)
        bound_logger.info("Transforming data for processing")
        transformed_data = self.transform()
        bound_logger.info("Data successfully transformed")
        pck_name = CORAFormatter.pck_name(self.ids.survey_id, self.ids.seq_nr)
        pck = self._create_pck(transformed_data)
        return pck_name, pck
