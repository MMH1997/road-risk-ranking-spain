import pandas as pd, numpy as np, geopandas as gpd, json
from shapely.geometry import Point, box
from shapely import affinity
import argparse
ap=argparse.ArgumentParser(description='Build atlas/src/data.json from the analysis tables, the province boundaries and the municipality table.')
ap.add_argument('--tables',required=True,help='dgt_tables.xlsx written by the notebook (outputs/tables/dgt_tables.xlsx)')
ap.add_argument('--provinces',required=True,help='INE/CNIG province boundaries (gpkg/geojson) with a COD_PROVINCIA column (INE code 1..52)')
ap.add_argument('--municipalities',required=True,help='pickle with columns name, pop, prov, x, y (ETRS89 / UTM 30N), see atlas/prep/README.md')
ap.add_argument('--out',default='atlas/src/data.json')
A=ap.parse_args(); F=A.tables
X=lambda s: pd.read_excel(F,sheet_name=s)
rd=X('risk_decomposition'); L=X('bayes_province_L'); Fm=X('bayes_province_F'); R=X('bayes_province_R')
eb=X('provinces_eb'); ebi=X('provinces_eb_interurban'); fa=X('funnel_all'); fi=X('funnel_interurban'); fu=X('funnel_urban')
ex=X('exposure'); gi=X('gi_cells')

# ---------- geometry ----------
p=gpd.read_file(A.provinces); p=p.dissolve(by='COD_PROVINCIA',as_index=False)
INS={'35':32628,'38':32628,'51':25830,'52':25830}
main=p[~p.COD_PROVINCIA.isin([35,38,51,52])].to_crs(25830)
main['geometry']=main.geometry.simplify(1500,preserve_topology=True)
x0,y0,x1,y1=main.total_bounds
S=1000.0  # metres per SVG unit
MARG=12
def to_svg(geom,ox,oy,k=1.0,x_ref=0,y_ref=0):
    """project to svg units: ((x-x_ref)*k+ox)/S , (oy-(y-y_ref)*k)/S"""
    return geom
def path(geom,tx):
    polys=[geom] if geom.geom_type=='Polygon' else list(geom.geoms)
    out=[]
    for pg in polys:
        for ring in [pg.exterior]+list(pg.interiors):
            c=[tx(x,y) for x,y in ring.coords]
            out.append('M'+'L'.join(f'{a:.1f} {b:.1f}' for a,b in c)+'Z')
    return ''.join(out)
W=(x1-x0)/S+2*MARG
H_main=(y1-y0)/S+2*MARG
INSET_H=165   # extra height for the insets row
H=H_main+INSET_H
tx_main=lambda x,y:((x-x0)/S+MARG,(y1-y)/S+MARG)
paths={}
for _,r in main.iterrows(): paths[int(r.COD_PROVINCIA)]=path(r.geometry,tx_main)
# insets (lower-left row), each as (cods, crs, scale, frame box in svg units, label)
def inset(cods,crs,k,fx,fy,fw,fh,label,simp):
    sub=p[p.COD_PROVINCIA.isin(cods)].to_crs(crs).copy()
    sub['geometry']=sub.geometry.simplify(simp,preserve_topology=True)
    a0,b0,a1,b1=sub.total_bounds
    cx=(a0+a1)/2; cy=(b0+b1)/2
    tx=lambda x,y:(fx+fw/2+(x-cx)*k/S, fy+fh/2-(y-cy)*k/S)
    for _,r in sub.iterrows(): paths[int(r.COD_PROVINCIA)]=path(r.geometry,tx)
    w=(a1-a0)*k/S; h=(b1-b0)*k/S
    return dict(x=fx,y=fy,w=fw,h=fh,label=label,k=k,fits=(w<=fw and h<=fh),w_=w,h_=h)
fy=H_main+6
frames=[]
canarias=inset([35,38],32628,0.62,MARG,fy,330,INSET_H-40,'Canarias (reduced)',1500); frames.append(canarias)
ceuta=inset([51],25830,9.0,MARG+345,fy,95,INSET_H-40,'Ceuta ×9',60); frames.append(ceuta)
melilla=inset([52],25830,9.0,MARG+455,fy,95,INSET_H-40,'Melilla ×9',60); frames.append(melilla)
print([ (f['label'],round(f['w_']),round(f['h_']),f['fits']) for f in frames])

# hot cells (corner = cx*10km, cy*10km) in main projection
# per province: hot cells & analysed cells via centre in polygon (full-res main)
pc=p[~p.COD_PROVINCIA.isin([35,38])].to_crs(25830)
def prov_of(x,y):
    q=Point(x,y)
    for _,r in pc.iterrows():
        if r.geometry.contains(q): return int(r.COD_PROVINCIA)
    return None
from shapely.strtree import STRtree
geoms=list(pc.geometry); codes=list(pc.COD_PROVINCIA.astype(int)); tree=STRtree(geoms)
def prov_fast(x,y):
    q=Point(x,y)
    for i in tree.query(q,predicate='within'): return codes[i]
    d=[(geoms[i].distance(q),codes[i]) for i in tree.query(q.buffer(8000))]
    return min(d)[1] if d else None
