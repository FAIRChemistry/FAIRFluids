#!/usr/bin/env python3
"""
Script to import FAIRFluids knowledge graph into Neo4j for complex graph queries.
Graph structure: Experiments (Measurements) are the central nodes.
Each Experiment connects to Compounds, Properties, and Citations.
"""

import json
import os
import argparse
from pathlib import Path
from neo4j import GraphDatabase
import pandas as pd
from collections import defaultdict
import time
from fairfluids.core.lib import Properties, Parameters, Method, LitType

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


class FAIRFluidsNeo4jImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.id_counter = 0

    def close(self):
        self.driver.close()

    @staticmethod
    def _parameter_field_key(parameter_name: str) -> str:
        """Build a stable experiment property key from a parameter name."""
        safe_name = "".join(
            ch.lower() if ch.isalnum() else "_" for ch in str(parameter_name)
        )
        while "__" in safe_name:
            safe_name = safe_name.replace("__", "_")
        return safe_name.strip("_")

    @staticmethod
    def _is_non_empty_value(value) -> bool:
        """Return True when a value is meaningfully populated."""
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip() != ""
        if isinstance(value, (list, tuple, set, dict)):
            return len(value) > 0
        return True

    def _build_sample_context(self, sample_entry):
        """
        Build flat, non-empty sample metadata that can be attached to Experiment nodes.
        Nested sample sub-blocks are serialized to JSON strings.
        """
        if not isinstance(sample_entry, dict):
            return {}

        sample_context = {}
        sample_id = sample_entry.get("sample_id")
        if self._is_non_empty_value(sample_id):
            sample_context["sample_id"] = sample_id

        associated_compounds = sample_entry.get("associated_compounds")
        if self._is_non_empty_value(associated_compounds):
            sample_context["sample_associated_compounds"] = associated_compounds

        for block_name in ["storage", "preparation", "vendor_chemical"]:
            block_value = sample_entry.get(block_name)
            if self._is_non_empty_value(block_value):
                sample_context[f"sample_{block_name}_json"] = json.dumps(
                    block_value, ensure_ascii=True, sort_keys=True
                )

        return sample_context

    def clear_database(self):
        """Clear existing data."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("🗑️  Cleared existing database")

    def create_constraints(self):
        """Create constraints for better performance."""
        with self.driver.session() as session:
            # Drop legacy composite property constraints and keep semantic
            # uniqueness on propertyType.
            try:
                existing_constraints = session.run(
                    "SHOW CONSTRAINTS YIELD name, labelsOrTypes, properties "
                    "RETURN name, labelsOrTypes, properties"
                )
                for record in existing_constraints:
                    labels_or_types = record.get("labelsOrTypes") or []
                    properties = record.get("properties") or []
                    if labels_or_types == ["Property"] and properties != [
                        "propertyType"
                    ]:
                        constraint_name = record.get("name")
                        if constraint_name:
                            escaped_name = constraint_name.replace("`", "``")
                            session.run(f"DROP CONSTRAINT `{escaped_name}` IF EXISTS")
                            print(
                                f"🧹 Dropped legacy Property constraint: {constraint_name}"
                            )
            except Exception as e:
                print(f"⚠️  Could not inspect/drop legacy constraints: {e}")

            # Create constraints
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Experiment) REQUIRE e.experiment_id IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Compound) REQUIRE c.pubChemID IS UNIQUE"
            )
            # Also create constraint for compoundID as fallback (for compounds without pubChemID)
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Compound) REQUIRE c.compoundID IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Property) REQUIRE p.propertyType IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (param:Parameter) REQUIRE param.parameter IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (u:Unit) REQUIRE u.unitID IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (cit:Citation) REQUIRE cit.doi IS UNIQUE"
            )
            print("🔒 Created database constraints")

    def _bulk_create_compounds(self, session, compounds_batch):
        """Bulk create compounds using UNWIND."""
        if not compounds_batch:
            return

        # Separate compounds with and without pubChemID
        compounds_with_pubchem = []
        compounds_without_pubchem = []

        for comp in compounds_batch:
            if comp.get("pubChemID") and comp["pubChemID"] > 0:
                compounds_with_pubchem.append(comp)
            else:
                compounds_without_pubchem.append(comp)

        # Bulk insert compounds with pubChemID
        if compounds_with_pubchem:
            session.run(
                """
                UNWIND $compounds AS compound
                MERGE (c:Compound {pubChemID: compound.pubChemID})
                SET c.compoundID = compound.compoundID,
                    c.commonName = CASE WHEN c.commonName IS NULL OR c.commonName = '' 
                                       THEN compound.commonName ELSE c.commonName END,
                    c.name_IUPAC = CASE WHEN c.name_IUPAC IS NULL OR c.name_IUPAC = '' 
                                       THEN compound.name_IUPAC ELSE c.name_IUPAC END,
                    c.standard_InChI = CASE WHEN c.standard_InChI IS NULL OR c.standard_InChI = '' 
                                           THEN compound.standard_InChI ELSE c.standard_InChI END,
                    c.standard_InChI_key = CASE WHEN c.standard_InChI_key IS NULL OR c.standard_InChI_key = '' 
                                                THEN compound.standard_InChI_key ELSE c.standard_InChI_key END,
                    c.molar_weigth = CASE WHEN c.molar_weigth IS NULL 
                                         THEN compound.molar_weigth ELSE c.molar_weigth END,
                    c.SELFIE = CASE WHEN c.SELFIE IS NULL OR c.SELFIE = '' 
                                   THEN compound.SELFIE ELSE c.SELFIE END,
                    c.smiles_code = CASE WHEN c.smiles_code IS NULL OR c.smiles_code = '' 
                                         THEN compound.smiles_code ELSE c.smiles_code END,
                    c.sigman_profile = CASE WHEN c.sigman_profile IS NULL 
                                           THEN compound.sigman_profile ELSE c.sigman_profile END
            """,
                compounds=compounds_with_pubchem,
            )

        # Bulk insert compounds without pubChemID
        if compounds_without_pubchem:
            session.run(
                """
                UNWIND $compounds AS compound
                MERGE (c:Compound {compoundID: compound.compoundID})
                SET c.commonName = CASE WHEN c.commonName IS NULL OR c.commonName = '' 
                                       THEN compound.commonName ELSE c.commonName END,
                    c.name_IUPAC = CASE WHEN c.name_IUPAC IS NULL OR c.name_IUPAC = '' 
                                       THEN compound.name_IUPAC ELSE c.name_IUPAC END,
                    c.pubChemID = CASE WHEN c.pubChemID IS NULL OR c.pubChemID = 0 
                                      THEN compound.pubChemID ELSE c.pubChemID END,
                    c.standard_InChI = CASE WHEN c.standard_InChI IS NULL OR c.standard_InChI = '' 
                                           THEN compound.standard_InChI ELSE c.standard_InChI END,
                    c.standard_InChI_key = CASE WHEN c.standard_InChI_key IS NULL OR c.standard_InChI_key = '' 
                                                THEN compound.standard_InChI_key ELSE c.standard_InChI_key END,
                    c.molar_weigth = CASE WHEN c.molar_weigth IS NULL 
                                         THEN compound.molar_weigth ELSE c.molar_weigth END,
                    c.SELFIE = CASE WHEN c.SELFIE IS NULL OR c.SELFIE = '' 
                                   THEN compound.SELFIE ELSE c.SELFIE END,
                    c.smiles_code = CASE WHEN c.smiles_code IS NULL OR c.smiles_code = '' 
                                         THEN compound.smiles_code ELSE c.smiles_code END,
                    c.sigman_profile = CASE WHEN c.sigman_profile IS NULL 
                                           THEN compound.sigman_profile ELSE c.sigman_profile END
            """,
                compounds=compounds_without_pubchem,
            )

    def _bulk_create_units(self, session, units_batch):
        """Bulk create units using UNWIND."""
        if not units_batch:
            return
        session.run(
            """
            UNWIND $units AS unit
            MERGE (u:Unit {unitID: unit.unitID})
            SET u.name = unit.name
        """,
            units=units_batch,
        )

    def _bulk_create_citations(self, session, citations_batch):
        """Bulk create citations using UNWIND."""
        if not citations_batch:
            return
        session.run(
            """
            UNWIND $citations AS citation
            MERGE (cit:Citation {doi: citation.doi})
            SET cit.title = citation.title,
                cit.pub_name = citation.pub_name,
                cit.publication_year = citation.publication_year,
                cit.litType = citation.litType,
                cit.litType_enum = citation.litType_enum,
                cit.page = citation.page,
                cit.lit_volume_num = citation.lit_volume_num,
                cit.url_citation = citation.url_citation
        """,
            citations=citations_batch,
        )

    def _bulk_create_properties(self, session, properties_batch):
        """Bulk create properties using UNWIND."""
        if not properties_batch:
            return
        session.run(
            """
            UNWIND $properties AS prop
            MERGE (p:Property {propertyType: prop.propertyType})
            SET p.properties = prop.properties_str
        """,
            properties=properties_batch,
        )

    def _bulk_create_parameters(self, session, parameters_batch):
        """Bulk create parameters using UNWIND."""
        if not parameters_batch:
            return
        session.run(
            """
            UNWIND $parameters AS param
            MERGE (p:Parameter {parameter: param.parameter_str})
            SET p.associated_compounds = param.associated_compounds
        """,
            parameters={"parameters": parameters_batch},
        )

    def _bulk_create_experiments(self, session, experiments_batch):
        """Bulk create experiments using UNWIND."""
        if not experiments_batch:
            return

        # First create base experiment nodes
        session.run(
            """
            UNWIND $experiments AS exp
            MERGE (e:Experiment {experiment_id: exp.experiment_id})
            SET e.source_doi = exp.source_doi,
                e.method = exp.method,
                e.method_description = exp.method_description,
                e.source_file = exp.source_file,
                e.fluid_index = exp.fluid_index,
                e.fluidID = exp.fluidID
        """,
            experiments=experiments_batch,
        )

        # Then update dynamic properties in batches (group by experiment_id)
        for exp in experiments_batch:
            dynamic_props = exp.get("dynamic_props", {})
            if dynamic_props:
                set_clauses = []
                query_params = {"experiment_id": exp["experiment_id"]}
                for key, value in dynamic_props.items():
                    safe_key = key.replace("`", "\\`")
                    param_name = f"val_{len(set_clauses)}"
                    set_clauses.append(f"e.`{safe_key}` = ${param_name}")
                    query_params[param_name] = value

                if set_clauses:
                    session.run(
                        f"""
                        MATCH (e:Experiment {{experiment_id: $experiment_id}})
                        SET {', '.join(set_clauses)}
                    """,
                        **query_params,
                    )

    def _bulk_create_relationships(self, session, relationships):
        """Bulk create relationships using UNWIND."""
        # HAS_COMPOUND relationships
        has_compound = relationships.get("HAS_COMPOUND", [])
        if has_compound:
            # Separate by whether they have mole_fraction
            with_mole_frac = [
                r for r in has_compound if r.get("mole_fraction") is not None
            ]
            without_mole_frac = [
                r for r in has_compound if r.get("mole_fraction") is None
            ]

            if with_mole_frac:
                # Group by matching strategy (pubChemID vs compoundID)
                with_pubchem = [r for r in with_mole_frac if r.get("pubChemID")]
                without_pubchem = [r for r in with_mole_frac if not r.get("pubChemID")]

                if with_pubchem:
                    session.run(
                        """
                        UNWIND $relationships AS rel
                        MATCH (e:Experiment {experiment_id: rel.experiment_id})
                        MATCH (c:Compound {pubChemID: rel.pubChemID})
                        MERGE (e)-[r:HAS_COMPOUND]->(c)
                        SET r.mole_fraction = rel.mole_fraction
                    """,
                        relationships=with_pubchem,
                    )

                if without_pubchem:
                    session.run(
                        """
                        UNWIND $relationships AS rel
                        MATCH (e:Experiment {experiment_id: rel.experiment_id})
                        MATCH (c:Compound {compoundID: rel.compound_id})
                        MERGE (e)-[r:HAS_COMPOUND]->(c)
                        SET r.mole_fraction = rel.mole_fraction
                    """,
                        relationships=without_pubchem,
                    )

            if without_mole_frac:
                with_pubchem = [r for r in without_mole_frac if r.get("pubChemID")]
                without_pubchem = [
                    r for r in without_mole_frac if not r.get("pubChemID")
                ]

                if with_pubchem:
                    session.run(
                        """
                        UNWIND $relationships AS rel
                        MATCH (e:Experiment {experiment_id: rel.experiment_id})
                        MATCH (c:Compound {pubChemID: rel.pubChemID})
                        MERGE (e)-[:HAS_COMPOUND]->(c)
                    """,
                        relationships=with_pubchem,
                    )

                if without_pubchem:
                    session.run(
                        """
                        UNWIND $relationships AS rel
                        MATCH (e:Experiment {experiment_id: rel.experiment_id})
                        MATCH (c:Compound {compoundID: rel.compound_id})
                        MERGE (e)-[:HAS_COMPOUND]->(c)
                    """,
                        relationships=without_pubchem,
                    )

        # HAS_PROPERTY relationships
        has_property = relationships.get("HAS_PROPERTY", [])
        if has_property:
            session.run(
                """
                UNWIND $relationships AS rel
                MATCH (e:Experiment {experiment_id: rel.experiment_id})
                MATCH (p:Property {propertyType: rel.property_type})
                MERGE (e)-[r:HAS_PROPERTY]->(p)
                SET r.value = rel.prop_value,
                    r.uncertainty = rel.prop_uncertainty
            """,
                relationships=has_property,
            )

        # HAS_PARAMETER relationships
        has_parameter = relationships.get("HAS_PARAMETER", [])
        if has_parameter:
            session.run(
                """
                UNWIND $relationships AS rel
                MATCH (e:Experiment {experiment_id: rel.experiment_id})
                MATCH (param:Parameter {parameter: rel.parameter_str})
                MERGE (e)-[r:HAS_PARAMETER]->(param)
                SET r.value = rel.param_value,
                    r.uncertainty = rel.param_uncertainty
            """,
                relationships=has_parameter,
            )

        # CITED_IN relationships
        cited_in = relationships.get("CITED_IN", [])
        if cited_in:
            session.run(
                """
                UNWIND $relationships AS rel
                MATCH (e:Experiment {experiment_id: rel.experiment_id})
                MATCH (cit:Citation {doi: rel.doi})
                MERGE (e)-[:CITED_IN]->(cit)
            """,
                relationships=cited_in,
            )

        # HAS_UNIT relationships for Properties
        property_has_unit = relationships.get("PROPERTY_HAS_UNIT", [])
        if property_has_unit:
            session.run(
                """
                UNWIND $relationships AS rel
                MATCH (p:Property {propertyType: rel.property_type})
                MATCH (u:Unit {unitID: rel.unit_id})
                MERGE (p)-[:HAS_UNIT]->(u)
            """,
                relationships=property_has_unit,
            )

        # HAS_UNIT relationships for Parameters
        parameter_has_unit = relationships.get("PARAMETER_HAS_UNIT", [])
        if parameter_has_unit:
            session.run(
                """
                UNWIND $relationships AS rel
                MATCH (param:Parameter {parameter: rel.parameter_str})
                MATCH (u:Unit {unitID: rel.unit_id})
                MERGE (param)-[:HAS_UNIT]->(u)
            """,
                relationships=parameter_has_unit,
            )

        # ASSOCIATED_WITH relationships
        associated_with = relationships.get("ASSOCIATED_WITH", [])
        if associated_with:
            with_pubchem = [r for r in associated_with if r.get("pubChemID")]
            without_pubchem = [r for r in associated_with if not r.get("pubChemID")]

            if with_pubchem:
                session.run(
                    """
                    UNWIND $relationships AS rel
                    MATCH (param:Parameter {parameter: rel.parameter_str})
                    MATCH (c:Compound {pubChemID: rel.pubChemID})
                    MERGE (param)-[:ASSOCIATED_WITH]->(c)
                """,
                    relationships=with_pubchem,
                )

            if without_pubchem:
                session.run(
                    """
                    UNWIND $relationships AS rel
                    MATCH (param:Parameter {parameter: rel.parameter_str})
                    MATCH (c:Compound {compoundID: rel.compound_id})
                    MERGE (param)-[:ASSOCIATED_WITH]->(c)
                """,
                    relationships=without_pubchem,
                )

    def import_from_json_files(self, json_directory, batch_size=100):
        """Import data directly from JSON files with bulk processing."""
        json_files = list(Path(json_directory).glob("*.json"))
        total_files = len(json_files)
        print(f"📁 Processing {total_files} JSON files...")

        # Track unique entities across all files
        compounds_seen = set()
        units_seen = set()
        citations_seen = set()
        properties_seen = set()
        parameters_seen = set()
        experiment_count = 0

        # Batch collections
        compounds_batch = []
        units_batch = []
        citations_batch = []
        properties_batch = []
        parameters_batch = []
        experiments_batch = []
        relationships_batch = {
            "HAS_COMPOUND": [],
            "HAS_PROPERTY": [],
            "HAS_PARAMETER": [],
            "CITED_IN": [],
            "PROPERTY_HAS_UNIT": [],
            "PARAMETER_HAS_UNIT": [],
            "ASSOCIATED_WITH": [],
        }

        with self.driver.session() as session:
            pbar = (
                tqdm(total=total_files, desc="Importing JSON", unit="file")
                if tqdm
                else None
            )
            for idx, json_file in enumerate(json_files):
                if pbar:
                    pbar.set_description(f"Importing {json_file.name}")
                else:
                    print(f"[{idx + 1}/{total_files}] Processing: {json_file.name}")

                try:
                    with open(json_file, "r") as f:
                        data = json.load(f)

                    # Step 1: Collect compounds from compound block
                    compound_id_map = {}
                    compound_pubchem_map = {}
                    compound_id_to_pubchem = {}

                    if "compound" in data and data["compound"]:
                        for compound in data["compound"]:
                            compound_id = compound.get(
                                "compoundID", f"compound_{len(compounds_seen)}"
                            )
                            pub_chem_id = compound.get("pubChemID")

                            unique_id = (
                                pub_chem_id
                                if (pub_chem_id and pub_chem_id > 0)
                                else compound_id
                            )

                            if unique_id not in compounds_seen:
                                compounds_seen.add(unique_id)
                                compound_id_map[compound_id] = compound
                                if pub_chem_id and pub_chem_id > 0:
                                    compound_pubchem_map[pub_chem_id] = compound
                                    compound_id_to_pubchem[compound_id] = pub_chem_id

                                # Prepare compound data for batch insert
                                compound_data = {
                                    "compoundID": compound_id,
                                    "pubChemID": (
                                        pub_chem_id
                                        if (pub_chem_id and pub_chem_id > 0)
                                        else None
                                    ),
                                    "commonName": compound.get("commonName") or "",
                                    "name_IUPAC": compound.get("name_IUPAC") or "",
                                    "standard_InChI": compound.get("standard_InChI")
                                    or "",
                                    "standard_InChI_key": compound.get(
                                        "standard_InChI_key"
                                    )
                                    or "",
                                    "molar_weigth": compound.get("molar_weigth"),
                                    "SELFIE": compound.get("SELFIE") or "",
                                    "smiles_code": compound.get("smiles_code") or "",
                                    # Keep Neo4j field name stable; adapt JSON parsing to lib.py key.
                                    "sigman_profile": compound.get("sigma_profile")
                                    if compound.get("sigma_profile") is not None
                                    else compound.get("sigman_profile"),
                                }
                                compounds_batch.append(compound_data)

                    # Step 2: Collect citations
                    citation_doi_map = {}
                    if "citation" in data and data["citation"]:
                        citation = data["citation"]
                        doi = citation.get("doi")
                        if doi and doi not in citations_seen:
                            citations_seen.add(doi)
                            citation_doi_map[doi] = citation

                            # Handle LitType enum
                            lit_type_value = citation.get("litType")
                            lit_type_str = None
                            if lit_type_value is not None:
                                if hasattr(lit_type_value, "value"):
                                    lit_type_str = lit_type_value.value
                                elif isinstance(lit_type_value, str):
                                    lit_type_str = lit_type_value
                                else:
                                    lit_type_str = str(lit_type_value)

                            citations_batch.append(
                                {
                                    "doi": doi,
                                    "title": citation.get("title") or "",
                                    "pub_name": citation.get("pub_name") or "",
                                    "publication_year": citation.get("publication_year")
                                    or "",
                                    "litType": lit_type_str or "",
                                    "litType_enum": (
                                        str(lit_type_value) if lit_type_value else None
                                    ),
                                    "page": citation.get("page") or "",
                                    "lit_volume_num": citation.get("lit_volume_num")
                                    or "",
                                    "url_citation": citation.get("url_citation") or "",
                                }
                            )

                    # Step 3: Process each fluid and create Experiments from measurements
                    if "fluid" in data and data["fluid"]:
                        for fluid_index, fluid_data in enumerate(data["fluid"]):
                            # Get compounds for this fluid
                            fluid_compound_ids = fluid_data.get("compounds", [])

                            # Get fluidID (UUID) from fluid data
                            fluid_id = None
                            fluid_id_list = fluid_data.get("fluidID", [])
                            if fluid_id_list and len(fluid_id_list) > 0:
                                fluid_id = fluid_id_list[
                                    0
                                ]  # Use first UUID if multiple exist

                            # Process parameters and store them for later use
                            parameter_map = (
                                {}
                            )  # Map parameterID to parameter definition
                            if "parameter" in fluid_data:
                                for param in fluid_data["parameter"]:
                                    parameter_id = param.get("parameterID")
                                    if parameter_id:
                                        # Handle enum values
                                        parameter_value = param.get("parameters")
                                        if parameter_value is None:
                                            # Backward compatibility with older exports.
                                            parameter_value = param.get("parameter")
                                        parameter_str = None
                                        if parameter_value is not None:
                                            if hasattr(parameter_value, "value"):
                                                parameter_str = parameter_value.value
                                            elif isinstance(parameter_value, str):
                                                parameter_str = parameter_value
                                            else:
                                                parameter_str = str(parameter_value)

                                        if not parameter_str:
                                            print(
                                                f"⚠️  Missing `parameters` value for parameterID '{parameter_id}' in file '{json_file.name}'. Skipping parameter mapping."
                                            )
                                            continue
                                        if parameter_str not in Parameters._value2member_map_:
                                            print(
                                                f"⚠️  Undefined parameter enum value '{parameter_str}' (parameterID '{parameter_id}') in file '{json_file.name}'. Skipping parameter mapping."
                                            )
                                            continue
                                        parameter_field_key = (
                                            self._parameter_field_key(parameter_str)
                                        )

                                        # Use parameterID as the unique identifier (it's already semantic)
                                        # Handle both associated_compound (singular) and associated_compounds (plural)
                                        associated_compounds_list = []
                                        if (
                                            "associated_compound" in param
                                            and param.get("associated_compound")
                                        ):
                                            # Handle singular form (e.g., "compound_1")
                                            associated_compounds_list = [
                                                param.get("associated_compound")
                                            ]
                                        elif "associated_compounds" in param:
                                            # Handle plural form (array)
                                            associated_compounds_list = param.get(
                                                "associated_compounds", []
                                            )

                                        parameter_map[parameter_id] = {
                                            "parameter_str": parameter_str,
                                            "parameter_field_key": parameter_field_key,
                                            "unit": param.get("unit"),
                                            "associated_compounds": associated_compounds_list,
                                        }

                                        # Check if this is a mole fraction parameter
                                        # Skip creating Parameter nodes for mole fractions since we store them on edges
                                        param_str_lower = parameter_str.lower()
                                        is_mole_fraction = "mole fraction" in param_str_lower

                                        # Collect Parameter node data - skip for mole fraction parameters
                                        if not is_mole_fraction:
                                            if parameter_str not in parameters_seen:
                                                parameters_seen.add(parameter_str)

                                            # Get associated compounds (handle both singular and plural)
                                            param_associated_compounds = []
                                            if (
                                                "associated_compound" in param
                                                and param.get("associated_compound")
                                            ):
                                                param_associated_compounds = [
                                                    param.get("associated_compound")
                                                ]
                                            elif "associated_compounds" in param:
                                                param_associated_compounds = param.get(
                                                    "associated_compounds", []
                                                )

                                            parameters_batch.append(
                                                {
                                                    "parameter_str": parameter_str,
                                                    "parameterID": parameter_id,
                                                    "associated_compounds": param_associated_compounds,
                                                }
                                            )

                                            # Collect unit data
                                            unit_data = param.get("unit")
                                            if unit_data and unit_data.get("unitID"):
                                                unit_id = unit_data.get("unitID")
                                                if unit_id not in units_seen:
                                                    units_seen.add(unit_id)
                                                    units_batch.append(
                                                        {
                                                            "unitID": unit_id,
                                                            "name": unit_data.get(
                                                                "name"
                                                            )
                                                            or "",
                                                        }
                                                    )

                                                # Collect Parameter-Unit relationship
                                                relationships_batch[
                                                    "PARAMETER_HAS_UNIT"
                                                ].append(
                                                    {
                                                        "parameter_str": parameter_str,
                                                        "unit_id": unit_id,
                                                    }
                                                )

                                            # Collect Parameter-Compound relationships
                                            param_associated_compounds_list = []
                                            if (
                                                "associated_compound" in param
                                                and param.get("associated_compound")
                                            ):
                                                param_associated_compounds_list = [
                                                    param.get("associated_compound")
                                                ]
                                            elif "associated_compounds" in param:
                                                param_associated_compounds_list = (
                                                    param.get(
                                                        "associated_compounds", []
                                                    )
                                                )

                                            if param_associated_compounds_list:
                                                for (
                                                    compound_id_ref
                                                ) in param_associated_compounds_list:
                                                    # Find the actual compound ID (similar logic as for experiments)
                                                    actual_compound_id = None

                                                    # Strategy 0: Check if it's an ordered reference like "compound_1", "compound_2", etc.
                                                    if (
                                                        compound_id_ref.startswith(
                                                            "compound_"
                                                        )
                                                        and compound_id_ref[
                                                            9:
                                                        ].isdigit()
                                                    ):
                                                        # Extract the index (1-based)
                                                        try:
                                                            index = (
                                                                int(compound_id_ref[9:])
                                                                - 1
                                                            )  # Convert to 0-based index
                                                            if (
                                                                0
                                                                <= index
                                                                < len(
                                                                    fluid_compound_ids
                                                                )
                                                            ):
                                                                # Use the compound at that index in the fluid's compounds list
                                                                compound_id_ref_from_index = fluid_compound_ids[
                                                                    index
                                                                ]
                                                                # Now resolve this reference
                                                                if (
                                                                    compound_id_ref_from_index
                                                                    in compound_id_map
                                                                ):
                                                                    actual_compound_id = compound_id_ref_from_index
                                                                else:
                                                                    # Try to find in compound_id_map
                                                                    for (
                                                                        cid
                                                                    ) in (
                                                                        compound_id_map.keys()
                                                                    ):
                                                                        if (
                                                                            compound_id_ref_from_index.lower()
                                                                            in cid.lower()
                                                                            or cid.lower()
                                                                            in compound_id_ref_from_index.lower()
                                                                        ):
                                                                            actual_compound_id = (
                                                                                cid
                                                                            )
                                                                            break
                                                        except ValueError:
                                                            pass  # Not a valid number, continue with other strategies

                                                    # Strategy 1: Direct match in current file
                                                    if (
                                                        not actual_compound_id
                                                        and compound_id_ref
                                                        in compound_id_map
                                                    ):
                                                        actual_compound_id = (
                                                            compound_id_ref
                                                        )

                                                    # Strategy 2: Fuzzy match in current file
                                                    if not actual_compound_id:
                                                        for (
                                                            cid
                                                        ) in compound_id_map.keys():
                                                            if (
                                                                compound_id_ref.lower()
                                                                in cid.lower()
                                                                or cid.lower()
                                                                in compound_id_ref.lower()
                                                            ):
                                                                actual_compound_id = cid
                                                                break

                                                    # Strategy 3: Check database for existing compound
                                                    if not actual_compound_id:
                                                        result = session.run(
                                                            """
                                                            MATCH (c:Compound {compoundID: $compound_id_ref})
                                                            RETURN c.compoundID as compoundID
                                                            LIMIT 1
                                                            """,
                                                            compound_id_ref=compound_id_ref,
                                                        )
                                                        record = result.single()
                                                        if record:
                                                            actual_compound_id = record[
                                                                "compoundID"
                                                            ]

                                                    # Strategy 4: Fuzzy match in database
                                                    if not actual_compound_id:
                                                        possible_names = [
                                                            compound_id_ref,
                                                            compound_id_ref.replace(
                                                                "compound_", ""
                                                            ),
                                                            compound_id_ref.replace(
                                                                "compound_", ""
                                                            ).replace("_", " "),
                                                            compound_id_ref.replace(
                                                                "compound_", ""
                                                            ).replace("_", "-"),
                                                        ]

                                                        for name in possible_names:
                                                            result = session.run(
                                                                """
                                                                MATCH (c:Compound)
                                                                WHERE c.compoundID CONTAINS $search_term 
                                                                   OR toLower(c.commonName) CONTAINS toLower($search_term)
                                                                RETURN c.compoundID as compoundID
                                                                LIMIT 1
                                                                """,
                                                                search_term=name,
                                                            )
                                                            record = result.single()
                                                            if record:
                                                                actual_compound_id = (
                                                                    record["compoundID"]
                                                                )
                                                                break

                                                    if actual_compound_id:
                                                        # Try to find pubChemID for this compound_id
                                                        pub_chem_id = (
                                                            compound_id_to_pubchem.get(
                                                                actual_compound_id
                                                            )
                                                        )
                                                        # Collect relationship for batch processing
                                                        relationships_batch[
                                                            "ASSOCIATED_WITH"
                                                        ].append(
                                                            {
                                                                "parameter_str": parameter_str,
                                                                "pubChemID": pub_chem_id,
                                                                "compound_id": (
                                                                    actual_compound_id
                                                                    if not pub_chem_id
                                                                    else None
                                                                ),
                                                            }
                                                        )

                            # Process properties and store them for later use
                            property_map = {}  # Map propertyID to property definition
                            if "property" in fluid_data:
                                for prop in fluid_data["property"]:
                                    property_id = prop.get("propertyID")
                                    if property_id:
                                        # Handle enum values
                                        properties_value = prop.get("properties")
                                        properties_str = None
                                        if properties_value is not None:
                                            if hasattr(properties_value, "value"):
                                                properties_str = properties_value.value
                                            elif isinstance(properties_value, str):
                                                properties_str = properties_value
                                            else:
                                                properties_str = str(properties_value)

                                        # Strict enum-based property mapping:
                                        # - no normalization
                                        # - no fallback mapping from propertyID
                                        if not properties_str:
                                            print(
                                                f"⚠️  Missing `properties` for propertyID '{property_id}' in file '{json_file.name}'. Skipping property mapping."
                                            )
                                            continue
                                        if properties_str not in Properties._value2member_map_:
                                            print(
                                                f"⚠️  Undefined property enum value '{properties_str}' (propertyID '{property_id}') in file '{json_file.name}'. Skipping property mapping."
                                            )
                                            continue
                                        property_type = properties_str

                                        property_map[property_id] = {
                                            "property_type": property_type,
                                            "properties_str": properties_str or "",
                                            "unit": prop.get("unit"),
                                        }

                                        # Collect Property node data
                                        prop_key = property_type
                                        if prop_key not in properties_seen:
                                            properties_seen.add(prop_key)

                                            properties_batch.append(
                                                {
                                                    "propertyType": property_type,
                                                    "properties_str": properties_str
                                                    or "",
                                                    "propertyID": property_id,
                                                }
                                            )

                                            # Collect unit data
                                            unit_data = prop.get("unit")
                                            if unit_data and unit_data.get("unitID"):
                                                unit_id = unit_data.get("unitID")
                                                if unit_id not in units_seen:
                                                    units_seen.add(unit_id)
                                                    units_batch.append(
                                                        {
                                                            "unitID": unit_id,
                                                            "name": unit_data.get(
                                                                "name"
                                                            )
                                                            or "",
                                                        }
                                                    )

                                                # Collect Property-Unit relationship
                                                relationships_batch[
                                                    "PROPERTY_HAS_UNIT"
                                                ].append(
                                                    {
                                                        "property_type": property_type,
                                                        "unit_id": unit_id,
                                                    }
                                                )

                            # Process each measurement as an Experiment.
                            # Current lib.py writes measurements under fluid.sample.measurement.
                            # Keep legacy fallback for older JSONs using fluid.measurement.
                            measurement_entries = []
                            sample_data = fluid_data.get("sample")
                            if isinstance(sample_data, dict):
                                sample_context = self._build_sample_context(sample_data)
                                for measurement in sample_data.get("measurement", []) or []:
                                    measurement_entries.append((measurement, sample_context))
                            elif isinstance(sample_data, list):
                                for sample_entry in sample_data:
                                    if isinstance(sample_entry, dict):
                                        sample_context = self._build_sample_context(
                                            sample_entry
                                        )
                                        for measurement in (
                                            sample_entry.get("measurement", []) or []
                                        ):
                                            measurement_entries.append(
                                                (measurement, sample_context)
                                            )
                            elif "measurement" in fluid_data:
                                for measurement in fluid_data.get("measurement", []) or []:
                                    measurement_entries.append((measurement, {}))

                            if measurement_entries:
                                for measurement, sample_context in measurement_entries:
                                    measurement_id = measurement.get("measurement_id")
                                    if not measurement_id:
                                        experiment_count += 1
                                        measurement_id = f"experiment_{experiment_count}_{json_file.stem}"

                                    # Collect property values
                                    property_values = {}
                                    for prop_val in measurement.get(
                                        "propertyValue", []
                                    ):
                                        prop_id = prop_val.get("propertyID")
                                        prop_value = prop_val.get("propValue")
                                        if prop_id and prop_value is not None:
                                            # Get property type from property_map
                                            prop_info = property_map.get(prop_id)
                                            if prop_info:
                                                prop_key = prop_info["property_type"]
                                                property_values[prop_key] = prop_value
                                                property_values[
                                                    f"{prop_key}_uncertainty"
                                                ] = prop_val.get("uncertainty")

                                    # Collect parameter values
                                    parameter_values = {}
                                    for param_val in measurement.get(
                                        "parameterValue", []
                                    ):
                                        param_id = param_val.get("parameterID")
                                        param_value = param_val.get("paramValue")
                                        if param_id and param_value is not None:
                                            param_info = parameter_map.get(param_id)
                                            if not param_info:
                                                print(
                                                    f"⚠️  parameterID '{param_id}' has no mapped parameter definition in file '{json_file.name}'. Skipping parameter value."
                                                )
                                                continue
                                            param_key = param_info.get(
                                                "parameter_field_key"
                                            )
                                            if not param_key:
                                                print(
                                                    f"⚠️  parameterID '{param_id}' has no parameter field key in file '{json_file.name}'. Skipping parameter value."
                                                )
                                                continue
                                            # Mole fraction is represented on HAS_COMPOUND edges,
                                            # not as an Experiment property.
                                            param_str_lower = (
                                                param_info.get("parameter_str", "").lower()
                                            )
                                            if "mole fraction" in param_str_lower:
                                                continue
                                            parameter_values[param_key] = param_value
                                            parameter_values[
                                                f"{param_key}_uncertainty"
                                            ] = param_val.get("uncertainty")

                                    # Handle method enum
                                    method_value = measurement.get("method")
                                    method_str = None
                                    if method_value is not None:
                                        if hasattr(method_value, "value"):
                                            method_str = method_value.value
                                        elif isinstance(method_value, str):
                                            method_str = method_value
                                        else:
                                            method_str = str(method_value)

                                    # Create Experiment node with all data
                                    experiment_props = {
                                        "experiment_id": measurement_id,
                                        "source_doi": measurement.get("source_doi")
                                        or "",
                                        "method": method_str or "",
                                        "method_description": measurement.get(
                                            "method_description"
                                        )
                                        or "",
                                        "source_file": json_file.name,
                                        "fluid_index": fluid_index,
                                        "fluidID": fluid_id,  # Add fluidID (UUID) to experiment
                                    }
                                    if sample_context:
                                        experiment_props.update(sample_context)

                                    # Add property and parameter values
                                    experiment_props.update(property_values)
                                    experiment_props.update(parameter_values)

                                    # Collect dynamic properties
                                    dynamic_props = {}
                                    for key, value in experiment_props.items():
                                        if key not in [
                                            "experiment_id",
                                            "source_doi",
                                            "method",
                                            "method_description",
                                            "source_file",
                                            "fluid_index",
                                            "fluidID",
                                        ]:
                                            if value is not None:
                                                dynamic_props[key] = value

                                    # Collect experiment data for batch insert
                                    experiments_batch.append(
                                        {
                                            "experiment_id": measurement_id,
                                            "source_doi": experiment_props.get(
                                                "source_doi", ""
                                            ),
                                            "method": experiment_props.get(
                                                "method", ""
                                            ),
                                            "method_description": experiment_props.get(
                                                "method_description", ""
                                            ),
                                            "source_file": experiment_props.get(
                                                "source_file", ""
                                            ),
                                            "fluid_index": experiment_props.get(
                                                "fluid_index", 0
                                            ),
                                            "fluidID": experiment_props.get(
                                                "fluidID", ""
                                            ),
                                            "dynamic_props": dynamic_props,
                                        }
                                    )

                                    # Connect Experiment to Compounds with mole fraction weights
                                    # Build a map: compound reference -> mole fraction parameter ID -> mole fraction value
                                    compound_mole_fraction_map = (
                                        {}
                                    )  # Maps compound_id_ref to mole_fraction value

                                    # First, find all mole fraction parameters and their associated compounds
                                    for param_id, param_info in parameter_map.items():
                                        # Check if this is a mole fraction parameter
                                        param_str_lower = param_info.get(
                                            "parameter_str", ""
                                        ).lower()
                                        if (
                                            "mole fraction" in param_str_lower
                                            or "mole_fraction" in param_id.lower()
                                        ):
                                            # Get associated compounds for this parameter
                                            associated_compounds_list = param_info.get(
                                                "associated_compounds", []
                                            )

                                            # Find the mole fraction value from the measurement
                                            mole_fraction_value = None
                                            for param_val in measurement.get(
                                                "parameterValue", []
                                            ):
                                                if (
                                                    param_val.get("parameterID")
                                                    == param_id
                                                ):
                                                    mole_fraction_value = param_val.get(
                                                        "paramValue"
                                                    )
                                                    break

                                            if mole_fraction_value is not None:
                                                # Map each associated compound to this mole fraction value
                                                for (
                                                    compound_ref
                                                ) in associated_compounds_list:
                                                    # Resolve compound reference (could be "compound_1" or direct compoundID)
                                                    resolved_compound_id = None

                                                    # Handle "compound_1" style references
                                                    if (
                                                        compound_ref.startswith(
                                                            "compound_"
                                                        )
                                                        and compound_ref[9:].isdigit()
                                                    ):
                                                        try:
                                                            index = (
                                                                int(compound_ref[9:])
                                                                - 1
                                                            )  # Convert to 0-based index
                                                            if (
                                                                0
                                                                <= index
                                                                < len(
                                                                    fluid_compound_ids
                                                                )
                                                            ):
                                                                resolved_compound_id = (
                                                                    fluid_compound_ids[
                                                                        index
                                                                    ]
                                                                )
                                                        except ValueError:
                                                            pass

                                                    # If not an ordered reference, use the compound_ref directly
                                                    if not resolved_compound_id:
                                                        resolved_compound_id = (
                                                            compound_ref
                                                        )

                                                    # Store the mole fraction for this compound
                                                    if resolved_compound_id:
                                                        compound_mole_fraction_map[
                                                            resolved_compound_id
                                                        ] = mole_fraction_value

                                    # Also check by index if no explicit parameter found (for ordered compounds)
                                    # If compound is at index i, check for mole_fraction_{i+1} parameter
                                    for idx, compound_id_ref in enumerate(
                                        fluid_compound_ids
                                    ):
                                        # Try to find mole fraction parameter for this compound by index
                                        mole_fraction_param_id = (
                                            f"mole_fraction_{idx + 1}"
                                        )
                                        if mole_fraction_param_id in parameter_map:
                                            # Check if this parameter has a value in the measurement
                                            for param_val in measurement.get(
                                                "parameterValue", []
                                            ):
                                                if (
                                                    param_val.get("parameterID")
                                                    == mole_fraction_param_id
                                                ):
                                                    mole_fraction_value = param_val.get(
                                                        "paramValue"
                                                    )
                                                    if mole_fraction_value is not None:
                                                        compound_mole_fraction_map[
                                                            compound_id_ref
                                                        ] = mole_fraction_value
                                                    break

                                    # Now create HAS_COMPOUND relationships with mole fraction weights
                                    for compound_id_ref in fluid_compound_ids:
                                        # Find the actual compound ID (could be a reference)
                                        actual_compound_id = None

                                        # Strategy 1: Try direct match in current file's compound_id_map
                                        if compound_id_ref in compound_id_map:
                                            actual_compound_id = compound_id_ref
                                        else:
                                            # Strategy 2: Try to find by matching compoundID in compound_id_map keys (fuzzy match)
                                            for cid in compound_id_map.keys():
                                                if (
                                                    compound_id_ref.lower()
                                                    in cid.lower()
                                                    or cid.lower()
                                                    in compound_id_ref.lower()
                                                ):
                                                    actual_compound_id = cid
                                                    break

                                        # Strategy 3: If not found in current file, check if compound exists in Neo4j database
                                        # (from previous files with the same compoundID or pubChemID)
                                        found_pubchem_id = None
                                        if not actual_compound_id:
                                            # First check if we know the pubChemID for this reference
                                            known_pubchem = compound_id_to_pubchem.get(
                                                compound_id_ref
                                            )
                                            if known_pubchem:
                                                # Try matching by pubChemID
                                                result = session.run(
                                                    """
                                                    MATCH (c:Compound {pubChemID: $pubChemID})
                                                    RETURN c.pubChemID as pubChemID, c.compoundID as compoundID
                                                    LIMIT 1
                                                    """,
                                                    pubChemID=known_pubchem,
                                                )
                                                record = result.single()
                                                if record:
                                                    actual_compound_id = compound_id_ref  # Use original reference
                                                    found_pubchem_id = record.get("pubChemID")
                                                    # Store pubChemID mapping for future use
                                                    if found_pubchem_id:
                                                        compound_id_to_pubchem[compound_id_ref] = found_pubchem_id
                                                    # Add to compound_id_map for reuse in same file
                                                    if compound_id_ref not in compound_id_map:
                                                        compound_id_map[compound_id_ref] = {
                                                            "compoundID": compound_id_ref,
                                                            "pubChemID": found_pubchem_id,
                                                        }
                                            else:
                                                # Try matching by compoundID
                                                result = session.run(
                                                    """
                                                    MATCH (c:Compound {compoundID: $compound_id_ref})
                                                    RETURN c.pubChemID as pubChemID, c.compoundID as compoundID
                                                    LIMIT 1
                                                    """,
                                                    compound_id_ref=compound_id_ref,
                                                )
                                                record = result.single()
                                                if record:
                                                    actual_compound_id = (
                                                        record.get("compoundID")
                                                        or compound_id_ref
                                                    )
                                                    found_pubchem_id = record.get("pubChemID")
                                                    # Store pubChemID mapping for future use
                                                    if found_pubchem_id:
                                                        compound_id_to_pubchem[actual_compound_id] = found_pubchem_id

                                        # Strategy 4: Try fuzzy matching in database (by common name if available)
                                        if not actual_compound_id:
                                            # Extract possible compound name from the reference
                                            # (e.g., "compound_cholinechloride" -> "cholinechloride" or "choline chloride")
                                            possible_names = [
                                                compound_id_ref,
                                                compound_id_ref.replace(
                                                    "compound_", ""
                                                ),
                                                compound_id_ref.replace(
                                                    "compound_", ""
                                                ).replace("_", " "),
                                                compound_id_ref.replace(
                                                    "compound_", ""
                                                ).replace("_", "-"),
                                            ]

                                            for name in possible_names:
                                                result = session.run(
                                                    """
                                                    MATCH (c:Compound)
                                                    WHERE c.compoundID CONTAINS $search_term 
                                                       OR toLower(c.commonName) CONTAINS toLower($search_term)
                                                       OR toLower(c.compoundID) CONTAINS toLower($search_term)
                                                    RETURN c.pubChemID as pubChemID, c.compoundID as compoundID
                                                    LIMIT 1
                                                    """,
                                                    search_term=name,
                                                )
                                                record = result.single()
                                                if record:
                                                    actual_compound_id = (
                                                        record.get("compoundID")
                                                        or compound_id_ref
                                                    )
                                                    found_pubchem_id = record.get("pubChemID")
                                                    # Store pubChemID mapping for future use
                                                    if found_pubchem_id:
                                                        compound_id_to_pubchem[actual_compound_id] = found_pubchem_id
                                                    break

                                        # Strategy 5: If still not found, create compound with minimal information
                                        if not actual_compound_id:
                                            # Try to get pubChemID from known mappings (might be from other files)
                                            known_pubchem = compound_id_to_pubchem.get(
                                                compound_id_ref
                                            )
                                            
                                            # Create compound with minimal information
                                            compound_data = {
                                                "compoundID": compound_id_ref,
                                                "pubChemID": known_pubchem if (known_pubchem and known_pubchem > 0) else None,
                                                "commonName": compound_id_ref.replace("_", " ").replace("compound ", ""),
                                                "name_IUPAC": "",
                                                "standard_InChI": "",
                                                "standard_InChI_key": "",
                                                "molar_weigth": None,
                                                "SELFIE": "",
                                                "smiles_code": "",
                                                "sigman_profile": None,
                                            }
                                            
                                            # Add to batch for creation
                                            unique_id = (
                                                known_pubchem
                                                if (known_pubchem and known_pubchem > 0)
                                                else compound_id_ref
                                            )
                                            
                                            if unique_id not in compounds_seen:
                                                compounds_seen.add(unique_id)
                                                compounds_batch.append(compound_data)
                                                # Add to compound_id_map for reuse in same file
                                                compound_id_map[compound_id_ref] = {
                                                    "compoundID": compound_id_ref,
                                                    "pubChemID": known_pubchem if (known_pubchem and known_pubchem > 0) else None,
                                                    "commonName": compound_id_ref.replace("_", " ").replace("compound ", ""),
                                                }
                                                if known_pubchem and known_pubchem > 0:
                                                    compound_id_to_pubchem[compound_id_ref] = known_pubchem
                                            
                                            actual_compound_id = compound_id_ref
                                            found_pubchem_id = known_pubchem

                                        # Collect relationship if we found or created the compound
                                        if actual_compound_id:
                                            # Get mole fraction value for this compound
                                            mole_fraction = (
                                                compound_mole_fraction_map.get(
                                                    compound_id_ref
                                                )
                                            )

                                            # Try to find pubChemID for this compound
                                            pub_chem_id = compound_id_to_pubchem.get(
                                                actual_compound_id
                                            ) or found_pubchem_id

                                            # Collect HAS_COMPOUND relationship
                                            relationships_batch["HAS_COMPOUND"].append(
                                                {
                                                    "experiment_id": measurement_id,
                                                    "pubChemID": pub_chem_id,
                                                    "compound_id": (
                                                        actual_compound_id
                                                        if not pub_chem_id
                                                        else None
                                                    ),
                                                    "mole_fraction": mole_fraction,
                                                }
                                            )

                                    # Collect Experiment-Property relationships
                                    for prop_id, prop_info in property_map.items():
                                        prop_key = prop_info["property_type"]
                                        if prop_key in experiment_props:
                                            relationships_batch["HAS_PROPERTY"].append(
                                                {
                                                    "experiment_id": measurement_id,
                                                    "property_type": prop_info[
                                                        "property_type"
                                                    ],
                                                    "prop_value": experiment_props.get(
                                                        prop_key
                                                    ),
                                                    "prop_uncertainty": experiment_props.get(
                                                        f"{prop_key}_uncertainty"
                                                    ),
                                                }
                                            )

                                    # Collect Experiment-Parameter relationships (skip mole fraction parameters)
                                    for param_id, param_info in parameter_map.items():
                                        param_str_lower = param_info.get(
                                            "parameter_str", ""
                                        ).lower()
                                        is_mole_fraction = "mole fraction" in param_str_lower

                                        if is_mole_fraction:
                                            continue

                                        parameter_str = param_info.get(
                                            "parameter_str", ""
                                        )
                                        if not parameter_str:
                                            continue

                                        param_key = param_info.get("parameter_field_key")
                                        if not param_key:
                                            continue
                                        if param_key in experiment_props:
                                            relationships_batch["HAS_PARAMETER"].append(
                                                {
                                                    "experiment_id": measurement_id,
                                                    "parameter_str": parameter_str,
                                                    "param_value": experiment_props.get(
                                                        param_key
                                                    ),
                                                    "param_uncertainty": experiment_props.get(
                                                        f"{param_key}_uncertainty"
                                                    ),
                                                }
                                            )

                                    # Collect Experiment-Citation relationships
                                    source_doi = measurement.get("source_doi") or ""
                                    if source_doi and source_doi in citation_doi_map:
                                        relationships_batch["CITED_IN"].append(
                                            {
                                                "experiment_id": measurement_id,
                                                "doi": source_doi,
                                            }
                                        )
                                    elif "citation" in data and data["citation"]:
                                        doc_doi = data["citation"].get("doi")
                                        if doc_doi and doc_doi in citation_doi_map:
                                            relationships_batch["CITED_IN"].append(
                                                {
                                                    "experiment_id": measurement_id,
                                                    "doi": doc_doi,
                                                }
                                            )

                                    # Process batches when we reach batch_size experiments
                                    if len(experiments_batch) >= batch_size:
                                        # First ensure all nodes exist
                                        self._bulk_create_compounds(
                                            session, compounds_batch
                                        )
                                        compounds_batch = []
                                        self._bulk_create_units(session, units_batch)
                                        units_batch = []
                                        self._bulk_create_citations(
                                            session, citations_batch
                                        )
                                        citations_batch = []
                                        self._bulk_create_properties(
                                            session, properties_batch
                                        )
                                        properties_batch = []
                                        self._bulk_create_parameters(
                                            session, parameters_batch
                                        )
                                        parameters_batch = []
                                        self._bulk_create_experiments(
                                            session, experiments_batch
                                        )
                                        experiments_batch = []
                                        self._bulk_create_relationships(
                                            session, relationships_batch
                                        )
                                        # Reset relationships batch
                                        relationships_batch = {
                                            "HAS_COMPOUND": [],
                                            "HAS_PROPERTY": [],
                                            "HAS_PARAMETER": [],
                                            "CITED_IN": [],
                                            "PROPERTY_HAS_UNIT": [],
                                            "PARAMETER_HAS_UNIT": [],
                                            "ASSOCIATED_WITH": [],
                                        }

                except Exception as e:
                    print(f"Error processing {json_file}: {e}")
                    import traceback

                    traceback.print_exc()
                    continue
                finally:
                    if pbar:
                        pbar.update(1)

            # Process remaining batches
            if (
                compounds_batch
                or units_batch
                or citations_batch
                or properties_batch
                or parameters_batch
                or experiments_batch
            ):
                self._bulk_create_compounds(session, compounds_batch)
                self._bulk_create_units(session, units_batch)
                self._bulk_create_citations(session, citations_batch)
                self._bulk_create_properties(session, properties_batch)
                self._bulk_create_parameters(session, parameters_batch)
                self._bulk_create_experiments(session, experiments_batch)
                self._bulk_create_relationships(session, relationships_batch)

            if pbar:
                pbar.close()

        print(f"✅ Data import completed! Created {experiment_count} experiments.")


def run_example_queries(driver):
    """Run example Cypher queries to demonstrate the power of Neo4j."""
    print("\n🔍 EXAMPLE CYPHER QUERIES")
    print("=" * 50)

    with driver.session() as session:
        # Query 0: Database statistics
        print("\n0️⃣ Database Statistics:")
        result = session.run(
            """
            MATCH (e:Experiment)
            WITH count(e) as total_experiments
            MATCH (c:Compound)
            WITH total_experiments, count(c) as total_compounds
            MATCH (p:Property)
            WITH total_experiments, total_compounds, count(p) as total_properties
            MATCH (cit:Citation)
            RETURN total_experiments, total_compounds, total_properties, count(cit) as total_citations
            """
        )
        record = result.single()
        if record:
            print(f"   Total Experiments: {record['total_experiments']}")
            print(f"   Total Compounds: {record['total_compounds']}")
            print(f"   Total Properties: {record['total_properties']}")
            print(f"   Total Citations: {record['total_citations']}")

        # Query 1: Find experiments with specific compound (including mole fractions)
        print("\n1️⃣ Experiments with 'Choline Chloride' (including mole fractions):")
        result = session.run(
            """
            MATCH (e:Experiment)-[r:HAS_COMPOUND]->(c:Compound)
            WHERE c.commonName CONTAINS 'Choline' OR c.compoundID CONTAINS 'choline'
            RETURN e.experiment_id as experiment_id, c.commonName as compound, 
                   e.source_file as source_file, r.mole_fraction as mole_fraction,
                   e.method as method
            ORDER BY CASE WHEN r.mole_fraction IS NULL THEN 1 ELSE 0 END, r.mole_fraction DESC
            LIMIT 10
            """
        )
        count = 0
        for record in result:
            count += 1
            mole_frac_str = (
                f", mole_fraction={record['mole_fraction']:.3f}"
                if record["mole_fraction"] is not None
                else ""
            )
            method_str = f" [{record['method']}]" if record.get('method') else ""
            print(
                f"   {record['experiment_id']}: {record['compound']}{method_str} ({record['source_file']}){mole_frac_str}"
            )
        if count == 0:
            print("   No experiments found with Choline Chloride")

        # Query 2: Temperature vs Viscosity experiments
        print("\n2️⃣ Temperature vs Viscosity experiments:")
        result = session.run(
            """
            MATCH (e:Experiment)
            WHERE e.temperature IS NOT NULL AND e.viscosity IS NOT NULL
            RETURN e.experiment_id as experiment_id, 
                   e.temperature as temperature, 
                   e.viscosity as viscosity,
                   e.source_file as source_file
            ORDER BY temperature
            LIMIT 10
            """
        )
        count = 0
        for record in result:
            count += 1
            print(
                f"   {record['experiment_id']}: T={record['temperature']:.2f}K, η={record['viscosity']:.4e} ({record['source_file']})"
            )
        if count == 0:
            print("   No temperature-viscosity experiments found")

        # Query 3: Experiments by citation
        print("\n3️⃣ Top citations by experiment count:")
        result = session.run(
            """
            MATCH (e:Experiment)-[:CITED_IN]->(cit:Citation)
            RETURN cit.doi as doi, 
                   cit.title as title, 
                   cit.publication_year as year,
                   count(e) as experiment_count
            ORDER BY experiment_count DESC
            LIMIT 5
            """
        )
        count = 0
        for record in result:
            count += 1
            year_str = f" ({record['year']})" if record.get('year') else ""
            title_short = (record['title'][:60] + "...") if record.get('title') and len(record['title']) > 60 else (record.get('title') or "No title")
            print(f"   [{record['experiment_count']} exps] {record['doi']}{year_str}")
            if record.get('title'):
                print(f"      {title_short}")
        if count == 0:
            print("   No citations found")

        # Query 4: Compound distribution across experiments
        print("\n4️⃣ Most common compounds (by experiment count):")
        result = session.run(
            """
            MATCH (e:Experiment)-[:HAS_COMPOUND]->(c:Compound)
            RETURN c.commonName as compound, 
                   c.compoundID as compoundID,
                   count(e) as experiment_count
            ORDER BY experiment_count DESC
            LIMIT 10
            """
        )
        count = 0
        for record in result:
            count += 1
            compound_id_str = f" ({record['compoundID']})" if record.get('compoundID') else ""
            print(f"   {record['compound']}{compound_id_str}: {record['experiment_count']} experiments")
        if count == 0:
            print("   No compounds found")

        # Query 5: Property types and their frequencies
        print("\n5️⃣ Property types and their frequencies:")
        result = session.run(
            """
            MATCH (e:Experiment)-[:HAS_PROPERTY]->(p:Property)
            RETURN p.propertyType as property_type, count(e) as experiment_count
            ORDER BY experiment_count DESC
            LIMIT 10
            """
        )
        for record in result:
            print(
                f"   {record['property_type']}: {record['experiment_count']} experiments"
            )

        # Query 5b: Parameter types and their frequencies
        print("\n5️⃣b Parameter types and their frequencies:")
        result = session.run(
            """
            MATCH (e:Experiment)-[:HAS_PARAMETER]->(param:Parameter)
            RETURN param.parameter as parameter_type, count(e) as experiment_count
            ORDER BY experiment_count DESC
            LIMIT 10
            """
        )
        for record in result:
            print(
                f"   {record['parameter_type']}: {record['experiment_count']} experiments"
            )

        # Query 6: Experiments with multiple compounds
        print("\n6️⃣ Experiments with multiple compounds:")
        result = session.run(
            """
            MATCH (e:Experiment)-[:HAS_COMPOUND]->(c:Compound)
            WITH e, collect(c.commonName) as compounds
            WHERE size(compounds) > 1
            RETURN e.experiment_id as experiment_id, compounds, size(compounds) as num_compounds
            LIMIT 10
            """
        )
        for record in result:
            print(
                f"   {record['experiment_id']}: {record['num_compounds']} compounds - {', '.join(record['compounds'])}"
            )

        # Query 6b: Compound reuse across experiments (shows compounds appearing in multiple experiments)
        print("\n6️⃣b Compound reuse: Compounds appearing in multiple experiments:")
        result = session.run(
            """
            MATCH (e:Experiment)-[:HAS_COMPOUND]->(c:Compound)
            WITH c, collect(DISTINCT e.experiment_id) as experiments
            WHERE size(experiments) > 1
            RETURN c.commonName as compound, c.compoundID as compoundID, size(experiments) as experiment_count
            ORDER BY experiment_count DESC
            LIMIT 10
            """
        )
        for record in result:
            print(
                f"   {record['compound']} ({record['compoundID']}): appears in {record['experiment_count']} experiments"
            )

        # Query 7: Experiments with specific mole fraction range (using edge properties)
        print("\n7️⃣ Experiments with mole fraction > 0.5:")
        result = session.run(
            """
            MATCH (e:Experiment)-[r:HAS_COMPOUND]->(c:Compound)
            WHERE r.mole_fraction IS NOT NULL AND r.mole_fraction > 0.5
            RETURN e.experiment_id as experiment_id, c.commonName as compound, 
                   r.mole_fraction as mole_fraction
            ORDER BY r.mole_fraction DESC
            LIMIT 10
            """
        )
        for record in result:
            print(
                f"   {record['experiment_id']}: {record['compound']} (mole_fraction={record['mole_fraction']})"
            )

        # Query 7b: Experiments with multiple compounds and their mole fractions
        print("\n7️⃣b Experiments with multiple compounds and their mole fractions:")
        result = session.run(
            """
            MATCH (e:Experiment)-[r:HAS_COMPOUND]->(c:Compound)
            WITH e, collect({compound: c.commonName, mole_fraction: r.mole_fraction}) as compounds
            WHERE size(compounds) > 1
            RETURN e.experiment_id as experiment_id, 
                   compounds, 
                   size(compounds) as num_compounds,
                   e.source_file as source_file
            LIMIT 10
            """
        )
        count = 0
        for record in result:
            count += 1
            compounds_str = ", ".join(
                [
                    (
                        f"{c['compound']}(x={c['mole_fraction']:.3f})"
                        if c["mole_fraction"] is not None
                        else f"{c['compound']}"
                    )
                    for c in record["compounds"]
                ]
            )
            print(f"   {record['experiment_id']} [{record['num_compounds']} compounds]: {compounds_str}")
            print(f"      Source: {record['source_file']}")
        if count == 0:
            print("   No multi-compound experiments found")

        # Query 8: Property and Parameter combinations
        print("\n8️⃣ Common property-parameter combinations:")
        result = session.run(
            """
            MATCH (e:Experiment)-[:HAS_PROPERTY]->(p:Property)
            MATCH (e)-[:HAS_PARAMETER]->(param:Parameter)
            RETURN p.propertyType as property_type,
                   param.parameter as parameter_type,
                   count(e) as experiment_count
            ORDER BY experiment_count DESC
            LIMIT 10
            """
        )
        count = 0
        for record in result:
            count += 1
            print(f"   {record['property_type']} × {record['parameter_type']}: {record['experiment_count']} experiments")
        if count == 0:
            print("   No property-parameter combinations found")

        # Query 9: Experiments with uncertainty data
        print("\n9️⃣ Experiments with uncertainty information:")
        result = session.run(
            """
            MATCH (e:Experiment)-[r:HAS_PROPERTY]->(p:Property)
            WHERE r.uncertainty IS NOT NULL
            WITH e, count(r) as properties_with_uncertainty
            RETURN count(e) as experiments_with_uncertainty,
                   avg(properties_with_uncertainty) as avg_properties_per_experiment
            """
        )
        record = result.single()
        if record and record['experiments_with_uncertainty'] > 0:
            print(f"   {record['experiments_with_uncertainty']} experiments have uncertainty data")
            print(f"   Average {record['avg_properties_per_experiment']:.1f} properties with uncertainty per experiment")
        else:
            print("   No uncertainty data found")

        # Query 10: Temperature range analysis
        print("\n🔟 Temperature range analysis:")
        result = session.run(
            """
            MATCH (e:Experiment)
            WHERE e.temperature IS NOT NULL
            RETURN min(e.temperature) as min_temp,
                   max(e.temperature) as max_temp,
                   avg(e.temperature) as avg_temp,
                   count(e) as temp_experiments
            """
        )
        record = result.single()
        if record and record['temp_experiments'] > 0:
            print(f"   Temperature range: {record['min_temp']:.2f}K - {record['max_temp']:.2f}K")
            print(f"   Average temperature: {record['avg_temp']:.2f}K")
            print(f"   Total experiments with temperature: {record['temp_experiments']}")
        else:
            print("   No temperature data found")


def main():
    parser = argparse.ArgumentParser(description="Import FAIRFluids data into Neo4j")
    parser.add_argument("--uri", default="bolt://localhost:7687", help="Neo4j URI")
    parser.add_argument("--user", default="neo4j", help="Neo4j username")
    parser.add_argument("--password", default="password", help="Neo4j password")
    parser.add_argument(
        "--json-dir", default="test_json_only", help="Directory with JSON files"
    )
    parser.add_argument("--clear", action="store_true", help="Clear existing data")
    parser.add_argument("--queries", action="store_true", help="Run example queries")

    args = parser.parse_args()

    print("🗄️  FAIRFluids Neo4j Import - Experiment-Centered Graph")
    print("=" * 50)

    importer = FAIRFluidsNeo4jImporter(args.uri, args.user, args.password)

    try:
        if args.clear:
            importer.clear_database()

        importer.create_constraints()
        importer.import_from_json_files(args.json_dir)

        if args.queries:
            run_example_queries(importer.driver)

    finally:
        importer.close()

    print("\n✅ Neo4j import completed!")
    print("\n💡 Example Cypher queries you can now run in Neo4j Browser:")
    print(
        """
    // 1. Database Statistics
    MATCH (e:Experiment)
    WITH count(e) as total_experiments
    MATCH (c:Compound)
    WITH total_experiments, count(c) as total_compounds
    MATCH (p:Property)
    RETURN total_experiments, total_compounds, count(p) as total_properties
    
    // 2. Find experiments with specific compound (including mole fractions)
    MATCH (e:Experiment)-[r:HAS_COMPOUND]->(c:Compound)
    WHERE c.commonName CONTAINS 'Water' OR c.commonName CONTAINS 'Glycerol'
    RETURN e.experiment_id, c.commonName, e.method, r.mole_fraction
    ORDER BY CASE WHEN r.mole_fraction IS NULL THEN 1 ELSE 0 END, r.mole_fraction DESC
    LIMIT 20
    
    // 3. Temperature vs Viscosity experiments
    MATCH (e:Experiment)
    WHERE e.temperature IS NOT NULL AND e.viscosity IS NOT NULL
    RETURN e.experiment_id, e.temperature as temperature, e.viscosity as viscosity
    ORDER BY temperature
    LIMIT 50
    
    // 4. Experiments with multiple compounds
    MATCH (e:Experiment)-[:HAS_COMPOUND]->(c:Compound)
    WITH e, collect(c.commonName) as compounds
    WHERE size(compounds) > 1
    RETURN e.experiment_id, compounds, size(compounds) as num_compounds
    ORDER BY num_compounds DESC
    
    // 5. Find experiments by citation
    MATCH (e:Experiment)-[:CITED_IN]->(cit:Citation)
    WHERE cit.doi CONTAINS '10.1016'
    RETURN cit.doi, cit.title, cit.publication_year, count(e) as experiment_count
    ORDER BY experiment_count DESC
    
    // 6. Property analysis with uncertainty
    MATCH (e:Experiment)-[r:HAS_PROPERTY]->(p:Property)
    WHERE p.propertyType = 'viscosity' AND r.uncertainty IS NOT NULL
    RETURN e.experiment_id, r.value as viscosity, r.uncertainty, 
           (r.uncertainty / r.value * 100) as relative_uncertainty_percent
    ORDER BY relative_uncertainty_percent
    
    // 7. Parameter analysis
    MATCH (e:Experiment)-[r:HAS_PARAMETER]->(param:Parameter)
    WHERE param.parameter CONTAINS 'temperature'
    RETURN e.experiment_id, param.parameter, r.value as temperature, r.uncertainty
    ORDER BY temperature
    
    // 8. Experiments with specific parameter and property combination
    MATCH (e:Experiment)-[rp:HAS_PROPERTY]->(p:Property)
    MATCH (e)-[rparam:HAS_PARAMETER]->(param:Parameter)
    WHERE p.propertyType = 'viscosity' AND param.parameter CONTAINS 'temperature'
    RETURN e.experiment_id, rparam.value as temperature, rp.value as viscosity,
           e.source_file
    ORDER BY temperature
    
    // 9. Parameter with associated compounds
    MATCH (param:Parameter)-[:ASSOCIATED_WITH]->(c:Compound)
    RETURN param.parameter, collect(DISTINCT c.commonName) as associated_compounds
    ORDER BY size(associated_compounds) DESC
    
    // 10. Compound combination analysis
    MATCH (e:Experiment)-[:HAS_COMPOUND]->(c:Compound)
    WITH e, collect(c.commonName) as compounds
    RETURN compounds, count(e) as experiment_count
    ORDER BY experiment_count DESC
    LIMIT 20
    
    // 11. Experiments with mole fractions
    MATCH (e:Experiment)-[r:HAS_COMPOUND]->(c:Compound)
    WHERE r.mole_fraction IS NOT NULL
    RETURN e.experiment_id, c.commonName, r.mole_fraction
    ORDER BY r.mole_fraction DESC
    LIMIT 50
    
    // 12. Experiments with multiple compounds and their mole fractions
    MATCH (e:Experiment)-[r:HAS_COMPOUND]->(c:Compound)
    WITH e, collect({compound: c.commonName, mole_fraction: r.mole_fraction}) as compounds
    WHERE size(compounds) > 1
    RETURN e.experiment_id, compounds, e.source_file
    LIMIT 20
    
    // 13. Find experiments with specific mole fraction range
    MATCH (e:Experiment)-[r:HAS_COMPOUND]->(c:Compound)
    WHERE r.mole_fraction > 0.5 AND r.mole_fraction < 0.8
    RETURN e.experiment_id, c.commonName, r.mole_fraction
    ORDER BY r.mole_fraction DESC
    
    // 14. Property and Parameter combinations
    MATCH (e:Experiment)-[:HAS_PROPERTY]->(p:Property)
    MATCH (e)-[:HAS_PARAMETER]->(param:Parameter)
    RETURN p.propertyType, param.parameter, count(e) as count
    ORDER BY count DESC
    
    // 15. Temperature range analysis
    MATCH (e:Experiment)
    WHERE e.temperature IS NOT NULL
    RETURN min(e.temperature) as min_temp,
           max(e.temperature) as max_temp,
           avg(e.temperature) as avg_temp,
           count(e) as experiments
    
    // 16. Experiments with uncertainty data
    MATCH (e:Experiment)-[r:HAS_PROPERTY]->(p:Property)
    WHERE r.uncertainty IS NOT NULL
    WITH e, count(r) as properties_with_uncertainty
    RETURN count(e) as experiments_with_uncertainty,
           avg(properties_with_uncertainty) as avg_properties_per_experiment
    
    // 17. Most common compound pairs
    MATCH (e:Experiment)-[:HAS_COMPOUND]->(c1:Compound)
    MATCH (e)-[:HAS_COMPOUND]->(c2:Compound)
    WHERE c1.commonName < c2.commonName
    RETURN c1.commonName as compound1, c2.commonName as compound2, count(e) as count
    ORDER BY count DESC
    LIMIT 20
    """
    )


if __name__ == "__main__":
    main()
