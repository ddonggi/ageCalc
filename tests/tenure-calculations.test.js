const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const calc = require('../static/js/tenure-calculations.js');
const globalRules = require('../static/js/global-calculations.js');
const cases = [
 ['2024-02-29','2025-02-28',[0,11,30,365],['2025-03-01',1,1]],
 ['2024-02-29','2025-03-01',[1,0,0,366],['2025-03-01',1,0]],
 ['2024-02-29','2025-03-02',[1,0,1,367],['2026-03-01',2,364]],
 ['2024-02-29','2028-02-28',[3,11,30,1460],['2028-02-29',4,1]],
 ['2024-02-29','2028-02-29',[4,0,0,1461],['2028-02-29',4,0]],
 ['2024-01-31','2024-02-29',[0,1,0,29],['2025-01-31',1,337]],
 ['2025-01-31','2025-02-28',[0,1,0,28],['2026-01-31',1,337]],
 ['2026-10-28','2026-10-28',[0,0,0,0],['2027-10-28',1,365]],
 ['2030-06-15','2031-06-15',[1,0,0,365],['2031-06-15',1,0]],
 ['2030-06-15','2031-06-16',[1,0,1,366],['2032-06-15',2,365]],
 ['0001-01-01','0001-01-01',[0,0,0,0],['0002-01-01',1,365]],
 ['0099-12-31','0100-01-01',[0,0,1,1],['0100-12-31',1,364]],
 ['9998-12-31','9999-12-31',[1,0,0,365],['9999-12-31',1,0]],
 ['9999-01-01','9999-01-01',[0,0,0,0],null],
 ['9998-01-01','9999-12-31',[1,11,30,729],null],
 ['9999-12-31','9999-12-31',[0,0,0,0],null],
 ['0001-01-01','9999-12-31',[9998,11,30,3652058],null],
 ['2096-02-29','2100-02-28',[3,11,30,1460],['2100-03-01',4,1]]
];
for (const [start,end,period,next] of cases) test(`${start} to ${end}`,()=>{
 const [years,months,days,elapsedDays]=period;
 assert.deepEqual(calc.calculate(start,end),{years,months,days,elapsedDays,
 nextAnniversary:next?{date:next[0],years:next[1],days:next[2]}:null});
});
for (const value of ['',null,undefined,42,'0000-01-01','10000-01-01','2024-2-29','2025-02-29','1900-02-29','2024-04-31','2024-01-01T00:00:00Z',' 2024-01-01','2024-01-01 ']) test(`invalid ${String(value)}`,()=>{
 assert.throws(()=>calc.calculate(value,'2026-10-28'),/invalid_date/);
 assert.throws(()=>calc.calculate('0001-01-01',value),/invalid_date/);
});
test('reverse range',()=>assert.throws(()=>calc.calculate('2026-10-29','2026-10-28'),/end_before_start/));
test('browser export reuses existing duration',()=>{
 let calls=0;
 const context={AgeCalcGlobalRules:{...globalRules,duration(...args){calls++;return globalRules.duration(...args);}}};
 vm.runInNewContext(fs.readFileSync('static/js/tenure-calculations.js','utf8'),context);
 assert.equal(context.AgeCalcTenureRules.calculate('2024-02-29','2025-02-28').days,30);
 assert.equal(calls,1);
});
test('include flag has no effect',()=>assert.deepEqual(calc.calculate('2026-10-28','2026-10-28',true),calc.calculate('2026-10-28','2026-10-28')));
