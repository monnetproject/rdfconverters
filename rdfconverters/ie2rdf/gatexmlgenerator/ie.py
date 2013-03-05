# -*- coding: utf-8 -*-

# Noëmi Aepli

"""Script extract information from annotated strings of GATE output
Dependencies: GICS-ontology: file with IDs, labels and descriptions of GICS activities
Usage: python ie.py FileIn
"""

from xml.etree import cElementTree
from collections import defaultdict
import re
from pprint import pprint as pp
import sys
import operator
import icbnltk
from xml.dom.minidom import Document

def convert_string(s):
  document = cElementTree.fromstring(s)
  xml_str = convert(document)
  return xml_str

def convert_file(filename):
  print("Converting", filename)
  document = cElementTree.parse(filename)
  xml_str = convert(document)
  return xml_str

#Convert human-readable number representation to monetary or numeric value
def normaliseMonetaryValue(m):
  m = re.sub(r'[\s,]', '', m)
  for c in ['EUR', 'USD', 'Euros', 'euros', 'Euro', 'euro']:
      if re.search(c, m):
          currency = c
          m = m.replace(currency, '')
          cu = re.sub('[Ee]uros?', 'EUR', c)
          currency = cu
          break
  else:
      currency=''
  r = re.search('\d+\.(\d+)', m)
  if r is not None:
      m = m.replace('.', '')
      numbers_after_decimals = len(r.group(1))
  else:
      numbers_after_decimals = 0

  multipliers = (('bn', 9), ('billion', 9), ('mn', 6), ('million', 6), ('m', 6))
  for phrase, multiplier in multipliers:
      m = re.sub(phrase, '0'*(multiplier-numbers_after_decimals), m, flags=re.IGNORECASE)
  return m+currency

def normaliseNumber(n):
  if re.search("[0-9,\'\.]+m", n):
      n = re.sub('m ','million', n)
  n = re.search("[0-9,\'\.]+( billion| million|bn|m)?", n).group()
  n = re.sub(r'[\s,]', '', n)

  r = re.search('\d+\.(\d+)', n)
  if r is not None:
      n = n.replace('.', '')
      numbers_after_decimals = len(r.group(1))
  else:
      numbers_after_decimals = 0

  multipliers = (('bn', 9), ('billion', 9), ('mn', 6), ('million', 6), ('m', 6))
  for phrase, multiplier in multipliers:
      n = re.sub(phrase, '0'*(multiplier-numbers_after_decimals), n, flags=re.IGNORECASE)
  return n

