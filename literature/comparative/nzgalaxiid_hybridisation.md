# Fish biogeography and hybridization: do contemporary distributions predict introgression history?

Jonathan M Waters*, Ciaran SM Campbell, Ludovic Dutoit

Department of Zoology, University of Otago, Dunedin, 9054, New Zealand

*Correspondence: jon.waters@otago.ac.nz

## Abstract

Freshwater ecosystems frequently house diverse assemblages of closely-related fish taxa, which can be particularly prone to hybridization and introgression. While extensive introgression may be expected among biogeographically proximate lineages, recent analyses imply that contemporary distributions do not always accurately predict hybridization history. Here we use the ABBA-BABA approach to test biogeographic hypotheses regarding the extent of hybridization in recent evolution of New Zealand’s species-rich freshwater Galaxias vulgaris fish complex. Genome-wide comparisons reveal significant increases in

introgression associated with increasing geographic overlap of taxa. The estimator DP, which assesses the net proportion of a genome originating from introgression, shows a particularly strong relationship with biogeographic overlap (R2 = 0.43; p = 0.005). Our analyses nevertheless reveal surprisingly substantial signatures of introgression among taxa that currently have disjunct distributions within drainages (e.g. separate subcatchments). These ‘anomalies’ imply that current biogeography is not always an accurate predictor of introgression history. Our study suggests that both modern and ancient biogeographic shifts, including recent anthropogenic range fragmentation and tectonically-driven riven capture events, have influenced introgression histories in this dynamic freshwater fish radiation.

Keywords: admixture, genome, hybrid, introgression, secondary contact, speciation.

## Introduction (Objectives)

Freshwater fish assemblages provide some of the world’s most iconic examples of rapid divergence and speciation (Echelle and Kornfield 1984; Avise 1990; Meyer et al. 1990; Schluter 2000; Feulner and Seehausen 2019). In many such cases, diverse but closely-related freshwater fish lineages have evolved in close geographic proximity to one another (Avise 1990). As a result of their diversity but relatively restricted habitats, freshwater fish taxa are thus expected to have extensive opportunities for hybridization (Joyce et al. 2011; Wallis et al. 2017; Svardal et al. 2020). Although historically overlooked as a source of evolutionary potential (Mallet 2007), the resulting introgression can potentially fuel major adaptive shifts (Seehausen 2004; Meier et al. 2017; Irisarri et al. 2018; Selz and Seehausen, 2019; see also Giska et al. 2019; Waters and McCulloch 2021).

Traditionally, genetic mixing between distinct freshwater lineages has been documented primarily via direct observations of hybrid phenotypes and/or genotypes in regions of species contact (e.g. Seehausen 2004), or via major discordance between cytoplasmic versus nuclear phylogenies (Joyce et al. 2011; Perea et al. 2016; Unmack et al. 2017; Waters et al. 2010; Wallis et al. 2017). More recently, the combination of genome-wide data and new statistical approaches (e.g. ABBA-BABA; Green et al., 2010; Durand et al., 2011; Beckman et al. 2018) has enabled tests for even subtle historic admixture between closely-related freshwater lineages (Meier et al. 2017; Ravinet et al. 2020; Masonick et al. 2022). For example, the ABBA-BABA approach uses a phylogenetic framework to test for asymmetric SNP-sharing between non-sister taxa due to the contribution of introgression rather than incomplete lineage sorting. Specifically, in the absence of introgression, SNPs mapped across a four-taxon phylogeny ([4[3[2,1]]]) are expected to show equal proportions of ‘ABBA’ and ‘BABA’ phylogenetic distribution patterns (where A and B represent alternative alleles at single loci). Conversely, significant excesses of either ABBA or BABA are considered potentially strong signatures of introgression between non-sister taxa 1 and 3, or 2 and 3, respectively (Green et al. 2010; Martin et al. 2015; Table 1). While this relatively simple approach can be sensitive to phylogenetic nonindependence among multiple taxon comparisons, and potential effects of unsampled taxa (Eaton et al. 2015), it nevertheless provides an elegant and popular test for gene flow between related lineages (Zheng and Janke 2018; Martin and Amos 2020; Kong and Kubatko 2021). Additionally, while the phylogenetic frameworks required to inform ABBA-BABA analysis could themselves potentially be compromised by reticulate evolution (Mallet et al 2016), this approach has nevertheless been demonstrated to effectively characterise the histories of relatively lowintrogression systems (e.g. Green et al 2010).

Species complexes exhibiting strong biogeographic structure (e.g. due to dispersal limitation; Waters et al. 2020) present fascinating systems for understanding the impact of species distributions on introgression signatures. While introgression is typically expected to have occurred most extensively among biogeographically proximate lineages (e.g. Harrison and Larson 2014; Hamlin et al. 2020), emerging data from several systems imply that contemporary distributions do not always accurately predict hybridization history. As a case in point, recent analyses have detected apparent mismatches between current biogeography and introgression signatures (Folk et al. 2018; Kang et al. 2017). Such mismatches may potentially shed new light on past range dynamics.

New Zealand’s Galaxias vulgaris complex represents a species-rich radiation of freshwater-limited fishes derived from a diadromous (migratory) ancestor (McDowall 1970; Waters and Wallis 2001a, b). While once thought to comprise a single common species (‘vulgaris’; McDowall 1970), subsequent molecular (e.g. Allibone et al. 1996; Waters and Wallis 2001a, b; Waters et al. 2010; Campbell et al. 2022) and morphological (McDowall and Wallis 1996, McDowall 1997) analyses of this complex have resolved 12 distinct taxa, all endemic to southern New Zealand (Campbell et al. 2022). Much of the group’s diversity is centred on the southern South Island (Fig. 1), with eight taxa present in the Clutha river system alone. In this region, several distinctive ‘flathead’ and ‘roundhead’ taxa (McDowall and Wallis 1996) exhibit broad biogeographic overlap (e.g. G. depressiceps and G. anomalus in the upper Taieri River; G. ‘sp D’ and G. ‘Pomahaka’ in the lower Clutha system; G. ‘southern’ and G. gollumoides in Southland; Campbell et al. 2022). Additionally, several zones of local species sympatry have been documented for these broadly overlapping taxa (Allibone et al. 1996; Waters et al. 2001b; Crow et al. 2009). While the local distributions of these taxa have been highly fragmented by anthropogenic activities, particularly by the introduction of exotic salmonid predators (Townsend and Crowl 1991; McDowall 2006), the strong biogeographic structure of extant populations (e.g. Fig. 2) potentially allows for numerous independent comparisons of species/populations in sympatry, parapatry, and allopatry.

