
class CSFormatter:

    @staticmethod
    def header(batchNo, ts):
        return "{0}{1:06}{2}".format("FBFV", batchNo, ts.strftime("%d/%m/%y"))

