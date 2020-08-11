
from transform.transformers.common_software import MBSTransformer, MWSSTransformer, CSTransformer
from transform.transformers.cora import UKISTransformer
from transform.transformers.cord import Ecommerce2019Transformer, EcommerceTransformer


def get_transformer(response, sequence_no=1000):
    survey_id = response['survey_id']

    # CORA
    if survey_id == "144":
        transformer = UKISTransformer(response, sequence_no)

    # CORD
    elif survey_id == "187":
        if response['collection']['instrument_id'] in ['0001', '0002']:
            transformer = Ecommerce2019Transformer(response, sequence_no)
        else:
            transformer = EcommerceTransformer(response, sequence_no)

    # COMMON SOFTWARE
    elif survey_id == "009":
        transformer = MBSTransformer(response, sequence_no)
    elif survey_id == "134":
        transformer = MWSSTransformer(response, sequence_no)
    else:
        transformer = CSTransformer(response, sequence_no)

    return transformer
