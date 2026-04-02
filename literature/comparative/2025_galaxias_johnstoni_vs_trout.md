# Historical Impacts of Invasive Species May Not Always Be What They Seem: A Genetic Perspective From an Endangered Native Species

Charlotte Jense1 | Bruce E. Deagle2 | Rob Freeman3 | Christopher P. Burridge1

1Discipline of Biological Sciences, School of Natural Sciences, University of Tasmania, Hobart, Tasmania, Australia | 2Australian National Fish Collection, CSIRO National Research Collections Australia, Hobart, Tasmania, Australia | 3Inland Fisheries Service, New Norfolk, Tasmania, Australia

Correspondence: Charlotte Jense (charlotte.jense@utas.edu.au) Received: 6 March 2025 | Revised: 9 July 2025 | Accepted: 10 August 2025 Editor: Laura D. Bertola Funding: This work was supported by Holsworth Wildlife Research Endowment. Bioplatforms Australia. Keywords: approximate Bayesian computation (ABC) | historical demography | invasive species | population fragmentation

## Abstract

Aim: Invasive species can affect native species detrimentally, causing localised population declines, range contractions and extinctions. Given the costs and difficulties of controlling invasive species, sound knowledge of the potential benefits to native species is essential. However, sometimes the impacts of invasive species have been inferred by proxy, based on allopatric distribution with native species. Galaxias johnstoni, an endemic freshwater fish in Tasmania, is one such species. It has a restricted range and is believed to have experienced fragmentation and decline due to the introduction of brown trout, Salmo trutta, in 1864. This study examines patterns of genetic diversity in contemporary G. johnstoni populations and tests for genetic signatures of impact by introduced brown trout.

Location: Central highlands Tasmania. Methods: Nuclear Single Nucleotide Polymorphisms and mitochondrial DNA sequences were used to assess genetic isolation of populations. Approximate Bayesian Computation was employed to test alternative historical demographic scenarios for the observed patterns of genetic variation.

Results: Genetic isolation of the sampled populations was confirmed. However, brown trout do not appear to have caused genetic isolation of contemporary G. johnstoni populations and received equivocal support for reductions in population size. Instead, habitat preferences and post-glacial recolonisation from local refugia appear more likely to explain the contemporary patterns of G. johnstoni genetic variation.

Main Conclusions: Our study highlights how genetic approaches can evaluate historical impacts of invasive species, especially where native and invasive species are presently allopatric. We also illustrate potential limitations of this approach: (1) the possibility that other processes have influenced native species coincident with the arrival of invasive pests, (2) the overshadowing of invasive species impacts by signatures from earlier demographic events and (3) the inability to recover signatures from genetically isolated populations that do not survive to the present. Multiple lines of evidence are critical to inform appropriate conservation actions.

## 1 | Introduction

The current global decline in biodiversity is largely driven by anthropogenic threats such as habitat loss and degradation, overexploitation, climate change and the introduction of invasive species (Halpern et al. 2008; Geldmann et al. 2014; Boonman et al. 2024; Lewin et al. 2024; Sayer et al. 2025). Although these factors often impact species concurrently, invasive species have been a major instigator for extinctions through competition, predation and disease transmission (Doherty et al. 2016). One of the biggest threats elevating extinction risk associated with invasive species is the contraction and fragmentation of native species' range (Atkinson 1996; Dudgeon et al. 2006; Blackburn et al. 2014; Havel et al. 2015; Lintermans et al. 2020; Duenas et al. 2021). Range fragmentation reduces (i) abundance, (ii) genetic diversity and (iii) gene flow, which can lead to inbreeding depression and reduced adaptive potential (Bessert and Ortí 2008; Pavlova et al. 2017). Therefore, it is important to identify instances where invasive species have impacted native species through range fragmentation such that they can be managed appropriately.

