import operator
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import reduce

from transform.transformers.survey import Survey


__doc__ = """
The processor module collects business logic processing functions under a single
namespace so they can be used in :ref:`transformers`.

"""


class Processor:
    """Business logic operations on data.

    These methods are used to perform business logic on survey data.
    They are mostly concerned with combining multiple fields into a
    single field for output.

    Principles for processor methods:

    * The method is responsible for range check according to its own logic.
    * Parametrisation is possible; use `functools.partial` to bind arguments.
    * Return data of the same type as the supplied default.
    * On any error, return the default.

    """

    @staticmethod
    def round_towards(val, precision, *args, rounding_direction=ROUND_HALF_UP, **kwargs):
        if precision:
            return val.quantize(Decimal(precision), rounding=rounding_direction)

    @staticmethod
    def aggregate(qid, data, default, *args, weights=[], precision=None,
                  rounding_direction=ROUND_HALF_UP, **kwargs):
        """Calculate the weighted sum of a question group.

        :param str qid: The question id.
        :param data: The full survey data.
        :type data: dict(str, str)
        :param default: The default value for the question.
        :param weights: A sequence of 2-tuples giving the weight value for each
            question in the group.
        :type weights: [(str, number)]
        :param precision: A string representing the precision of the Decimal
            after rounding. To get an integer, use '1.'.
        :type precision: str
        :param rounding_direction: How rounding should be carried out. Uses the
            decimal standard library module's rounding modes
            https://docs.python.org/3/library/decimal.html#rounding-modes
        """
        try:
            val = Decimal(data.get(qid, 0)) \
                + sum(Decimal(scale) * Decimal(data.get(q, 0))
                      for q, scale in weights)

            if precision:
                val = Processor.round_towards(
                    val, precision=precision, rounding_direction=rounding_direction)
            return type(default)(val)

        except (InvalidOperation, ValueError):
            return default

    @staticmethod
    def evaluate(qid, data, default, *args, group=[], convert=bool, op=operator.or_, **kwargs):
        """Perform a map/reduce evaluation of a question group.

        :param str qid: The question id.
        :param data: The full survey data.
        :type data: dict(str, str)
        :param default: The default value for the question.
        :param group: A sequence of question ids.
        :param convert: A type or function to convert the group values.
        :param op: A binary operator or function to reduce data to a single value.

        """
        try:
            group_vals = [data.get(qid, None)] + [data.get(q, None) for q in group]
            data = [convert(i) for i in group_vals if i is not None]
            return type(default)(reduce(op, data))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def boolean(qid, data, default, *args, group=[], **kwargs):
        """Returns bool True if a value is supplied, else false.

        :param str qid: The question id.
        :param data: The full survey data.
        :param default: The default value for the question.
        :type data: dict(str, str)
        :param group: A sequence of question ids.

        """

        try:
            return any([data.get(qid, None)] + [data.get(q, None) for q in group])
        except (AttributeError, InvalidOperation, TypeError, ValueError):
            return False

    @staticmethod
    def mean(qid, data, default, *args, group=[], **kwargs):
        """Calculate the mean of all fields in a question group.

        :param str qid: The question id.
        :param data: The full survey data.
        :type data: dict(str, str)
        :param default: The default value for the question.
        :param group: A sequence of question ids.
        :param precision: A string representing the precision of the Decimal
            after rounding. To get an integer, use '1.'.
        :type precision: str
        :param rounding_direction: How rounding should be carried out. Uses the
            decimal standard library module's rounding modes
            https://docs.python.org/3/library/decimal.html#rounding-modes

        """
        try:
            group_vals = [data.get(qid, None)] + [data.get(q, None) for q in group]
            data = [Decimal(i) for i in group_vals if i is not None]
            divisor = len(data) or 1
            val = sum(data) / divisor
            return type(default)(val)
        except (AttributeError, InvalidOperation, TypeError, ValueError):
            return default

    @staticmethod
    def events(qid, data, default, *args, group=[], **kwargs):
        """Return a sequence of time events from a question group.

        :param str qid: The question id.
        :param data: The full survey data.
        :type data: dict(str, str)
        :param default: The default value for the question.
        :param group: A sequence of question ids.

        """
        try:
            group_vals = [data.get(qid, None)] + [data.get(q, None) for q in group]
            data = sorted(filter(
                None, (Survey.parse_timestamp(i) for i in group_vals if i is not None)
            ))
            if all(isinstance(i, type(default)) for i in data):
                return data
            else:
                return type(default)(data)
        except (AttributeError, TypeError, ValueError):
            return default

    @staticmethod
    def survey_string(qid, data, default, *args, survey=None, **kwargs):
        """Accept a string as an option for a question.

        This method provides an opportunity for validating the string against
        the survey definition, though this has not been a requirement so far.

        :param str qid: The question id.
        :param data: The full survey data.
        :type data: dict(str, str)
        :param default: The default value for the question.
        :param dict survey: The survey definition.

        """
        try:
            return type(default)(data[qid])
        except (KeyError, ValueError):
            return default

    @staticmethod
    def unsigned_integer(qid, data, default, *args, precision=None,
                         rounding_direction=ROUND_HALF_UP, **kwargs):
        """Process a string as an unsigned integer.

        :param str qid: The question id.
        :param data: The full survey data.
        :type data: dict(str, str)
        :param default: The default value for the question.

        """
        try:
            val = Decimal(data.get(qid, default))
            if precision:
                val = Processor.round_towards(
                    val, precision=precision, rounding_direction=rounding_direction)
        except ValueError:
            return default
        else:
            return type(default)(val) if val >= 0 else default

    @staticmethod
    def percentage(qid, data, default, *args, **kwargs):
        """Process a string as a number, checking that it is valid as a percentage.

        :param str qid: The question id.
        :param data: The full survey data.
        :type data: dict(str, str)
        :param default: The default value for the question.

        """
        try:
            rv = Decimal(data.get(qid, default))
        except ValueError:
            return default
        else:
            return type(default)(rv) if 0 <= rv <= 100 else default