Understanding the extent and impact of introgression along the speciation continuum is a key goal of evolutionary biology. To date, fine-scale genetic analyses of Galaxias contact zones have detected only minimal hybridization between sympatric taxa (Allibone et al. 1996; Esa et al. 2000; Waters et al. 2001b; Crow et al. 2009). By contrast, major discrepancies between mitochondrial (Waters and

Wallis 2001b) versus nuclear (Waters et al. 2010) phylogenetic reconstructions suggest that introgression may have been pervasive in the evolution of this assemblage over deeper evolutionary timeframes. We hypothesise that this apparent discrepancy may partly reflect the widespread loss and fragmentation of native Galaxias populations following human arrival (Townsend and Crowl 1991; McDowall 2006) which have reduced species ranges within drainages, hence limiting levels of contemporary admixture between taxa.

Here we capitalise on well-resolved phylogenomic and biogeographic (Fig. 1) frameworks for New Zealand galaxiid fishes (Campbell et al. 2022) to help understand the history of introgression in this species-rich complex, and to test hybridization hypotheses based on current distributional data. Specifically, we use the ABBA-BABA approach (Green et al. 2010; Martin et al. 2015) to test the extent to which the contemporary biogeographic overlap between taxa accurately predicts their introgression history. While numerous previous studies have detected extensive introgression among biogeographically proximate lineages (Hamlin et al. 2020), a handful of recent analyses imply that contemporary distributions do not always predict hybridization history (Folk et al. 2018). In the case of galaxiid fishes, we predict that both recent anthropogenic (Townsend and Crowl 1991; Esa et al. 2000) and ancient geologically-driven (Waters et al. 2001a; 2015; 2020) range shifts may have substantially impacted the introgression history of this diverse fish assemblage.

#### Methods

Selection of taxa for ABBA-BABA analysis

The ABBA-BABA approach was used to test for introgression among particular non-migratory Galaxias lineage pairs, using phylogenetic (Fig. 3) and biogeographic (Fig. 4) frameworks. Specifically, taxon selection was informed by a well-resolved genome-wide phylogeny of Galaxias previously derived from SNAPP analysis (Campbell et al. 2022; Fig. 1), which suggests little if any reticulation at deep phylogenetic levels (Fig. S1). All tests were phylogenetically rooted by inclusion of the diadromous sister species G. brevipinnis as an outgroup. Selection of ingroup taxa was based on the following criteria:

Sympatric taxa: the selection of sympatric taxa was based on regional biogeographic overlap, along with evidence for direct sympatry (i.e. species co-occurrence within single streams). For instance, the upper Taieri River species G. depressiceps and G. anomalus show broadly overlapping ranges (Figs. 1, 2, 4; Waters et al. 2015) and also occur sympatrically in Healy Ck (Allibone et al. 1996). Similarly, the widespread Southland G. ‘southern’ and G. gollumoides have numerous direct sympatry zones, and broad overlap across multiple distinct river systems (Waters et al. 2001b; Crow et al. 2009; Waters and Burridge 2016). A contact zone for the broadly overlapping G. ‘sp D’ and G. anomalus has been documented in Maori Creek (Campbell et al. 2022), and both taxa have wide distributions across the Manuherikia system (Figs. 1, 4). Finally, very tight geographic overlap is evident in Clutha River pairs G. ‘sp D’ and G. ‘Pomahaka’ (lower Clutha system; Fig. 1), and for G. ‘Teviot’ and G. pullus (Teviot system; Campbell et al. 2022) (Fig. 4). The broadly sympatric lower Taieri species pair (G. eldoni, G. pullus; McDowall 1997), which shows evidence of localized mitochondrial introgression (Waters and Wallis 2001a), could not be included in this analysis owing to their close sister relationship (Campbell et al. 2022). Additionally, samples from known hybrid zones, such as that formed via anthropogenic translocation of Taieri G. depressiceps into the Pool Burn (Esa et al. 2000), were excluded from all analyses.

Parapatric taxa: A few Galaxias taxa exhibit adjacent yet non-overlapping (parapatric) distributions within single drainages. Most notably, parapatric distributions have apparently arisen via ancient river capture events effecting the Clutha and Taieri systems (Waters et al. 2001a, 2015, 2020). While contemporary distributions imply the effected taxa have never infiltrated one another’s ranges, their pre-human distributions (now heavily fragmented) remain uncertain. As a case in point, the ‘captured’ Nevis River endemic G. ‘Nevis’ is nested within the broad range of the upper Clutha clade of G. ‘sp D’ (Waters et al. 2001a; Campbell et al. 2022); and likewise the Teviot River endemic G. ‘Teviot’ is nested within the lower Clutha clade of G. ‘sp D’. Along similar lines, the ‘captured’ upper Taieri lineages (G. depressiceps, G. anomalus) show essentially no geographic overlap with the distinctive lower Taieri galaxiid clade (G. eldoni, G. pullus) (Waters et al. 2015) (Fig. 4).

Allopatric taxa: The presence of isolated phylogeographic lineages (e.g. G. vulgaris Canterbury; G. ‘northern’ – Marlborough; G. gollumoides – Southland; G. eldoni – Taieri) allowed for ABBA-BABA tests involving completely allopatric taxa (i.e. geographically isolated in completely distinct drainage systems) (Fig. 4).

The extent of biogeographic overlap between pairs of taxa was further characterized on a scale ranging from 0 (complete allopatry; different rivers) to 5 (near-complete range overlap; extensive local sympatry). On this scale, parapatric taxa (Fig. 2) that lack current overlap yet co-occur within a drainage were ranked as 1, whereas 2-4 represent increasing extent of direct overlap.

Genomic analyses

