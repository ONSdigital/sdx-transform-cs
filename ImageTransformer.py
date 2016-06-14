from PDFTransformer import PDFTransformer


class ImageTransformer(object):
    def __init__(self, survey, response_data):
        # We need to generate a pdf first
        pdfTransformer = PDFTransformer(survey, response_data)
        pdfFile = pdfTransformer.render_to_file()