### BiocatalyticExpression

  - organism
      - Type: Organism
  - construct
      - Type: Construct
  - gene_delivery
      - Type: GeneDelivery
  - expression_control
      - Type: ExpressionControl
  - transcription
      - Type: Transcription
  - protein_expression
      - Type: ProteinExpression
  - localization_module
      - Type: LocalizationModule
  - bioprocess_performance
      - Type: BioprocessPerformance

### Organism

  - origin_organism
      - Type: string
      - Description: STRENDA:The specific species or source from which the enzyme is derived or isolated. It includes information about the genus and species of the organism.
  - production_organism
      - Type: string
      - Description: STRENDA: Information about the organism in which the biocatalyst was produced is crucial in the context of heterologous gene expression. If the production strain was purchased, more detailed information on the manufacturer and the organism should be provided.
  - po_strain
      - Type: string

### Construct

  - gene_name
      - Type: string
      - Description: A gene name encoding the target enzyme/protein. The name is specific and can be in different formats such as an acronym associated with enzyme nomenclature, an accession number (e.g. GenBank, UniProt), or a newly created code designated for a computer-generated protein.
  - sequence
      - Type: string
      - Description: The full DNA sequence of the gene you are trying to express. This includes the gene itself and any control elements (like the promoter, terminator, and tags). DNA sequences are usually written using the letters A, T, C, and G for precise reporting. IUPAC nucleotide notatition may also be feasible. This can be obtained experimentally through DNA sequencing or computationally through gene synthesis or retrieval from databases. [computational] [experimental]
  - promoter_strength
      - Type: float
      - Description: Describes how strongly a promoter initiates transcription. A stronger promoter will lead to more mRNA being produced. Can be measured experimentally using reporter genes (e.g., green fluorescent protein (GFP) or luciferase) whose expression is driven by the promoter of interest. The activity is quantified via fluorescence or luminescence measurements. [experimental]
      - Unit: Relative fluorescence units (RFU), or fold change compared to a reference promoter
  - codon_optimization_status
      - Type: boolean
      - Description: Indicates whether the coding sequence has been codon-optimized for the host organism. Codon optimization is a computational process that involves changing the nucleotide sequence of a gene to match the codon usage bias of the host organism, improving translation efficiency. [computational]
      - Unit: true / false
  - plasmid_copy_number
      - Type: integer
      - Description: Number of copies of the plasmid (DNA molecule) present inside each cell. Higher copy number usually means more gene expression, but can stress the host cell. This can be determined experimentally using quantitative PCR (qPCR) to compare the plasmid DNA amount to a known single-copy chromosomal gene. [experimental]
      - Unit: Copies per cell
  - selections_marker
      - Type: string
      - Description: Antibiotic resistance
  - regulatory_element_activity
      - Type: float
      - Description: Measures how much regulatory DNA sequences (like repressors or operators) affect the expression of your gene - either by increasing or decreasing transcription. This is often measured experimentally using reporter assays, comparing the expression level with and without the regulatory element present. [experimental]
      - Unit: Fold repression or activation

### GeneDelivery

  - delivery_type
      - Type: DeliveryType
      - Description: The overarching method of gene delivery into cells. Can be one of: transformation, transfection, or transduction.
  - delivery_method
      - Type: DeliveryMethod[]
      - Description: The specific technique used depending on the delivery type.
  - delivery_parameters
      - Type: DeliveryParameters[]
      - Description: Method-specific physical or chemical parameters used to optimize gene delivery (e.g., voltage, temperature, DNA amount).
  - delivery_efficiency
      - Type: float
      - Unit: %
      - Description: The percentage of cells that successfully receive and express the gene. This is an experimental measurement, typically performed by flow cytometry or microscopy by counting the number of fluorescent cells after delivery of a reporter plasmid (e.g., containing GFP). [experimental]
  - post_delivery_steps
      - Type: string[]
      - Description: Any steps performed after delivery to improve expression or select transformed cells (e.g., antibiotic selection, recovery incubation).

