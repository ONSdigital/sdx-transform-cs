#!/usr/bin/env python
#   coding: UTF-8

import argparse
from io import BytesIO
import json
import os
import sys
import uuid

import arrow
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.enums import TA_LEFT, TA_CENTER

__doc__ = """
SDX PDF Transformer.

Example:

python transform/transformers/PDFTransformer.py --survey transform/surveys/144.0001.json \\
< tests/replies/ukis-01.json > output.pdf

"""

styles = getSampleStyleSheet()

# Basic text style
styleN = styles["BodyText"]
styleN.alignment = TA_LEFT
styleN.spaceAfter = 25

# Subheading style
styleSH = styles["Heading2"]
styleSH.alignment = TA_LEFT

# Sub-subheading style (questions)
styleSSH = styles["Heading3"]
styleSSH.alignment = TA_LEFT

# Main heading style
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
        doc.build(self.get_elements(self.survey, self.response))

        pdf = buffer.getvalue()
        buffer.close()

        return pdf

    def render_to_file(self):
        randomName = uuid.uuid4()

        os.makedirs("./tmp/%s" % randomName)

        tmpName = "./tmp/%s/%s.pdf" % (randomName, randomName)
        doc = SimpleDocTemplate(tmpName, pagesize=A4)
        doc.build(self.get_elements(self.survey, self.response))

        return os.path.realpath(tmpName)

    @staticmethod
    def get_elements(survey, response):

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

        localised_date_str = PDFTransformer.get_localised_date(response['submitted_at'])

        heading_data = [[Paragraph(survey['title'], styleH)]]
        heading_data.append(['Form Type', response['collection']['instrument_id']])
        heading_data.append(['Respondent', response['metadata']['ru_ref'][:11]])
        heading_data.append(['Submitted At', localised_date_str])

        heading = Table(heading_data, style=heading_style, colWidths='*')

        elements.append(heading)

        for question_group in survey['question_groups']:

            if 'title' in question_group:
                elements.append(Paragraph(question_group['title'], styleSH))

                for question in question_group['questions']:
                    if 'text' in question:
                        answer = ''
                        if question['question_id'] in response['data']:
                            answer = response['data'][question['question_id']]

                        text = question.get("text", " ")
                        if not text[0].isdigit():
                            text = " ".join((question.get("number", ""), text))
                        elements.append(Paragraph(text, styleSSH))
                        elements.append(Paragraph(answer, styleN))

        return elements

    @staticmethod
    def get_localised_date(date_to_transform, timezone='Europe/London'):
        return arrow.get(date_to_transform).to(timezone).format("DD MMMM YYYY HH:mm:ss")


def parser(description=__doc__):
    rv = argparse.ArgumentParser(
        description,
    )
    rv.add_argument(
        "--survey", required=True,
        help="Set a path to the survey JSON file.")
    return rv


def main(args):
    fP = os.path.expanduser(os.path.abspath(args.survey))
    with open(fP, "r") as fObj:
        survey = json.load(fObj)

    data = json.load(sys.stdin)
    tx = PDFTransformer(survey, data)
    output = tx.render()
    sys.stdout.write(output.decode("latin-1"))
    return 0


def run():
    p = parser()
    args = p.parse_args()
    rv = main(args)
    sys.exit(rv)

if __name__ == "__main__":
    run()
