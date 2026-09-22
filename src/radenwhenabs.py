# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.4.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

import pandas as pd
import numpy as np
import re
import io
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import subprocess
import requests
import json
import os

maxraadsqrt=5
#raadidx=np.arange(-maxraadsqrt,maxraadsqrt)+0.5
#risqr =np.meshgrid(raadidx, raadidx)
risqr= np.mgrid[-maxraadsqrt:maxraadsqrt,-maxraadsqrt:maxraadsqrt]+0.501
risqr=np.moveaxis(risqr,0,2)
risqr=np.reshape(risqr,(-1,2))
#df1r=pd.DataFrame(risqr)
risqr.shape
risqr
ridf=pd.DataFrame(risqr).add_prefix('Lidcol')
ridf['Liddst']= ridf['Lidcol0']*ridf['Lidcol0'] + ridf['Lidcol1']*ridf['Lidcol1'] 
ridf 

# +
nparty=3
rsizes=(4.3, 12.2 ,7.8)
def mkraad(genridif, rdid,straal, posx,posy):
    rv=genridif.copy()
    rv['Rdidx']= "Gem"+ (str(rdid))
    rv['Rdcol0']= posx
    rv['Rdcol1']= posy
    rv['ang']=np.arctan2(rv['Lidcol0'],rv['Lidcol1'])/np.pi+1
    rv['Lidcol0']+= posx
    rv['Lidcol1']+= posy
    rv['Lidsiz']=0.6
    rv['Rstri']= straal
    rv['inraad']= rv['Liddst'] < straal
    rvx=rv[rv['inraad']==False].sort_values("Liddst").head()
    #print(rvx)
    rv=rv[rv['inraad']].copy()
    rv=pd.concat([rv,rvx])
    plevs=(np.random.rand (nparty) +0.1).cumsum()
    plevs=2*plevs/plevs[-1]
    #print(plevs)
    #rv['party'] = (np.random.rand (len(rv))*nparty).astype(int)
    rv['party'] = (np.digitize(rv['ang'],plevs).astype(str) )
    return rv

allraad=pd.concat([mkraad(ridf,i+1,rsizes[i],0,i*2*maxraadsqrt+maxraadsqrt) for i in range(0,3) ])
allraad


# -

def mkcollege(rd):
    ptot= allraad.groupby(['Rdidx','party'])["inraad"].agg("count").reset_index()
#    ptot= ptot.sort_values("inraad").groupby(['Rdidx']).last(2)
    rtot= allraad.groupby(['Rdidx'])["inraad"].agg("count").reset_index().rename(columns={"inraad": "raadsgrootte"})
    rinfo= allraad.groupby(['Rdidx','party'])["Rdcol0","Rdcol1","Lidcol0","Lidcol1","Lidsiz","Rstri"].agg("mean").reset_index()
    grpart= ptot.groupby(['Rdidx'])["inraad"].agg("max").reset_index().rename(columns={"inraad": "maxpart"})
    klpart= ptot.groupby(['Rdidx'])["inraad"].agg("min").reset_index().rename(columns={"inraad": "minpart"})
    colle=ptot.merge(rtot,how='left').merge(rinfo,how='left').merge(grpart,how='left').merge(klpart,how='left')
    colle['Colsel']= (colle['maxpart']==colle['inraad'] ) | \
       ( (colle['maxpart'] -1 < colle['raadsgrootte'] /2  ) & ( colle['minpart']!=colle['inraad'] ))
    colle['raadsleden'] =colle['inraad'] 
    colle['Lidsiz'] =2-((colle['maxpart']< colle['raadsgrootte'] /2  ) .astype(int)  )
    #colle['Lidsiz'] *=2
    colle['Lidcol0'] +=8
    colle['Lidcol1'] +=2
    colle['Rdcol0'] +=8
    colle['Rdcol1'] +=2
    colle['Rstri'] *=0.5
    collsel=colle[colle['Colsel']]
    return collsel
allcoll=mkcollege(allraad)
allcoll

regiotot1= allraad.groupby(['party'])["inraad"].agg("count").reset_index()
regiotot2= allcoll.groupby(['party'])["inraad"].agg("sum").reset_index().rename(columns={"inraad":"incollege"})
regiotot=regiotot1.merge(regiotot2).drop(columns="party")
str(regiotot)