Detriments of invasive species on native species can be most readily confirmed by direct observations of predation and competition, or studies contrasting native populations in sympatry and allopatry with invasive species, including experimental manipulations such as invasive species removals (Busst and Britton 2017; Dominguez Almela et al. 2021). The presence of contemporary fragmented native species distributions that are allopatric or parapatric with invasive species can also suggest impact. However, a limitation exists with this approach for native species lacking detailed distribution information prior to the arrival of invasive species (i.e., before-after-control-impact; Richardson and Rejmanek 2011). Hence, some inferences of invasive species causing impacts such as range fragmentation in native taxa remain entirely correlative and based solely on contemporary distributions (Mooney and Cleland 2001; O'Loughlin et al. 2019). Definitive knowledge of invasive species' contribution to current range fragmentation of threatened species is important since control of invasive species is often prioritised during threatened species and biodiversity management (Commonwealth of Australia 2024; Department of Conservation (NZ) 2024), yet it may not necessarily result in range expansions, increased population connectivity, or increased abundance in native species if fragmentation is unrelated to invasive species (Erskine Ogden and Rejmánek 2005; Velez-Espino et al. 2011; Prior et al. 2018; Bradshaw et al. 2021). This is particularly significant given invasive species control is typically challenging and expensive (Linklater and Steer 2018).

When distributions of native species prior to the arrival of invasive species are largely unknown, Species Distribution Models (SDMs) could be used to test the possibility of fragmentation owing to invasive species. Although SDMs are more commonly employed to estimate the potential range of invasive species (e.g., Bradley 2013; de la Vega and Corley 2019; Rodríguez-Rey et al. 2019), they have also provided insights into contemporary population fragmentation by determining potential historical distributions (e.g., Pease et al. 2009). Nonetheless, correlative SDMs rely on distribution data, which for many threatened species may be depauperate or provide an inaccurate representation

of their potential environmental envelope (i.e., fails to identify broader historical range; Araújo and Guisan 2006; Radomski et al. 2022). For example, the restriction of native freshwater fishes to headwater streams above waterfalls, or other barriers to invasive species incursion, may give a false signal that the native species can only occupy headwaters (O'Malley et al. 2013). Mechanistic SDMs offer benefits through consideration of species physiology, but assume such knowledge is available, including any differences among populations and changes through time (Kearney et al. 2008; Briscoe et al. 2019; Strubbe et al. 2023).

Genetic approaches offer an appealing assessment of whether a fragmented native species' range reflects the action of an invasive species or otherwise preceded their arrival (Darling and Blum 2007; O'Malley et al. 2013; Dussex et al. 2015). This can be achieved using approaches such as Approximate Bayesian Computation (ABC; Dussex et al. 2014; Dussex et al. 2015), which compare alternative past demographic scenarios for current patterns of genetic variation. These genetic approaches may support or refute invasive species impacts by testing for contemporaneous fragmentation or declines in native species' effective population size (Jackson et al. 2016). Contrasting current population connectivity in native species against genetic inferences of historical connectivity can also be informative in this regard (Epps and Keyghobadi 2015). For instance, inference of genetic homogeneity and gene flow among populations known to be presently isolated suggests recent range fragmentation, possibly coinciding with the introduction of invasive species in the area, or involving habitat fragmentation (Anderson et al. 2010; Schlaepfer et al. 2018).

Galaxias johnstoni (Family Galaxiidae) is a non-diadromous freshwater fish endemic to Tasmania and is listed as Critically Endangered (Environment Protection and Biodiversity Conservation Act (EPBC); Department of the Environment 2021). It is presently represented by seven geographically isolated populations restricted to three upper catchments of the Derwent River in Central Tasmania (i.e., Clarence, Nive and Travellers Rest catchments; Crook and David 1998a) but is generally abundant at these sites (Figure 1). Geographic isolation of G. johnstoni populations may be related to the introduction of brown trout (Salmo trutta) for sport fishing, which are allopatrically distributed with G. johnstoni except for occasional records of G. johnstoni downstream of their main populations; in essence, brown trout are continuous in distribution downstream of G. johnstoni populations (Figure 1). Brown trout were introduced to Tasmania in 1864 and were considered to occupy all principal rivers by 1882 (Johnston 1882). Brown trout introductions are also implicated for declines in many native species (Závorka et al. 2018), including other galaxiids (Townsend 1996; McDowall 2003; Hardie et al. 2006; McDowall 2006; De Leaniz et al. 2010; Vera-Escalona et al. 2019; Lintermans et al., 2020; Minett et al. 2021) and putative barriers to trout movement, such as waterfalls, presently isolate them from G. johnstoni. However, G. johnstoni range data before 1970 are limited to the narrow distribution of type material collected in 1934 (Figure 1; Scott 1935). In Clarence Lagoon, G. johnstoni also co-exist with—despite being preyed on by—brook trout (Salvelinus fontinalis). Although brook trout is generally considered less threatening to galaxiids than brown trout, other galaxiids have been unable to co-exist with it (Allibone 1999). Conversely, some

- FIGURE 1 | Locality records and sample locations of Galaxias johnstoni. Historical records are from the Natural Values Atlas Version 3.12.7 (Department of Natural Resources and Environment Tasmania 2024). To enable clarity, brown trout distributions are not shown but are essentially continuous in distribution downstream of the sampled G. johnstoni populations. Ice limits—generally advancing from the northwest—during the Pleistocene and Last Glacial Maximum (LGM) as seen in Colhoun (2004) are superimposed.

galaxiid species have co-existed with brown trout for > 100 years (Fulton and Kroger 1990; Sanger and Fulton 1991), and life history differences among galaxiids may have bearing on this (Jones and Closs 2015).

The current geographic isolation among G. johnstoni populations could have been driven by factors other than brown trout introduction. Competition with the native G. brevipinnis, which has a similar distribution to brown trout and appears to displace other galaxiids (Allibone 1999), may have fragmented the G. johnstoni range. Alternatively, habitat preferences may underlie the fragmented distribution of G. johnstoni, which appears mostly in lakes and slow-flowing waters through buttongrass (Gymnoschoenus sphaerocephalus) moorlands at elevations 800–1140 m (Crook and David 1998a). These areas were also either glaciated or proximate to glaciers during the Pleistocene (Figure 1; Kiernan 1990; Colhoun et al. 1996), with local summer temperatures estimated to have been 6°–8°C cooler than present averages (Colhoun et al. 1996; Barrows et al. 2002; Mackintosh et al. 2006), such that contemporary population isolation could reflect independent colonisation of these areas from lower elevation refugia following a glacial period. Glaciations dramatically displaced Central Tasmanian biological communities presently occupying similar elevations to G. johnstoni. For

example, pollen records indicate flora at these elevations and higher were displaced to areas that are presently 500–600 m elevation (Henríquez et al. 2023). It is also important to note that while contemporary movement between some G. johnstoni populations would be prevented by hydroelectric developments that started in 1934, none of the populations' ranges are presently defined by these structures and hence they are unlikely to be responsible for any genetic separation.

In this study we provide the first population genetic assessment of G. johnstoni. We use nuclear genetic data from tens of thousands of loci obtained through Genotyping-by-Sequencing, which allows reliable population genetic inferences and tests of demographic history (Narum et al. 2013). We use Approximate Bayesian Computation to evaluate whether introduced brown trout are primarily responsible for the present geographic isolation of G. johnstoni populations. Conceptually, this involves contrasting metrics of genetic diversity and connectivity against expectations under alternative demographic scenarios. We also survey mitochondrial DNA genetic variation to enable comparison against other studies investigating population isolation in related species over known timescales (Burridge et al. 2006; Burridge, Craw, Fletcher, and Waters 2008; Burridge, Craw, Jack, et al. 2008).

- 2 | Materials and Methods

- 2.1 | Sampling, DNA Extraction and Data Collection

Tissue samples from 166 G. johnstoni individuals were collected in 2021 using electrofishing and fyke nets at six sites (Figure 1): Lake Knight (n = 38), Tibbs Plain (n = 3), Clarence Lagoon (n = 25), Upper Clarence (n = 25), Upper Dyes Marsh (n = 25) and Johnsons Lagoon (n = 50). Tibbs Plain is not considered a stronghold population. The two Clarence sites are proximate within the same catchment and are considered a single population for management purposes; hence, five of the seven known populations are represented (Skullbone Plains and Olive Lagoon unsampled). DNA was extracted from entire pelvic fins using the Qiagen DNeasy tissue kit, according to the manufacturer's spin-column protocol for animal tissue.

The Australian Genome Research Facility (AGRF) generated Single Nucleotide Polymorphism (SNP) data using a double digest restriction-site associated DNA sequencing (dd-RAD-seq) protocol (Peterson et al. 2012). PstI and MseI were employed to generate 280–342 bp fragments prior to single-end sequencing on an Illumina NovaSeq 6000 Sequencing System using 150 cycles. Technical replicates for the three individuals from Tibbs Plain were included to confirm sequencing reliability.

The mitochondrial cytochrome b gene was amplified using primers Cytb-Glu and Cytb-Thr (Waters and Wallis 2001). PCRs were set up in 25 μL containing 1× Immomix reaction buffer, 0.5 μM of each primer and 2 μL of DNA template. Thermocycling comprised 95°C for 10 min followed by 34 cycles of 95°C for 30 s, 52°C for 30 s and 72°C for 1 min, with a final extension of 72°C for 5 min. PCR products were purified according to the Qiaquick PCR purification protocol and then sequenced from the CytbGlu primer using the Big Dye sequencing kit. mtDNA sequences were edited and aligned to a reference sequence with Geneious Prime version 2021.2 (https://www.geneious.com) and checked manually.

- 2.2 | SNP Data Preparation

SNPs were scored using an AGRF pipeline that incorporates STACKS software version 2.3d (Catchen et al. 2011). This pipeline checks read quality and restriction site presence and trims the FASTQ files to the same lengths, which is important for running STACKS. Demultiplexing and de novo assembly with STACKS used the following parameters: a minimum depth coverage of two stacks was required (-m); two nucleotide differences were allowed between stacks merged into a single locus (-M); calling of haplotypes for secondary reads (i.e., those that were not placed in a stack) was disabled (-H); and one mismatch was allowed between sample loci when building the catalogue (-n). The interactive pipeline integrated in the Radiator version 1.2.5 R package (Gosselin et al. 2020) was used to filter SNPs based on monomorphism, common markers (i.e., retaining those that are common across populations), global low minor allele count (≤ 7), low and high coverage per locus (retaining those that are between 5 and 80), maximum missing proportion per SNP (0.2), the SNP's position on the read (retaining those are between 2

and 135 bp), short linkage disequilibrium to keep one SNP per locus based on the minimum allele count (MAC) and SNPs out of Hardy Weinberg equilibrium with a p value threshold of 0.05 (excluding individuals from Tibbs Plain due to sample size < 10). Only loci out of Hardy Weinberg equilibrium in all populations were removed (Pearman et al. 2022). The same pipeline was also used to filter individuals based on missingness and coverage, removing outliers based on total (463,150–555,883.5), median (4–16) and Interquartile Range coverage (5–21.5), high and low heterozygosity based on the helper plots and to filter out technical replicates from Tibbs Plain. Radiator was also used to identify and remove sex-linked markers, and to convert the final filtered dataset to the formats needed for further analyses.

## 2.3 | Phylogeography

The filtered SNP dataset was used for multilocus coalescent phylogenetic inference with SNAPP version 1.6.1 (Bryant et al. 2012), implemented in the Bayesian software BEAST version 2.7.4 (Bouckaert et al. 2019). The input file was created in BEAUti using a subset of 10 individuals per population (except for Tibbs Plain which had n = 3) and a random subset of 1000 SNPs. Default parameters were used, except we excluded nonpolymorphic sites and used a MCMC chain length of 5,000,000. Analyses were checked for convergence, adequacy of burn-in and a sufficient effective sample size (> 200) using Tracer version 1.7 (Rambaut et al. 2018). TreeAnnotator was used to process the trees using a burn-in of 10%, and trees were visualised using Densitree (Bouckaert and Heled 2014). A minimum spanning haplotype network was created for the mtDNA sequences using PopART (Bandelt et al. 1999).

## 2.4 | Population Genetic Structuring

The filtered nuclear SNP dataset was used to calculate expected and observed heterozygosity for each population with Hierfstat version 0.5-11 (Goudet 2005). An Analysis of Variance (ANOVA) was used to assess significant differences in average heterozygosity among populations using the R stats package version 4.2.1. StrataG version 2.0.2 (Archer et al. 2017) was employed to quantify the divergence among populations for the nuclear SNPs based on pairwise FST using 1000 permutations to test for significance. To account for multiple comparisons, a false discovery rate (FDR) correction was applied to the p values (also referred to as q-values) using the R stats package version 4.4.1 (Benjamini and Hochberg 1995). Haplotype and allele frequency homogeneity were tested using the G-statistic implemented in Hierfstat with 99 permutations. Furthermore, Bayesian clustering of nuclear SNPs was performed using fastSTRUCTURE (Raj et al. 2014) to quantitatively assess the number of genetically distinct populations within the dataset. Clustering of individuals was assessed for K = 1–10 populations, with each K run for five iterations.

## 2.5 | Historical Demography

The Approximate Bayesian Computation random forest method in DIYABC-RF v1.0 (Collin et al. 2021) was used to

| | |
|---|---|
| | |

| | |
|---|---|
| | |

| | |
|---|---|
| | |

- FIGURE 2 | DIYABC-RF scenarios. The colours represent the four populations included in the analysis and the grey line signifies trout introduction. Different branch widths indicate that different population sizes were allowed.

test alternative historical scenarios for the observed patterns of genetic variation. DIYABC-RF utilised the filtered nuclear SNP dataset. Tibbs Plain was excluded due to small sample size (n = 3). Additionally, Upper Clarence was excluded to expedite simulated scenarios, as its geographic location relative to both Clarence Lagoon and brown trout rendered it unnecessary for inferring brown trout impact. DIYABC-RF was performed by simulating training sets under six scenarios (Figure 2). Historical demographic parameters included in all scenarios were four population sizes (N1—N4), and one sampling event (i.e., all samples were collected within the same generation).

- Scenario 1 assumes population divergence in a manner consistent with the SNAPP topology, enforced with conditions on the order of divergence times (t3 > t2 > t1). Scenario 2 represents the same topology but with population divergences occurring before—and population size changes after—trout arrival. Scenario

3 matches Scenario 2 but allows population size change to precede trout arrival and hence has the same level of complexity as

- Scenario 2. Scenarios 4–6 included an ancestral population size and a single divergence event. Scenario 4 represents population divergence from a single panmictic ancestor owing to fragmentation following the introduction of trout. Scenario 5 matches Scenario 4 but allows the population divergence to precede trout arrival. Scenario 6 represents the same topology as Scenario 4 and 5 but allows the population divergence to occur before—and population size changes after—trout arrival. The time of population size change tb1 (Scenario 2 and 6) and tb2 (Scenario 3) was constrained to be more recent than the divergence times t1 and

t5 (t1 > tb1/tb2 and t5 > tb1), such that population size changes always post-dated population divergences.

Log-uniform prior distributions were employed, keeping the lower bound as default (10) and setting the upper bound to 10,000,000 individuals for each of the contemporary and historical population sizes and 500,000 generations for divergence times (t1—t3, t5). Events corresponding to possible brown trout impact (t4 and tb1) were set to 157 generations ago. This reflects the introduction of trout in 1864, conservatively allowing for the possibility of a 1-year generation time in G. johnstoni, whereas also encompassing the 63 generations under a 2.5-year generation time, which seems more likely based on observations of four-year classes in populations of G. johnstoni (Sanger and Fulton 1991; Threatened Species Section 2006) and inferences for close relatives (Crook and David 1998b; Crook and Sanger 1998; Threatened Species Section 2006). Hence, our analysis is structured to maximise the potential for detecting any impact of trout on population divergences and size changes. The timeframe for size changes preceding trout impact (tb2) was set to an upper limit of 250,000 generations to encompass recent glacial and interglacial periods.

Scenarios and parameter priors were pre-evaluated using Principal Component Analysis (PCA) and all available summary statistics to assess if observed genetic variation was encapsulated by the simulations. Although a proportion of the summary statistics may not be informative for the given data, the inclusion of these summary statistics should not alter

- FIGURE 3 | Phylogeography of Galaxias johnstoni represented by (A) SNAPP phylogeny based on nuclear SNPs, and (B) haplotype network for mitochondrial cytochrome b sequences, where each circle represents one haplotype and the size is proportional to the number of samples with that haplotype.

inferences (Collin et al. 2021). Six independent DIYABC-RF runs were then performed for scenario selection and parameter estimation. Training sets for scenario selection comprised

- 20,000 simulations per scenario (120,000 total). The best-suited scenario for all simulated data sets in the training set was selected based on estimated posterior probabilities and classification votes with forests comprising 1000 trees. Demographic parameter estimation for the selected scenario was performed using a second training set with 50,000 simulations, reporting median values (Collin et al. 2021).

- 3 | Results

- 3.1 | Nuclear DNA Sequence Variation

Genotyping by sequencing resulted in a dataset containing 405,328 SNPs across 270,608 loci and 166 individuals. After filtering, 21,299 SNPs and 155 individuals remained; 384,029 SNPs and eight individuals from Johnson's Lagoon and three from Lake Knight were removed. Loci were filtered out mostly based on common markers and minimum allele count, and no loci were removed based on Hardy–Weinberg equilibrium because none were discordant in all populations (excluding Tibbs Plain). Observed and expected heterozygosity ranged from 0.05 in Tibbs Plain to 0.15 in Clarence Lagoon and Upper Dyes Marsh (Figure S1). ANOVA revealed a significant effect of population on average expected heterozygosity (F5,127279 = 1091, p < 2e-16) and observed heterozygosity (F5,127788 = 830.1, p < 2e-16). The percentage of variance in expected and observed heterozygosity explained by populations was 4.11% and 3.15%, respectively. Post hoc comparisons using Tukey's HSD indicated significant differences between all population pairs except for Clarence

Lagoon and Upper Dyes Marsh, which were significantly higher than all other populations (Figure S1). Tibbs Plain had significantly lower expected and observed heterozygosity than all other populations.

## 3.2 | Phylogeography

The SNAPP consensus tree clustered Clarence Lagoon with Upper Clarence, Upper Dyes Marsh with Lake Knight and Johnsons Lagoon with Tibbs Plain (Figure 3a). It showed some uncertainty in the relationships among these pairs, the consensus being that Johnsons Lagoon and Tibbs Plain are most distant from the other populations (Figure 3a). Six haplotypes were identified from 800 bp of mtDNA cytochrome b, defined by 11 parsimony informative sites (Figure 3b). All populations were identifiable by unique mitochondrial haplotypes, except for Lake Knight and Upper Dyes Marsh, which share a haplotype. Clarence Lagoon was the only population with more than one haplotype (two).

## 3.3 | Population Genetic Structuring

fastSTRUCTURE using the same number of groups as sample sites (K = 6) indicated that each population appeared almost entirely represented by a single unique coancestry group (Figure 4). For K = 7–10, each population remained dominated by a single group but with small proportions (e.g., < 0.05 of each individual) assigned to additional groups (Figure S2). Admixed individuals were not observed until the number of groups was less than the number of sample sites (K = 2–5; Figure S2). Hence, K = 6 was selected as the best fit for the data, also supported by the model complexity

analysis included in fastSTRUCTURE. Pairwise FST values for nuclear SNPs ranged from 0.19 between Upper Dyes Marsh and Lake

Knight to 0.60 between Upper Clarence and Tibbs Plain (Table 1). All pairwise FST values were statistically significant after FDR correction except for comparisons with Tibbs Plain, likely reflecting low sample size (Table 1). Homogeneity of mtDNA haplotype and nuclear allele frequencies among populations were rejected (G statistic = 533.96 and 1,217,668, respectively; p < 0.01).

## 3.4 | Historical Demography

All six independent runs selected scenarios with the SNAPP topology and either population size changes before or after trout (Scenario 2 or 3), with average proportions of 0.332 and 0.304 trees, respectively, and posterior probabilities > 0.48 (Table S1). However, the mean misclassification error rate (‘prior error’; Table S1) was relatively high. This likely reflects the difficulty to differentiate the scenarios, indicated by their overlap in the LDA plot (Figure S3) and the high levels of error observed when classifying simulated data back to the potential scenarios under which they were derived (i.e., class error in Table S2). Model and prior misspecification appears less likely to be a contributor to the difficulty in differentiating scenarios as the observed data appear firmly within the cloud of simulated data in the LDA

plot (Figure S3), and summary statistics with high importance showed concordance with the observed data under the favoured scenarios (Table S3; Figure S4). Furthermore, reducing the potential difficulty of differentiating scenarios by grouping them as 1,2,3 and 4,5,6 provided much higher classification votes (> 0.69) and posterior probabilities (> 0.92), specifically for Scenarios 1,2,3 and very small (0.01) prior error rates (Table S4).

Because Scenario 1 received low classification votes (< 0.015) when scenarios were ungrouped (Table S1), we estimated demographic parameters with six independent runs for Scenarios

- 2 and 3. Times are reported in generations (=years under a 1year generation time). The most recent divergence time (t1) was estimated to range from 581 to 3830 generations ago under Scenario 2, and from 4017 to 14,639 generations ago for Scenario
- 3 (Figure S5). Size change enforced after trout introduction (tb1, Scenario 2) ranged between 59 and 74 generations ago, whereas size change before trout introduction (tb2, Scenario

3) ranged between 156 and 1089 generations ago (Figure S6). Although Scenario 2 considered size changes to be potentially resulting from trout invasion, changes were inconsistent in direction across populations and runs, ranging from −1,487,727 to +2,519,609 individuals (Figure S7). A similar pattern was observed for size changes inferred before trout invasion (Scenario 3; −1,667,194 to +1,302,310 individuals; Figure S7).

| | |
|---|---|
| | |
| | |

| | |
|---|---|
| | |

| | |
|---|---|
| | |

- FIGURE 4 | Bayesian clustering analysis of Galaxias johnstoni depicting individual coancestry for K = 6 estimated by fastSTRUCTURE (based on

- 21,299 nuclear SNPs). The colours represent the six sample locations.

TABLE 1 | Pairwise FST estimates for Galaxias johnstoni populations.

Tibbs Plain Lake Knight Clarence Lagoon Upper Clarence Upper Dyes Marsh Lake Knight 0.52 Clarence Lagoon 0.49 0.28a Upper Clarence 0.60 0.34a 0.27a Upper Dyes Marsh 0.47 0.19a 0.22a 0.26a Johnsons Lagoon 0.55 0.32a 0.33a 0.42a 0.28a

Note: Tibbs Plain was represented by only three individuals. aq≤ 0.01 indicates statistical significance after FDR correction.

## 4 | Discussion

To better manage invasive pest species, it is desirable to quantify their impacts on native species (Prior et al. 2018; CrystalOrnelas and Lockwood 2020; Robertson et al. 2020), but in some situations this is complicated by pest and native species exhibiting allopatric distributions, with the former assumed to have fragmented the latter. Here we applied a genetic approach to formally test for invasive species' impact in such a situation. The introduction of brown trout can be rejected for the present genetic isolation of G. johnstoni populations, given that scenarios favoured by ABC involved population divergences that minimally pre-date trout introduction by ~518 years, assuming a single year generation time, but are more likely to be ~1300 years (2.5-year generation time). Furthermore, the strong spatial genetic structuring we observed is unlikely to reflect the short duration of potential brown trout impact on G. johnstoni (157 generations maximum, or 65 generations with a 2.5-year generation time) given time lags for the development of genetic divergence in populations with moderate to large effective population sizes (Epps and Keyghobadi 2015). Inferred G. johnstoni population size changes during brown trout invasion were also both positive and negative and varied in direction across ABC runs, further refuting an impact of trout on the sampled populations.

Our study provides an illustration of how genetic analyses can provide an alternative perspective on invasive species impacts that can inform management actions. Other studies have demonstrated the failure of management interventions due to false inference of invasive species impacts. For example, no improvement of bird-plant networks was observed after removal of invasive honeysuckle from urban forests, and the invasive species was not deemed the primary driver of modifications to the ecological network (Rodewald et al. 2015). Furthermore, regardless of whether invasive species are having detrimental impacts on a native species, management interventions come at the risk of counterproductive outcomes (Prior et al. 2018). For instance, control of invasive flora through herbicides caused more damage to the native species, whereas the invasive species showed a quick recovery (Rinella et al. 2009). In areas that are occupied by multiple invasive species, the control of one such species can also yield proliferation by the others (Prior et al. 2018). For example, the control of invasive top-predators can result in higher densities of invasive mesopredators, thereby reducing the abundance of native prey species (Norbury et al. 2013; Rees et al. 2024). Therefore, both ineffective and potentially perverse outcomes of invasive species management interventions can be avoided by more accurate assessment of invasive species impacts.

Understanding invasive species impacts based on limited information can be challenging and should be inferred with caution. Although most studies use observations such as differences in native species abundance and behaviour to assess invasive species impacts, even these approaches are potentially confounded by concurrent influences of multiple stressors (Lawrence et al. 2014; Stricker et al. 2015; Wauters et al. 2023). Furthermore, the presence of invasive species might skew estimates of native species abundance due to lower detection probabilities without necessarily indicating a true decline (Wohner et al. 2023). Therefore, the use of predictive modelling and direct experimentation has

been recommended to test for negative impacts of invasive species (Stricker et al. 2015). For instance, experimental or opportunistic reduction of invasive species can be insightful as they might reveal increases in native species abundance or range. However, results from experiments in controlled environments may not always reflect outcomes in more complex or natural settings (Busst and Britton 2015; Busst and Britton 2017). Hence, our genetic approach employed here may represent a useful addition in such regards.

The genetic structure observed in G. johnstoni, with divergence times up to ~684,000 years ago (assuming a 2.5-year generation time), may reflect independent post-glacial recolonisation from lower elevation refugia. Although most of G. johnstoni's present range remained unglaciated during the Last Glacial Maximum (LGM; approximately 19,000 years ago), all contemporary populations are in regions that were at least proximate to LGM glaciers or were glaciated earlier during the Pleistocene (Figure 1; Colhoun et al. 1996), representing historically unfavourable areas (e.g., Perea and Doadrio 2015). In particular, the confluence of rivers (Clarence and Nive river) connecting the populations analysed by ABC is at an elevation of 540 m (Figure 1), with glaciers descending to within 100 m of this elevation in at least one of the river valleys (Kiernan 1991; Colhoun 2004). Given the contemporary distribution was glaciated during the Pleistocene and there are no glaciers presently within 400 m elevation of G. johnstoni populations, it is highly likely populations were historically pushed downstream to shared habitat. The impact of glaciations on past population connectivity was also suggested based on Upper Dyes Marsh and Lake Knight exhibiting the most recent divergence among populations (between ~1500–36,000 years ago under a 2.5-year generation time), given that Lake Knight is the only presently inhabited region that was covered by a glacier during the LGM (Colhoun et al. 1996).

A role of post-glacial recolonisation for current patterns of G. johnstoni genetic variation is supported by inferences for another non-diadromous galaxiid with similar mtDNA variation. The Waitaki River New Zealand longjaw galaxias G. prognathus has sub-catchments dominated by single but distinct mtDNA haplotypes, with usually one mutation separating them. This stream-dwelling species occupies historically (LGM) glaciated regions separated by presently unsuitable lake habitat (Waters et al. 2007). Likewise, while there are no records of potential ancestral populations from which G. prognathus have recolonised the formerly unsuitable areas, it is possible that such populations have been extirpated (Waters et al. 2007). In contrast, divergences among other New Zealand galaxiid populations associated with LGM and earlier catchment isolation events typically exhibit greater within-population mtDNA haplotype diversity and divergences (Burridge et al. 2006; Waters et al. 2007; Burridge, Craw, Fletcher, and Waters 2008; Burridge, Craw, Jack, et al. 2008). However, these mtDNA comparisons suggesting post-LGM isolation among G. johnstoni populations need to be reconciled with the older divergences inferred from ABC based on nuclear SNPs, perhaps by means of subsequent population bottlenecks reducing mtDNA diversity, consistent with ABC Scenario 3.

Habitat preferences and competition with other species may also explain the current population genetic divergence among

G. johnstoni populations. Both limited dispersal ability and specific habitat requirements are often implicated for species with restricted distributions. Galaxias johnstoni appears presently restricted to lakes and other low flow freshwater habitats, which may have inhibited gene flow through higher-order streams if it reflects a habitat preference. Likewise, competition with G. brevipinnis may also have restricted gene flow. For example, G. johnstoni does not presently occupy several lakes in the upper Nive catchment (e.g., Lake Norman area; Figure 1) which are trout free and were glaciated during the LGM but are inhabited by G. brevipinnis. Galaxias brevipinnis is considered a threat to other non-diadromous Tasmanian galaxiids as well as those in New Zealand (Allibone 1999; Hardie et al. 2006), and may have contributed to the demise of G. pedderensis in Lake Pedder (Hamr 1995; Chilcott et al. 2013).

Although our study refutes a role of brown trout for geographic isolation or decline of extant G. johnstoni populations, this does not preclude impacts on populations that no longer exist, or future impacts since invasive species impacts and ranges are unlikely to be static over space and time (Britton 2023). Both

- G. platei and G. pedderensis suffered declines and extirpations following salmonid invasion, with direct observations of predation (Threatened Species Section 2006; Chilcott et al. 2013; Vera-Escalona et al. 2019). The present barriers for trout invasion into the range of G. johnstoni are waterfalls and steep gradients (Clarence Lagoon, Lake Knight), small streams anastomosing through buttongrass plains (Upper Dyes Marsh, Tibbs Plain, Johnsons Lagoon) and a road culvert (Tibbs Plain). While these barriers appear currently effective, this can change (Jolly et al. 2024). Human mediated trout translocation remains a threat (Threatened Species Section 2006) and warrants ongoing surveillance; illegally introduced rainbow trout Oncorhynchus mykiss were eradicated from Johnsons Lagoon in 2004 (Jackson et al. 2004). However, many other non-diadromous Tasmanian galaxiids show similarly restricted distributions as G. johnstoni but coexist with brown trout: G. auratus, G. tanycephalus and four species of Paragalaxias (Sanger 2002). Interaction experiments are required to assess the likely consequences of brown trout incursion into stronghold G. johnstoni populations. Although this may seem paradoxical for threatened species, the use of a limited number of G. johnstoni individuals may be justified to achieve a more comprehensive understanding of potential future interactions with trout (Moseby et al. 2019), especially for G. johnstoni which is typically abundant where present. Behavioural studies in Clarence Lagoon where G. johnstoni coexist with brook trout may also be informative in this regard (Jolly et al. 2024). Regardless, whereas continued efforts to avoid trout invasions are advised, the control of brown trout, through exclusion and removal, to enable downstream range expansion of G. johnstoni populations is not supported based on deficient evidence that trout have caused declines in contemporary G. johnstoni populations.

The exchange of individuals among populations that are genetically isolated and have low genetic diversity (‘genetic rescue’) is increasingly advocated for improved conservation outcomes (Tallmon et al. 2004; Whiteley et al. 2015; Weeks et al. 2016). However, while contemporary G. johnstoni populations fit this description genetically, assisted gene flow between populations would need justification based on extirpation risk from low

fitness. Tibbs Plain is perhaps the only candidate for genetic rescue, based on both heterozygosity and abundance evident from this study and previous surveys by Inland Fisheries Tasmania (Threatened Species Section 2006). However, low abundance and genetic diversity are unsurprising given that the main habitat at Tibbs Plain is limited in area and comprises ephemeral pools in a marshy plain.

Although genetic approaches such as the one employed here provide an additional lens for testing the impact of invasive species, they have some limitations. Crucially, they rely on temporal segregation of events potentially responsible for fragmentation of native populations. For example, O'Malley et al. (2013) could not genetically distinguish between the introduction of a non-native predator and another recent environmental disturbance for fragmentation of native Umpqua Chub (Oregonichthys kalawatseti) populations in one instance. However, ABC has been shown to be a powerful approach for the biological inference of complex scenarios, assuming models are well formulated, fitted to the data and improved through model checks (e.g., using summary statistics; Beaumont et al. 2010; Csilléry et al. 2010). For example, DIYABC-RF has been used to establish divergence and admixture times in a migratory bird species (Limosa lapponica) and reliably identified landlocking events in smelt (Retropinna retropinna) populations (Arandjelovic and Vigilant 2018; Conklin et al. 2024).

A second limitation of genetically assessing invasive species impacts on native species is a signature of recent population decline might be overshadowed by a deeper historical population size change. For instance, any decline of G. johnstoni during the rainbow trout invasion in Johnsons Lagoon in 2004 has been insufficient to overshadow a genetic signature of an earlier (on average ~67 generations ago under Scenario 2 and ~615 generations ago under Scenario 3) weak decline. Contrary to the powerful model selection provided by ABC, estimates of population sizes appear less reliable and may require more than 50,000 loci (Shafer et al. 2015). However, this is based on an earlier version of DIYABC, and the more recent version implementing RF is more accurate (Collin et al. 2021). For example, Razgour et al. (2024) estimated historic population declines of 99% in a European bat Barbastella barbastellus, confirming previous suspicions of population declines in the last centuries based on observation of range contractions. In addition, genetic diversity in G. platei was much more influenced by the presence of invasive salmonids than proxies for earlier historical events such as glaciations (Vera-Escalona et al. 2019).

A third limitation of genetically assessing invasive species impacts on native species is the invisibility of demographic histories from which genes did not survive to the present. For example, we cannot preclude extirpation of other G. johnstoni populations by brown trout if they did not exchange genes with populations that survived to the present and were sampled, or did exchange genes but represented a population much smaller in size. In this regard, the type material for G. johnstoni was obtained from a site—Brown Marsh Creek—considered presently inhospitable because of brown trout (Figure 1; Threatened Species Section 2006). This location is 15–22 km downstream from three current populations ofG. johnstoni (Clarence Lagoon, Lake Knight, Upper Dyes Marsh; see Figure 1), and hence it is uncertain whether the type specimens represent an isolated

population that was extirpated by trout, or merely downstream dispersal from populations that have survived to the present. Indeed, the impacts of trout may have now stabilised (Závorka et al. 2018). Sedimentary ancient DNA could be explored to test for G. johnstoni populations extirpated by brown trout, as this approach appears sensitive to past changes in aquatic and proximate systems (Ficetola et al. 2018; Laine et al. 2024).

Author Contributions

C.J. led the sample collection (with invaluable insight from R.F.), analyses of the data, the interpretation of results and the writing of the manuscript. C.P.B., B.D. and C.J. conceptualised the initial study with input from R.F. C.J. carried out laboratory analysis. All authors critically reviewed and edited the manuscript and approved the final version.

## Acknowledgements

The authors would like to acknowledge the use of the high-performance computing facilities provided by Digital Research at the University of Tasmania. The authors would also like to thank the volunteers, Leonard Hambrecht, Bridgette Barnden, Cyril Scomparin and Bridget White for assistance with sample collection, and Floriaan DevlooDelva for guidance with SNP filtering. This project was funded by the Holsworth Wildlife Research Endowment—Equity Trustees Charitable Foundation & the Ecological Society of Australia. ddRAD-seq genotyping costs were covered by Bioplatforms Australia through the Threatened Species Initiative (TSI) (https://bioplatforms.com/projects/ threatened-species/). Open access publishing facilitated by University of Tasmania, as part of the Wiley - University of Tasmania agreement via the Council of Australian University Librarians.

#### Ethics Statement

Research was conducted with the approval of the University of Tasmania Animal Ethics Committee (Project ID: 24238) and in accordance with the Threatened Species Protection Regulations 2016 and the Nature Conservation Act 2002 (Permit No.: TFA 21029) as well as the Inland Fisheries Act 1995 (Permit No.: D21-38374) and Sustainable Timber Tasmania Permit No. 2127. Fieldwork on private land was conducted with the approval of the landowners (Tasmanian Land Conservancy, Tasmanian Aboriginal Centre).

Conflicts of Interest The authors declare no conflicts of interest.

#### Data Availability Statement

The mtDNA sequence data are available on GenBank under accession numbers PX147885 - PX148050. ddRAD-seq raw reads are available through the Bioplatforms Australia data portal under dataset ID 102.100.100/358844 (https://data.bioplatforms.com/tsi-genomicsddrad/bpa-tsi-genomics-ddrad-102_100_100_358756-htvvmdrxy).

Peer Review The peer review history for this article is available at https://www.webof science.com/api/gateway/wos/peer-review/10.1111/ddi.70072.

## References

Allibone, R. 1999. “Impoundment and Introductions: Their Impacts on Native Fish of the Upper Waipori River, New Zealand.” Journal of the Royal Society of New Zealand 29: 291–299. https://doi.org/10.1080/03014 223.1999.9517598.

Anderson, C. D., B. K. Epperson, M.-j. Fortin, et al. 2010. “Considering Spatial and Temporal Scale in Landscape-Genetic Studies of Gene Flow.” Molecular Ecology 19, no. 17: 3565–3575. https://doi.org/10. 1111/j.1365-294X.2010.04757.x.

Arandjelovic, M., and L. Vigilant. 2018. “Non-Invasive Genetic Censusing and Monitoring of Primate Populations.” American Journal of Primatology 80, no. 3: 14. https://doi.org/10.1002/ajp.22743.

Araújo, M. B., and A. Guisan. 2006. “Five (Or So) Challenges for Species Distribution Modelling.” Journal of Biogeography 33, no. 10: 1677–1688. https://doi.org/10.1111/j.1365-2699.2006.01584.x.

Archer, F. I., P. E. Adams, and B. B. Schneiders. 2017. “Stratag: An r Package for Manipulating, Summarizing and Analysing Population Genetic Data.” Molecular Ecology Resources 17, no. 1: 5–11. https://doi. org/10.1111/1755-0998.12559.

Atkinson, I. A. E. 1996. “Introductions of Wildlife as a Cause of Species Extinctions.” Wildlife Biology 2, no. 3: 135–141. https://doi.org/10.2981/ wlb.1996.011.

Bandelt, H.-J., P. Forster, and A. Röhl. 1999. “Median-Joining Networks for Inferring Intraspecific Phylogenies.” Molecular Biology and Evolution 16, no. 1: 37–48.

Barrows, T. T., J. O. Stone, L. K. Fifield, and R. G. Cresswell. 2002. “The Timing of the Last Glacial Maximum in Australia.” Quaternary Science Reviews 21, no. 1: 159–173. https://doi.org/10.1016/S0277-3791(01) 00109-3.

Beaumont, M. A., R. Nielsen, C. Robert, et al. 2010. “In Defence of Model-Based Inference in Phylogeography.” Molecular Ecology 19, no. 3: 436–446. https://doi.org/10.1111/j.1365-294X.2009.04515.x.

Benjamini, Y., and Y. Hochberg. 1995. “Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing.” Journal of the Royal Statistical Society. Series B, Statistical Methodology 57, no. 1: 289–300. https://doi.org/10.1111/j.2517-6161. 1995.tb02031.x.

Bessert, M. L., and G. Ortí. 2008. “Genetic Effects of Habitat Fragmentation on Blue Sucker Populations in the Upper Missouri River (Cycleptus elongatus Lesueur, 1918).” Conservation Genetics 9, no. 4: 821–832. https://doi.org/10.1007/s10592-007-9401-4.

Blackburn, T. M., F. Essl, T. Evans, et al. 2014. “A Unified Classification of Alien Species Based on the Magnitude of Their Environmental Impacts.” PLoS Biology 12, no. 5: e1001850. https://doi.org/10.1371/ journal.pbio.1001850.

Boonman, C. C. F., J. M. Serra-Diaz, S. Hoeks, et al. 2024. “More Than 17,000 Tree Species Are at Risk From Rapid Global Change.” Nature Communications 15, no. 1: 166. https://doi.org/10.1038/s41467-02344321-9.

Bouckaert, R., T. G. Vaughan, J. Barido-Sottani, et al. 2019. “BEAST 2.5: An Advanced Software Platform for Bayesian Evolutionary Analysis.” PLoS Computational Biology 15, no. 4: e1006650. https://doi.org/10. 1371/journal.pcbi.1006650.

Bouckaert, R. R., and J. Heled. 2014. “DensiTree 2: Seeing Trees Through the Forest.” bioRxiv. https://doi.org/10.1101/012401.

Bradley, B. A. 2013. “Distribution Models of Invasive Plants OverEstimate Potential Impact.” Biological Invasions 15, no. 7: 1417–1429. https://doi.org/10.1007/s10530-012-0380-0.

Bradshaw, C. J. A., A. J. Hoskins, P. J. Haubrock, et al. 2021. “Detailed Assessment of the Reported Economic Costs of Invasive Species in Australia.” NeoBiota 67: 511–550. https://doi.org/10.3897/neobiota.67. 58834.

Briscoe, N. J., J. Elith, R. Salguero-Gómez, et al. 2019. “Forecasting Species Range Dynamics With Process-Explicit Models: Matching Methods to Applications.” Ecology Letters 22, no. 11: 1940–1956. https:// doi.org/10.1111/ele.13348.

Britton, J. R. 2023. “Contemporary Perspectives on the Ecological Impacts of Invasive Freshwater Fishes.” Journal of Fish Biology 103, no.

- 4: 752–764. https://doi.org/10.1111/jfb.15240.

Bryant, D., R. Bouckaert, J. Felsenstein, N. A. Rosenberg, and A. RoyChoudhury. 2012. “Inferring Species Trees Directly From Biallelic Genetic Markers: Bypassing Gene Trees in a Full Coalescent Analysis.” Molecular Biology and Evolution 29, no. 8: 1917–1932. https://doi.org/10. 1093/molbev/mss086.

Burridge, C. P., D. Craw, D. Fletcher, and J. M. Waters. 2008. “Geological Dates and Molecular Rates: Fish DNA Sheds Light on Time Dependency.” Molecular Biology and Evolution 25, no. 4: 624–633. https://doi.org/10.1093/molbev/msm271.

Burridge, C. P., D. Craw, D. C. Jack, T. M. King, and J. M. Waters. 2008. “Does Fish Ecology Predict Dispersal Across a River Drainage Divide?” Evolution 62, no. 6: 1484–1499. https://doi.org/10.1111/j.1558-5646. 2008.00377.x.

Burridge, C. P., D. Craw, and J. M. Waters. 2006. “River Capture, Range Expansion, and Cladogenesis: The Genetic Signature of Freshwater Vicariance.” Evolution 60, no. 5: 1038–1049. https://doi.org/10.1111/j. 0014-3820.2006.tb01181.x.

Busst, G. M. A., and J. R. Britton. 2015. “Quantifying the Growth Consequences for Crucian Carp Carassius carassius of Competition from Non-Native Fishes.” Ecology of Freshwater Fish 24, no. 3: 489–492. https://doi.org/10.1111/eff.12155.

Busst, G. M. A., and J. R. Britton. 2017. “Comparative Trophic Impacts of Two Globally Invasive Cyprinid Fishes Reveal Species-Specific Invasion Consequences for a Threatened Native Fish.” Freshwater Biology 62, no. 9: 1587–1595. https://doi.org/10.1111/fwb.12970.

Catchen, J. M., A. Amores, P. Hohenlohe, W. Cresko, and J. H. Postlethwait. 2011. “Stacks: Building and Genotyping Loci De Novo From Short-Read Sequences.” G3: Genes, Genomes, Genetics 1, no. 3: 171–182. https://doi.org/10.1534/g3.111.000240.

Chilcott, S., R. Freeman, P. E. Davies, et al. 2013. “Extinct Habitat, Extant Species: Lessons Learned From Conservation Recovery Actions for the Pedder Galaxias (Galaxias pedderensis) in South-West Tasmania, Australia.” Marine and Freshwater Research 64, no. 9: 864–873. https:// doi.org/10.1071/mf12257.

Colhoun, E., D. Hannan, and K. Kiernan. 1996. “Late Wisconsin Glaciation of Tasmania.” Papers and Proceedings of the Royal Society of Tasmania 130: 35–45. https://doi.org/10.26749/rstpp.130.2.33.

Colhoun, E. A. 2004. “Quaternary Glaciations of Tasmania and Their Ages.” In Developments in Quaternary Sciences, edited by J. Ehlers and P. L. Gibbard, vol. 2, 353–360. Elsevier. https://doi.org/10.1016/S15710866(04)80142-8.

Collin, F.-D., G. Durif, L. Raynal, et al. 2021. “Extending Approximate Bayesian Computation With Supervised Machine Learning to Infer Demographic History From Genetic Polymorphisms Using DIYABC Random Forest.” Molecular Ecology Resources 21, no. 8: 2598–2613. https://doi.org/10.1111/1755-0998.13413.

Commonwealth of Australia. 2024. “Australia's Strategy for Nature 2024–2030.”

Conklin, J. R., Y. I. Verkuil, M. J. M. Lefebvre, et al. 2024. “High Dispersal Ability Versus Migratory Traditions: Fine-Scale Population Structure and Post-Glacial Colonisation in Bar-Tailed Godwits.” Molecular Ecology 33, no. 15: e17452. https://doi.org/10.1111/mec.17452.

- Crook, D. A., and A. David. 1998a. “Threatened Species Unit Listing Statement Clarence Galaxias, Galaxias johnstoni.”
- Crook, D. A., and A. David. 1998b. “Threatened Species Unit Listing Statement Swan Galaxias, Galaxias fontanus.”

Crook, D. A., and A. C. Sanger. 1998. “Threatened Fishes of the World: Galaxias fontanus Fulton, 1978 (Galaxiidae).” Environmental Biology of Fishes 53, no. 1: 32. https://doi.org/10.1023/A:1007413205067.

Crystal-Ornelas, R., and J. L. Lockwood. 2020. “The ‘Known Unknowns’ of Invasive Species Impact Measurement.” Biological Invasions 22, no. 4: 1513–1525. https://doi.org/10.1007/s10530-020-02200-0.

Csilléry, K., M. G. B. Blum, O. E. Gaggiotti, and O. François. 2010. “Approximate Bayesian Computation (ABC) in Practice.” Trends in Ecology & Evolution 25, no. 7: 410–418. https://doi.org/10.1016/j.tree. 2010.04.001.

Darling, J. A., and M. J. Blum. 2007. “DNA-Based Methods for Monitoring Invasive Species: A Review and Prospectus.” Biological Invasions 9, no. 7: 751–765. https://doi.org/10.1007/s10530-006-9079-4.

de la Vega, G. J., and J. C. Corley. 2019. “Drosophila suzukii (Diptera: Drosophilidae) Distribution Modelling Improves Our Understanding of Pest Range Limits.” International Journal of Pest Management 65, no. 3: 217–227. https://doi.org/10.1080/09670874.2018.1547460.

De Leaniz, C. G., G. Gajardo, and S. Consuegra. 2010. “From Best to Pest: Changing Perspectives on the Impact of Exotic Salmonids in the Southern Hemisphere.” Systematics and Biodiversity 8, no. 4: 447–459. https://doi.org/10.1080/14772000.2010.537706.

Department of Conservation (NZ). 2024. “Predator Free 2050.” www. doc.govt.nz.

Department of Natural Resources and Environment Tasmania. 2024. Natural Values Atlas. Tasmanian Government. https://www.naturalval uesatlas.tas.gov.au/.

Department of the Environment. 2021. Environment Protection and Biodiversity Conservation Act 1999. Commonwealth of Australia. www. environment.gov.au/sprat.

Doherty, T. S., A. S. Glen, D. G. Nimmo, E. G. Ritchie, and C. R. Dickman. 2016. “Invasive Predators and Global Biodiversity Loss.” Proceedings of the National Academy of Sciences of the United States of America 113, no. 40: 11261–11265. https://doi.org/10.1073/pnas.1602480113.

Dominguez Almela, V., J. South, and J. R. Britton. 2021. “Predicting the Competitive Interactions and Trophic Niche Consequences of a Globally Invasive Fish With Threatened Native Species.” Journal of Animal Ecology 90, no. 11: 2651–2662. https://doi.org/10.1111/1365-2656.13571.

Dudgeon, D., A. H. Arthington, M. O. Gessner, et al. 2006. “Freshwater Biodiversity: Importance, Threats, Status and Conservation Challenges.” Biological Reviews 81, no. 2: 163–182. https://doi.org/10. 1017/S1464793105006950.

Duenas, M. A., D. J. Hemming, A. Roberts, and H. Diaz-Soltero. 2021. “The Threat of Invasive Species to IUCN-Listed Critically Endangered Species: A Systematic Review.” Global Ecology and Conservation 26: e01476. https://doi.org/10.1016/j.gecco.2021.e01476.

Dussex, N., N. J. Rawlence, and B. C. Robertson. 2015. “Ancient and Contemporary DNA Reveal a Pre-Human Decline but no Population Bottleneck Associated With Recent Human Persecution in the Kea (Nestor notabilis).” PLoS One 10, no. 2: e0118522. https://doi.org/10. 1371/journal.pone.0118522.

Dussex, N., D. Wegmann, and B. C. Robertson. 2014. “Postglacial Expansion and Not Human Influence Best Explains the Population Structure in the Endangered Kea (Nestor notabilis).” Molecular Ecology 23, no. 9: 2193–2209. https://doi.org/10.1111/mec.12729.

Epps, C. W., and N. Keyghobadi. 2015. “Landscape Genetics in a Changing World: Disentangling Historical and Contemporary Influences and Inferring Change.” Molecular Ecology 24, no. 24: 6021– 6040. https://doi.org/10.1111/mec.13454.

Erskine Ogden, J. A., and M. Rejmánek. 2005. “Recovery of Native Plant Communities After the Control of a Dominant Invasive Plant Species, Foeniculum vulgare: Implications for Management.” Biological Conservation 125, no. 4: 427–439. https://doi.org/10.1016/j.biocon.2005. 03.025.

Ficetola, G. F., J. Poulenard, P. Sabatier, et al. 2018. “DNA From Lake Sediments Reveals Long-Term Ecosystem Changes After a Biological

Invasion.” Science Advances 4, no. 5: eaar4292. https://doi.org/10.1126/ sciadv.aar4292.

Fulton, W., and C. Kroger. 1990. Tasmanian Freshwater Fishes Fauna of Tasmania Committee. University of Tasmania. https://books.google. com.au/books?id=H5I_AAAAYAAJ.

Geldmann, J., L. N. Joppa, and N. D. Burgess. 2014. “Mapping Change in Human Pressure Globally on Land and Within Protected Areas.” Conservation Biology 28, no. 6: 1604–1616. https://doi.org/10.1111/cobi. 12332.

Gosselin, T., M. Lamothe, F. Devloo-Delva, and P. Grewe. 2020. “radiator: RADseq Data Exploration, Manipulation and Visualization Using R.”

Goudet, J. 2005. “Hierfstat, a Package for r to Compute and Test Hierarchical F-Statistics.” Molecular Ecology Notes 5, no. 1: 184–186. https://doi.org/10.1111/j.1471-8286.2004.00828.x.

Halpern, B. S., S. Walbridge, K. A. Selkoe, et al. 2008. “A Global Map of Human Impact on Marine Ecosystems.” Science 319, no. 5865: 948–952. https://doi.org/10.1126/science.1149345.

Hamr, P. 1995. “Threatened Fishes of the World: Galaxias pedderensis Frankenberg, 1968 (Galaxiidae).” Environmental Biology of Fishes 43, no. 4: 406. https://doi.org/10.1007/BF00001177.

Hardie, S. A., J. E. Jackson, L. A. Barmuta, and R. W. G. White. 2006. “Status of Galaxiid Fishes in Tasmania, Australia: Conservation Listings, Threats and Management Issues.” Aquatic Conservation: Marine and Freshwater Ecosystems 16, no. 3: 235–250. https://doi.org/ 10.1002/aqc.722.

Havel, J. E., K. E. Kovalenko, S. M. Thomaz, S. Amalfitano, and L. B. Kats. 2015. “Aquatic Invasive Species: Challenges for the Future.” Hydrobiologia 750, no. 1: 147–170. https://doi.org/10.1007/s1075 0-014-2166-0.

Henríquez, W. I., M.-S. Fletcher, and A. Romano. 2023. “Vegetation, Fire and Climate History in Central-Western Tasmania (41°S), Australia, Over the Last ∼21,000 Years.” Quaternary Science Reviews 318: 108315. https://doi.org/10.1016/j.quascirev.2023.108315.

Jackson, J. A., E. L. Carroll, T. D. Smith, A. N. Zerbini, N. J. Patenaude, and C. S. Baker. 2016. “An Integrated Approach to Historical Population Assessment of the Great Whales: Case of the New Zealand Southern Right Whale.” Royal Society Open Science 3, no. 3: 150669. https://doi. org/10.1098/rsos.150669.

Jackson, J. E., T. A. Raadik, M. Lintermans, and M. Hammer. 2004. “Alien Salmonids in Australia: Impediments to Effective Impact Management, and Future Directions.” New Zealand Journal of Marine and Freshwater Research 38, no. 3: 447–455. https://doi.org/10.1080/ 00288330.2004.9517252.

Johnston, R. M. 1882. “General and Critical Observations on the Fishes of Tasmania: With a Classified Catalogue of All Known Species.” Papers and Proceedings of the Royal Society of Tasmania, 51–170.

Jolly, M. E., H. J. Warburton, S. Bowie, E. Challies, P. G. Jellyman, and A. R. McIntosh. 2024. “Isolation Management to Protect Threatened Native Galaxiid Fish Species: Lessons From Aotearoa New Zealand.” Aquatic Conservation: Marine and Freshwater Ecosystems 34, no. 7: e4220. https://doi.org/10.1002/aqc.4220.

Jones, P. E., and G. P. Closs. 2015. “Life History Influences the Vulnerability of New Zealand Galaxiids to Invasive Salmonids.” Freshwater Biology 60, no. 10: 2127–2141. https://doi.org/10.1111/fwb. 12637.

Kearney, M., B. L. Phillips, C. R. Tracy, K. A. Christian, G. Betts, and W. P. Porter. 2008. “Modelling Species Distributions Without Using Species Distributions: The Cane Toad in Australia Under Current and Future Climates.” Ecography 31, no. 4: 423–434. https://doi.org/10.1111/j.09067590.2008.05457.x.

- Kiernan, K. 1990. “The Extent of Late Cenozoic Glaciation in the Central Highlands of Tasmania, Australia.” Arctic and Alpine Research 22: 187–206. https://doi.org/10.2307/1551459.
- Kiernan, K. 1991. “Glacial History of the Upper Derwent Valley, Tasmania.” New Zealand Journal of Geology and Geophysics 34, no. 2: 157–166. https://doi.org/10.1080/00288306.1991.9514453.

Laine, J., S. S. T. Mak, N. F. G. Martins, et al. 2024. “Late Pleistocene Stickleback Environmental Genomes Reveal the Chronology of Freshwater Adaptation.” Current Biology 34, no. 5: 1142–1147. https:// doi.org/10.1016/j.cub.2024.01.056.

Lawrence, D. J., B. Stewart-Koster, J. D. Olden, et al. 2014. “The Interactive Effects of Climate Change, Riparian Management, and a Nonnative Predator on Stream-Rearing Salmon.” Ecological Applications 24, no. 4: 895–912. https://doi.org/10.1890/13-0753.1.

Lewin, A., G. Murali, S. Rachmilevitch, and U. Roll. 2024. “Global Evaluation of Current and Future Threats to Drylands and Their Vertebrate Biodiversity.” Nature Ecology & Evolution 8, no. 8: 1448– 1458. https://doi.org/10.1038/s41559-024-02450-4.

Linklater, W., and J. Steer. 2018. “Predator Free 2050: A Flawed Conservation Policy Displaces Higher Priorities and Better, EvidenceBased Alternatives.” Conservation Letters 11, no. 6: e12593. https://doi. org/10.1111/conl.12593.

Lintermans, M., H. M. Geyle, S. Beatty, et al. 2020. “Big Trouble for Little Fish: Identifying Australian Freshwater Fishes in Imminent Risk of Extinction.” Pacific Conservation Biology 26, no. 4: 365–377. https:// doi.org/10.1071/PC19053.

Mackintosh, A. N., T. T. Barrows, E. A. Colhoun, and L. K. Fifield. 2006. “Exposure Dating and Glacial Reconstruction at Mt. Field, Tasmania, Australia, Identifies MIS 3 and MIS 2 Glacial Advances and Climatic Variability.” Journal of Quaternary Science 21, no. 4: 363–376. https:// doi.org/10.1002/jqs.989.

McDowall, R. M. 2003. “Impacts of Introduced Salmonids on Native Galaxiids in New Zealand Upland Streams: A New Look at an Old Problem.” Transactions of the American Fisheries Society 132, no. 2: 229– 238. https://doi.org/10.1577/1548-8659(2003)132<0229:Ioison>2.0.Co;2.

McDowall, R. M. 2006. “Crying Wolf, Crying Foul, or Crying Shame: Alien Salmonids and a Biodiversity Crisis in the Southern CoolTemperate Galaxioid Fishes?” Reviews in Fish Biology and Fisheries 16, no. 3–4: 233–422. https://doi.org/10.1007/s11160-006-9017-7.

Minett, J. F., C. Garcia de Leaniz, H. Sobolewska, P. Brickle, G. T. Crossin, and S. Consuegra. 2021. “SNP Analyses and Acoustic Tagging Reveal Multiple Origins and Widespread Dispersal of Invasive Brown Trout in The Falkland Islands.” Evolutionary Applications 14, no. 8: 2134–2144. https://doi.org/10.1111/eva.13274.

Mooney, H. A., and E. E. Cleland. 2001. “The Evolutionary Impact of Invasive Species.” Proceedings of the National Academy of Sciences 98, no. 10: 5446–5451. https://doi.org/10.1073/pnas.091093398.

Moseby, K. E., M. Letnic, D. T. Blumstein, and R. West. 2019. “Understanding Predator Densities for Successful Co-Existence of Alien Predators and Threatened Prey.” Austral Ecology 44, no. 3: 409– 419. https://doi.org/10.1111/aec.12697.

Narum, S. R., C. A. Buerkle, J. W. Davey, M. R. Miller, and P. A. Hohenlohe. 2013. “Genotyping-By-Sequencing in Ecological and Conservation Genomics.” Molecular Ecology 22, no. 11: 2841–2847. https://doi.org/10.1111/mec.12350.

Norbury, G., A. Byrom, R. Pech, et al. 2013. “Invasive Mammals and Habitat Modification Interact to Generate Unforeseen Outcomes for Indigenous Fauna.” Ecological Applications 23, no. 7: 1707–1721. https:// doi.org/10.1890/12-1958.1.

O'Loughlin, L. S., B. Gooden, J. N. Barney, and D. B. Lindenmayer. 2019. “Surrogacy in Invasion Research and Management: Inferring “Impact”

From “Invasiveness”.” Frontiers in Ecology and the Environment 17, no. 8: 464–473. https://doi.org/10.1002/fee.2097.

O'Malley, K. G., D. F. Markle, and W. R. Ardren. 2013. “Timing of Population Fragmentation in a Vulnerable Minnow, the Umpqua Chub, and the Role of Nonnative Predators.” Transactions of the American Fisheries Society 142, no. 2: 447–457. https://doi.org/10.1080/00028487. 2012.728166.

Pavlova, A., L. B. Beheregaray, R. Coleman, et al. 2017. “Severe Consequences of Habitat Fragmentation on Genetic Diversity of an Endangered Australian Freshwater Fish: A Call for Assisted Gene Flow.” Evolutionary Applications 10, no. 6: 531–550. https://doi.org/10. 1111/eva.12484.

Pearman, W. S., L. Urban, and A. Alexander. 2022. “Commonly Used Hardy–Weinberg Equilibrium Filtering Schemes Impact Population Structure Inferences Using RADseq Data.” Molecular Ecology Resources

- 22, no. 7: 2599–2613. https://doi.org/10.1111/1755-0998.13646.

Pease, K. M., A. H. Freedman, J. P. Pollinger, et al. 2009. “Landscape Genetics of California Mule Deer (Odocoileus hemionus): The Roles of Ecological and Historical Factors in Generating Differentiation.” Molecular Ecology 18, no. 9: 1848–1862. https://doi.org/10.1111/j.1365294X.2009.04112.x.

Perea, S., and I. Doadrio. 2015. “Phylogeography, Historical Demography and Habitat Suitability Modelling of Freshwater Fishes Inhabiting Seasonally Fluctuating Mediterranean River Systems: A Case Study Using the Iberian Cyprinid Squalius valentinus.” Molecular Ecology 24, no. 14: 3706–3722. https://doi.org/10.1111/mec.13274.

Peterson, B. K., J. N. Weber, E. H. Kay, H. S. Fisher, and H. E. Hoekstra. 2012. “Double Digest RADseq: An Inexpensive Method for De Novo SNP Discovery and Genotyping in Model and Non-Model Species.” PLoS One 7, no. 5: e37135. https://doi.org/10.1371/journal.pone.0037135.

Prior, K. M., D. C. Adams, K. D. Klepzig, and J. Hulcr. 2018. “When Does Invasive Species Removal Lead to Ecological Recovery? Implications for Management Success.” Biological Invasions 20, no. 2: 267–283. https:// doi.org/10.1007/s10530-017-1542-x.

Radomski, T., D. Beamer, A. Babineau, C. Wilson, J. Pechmann, and K.

- H. Kozak. 2022. “Finding What You Don't Know: Testing SDM Methods for Poorly Known Species.” Diversity and Distributions 28, no. 9: 1769–

1780. https://doi.org/10.1111/ddi.13536.

Raj, A., M. Stephens, and J. K. Pritchard. 2014. “fastSTRUCTURE: Variational Inference of Population Structure in Large SNP Data Sets.” Genetics 197, no. 2: 573–589. https://doi.org/10.1534/genetics.114. 164350.

Rambaut, A., A. J. Drummond, D. Xie, G. Baele, and M. A. Suchard. 2018. “Posterior Summarization in Bayesian Phylogenetics Using Tracer 1.7.” Systematic Biology 67, no. 5: 901–904. https://doi.org/10. 1093/sysbio/syy032.

Razgour, O., C. Montauban, F. Festa, et al. 2024. “Applying Genomic Approaches to Identify Historic Population Declines in European Forest Bats.” Journal of Applied Ecology 61, no. 1: 160–172. https://doi. org/10.1111/1365-2664.14540.

Rees, M. W., B. A. Wintle, A. Robley, et al. 2024. “Fox Control and Fire Influence the Occurrence of Invasive Predators and Threatened Native Prey.” Biological Invasions 26, no. 3: 685–703. https://doi.org/10.1007/ s10530-023-03200-6.

Richardson, D. M., and M. Rejmanek. 2011. “Trees and Shrubs as Invasive Alien Species - a Global Review.” Diversity and Distributions 17, no. 5: 788–809. https://doi.org/10.1111/j.1472-4642.2011.00782.x.

Rinella, M. J., B. D. Maxwell, P. K. Fay, T. Weaver, and R. L. Sheley. 2009. “Control Effort Exacerbates Invasive-Species Problem.” Ecological Applications 19, no. 1: 155–162. https://doi.org/10.1890/07-1482.1.

Robertson, P. A., A. Mill, A. Novoa, et al. 2020. “A Proposed Unified Framework to Describe the Management of Biological Invasions.”

Biological Invasions 22, no. 9: 2633–2645. https://doi.org/10.1007/s1053 0-020-02298-2.

Rodewald, A. D., R. P. Rohr, M. A. Fortuna, and J. Bascompte. 2015. “Does Removal of Invasives Restore Ecological Networks? An Experimental Approach.” Biological Invasions 17, no. 7: 2139–2146. https://doi.org/10.1007/s10530-015-0866-7.

Rodríguez-Rey, M., S. Consuegra, L. Börger, and C. Garcia de Leaniz. 2019. “Improving Species Distribution Modelling of Freshwater Invasive Species for Management Applications.” PLoS One 14, no. 6: e0217896. https://doi.org/10.1371/journal.pone.0217896.

Sanger, A. C. 2002. “Prospects and Problems for the Restoration of the Pedder galaxias.” In Lake Pedder: Values and Restoration. Occasional Paper No. 27, edited by C. Sharples, 125–130. Centre for Environmental Studies, University of Tasmania.

Sanger, A. C., and W. Fulton. 1991. “Conservation of Endangered Species of Tasmanian Freshwater Fish: Final Report.”

Sayer, C. A., E. Fernando, R. R. Jimenez, et al. 2025. “One-Quarter of Freshwater Fauna Threatened With Extinction.” Nature 638: 138–145. https://doi.org/10.1038/s41586-024-08375-z.

Schlaepfer, D. R., B. Braschler, H.-P. Rusterholz, and B. Baur. 2018. “Genetic Effects of Anthropogenic Habitat Fragmentation on Remnant Animal and Plant Populations: A Meta-Analysis.” Ecosphere 9, no. 10: e02488. https://doi.org/10.1002/ecs2.2488.

Scott, E. O. G. 1935. “Observations on Fishes of the Family Galaxiidae. Part 1.” Papers and Proceedings of the Royal Society of Tasmania, 85–112.

Shafer, A. B. A., L. M. Gattepaille, R. E. A. Stewart, and J. B. W. Wolf. 2015. “Demographic Inferences Using Short-Read Genomic Data in an Approximate Bayesian Computation Framework: In Silico Evaluation of Power, Biases and Proof of Concept in Atlantic Walrus.” Molecular Ecology 24, no. 2: 328–345. https://doi.org/10.1111/mec.13034.

Stricker, K. B., D. Hagan, and S. L. Flory. 2015. “Improving Methods to Evaluate The Impacts of Plant Invasions: Lessons From 40 Years of Research.” AoB Plants 7: plv028. https://doi.org/10.1093/aobpla/plv028.

Strubbe, D., L. Jiménez, A. M. Barbosa, A. J. S. Davis, L. Lens, and C. Rahbek. 2023. “Mechanistic Models Project Bird Invasions With Accuracy.” Nature Communications 14, no. 1: 15. https://doi.org/10. 1038/s41467-023-38329-4.

Tallmon, D. A., G. Luikart, and R. S. Waples. 2004. “The Alluring Simplicity and Complex Reality of Genetic Rescue.” Trends in Ecology & Evolution 19, no. 9: 489–496. https://doi.org/10.1016/j.tree.2004.07.003.

Threatened Species Section. 2006. “Recovery Plan: Tasmanian Galaxiidae 2006–2010.”

Townsend, C. R. 1996. “Invasion Biology and Ecological Impacts of Brown Trout Salmo trutta in New Zealand.” Biological Conservation 78, no. 1: 13–22. https://doi.org/10.1016/0006-3207(96)00014-6.

Velez-Espino, L. A., R. L. McLaughlin, M. L. Jones, and T. C. Pratt. 2011. “Demographic Analysis of Trade-Offs With Deliberate Fragmentation of Streams: Control of Invasive Species Versus Protection of Native Species.” Biological Conservation 144, no. 3: 1068–1080. https://doi.org/ 10.1016/j.biocon.2010.12.026.

Vera-Escalona, I., E. Habit, and D. E. Ruzzante. 2019. “Invasive Species and Postglacial Colonization: Their Effects on the Genetic Diversity of a Patagonian Fish.” Proceedings of the Royal Society B: Biological Sciences 286, no. 1897: 20182567. https://doi.org/10.1098/rspb.2018.2567.

Waters, J. M., D. L. Rowe, S. Apte, et al. 2007. “Geological Dates and Molecular Rates: Rapid Divergence of Rivers and Their Biotas.” Systematic Biology 56, no. 2: 271–282. https://doi.org/10.1080/10635 150701313855.

Waters, J. M., and G. P. Wallis. 2001. “Cladogenesis and Loss of the Marine Life-History Phase in Freshwater Galaxiid Fishes

(Osmeriformes: Galaxiidae).” Evolution 55, no. 3: 587–597. https://doi. org/10.1554/0014-3820(2001)055[0587:Calotm]2.0.Co;2.

Wauters, L. A., P. W. W. Lurz, F. Santicchia, et al. 2023. “Interactions Between Native and Invasive Species: A Systematic Review of the Red Squirrel-Gray Squirrel Paradigm.” Frontiers in Ecology and Evolution 11, no. 20: Article 1083008. https://doi.org/10.3389/fevo.2023.1083008.

Weeks, A. R., J. Stoklosa, and A. A. Hoffmann. 2016. “Conservation of Genetic Uniqueness of Populations May Increase Extinction Likelihood of Endangered Species: The Case of Australian Mammals.” Frontiers in Zoology 13, no. 1: 31. https://doi.org/10.1186/s12983-016-0163-z.

Whiteley, A. R., S. W. Fitzpatrick, W. C. Funk, and D. A. Tallmon. 2015. “Genetic Rescue to the Rescue.” Trends in Ecology & Evolution 30, no. 1: 42–49. https://doi.org/10.1016/j.tree.2014.10.009.

Wohner, P. J., P. D. Scheerer, M. H. Meeuwig, and J. T. Peterson. 2023. “A Comprehensive Multi-State Conditional Occupancy Model for Evaluating Interactions of Non-Native and Native Species.” Frontiers in Ecology and Evolution 10: 1014707. https://doi.org/10.3389/fevo.2022. 1014707.

Závorka, L., M. Buoro, and J. Cucherousset. 2018. “The Negative Ecological Impacts of a Globally Introduced Species Decrease With Time Since Introduction.” Global Change Biology 24, no. 9: 4428–4437. https://doi.org/10.1111/gcb.14323.

#### Supporting Information

Additional supporting information can be found online in the Supporting Information section. Data S1: ddi70072-sup-0001-Supinfo. docx.
