#!/usr/bin/env Rscript
# Standalone descriptive figures from frozen-history analysis; base R only.
root <- 'data/common_model/interrogation_20260920'
cases <- read.csv(file.path(root, 'selected_cases.csv'), check.names=FALSE)
annual <- read.csv(file.path(root, 'case_annual_refuge.csv'), check.names=FALSE)
counts <- read.csv(gzfile(file.path(root, 'survivor_conditioned_natural_counts.csv.gz')), check.names=FALSE)
colours <- c(R_H='#16857d', R_T='#8662a6', R_C='#c46d20', R_J='#286caa')
out <- file.path(root, 'figures'); dir.create(out, recursive=TRUE, showWarnings=FALSE)
device_pair <- function(name, width, height, draw) {
  png(file.path(out,paste0(name,'.png')),width=width,height=height,units='in',res=160)
  draw(); dev.off()
  pdf(file.path(out,paste0(name,'.pdf')),width=width,height=height,useDingbats=FALSE)
  draw(); dev.off()
}
profile_panel <- function(z, heading) {
  a <- annual[annual$source_id==z$source_id & abs(annual$q-z$q)<1e-12 & annual$observation_model==z$observation_model,]
  a <- a[a$year>=1972,]; a<-a[order(a$year),]
  upper <- a$weighted_refuge_mean+1.96*a$weighted_refuge_mean_mc_se
  ylim <- c(0,max(a$unconditional_refuge_mean,upper,na.rm=TRUE)*1.08)
  plot(a$year,a$weighted_refuge_mean,type='n',xlim=c(1972,2002),ylim=ylim,
       xlab='State year',ylab='Refuge mean (model counts)',main=heading,cex.main=.88)
  abline(v=c(1996,1998),col='#dddddd',lty=3)
  polygon(c(a$year,rev(a$year)),c(pmax(0,a$weighted_refuge_mean-1.96*a$weighted_refuge_mean_mc_se),rev(upper)),
          col=adjustcolor(colours[z$restriction],alpha.f=.17),border=NA)
  lines(a$year,a$unconditional_refuge_mean,lty=2,col='#777777',lwd=1.4)
  lines(a$year,a$weighted_refuge_mean,col=colours[z$restriction],lwd=2)
  mtext(sprintf('S2002 = %.3g; K_R = %.1f; q = %.3f',min(1,z$weighted_terminal_survival),z$K_R,z$q),side=3,line=.1,cex=.68)
}
device_pair('base_refuge_examples',12,9,function(){
  par(mfrow=c(3,4),mar=c(3.3,3.7,2.9,.6),oma=c(2.4,0,2,0),mgp=c(2.3,.7,0),las=1)
  for (role in c('minimum','middle','maximum')) for (restriction in names(colours)) {
    z <- cases[cases$role==paste('base',restriction,role,sep='_'),]
    profile_panel(z,paste(restriction,role,'survival example'))
  }
  mtext('Base configuration: fixed q = 0.02 and shared observation quality',outer=TRUE,side=3,line=.4,cex=1.05)
  mtext('Solid: factual-weighted mean; dashed: unconditional mean; band: pointwise +/-1.96 Monte Carlo SE. Panel y scales differ.',outer=TRUE,side=1,line=.3,cex=.78)
  mtext('Illustrative source order statistics, not a posterior sample. Lines are ensemble means, not individual fish histories.',outer=TRUE,side=1,line=1.4,cex=.78)
})
device_pair('boundary_refuge_examples',11,8,function(){
  par(mfrow=c(2,3),mar=c(3.5,4,3.2,.7),oma=c(2.3,0,2,0),mgp=c(2.5,.7,0),las=1)
  for (restriction in names(colours)) {
    z <- cases[cases$role==paste('across_config',restriction,'minimum',sep='_'),]
    heading<-paste(restriction,gsub('minimum_dated_','',z$configuration),sep=': ')
    profile_panel(z,heading)
  }
  for (seed in c(20260918,20260919)) {
    z <- cases[cases$role==paste('high_q',seed,sep='_'),]
    profile_panel(z,paste('R_C adult-first; seed',substr(seed,7,8)))
  }
  mtext('Boundary examples: changed configuration or detection scenario labelled',outer=TRUE,side=3,line=.4,cex=1.02)
  mtext('First four: lowest survival across configurations at q=.02/shared quality. Last two: qualified q=.20 examples.',outer=TRUE,side=1,line=.3,cex=.78)
  mtext('Same legend as base examples; ensemble means and Monte Carlo bands. Different panels need not share parameter values.',outer=TRUE,side=1,line=1.4,cex=.78)
})
device_pair('survival_and_persistent_population',10,8,function(){
  par(mfrow=c(2,2),mar=c(4.1,4.5,2.4,.7),oma=c(4.8,0,1,0),mgp=c(2.8,.8,0),las=1)
  for (q in c(.005,.02,.05,.2)) {
    z<-counts[abs(counts$q-q)<1e-12 & counts$state_year==2002,]
    plot(NA,xlim=c(0,1),ylim=c(3,550),log='y',xlab='Factual-weighted survival to 2002',
         ylab='Mean natural-range count | survival',main=paste('Effective detection q =',q))
    abline(h=c(10,50,100,500),col='#eeeeee')
    ok <- tolower(as.character(z$conditional_weight_qualified))=='true'
    if(any(ok)) points(pmin(1,z$weighted_terminal_survival[ok]),z$natural_total_mean_given_terminal_survival[ok],
           pch=ifelse(z$observation_model[ok]=='shared_quality',16,1),cex=.65,
           col=adjustcolor(colours[z$restriction[ok]],alpha.f=.6))
    if(any(!ok)) points(pmin(1,z$weighted_terminal_survival[!ok]),z$natural_total_mean_given_terminal_survival[!ok],pch=4,col='#666666',cex=.75)
  }
  mtext('Conditional process means, not population bounds. Points reuse sources across q and observation laws.',outer=TRUE,side=1,line=.7,cex=.72)
  par(fig=c(0,1,0,.075),new=TRUE,mar=c(0,0,0,0),oma=c(0,0,0,0));plot.new()
  legend('center',legend=c(names(colours),'Homogeneous','Shared quality','Conditional weights unqualified'),
         col=c(colours,'#444444','#444444','#666666'),pch=c(rep(16,4),1,16,4),ncol=4,bty='n',cex=.78)
})
early <- read.csv('data/common_model/early_lake_20260920/early_lake_contrasts.csv',check.names=FALSE)
early <- early[tolower(as.character(early$factual_compatible))=='true' & early$configuration=='base' &
               abs(early$q-.02)<1e-12 & early$observation_model=='shared_quality',]
