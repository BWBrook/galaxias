# Bibliographic search log

Search date: 2026-10-04 (Australia/Hobart). Scope: librarian-style verification for manuscript planning; no simulator, data, or manuscript source files were changed.

## Search and metadata queries

Web searches were run in bounded batches using the following exact queries:

1. `MacKenzie 2002 Estimating site occupancy rates when detection probabilities are less than one DOI publisher`
2. `MacKenzie Royle 2005 Designing occupancy studies DOI publisher`
3. `Royle Nichols 2003 Estimating abundance repeated presence absence point counts DOI`
4. `Solow 2005 Inferring extinction from a sighting record DOI`
5. `Boakes McGowan Fuller Distorted views of biodiversity spatial temporal bias species occurrence DOI`
6. `Rout Salomon McCarthy Using sighting records to declare extinction DOI`
7. `Choosing optimal trigger points ex situ in toto conservation single population threatened species 2022 DOI PMC8989361`
8. `Tenhumberg Linking wild and captive populations to maximize species persistence DOI`
9. `McGowan Traylor-Holzer Leus 2017 IUCN guidelines ex situ management DOI`
10. `Goldberg critical considerations application environmental DNA methods detect aquatic species 2016 DOI`
11. `Deiner environmental DNA metabarcoding transforming survey animal plant communities 2017 DOI`
12. `Smart Tingley Weeks van Rooyen McCarthy environmental DNA sampling more sensitive traditional surveys detecting fish DOI`
13. `Wood 2010 Statistical inference for noisy nonlinear ecological dynamic systems DOI`
14. `Beaumont Zhang Balding 2002 approximate Bayesian computation population genetics DOI`
15. `Robert Cornuet Marin Pillai Tavaré 2011 Lack of confidence approximate Bayesian computation model choice DOI`
16. `Cranmer Brehmer Louppe 2020 Frontier of simulation-based inference DOI`
17. `Kennedy O'Hagan 2001 Bayesian calibration of computer models DOI`
18. `Brynjarsdottir O'Hagan 2014 Learning about physical parameters effect of model discrepancy DOI`
19. `Rykiel 1996 Testing ecological models meaning validation DOI`
20. `Grimm 2020 ODD protocol update guidance DOI 109105`
21. `Morris White Crowther 2019 using simulation studies evaluate statistical methods DOI`
22. `Owen 2013 Monte Carlo theory methods computation book`
23. `Vehtari 2024 Pareto smoothed importance sampling DOI`
24. `Talts Betancourt Simpson Vehtari 2018 Validating Bayesian Inference Simulation-Based Calibration DOI`
25. `Conn 2018 guide model checking ecological hierarchical models DOI`
26. `Galaxias eDNA galaxias detection environmental DNA fish Australia primary study`
27. `Galaxias eDNA detection Galaxias maculatus environmental DNA`
28. `site:doi.org Rout Salomon McCarthy Using sighting records to declare extinction`
29. `"Using sighting records to declare" Rout Salomon McCarthy`

Crossref REST metadata was then queried directly, sequentially, for these exact DOI endpoints with a descriptive User-Agent:

- `https://api.crossref.org/works/10.1890/0012-9658(2002)083[2248:ESORWD]2.0.CO;2`
- `https://api.crossref.org/works/10.1111/j.1365-2664.2005.01098.x`
- `https://api.crossref.org/works/10.1038/nature09319`
- `https://api.crossref.org/works/10.1073/pnas.1102900108`

The direct Crossref records agreed on DOI, title, year and venue for all four checks. An initial title-query attempt returned HTTP 400/429 responses (invalid field selection and rate limiting); it was not treated as evidence and was followed by direct DOI endpoint checks.

## Primary and repository sources used

