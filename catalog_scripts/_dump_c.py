# -*- coding: utf-8 -*-
import io,json,os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d=json.load(io.open(os.path.join(ROOT,'catalog_scripts','_out','room_data.json'),encoding='utf-8'))
for k in sys.argv[1:]:
    print('=== %s (%d) ==='%(k,len(d[k])))
    for e in d[k]:
        o={kk:vv for kk,vv in e.items() if kk!='label'}
        lab=e.get('label','')
        print(json.dumps(o,ensure_ascii=False)+'  |LBL80| '+lab[:90].replace('\n',' '))