def convert(document):

  activity = document.findall('.//Activity')
  company = document.findall('.//Company')
  employee = document.findall('.//Employee')
  monetaryValue = document.findall('.//MonetaryValue')
  location = document.findall('.//Location')
  customer = document.findall('.//Customer')

  activityList = [act.text for act in activity]
  companyList = [com.text for com in company]
  employeeList = [emp.text for emp in employee]
  monetaryValueList = [mv.text for mv in monetaryValue]
  locationList = [loc.text for loc in location]
  locationString = ", ".join(locationList)
  customerList = [cus.text for cus in customer]


  # Company - Name -------------------------------------------------------------------------
  companySet = set(companyList)

  # Activity - ------------------------------------------------------------------------
  activitySet = set(activityList)
  activities = icbnltk.icb_matches(' '.join(activitySet))


  # Employee - number ----------------------------------------------------------------------

  enr = " ".join(employeeList)
  if enr != '':
      employeeNumber = normaliseNumber(enr)
  else:
      employeeNumber = ''

  # Customer - number & type ----------------------------------------------------------------------
  customer = defaultdict(int)

  for cust in customerList:
      if re.search('\d',cust):
          customerNumber = normaliseNumber(cust)
      else:
          customerNumber = ''

      kindC = re.findall('(\w+|\w+ and \w+) (?:customers|clients|consumers|patients)', cust)
      if re.search('\d', " ".join(kindC)) == None and "million" not in kindC and "billion" not in kindC:
          customerKind = ", ".join(kindC)
      else:
          customerKind = ""

      customer[cust] = (customerNumber, customerKind)

  # Location -------------------------------------------------------------------------------
  locations = []
  [locations.append(l) for l in locationString.split() if l[0].isupper() or l == "and"]

  if len(locations) == 0:
      locResult = ""
  else:
      locResult = " ".join(locations)
      locResult = re.sub(" and", ",",locResult)

  # MonetaryValue --------------------------------------------------------------------------
  resultDict = defaultdict(int)

  for mon in monetaryValueList:
      if re.search("(EUR|EUR || |[eE]uro)[0-9,\'\.]+ ?([mb]illion|m|bn)( [eE]uro)?", mon):
          v = re.search("(EUR|EUR || |[eE]uro )[0-9,\'\.]+ ?([mb]illion|m|bn)( [eE]uro)?", mon).group()
      else:
          v = ""
      value = normaliseMonetaryValue(v)

      if re.search('\d{4}', mon):
          date = re.search('\d{4}', mon).group()
      else:
          date = ""

      if re.search('revenue', mon) != None:
          kind = re.search('revenue', mon).group()
      elif re.search('income', mon) != None:
          kind = re.search('income', mon).group()
      elif re.search('profit', mon) != None:
          kind = re.search('profit', mon).group()
      elif re.search('sales', mon) != None:
          kind = re.search('sales', mon).group()
      elif re.search('turnover', mon) != None:
          kind = re.search('turnover', mon).group()
      else:
          kind = "unknownMonetaryValue"

      resultDict[value] = (kind, date, mon)

  # print output on standard output	
  print("ANNOTATIONS-----------------------------------------------")
  print("{0: <20}{1}".format("Company:", companySet))
  print("{0: <20}{1}".format("Activity:", activityList))
  print("{0: <20}{1}".format("Location:", locationList))
  print("{0: <20}{1}".format("MonetaryValue:", monetaryValueList))
  print("{0: <20}{1}".format("Employee:", employeeList))
  print("{0: <20}{1}".format("Customer:", customerList))

  print("TEMPLATE--------------------------------------------------")
  print("{0: <30}{1}".format("Activity:", activities))
  print("{0: <30}{1}".format("Location:", locResult))
  if len(resultDict) > 0:
      for key in resultDict:
          if resultDict[key][0] != "":
              print("{0: <30}{1}".format(resultDict[key][0].title()+", "+resultDict[key][1], key))
          else:
              print("{0: <20}{1}".format("Monetary Value:", ""))
  else:
      print ("{0: <30}{1}".format("UnknownMonetaryValue:", ""))
  print ("{0: <30}{1}".format("Number of employees:", employeeNumber))
  nr = []
  kind = []
  if len(customer) > 0:
      for c in customer:
          if customer[c][0] != '':
              nr.append(customer[c][0])
          if customer[c][1] != '':
              kind.append(customer[c][1])
  print("{0: <30}{1}".format("Number of customers:", ", ".join(nr)))
  print("{0: <30}{1}".format("Kind of customers:", ", ".join(kind)))


  # write output to XML files
  doc = Document()
  cp = doc.createElement("companyprofile")
  doc.appendChild(cp)

  def make_element(tag_name, **attributes):
      el = doc.createElement(tag_name)
      for att, val in attributes.items():
          el.setAttribute(att, val)
      return el

  def make_annotation(value):
      annotation = doc.createElement("annotation")
      annotationText = doc.createTextNode(value)
      annotation.appendChild(annotationText)
      return annotation

  #Company
  for company in companySet:
      el = make_element("company", name=company)
      annotation = make_annotation(company)
      el.appendChild(annotation)
      cp.appendChild(el)

  #Activity
  if activities is not None and len(activities) > 0:
      for icb_number, icb_activity in activities:
          el = make_element("activity", label=icb_activity, id=icb_number)

          for activity in activitySet:
              annotation = make_annotation(activity)
              el.appendChild(annotation)
          cp.appendChild(el)

  # Location
  if locResult != "":
      location = doc.createElement("location")
      location.setAttribute("value", locResult)
      cp.appendChild(location)
      for element in locationList:
          annotation = doc.createElement("annotation")
          location.appendChild(annotation)
          annotationText = doc.createTextNode(element)
          annotation.appendChild(annotationText)

  # Monetary Values
  if len(resultDict) > 0:
      for key in resultDict:
          mV = doc.createElement(resultDict[key][0])
          mV.setAttribute("date", resultDict[key][1])
          mV.setAttribute("value", key)
          cp.appendChild(mV)
          annotation = doc.createElement("annotation")
          mV.appendChild(annotation)
          annotationText = doc.createTextNode(resultDict[key][2])
          annotation.appendChild(annotationText)

  # Employees
  if employeeNumber != "":
      employees = doc.createElement("employees")
      employees.setAttribute("number", employeeNumber)
      cp.appendChild(employees)
      for element in employeeList:
          annotation = doc.createElement("annotation")
          employees.appendChild(annotation)
          annotationText = doc.createTextNode(element)
          annotation.appendChild(annotationText)

  # Customers
  if len(customer) > 0:
      for c in customer:
          if customer[c][0] != '' or customer[c][1] != '':
              customers = doc.createElement("customers")
              customers.setAttribute("number", customer[c][0])
              customers.setAttribute("kind", customer[c][1])
              cp.appendChild(customers)
              annotation = doc.createElement("annotation")
              customers.appendChild(annotation)
              annotationText = doc.createTextNode(c)
              annotation.appendChild(annotationText)

  return doc.toprettyxml(indent="  ")

if __name__=='__main__':
  print(convert_file(sys.argv[1]))