- Wiley/ESA record for MacKenzie et al. 2002: https://esajournals.onlinelibrary.wiley.com/doi/abs/10.1890/0012-9658%282002%29083%5B2248%3AESORWD%5D2.0.CO%3B2
- USGS record for MacKenzie & Royle 2005: https://pubs.usgs.gov/publication/5224604
- Wiley/ESA record for Royle & Nichols 2003: https://esajournals.onlinelibrary.wiley.com/doi/full/10.1890/0012-9658%282003%29084%5B0777%3AEAFRPA%5D2.0.CO%3B2
- ScienceDirect/PubMed record for Solow 2005: https://doi.org/10.1016/j.mbs.2005.02.001
- PLOS/PMC record for Boakes et al. 2010: https://pmc.ncbi.nlm.nih.gov/articles/PMC2879389/
- Wiley record/PDF for Rout et al. 2009: https://doi.org/10.1111/j.1365-2664.2008.01586.x
- PLOS/PMC record for Brown et al. 2022: https://pmc.ncbi.nlm.nih.gov/articles/PMC8989361/
- University of Nebraska repository for Tenhumberg et al. 2004: https://digitalcommons.unl.edu/bioscifacpub/119/
- Wiley/Conservation Biology record for McGowan et al. 2017: https://conbio.onlinelibrary.wiley.com/doi/full/10.1111/conl.12285
- USGS/Wiley record for Goldberg et al. 2016: https://pubs.usgs.gov/publication/70178375
- PubMed/repository record for Deiner et al. 2017: https://pubmed.ncbi.nlm.nih.gov/28921802/
- Wiley/ESA record for Smart et al. 2015: https://esajournals.onlinelibrary.wiley.com/doi/abs/10.1890/14-1751.1
- Australian Government Lachlan report: https://www.dcceew.gov.au/sites/default/files/documents/monitoring-native-fish-lachlan-environmental-dna-conventional-methods.pdf
- PubMed/author PDF for Wood 2010: https://pubmed.ncbi.nlm.nih.gov/20703226/
- PMC record for Beaumont et al. 2002: https://pmc.ncbi.nlm.nih.gov/articles/PMC1462356/
- PMC record for Robert et al. 2011: https://pmc.ncbi.nlm.nih.gov/articles/PMC3174657/
- PMC record for Cranmer et al. 2020: https://pmc.ncbi.nlm.nih.gov/articles/PMC7720103/
- Oxford Academic record for Kennedy & O'Hagan 2001: https://academic.oup.com/jrsssb/article-abstract/63/3/425/7083367
- DOI/publisher record for Brynjarsdóttir & O'Hagan 2014: https://doi.org/10.1088/0266-5611/30/11/114007
- Author PDF/metadata for Rykiel 1996: https://www.researchgate.net/publication/222486663_Testing_ecological_models_The_meaning_of_validation
- UFZ author-version metadata for Grimm 2020: https://www.ufz.de/index.php?en=20939&pub_data%5Bdbaf%5D%5Bdbaf_page%5D=view&pub_data%5Bdbaf%5D%5Bpk%5D%5BPUB_ID%5D=23182
- Wiley record for Morris et al. 2019: https://doi.org/10.1002/sim.8086
- Owen's author-hosted book: https://artowen.su.domains/mc/
- JMLR full text for Vehtari et al. 2024: https://jmlr.org/papers/volume25/19-556.html
- arXiv record for Talts et al. 2018: https://arxiv.org/abs/1804.06788
- NOAA repository for Conn et al. 2018: https://repository.library.noaa.gov/view/noaa/52908

The initial Galaxias-specific search found the Lachlan government report and a non-peer-reviewed lead concerning flat-headed galaxias, but no verified recent peer-reviewed Galaxias-specific eDNA detection paper with a DOI at that stage. The report was retained as a clearly limited context lead, not as a validated Pedder assay; the targeted correction/addition pass below subsequently added a peer-reviewed *Galaxiella pusilla* occupancy paper.

## Targeted correction and addition pass

Additional bounded queries run on 2026-10-04:

30. `Brynjarsdottir O'Hagan Learning about physical parameters importance model discrepancy DOI 0266-5611`
31. `The ODD protocol second update 2020 JASSS 10.18564/jasss.4259 primary`
32. `Smart 2016 Environmental DNA sampling cost efficiency traditional survey DOI 10.1111/2041-210X.12598`
33. `Galaxiella pusilla false positive occupancy 2021 10.1002/edn3.124`
34. `"10.1016/j.jenvman.2025.124531" freshwater fish environmental DNA review`
35. `Lachlan "Monitoring native fish" environmental DNA conventional methods PDF authors cover`
36. `DataCite 10.48550/arXiv.1804.06788 Talts`

Primary or authoritative records checked in this pass:

- IOP DOI metadata for Brynjarsdóttir & O'Hagan: https://doi.org/10.1088/0266-5611/30/11/114007. The verified DOI uses ISSN stem `0266-5611`; the earlier `0265-5611` string was corrected.
- JASSS full article for the multi-author ODD second update: https://jasss.soc.surrey.ac.uk/23/2/7.html. The page gives the full author list, 2020 publication date and DOI `10.18564/jasss.4259`.
- Monash author record for Smart et al. (2016): https://research.monash.edu/en/publications/assessing-the-cost-efficiency-of-environmental-dna-sampling/. The abstract identifies budget and assay-cost drivers of eDNA cost-efficiency.
- Monash publisher/author record and open author PDF for Tingley et al. (2021): https://research.monash.edu/en/publications/accounting-for-false-positive-detections-in-occupancy-studies-bas and https://minerva-access.unimelb.edu.au/server/api/core/bitstreams/8dbdcfb2-6798-5f12-ad75-35ec91838d6f/content. The exact title, DOI `10.1002/edn3.124`, year and *Galaxiella pusilla* case study were verified.
- ScienceDirect record for Liu et al. (2025): https://www.sciencedirect.com/science/article/pii/S0301479725005079. The title, six authors, Journal of Environmental Management volume 376, article 124531, DOI `10.1016/j.jenvman.2025.124531` and review abstract were available.
- DCCEEW publication page for the Lachlan report: https://www.dcceew.gov.au/water/cewo/publications/monitoring-native-fish-lachlan-environmental-dna-conventional-methods. The page lists the report as 2019 and gives authors Hinlo, Broadhurst, Bylemans, Allan, Gleeson, Thiem and Dyer; the page was used instead of retaining the prior guessed year/organizational author.
- arXiv record for Talts et al. (2018): https://arxiv.org/abs/1804.06788. The arXiv title, authors and date were verified; `10.48550/arXiv.1804.06788` is retained as the canonical arXiv/DataCite DOI and is not treated as a Crossref failure. Direct DataCite API metadata also returned this DOI, publisher `arXiv`, publication year 2018, the same title/authors, and the arXiv URL: https://api.datacite.org/dois/10.48550%2FarXiv.1804.06788

The targeted Galaxias result is now a peer-reviewed *Galaxiella pusilla* false-positive occupancy paper, while the Lachlan item remains a government-report context source. Neither is treated as a species-specific *Galaxias pedderensis* assay or as evidence that the current analysis is calibrated.
