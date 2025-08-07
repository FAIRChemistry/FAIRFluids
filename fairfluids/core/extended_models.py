from FAIRFluids.core.lib import *

class FAIRFluidsDocument(FAIRFluidsDocument):
    def dummy_method(self):
        pass

class Version(Version):
    def dummy_method(self):
        pass

class Citation(Citation):
    def dummy_method(self):
        pass

class Author(Author):
    def dummy_method(self):
        pass

class Compound(Compound):
    @computed_field
    @property
    def pubChemID(self) -> int:
        if not self.pubChemID and self.commonName:
            try:
                url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{self.commonName}/cids/JSON"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'IdentifierList' in data:
                        self.pubChemID = data['IdentifierList']['CID'][0]
                    else:
                        self.pubChemID = 0
                else:
                    self.pubChemID = 0
            except:
                self.pubChemID = 0
        return self.pubChemID

class Fluid(Fluid):
    def dummy_method(self):
        pass

class Property(Property):
    def dummy_method(self):
        pass

class Parameter(Parameter):
    def dummy_method(self):
        pass

class Measurement(Measurement):
    def dummy_method(self):
        pass

class PropertyValue(PropertyValue):
    def dummy_method(self):
        pass

class ParameterValue(ParameterValue):
    def dummy_method(self):
        pass

class UnitDefinition(UnitDefinition):
    def dummy_method(self):
        pass

class BaseUnit(BaseUnit):
    def dummy_method(self):
        pass 