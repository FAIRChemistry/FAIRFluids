"""
fluid_io.py

Extends the Fluid class with input utilities for loading data from CSV files.

Example CSV format:

# compounds,propertyID,propertyType,parameterID,parameterType,parameterValue,propertyValue,uncertainty,method,method_description
# H2O_001;urea_001,viscosity,viscosity,temp,Temperature, K,298.15,1.23,0.01,measured,Rotational viscometer
# H2O_001;urea_001,viscosity,viscosity,temp,Temperature, K,303.15,1.10,0.01,measured,Rotational viscometer

Usage:
    from FAIRFluids.core.fluid_io import FluidIO
    from FAIRFluids.core.lib import FAIRFluidsDocument
    fluid = FluidIO()
    fluid.data_from_csv('path/to/data.csv')
    doc = FAIRFluidsDocument()
    doc.fluid.append(fluid)
"""
import csv
from typing import Optional
from .lib import Fluid, Property, Parameter, Measurement, PropertyValue, ParameterValue, Method

class FluidIO(Fluid):
    """
    Extends Fluid with input utility to load data from a CSV file.
    """
    def data_from_csv(self, csv_path: str):
        """
        Populate this Fluid instance with data from a CSV file.
        Each row is interpreted as a measurement with associated property and parameter values.
        """
        with open(csv_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Parse compounds (semicolon-separated)
                compounds = [c.strip() for c in row['compounds'].split(';')]
                if not self.compounds:
                    self.compounds = compounds
                # Property
                prop = Property(
                    propertyID=row['propertyID'],
                    properties=row.get('propertyType')
                )
                if all(p.propertyID != prop.propertyID for p in self.property):
                    self.property.append(prop)
                # Parameter
                param = Parameter(
                    parameterID=row['parameterID'],
                    parameter=row.get('parameterType'),
                )
                if all(p.parameterID != param.parameterID for p in self.parameter):
                    self.parameter.append(param)
                # Measurement
                prop_val = PropertyValue(
                    propertyID=row['propertyID'],
                    propValue=float(row['propertyValue']),
                    uncertainty=float(row['uncertainty']) if row.get('uncertainty') else None
                )
                param_val = ParameterValue(
                    parameterID=row['parameterID'],
                    paramValue=float(row['parameterValue'])
                )
                meas = Measurement(
                    propertyValue=[prop_val],
                    parameterValue=[param_val],
                    method=Method[row['method'].upper()] if row.get('method') else None,
                    method_description=row.get('method_description')
                )
                self.measurement.append(meas) 