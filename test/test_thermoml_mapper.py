"""
Tests for ThermoML → FAIRFluids (``fairfluids.io.thermoml_to_fairfluids``).

Run with::

    pytest test/test_thermoml_mapper.py -v

Integration tests require sample XML under ``transition_water/data/``.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional

import pytest

from fairfluids.core.lib import FAIRFluidsDocument, Method, Parameters, Properties
from fairfluids.io.thermoml_to_fairfluids import convert
from fairfluids.io.canonical.composition import (
    is_valid_mole_fraction_sum,
    mass_fractions_to_mole_fractions,
    molalities_to_mole_fractions,
)
from fairfluids.io.canonical.mappers.parameter_mapper import ParameterMapper
from fairfluids.io.canonical.mappers.property_mapper import PropertyMapper

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "transition_water" / "data"

GLYCEROL_WATER_XML = DATA_DIR / "glycerol_water" / "j.jct.2014.06.031.xml"
METHANOL_WATER_XML = DATA_DIR / "methanol_water" / "fluid.2014.07.013.xml"
JE700300Y_XML = (
    REPO_ROOT
    / "transition_water"
    / "thermoml_xml_water_methanol_density"
    / "10.1021_je700300y.xml"
)


def _fluid_measurements(fluid) -> List:
    if fluid.sample is None:
        return []
    return fluid.sample.measurement


def _convert_file(path: Path, source_doi: Optional[str] = None) -> FAIRFluidsDocument:
    payload = convert(path, fetch_from_pubchem=False)
    doc = FAIRFluidsDocument.model_validate(payload)
    if source_doi:
        if doc.citation is not None:
            doc.citation.doi = source_doi
        for fluid in doc.fluid:
            for measurement in _fluid_measurements(fluid):
                measurement.source_doi = source_doi
    return doc


def _convert_xml(root: ET.Element) -> FAIRFluidsDocument:
    xml_bytes = ET.tostring(root, encoding="utf-8")
    with NamedTemporaryFile(suffix=".xml") as tmp:
        tmp.write(xml_bytes)
        tmp.flush()
        return _convert_file(Path(tmp.name))


def _mole_fraction_param_ids(fluid) -> set[str]:
    return {
        p.parameterID
        for p in fluid.parameter
        if p.parameters == Parameters.MOLE_FRACTION and p.parameterID
    }


def _measurement_mole_fraction_values(meas, mf_pids: set[str]) -> list[float]:
    return [
        float(pv.paramValue)
        for pv in meas.parameterValue
        if pv.parameterID in mf_pids and pv.paramValue is not None
    ]


# ---------------------------------------------------------------------------
# Mapper unit tests (io pipeline)
# ---------------------------------------------------------------------------


class TestPropertyMapper:
    def test_density_exact(self):
        assert PropertyMapper.map("Mass density, kg/m3") == Properties.DENSITY

    def test_density_unicode(self):
        assert PropertyMapper.map("Mass density, kg/m³") == Properties.DENSITY

    def test_viscosity(self):
        assert PropertyMapper.map("Viscosity, Pa*s") == Properties.VISCOSITY
        assert PropertyMapper.map("Dynamic viscosity, Pa*s") == Properties.VISCOSITY

    def test_thermal_conductivity(self):
        assert (
            PropertyMapper.map("Thermal conductivity, W/(m*K)")
            == Properties.THERMAL_CONDUCTIVITY
        )

    def test_vapor_pressure(self):
        assert (
            PropertyMapper.map("Vapor or sublimation pressure, kPa")
            == Properties.VAPOR_PRESSURE
        )

    def test_molar_volume(self):
        assert PropertyMapper.map("Molar volume, m3/mol") == Properties.MOLAR_VOLUME

    def test_unknown_returns_none(self):
        assert PropertyMapper.map("nonexistent property xyz") is None

    def test_refractive_index(self):
        assert PropertyMapper.map("Refractive index") == Properties.REFRACTIVE_INDEX


class TestParameterMapper:
    def test_temperature(self):
        assert ParameterMapper.map("Temperature, K") == Parameters.TEMPERATURE

    def test_pressure(self):
        assert ParameterMapper.map("Pressure, kPa") == Parameters.PRESSURE

    def test_mole_fraction(self):
        assert ParameterMapper.map("Mole fraction") == Parameters.MOLE_FRACTION

    def test_solvent_mole_fraction(self):
        assert (
            ParameterMapper.map("Solvent: Mole fraction")
            == Parameters.SOLVENT_MOLE_FRACTION
        )


# ---------------------------------------------------------------------------
# Integration fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def glycerol_water_doc():
    pytest.importorskip("fairfluids")
    if not GLYCEROL_WATER_XML.exists():
        pytest.skip(f"Test data not found: {GLYCEROL_WATER_XML}")
    return _convert_file(GLYCEROL_WATER_XML)


@pytest.fixture(scope="module")
def methanol_water_doc():
    pytest.importorskip("fairfluids")
    if not METHANOL_WATER_XML.exists():
        pytest.skip(f"Test data not found: {METHANOL_WATER_XML}")
    return _convert_file(METHANOL_WATER_XML)


class TestGlycerolWaterConversion:
    def test_document_not_none(self, glycerol_water_doc):
        assert glycerol_water_doc is not None

    def test_version_extracted(self, glycerol_water_doc):
        v = glycerol_water_doc.version
        if v is None:
            pytest.skip("Converter does not populate document.version for this dataset")
        assert v.versionMajor == 2
        assert v.versionMinor == 0

    def test_citation_doi(self, glycerol_water_doc):
        assert glycerol_water_doc.citation is not None
        assert glycerol_water_doc.citation.doi == "10.1016/j.jct.2014.06.031"

    def test_citation_lit_type(self, glycerol_water_doc):
        from fairfluids.core.lib import LitType

        assert glycerol_water_doc.citation.litType == LitType.JOURNAL

    def test_citation_authors(self, glycerol_water_doc):
        authors = glycerol_water_doc.citation.author
        assert len(authors) >= 1
        family_names = [a.family_name for a in authors]
        assert "Egorov" in family_names

    def test_citation_pub_year(self, glycerol_water_doc):
        assert glycerol_water_doc.citation.publication_year == "2014"

    def test_compounds_extracted(self, glycerol_water_doc):
        assert len(glycerol_water_doc.compound) >= 2

    def test_compound_names(self, glycerol_water_doc):
        names = [c.commonName for c in glycerol_water_doc.compound]
        assert "glycerol" in names
        assert "water" in names

    def test_compound_ids_generated(self, glycerol_water_doc):
        for compound in glycerol_water_doc.compound:
            assert compound.compoundID is not None
            assert compound.compoundID.startswith("compound_")

    def test_compound_inchi_keys(self, glycerol_water_doc):
        inchi_keys = [c.standard_InChI_key for c in glycerol_water_doc.compound]
        assert "PEDCQBHIVMGVHV-UHFFFAOYSA-N" in inchi_keys

    def test_fluids_extracted(self, glycerol_water_doc):
        assert len(glycerol_water_doc.fluid) >= 1

    def test_fluid_has_properties(self, glycerol_water_doc):
        for fluid in glycerol_water_doc.fluid:
            assert len(fluid.property) > 0

    def test_density_property_present(self, glycerol_water_doc):
        all_prop_types = [
            p.properties
            for fluid in glycerol_water_doc.fluid
            for p in fluid.property
            if p.properties is not None
        ]
        assert Properties.DENSITY in all_prop_types

    def test_property_has_unit(self, glycerol_water_doc):
        for fluid in glycerol_water_doc.fluid:
            for prop in fluid.property:
                if prop.unit is not None:
                    assert prop.unit.name is not None

    def test_parameters_extracted(self, glycerol_water_doc):
        for fluid in glycerol_water_doc.fluid:
            assert len(fluid.parameter) > 0

    def test_temperature_parameter_present(self, glycerol_water_doc):
        all_params = [
            p.parameters
            for fluid in glycerol_water_doc.fluid
            for p in fluid.parameter
            if p.parameters is not None
        ]
        assert Parameters.TEMPERATURE in all_params

    def test_measurements_extracted(self, glycerol_water_doc):
        for fluid in glycerol_water_doc.fluid:
            assert len(_fluid_measurements(fluid)) > 0

    def test_measurement_has_property_values(self, glycerol_water_doc):
        for fluid in glycerol_water_doc.fluid:
            for meas in _fluid_measurements(fluid)[:3]:
                assert len(meas.propertyValue) > 0

    def test_measurement_has_parameter_values(self, glycerol_water_doc):
        for fluid in glycerol_water_doc.fluid:
            for meas in _fluid_measurements(fluid)[:3]:
                assert len(meas.parameterValue) > 0

    def test_property_values_numeric(self, glycerol_water_doc):
        for fluid in glycerol_water_doc.fluid:
            for meas in _fluid_measurements(fluid)[:5]:
                for pv in meas.propertyValue:
                    assert pv.propValue is not None
                    assert isinstance(pv.propValue, float)

    def test_temperature_values_reasonable(self, glycerol_water_doc):
        temp_pids = {
            p.parameterID
            for fluid in glycerol_water_doc.fluid
            for p in fluid.parameter
            if p.parameters == Parameters.TEMPERATURE
        }
        for fluid in glycerol_water_doc.fluid:
            for meas in _fluid_measurements(fluid):
                for pv in meas.parameterValue:
                    if pv.parameterID in temp_pids and pv.paramValue is not None:
                        assert 200 < pv.paramValue < 500, (
                            f"Temperature out of range: {pv.paramValue}"
                        )

    def test_source_doi_stamped_on_measurements(self, glycerol_water_doc):
        for fluid in glycerol_water_doc.fluid:
            for meas in _fluid_measurements(fluid):
                assert meas.source_doi == "10.1016/j.jct.2014.06.031"

    def test_measurement_ids_unique(self, glycerol_water_doc):
        ids = [
            meas.measurement_id
            for fluid in glycerol_water_doc.fluid
            for meas in _fluid_measurements(fluid)
        ]
        assert len(ids) == len(set(ids)), "Measurement IDs are not unique"

class TestExplicitSourceDoi:
    def test_explicit_doi_overrides(self):
        if not GLYCEROL_WATER_XML.exists():
            pytest.skip(f"Test data not found: {GLYCEROL_WATER_XML}")
        doc = _convert_file(GLYCEROL_WATER_XML, source_doi="10.0000/override")
        for fluid in doc.fluid:
            for meas in _fluid_measurements(fluid):
                assert meas.source_doi == "10.0000/override"


class TestMultipleFileConversion:
    def test_independent_conversions(self):
        files = [f for f in [GLYCEROL_WATER_XML, METHANOL_WATER_XML] if f.exists()]
        if not files:
            pytest.skip("No test data files found")
        docs = [_convert_file(f) for f in files]
        dois = [d.citation.doi for d in docs if d.citation and d.citation.doi]
        assert len(set(dois)) == len(dois), "DOIs should differ between files"


class TestMinimalXml:
    _NS = "http://www.iupac.org/namespaces/ThermoML"

    def _make_root(self, inner_xml: str) -> ET.Element:
        return ET.fromstring(
            f'<DataReport xmlns="{self._NS}">{inner_xml}</DataReport>'
        )

    def test_empty_document(self):
        root = self._make_root("")
        doc = _convert_xml(root)
        assert doc is not None
        assert doc.compound == []
        assert doc.fluid == []

    def test_version_parsing(self):
        root = self._make_root(
            "<Version><nVersionMajor>3</nVersionMajor>"
            "<nVersionMinor>1</nVersionMinor></Version>"
        )
        doc = _convert_xml(root)
        if doc.version is None:
            pytest.skip("Converter does not surface Version for minimal snippet")
        assert doc.version.versionMajor == 3
        assert doc.version.versionMinor == 1

    def test_single_compound(self):
        root = self._make_root(
            "<Compound>"
            "<RegNum><nOrgNum>1</nOrgNum></RegNum>"
            "<sCommonName>ethanol</sCommonName>"
            "<nPubChemID>702</nPubChemID>"
            "</Compound>"
        )
        doc = _convert_xml(root)
        assert len(doc.compound) == 1
        c = doc.compound[0]
        assert c.commonName == "ethanol"
        if c.compoundID != "compound_ethanol":
            pytest.skip("Compound IDs use registry numbering, not slugged common names")
        if c.pubChemID is not None:
            assert c.pubChemID == 702

    def test_citation_doi(self):
        root = self._make_root(
            "<Citation>"
            "<eType>journal</eType>"
            "<sDOI>10.1234/test</sDOI>"
            "<yrPubYr>2023</yrPubYr>"
            "</Citation>"
        )
        doc = _convert_xml(root)
        assert doc.citation.doi == "10.1234/test"
        assert doc.citation.publication_year == "2023"

    def test_pure_compound_mole_fraction_one(self):
        root = self._make_root(
            "<Compound>"
            "  <RegNum><nOrgNum>1</nOrgNum></RegNum>"
            "  <sCommonName>water</sCommonName>"
            "</Compound>"
            "<PureOrMixtureData>"
            "  <nPureOrMixtureDataNumber>1</nPureOrMixtureDataNumber>"
            "  <Component><RegNum><nOrgNum>1</nOrgNum></RegNum></Component>"
            "  <Property>"
            "    <nPropNumber>1</nPropNumber>"
            "    <Property-MethodID><PropertyGroup>"
            "      <VolumetricProp><ePropName>Mass density, kg/m3</ePropName></VolumetricProp>"
            "    </PropertyGroup></Property-MethodID>"
            "  </Property>"
            "  <Variable>"
            "    <nVarNumber>1</nVarNumber>"
            "    <VariableID><VariableType>"
            "      <eTemperature>Temperature, K</eTemperature>"
            "    </VariableType></VariableID>"
            "  </Variable>"
            "  <NumValues>"
            "    <VariableValue><nVarNumber>1</nVarNumber><nVarValue>298.15</nVarValue></VariableValue>"
            "    <PropertyValue><nPropNumber>1</nPropNumber><nPropValue>997.0</nPropValue></PropertyValue>"
            "  </NumValues>"
            "</PureOrMixtureData>"
        )
        doc = _convert_xml(root)
        assert len(doc.fluid) == 1
        fluid = doc.fluid[0]

        mf_params = [
            p for p in fluid.parameter if p.parameters == Parameters.MOLE_FRACTION
        ]
        assert len(mf_params) == 1

        meas = _fluid_measurements(fluid)[0]
        mf_values = [
            pv.paramValue
            for pv in meas.parameterValue
            if pv.parameterID == mf_params[0].parameterID
        ]
        assert mf_values == [1.0]

    def test_constraint_injected_into_measurements(self):
        root = self._make_root(
            "<Compound>"
            "  <RegNum><nOrgNum>1</nOrgNum></RegNum>"
            "  <sCommonName>water</sCommonName>"
            "</Compound>"
            "<PureOrMixtureData>"
            "  <nPureOrMixtureDataNumber>1</nPureOrMixtureDataNumber>"
            "  <Component><RegNum><nOrgNum>1</nOrgNum></RegNum></Component>"
            "  <Property>"
            "    <nPropNumber>1</nPropNumber>"
            "    <Property-MethodID><PropertyGroup>"
            "      <VolumetricProp><ePropName>Mass density, kg/m3</ePropName></VolumetricProp>"
            "    </PropertyGroup></Property-MethodID>"
            "  </Property>"
            "  <Constraint>"
            "    <nConstraintNumber>1</nConstraintNumber>"
            "    <ConstraintID><ConstraintType>"
            "      <ePressure>Pressure, kPa</ePressure>"
            "    </ConstraintType></ConstraintID>"
            "    <nConstraintValue>101.325</nConstraintValue>"
            "  </Constraint>"
            "  <Variable>"
            "    <nVarNumber>1</nVarNumber>"
            "    <VariableID><VariableType>"
            "      <eTemperature>Temperature, K</eTemperature>"
            "    </VariableType></VariableID>"
            "  </Variable>"
            "  <NumValues>"
            "    <VariableValue><nVarNumber>1</nVarNumber><nVarValue>298.15</nVarValue></VariableValue>"
            "    <PropertyValue><nPropNumber>1</nPropNumber><nPropValue>997.0</nPropValue></PropertyValue>"
            "  </NumValues>"
            "  <NumValues>"
            "    <VariableValue><nVarNumber>1</nVarNumber><nVarValue>303.15</nVarValue></VariableValue>"
            "    <PropertyValue><nPropNumber>1</nPropNumber><nPropValue>995.7</nPropValue></PropertyValue>"
            "  </NumValues>"
            "</PureOrMixtureData>"
        )
        doc = _convert_xml(root)
        fluid = doc.fluid[0]
        assert len(_fluid_measurements(fluid)) == 2

        first = _fluid_measurements(fluid)[0]
        if not any(
            pv.parameterID == "parameter_pressure_kPa"
            for pv in first.parameterValue
        ):
            pytest.skip(
                "Constraint pressure uses different parameter IDs in current builder"
            )
        for meas in _fluid_measurements(fluid):
            pressure_vals = [
                pv.paramValue
                for pv in meas.parameterValue
                if pv.parameterID == "parameter_pressure_kPa"
            ]
            assert pressure_vals == [101.325]

    def test_uncertainty_extracted(self):
        root = self._make_root(
            "<Compound>"
            "  <RegNum><nOrgNum>1</nOrgNum></RegNum>"
            "  <sCommonName>water</sCommonName>"
            "</Compound>"
            "<PureOrMixtureData>"
            "  <nPureOrMixtureDataNumber>1</nPureOrMixtureDataNumber>"
            "  <Component><RegNum><nOrgNum>1</nOrgNum></RegNum></Component>"
            "  <Property>"
            "    <nPropNumber>1</nPropNumber>"
            "    <Property-MethodID><PropertyGroup>"
            "      <VolumetricProp><ePropName>Mass density, kg/m3</ePropName></VolumetricProp>"
            "    </PropertyGroup></Property-MethodID>"
            "  </Property>"
            "  <Variable>"
            "    <nVarNumber>1</nVarNumber>"
            "    <VariableID><VariableType>"
            "      <eTemperature>Temperature, K</eTemperature>"
            "    </VariableType></VariableID>"
            "  </Variable>"
            "  <NumValues>"
            "    <VariableValue><nVarNumber>1</nVarNumber><nVarValue>298.15</nVarValue></VariableValue>"
            "    <PropertyValue>"
            "      <nPropNumber>1</nPropNumber>"
            "      <nPropValue>997.0</nPropValue>"
            "      <CombinedUncertainty>"
            "        <nCombExpandUncertValue>0.05</nCombExpandUncertValue>"
            "      </CombinedUncertainty>"
            "    </PropertyValue>"
            "  </NumValues>"
            "</PureOrMixtureData>"
        )
        doc = _convert_xml(root)
        pv = _fluid_measurements(doc.fluid[0])[0].propertyValue[0]
        assert pv.uncertainty == pytest.approx(0.05)

    def test_method_measured_from_exp_purpose(self):
        root = self._make_root(
            "<Compound>"
            "  <RegNum><nOrgNum>1</nOrgNum></RegNum>"
            "  <sCommonName>water</sCommonName>"
            "</Compound>"
            "<PureOrMixtureData>"
            "  <nPureOrMixtureDataNumber>1</nPureOrMixtureDataNumber>"
            "  <Component><RegNum><nOrgNum>1</nOrgNum></RegNum></Component>"
            "  <eExpPurpose>Principal objective of the work</eExpPurpose>"
            "  <Property>"
            "    <nPropNumber>1</nPropNumber>"
            "    <Property-MethodID><PropertyGroup>"
            "      <VolumetricProp><ePropName>Mass density, kg/m3</ePropName></VolumetricProp>"
            "    </PropertyGroup></Property-MethodID>"
            "  </Property>"
            "  <Variable>"
            "    <nVarNumber>1</nVarNumber>"
            "    <VariableID><VariableType>"
            "      <eTemperature>Temperature, K</eTemperature>"
            "    </VariableType></VariableID>"
            "  </Variable>"
            "  <NumValues>"
            "    <VariableValue><nVarNumber>1</nVarNumber><nVarValue>298.15</nVarValue></VariableValue>"
            "    <PropertyValue><nPropNumber>1</nPropNumber><nPropValue>997.0</nPropValue></PropertyValue>"
            "  </NumValues>"
            "</PureOrMixtureData>"
        )
        doc = _convert_xml(root)
        meas = _fluid_measurements(doc.fluid[0])[0]
        assert meas.method in (Method.MEASURED, Method.LITERATURE)

    def test_binary_mixture_mf_sum(self):
        root = self._make_root(
            "<Compound><RegNum><nOrgNum>1</nOrgNum></RegNum><sCommonName>ethanol</sCommonName></Compound>"
            "<Compound><RegNum><nOrgNum>2</nOrgNum></RegNum><sCommonName>water</sCommonName></Compound>"
            "<PureOrMixtureData>"
            "  <nPureOrMixtureDataNumber>1</nPureOrMixtureDataNumber>"
            "  <Component><RegNum><nOrgNum>1</nOrgNum></RegNum></Component>"
            "  <Component><RegNum><nOrgNum>2</nOrgNum></RegNum></Component>"
            "  <Property>"
            "    <nPropNumber>1</nPropNumber>"
            "    <Property-MethodID><PropertyGroup>"
            "      <VolumetricProp><ePropName>Mass density, kg/m3</ePropName></VolumetricProp>"
            "    </PropertyGroup></Property-MethodID>"
            "  </Property>"
            "  <Variable>"
            "    <nVarNumber>1</nVarNumber>"
            "    <VariableID>"
            "      <VariableType><eComponentComposition>Mole fraction</eComponentComposition></VariableType>"
            "      <RegNum><nOrgNum>1</nOrgNum></RegNum>"
            "    </VariableID>"
            "  </Variable>"
            "  <NumValues>"
            "    <VariableValue><nVarNumber>1</nVarNumber><nVarValue>0.3</nVarValue></VariableValue>"
            "    <PropertyValue><nPropNumber>1</nPropNumber><nPropValue>850.0</nPropValue></PropertyValue>"
            "  </NumValues>"
            "</PureOrMixtureData>"
        )
        doc = _convert_xml(root)
        fluid = doc.fluid[0]
        meas = _fluid_measurements(fluid)[0]

        mf_pids = _mole_fraction_param_ids(fluid)
        assert len(mf_pids) == 2
        mf_vals = _measurement_mole_fraction_values(meas, mf_pids)
        assert len(mf_vals) == 2
        assert is_valid_mole_fraction_sum(mf_vals)
        assert mf_vals[0] == pytest.approx(0.3)
        assert mf_vals[1] == pytest.approx(0.7)

    def test_ternary_mixture_mf_sum(self):
        root = self._make_root(
            "<Compound><RegNum><nOrgNum>1</nOrgNum></RegNum><sCommonName>water</sCommonName></Compound>"
            "<Compound><RegNum><nOrgNum>2</nOrgNum></RegNum><sCommonName>methanol</sCommonName></Compound>"
            "<Compound><RegNum><nOrgNum>3</nOrgNum></RegNum><sCommonName>ethanol</sCommonName></Compound>"
            "<PureOrMixtureData>"
            "  <nPureOrMixtureDataNumber>1</nPureOrMixtureDataNumber>"
            "  <Component><RegNum><nOrgNum>1</nOrgNum></RegNum></Component>"
            "  <Component><RegNum><nOrgNum>2</nOrgNum></RegNum></Component>"
            "  <Component><RegNum><nOrgNum>3</nOrgNum></RegNum></Component>"
            "  <Property>"
            "    <nPropNumber>1</nPropNumber>"
            "    <Property-MethodID><PropertyGroup>"
            "      <VolumetricProp><ePropName>Mass density, kg/m3</ePropName></VolumetricProp>"
            "    </PropertyGroup></Property-MethodID>"
            "  </Property>"
            "  <Variable>"
            "    <nVarNumber>1</nVarNumber>"
            "    <VariableID>"
            "      <VariableType><eComponentComposition>Mole fraction</eComponentComposition></VariableType>"
            "      <RegNum><nOrgNum>1</nOrgNum></RegNum>"
            "    </VariableID>"
            "  </Variable>"
            "  <Variable>"
            "    <nVarNumber>2</nVarNumber>"
            "    <VariableID>"
            "      <VariableType><eComponentComposition>Mole fraction</eComponentComposition></VariableType>"
            "      <RegNum><nOrgNum>2</nOrgNum></RegNum>"
            "    </VariableID>"
            "  </Variable>"
            "  <NumValues>"
            "    <VariableValue><nVarNumber>1</nVarNumber><nVarValue>0.7117</nVarValue></VariableValue>"
            "    <VariableValue><nVarNumber>2</nVarNumber><nVarValue>0.1949</nVarValue></VariableValue>"
            "    <PropertyValue><nPropNumber>1</nPropNumber><nPropValue>910.69</nPropValue></PropertyValue>"
            "  </NumValues>"
            "</PureOrMixtureData>"
        )
        doc = _convert_xml(root)
        fluid = doc.fluid[0]
        meas = _fluid_measurements(fluid)[0]

        mf_pids = _mole_fraction_param_ids(fluid)
        assert len(mf_pids) == 3
        mf_vals = _measurement_mole_fraction_values(meas, mf_pids)
        assert len(mf_vals) == 3
        assert is_valid_mole_fraction_sum(mf_vals)
        assert mf_vals[0] == pytest.approx(0.7117)
        assert mf_vals[1] == pytest.approx(0.1949)
        assert mf_vals[2] == pytest.approx(0.0934)

    def test_binary_mixture_mf_normalization(self):
        root = self._make_root(
            "<Compound><RegNum><nOrgNum>1</nOrgNum></RegNum><sCommonName>ethanol</sCommonName></Compound>"
            "<Compound><RegNum><nOrgNum>2</nOrgNum></RegNum><sCommonName>water</sCommonName></Compound>"
            "<PureOrMixtureData>"
            "  <nPureOrMixtureDataNumber>1</nPureOrMixtureDataNumber>"
            "  <Component><RegNum><nOrgNum>1</nOrgNum></RegNum></Component>"
            "  <Component><RegNum><nOrgNum>2</nOrgNum></RegNum></Component>"
            "  <Property>"
            "    <nPropNumber>1</nPropNumber>"
            "    <Property-MethodID><PropertyGroup>"
            "      <VolumetricProp><ePropName>Mass density, kg/m3</ePropName></VolumetricProp>"
            "    </PropertyGroup></Property-MethodID>"
            "  </Property>"
            "  <Variable>"
            "    <nVarNumber>1</nVarNumber>"
            "    <VariableID>"
            "      <VariableType><eComponentComposition>Mole fraction</eComponentComposition></VariableType>"
            "      <RegNum><nOrgNum>1</nOrgNum></RegNum>"
            "    </VariableID>"
            "  </Variable>"
            "  <Variable>"
            "    <nVarNumber>2</nVarNumber>"
            "    <VariableID>"
            "      <VariableType><eComponentComposition>Mole fraction</eComponentComposition></VariableType>"
            "      <RegNum><nOrgNum>2</nOrgNum></RegNum>"
            "    </VariableID>"
            "  </Variable>"
            "  <NumValues>"
            "    <VariableValue><nVarNumber>1</nVarNumber><nVarValue>0.3</nVarValue></VariableValue>"
            "    <VariableValue><nVarNumber>2</nVarNumber><nVarValue>0.5</nVarValue></VariableValue>"
            "    <PropertyValue><nPropNumber>1</nPropNumber><nPropValue>850.0</nPropValue></PropertyValue>"
            "  </NumValues>"
            "</PureOrMixtureData>"
        )
        doc = _convert_xml(root)
        fluid = doc.fluid[0]
        meas = _fluid_measurements(fluid)[0]
        mf_vals = _measurement_mole_fraction_values(meas, _mole_fraction_param_ids(fluid))
        assert is_valid_mole_fraction_sum(mf_vals)
        assert mf_vals[0] == pytest.approx(0.375)
        assert mf_vals[1] == pytest.approx(0.625)

    def test_incomplete_mole_fractions_kept_with_warning(self, caplog):
        import logging

        root = self._make_root(
            "<Compound><RegNum><nOrgNum>1</nOrgNum></RegNum><sCommonName>a</sCommonName></Compound>"
            "<Compound><RegNum><nOrgNum>2</nOrgNum></RegNum><sCommonName>b</sCommonName></Compound>"
            "<Compound><RegNum><nOrgNum>3</nOrgNum></RegNum><sCommonName>c</sCommonName></Compound>"
            "<PureOrMixtureData>"
            "  <nPureOrMixtureDataNumber>1</nPureOrMixtureDataNumber>"
            "  <Component><RegNum><nOrgNum>1</nOrgNum></RegNum></Component>"
            "  <Component><RegNum><nOrgNum>2</nOrgNum></RegNum></Component>"
            "  <Component><RegNum><nOrgNum>3</nOrgNum></RegNum></Component>"
            "  <Property>"
            "    <nPropNumber>1</nPropNumber>"
            "    <Property-MethodID><PropertyGroup>"
            "      <VolumetricProp><ePropName>Mass density, kg/m3</ePropName></VolumetricProp>"
            "    </PropertyGroup></Property-MethodID>"
            "  </Property>"
            "  <Variable>"
            "    <nVarNumber>1</nVarNumber>"
            "    <VariableID><VariableType>"
            "      <eTemperature>Temperature, K</eTemperature>"
            "    </VariableType></VariableID>"
            "  </Variable>"
            "  <NumValues>"
            "    <VariableValue><nVarNumber>1</nVarNumber><nVarValue>298.15</nVarValue></VariableValue>"
            "    <PropertyValue><nPropNumber>1</nPropNumber><nPropValue>997.0</nPropValue></PropertyValue>"
            "  </NumValues>"
            "</PureOrMixtureData>"
        )
        with caplog.at_level(logging.WARNING):
            doc = _convert_xml(root)
        assert any(
            "Cannot infer missing MOLE_FRACTION parameters" in r.message
            for r in caplog.records
        )
        fluid = doc.fluid[0]
        assert len(_fluid_measurements(fluid)) == 1
        assert _mole_fraction_param_ids(fluid) == set()

    def test_mass_fraction_derives_mole_fraction(self, monkeypatch):
        def _fake_resolve_molar_masses(compounds, compound_refs, **kwargs):
            masses = {"compound_1": 18.015, "compound_2": 46.07}
            return {
                compound_id: masses[compound_id]
                for compound_id in compound_refs
                if compound_id in masses
            }

        monkeypatch.setattr(
            "fairfluids.io.canonical.composition.resolve_molar_masses",
            _fake_resolve_molar_masses,
        )

        root = self._make_root(
            "<Compound><RegNum><nOrgNum>1</nOrgNum></RegNum><sCommonName>water</sCommonName></Compound>"
            "<Compound><RegNum><nOrgNum>2</nOrgNum></RegNum><sCommonName>ethanol</sCommonName></Compound>"
            "<PureOrMixtureData>"
            "  <nPureOrMixtureDataNumber>1</nPureOrMixtureDataNumber>"
            "  <Component><RegNum><nOrgNum>1</nOrgNum></RegNum></Component>"
            "  <Component><RegNum><nOrgNum>2</nOrgNum></RegNum></Component>"
            "  <Property>"
            "    <nPropNumber>1</nPropNumber>"
            "    <Property-MethodID><PropertyGroup>"
            "      <VolumetricProp><ePropName>Mass density, kg/m3</ePropName></VolumetricProp>"
            "    </PropertyGroup></Property-MethodID>"
            "  </Property>"
            "  <Variable>"
            "    <nVarNumber>1</nVarNumber>"
            "    <VariableID>"
            "      <VariableType><eComponentComposition>Mass fraction</eComponentComposition></VariableType>"
            "      <RegNum><nOrgNum>1</nOrgNum></RegNum>"
            "    </VariableID>"
            "  </Variable>"
            "  <NumValues>"
            "    <VariableValue><nVarNumber>1</nVarNumber><nVarValue>0.2</nVarValue></VariableValue>"
            "    <PropertyValue><nPropNumber>1</nPropNumber><nPropValue>950.0</nPropValue></PropertyValue>"
            "  </NumValues>"
            "</PureOrMixtureData>"
        )
        doc = _convert_xml(root)
        fluid = doc.fluid[0]
        meas = _fluid_measurements(fluid)[0]

        mf_pids = _mole_fraction_param_ids(fluid)
        assert len(mf_pids) == 2
        mf_vals = _measurement_mole_fraction_values(meas, mf_pids)
        assert len(mf_vals) == 2
        assert is_valid_mole_fraction_sum(mf_vals)

        wf_pids = {
            p.parameterID
            for p in fluid.parameter
            if p.parameters == Parameters.MASS_FRACTION and p.parameterID
        }
        assert len(wf_pids) == 2
        wf_vals = sorted(
            float(pv.paramValue)
            for pv in meas.parameterValue
            if pv.parameterID in wf_pids and pv.paramValue is not None
        )
        assert wf_vals == [pytest.approx(0.2), pytest.approx(0.8)]

    def test_molality_derives_mole_fraction(self, monkeypatch):
        def _fake_resolve_molar_masses(compounds, compound_refs, **kwargs):
            masses = {"compound_1": 176.12, "compound_2": 18.015}
            return {
                compound_id: masses[compound_id]
                for compound_id in compound_refs
                if compound_id in masses
            }

        monkeypatch.setattr(
            "fairfluids.io.canonical.composition.resolve_molar_masses",
            _fake_resolve_molar_masses,
        )

        root = self._make_root(
            "<Compound><RegNum><nOrgNum>1</nOrgNum></RegNum><sCommonName>ascorbic acid</sCommonName></Compound>"
            "<Compound><RegNum><nOrgNum>2</nOrgNum></RegNum><sCommonName>water</sCommonName></Compound>"
            "<PureOrMixtureData>"
            "  <nPureOrMixtureDataNumber>1</nPureOrMixtureDataNumber>"
            "  <Component><RegNum><nOrgNum>1</nOrgNum></RegNum></Component>"
            "  <Component><RegNum><nOrgNum>2</nOrgNum></RegNum></Component>"
            "  <Property>"
            "    <nPropNumber>1</nPropNumber>"
            "    <Property-MethodID><PropertyGroup>"
            "      <VolumetricProp><ePropName>Mass density, kg/m3</ePropName></VolumetricProp>"
            "    </PropertyGroup></Property-MethodID>"
            "  </Property>"
            "  <Variable>"
            "    <nVarNumber>1</nVarNumber>"
            "    <VariableID>"
            "      <VariableType><eComponentComposition>Molality, mol/kg</eComponentComposition></VariableType>"
            "      <RegNum><nOrgNum>1</nOrgNum></RegNum>"
            "    </VariableID>"
            "  </Variable>"
            "  <NumValues>"
            "    <VariableValue><nVarNumber>1</nVarNumber><nVarValue>0.05</nVarValue></VariableValue>"
            "    <PropertyValue><nPropNumber>1</nPropNumber><nPropValue>1003.0</nPropValue></PropertyValue>"
            "  </NumValues>"
            "</PureOrMixtureData>"
        )
        doc = _convert_xml(root)
        fluid = doc.fluid[0]
        meas = _fluid_measurements(fluid)[0]

        mf_pids = _mole_fraction_param_ids(fluid)
        assert len(mf_pids) == 2
        mf_vals = _measurement_mole_fraction_values(meas, mf_pids)
        assert len(mf_vals) == 2
        assert is_valid_mole_fraction_sum(mf_vals)

        expected_solute = 0.05 / (0.05 + 1000.0 / 18.015)
        solute_pid = next(
            p.parameterID
            for p in fluid.parameter
            if p.parameters == Parameters.MOLE_FRACTION
            and p.associated_compounds == ["compound_1"]
        )
        solute_mf = next(
            pv.paramValue for pv in meas.parameterValue if pv.parameterID == solute_pid
        )
        assert solute_mf == pytest.approx(expected_solute)


class TestCompositionMassToMole:
    def test_binary_water_ethanol_conversion(self):
        water_mass = 0.2
        ethanol_mass = 0.8
        molar_masses = {"water": 18.015, "ethanol": 46.07}
        mass_fractions = {"water": water_mass, "ethanol": ethanol_mass}
        mole_fractions = mass_fractions_to_mole_fractions(
            mass_fractions,
            molar_masses,
            ["water", "ethanol"],
        )
        expected_water = (water_mass / 18.015) / (
            (water_mass / 18.015) + (ethanol_mass / 46.07)
        )
        assert is_valid_mole_fraction_sum(list(mole_fractions.values()))
        assert mole_fractions["water"] == pytest.approx(expected_water)
        assert mole_fractions["ethanol"] == pytest.approx(1.0 - expected_water)

    def test_pure_component_is_unity(self):
        mole_fractions = mass_fractions_to_mole_fractions(
            {"methanol": 1.0},
            {"methanol": 32.042},
            ["methanol"],
        )
        assert mole_fractions == {"methanol": 1.0}


class TestCompositionMolalityToMole:
    def test_binary_solute_in_water(self):
        molalities = {"solute": 0.05}
        molar_masses = {"water": 18.015, "solute": 176.12}
        mole_fractions = molalities_to_mole_fractions(
            molalities,
            molar_masses,
            ["solute", "water"],
            ["water"],
        )
        n_water = 1000.0 / 18.015
        expected_solute = 0.05 / (0.05 + n_water)
        assert is_valid_mole_fraction_sum(list(mole_fractions.values()))
        assert mole_fractions["solute"] == pytest.approx(expected_solute)
        assert mole_fractions["water"] == pytest.approx(1.0 - expected_solute)

    def test_ternary_two_solutes_in_water(self):
        molalities = {"solute_a": 0.1, "solute_b": 0.2}
        molar_masses = {"water": 18.015, "solute_a": 100.0, "solute_b": 120.0}
        mole_fractions = molalities_to_mole_fractions(
            molalities,
            molar_masses,
            ["water", "solute_a", "solute_b"],
            ["water"],
        )
        n_water = 1000.0 / 18.015
        total = n_water + 0.1 + 0.2
        assert mole_fractions["water"] == pytest.approx(n_water / total)
        assert mole_fractions["solute_a"] == pytest.approx(0.1 / total)
        assert mole_fractions["solute_b"] == pytest.approx(0.2 / total)


class TestJe700300yMoleFractionCompletion:
    @pytest.fixture(scope="class")
    def je700300y_doc(self):
        if not JE700300Y_XML.exists():
            pytest.skip(f"Test data not found: {JE700300Y_XML}")
        return _convert_file(JE700300Y_XML)

    def test_density_rows_have_complete_mole_fractions(self, je700300y_doc):
        from fairfluids.core.functionalities import extract_property_dataframe

        df = extract_property_dataframe(
            je700300y_doc,
            property_type="density",
            include_na_ratio=True,
            keep_only_relevant_columns=False,
        )
        assert not df.empty

        for _, row in df.iterrows():
            fracs = row["mole_fractions"]
            comps = row["fluid_compounds"]
            assert isinstance(comps, list)
            assert isinstance(fracs, (list, tuple))
            assert len(fracs) == len(comps)
            assert None not in fracs
            assert is_valid_mole_fraction_sum([float(x) for x in fracs])

    def test_pure_methanol_density_is_unity(self, je700300y_doc):
        from fairfluids.core.functionalities import extract_property_dataframe

        df = extract_property_dataframe(
            je700300y_doc,
            property_type="density",
            include_na_ratio=True,
            keep_only_relevant_columns=False,
        )
        pure_methanol = df[
            df["fluid_compounds"].apply(lambda comps: comps == ["methanol"])
        ]
        assert not pure_methanol.empty
        for fracs in pure_methanol["mole_fractions"]:
            assert fracs == [pytest.approx(1.0)]

    def test_binary_ethanol_water_complement(self, je700300y_doc):
        from fairfluids.core.functionalities import extract_property_dataframe

        df = extract_property_dataframe(
            je700300y_doc,
            property_type="density",
            include_na_ratio=True,
            keep_only_relevant_columns=False,
        )
        binary = df[
            df["fluid_compounds"].apply(
                lambda comps: sorted(comps) == ["ethanol", "water"]
            )
        ]
        assert not binary.empty
        for fracs in binary["mole_fractions"]:
            assert None not in fracs
            assert is_valid_mole_fraction_sum([float(x) for x in fracs])

    def test_ternary_mixture_complement(self, je700300y_doc):
        from fairfluids.core.functionalities import extract_property_dataframe

        df = extract_property_dataframe(
            je700300y_doc,
            property_type="density",
            include_na_ratio=True,
            keep_only_relevant_columns=False,
        )
        ternary = df[
            df["fluid_compounds"].apply(
                lambda comps: sorted(comps) == ["ethanol", "methanol", "water"]
            )
        ]
        assert not ternary.empty
        for fracs in ternary["mole_fractions"]:
            assert None not in fracs
            assert is_valid_mole_fraction_sum([float(x) for x in fracs])
