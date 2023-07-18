from dateConverter import DateConverter

class Date(DateConverter):
    intMonth = 0
    year = 0

    def init(self, month = 7, year=2023):
        self.intMonth = month
        self.year = year

    def toString(self):
        return self.month_names[self.intMonth - 1] + " " + str(self.year)

    def getMonthNumber(self):
        return self.intMonth

    def getYear(self):
        return self.year

    def getMonthName(self):
        return self.month_names[self.intMonth - 1]

    def setMonth(self, month):
        self.intMonth = month

    def setYear(self, year):
        self.year = year