gi['prov']=[prov_fast(cx*10000+5000,cy*10000+5000) for cx,cy in zip(gi.cx,gi.cy)]
cellcnt=gi.groupby('prov').size().to_dict(); hotcnt=gi[gi['class']=='hot'].groupby('prov').size().to_dict()
print('unassigned',gi.prov.isna().sum())
cl=[]
for _,r in gi.iterrows():
    xx,yy=tx_main(r.cx*10000,(r.cy+1)*10000)
    cl.append([round(xx,1),round(yy,1),int(r.crashes),int(r.fatal),int(r.road_km),round(float(r.eb),6),round(float(r.z),2),round(float(r.p_fdr),4),1 if r['class']=='hot' else 0,0 if pd.isna(r.prov) else int(r.prov),int(r.cx),int(r.cy)])
print('cells',len(cl),'hot',sum(c[8] for c in cl))


# ---------- nearby municipalities (open INE/CNIG-based database, population 1 Jan 2021, municipal centroids) ----------
from scipy.spatial import cKDTree
mm=pd.read_pickle(A.municipalities); kd=cKDTree(mm[['x','y']].values)
cen=np.c_[gi.cx.values*10000+5000, gi.cy.values*10000+5000]
dd,ii=kd.query(cen,k=3)
used={}; cn=[]
def ix(j):
    if j not in used: used[j]=len(used)
    return used[j]
for n,(c0,c1) in enumerate(cen):
    near=kd.query_ball_point([c0,c1],20000)
    pop20=int(mm['pop'].values[near].sum()) if near else 0
    big=-1;dbig=-1
    if near:
        b=max(near,key=lambda j:mm['pop'].values[j]); big=ix(b); dbig=round(float(np.hypot(mm.x.values[b]-c0,mm.y.values[b]-c1))/1000,1)
    row=[]
    for k in range(3):
        row+= [ix(int(ii[n,k])), round(float(dd[n,k])/1000,1)]
    cn.append(row+[pop20,big,dbig])
inv=sorted(used,key=lambda j:used[j])
munl=[[mm.name.values[j],int(mm['pop'].values[j]),int(mm.prov.values[j])] for j in inv]
print('municipalities used',len(munl),'cells',len(cn))

# ---------- data ----------
nat_rate=rd.deaths.sum()/rd.person_years.sum()*1e6
pooled_share=rd.fatal.sum()/rd.crashes.sum()
nat=dict(crashes=int(rd.crashes.sum()),fatal=int(rd.fatal.sum()),deaths=int(rd.deaths.sum()),py=float(rd.person_years.sum()),rate=float(nat_rate),
         share=float(pooled_share),pop25=float(ex[ex.ANYO==2025].POP.sum()),pop22=float(ex[ex.ANYO==2022].POP.sum()),
         cells=int(len(gi)),hot=int((gi['class']=='hot').sum()),
         f1=float(rd.crashes.sum()/rd.person_years.sum()),f2=float(pooled_share),f3=float(rd.deaths.sum()/rd.fatal.sum()))
def eff(d,c):
    r=d[d.COD_PROVINCIA==c].iloc[0]
    return dict(rr=r['RR'],lo=r['lo'],hi=r['hi'],p=r['P_RR>1'],rk=r['rank_median'],rklo=r['rank_lo'],rkhi=r['rank_hi'],t10=r['P_top10'])
def ebrow(d,c):
    r=d[d.COD_PROVINCIA==c].iloc[0]; return dict(raw=r['raw'],eb=r['eb'],lo=r['eb_lo'],hi=r['eb_hi'],n=int(r['n']),x=int(r['x']))
def z(d,c):
    r=d[d.COD_PROVINCIA==c]; return None if r.empty else float(r.z.iloc[0])
provs=[]
for _,r in rd.iterrows():
    c=int(r.COD_PROVINCIA)
    e=ex[ex.COD_PROVINCIA==c].set_index('ANYO').POP
    row=dict(c=c,n=r.province,pop22=float(e[2022]),pop25=float(e[2025]),crashes=int(r.crashes),fatal=int(r.fatal),deaths=int(r.deaths),py=float(r.person_years),
             rate=float(r.rate_pm),rlo=float(r.lo),rhi=float(r.hi),fs=float(r.fatal/r.crashes),
             f1=float(r.f1),f2=float(r.f2),f3=float(r.f3),cf=float(r.c_freq),cs=float(r.c_sev),cm=float(r.c_mult),ct=float(r.c_tot),
             L=eff(L,c),F=eff(Fm,c),R=eff(R,c),eb=ebrow(eb,c),ebi=ebrow(ebi,c),
             z=dict(a=z(fa,c),i=z(fi,c),u=z(fu,c)),hot=int(hotcnt.get(c,0)),cells=int(cellcnt.get(c,0)))
    provs.append(row)
def clean(o):
    if isinstance(o,dict): return {k:clean(v) for k,v in o.items()}
    if isinstance(o,list): return [clean(v) for v in o]
    if isinstance(o,(np.floating,float)): return None if (o!=o) else round(float(o),5)
    if isinstance(o,(np.integer,)): return int(o)
    return o
out=dict(org=[round(float(x0)/1000,3),round(float(y1)/1000,3)],marg=MARG,mh=round(float(H_main),1),vb=[round(float(W),1),round(float(H),1)],paths={str(k):v for k,v in paths.items()},frames=[{k:(round(v,1) if isinstance(v,float) else v) for k,v in f.items() if k in('x','y','w','h','label')} for f in frames],
         cl=cl,cn=cn,mun=munl,nat=clean(nat),provs=clean(provs))
json.dump(out,open(A.out,'w'),separators=(',',':'),ensure_ascii=False)
import os; print(os.path.getsize(A.out)/1024,'KB', 'viewBox',out['vb'])
