import xlrd, openpyxl, json, collections, unicodedata, re
def norm(s): return re.sub(r'[^a-z]','',unicodedata.normalize('NFKD',str(s).lower()).encode('ascii','ignore').decode())
def rows(y):
    if y==2024:
        ws=openpyxl.load_workbook('years/2024.xlsx',read_only=True,data_only=True)
        ws=ws[ws.sheetnames[-1]]; return [list(r) for r in ws.iter_rows(values_only=True)]
    b=xlrd.open_workbook(f'years/{y}.xls'); s=b.sheet_by_index(b.nsheets-1)
    return [s.row_values(r) for r in range(s.nrows)]
def f(x):
    try: return float(x)
    except: return 0.0
ING=[('impuestos_directos','impuestosdirectos'),('impuestos_indirectos','impuestosindirectos'),('tasas_otros','tasas'),('transf_corrientes','transferenciascorrientes'),('patrimoniales','ingresospatrimoniales'),('enajenacion','enajenacion'),('transf_capital','transferenciasdecapital'),('activos_fin','activosfinancieros'),('pasivos_fin','pasivosfinancieros')]
GAS=[('personal','gastosdepersonal'),('bienes_servicios','bienes'),('financieros','gastosfinancieros'),('transf_corrientes','transferenciascorrientes'),('contingencia','fondodecontingencia'),('inversiones','inversionesreales'),('transf_capital','transferenciasdecapital'),('activos_fin','activosfinancieros'),('pasivos_fin','pasivosfinancieros')]
AREAS_NEW=[('deuda','deudapublica'),('servicios_basicos','serviciospublicosbasicos'),('proteccion_social','actuacionesdeproteccion'),('bienes_preferentes','produccionde'),('economico','actuacionesdecaracter'),('general','actuacionesdecaracter')]
out={}
for y in range(2005,2025):
    R=rows(y)
    hi=next(i for i,r in enumerate(R[:12]) if any(str(c).strip().startswith('Nombre') for c in r))
    h=[norm(c) for c in R[hi]]
    raw=[str(c).strip() for c in R[hi]]
    row=next(r for r in R[hi+1:] if str(r[0]).strip() and str(r[1]).strip() and re.match(r'^\d+(\.0)?$',str(r[0]).strip()) and int(float(r[0]))==37 and int(float(r[1]))==274 and str(r[2]).startswith('A'))
    # split into blocks by 'total'
    tot=[i for i,c in enumerate(h) if c.startswith('total')]
    ti,tg,tg2=tot[0],tot[1],(tot[2] if len(tot)>2 else None)
    def pick(lo,hi_,key,occ=0):
        idx=[i for i in range(lo,hi_) if key in h[i]]
        return f(row[idx[occ]]) if idx else 0.0
    d={'poblacion':f(row[4]),'ingresos':{k:pick(6,ti,key) for k,key in ING},'gastos':{k:pick(ti+1,tg,key) for k,key in GAS}}
    d['total_ingresos']=f(row[ti]); d['total_gastos']=f(row[tg])
    if y>=2010:
        a={}
        lo=tg+1
        a['deuda']=f(row[lo]); a['servicios_basicos']=f(row[lo+1]); a['proteccion_social']=f(row[lo+2]); a['bienes_preferentes']=f(row[lo+3]); a['economico']=f(row[lo+4]); a['general']=f(row[lo+5])
        assert norm(R[hi][lo]).startswith('deuda') and norm(R[hi][lo+1]).startswith('servicios'), (y,R[hi][lo:lo+2])
        d['areas']=a
        assert abs(sum(a.values())-d['total_gastos'])<5,(y,sum(a.values()),d['total_gastos'])
    assert abs(sum(d['ingresos'].values())-d['total_ingresos'])<5,(y,'ing')
    assert abs(sum(d['gastos'].values())-d['total_gastos'])<5,(y,'gas',sum(d['gastos'].values()),d['total_gastos'])
    out[y]=d
    print(y,round(d['total_ingresos']/1e6,1),round(d['total_gastos']/1e6,1),int(d['poblacion']))
ipc={}
by=collections.defaultdict(list)
for x in json.load(open('ipc.json',encoding='utf8'))['Data']: by[x['Anyo']].append(x['Valor'])
ipc={y:round(sum(v)/len(v),3) for y,v in by.items()}
js={'fuente':'Ministerio de Hacienda, CONPREL: liquidaciones de presupuestos de entidades locales (presupuesto consolidado del Ayuntamiento de Salamanca, derechos y obligaciones reconocidas netas). IPC: INE, índice general nacional, media anual.','unidad':'euros','ipc_base2021':ipc,'anios':{str(k):v for k,v in out.items()}}
json.dump(js,open('presupuestos-salamanca.json','w',encoding='utf8'),ensure_ascii=False,separators=(',',':'))
