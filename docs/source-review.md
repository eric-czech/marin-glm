# Source review and resolved catalogue fields

The catalogue distinguishes a source omission from a protocol choice, and a model’s participation in a benchmark from execution of every assay. Reviews cover the indexed definitions and identified releases. They do not reproduce model training or reported performance from raw experimental signals.

## Protocol fields

All 1,417 protocols have a source review. Each remaining null embedding requirement, fitted component or selection rule has a cited interpretation in `protocol_field_reviews`. There is no generic “Not established” UI fallback.

| Disposition | Meaning |
| --- | --- |
| Model-dependent | A dataset definition or benchmark supports several interfaces; the model-specific protocol determines the requirement. |
| Not applicable | No additional predictor is fitted, or the result is a descriptive projection rather than supervised selection. This says nothing about historical backbone training. |
| Not reported | The identified method omits the particular rule. The field describes the omission and cites that method. |
| Conflicting | Inspected sources specify different interfaces or values; both remain explicit. |

The review fills 373 formerly null fitted-component fields, 164 selection fields and two embedding flags. Other nulls receive explicit interpretations; they are not converted to invented values. [Field-level report](../data/completion-review.json).

Specific corrections include TraitGym’s chromosome-grouped inner grid search, GENEB’s fixed classifier configuration, mRNABench’s fixed classification probes, BOTANIC-1’s early stopping and SAE feature selection, NTv3’s validation selection, and GeneCAD’s validation monitoring without early stopping. Each protocol links its primary method or implementation.

