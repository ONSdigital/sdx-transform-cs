from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from io import BytesIO
from textwrap import wrap
import uuid
import os
import arrow

styles = getSampleStyleSheet()
styleN = styles["BodyText"]
styleN.alignment = TA_LEFT

styleH = styles['Heading1']
styleH.alignment = TA_CENTER

MAX_ANSWER_CHARACTERS_PER_LINE = 35


class PDFTransformer(object):
    def __init__(self, survey, response_data):
        '''
        Sets up variables needed to write out a pdf
        '''
        self.survey = survey
        self.response = response_data

    def render(self):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        doc.build(self.get_elements())

        pdf = buffer.getvalue()
        buffer.close()

        return pdf

    def render_to_file(self):
        randomName = uuid.uuid4()

        os.makedirs("./tmp/%s" % randomName)

        tmpName = "./tmp/%s/%s.pdf" % (randomName, randomName)
        doc = SimpleDocTemplate(tmpName, pagesize=A4)
        doc.build(self.get_elements())

        return os.path.realpath(tmpName)

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

        localised_date_str = self.get_localised_date(self.response['submitted_at'])

        heading_data = [[Paragraph(self.survey['title'], styleH)]]
        heading_data.append(['Form Type', self.response['collection']['instrument_id']])
        heading_data.append(['Respondent', self.response['metadata']['ru_ref']])
        heading_data.append(['Submitted At', localised_date_str])

        heading = Table(heading_data, style=heading_style, colWidths='*')

        elements.append(heading)

        for question_group in self.survey['question_groups']:
            table_data = self.get_table_data(question_group)

            if len(table_data) > 0:
                table = Table(table_data, style=table_style, colWidths='*', repeatRows=1)

                elements.append(table)

        return elements

    def get_localised_date(self, date_to_transform, timezone='Europe/London'):
        return arrow.get(date_to_transform).to(timezone).format("DD MMMM YYYY HH:mm:ss")

    def get_table_data(self, question_group):
        table_data = []

        if 'title' in question_group:
            meta = question_group['meta'] if 'meta' in question_group else ''
            table_data.append([question_group['title'], meta])

        for question in question_group['questions']:
            if 'text' in question:
                answer = ''
                if question['question_id'] in self.response['data']:
                    answer = self.response['data'][question['question_id']]

                wrapped_answer = "\n".join(wrap(answer, MAX_ANSWER_CHARACTERS_PER_LINE))

                table_data.append([Paragraph(question['text'], styleN), Paragraph(wrapped_answer, styleN)])

        return table_data
