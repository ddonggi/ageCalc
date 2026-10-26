const test = require('node:test');
const assert = require('node:assert/strict');
const { normalize, search } = require('../static/js/tool-finder.js');
const items = [
 {endpoint:'age', title:'만 나이 계산기', aliases:['만나이'], group:'age', order:1},
 {endpoint:'days', title:'백일 계산기', aliases:['첫돌','천일','1000일'], group:'anniversary', order:2},
 {endpoint:'time', title:'시간 차이 계산기', aliases:['휴게시간','익일','근무시간'], group:'anniversary', order:3},
 {endpoint:'date', title:'날짜 가감 계산기', aliases:['ISO 주차','연간 진행률'], group:'anniversary', order:4},
];
test('NFKC lowercase whitespace; punctuation retained',()=> {
 assert.equal(normalize('  ＩＳＯ  주차 '),'iso 주차');
 assert.equal(normalize('<img>'),'<img>');
});
test('reviewed aliases, compact whitespace and AND independent tokens',()=>{
 for(const [q,e] of [['만나이','age'],['만 나이','age'],['첫돌','days'],['천일','days'],['1000일','days'],['휴게시간','time'],['익일','time'],['주차 ISO','date'],['연간 진행률','date']]) assert.equal(search(items,q)[0].endpoint,e);
 assert.deepEqual(search(items,'천일','school'),[]);
 for(const q of ['급여','세금','임신 진단','<img src=x onerror=alert(1)>']) assert.deepEqual(search(items,q),[]);
 assert.equal(search(items,' \t ').length,4);
});
test('ranking exact title then alias then title tokens then mixed; deterministic ties',()=>{
 const data=[{endpoint:'z',title:'새 도구',aliases:['도구'],order:0},{endpoint:'a',title:'도구',aliases:[],order:9},{endpoint:'b',title:'다른 것',aliases:['도구'],order:3}];
 assert.deepEqual(search(data,'도구').map(x=>x.endpoint),['a','z','b']);
 assert.deepEqual(search([{endpoint:'z',title:'도구',order:1},{endpoint:'a',title:'도구',order:1}],'').map(x=>x.endpoint),['a','z']);
});
test('80 UTF-16 limit, mixed fields and title precedence',()=>{
 const title='a'.repeat(80);
 const data=[{endpoint:'x',title,aliases:[],order:0},{endpoint:'b',title:'나이 비교',aliases:['부모 자녀'],order:2},{endpoint:'a',title:'부모 자녀 나이',aliases:[],order:3}];
 assert.equal(search(data,title+'b')[0].endpoint,'x');
 assert.deepEqual(search(data,'부모 나이').map(x=>x.endpoint),['a','b']);
 assert.deepEqual(search(items,'첫돌','anniversary').map(x=>x.endpoint),['days']);
});