NABench’s paper describes hidden representations, while its released Evo extractor saves nucleotide log probabilities. The catalogue preserves that discrepancy and does not assert which arrays were used by an unreleased downstream runner. [Paper §3.4](https://arxiv.org/html/2511.02888v1), [released extractor](https://github.com/mrzzmrzz/NABench/blob/99c8681ec1eab706e10ff90a5c329dcf184cc1d1/scripts/evo/seq_emb.py#L178-L193).

## Dataset identity and phenotype

**NABench / Gregory_2018_mRNA.** All 287 scalar scores match uniquely to `d11/lib.loess.r1`, column AI of Findlay’s original BRCA1 table. Every match also agrees with transcript-strand alleles and the same genomic coordinate offset; all belong to experiment X20. The largest absolute score difference is below 9 × 10⁻¹⁶. No other numerical column matches all rows. This identifies a replicate-1 day-11/library genomic-DNA selection score, despite the benchmark filename. It is neither `mean.rna.score` nor `function.score.mean`.

The task’s target, application and feature assignments now follow that measurement. Its sequence contains an `X` separator, and the source cohort contains coding, intronic and splice-related variants; it is not a CDS-only task. Missing benchmark folds and ridge-selection details remain separate source omissions. [Pinned benchmark rows](https://github.com/mrzzmrzz/NABench/blob/99c8681ec1eab706e10ff90a5c329dcf184cc1d1/data/Gregory_2018_mRNA.csv#L2-L4), [original score table](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-018-0461-z/MediaObjects/41586_2018_461_MOESM3_ESM.xlsx), [all row correspondences and column comparisons](../data/nabench-findlay-target-review.json), [reproduction script](../scripts/review_findlay_target.py).

**Original NT / GUE H3 and H4.** Complete native sequence–label pools are identical: 14,965 H3 rows and 14,601 H4 rows. Their partition assignments differ. Each pair is now one dataset–target record with separate releases and protocols; old task links redirect. The catalogue therefore contains 739 task records rather than 741.

| Target | NT train → GUE test | GUE train → NT test |
| --- | ---: | ---: |
| H3 | 1,347 / 1,497 | 1,191 / 1,497 |
| H4 | 1,336 / 1,461 | 1,188 / 1,461 |

These are cross-release exposures. They do not imply within-release train/test overlap. Published evaluations cannot be combined as independent cohorts, and using the other release’s training rows would invalidate the corresponding test holdout. All ten files matched their previously recorded hashes. Only summaries were retained; no raw files were stored. [Partition comparisons, pinned files and hashes](../data/nt-gue-identity-review.json), [reproduction script](../scripts/review_nt_gue_identity.py).

**PlantCAD2 context variants.** Figure 4D’s extended-context ACR experiment belongs to the multispecies training arm; Figure 4G covers maize cell-type accessibility. Four unsupported extended-context assignments to the Arabidopsis-only arm were removed. The 600-bp target and longer input contexts remain distinct. [Paper Figure 4 and Results](https://doi.org/10.1016/j.xgen.2026.101329).

**BOTANIC-1 donor usage.** Classification uses 885 intermediate donors, 885 constitutive donors and 885 decoys. Correlation uses a broader 3,254-donor panel, whose added donors do not participate in feature/threshold fitting. The stated chromosome split lacks a separately supplied assignment and held-out classification denominator; the known panel totals are not presented as that denominator. [Report §4.8.3](https://huggingface.co/spaces/living-models/botanic1-report/resolve/1a1826804938e6320e20f037956b3818b9c40700/botanic1-report-v3.pdf#page=59).

## Reference RNA and assay hosts

Primary assay papers resolve additional RNA references without treating experimental hosts as sequence origins. The Soo assay uses a *Tetrahymena thermophila* intron in *E. coli*. The Zhang 5S assay uses *Vibrio proteolyticus* RNA in an *E. coli* knockout host. Kobori's J1/2 and P4 aptazymes combine *Anopheles gambiae* and *Bacillus subtilis* components; they are recorded as engineered constructs. [Soo methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC7877785/), [Zhang §§2.1–2.2](https://zdzlab.einsteinmed.edu/m/publications/19041908.pdf#page=2), [Kobori Figure 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC4513843/).

The Peri reference accession DQ103524.1 resolves to *Azoarcus olearius*, formerly *Azoarcus* sp. BH72. Rice twister references, human LINE-1/OR4K15 and 81-nt CPEB3 references, selected ligase/polymerase/aptamer constructs, and yeast tRNA origins are distinguished. Mammalian CPEB3 constructs without a species accession retain the supported mammalian assignment. An environmental twister and a hammerhead construct lack an exact source-organism accession; their notes identify that specific limit instead of inferring a species from the RNA family. [Peri reference](https://pmc.ncbi.nlm.nih.gov/articles/PMC8890501/), [GenBank accession](https://www.ncbi.nlm.nih.gov/nuccore/DQ103524.1), [reference decisions and access receipts](../data/rna-reference-review.json).

HDV RNA is assigned to Ribozyviria. The tobacco ringspot satellite RNA is kept separate from its helper virus's Riboviria lineage and from the plant host. Different CPEB3 or twister assays are not merged on the basis of a shared RNA family or row count. [Roberts assay definitions](https://pmc.ncbi.nlm.nih.gov/articles/PMC9901934/), [HDV taxonomy](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=12475), [satellite taxonomy](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=31504).

## Model usage and source availability

The original Evo 2 inventory contains 83 task/panel records, exactly matching its original-paper associations. This finite inventory supports “not listed in original-paper inventory” for other catalogue records. External task-level use and aggregate benchmark participation remain separate. NABench lists Evo 1, Evo 2 and GENERator without supplying a complete model × assay × protocol execution manifest; those associations are recorded in `model_collection_evaluations`.

Source access was checked again. BaseSpace redirects to login; tested Synapse file-handle requests deny anonymous access; the five DNALongBench Dataverse APIs return 403. DeepD DC2, Cerberus/LOAM full text and AlphaGenome2 supplements remain blocked at identified publisher endpoints. Carbon APIs return 401. These are precise access observations, not proof that the underlying data do not exist. Large-file exclusions remain explicit, and omitted manuscript details are not filled from predecessor models or presumed defaults. [Requests, statuses, revisions and hashes](../data/completion-source-checks.json).
