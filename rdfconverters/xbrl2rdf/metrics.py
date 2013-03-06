from rdfconverters.xbrl2rdf.monetary import Monetary

class Metrics:
    def __init__(self, xebr_map):
        self.xebr_map = xebr_map

    def get_metrics(self):
        '''{xebr_concept: calculating_function}+'''
        return {
            'ebit': self.ebit,
            'netResult': self.netResult,
            'ownFunds': self.ownFunds,
            'addedValue': self.addedValue,
            'currentRatio': self.currentRatio,
            'netWorkingCapital': self.netWorkingCapital
        }

    def __has_all(self, keys):
        return all(key in self.xebr_map for key in keys)

    def __monetary(self, key):
        return Monetary.from_string(self.xebr_map[key])

    def ebit(self):
        concepts = ['hasOperatingProfitLossTotal']
        if not self.__has_all(concepts): return None
        return self.__monetary(concepts[0])

    def netResult(self):
        concepts = ['hasProfitLossForThePeriodTotal']
        if not self.__has_all(concepts): return None
        return self.__monetary(concepts[0])

    def ownFunds(self):
        concepts = ['hasEquityTotal']
        if not self.__has_all(concepts): return None
        return self.__monetary(concepts[0])

    def addedValue(self):
        concepts = ['hasOperatingIncomeTotal', 'hasRawMaterialsAndConsumablesTotal', 'hasOtherOperatingCharges']
        if not self.__has_all(concepts): return None

        monetary = [self.__monetary(concept) for concept in concepts]
        return monetary[0] - monetary[1] - monetary[2]

    def currentRatio(self):
        concepts = ['hasCurrentAssetsTotal', 'hasAmountsPayableWithinOneYearTotal']
        if not self.__has_all(concepts): return None

        monetary = [self.__monetary(concept) for concept in concepts]
        return (monetary[0] / monetary[1]).decimal # Current ratio is not a monetary value

    def netWorkingCapital(self):
        concepts = ['hasCurrentAssetsTotal', 'hasAmountsPayableWithinOneYearTotal']
        if not self.__has_all(concepts): return None

        monetary = [self.__monetary(concept) for concept in concepts]
        return monetary[0] - monetary[1]
