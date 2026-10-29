const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const enginePath = path.join(__dirname, '../static/js/world-time-calculations.js');
const api = fs.existsSync(enginePath) ? require(enginePath) : {};
const input = (date='2027-01-01', time='00:00', sourceOffsetMinutes=0) => ({date,time,sourceOffsetMinutes});
const zones = ['UTC','Asia/Seoul','Asia/Tokyo','Asia/Shanghai','Asia/Kolkata','Europe/London','America/New_York'];
function calculate(value, dependency) { assert.equal(typeof api.calculate, 'function', 'world time engine must expose calculate'); return api.calculate(value, dependency); }
test('single instant produces ordered cities and previous-day New York', () => {
 const result = calculate(input());
 assert.equal(result.ok, true);
 assert.equal(result.instant,'2027-01-01T00:00:00Z');
 assert.deepEqual(result.rows.map(row=>row.zone),zones);
 assert.deepEqual(result.rows[6],{zone:zones[6],status:'ok',date:'2026-12-31',time:'19:00',offsetMinutes:-300,weekday:4,dayDelta:-1});
 assert.equal(result.rows[4].time,'05:30');
 assert.equal(result.seoulMismatch,false);
});
for (const date of ['',null,20270101,'2027-1-01','2027-02-29','2024-02-30','2027-04-31','2019-12-31','2031-01-01',' 2027-01-01']) test(`invalid date ${date}`,()=>assert.deepEqual(calculate(input(date)),{ok:false,field:'date',code:'invalid_date'}));
for (const time of ['',null,1200,'24:00','23:60','9:00','12:00:00',' 12:00']) test(`invalid time ${time}`,()=>assert.deepEqual(calculate(input('2027-01-01',time)),{ok:false,field:'time',code:'invalid_time'}));
for (const offset of [undefined,null,'0','540',60,-540,NaN,{},true]) test(`invalid offset ${String(offset)}`,()=>assert.deepEqual(calculate({...input(),sourceOffsetMinutes:offset}),{ok:false,field:'sourceOffsetMinutes',code:'invalid_source'}));
test('fixed offset input allows previous-year output and computes delta against source civil date',()=> {
 const result=calculate(input('2020-01-01','00:00',540));
 assert.equal(result.instant,'2019-12-31T15:00:00Z');
 assert.equal(result.rows[0].dayDelta,-1);
 assert.equal(result.rows[1].dayDelta,0);
 assert.equal(result.rows[1].date,'2020-01-01');
});
test('end of input range allows next-year city dates',()=>assert.equal(calculate(input('2030-12-31','23:59')).rows[1].date,'2031-01-01'));
test('UTC and fixed +9 produce identical instants and city clock values',()=>{
 const utc=calculate(input('2027-03-14','07:00',0));
 const fixed=calculate(input('2027-03-14','16:00',540));
 assert.equal(utc.instant,fixed.instant); assert.deepEqual(utc.rows,fixed.rows);
});
for (const dependency of [{DateTimeFormat:null},{DateTimeFormat:function Missing(){}}]) test('missing Intl or formatToParts is a global failure',()=>assert.deepEqual(calculate(input(),dependency),{ok:false,field:null,code:'unsupported_intl'}));
function formatter(transform, optionsTransform) {
 return class {
  constructor(locale,options) {
   assert.equal(options.calendar,'gregory'); assert.equal(options.numberingSystem,'latn'); assert.equal(options.hourCycle,'h23'); assert.equal('hour12' in options,false);
   this.options=options; this.base=new Intl.DateTimeFormat(locale,options);
  }
  resolvedOptions(){const value=this.base.resolvedOptions(); return optionsTransform ? optionsTransform(value,this.options.timeZone): value;}
  formatToParts(date){ return transform(this.base.formatToParts(date),this.options.timeZone,date); }
 };
}
test('unsupported city does not replace its data with a different time zone',()=>{
 const Format=formatter((parts,zone)=>{if(zone==='Europe/London')throw new RangeError('unsupported');return parts;});
 const result=calculate(input(),{DateTimeFormat:Format});
 assert.equal(result.ok,true); assert.deepEqual(result.rows[5],{zone:'Europe/London',status:'unsupported'}); assert.equal(result.rows[6].status,'ok');
});
for (const [name,transform] of [
 ['hour 24',parts=>parts.map(p=>p.type==='hour'?{...p,value:'24'}:p)],
 ['missing minute',parts=>parts.filter(p=>p.type!=='minute')],
 ['duplicate year',parts=>[...parts,{type:'year',value:'2027'}]],
 ['non-latin digit',parts=>parts.map(p=>p.type==='hour'?{...p,value:'٠١'}:p)],
 ['invalid calendar day',parts=>parts.map(p=>p.type==='day'?{...p,value:'32'}:p)]
]) test(`malformed parts ${name} hide all affected row numbers`,()=>{
 const Format=formatter((parts,zone)=>zone==='Asia/Tokyo'?transform(parts):parts);
 const result=calculate(input(),{DateTimeFormat:Format});
 assert.deepEqual(result.rows[2],{zone:'Asia/Tokyo',status:'unsupported'}); assert.equal(result.rows[1].status,'ok');
});
test('wrong resolved hour cycle is unsupported rather than normalized',()=>{
 const Format=formatter(parts=>parts,(value,zone)=>zone==='Asia/Tokyo'?{...value,hourCycle:'h24'}:value);
 assert.deepEqual(calculate(input(),{DateTimeFormat:Format}).rows[2],{zone:'Asia/Tokyo',status:'unsupported'});
});
test('changed Seoul city rules warn about fixed +09 input without rewriting the instant',()=>{
 const Format=formatter((parts,zone,date)=> zone==='Asia/Seoul' ? new Intl.DateTimeFormat('en-US',{timeZone:'UTC',calendar:'gregory',numberingSystem:'latn',hourCycle:'h23',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}).formatToParts(date):parts);
 const result=calculate(input('2027-01-01','09:00',540),{DateTimeFormat:Format});
 assert.equal(result.instant,'2027-01-01T00:00:00Z'); assert.equal(result.seoulMismatch,true); assert.equal(result.rows[1].offsetMinutes,0);
});
const fixture = require('./fixtures/world-time-2026f.json');
for (const item of fixture.cases) test(`IANA 2026f ${item.instant}`,()=>{
 const instant=new Date(item.instant);
 const utcDate=item.instant.slice(0,10);
 let source=input(utcDate,item.instant.slice(11,16),0);
 if (utcDate<'2020-01-01') {
  const civil=new Date(instant.getTime()+540*60000).toISOString();
  source=input(civil.slice(0,10),civil.slice(11,16),540);
 }
 const result=calculate(source);
 assert.equal(result.ok,true); assert.equal(result.instant,item.instant);
 for (const row of result.rows) {
  const expected=item.zones[row.zone];
  const dayDelta=(Date.parse(expected.date+'T00:00:00Z')-Date.parse(source.date+'T00:00:00Z'))/86400000;
  assert.deepEqual(row,{zone:row.zone,status:'ok',...expected,dayDelta});
 }
});
test('input remains unchanged and repeated calls do not retain state',()=>{
 const original=Object.freeze(input());const before=calculate(original);
 calculate(input('2027-01-01','24:00'));
 assert.deepEqual(calculate(original),before);
});
test('browser global export works without CommonJS, and missing browser Intl fails closed',()=>{
 const vm=require('node:vm');
 const context=vm.createContext({Intl:undefined});
 vm.runInContext(fs.readFileSync(enginePath,'utf8'),context);
 assert.equal(typeof context.WorldTimeCalculations.calculate,'function');
 assert.equal(JSON.stringify(context.WorldTimeCalculations.calculate(input())),JSON.stringify({ok:false,field:null,code:'unsupported_intl'}));
});
test('equivalent fixed +09 input preserves official values across every eligible fixture',()=>{
 for(const item of fixture.cases){
  const shifted=new Date(Date.parse(item.instant)+540*60000).toISOString();
  if(shifted.slice(0,10)>'2030-12-31')continue;
  const result=calculate(input(shifted.slice(0,10),shifted.slice(11,16),540));
  assert.equal(result.instant,item.instant);
  for(const row of result.rows){
   const {dayDelta,...clock}=row;
   assert.deepEqual(clock,{zone:row.zone,status:'ok',...item.zones[row.zone]});
   assert.equal(dayDelta,(Date.parse(row.date+'T00:00:00Z')-Date.parse(shifted.slice(0,10)+'T00:00:00Z'))/86400000);
  }
 }
});
test('ignored requested zone does not silently show UTC city values',()=>{
 class IgnoredZone extends Intl.DateTimeFormat {constructor(locale,options){super(locale,{...options,timeZone:'UTC'});}}
 const result=calculate(input(),{DateTimeFormat:IgnoredZone});
 assert.equal(result.rows[0].status,'ok');
 for(const row of result.rows.slice(1)) assert.deepEqual(row,{zone:row.zone,status:'unsupported'});
});
test('missing resolved zone suppresses every row',()=>{
 const Format=formatter(parts=>parts,({timeZone,...rest})=>rest);
 for(const row of calculate(input(),{DateTimeFormat:Format}).rows)assert.deepEqual(row,{zone:row.zone,status:'unsupported'});
});
for(const alias of ['UTC','Etc/UTC','Etc/UCT','UCT','Universal','Etc/Universal','Zulu','Etc/Zulu'])test(`official UTC alias ${alias} is accepted`,()=>{
 const Format=formatter(parts=>parts,(value,zone)=>zone==='UTC'?{...value,timeZone:alias}:value);
 assert.equal(calculate(input(),{DateTimeFormat:Format}).rows[0].status,'ok');
});
test('unlisted zero-offset zone is not treated as a UTC alias',()=>{
 const Format=formatter(parts=>parts,(value,zone)=>zone==='UTC'?{...value,timeZone:'Africa/Abidjan'}:value);
 assert.deepEqual(calculate(input(),{DateTimeFormat:Format}).rows[0],{zone:'UTC',status:'unsupported'});
});
test('official Calcutta backward alias is accepted only for Kolkata',()=>{
 const Format=formatter(parts=>parts,value=>({...value,timeZone:'Asia/Calcutta'}));
 const result=calculate(input(),{DateTimeFormat:Format});
 assert.equal(result.rows[4].status,'ok');
 for(const row of result.rows.filter(r=>r.zone!=='Asia/Kolkata'))assert.deepEqual(row,{zone:row.zone,status:'unsupported'});
});