# +
def plotrd(raad,colle,regiostats):    
    fig, ax = plt.subplots(figsize=(6, 4))
    rd= pd.concat([raad,colle])
#    sns.scatterplot(x="Rdcol0", y="Rdcol1", hue="Rdidx", size="Rstri",  alpha=.1,  data=rd,ax=ax)
    sns.scatterplot(x="Lidcol0", y="Lidcol1", hue="party", size="Lidsiz",  alpha=.8, palette="muted", data=rd,ax=ax)
#    sns.scatterplot(x="Rdcol0", y="Rdcol1", hue="Rdidx", size="Rstri",  alpha=.1,  data=colle,ax=ax)
#    sns.scatterplot(x="Lidcol0", y="Lidcol1", hue="party", size="Lidsiz",  alpha=.8, palette="muted", data=colle,ax=ax)
    (abx,aby)=(16,14)
    (dbx,dby)=(22,14)
    repcol='grey'
    for index, row in colle.iterrows(): 
        (cx,cy)=(row['Rdcol0'] , row['Rdcol1'] )
        ax.annotate("",xy=(cx-8,cy-2),xytext=(cx-2, cy-1), 
                    arrowprops=dict(arrowstyle="<-",color=repcol))
        ax.annotate("",xytext=(abx-1,aby),xy=(cx+2, cy), 
                    arrowprops=dict(arrowstyle="<-",color=repcol))
        ax.annotate("%s"%(row['Rdidx']),xy=(cx-8,cy+2),
                   horizontalalignment='right',
                   verticalalignment='top',alpha=0.5)
#        ax.annotate("AB lid %s"%(row['Rdidx']),xy=(cx+3,cy),
#                   horizontalalignment='left',
#                   verticalalignment='bottom',alpha=0.5)
        ax.annotate("",xy=(cx-8,cy-2),xytext=(abx, aby), 
                    arrowprops=dict(arrowstyle="<-",color='green'))
        radius = row["Rstri"]*8+20
        ax.plot(cx-8,cy-2, 'o',
            ms=radius , mec='yellow', mfc='none')
        radius = row["Rstri"]*4+20
        ax.plot(cx,cy, 'o',
            ms=radius , mec='yellow', mfc='none')
    ax.annotate("Gemeenteraad",xy=(0,2),
                   horizontalalignment='center',
                   verticalalignment='center',alpha=0.5)
    ax.annotate("College",xy=(8,2),
                   horizontalalignment='center',
                   verticalalignment='center',alpha=0.5)
    ax.annotate("AB GR",xy=(abx,2),
                   horizontalalignment='center',
                   verticalalignment='center',alpha=0.5)
    ax.annotate("DB GR",xy=(dbx,2),
                   horizontalalignment='center',
                   verticalalignment='center',alpha=0.5)
    ax.annotate("",xytext=(dbx,dby),xy=(abx, aby), 
                    arrowprops=dict(arrowstyle="<-",color=repcol))
    ax.annotate("Regio totaal\n"+str(regiostats),xy=(dbx-3,30),
                   horizontalalignment='left',
                   verticalalignment='top',alpha=0.5)
    radius = 20
    ax.plot(abx,aby, 'o',
            ms=radius , mec='yellow', mfc='none')
    radius = 10
    ax.plot(dbx,dby, 'o',
            ms=radius , mec='yellow', mfc='none')
    ax.set_aspect(1.0)
    ax.set_ylim(bottom=0,top=32)
    ax.set_xlim(right=35)
    ax.set_ylabel("Deelnemende gemeente")
    ax.set_xlabel("Vertegenwoordingingslaag")
    if 1==1:
        plt.tick_params(
        axis='both',          # changes apply to both axes
        which='both',      # both major and minor ticks are affected
        bottom=False,      # ticks along the bottom edge are off
        top=False,         # ticks along the top edge are off
        labelleft=False,    
        labelbottom=False) # labels along the bottom edge are off
        #ax.get_legend().remove()        
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    else:
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    savtag="01"
    figname = "../output/example_cvp_"+savtag+"_"+'m1.svg';
    plt.savefig(figname, bbox_inches="tight")

