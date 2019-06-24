import pandas as pd
import os
from fredapi import Fred
fred = Fred(api_key='30239c301afe55694c8d903e5856b061')


class getFredData:

    def __init__(self):
        self.BASE_DIR = os.path.dirname(__file__)
        """
        Initialize the getFredData class
        This has default methods to download data from Fred & Zillow
        """

    def sanitize(self,inputString):
        fredCodeLookup = self.available_codes()

        standardizedString = None
        if inputString in list(fredCodeLookup['Code']):
            inputString = inputString.upper()
        else:
            inputString = None

        if inputString in ('UE', 'UR'):
            standardizedString = 'UNRATE'
        elif inputString == 'CPI':
            standardizedString = 'CPILFESL'
        elif inputString in ('HPI', 'HPA'):
            standardizedString = 'USSTHPI'
        elif inputString != None:
            standardizedString = inputString
        return standardizedString


    def available_codes(self):
        codeLookup = pd.read_excel(os.path.join(self.BASE_DIR, 'FREDCode.xlsx'))
        return codeLookup

    def fetch_data(self,macroVarInput):

        macroVar = self.sanitize(macroVarInput)
        if macroVar is None:
            import textwrap
            raise ValueError(textwrap.dedent("""\
                    You need to valid input - HPI, Unemployment, GDP, CPI etc.
                    Use the available_codes to view codes"""))
        else:
            macroVar = macroVar.upper()
            print(macroVar)
            fredData = fred.get_series_latest_release(macroVar).reset_index()
            fredData.columns = ['Date',macroVarInput]

        return fredData