source_ids <- sort(unique(early$source_id))
labels <- sub('common-production\\|202609','',source_ids)
labels <- gsub('\\|base\\|R_J\\|',' / ',labels)
labels <- gsub('\\|',' / ',labels)
device_pair('early_lake_overshoot',12,6.8,function(){
  par(mfrow=c(1,4),mar=c(4.4,5.6,3,.5),oma=c(2.7,0,2,0),mgp=c(2.9,.7,0),las=1)
  for (year in c(1980,1983,1987,1988)) {
    z <- early[early$endpoint==paste0('lake_N_L_',year),]
    z <- z[match(source_ids,z$source_id),]
    limits<-range(z$ci95_low,z$ci95_high,0); limits<-limits+c(-1,1)*max(diff(limits)*.08,.05)
    plot(z$estimate_cf_minus_factual,seq_along(source_ids),xlim=limits,ylim=c(.5,length(source_ids)+.5),
         pch=16,col='#286caa',yaxt='n',xlab='Overshoot removed - factual',ylab='',main=paste('Lake count:',year))
    axis(2,at=seq_along(source_ids),labels=labels,cex.axis=.72)
    abline(v=0,lty=2,col='#777777')
    segments(z$ci95_low,seq_along(source_ids),z$ci95_high,seq_along(source_ids),col='#286caa',lwd=1.3)
  }
  mtext('Paired early-lake effects: base R_J, q=.02, shared quality; 12 factual-compatible source profiles',outer=TRUE,side=3,line=.5,cex=1)
  mtext('Positive differences mean greater lake abundance without the piscivory overshoot. Baseline trout effects remain.',outer=TRUE,side=1,line=.3,cex=.78)
  mtext('Intervals: estimate +/-1.96 paired Monte Carlo SE; not simultaneous confidence or field uncertainty. Panel x scales differ.',outer=TRUE,side=1,line=1.5,cex=.78)
})
