const $ = (id) => document.getElementById(id);
const modules = {
  equipos: { title: 'Equipos', source: 'MongoDB', fields: [['codigo','Codigo FIFA','text',''],['limite','Limite','number','25']], path: v => v.codigo ? `/api/v1/equipos/${encodeURIComponent(v.codigo)}` : '/api/v1/equipos', params: v => v.codigo ? {} : {limite:v.limite}, next:'siguiente_codigo', param:'despues' },
  eventos: { title: 'Explorador del grafo', source: 'Neo4j', fields: [], path:()=>'/api/v1/grafo', params:()=>({}) },
  comentarios: { title:'Comentarios',source:'Cassandra',fields:[['partido','Partido','text','P001'],['bucket_10m','Bloque de 10 minutos (UTC)','datetime-local','2030-06-10T18:00'],['shard','Shard','number','0'],['limite','Limite','number','7']],path:v=>`/api/v1/partidos/${encodeURIComponent(v.partido)}/comentarios`,params:v=>({bucket_10m:v.bucket_10m+':00Z',shard:v.shard,limite:v.limite}),next:'siguiente_cursor',param:'cursor'},
  sesiones: {title:'Sesiones',source:'Redis',fields:[['session','Sesion','text','sess-demo-001']],path:v=>`/api/v1/sesiones/${encodeURIComponent(v.session)}`,params:()=>({})},
  estadisticas: {title:'Estadisticas',source:'InfluxDB',fields:[['partido','Partido','text','P001'],['desde','Desde (UTC)','datetime-local','2030-06-08T19:00'],['hasta','Hasta (UTC)','datetime-local','2030-06-08T20:30'],['equipo','Equipo','text','AAA'],['resolucion','Resolucion','select','5m']],path:v=>`/api/v1/partidos/${encodeURIComponent(v.partido)}/estadisticas`,params:v=>({desde:v.desde+':00Z',hasta:v.hasta+':00Z',resolucion:v.resolucion,...(v.equipo?{equipo:v.equipo}:{})})},
  objetos: {title:'Objetos',source:'IRIS',fields:[['partido','Partido','text','P001'],['limite_eventos','Limite de eventos','number','50']],path:v=>`/api/v1/objetos/partidos/${encodeURIComponent(v.partido)}`,params:v=>({limite_eventos:v.limite_eventos})}
};
let active='equipos', controller=null, sequence=0, lastQuery=null, nextValue=null, dispose=()=>{}, loaded=null;
const sources=['mongodb','neo4j','cassandra','redis','influxdb','iris'];
const labels=['MongoDB','Neo4j','Cassandra','Redis','InfluxDB','IRIS'];
function healthCards(data){
  $('health').replaceChildren(...sources.map((name,i)=>{
    const item=document.createElement('div'); const state=data?.[name];
    item.className='health-item '+(state?(state.estado==='ok'?'ok':'bad'):'');
    const title=document.createElement('strong'); title.textContent=labels[i];
    const small=document.createElement('small'); const dot=document.createElement('span'); dot.className='dot';
    small.append(dot, document.createTextNode(state?(state.estado==='ok'?'Disponible':'No disponible'):'Comprobando...'));
    item.append(title,small); return item;
  }));
}
async function health(){
  $('health-refresh').disabled=true;
  try { const r=await fetch('/api/v1/salud',{signal:AbortSignal.timeout(45000)}); const body=await r.json(); if(!body.data?.dependencias) throw Error(); healthCards(body.data.dependencias); }
  catch { healthCards(Object.fromEntries(sources.map(s=>[s,{estado:'error'}]))); }
  finally{$('health-refresh').disabled=false;}
}
function activate(key){
  dispose(); dispose=()=>{};
  sequence++; controller?.abort(); active=key; nextValue=null;lastQuery=null;
  loaded=null;
  const m=modules[key]; $('module-title').textContent=m.title; $('source').textContent=m.source;
  for(const button of $('tabs').children)button.setAttribute('aria-selected',String(button.dataset.key===key));
  $('fields').replaceChildren(...m.fields.map(([name,label,type,value])=>{
    const wrapper=document.createElement('label'); wrapper.textContent=label;
    const input=document.createElement(type==='select'?'select':'input'); input.name=name;
    if(type==='select')for(const v of ['1m','5m','15m','1h']){const opt=document.createElement('option');opt.value=v;opt.textContent=v;input.append(opt);}
    else input.type=type;
    input.value=name==='limite'?'100':name==='equipo'?'':value; input.required=!['codigo','equipo'].includes(name);
    if(type==='number'){input.min=name==='shard'?'0':'1';input.max=name==='shard'?'7':'100';}
    wrapper.append(input);return wrapper;
  }));
  $('error').hidden=true;$('next').hidden=true;$('submit').disabled=false;$('submit').textContent='Consultar';
  $('result-state').textContent='Sin consultar';$('timing').textContent='';$('json').textContent='{}';
  $('endpoint').textContent='';$('request-id').textContent='';$('results').replaceChildren();
  const empty=document.createElement('p');empty.className='empty';empty.textContent='Sin resultados.';$('results').append(empty);
}
function table(data){
  const array=Array.isArray(data.items)?data.items:Array.isArray(data.eventos)?data.eventos:null;
  const rows=array??Object.entries(data).map(([campo,valor])=>({campo,valor}));
  $('results').replaceChildren();
  if(array){const meta=document.createElement('p');meta.className='source';meta.textContent=`${rows.length} registros${data.truncado||data.eventos_truncados?' · Resultado limitado':''}`;$('results').append(meta);}
  if(!rows.length){const p=document.createElement('p');p.className='empty';p.textContent='No hay registros para esta consulta.';$('results').append(p);return;}
  const columns=[...new Set(rows.flatMap(row=>Object.keys(row)))];
  const t=document.createElement('table'), head=document.createElement('thead'), hr=document.createElement('tr'),body=document.createElement('tbody');
  columns.forEach(key=>{const th=document.createElement('th');th.scope='col';th.textContent=key.replaceAll('_',' ');hr.append(th);});head.append(hr);
  for(const row of rows){const tr=document.createElement('tr');for(const key of columns){const td=document.createElement('td');const value=row[key];td.textContent=value==null?'—':typeof value==='object'?JSON.stringify(value):String(value);tr.append(td);}body.append(tr);}
  t.append(head,body);$('results').append(t);
}
async function query(next=false){
  const m=modules[active]; const values=Object.fromEntries(new FormData($('query-form')));
  const current=next&&lastQuery?{path:lastQuery.path,params:{...lastQuery.params,[m.param]:nextValue}}:{path:m.path(values),params:m.params(values)};
  controller?.abort();controller=new AbortController();const own=++sequence;
  const requestController=controller;
  const timeout=setTimeout(()=>requestController.abort(),45000);
  dispose(); dispose=()=>{};
  $('submit').disabled=true;$('next').hidden=true;$('error').hidden=true;$('submit').textContent='Consultando...';
  $('results').replaceChildren();$('result-state').textContent='Consultando';$('json').textContent='{}';$('timing').textContent='';$('request-id').textContent='';
  const url=current.path+'?'+new URLSearchParams(current.params);$('endpoint').textContent='GET '+url;
  const start=performance.now();
  try{
    const r=await fetch(url,{signal:controller.signal}); const body=await r.json();if(own!==sequence)return;
    $('json').textContent=JSON.stringify(body,null,2);$('result-state').textContent=`HTTP ${r.status}`;
    $('timing').textContent=`${Math.round(performance.now()-start)} ms`;$('request-id').textContent='Request ID: '+(r.headers.get('X-Request-ID')||'—');
    if(!r.ok){$('error').textContent=(body.error?.message||'No se pudo completar la consulta.')+(body.error?.fields?.length?' '+body.error.fields.join(', '):'');$('error').hidden=false;return;}
    if(next&&loaded?.items&&body.data.items)body.data.items=[...loaded.items,...body.data.items];
    loaded=body.data;
    dispose=active==='eventos'?GraphExplorer($('results'),body.data):DataExplorer(active,$('results'),body.data);lastQuery=current;nextValue=m.next?body.data[m.next]:null;$('next').hidden=nextValue==null;
    $('next').textContent='Cargar mas';
  }catch(e){if(own!==sequence)return;$('result-state').textContent='Sin respuesta';$('error').textContent=e.name==='AbortError'?'La consulta supero el tiempo de espera.':'No se pudo conectar con la API.';$('error').hidden=false;}
  finally{clearTimeout(timeout);if(own===sequence){$('submit').disabled=false;$('submit').textContent='Consultar';}}
}
for(const [key,m] of Object.entries(modules)){const b=document.createElement('button');b.type='button';b.role='tab';b.dataset.key=key;b.textContent=m.source;b.onclick=()=>{activate(key);query();};$('tabs').append(b);}
$('query-form').onsubmit=e=>{e.preventDefault();query();};$('next').onclick=()=>query(true);$('health-refresh').onclick=health;
healthCards();activate('eventos');health();query();
