import arrow
import os
import uuid

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER

__doc__ = """
SDX PDF Transformer.
"""
styles = getSampleStyleSheet()

# Basic text style
style_n = styles["BodyText"]
style_n.alignment = TA_LEFT
style_n.spaceAfter = 25

# Subheading style
style_sh = styles["Heading2"]
style_sh.alignment = TA_LEFT

# Sub-subheading style (questions)
style_ssh = styles["Heading3"]
style_ssh.alignment = TA_LEFT

# Main heading style
style_h = styles['Heading1']
style_h.alignment = TA_CENTER


# Answer Style
style_answer = ParagraphStyle(name='BodyText', parent=styles['Normal'], spaceBefore=6)
style_answer.alignment = TA_LEFT
style_answer.fontName = "Helvetica-Bold"
style_answer.textColor = colors.red
style_answer.fontSize = 15
style_answer.leading = 20
style_answer.spaceAfter = 20

MAX_ANSWER_CHARACTERS_PER_LINE = 35


class PDFTransformer(object):

    def __init__(self, survey, response_data):
        '''
        Sets up variables needed to write out a pdf
        '''
        self.survey = survey
        self.response = response_data

    def render(self):
        """Get the pdf data in memory"""
        return self.render_pages()[0]

    def render_pages(self):
        """Return both the in memory pdf data and a count of the pages"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        doc.build(self.get_elements())

        pdf = buffer.getvalue()

        buffer.close()

        return pdf, doc.page

    def render_to_file(self):
        rndm_name = uuid.uuid4()

        os.makedirs("./tmp/%s" % rndm_name)

        tmp_name = "./tmp/%s/%s.pdf" % (rndm_name, rndm_name)
        doc = SimpleDocTemplate(tmp_name, pagesize=A4)
        doc.build(self.get_elements())

        return os.path.realpath(tmp_name)

    def get_elements(self):

        elements = []
        table_style_data = [('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.black),
                            ('BOX', (0, 0), (-1, -1), 1, colors.black),
                            ('BOX', (0, 0), (0, -1), 1, colors.black),
                            ('BACKGROUND', (0, 0), (1, 0), colors.lightblue)]

        table_style = TableStyle(table_style_data)
        table_style.spaceAfter = 25

        heading_style = TableStyle(table_style_data)
        heading_style.spaceAfter = 25
        heading_style.add('SPAN', (0, 0), (1, 0))
        heading_style.add('ALIGN', (0, 0), (1, 0), 'CENTER')

        localised_date_str = PDFTransformer.get_localised_date(self.response['submitted_at'])

        heading_data = [[Paragraph(self.survey['title'], style_h)]]
        heading_data.append(['Form Type', self.response['collection']['instrument_id']])
        heading_data.append(['Respondent', self.response['metadata']['ru_ref']])
        heading_data.append(['Submitted At', localised_date_str])

        heading = Table(heading_data, style=heading_style, colWidths='*')

        elements.append(heading)

        for question_group in filter(lambda x: 'title' in x, self.survey['question_groups']):

            section_heading = True

            for question in filter(lambda x: 'text' in x, question_group['questions']):
                if question['question_id'] in self.response['data']:
                    try:
                        answer = str(self.response['data'][question['question_id']])
                    except KeyError:
                        answer = ''

                    # Output the section header if we haven't already
                    # Checking here so that whole sections are suppressed
                    # if they have no answers.
                    if section_heading:
                        elements.append(HRFlowable(width="100%"))
                        elements.append(Paragraph(question_group['title'], style_sh))
                        section_heading = False

                    # Question not output if answer is empty
                    text = question.get("text")
                    if not text[0].isdigit():
                        text = " ".join((question.get("number", ""), text))
                    elements.append(Paragraph(text, style_n))
                    elements.append(Paragraph(answer, style_answer))

        return elements

    @staticmethod
    def get_localised_date(date_to_transform, timezone='Europe/London'):
        return arrow.get(date_to_transform).to(timezone).format("DD MMMM YYYY HH:mm:ss")