Genome-wide comparisons among Galaxias taxa were performed using genotyping-by-sequencing (GBS) data from Campbell et al. (2022). These data comprised 52,352 SNPs from 187 specimens, across 13 taxa, representing 99 distinct sampling localities. Outgroup sequences were included from 17 individuals of the widespread diadromous taxon G. brevipinnis (the sister taxon of the nonmigratory G. vulgaris complex). All 12 freshwater-limited taxa (G. vulgaris complex; Waters et al.

- 2010) were represented by multiple specimens from multiple sites (total 170 individuals across 90 localities; mean 14 individuals per taxon).

We tested for nuclear introgression between specific sympatric, parapatric or allopatric taxon pairs (see above; Figs. 3, 4, Table 1) using the ABBA-BABA approach (Green et al., 2010; Durand et al.,

- 2011) as implemented in Dsuite v0.5. (Malinsky et al., 2021), under the genome-wide phylogenetic framework of Campbell et al. 2022 (Figs. 3, S1). This method statistically tests for asymmetric SNPsharing across a four-species phylogeny: [4[3[2,1]]]. Specifically, in cases of introgression between non-sister species 2 and 3, nucleotide polymorphisms mapped across this phylogeny are expected to show an excess of the ‘ABBA’ phylogenetic distribution (where A and B represent alternate alleles at a single locus; Martin et al. 2015) relative to ‘BABA’, i.e. with significantly more SNPs shared by species 2 and 3 than by species 1 and 3 (Table 1). F4, a very similar statistic based on correlation in allele frequencies among four taxa (Reich et al. 2009), was also computed using Dsuite. Finally, to further estimate the net proportion of the genome originating from introgression in each trio, we also calculated DP (Hamlin et al. 2020) from the output of Dsuite. In our analysis, the diadromous outgroup taxon G. brevipinnis was included as the ancestral lineage for each of these 4-taxon introgression analyses (Fig. 3). 3 of 18 tests (not shown) were ultimately excluded on the basis of tree uncertainty because BBAA was not the most common pattern for the trio topology leading to the lowest Dstatistic, suggesting tree uncertainty or non tree-like evolution (e.g. note evidence of phylogenetic conflict in Fig. S1).

We used a non-parametric approach to test for associations between geographic distributions and introgression signatures. Specifically, ABBA-BABA D-statistics obtained for allopatric, parapatric and sympatric taxon pairs (Figs. 3, 4) were compared using the Wilcoxon signed-rank test (Sokal and Rohlf, 1981). Additionally, we used regression analysis to test for more nuanced relationships between D-statistics and the extent of geographic overlap between taxon pairs (scaled from 0 (no overlap) to 5 (near-complete overlap).

Results Comparisons of ABBA-BABA D-statistics revealed a clear trend of increasing introgression signatures associated with increased geographic proximity of Galaxias lineages (Figs. 4, 5, 6). Combined parapatric and sympatric taxon pairs exhibited significantly stronger signatures of introgression relative to those of allopatric species (Wilcoxon test: W = 43, p = 0.03). Wilcoxon tests revealed near-significant increases in introgression for sympatric versus allopatric species pairs (W = 22, p = 0.06) and also for parapatric versus allopatric pairs (W = 4, p = 0.10). When range overlap between taxa was quantified on a scale of 0 (no overlap, distinct drainages) to 5 (near-complete overlap), significant correlations were observed between biogeographic overlap and introgression as estimated by D (R2 = 0.31; p = 0.02; Fig. 6), F4 (R2 = 0.28; p = 0.02; Fig. S2) and DP (R2 = 0.43; p = 0.005; Fig. S3).

Across the 15 ABBA-BABA tests, the strongest introgression signal was observed for the widely overlapping Southland species pair (G. ‘southern’ and G. gollumoides; D-statistic = 0.38; Table 1), with similarly substantial introgression (D = 0.36) signatures detected between G. ‘sp D’ and G. anomalus which co-occur in the Clutha system (Fig.1; Table 1). Notably strong introgression signatures were also detected for non-overlapping lineages within rivers, including upper-Taieri versus lower-Taieri comparisons (Fig. 2) (G. anomalus and G. eldoni, D = 0.30; G. depressiceps and G. pullus, D = 0.21; Table 1). Indeed, all sympatric (mean D = 0.26) and parapatric (mean D = 0.21) pairs showed highly significant introgression signals (D > 0.13; Table 1). By contrast, the allopatric comparisons (mean D = 0.10; Table 1) yielded the four lowest D values (Fig. 5, 6), with three of these five comparisons yielding D-statistics not significantly different from 0.

Discussion and Conclusions Introgression signatures strongest among sympatric taxa In the current study, genome-wide comparisons of freshwater Galaxias fish lineages revealed increasingly strong signatures of introgression with increasing geographic overlap of taxa. Allopatric lineages isolated across distinct river systems show significantly less evidence of hybridization than do lineages that co-occur within drainages. Interestingly, in addition to the predicted extensive introgression between sympatric lineages, our study also detected surprisingly strong signatures of introgression among taxa that currently have disjunct (‘parapatric’) distributions within catchments.

Our results for Galaxias broadly conform to the expectation that introgression is most likely to occur among proximate rather than geographically remote lineages (Figs. 4, 5, 6, S2, S3). Indeed, it is intuitive that species that regularly co-occur are most likely to experience hybridization and introgression (Harrison and Larson 2014). Unsurprisingly, the strongest signatures of introgression in the current study were detected for the species pair displaying the most extensive geographic overlap (Southland pair G. ‘southern’ and G. gollumoides; Fig. 4; Table 1), even though no hybrids between these taxa have previously been detected in nature; Waters et al. 2001b; Crow et al. 2009). Interestingly, the associated phylogenetic reconstructions of these taxa show little evidence of any substantial reticulation (Fig. S1). The analysis also supports a history of introgression between sympatric G. depressiceps and G. anomalus, which are again phylogenetically highly distinct (Fig. S1), and for which natural hybrids have previously been detected (Allibone et al. 1996). A strong introgression signature is also evident for sympatric but phylogenetically unrelated G. ‘sp D’ and G. ‘Pomahaka’, for which introgressive mitochondrial capture has previously been inferred (Waters et al. 2010; Campbell et al. 2022). Such findings are echoed by numerous previous analyses of diverse taxa which have found geographical proximity to be a strong predictor of introgression (e.g. Hamlin et al. 2020; Singhal et al. 2021).

