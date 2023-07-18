month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December' ]

class DateConverter:

    @staticmethod
    def convertYearAndMonth(year, month):
        if type(year) is int:
            year = str(year)

        if type(month) is str:
            return  year + " " + month
        else:
            return  year + " " + month_names[month - 1]

    @staticmethod
    def getMonthAndYear(str):
        year, month = str.split(" ")

        return int(year), month_names.index(month)