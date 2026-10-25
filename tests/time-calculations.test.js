const test = require('node:test');
const assert = require('node:assert/strict');
const {calculateDuration} = require('../static/js/time-calculations.js');
const input = (start='09:00',end='18:00',nextDay=false,breakMinutes='0') => ({start,end,nextDay,breakMinutes});
const cases = [
 ['09:00','18:00',false,'60',540,480,'8.00'],
 ['22:00','06:00',true,'60',480,420,'7.00'],
 ['09:00','09:00',false,'0',0,0,'0.00'],
 ['09:00','09:00',true,'0',1440,1440,'24.00'],
 ['09:00','09:00',true,'1440',1440,0,'0.00'],
 ['23:59','00:00',true,'0',1,1,'0.02'],
 ['00:00','23:59',false,'0',1439,1439,'23.98'],
 ['12:00','12:59',false,'0',59,59,'0.98'],
 ['12:00','13:01',false,'0',61,61,'1.02'],
 ['12:00','13:01',false,'61',61,0,'0.00'],
 ['01:30','03:30',false,'0',120,120,'2.00'],
];
for (const [start,end,nextDay,breakMinutes,grossMinutes,netMinutes,decimalHours] of cases) {
 test(`wall clock ${start} to ${end}, next=${nextDay}, break=${breakMinutes}`, () => {
  const original = input(start,end,nextDay,breakMinutes);
  const snapshot = {...original};
  const result = calculateDuration(original);
  assert.deepEqual(result,{ok:true,grossMinutes,breakMinutes:Number(breakMinutes),netMinutes,decimalHours});
  assert.deepEqual(original,snapshot);
  assert.equal(result.netMinutes+result.breakMinutes,result.grossMinutes);
  assert.deepEqual(calculateDuration(original),result);
 });
}
for (const value of ['', '24:00','12:60','9:00','12:00:01',' 09:00','09:00 ','abc',null,900,{},'x'.repeat(10000)]) {
 for (const field of ['start','end']) test(`reject ${field} ${String(value).slice(0,20)}`,()=> {
  assert.deepEqual(calculateDuration({...input(),[field]:value}),{ok:false,field,code:'invalid_time'});
 });
}
for (const value of ['', '-1','1.5','1e2','NaN','Infinity','1441',' 1','1 ',null,1,true,{},'x'.repeat(10000)]) {
 test(`reject break ${String(value).slice(0,20)}`,()=>assert.deepEqual(calculateDuration({...input(),breakMinutes:value}),{ok:false,field:'breakMinutes',code:'invalid_break'}));
}
for (const nextDay of ['true','false',0,1,null,undefined,{}]) {
 test(`reject day ${String(nextDay)}`,()=>assert.deepEqual(calculateDuration({...input(),nextDay}),{ok:false,field:'nextDay',code:'invalid_day'}));
}
test('same day reversal requires explicit next day',()=>assert.deepEqual(calculateDuration(input('22:00','06:00')),{ok:false,field:'end',code:'end_before_start'}));
test('more than 24 hours rejected',()=>assert.deepEqual(calculateDuration(input('09:00','09:01',true)),{ok:false,field:'end',code:'duration_too_long'}));
test('break exceeds gross rejected',()=>assert.deepEqual(calculateDuration(input('12:00','13:01',false,'62')),{ok:false,field:'breakMinutes',code:'break_exceeds_duration'}));