Of the various estimators used to assess introgression in the current study, a particularly strong relationship with biogeographic overlap was observed for DP (R2 = 0.43, p = 0.005) Fig. S3). This statistic, proposed by Hamlin et al. (2020), represents a straightforward extension of D that includes BBAA in its denominator, in order to more accurately assess the net proportion of a genome originating from introgression. By contrast, the traditionally-used D statistic has been suggested to substantially overestimate admixture proportions (Martin et

al. 2015; Hamlin et al 2020), and may fail to scale linearly with introgression magnitude. Importantly, our findings across different introgression metrics (Fig. 6, S2, S3) support the increased use of DP in future analyses.

Past introgression among currently disjunct taxa In addition to introgression between sympatric taxa, our study also detected surprisingly strong signatures of introgression among taxa that are currently disjunct (e.g. parapatric lineages isolated in different subcatchments). Such cases include G. ‘sp D’ and G. ‘Nevis’ (which currently occupy distinct tributaries of the Clutha river system; Fig. 1); and disjunct upper-Taieri (G. depressiceps, G. anomalus) versus lower-Taieri (G. eldoni, G. pullus) taxa (Fig. 2; Waters et al. 2015). In each of these cases, no natural hybrids between these parapatric lineages have previously been detected, although ancient introgressive mtDNA capture has previously been proposed for parapatric G. pullus and G. anomalus (Waters et al. 2010). These data imply that contemporary biogeographic relationships do not completely predict past introgression dynamics, and thus may require evolutionary biogeographic explanations (e.g. temporal range shifts; see below).

A few previous studies have similarly found mismatches between current distributions and introgression history, perhaps resulting from past range shifts. For example, Folk et al. (2018) detected genetic signatures of past (Pleistocene) introgression between now biogeographically disjunct (separated by <1000 km) genera of montane versus boreal angiosperms. Similarly, multiple cases of ancient introgression have been detected among ancestral primate lineages (Vanderpool et al. 2020), for which ancient ranges (e.g. ancestral Macaca) are not representative of their contemporary distributions. Indeed, in cases where introgression was ancient, and/or the lineages involved subsequently experienced major biogeographic shifts (e.g. due to climatic change; Hewitt 2000; Wallis et al. 2016), it is quite plausible that current biogeography may fail to predict past introgression events (e.g. Kang et al. 2017; Meier et al. 2017; Manthey et al. 2020). However, in the absence of detailed fossil records and/or ancient DNA data, the potential contributions of range shifts and/or lineage extinctions to discordant relationships between modern distributions and introgression history (e.g. Green et al. 2010; Rogers et al. 2017) may be challenging to disentangle.

Unlike the aforementioned examples of terrestrial biogeographic range shifts, freshwaterlimited Galaxias lineages are tightly confined by drainage boundaries (Craw et al. 2016a).

These lineages often show deep phylogeographic structure among rivers and subcatchments (Waters et al. 2001a; Burridge et al. 2006, 2007, 2008), implying long-term biogeographic stability. Indeed, available evidence suggests that biogeographic evolution of these lineages has been broadly constrained by geological processes (Burridge et al. 2006; Waters et al. 2015). Moreover, such tectonic processes are thought to have generated the now parapatric distributions of formerly isolated lineages in the current Clutha (Waters et al. 2001a) and Taieri systems (Fig. 2; Waters et al. 2015). These ancient, geologically-mediated secondary contact events may explain several cases of inferred introgression (e.g. upper-Taieri species G. anomalus and G. depressiceps admixing with lower-Taieri taxa G. eldoni and G. pullus) (Fig. 2; Table 1).

Anthropogenic fragmentation obscures hybridization history The extent to which contemporary galaxiid biogeography has been impacted by anthropogenic forces remains unclear. Local Galaxias distributions have certainly been heavily impacted by anthropogenic phenomena including hydroelectric impoundments and invasive species (McDowall 1990; Townsend and Crowl 1991; McDowall 2006). In particular, the ranges of non-migratory species have been highly fragmented by the proliferation of exotic salmonid predators (Townsend and Crowl 1991), with Galaxias populations now excluded from major river channels (see Fig. 2) and broadly confined to isolated headwater habitats protected by waterfall barriers (McDowall 1990). Indeed, it seems very likely that salmonid predators have drastically reduced the potential for hybridization among now-fragmented Galaxias populations. These fragmented distributions may thus help to explain the discordance between contemporary biogeography versus inferred introgression histories. Crucially, the strong introgression signatures evident even among taxa that are no longer in direct contact (see above) may be partly explained by this anthropogenic fragmentation, with former species contact zones likely eliminated by invasive salmonids.

Given the evolutionary constraints of the New Zealand Galaxias radiation, and the unavoidably limited number of sympatric/parapatric taxon pairs, it is conceivable that the imperfect correlation between biogeographic overlap and introgression could partly reflect phylogenetic non-independence across multiple tests (Eaton et al. 2015). For instance, the seemingly anomalous signature of introgression detected for the allopatric pair G. ‘Pomahaka’ and G. vulgaris (Fig. 4) may actually relate to introgression between G. ‘Pomahaka’ and the sympatric G. ‘sp D’ (the latter being a sister species of G. vulgaris (Fig.

S1)). Potential ancient introgression among ancestral lineages could also have contributed to some of the admixture signatures detected among extant taxa (Vanderpool et al. 2020). However, there is also ample evidence of relatively recent introgression (see above) among sympatric (and even parapatric) taxa. Crucially, any ancestral introgression should not disproportionately have impacted any of the three biogeographic categories under consideration, which all involve comparable phylogenetic depths (Fig. 3). Interestingly, our inference of extensive introgression among even the most-divergent lineages of this species complex (e.g. G. ‘southern’ versus G. gollumoides) suggests that phylogenetic relatedness does not substantively impact the potential for (and extent of) introgression, at least over the Quaternary temporal scale of this recent freshwater fish radiation (Burridge et al. 2008; Craw et al. 2016a). This finding appears to contrast with the conclusions of some previous studies suggesting strong correlations between phylogenetic relatedness and introgression (e.g. Hamlin et al. 2020).

