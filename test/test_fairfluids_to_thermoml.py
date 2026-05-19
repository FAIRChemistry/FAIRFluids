from fairfluids.io.fairfluids_to_thermoml.converter import convert
from fairfluids.io.thermoml_to_fairfluids.parser import parse


def test_convert_minimal_fairfluids_to_thermoml():
    ff_doc = {
        "citation": {
            "title": "Example dataset",
            "doi": "10.1000/example",
            "pub_name": "Journal",
            "publication_year": "2024",
            "author": [{"family_name": "Doe", "given_name": "J."}],
            "litType": "journal",
        },
        "compound": [
            {
                "compoundID": "compound_1",
                "commonName": "water",
                "standard_InChI": "InChI=1S/H2O/h1H2",
                "standard_InChI_key": "XLYOFNOQVPJJNP-UHFFFAOYSA-N",
            }
        ],
        "fluid": [
            {
                "fluidID": ["fluid_1"],
                "compounds": ["compound_1"],
                "property": [
                    {
                        "propertyID": "property_1",
                        "properties": "density",
                        "unit": {"name": "kilogram per cubic meter"},
                    }
                ],
                "parameter": [
                    {
                        "parameterID": "parameter_1",
                        "parameters": "Temperature",
                        "unit": {"name": "kelvin"},
                    },
                    {
                        "parameterID": "parameter_2",
                        "parameters": "Pressure",
                        "unit": {"name": "kilopascal"},
                    },
                ],
                "sample": {
                    "measurement": [
                        {
                            "propertyValue": [
                                {
                                    "propertyID": "property_1",
                                    "propValue": 997.1,
                                    "uncertainty": 0.2,
                                }
                            ],
                            "parameterValue": [
                                {"parameterID": "parameter_1", "paramValue": 298.15},
                                {"parameterID": "parameter_2", "paramValue": 101.325},
                            ],
                        },
                        {
                            "propertyValue": [
                                {"propertyID": "property_1", "propValue": 995.6}
                            ],
                            "parameterValue": [
                                {"parameterID": "parameter_1", "paramValue": 303.15},
                                {"parameterID": "parameter_2", "paramValue": 101.325},
                            ],
                        },
                    ]
                },
            }
        ],
    }

    xml = convert(ff_doc)
    assert "<DataReport" in xml
    assert "PureOrMixtureData" in xml

    parsed = parse_from_xml_string(xml)
    assert len(parsed.compounds) == 1
    assert len(parsed.datasets) == 1
    ds = parsed.datasets[0]
    assert len(ds.properties) == 1
    assert len(ds.variables) == 1
    assert len(ds.constraints) == 1
    assert len(ds.num_values) == 2
    assert ds.properties[0].prop_name.startswith("Mass density")


def parse_from_xml_string(xml: str):
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "out.xml"
        path.write_text(xml, encoding="utf-8")
        return parse(path)
