import logging
import os


def logger_initial_config(service_name=None,
                          log_level=None,
                          logger_format=None,
                          logger_date_format=None):
    '''Set initial logging configurations.

    :param service_name: Name of the service
    :type logger: String

    :param log_level: A string or integer corresponding to a Python logging level
    :type log_level: String

    :param logger_format: A string defining the format of the logs
    :type log_level: String

    :param logger_date_format: A string defining the format of the date/time in the logs
    :type log_level: String

    :rtype: None

    '''
    if not log_level:
        log_level = os.getenv('LOGGING_LEVEL', 'DEBUG')
    if not logger_format:
        logger_format = (
            "%(asctime)s.%(msecs)06dZ|"
            "%(levelname)s: {}: %(message)s"
        ).format(service_name)
    if not logger_date_format:
        logger_date_format = os.getenv('LOGGING_DATE_FORMAT', "%Y-%m-%dT%H:%M:%S")

    logging.basicConfig(level=log_level,
                        format=logger_format,
                        datefmt=logger_date_format)