Broadly, the current study implies that contemporary biogeographic relationships provide a powerful framework for understanding the history of geneflow among closely-related freshwater fish taxa. We also conclude that both modern and ancient biogeographic shifts, including recent anthropogenic range fragmentation and geologically-driven riven capture events, have strongly influenced introgression histories, in turn shaping the evolutionary trajectories of these diverse freshwater-limited fish lineages.

Overall, our findings suggest that reliance on modern species distributional data may lead researchers to underestimate the potential for past contact and admixture between currently isolated/disjunct populations and species. Indeed, we suspect that both natural and anthropogenic range shifts may have obscured past biological distributions in many regions, and for many taxa (e.g. Waters and Grosser 2016). We recommend that biologists more widely apply the types of phylogenomic and biogeographic approaches outlined in the current study to help shed new light on the past evolutionary and spatial dynamics of geographically structured lineages.

References Allibone RM, Crowl TA, Holmes JM, King TM, McDowall RM, Townsend CR, Wallis GP.

1996. Isozyme analysis of Galaxias species (Teleostei: Galaxiidae) from the Taieri River, South Island, New Zealand: a species complex revealed. Biological Journal of the Linnean Society 57: 107–127.

Avise JC. 1990. Flocks of African fishes. Nature 347: 512–513.

Beckman EJ, Benham PM, Cheviron ZA, Witt CC. 2018. Detecting introgression despite phylogenetic uncertainty. The case of the South American siskins. Molecular Ecology 27:4350-4367.

Burridge CP, Craw D, Fletcher D, Waters JM. 2008. Geological dates and molecular rates: Fish DNA sheds light on time dependency. Molecular Biology and Evolution 25: 624–633.

- Burridge CP, Craw D, Waters JM. 2006. River capture, range expansion, and cladogenesis: the genetic signature of freshwater vicariance. Evolution 60: 1038–1049.
- Burridge CP, Craw D, Waters JM. 2007. An empirical test of freshwater vicariance via river capture. Molecular Ecology 16: 1883–1895.

Campbell CSM, Dutoit L, King TM, Craw D, Burridge CP, Wallis GP, Waters JM. 2022. Genome-wide analysis resolves the radiation of New Zealand’s freshwater Galaxias vulgaris complex and reveals a candidate species obscured by mitochondrial capture. Diversity and Distributions 28: 2255–2267.

Craw D, Upton P, Burridge CP, Wallis GP, Waters JM. 2016a. Rapid biological speciation driven by tectonic evolution in New Zealand. Nature Geoscience 9: 140–144.

### Craw D, Craw L, Burridge CP, Wallis GP, Waters JM. 2016b. Evolution of the Taieri River catchment, East Otago, New Zealand. New Zealand Journal of Geology and Geophysics 59: 257–273.

Crow SK, Waters JM, Closs GP, Wallis GP. 2009. Morphological and genetic analysis of Galaxias ‘southern’ and G. gollumoides: interspecific differentiation and intraspecific structuring. Journal of the Royal Society of New Zealand 39: 43–62.

Durand EY, Patterson N, Reich D, Slatkin M. 2011. Testing for ancient admixture between closely related populations. Molecular Biology and Evolution 28: 2239–2252.

Eaton DAR, Hipp AL, González-Rodríguez A, Cavender-Bares J. 2015. Historical introgression among the American live oaks and the comparative nature of tests for introgression. Evolution 69: 2587–2601.

Echelle AA, Kornfield I. 1984. Evolution of fish. Species flocks. Orono Press, University of Maine.

### Esa YB, Waters JM, Wallis GP. 2000. Introgressive hybridization between Galaxias depressiceps and Galaxias sp D (Teleostei: Galaxiidae) in Otago, New Zealand: secondary contact mediated by water races. Conservation Genetics 1: 329–339.

Feulner PGD, Seehausen O. 2019. Genomic insights into the vulnerability of sympatric whitefish species flocks. Molecular Ecology 28: 615–629.

Folk RA, Visger CJ, Soltis PS, Soltis DE, Guralnick RP. 2018. Geographic range dynamics drove ancient hybridization in a lineage of angiosperms. American Naturalist 192: 171– 187.

Giska I, Farelo L, Pimenta J, Seixas FA, Ferreira MS, Marques JP, Miranda I, Letty J, Jenny H, Hackländer K, Magnussen E, Melo-Ferreira. 2019. Introgression drives repeated evolution of winter coat color polymorphism in hares. Proceedings of the National Academy of Sciences 116: 24150-24156.

Green RE, Krause J, Briggs AW, Maricic T, Stenzel U, Kircher M, Patterson N, Li H, Zhai W, Fritz MHY, Hansen NF, Durand EY, Malaspinas AS, Jensen JD, Marques-Bonet T, Alkan C, Prufer K, Meyer M, Burbano HA, … Paabo S. 2010. A draft sequence of the Neandertal genome. Science 328, 710–722.

### Hamlin JAP, Hibbins MS, Moyle LC. 2020. Assessing biological factors affecting postspeciation introgression. Evolution Letters 4: 137–154. Harrison RG, Larson EL. 2014. Hybridization, introgression, and the nature of species boundaries. Journal of Heredity 105: 795–809.

Hewitt G. 2000. The genetic legacy of the Quaternary ice ages. Nature 405: 907–913.

Irisarri I, Singh P, Koblmüller S, Torres-Dowdall J, Henning F, Franchini P, Fischer C, Lemmon AR, Moriarty Lemmon E, Thallinger GG, Sturmbauer C, Meyer A. 2018. Phylogenomics uncovers early hybridization and adaptive loci shaping the radiation of Lake Tanganyika cichlid fishes. Nature Communications 9: 3159.

Joyce DA, Lunt DH, Genner MJ, Turner GF, Bills R, Seehausen O. 2011. Repeated colonization and hybridization in Malawi cichlids. Current Biology 21: R109–109.

Kang L, Garner HR, Price DK, Michalak P. 2017. A test for gene flow among sympatric and allopatric Hawaiian picture-winged Drosophila. Journal of Molecular Evolution 84: 259–266.

Kong S, Kubatko LS. 2021. Comparative performance of popular methods for hybrid detection using genomic data. Systematic Biology 70: 891–907.

MacGuigan DJ, Near TJ. 2019. Phylogenomic signatures of ancient introgression in a rogue lineage of darters (Teleostei: Percidae). Systematic Biology 68:329–346.

