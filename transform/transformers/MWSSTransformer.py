
class CSFormatter:

    @staticmethod
    def batch_header(batchNo, ts):
        return "{0}{1:06}{2}".format("FBFV", batchNo, ts.strftime("%d/%m/%y"))

    @staticmethod
    def form_header(formId, ruRef, check, period):
        formId = "{0:04}".format(formId) if isinstance(formId, int) else formId
        return "{0}:{1}{2}:{3}".format(formId, ruRef, check, period)

    @staticmethod
    def pck_lines(batchNo, ts, data):
        return [
            header(batchNo, ts),
            "FV",
        ]