### DeliveryParameters

  - voltage
      - Type: float
      - Unit: Volts (V)
      - Description: Electroporation voltage, if applicable.
  - current
      - Type: float
      - Unit: Amps (A)
      - Description: Electroporation current, if used.
  - temperature
      - Type: float
      - Unit: °C
      - Description: Temperature during (e.g., heat shock).
  - dna_amount
      - Type: float
      - Description: Quantity of DNA/RNA/plasmid used.
      - Unit: µg or ng
  - reagent
      - Type: string[]
      - Description: List of the reagents used.
  - reagent_concentration
      - Type: float
      - Unit: mg/mL or mM
      - Description: Concentration of chemical or biological reagents (e.g., lipids, CaCl₂, viral particles).
  - delivery_duration
      - Type: float
      - Description: The total time needed for successful gene delivery.
      - Unit: min or h
  - incubation_time
      - Type: float
      - Unit: min or h
      - Description: Time cells are incubated with reagents after delivery.

### ExpressionControl

  - expression_mode
      - Type: ExpressionMode
      - Description: Describes whether the gene is always turned on (constitutive) or only turned on when an inducer is added (inducible).
  - inducers
      - Type: string[]
      - Description: Lists which chemicals (like IPTG, arabinose) can be added to the culture to activate the gene expression. These interact with the promoter.
  - inducer_concentration
      - Type: float
      - Unit: mg/mol
  - induction_fold_change
      - Type: float
      - Description: Tells you how much more expression happens when the inducer is added. For example, a fold change of 50 means expression increases 50x after induction. This is an experimental measurement. It is calculated by dividing the protein or mRNA expression level in the induced state by the level in the uninduced state. For example: `Fold Change = Expression_induced / Expression_uninduced` [experimental]
      - Unit: Fold change
  - feedback_regulation
      - Type: boolean
      - Description: Indicates whether the gene expression system includes feedback. For example, the protein might inhibit its own production - a negative feedback loop.
      - Unit: true / false

### Transcription

  - mRNA_abundance
      - Type: float
      - Description: Measures how many copies of mRNA are produced from the DNA. This mRNA is what the ribosomes will use to make protein. Measured experimentally using techniques like quantitative PCR (qPCR) or RNA-seq. [experimental]
      - Unit: Transcripts per cell, Ct value, or TPM/FPKM
  - transcription_rate
      - Type: float
      - Description: How fast RNA polymerase makes mRNA from the gene. A faster rate usually leads to more protein being made. This is an experimental measurement, often determined using techniques that measure the rate of RNA synthesis in real time, such as nuclear run-on assays. [experimental]
      - Unit: Transcripts per minute per cell
  - mRNA_half_time
      - Type: float
      - Description: How long mRNA lasts before being degraded. Short-lived mRNA means less time for protein to be made. This is an experimental measurement, typically determined by blocking transcription and measuring the decay of specific mRNA over time using qPCR. [experimental]
      - Unit: Minutes

  - promoter_induction_ratio
      - Type: float
      - Description: Shows how much more mRNA is made when an inducible promoter is activated. The ratio is calculated by dividing the mRNA abundance after induction by the mRNA abundance before induction. [experimental]
      - Unit: Fold increase
  - terminator_efficiency
      - Type: float
      - Description: Describes how efficiently transcription stops after the gene. Inefficient terminators can cause read-through. This is an experimental measurement, often determined by comparing the amount of mRNA that terminates at the intended site versus that which reads through, using techniques like qPCR. [experimental]
      - Unit: %

### ProteinExpression

  - expression_time
      - Type: float
      - Description: A time that is used to induce enzyme/protein expression in hours.
  - expression_temp
      - Type: float
      - Description: A temperature that is used to induce enzyme/protein expression in °C.
  - expression_culture_medium
      - Type: string
      - Description: A liquid culture that is used for host cell culture and gene expression.
  - translation
      - Type: Translation
  - post_translation_folding
      - Type: PostTranslationFolding