Malinsky M, Matschiner M, Svardal H. 2021. Dsuite ‐ Fast D‐statistics and related admixture evidence from VCF files. Molecular Ecology Resources 21: 584–595.

Mallet J. 2007. Hybrid speciation. Nature 446: 279–283.

Mallet J, Besansky N, Hahn MW. 2016. How reticulated are species? BioEssays 38:140–149.

Manthey JD, Oliveros CH, Andersen MJ, Filardi CE, Moyle RG. 2020. Gene flow and rapid differentiation characterize a rapid insular radiation in the southwest Pacific (Aves: Zosterops). Evolution. 74: 1788–1803.

Martin SH, Amos W. 2020. Signatures of introgression across the allele frequency spectrum. Molecular Biology and Evolution 38: 717–726. Martin SH, Davey JW, Jiggins CD. 2015. Evaluating the use of ABBA-BABA statistics to locate introgressed loci. Molecular Biology and Evolution 32: 244–257.

Masonick P, Meyer A, Hulsey CD. 2022. Phylogenomic analyses show repeated evolution og hypertrophied lips among Lake Malawi fishes. Genome Biology and Evolution 14: evac051.

McDowall RM. 1970. The galaxiid fishes of New Zealand. Bulletin of the Museum of Comparative Zoology 139: 341–431.

McDowall RM. 1990. New Zealand freshwater fishes: a natural history and guide. Heinemann Reed, Auckland.

McDowall RM. 1997. Two further new species of Galaxias (Teleostei: Galaxiidae) from the Taieri River, southern New Zealand. Journal of the Royal Society of New Zealand 27: 199–217.

McDowall RM. 2006. Crying wolf, crying foul, or crying shame: alien salmonids and a biodiversity crisis in the southern cool-temperate galaxioid fishes? Reviews in Fish Biology and Fisheries 16: 233–422.

McDowall RM, Wallis GP. 1996. Description and redescription of Galaxias species (Teleostei: Galaxiidae) from Otago and Southland. Journal of the Royal Society of New Zealand 26: 401–427.

Meier JI, Marques DA, Mwaiko S, Wagner CE, Excoffier L, Seehausen O. 2017. Ancient hybridization fuels rapid cichlid fish adaptive radiations. Nature Communications 8: 1– 11.

Meyer A, Kocher TD, Basasibwalu P, Wilson AC. 1990. Monophyletic origin of Lake Victoria cichlid fishes suggested by mitochondrial DNA sequences. Nature 347: 550–553.

Perea S, Vukid J, Šanda R, Doadrio I. 2016. Ancient mitochondrial capture as factor promoting mitonuclear discordance in freshwater fishes: a case study in the genus Squalius (Actinopterygii, Cyprinidae) in Greece. PLoS One 11: e0166292.

Ravinet M, Kume M, Ishikawa A, Kitano J. 2020. Patterns of genomic divergence and introgression between Japanese stickleback species with overlapping breeding habitats. Journal of Evolutionary Biology 34: 114–127.

Reich D, Thangaraj K, Patterson N, Price AL, Singh L. 2009. Reconstructing Indian population history. Nature 461: 489–494. Rogers AR, Bohlender RJ, Huff CD. 2017. Early history of Neanderthals and Denisovans.

Proceedings of the National Academy of Sciences 114: 9859–9863. Schluter D. 2000. The Ecology of Adaptive Radiation. Oxford University Press, Oxford. Seehausen O. 2004. Hybridization and adaptive radiation. Trends in Ecology and

Evolution 19: 198-207. Selz OM, Seehausen O. 2019. Interspecific hybridization can generate functional novelty in cichlid fish. Proceedings of the Royal Society B 286: 20191621. Singhal S, Derryberry GE, Bravo GA, Derryberry EP, Brumfield RT, Harvey MG. 2021. The dynamics of introgression across an avian radiation. Evolution Letters 5-6: 568–581.

Sokal RR, Rohlf FJ. 1981. Biometry, 2nd edn. Freeman, San Francisco, 859 pp.

Svardal H, Quah FX, Malinsky M, Ngatunga BP, Miska EA, Salzburger W, Genner MJ, Turner GF, Durbin R. 2020. Ancestral hybridization facilitated species diversification in the Lake Malawi cichlid fish adaptive radiation. Molecular Biology and Evolution 37: 1100-1113.

Townsend CR, Crowl TA. 1991. Fragmented population structure in a native New Zealand fish: an effect of introduced brown trout? Oikos 61: 347–354.

Unmack PJ, Sandoval-Castillo J, Hammer MP, Adams M, Raadik TA, Beheregaray LB. 2017. Genomewide SNPs resolve a key conflict between sequence and allozyme data to confirm another threatened candidate species of river blackfishes (Teleostei: Percichthyidae: Gadopsis). Molecular Phylogenetics and Evolution 109: 415–420.

Vanderpool D, Minh BQ, Lanfear R, Hughes D, Murali S, Harris RA, Raveendran M, Muzny DM, Hibbins MS, Williamson RJ, Gibbs RA, Worley KC, Roges J, Hahn MW. 2020. Primate phylogenomics uncovers multiple rapid radiations and ancient interspecific introgression. PLoS Biology 18: e3000954.

Wallis GP, Cameron‐ Christie SR, Kennedy HL, Palmer G, Sanders TR, Winter DJ. 2017. Interspecific hybridization causes long‐ term phylogenetic discordance between nuclear and mitochondrial genomes in freshwater fishes. Molecular Ecology 26: 3116– 3127.

Wallis GP, Waters JM, Upton P, Craw D. 2016. Transverse alpine speciation driven by glaciation. Trends in Ecology and Evolution 31: 916–926.

Waters JM, Burridge CP. 2016. Fine‐scale habitat preferences influence within‐river population connectivity: a case‐study using two sympatric New Zealand Galaxias fish species. Freshwater Biology 61: 51–56.

Waters JM, Burridge CP, Craw D. 2020. River capture and freshwater biological evolution: A review of galaxiid fish vicariance. Diversity 12: 216.

Waters JM, Craw D, Youngson JH, Wallis GP. 2001a. Genes meet geology: fish phylogeographic pattern reflects ancient, rather than modern, drainage connections. Evolution 55: 1844–1851.

