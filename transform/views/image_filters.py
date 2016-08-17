import os
from jinja2 import Environment, PackageLoader
import arrow


def format_date(value, style='long'):
    """convert a datetime to a different format."""

    timezone = 'Europe/London'
    if style is 'short':
        return arrow.get(value).to(timezone).format("YYYYMMDD")
    else:
        return arrow.get(value).to(timezone).format("DD/MM/YYYY HH:mm:ss")


def statistical_unit_id_filter(value):
    if len(value) == 12:
        return value[0:-1]

    return value


def scan_id_filter(value):
    scanfile, _ = os.path.splitext(value)

    return scanfile


def page_filter(value):
    page = str(value).zfill(3) if value else ''

    return "%s,0" % page if value == 1 else page


def format_period(value):
    if not value:
        return ''

    if len(value) == 4:
        return "20%s" % value
    elif len(value) < 6:
        return value.zfill(6)
    elif len(value) > 6:
        return value[0:6]

    return value


def trim_final_newline(value):
    return value.rstrip('\r\n')


def get_env():
    env = Environment(loader=PackageLoader('transform', 'templates'))

    env.filters['format_date'] = format_date
    env.filters['statistical_unit_id'] = statistical_unit_id_filter
    env.filters['scan_id'] = scan_id_filter
    env.filters['format_page'] = page_filter
    env.filters['format_period'] = format_period
    env.filters['trim_final_newline'] = trim_final_newline

    return env