### Translation

  - protein_abundance
      - Type: float
      - Description: Total amount of protein made from the mRNA. This includes both functional and non-functional forms. Measured experimentally using methods like Western blotting, ELISA, or mass spectrometry. [experimental]
      - Unit: µg/mL or relative intensity
  - translation_efficiency
      - Type: float
      - Description: How efficiently mRNA is turned into protein. This depends on factors like codon usage and ribosome availability. This is a calculation. It is calculated by dividing the protein abundance by the mRNA abundance. `Translation Efficiency = Protein_abundance / mRNA_abundance`. [calculation]
      - Unit: Relative ratio or protein/mRNA
  - rbs_strength
      - Type: float
      - Description: Describes how efficiently the ribosome binding site initiates translation. This is typically measured experimentally using a reporter system, like the Ribosome Binding Site Calculator which uses a model to predict the strength of an RBS based on its sequence and context. [computational: https://docs.denovodna.com/docs/rbs-calculator]
      - Unit: Arbitrary units or relative to a standard RBS
  - ribosome_occupancy
      - Type: float
      - Description: Shows how many ribosomes are actively translating the mRNA. More ribosomes usually mean higher translation. This is measured experimentally via ribosome profiling (Ribo-seq), which maps the positions of ribosomes on mRNA. [experimental]
      - Unit: Ribosome footprints per kilobase
  - codon_adaptation_index
      - Type: float
      - Description: CAI. A number between 0 and 1 that tells you how well the gene uses codons preferred by the host organism. A higher value usually means better translation. This is a computational value calculated based on the gene sequence and the host's codon usage table. [computational: doi: 10.1038/s41598-020-74091-z]
      - Unit: Score (0.0–1.0)
  - tRNA_adaptation_index
      - Type: float
      - Description: Indicates how well the gene’s codons match the available tRNA pool in the host. This is a computational value calculated based on the gene sequence and the host's tRNA gene copy number. [computational]
      - Unit: Score (0.0–1.0)

### PostTranslationFolding

  - soluble_protein_fraction
      - Type: float
      - Description: Shows how much of the protein is properly folded and remains in the soluble part of the cell. This is an experimental measurement, obtained by lysing the cells, centrifuging to separate soluble and insoluble fractions, and then quantifying the protein in each fraction (e.g., via SDS-PAGE or Western blot). [experimental]
      - Unit: %
  - enzymatic_activity
      - Type: float
      - Description: How well the protein performs its function (e.g., catalyzing a chemical reaction). This is an experimental measurement determined by a standardized assay that measures the rate of substrate conversion or product formation. [experimental]
      - Unit: U/mg or µmol/min/mg
  - protein_aggregation_level
      - Type: float
      - Description: Proportion of total protein that is clumped together into insoluble, non-functional aggregates. This is an experimental measurement, often quantified via image analysis of fluorescently tagged proteins or by SDS-PAGE analysis of the insoluble fraction after cell lysis. [experimental]
      - Unit: %
  - thermal_stability
      - Type: float
      - Description: The temperature at which half of the protein is unfolded or denatured. This is an experimental measurement, typically determined by techniques like differential scanning fluorimetry (DSF) or circular dichroism (CD) spectroscopy. [experimental]
      - Unit: °C
  - proteolytic_degradation_rate
      - Type: float
      - Description: Speed at which the protein is broken down by cellular proteases. This is an experimental measurement. It is determined by blocking protein synthesis and measuring the decrease in the target protein's concentration over time (half-life) using Western blotting or other quantification methods. [experimental]
      - Unit: Minutes or hours (half-life)
  - chaperone_coexpression
      - Type: string[]
      - Description: Lists any molecular chaperones co-expressed to assist in proper protein folding.
      - Unit: -

### LocalizationModule

  - localization
      - Type: Localization
      - Description: The intended location of the protein - inside the cell (cytoplasm), between membranes (periplasm), or outside the cell (secreted).
      - Unit: -
  - signal_peptide_sequence
      - Type: string
      - Description: DNA or protein sequence of the secretion signal tag used to export the protein. This is a computational or experimental value. It can be found in sequence databases or designed using computational tools. [computational] [experimental]
      - Unit: -
  - secreted_protein_yield
      - Type: float
      - Description: Amount of protein found in the culture medium, useful for secreted enzymes or therapeutic proteins. This is an experimental measurement, obtained by quantifying the protein in the cell-free culture supernatant using methods like ELISA or SDS-PAGE. [experimental]
      - Unit: µg/mL or U/mL
  - secretion_efficiency
      - Type: float
      - Description: What fraction of the total produced protein is actually secreted. This is a calculation. It is calculated by dividing the secreted protein yield by the total protein yield (secreted plus intracellular). `Secretion Efficiency = (Secreted_protein_yield / Total_protein_yield) * 100`. [calculation]
      - Unit: %
  - signal_peptide_cleavage_efficiency
      - Type: float
      - Description: After secretion, signal peptides should be removed. This shows how efficiently that cleavage happens. This is an experimental measurement, typically determined by mass spectrometry or Western blot analysis to compare the molecular weight of the secreted protein to its theoretical size without the signal peptide. [experimental]
      - Unit: %

### BioprocessPerformance

  - biomass_od_600
      - Type: float
      - Description: A measure of how many cells are growing in your culture. Used as a baseline for other calculations. This is an experimental measurement using a spectrophotometer to measure the optical density at 600 nm. [experimental]
      - Unit: OD600
  - total_protein_yield
      - Type: float
      - Description: How much recombinant protein is made per liter of culture. This includes all forms (soluble or not). This is an experimental measurement, determined by lysing the cells and quantifying the total protein using assays like Bradford, BCA, or SDS-PAGE densitometry, scaled to the culture volume. [experimental]
      - Unit: mg/L
  - specific_productivity
      - Type: float
      - Description: Enzyme activity or product formed per unit of biomass. This shows how efficient the cells are. This is a calculation. It is calculated by dividing the volumetric productivity or enzymatic activity by the biomass concentration (OD600 or dry cell weight). `Specific Productivity = Volumetric_productivity / Biomass_concentration`. [calculation]
      - Unit: U/OD600 or g product / g dry cell weight
  - volumetric_productivity
      - Type: float
      - Description: Total product formed per liter per hour - useful in industrial scale-up. This is a calculation. It is calculated by dividing the final product titer by the total culture time. `Volumetric Productivity = Product_titer / Total_time`. [calculation]
      - Unit: g/L/h or U/L/h
  - yield
      - Type: float
      - Description: Tells you how much of the theoretical maximum product you actually obtained, based on substrate input. This is a calculation. It is calculated by dividing the final product titer by the initial substrate concentration (stoichiometrically adjusted) and multiplying by 100. `Yield = (Final_product_titer / Initial_substrate_concentration) * 100`. [calculation]
      - Unit: %
  - substrate_concentration
      - Type: float
      - Description: Initial concentration of the biocatalytic substrate.
      - Unit: mM or g/L
  - product_titer
      - Type: float
      - Description: Final concentration of the desired product in the culture. This is an experimental measurement, typically determined by HPLC, GC, or a colorimetric assay. [experimental]
      - Unit: g/L or U/L
  - culture_conditions
      - Type: string
      - Description: Experimental conditions including media, temperature, pH, shaking speed, etc.
      - Unit: -

### ExpressionMode

```python
CONSTITUTIVE=constitutive
INDUCED=induced
```

### DeliveryType

```python
TRANSFORMATION=transformation
TRANSFECTION=transfection
TRANSDUCTION=transduction
```

### DeliveryMethod

```python
HEATSHOCK = heatshock
ELECTROPORATION = electroporation
SONOPORATION = sonoporation
CHEMICAL = chemical
LIPOFECTION = lipofection
VIRAL = viral
MICROINJECTION = microinjection
HYDRODYNAMIC = hydrodynamic
BIOLISTICS = biolistics
MAGNETOFECTION = magnetofection
OTHER = other
```

### Localization
```python
CYPTOPLASM =cytoplasm
PERIPLASM=periplasm
SECRETED=secreted
```