Waters JM, Emerson BC, Arribas P, McCulloch GA. 2020. Dispersal reduction: causes, genomic mechanisms, and evolutionary consequences. Trends in Ecology and Evolution 35: 512–522.

Waters JM, Grosser S. 2016. Managing shifting species: ancient DNA reveals conservation conundrums in a dynamic world. BioEssays 38: 1177–1184.

Waters JM, Esa YB, Wallis GP. 2001b. Genetic and morphological evidence for reproductive isolation between sympatric populations of Galaxias (Teleostei: Galaxiidae) in South Island, New Zealand. Biological Journal of the Linnean Society 73: 287–298.

Waters JM, McCulloch GA. 2021. Reinventing the wheel? Reassessing the roles of gene flow, sorting and convergence in repeated evolution. Molecular Ecology 30: 4162– 4172.

Waters JM, Rowe DL, Burridge CP, Wallis GP. 2010. Gene trees versus species trees: reassessing life-history evolution in a freshwater fish radiation. Systematic Biology 59: 504–517.

- Waters JM, Wallis GP. 2001a. Mitochondrial DNA phylogenetics of the Galaxias vulgaris complex from South Island, New Zealand: rapid radiation of a species flock. Journal of Fish Biology 58: 1166–1180.
- Waters JM, Wallis GP. 2001b. Cladogenesis and loss of the marine life‐ history phase in freshwater galaxiid fishes (Osmeriformes: Galaxiidae). Evolution 55: 587–597.

Waters JM, Wallis GP, Burridge CP, Craw D. 2015. Geology shapes biogeography: Quaternary river-capture explains New Zealand's biologically ‘composite’ Taieri River. Quaternary Science Reviews 120: 47–56.

Zheng Y, Janke A. 2018. Gene flow analysis method, the D-statistic, is robust in a wide parameter space. BMC Bioinformatics 19: 10.

Table 1. Summary of ABBA-BABA analyses for sympatric (sym), parapatric (par), and allopatric (all) Galaxias taxa, showing D-statistics (D) (and associated metrics F4 and DP). The relative numbers of SNPs (mapped across each four-species phylogeny; Fig. 3) fitting BBAA, ABBA, and BABA phylogenetic distributions are shown for each comparison (com). In each case, an excess of ABBA over BABA is consistent with introgression between species 2 and 3. For each comparison (comp), the extent of geographic overlap between species 2 and species 3 is indicated on a scale from 0 (isolated in distinct drainages) to 5 (full overlap within drainages). The diadromous sister species Galaxias brevipinnis is included as an outgroup for each test. Phylogenetic relationships for each comparison are highlighted in Fig. 3, and biogeographic relationships in Fig. 4.

comp sp1 sp2 sp3 out type overlap D p F4 DP BBAA ABBA BABA

- 1 dep sth gol bre sym 5 0.38 <0.0001 0.08 0.11 905.72 255.82 115.64

- 2 sth dep ano bre sym 4 0.13 0.0019 0.02 0.04 845.50 229.10 174.88

- 3 dep tev pul bre sym 3 0.14 0.0005 0.05 0.04 871.31 185.21 140.53

- 4 gol pom spd bre sym 4 0.27 <0.0001 0.06 0.07 823.67 198.57 115.27

- 5 gol ano spd bre sym 4 0.36 <0.0001 0.10 0.13 726.34 266.37 124.75

- 6 gol ano pul bre par 1 0.18 0.0003 0.04 0.04 955.05 146.60 101.84

- 7 vul dep eld bre par 2 0.20 <0.0001 0.06 0.07 750.88 250.57 166.78

- 8 gol nev spd bre par 1 0.19 0.0004 0.02 0.02 1297.21 84.28 57.86

- 9 gol ano eld bre par 1 0.30 <0.0001 0.05 0.07 938.40 170.77 92.26

- 10 vul dep pul bre par 1 0.21 <0.0001 0.08 0.06 864.09 236.80 156.22

- 11 vul dep gol bre all 0 0.12 0.0019 0.03 0.04 939.38 226.74 177.36

- 12 eld pul gol bre all 0 0.00 0.9234 0.00 0.00 626.24 191.77 190.48

- 13 vul spd eld bre all 0 0.01 0.8461 0.00 0.00 926.99 169.85 166.99

- 14 sth nth eld bre all 0 0.09 0.1156 0.03 0.03 779.41 187.57 155.44

- 15 ano pom vul bre all 0 0.27 <0.0001 0.05 0.06 963.40 184.80 106.59

Fig. 1

Figure 1: Biogeography of the freshwater-limited Galaxias vulgaris complex (South Island, New Zealand), summarising the distributions of the 12 recognised taxa (Waters et al. 2010, 2015; Campbell et al. 2022). The Stewart Island distributions of sympatric Southland taxa G. gollumoides and G. ‘southern’ are not shown. Lineages are coloured according to region, to highlight the overlapping ranges of several unrelated ‘flathead’ (left), ‘roundhead’ and ‘lower Taieri’ (right) clade lineages.

Fig. 2

gollumoides ‘Nevis’

R

anomalus

Manuherikia

‘Pomahaka’

Kye Burn

pullus eldoni

depressiceps

urn

‘Teviot’ ‘southern’ vulgaris

B

ol

o

P

| | |
|---|---|
| | |
| | |

TaieriR

‘northern’

‘sp D’

TeviotR

Clutha R

R

ri

i

T

WaiporiR

20 km N

Figure 2: Examples of Galaxias lineage sympatry versus parapatry in southern New Zealand. Otago’s Taieri River (drainage boundaries indicated by dashes) has a geologically composite origin stemming from an ancient river capture event which united the formerly distinct upper and lower Taieri systems (Waters et al. 2015; Craw et al. 2016b). This capture event led to broadly disjunct (parapatric) distributions of unrelated upper-Taieri (anomalus, depressiceps) versus lower-Taieri (eldoni, pullus) fish assemblages, but is likely to have facilitated opportunities for secondary contact. In addition to broad range overlap within each zone, direct sympatry has been detected for both upper Taieri (Allibone et al. 1996) and lower Taieri (Waters et al. 2000a) species pairs. However, as the local distributions of these lineages have been highly fragmented following introductions of salmonid predators (Townsend and Crowl 1991; McDowall 2006), the extent of historic lineage sympatry (e.g. in main channel habitats now dominated by trout) remains uncertain.

