'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { calculateWeek, createCsv } = require('../static/js/weekly-time-calculations.js');
const empty = () => Array.from({length:7}, () => ({start:'',end:'',nextDay:false,breakMinutes:'0'}));
function week(entries) { const rows=empty(); for(const [index,value] of entries) rows[index]={...rows[index],...value}; return rows; }
const shift=(start,end,nextDay=false,breakMinutes='0')=>({start,end,nextDay,breakMinutes});
function hasError(rows, row, field, code) { const result=calculateWeek(rows); assert.equal(result.ok,false); assert.ok(result.errors.some(e=>e.row===row&&e.field===field&&e.code===code),JSON.stringify(result)); assert.equal('totals' in result,false); }
test('empty week requests input, with no zero-success total',()=>hasError(empty(),null,'rows','empty_week'));
test('sums integer minutes before decimal rounding and preserves input',()=>{const rows=week([[0,shift('00:00','00:01')],[1,shift('00:00','00:01')]]);const original=JSON.stringify(rows);const result=calculateWeek(rows);assert.deepEqual(result.totals,{grossMinutes:2,breakMinutes:0,netMinutes:2,decimalHours:'0.03'});assert.equal(result.days[2].status,'empty');assert.equal(JSON.stringify(rows),original);assert.deepEqual(calculateWeek(rows),result);});
test('deducts breaks through the existing duration rule',()=>{const result=calculateWeek(week([[0,shift('09:00','18:00',false,'60')]]));assert.deepEqual(result.totals,{grossMinutes:540,breakMinutes:60,netMinutes:480,decimalHours:'8.00'});});
test('zero minutes is valid and differs from empty',()=>{const result=calculateWeek(week([[0,shift('09:00','09:00')]]));assert.equal(result.ok,true);assert.equal(result.days[0].status,'valid');assert.equal(result.totals.netMinutes,0);assert.equal(result.days[1].status,'empty');});
test('overnight equal times allow the exact seven-day maximum',()=>{const result=calculateWeek(Array.from({length:7},()=>shift('00:00','00:00',true)));assert.equal(result.totals.netMinutes,10080);assert.equal(result.totals.decimalHours,'168.00');assert.equal(result.crossesWeekBoundary,false);});
test('the full gross amount can be a break',()=>{const result=calculateWeek(Array.from({length:7},()=>shift('00:00','00:00',true,'1440')));assert.deepEqual(result.totals,{grossMinutes:10080,breakMinutes:10080,netMinutes:0,decimalHours:'0.00'});});
test('Sunday spill does not wrap back to the earlier Monday',()=>{const result=calculateWeek(week([[0,shift('00:00','02:00')],[6,shift('23:00','01:00',true)]]));assert.equal(result.ok,true);assert.equal(result.totals.netMinutes,240);assert.equal(result.crossesWeekBoundary,true);});
test('overlap blocks both rows even when breaks cover its duration',()=>{const rows=week([[4,shift('22:00','06:00',true,'60')],[5,shift('05:00','13:00',false,'60')]]);const result=calculateWeek(rows);assert.deepEqual(result.errors,[{row:4,field:'rows',code:'overlap',relatedRow:5},{row:5,field:'rows',code:'overlap',relatedRow:4}]);assert.equal(createCsv(rows).ok,false);});
test('one minute overlap fails while touching endpoints pass',()=>{hasError(week([[4,shift('22:00','06:00',true)],[5,shift('05:59','13:00')]]),4,'rows','overlap');const result=calculateWeek(week([[4,shift('22:00','06:00',true,'60')],[5,shift('06:00','13:00',false,'60')]]));assert.equal(result.ok,true);assert.equal(result.totals.netMinutes,780);});
test('zero-length gross intervals do not create overlap',()=>{const result=calculateWeek(week([[0,shift('22:00','10:00',true)],[1,shift('09:00','09:00')]]));assert.equal(result.ok,true);});
for(const [name,value,field,code] of [
 ['same-day reverse',shift('22:00','06:00'),'end','end_before_start'],
 ['more than 24 hours',shift('09:00','09:01',true),'end','duration_too_long'],
 ['invalid start',shift('24:00','10:00'),'start','invalid_time'],
 ['non-padded start',shift('9:00','10:00'),'start','invalid_time'],
 ['invalid end',shift('09:00','00:60'),'end','invalid_time'],
 ['missing end',shift('09:00',''),'end','invalid_time'],
 ['break exceeds duration',shift('09:00','09:00',false,'1'),'breakMinutes','break_exceeds_duration'],
 ['nonboolean overnight',shift('09:00','10:00','true'),'nextDay','invalid_day'],
 ['break only',shift('','',false,'1'),'start','invalid_time'],
 ['overnight only',shift('','',true),'start','invalid_time']
]) test(name,()=>hasError(week([[0,value]]),0,field,code));
for(const value of ['', '-1','1.5','1e2','+1',' 1 ','NaN','Infinity','1441','=1+1','@SUM(1)','\t1','1\r\n2','"1"',60]) test('rejects break '+JSON.stringify(value),()=>hasError(week([[0,shift('09:00','18:00',false,value)]]),0,'breakMinutes','invalid_break'));
for(const value of [null,{},[],empty().slice(1),[...empty(),empty()[0]]]) test('rejects invalid week shape '+JSON.stringify(value),()=>hasError(value,null,'rows','invalid_week'));
test('rejects nonobject, unknown fields and inherited fields',()=>{for(const value of [null,[],{...empty()[0],memo:'=1+1'},Object.create(empty()[0])])hasError(week([[0,value]]).map((r,i)=>i===0?value:r),0,'rows','invalid_week');});
test('reports all row failures in stable row order without echoing raw input',()=>{const rows=week([[5,shift('<script>alert(1)</script>','01:00')],[0,shift('02:00','01:00')]]);const result=calculateWeek(rows);assert.deepEqual(result.errors.map(e=>e.row),[0,5]);assert.equal(JSON.stringify(result).includes('script'),false);assert.deepEqual(createCsv(rows),result);});
test('CSV revalidates, quotes every cell, and has BOM plus nine CRLF records',()=>{const rows=week([[0,shift('09:00','09:00')],[1,shift('22:00','06:00',true,'60')]]);const result=createCsv(rows);assert.equal(result.ok,true);assert.equal(result.csv.charCodeAt(0),0xFEFF);const lines=result.csv.slice(1).split('\r\n');assert.equal(lines.length,9);for(const line of lines){assert.match(line,/^"(?:[^"]|"")*"(?:,"(?:[^"]|"")*"){8}$/);}const cells=lines.map(l=>l.slice(1,-1).split('","'));assert.deepEqual(cells[1].slice(2),['09:00','09:00',cells[1][4],'0','0','0','0.00']);assert.deepEqual(cells[3].slice(2),['','','','','','','']);assert.deepEqual(cells[8].slice(5),['480','60','420','7.00']);rows[0].start='=1+1';assert.equal(createCsv(rows).ok,false);});
test('CSV totals use integer minutes rather than summed rounded day values',()=>{const result=createCsv(week([[0,shift('00:00','00:01')],[1,shift('00:00','00:01')]]));assert.ok(result.csv.endsWith('"2","0","2","0.03"'));});
test('one minute after midnight and decimal boundaries are exact',()=>{for(const [start,end,nextDay,minutes,decimal] of [['23:59','00:00',true,1,'0.02'],['00:00','00:59',false,59,'0.98'],['00:00','01:01',false,61,'1.02']]){const result=calculateWeek(week([[0,shift(start,end,nextDay)]]));assert.equal(result.totals.netMinutes,minutes);assert.equal(result.totals.decimalHours,decimal);}});
test('deterministic valid weeks match an independent integer-minute oracle',()=>{
    for(let seed=0;seed<100;seed++){
        let gross=0,rest=0;
        const rows=Array.from({length:7},(_,day)=>{
            const duration=(seed*37+day*61)%481;
            const pause=(seed+day)%Math.min(duration+1,61);
            gross+=duration;rest+=pause;
            const end=9*60+duration;
            return shift('09:00',String(Math.floor(end/60)).padStart(2,'0')+':'+String(end%60).padStart(2,'0'),false,String(pause));
        });
        assert.deepEqual(calculateWeek(rows).totals,{grossMinutes:gross,breakMinutes:rest,netMinutes:gross-rest,decimalHours:((gross-rest)/60).toFixed(2)});
    }
});
test('browser globals use the daily module without DOM, storage, or device date',()=>{
    const vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
    const sandbox={Date:function(){throw new Error('device date is forbidden');}};
    vm.createContext(sandbox);
    for(const file of ['time-calculations.js','weekly-time-calculations.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/js',file),'utf8'),sandbox);
    const result=sandbox.WeeklyTimeCalculations.calculateWeek(week([[0,shift('09:00','18:00',false,'60')]]));
    assert.equal(result.totals.netMinutes,480);
    assert.equal(Object.isFrozen(sandbox.WeeklyTimeCalculations),true);
});