plotrd(allraad,allcoll,regiotot)      
# -



# +
#let op: lijkt deels spitsstrook RWS01_MONIBAS_0270vwa0678ra	a27	678	r	af
#67.5 = zoutopslag na oprit 28 , 69.1 = Euretco, r = richting noord (Euretco vanaf afslag 28)

some_string="""ID	xax	tax	altnr	wie	wat
L10	0	0		DB-GR	stuk voor zienswijze
L20	2	1		COLL-GEM	concept zienswijze 
L30	2	2		COLL-GEM	vaststellen concept zienswijze 
L40	4	3		CVPX-GEM	amendementen zienswijze 
L50	5	4		RPF	zienswijzes en amendementen vergelijken
L60	4	5		CVP	consolideren RPF
L70	3	6		RTG-GEM	doorspreken zienswijzes RTG
L80	3	8		RAAD-GEM	zienswijze aangenomen raad
L90	0	12		DB-GR	deadline zienswijze
L40	4	-1	L40	CVPX-GEM	kern beoordeelpunten
L42	6	2.5	L50	RR-OVGEM	amendementen zienswijzes
L72	6	10	L90	RR-OVGEM	zienswijzes"""
#read CSV string into pandas DataFrame
termijnendb= pd.read_csv(io.StringIO(some_string), sep="\t")
termijnendb


# +
def plotterm(termdb):    
    fig, ax = plt.subplots(figsize=(6, 4))
    rd= termdb
#    sns.scatterplot(x="Rdcol0", y="Rdcol1", hue="Rdidx", size="Rstri",  alpha=.1,  data=rd,ax=ax)
    sns.scatterplot(data=rd,x="xax", y="tax",ax=ax)
#    sns.scatterplot(x="Rdcol0", y="Rdcol1", hue="Rdidx", size="Rstri",  alpha=.1,  data=colle,ax=ax)
#    sns.scatterplot(x="Lidcol0", y="Lidcol1", hue="party", size="Lidsiz",  alpha=.8, palette="muted", data=colle,ax=ax)
    (px,py)=(0,0)
    opos=dict()
    repcol='grey'
    for index, row in rd.iterrows(): 
        #print(row)
        (cx,cy)=(row['xax'] , row['tax'] )
        if pd.isna(row['altnr'] ):
            ax.annotate("",xy=(px,py),xytext=(cx, cy), 
                    arrowprops=dict(arrowstyle="<-",color=repcol))
        else:
            (lx,ly)=(opos["X"+row['altnr']],opos["Y"+row['altnr']])
            ax.annotate("",xy=(cx,cy),xytext=(lx, ly), 
                    arrowprops=dict(arrowstyle="<-",color=repcol))          
        if 1==1:
            ax.text(cx+0.5,cy,row['wat'], ha='left', va='center',alpha=0.5,size =6,
                    bbox=dict(boxstyle="Square,pad=0.3",
                      fc="yellow", ec="yellow", lw=2) )
            ax.text(cx-0.5,cy,row['wie'], ha='right', va='center',alpha=0.8,size =6,
                   bbox=dict(boxstyle="Square,pad=0.3",
                      fc="lightblue", ec="steelblue", lw=2))
        (opos["X"+row['ID']],opos["Y"+row['ID']])=(cx,cy)
        (px,py)=(cx,cy)
    #ax.set_aspect(0.5)
    #ax.set_ylim(bottom=0,top=12)
    ax.set_ylim(bottom=13,top=-2)
    ax.set_xlim(left=-2,right=12)
    ax.set_ylabel("Tijd (weken)")
    ax.set_xlabel("actiehouder")
    if 1==1:
        plt.tick_params(
        axis='both',          # changes apply to both axes
        which='both',      # both major and minor ticks are affected
        bottom=False,      # ticks along the bottom edge are off
        top=False,         # ticks along the top edge are off
#        labelleft=False,    
        labelbottom=False) # labels along the bottom edge are off
        #ax.get_legend().remove()        
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    else:
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    savtag="01"
    figname = "../output/termijn_cvp_"+savtag+"_"+'m1.svg';
    plt.savefig(figname, bbox_inches="tight")

plotterm(termijnendb)   
# -