brevipinnis

brevipinnis

brevipinnis

brevipinnis

brevipinnis

1 2 3 4 5

gollumoides ‘Nevis’

gollumoides ‘Nevis’

###### gollumoides ‘Nevis’

gollumoides ‘Nevis’

gollumoides ‘Nevis’

###### ARAPATRYPSYMPATRYALLOPATRY

###### anomalus

anomalus

anomalus

###### anomalus

anomalus

‘Pomahaka’

###### ‘Pomahaka’

‘Pomahaka’

‘Pomahaka’

‘Pomahaka’

pullus eldoni

pullus eldoni

###### pullus eldoni

pullus eldoni

pullus eldoni

depressiceps ‘Teviot’

depressiceps ‘Teviot’ southern’ vulgaris

depressiceps ‘Teviot’

###### depressiceps

depressiceps ‘Teviot’ southern’ vulgaris

‘Teviot’

‘southern’ vulgaris

###### ‘southern’

‘southern’ vulgaris

vulgaris

‘northern

‘northern’

‘northern’

‘northern’

‘northern’

‘sp D’

‘sp D’

‘sp D’

‘sp D’

‘sp D’

brevipinnis

brevipinnis

brevipinnis

brevipinnis

brevipinnis

6 7 8 9 10

gollumoides ‘Nevis’

gollumoides ‘Nevis’

gollumoides ‘Nevis’

gollumoides ‘Nevis’

gollumoides ‘Nevis’

anomalus

anomalus

anomalus

anomalus

anomalus

‘Pomahaka

‘Pomahaka’

‘Pomahaka’

‘Pomahaka’

Pomahaka’

pullus eldoni

pullus eldoni

pullus eldoni

pullus eldoni

pullus eldoni

depressiceps

depressiceps ‘Teviot’

depressiceps ‘Teviot’

depressiceps

depressiceps ‘Teviot’ southern’ vulgaris

‘Teviot’

‘Teviot’

‘southern’ vulgaris

‘southern’ vulgaris

‘southern’ vulgaris

‘southern’ vulgaris

‘northern’

‘northern’

‘northern’

‘northern’

‘northern’

‘sp D’

‘sp D’

‘sp D’

‘sp D’

‘sp D’

brevipinnis

brevipinnis

brevipinnis

brevipinnis

brevipinnis

11 12 13 14 15

###### gollumoides ‘Nevis’

gollumoides ‘Nevis’

###### gollumoides ‘Nevis’

gollumoides ‘Nevis’

gollumoides ‘Nevis’

anomalus

anomalus

anomalus

anomalus

anomalus

‘Pomahaka’

###### ‘Pomahaka’

‘Pomahaka’

‘Pomahaka’

Pomahaka’

pullus eldoni

###### pullus eldoni

pullus eldoni

###### pullus eldoni

###### pullus eldoni

###### depressiceps

depressiceps ‘Teviot’

depressiceps ‘Teviot’

depressiceps ‘Teviot’

depressiceps ‘Teviot’

‘Teviot’

‘southern’ vulgaris

‘southern’ vulgaris

‘southern’ vulgaris

‘southern’ vulgaris

‘southern’ vulgaris

‘northern’

‘northern’

‘northern’

‘northern’

‘northern’

‘sp D’

‘sp D’

‘sp D’

‘sp D’

‘sp D’

Figure 3: Phylogenetic relationships of Galaxias taxon pairs included in ABBA-BABA analyses, based on Campbell et al. (2022). Each tree represents a distinct test for introgression, as summarized in Table 1. The diadromous sister species Galaxias brevipinnis (blue) was used as the outgroup taxon for each analysis. For each comparison, species one is coloured red, whereas species two and three are colour-coded according to their biogeographic relationships (see Fig. 4; green – sympatric; orange – parapatric; purple – allopatric).

|1<br><br>D = 0.38|
|---|

|2<br><br>D = 0.13|
|---|

|4<br><br>D = 0.27|
|---|

|3<br><br>D = 0.14|
|---|

|5<br><br>D = 0.36|
|---|

SYMPATRYARAPATRYP

|6<br><br>D = 0.18|
|---|

|10<br><br>D = 0.21|
|---|

|8<br><br>D = 0.19|
|---|

|9<br><br>D = 0.30|
|---|

|7<br><br>D = 0.20|
|---|

|11<br><br>D = 0.12|
|---|

|D = 0.27|
|---|

|13<br><br>D = 0.01<br><br>|
|---|

|14<br><br>D = 0.09|
|---|

|12<br><br>D = 0.00<br><br>|
|---|

ALLOPATRY

Figure 4: Biogeographic range comparisons of sympatric (1-5), parapatric (6-10) and allopatric (11-

15) Galaxias taxon pairs included in ABBA-BABA analyses (see Fig 3). Sympatric taxa show extensive overlap, with evidence of direct contact; parapatric taxa co-occur within drainages but with little or no overlap; allopatric taxa are restricted to completely distinct drainage systems. D statistics are indicated for each comparison (see Table 1).

|allopatry parapatry sympatry<br><br>0.0<br><br>0.1<br><br>0.3<br><br>0.2<br><br>0.0<br><br>0.1<br><br>0.2<br><br>0.3<br><br>| |
|---|
<br><br>allopatry pastcontact sympatry<br><br>type<br><br>D statistic|
|---|

D statistic

D statistic

Figure 5: Comparison of ABBA-BABA D-statistics for allopatric, parapatric and sympatric Galaxias species comparisons (Figs. 3, 4; Table 1). Combined sympatric and parapatric taxon comparisons (mean D = 0.23) yielded significantly stronger introgression signals than were detected for allopatric taxa (mean D = 0.10) (p = 0.03).

|0.0<br><br>0.1<br><br>0.2<br><br>0.3<br><br>0 1 2 3 4 5<br><br>overlap<br><br>D statistic|
|---|

D statistic

Figure 6: Comparison of D-statistics against biogeographic overlap among selected pairs of freshwater-limited Galaxias taxa (R2 = 0.31; p = 0.02) (ranked from 0 (no overlap) to 5 (nearcomplete overlap)) (Fig. 4, Table 1).
