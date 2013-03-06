import re
from decimal import *

getcontext().rounding=ROUND_HALF_UP


class Monetary:
    '''MFO's xsd:monetary representation with overloaded operators for arithmetic'''

    @staticmethod
    def from_string(str_monetary):
        currency = str_monetary[-3:]
        amount = str_monetary[:-3]
        return Monetary(amount, currency)

    q = Decimal(10) ** -2
    def __init__(self, amount, currency):
        if re.match(r'^[A-Z]{3}?$', currency) is None:
            raise ValueError('%s is not a valid currency' % currency)

        self.currency = currency
        self.decimal = Decimal(amount).quantize(self.q)

    def __str__(self):
        return str(self.decimal) + self.currency

    def __repr__(self):
        return str(self.decimal) + self.currency

    def __add__(self, monetary):
        if monetary.currency != self.currency: raise ValueError('Incompatible currencies: cannot add %s to %s ' % (monetary, self))
        return Monetary(self.decimal + monetary.decimal, self.currency)

    def __sub__(self, monetary):
        if monetary.currency != self.currency: raise ValueError('Incompatible currencies: cannot subtract %s from %s ' % (monetary, self))
        return Monetary(self.decimal - monetary.decimal, self.currency)

    def __mul__(self, monetary):
        if monetary.currency != self.currency: raise ValueError('Incompatible currencies: cannot multiply %s and %s ' % (monetary, self))
        return Monetary(self.decimal * monetary.decimal, self.currency)

    def __truediv__(self, monetary):
        if monetary.currency != self.currency: raise ValueError('Incompatible currencies: cannot divide %s and %s ' % (monetary, self))
        return Monetary(self.decimal / monetary.decimal, self.currency)

    def __lt__(self, monetary):
        if monetary.currency != self.currency: raise ValueError('Incompatible currencies: cannot compare %s and %s ' % (monetary, self))
        return self.decimal < monetary.decimal

    def __le__(self, monetary):
        if monetary.currency != self.currency: raise ValueError('Incompatible currencies: cannot compare %s and %s ' % (monetary, self))
        return self.decimal <= monetary.decimal

    def __gt__(self, monetary):
        if monetary.currency != self.currency: raise ValueError('Incompatible currencies: cannot compare %s and %s ' % (monetary, self))
        return self.decimal > monetary.decimal

    def __ge__(self, monetary):
        if monetary.currency != self.currency: raise ValueError('Incompatible currencies: cannot compare %s and %s ' % (monetary, self))
        return self.decimal >= monetary.decimal

    def __eq__(self, monetary):
        if isinstance(monetary):
            return self.decimal == monetary.decimal and monetary.currency == self.currency
        else:
            return str(self) == monetary
