import logging

from structlog import wrap_logger

from transform.transformers.cora.cora_formatter import CORAFormatter
from transform.transformers.survey_transformer import SurveyTransformer

logger = wrap_logger(logging.getLogger(__name__))


def no_transform(v):
    return v


def yes(v):
    return '1' if v.lower() == "yes" else ''


def yes_no(v):
    return '10' if v.lower() == "yes" else '01'


cb1_dict = {'a': '0001',
            'b': '0010',
            'c': '0011',
            'd': '0100',
            'e': '0101',
            'f': '0110',
            'g': '0111'}


def cb1(v):
    return cb1_dict.get(v) or ''


cb2_dict = {'a': '1000',
            'b': '0100',
            'c': '0010',
            'd': '0001'}


def cb2(v):
    return cb2_dict.get(v) or ''


cb3_dict = {'a': '10000',
            'b': '01000',
            'c': '00100',
            'd': '00010',
            'e': '00001'}


def cb3(v):
    return cb3_dict.get(v) or ''


def pounds_thousands(v):
    # no transformation currently needed!
    return v


def comments(v):
    return '1' if not v == "" else ''


class MESTransformer(SurveyTransformer):
    """Perform the transforms and formatting for the MES survey."""

    instance = '00000'
    page = '1'

    transforms = {
        '1171': no_transform,
        '1203': no_transform,
        '1159': no_transform,
        '1208': cb1,
        '1207': cb1,
        '1174': cb2,
        '1206': yes_no,
        '1001': cb2,
        '1172': cb2,
        '1005': cb2,
        '1211': cb1,
        '1210': cb1,
        '1173': cb2,
        '1175': cb1,
        '1205': cb1,
        '1016': cb2,
        '1020': cb3,
        '1230': cb2,
        '1229': cb2,
        '1176': cb2,
        '1177': cb3,
        '1178': cb2,
        '1179': cb2,
        '1231': cb1,
        '1232': cb1,
        '1233': cb1,
        '1234': cb1,
        '1235': cb2,
        '1236': cb2,
        '1237': cb2,
        '1238': cb2,
        '1180': cb3,
        '1181': cb3,
        '1182': cb3,
        '1183': cb3,
        '1184': cb2,
        '1185': cb2,
        '1186': cb2,
        '1187': cb2,
        '1280': no_transform,
        '1281': no_transform,
        '1282': no_transform,
        '1283': no_transform,
        '1284': no_transform,
        '1285': no_transform,
        '1188': yes_no,
        '1166': cb2,
        '1189': cb2,
        '1170': cb3,
        '1164': no_transform,
        '1165': no_transform,
        '1086': pounds_thousands,
        '1087': pounds_thousands,
        '1191': no_transform,
        '1192': no_transform,
        '1286': yes,
        '1287': yes,
        '1288': yes,
        '1289': yes,
        '1290': yes,
        '1193': no_transform,
        '1194': no_transform,
        '1088': pounds_thousands,
        '1090': pounds_thousands,
        '1092': pounds_thousands,
        '1094': pounds_thousands,
        '1096': pounds_thousands,
        '1089': no_transform,
        '1091': no_transform,
        '1093': no_transform,
        '1095': no_transform,
        '1097': no_transform,
        '1099': pounds_thousands,
        '1100': pounds_thousands,
        '1195': no_transform,
        '1198': no_transform,
        '1291': yes,
        '1292': yes,
        '1293': yes,
        '1294': yes,
        '1295': yes,
        '1296': yes,
        '1297': yes,
        '1298': yes,
        '1299': yes,
        '1300': yes,
        '1301': yes,
        '1302': yes,
        '1303': cb3,
        '1125': pounds_thousands,
        '1126': pounds_thousands,
        '1308': yes,
        '1309': yes,
        '1310': yes,
        '1311': yes,
        '1312': yes,
        '1313': yes,
        '1201': no_transform,
        '1202': no_transform,
        '1114': no_transform,
        '1116': no_transform,
        '1118': no_transform,
        '1120': no_transform,
        '1122': no_transform,
        '1115': no_transform,
        '1117': no_transform,
        '1119': no_transform,
        '1121': no_transform,
        '1123': no_transform,
        '1138': no_transform,
        '1139': no_transform,
        '1140': no_transform,
        '1141': no_transform,
        '1142': no_transform,
        '1143': no_transform,
        '1144': no_transform,
        '1190': yes_no,
        '1149': no_transform,
        '1150': no_transform,
        '1163': comments,
    }

    def __init__(self, response, seq_nr=0):
        super().__init__(response, seq_nr)

    def transform(self):
        result = {}
        for qcode, value in self.response['data'].items():
            if qcode in self.transforms.keys():
                result[qcode] = self.transforms.get(qcode)(value)

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
