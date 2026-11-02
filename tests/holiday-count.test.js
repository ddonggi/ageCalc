const test = require('node:test');
const assert = require('node:assert/strict');
const holiday = require('../static/js/holiday-count.js');
function setup() {
    let online = true, interval;
    let now = 0, wall = Date.parse('2026-11-02T03:00:00Z'), timer;
    const pending = [], states = [];
    const controller = holiday.create({
        fetch: (url, options) => new Promise((resolve, reject) => pending.push({url, options, resolve, reject})),
        now: () => now, wall: () => wall, online: () => online,
        setTimeout: callback => {timer = callback; return 1;}, clearTimeout: () => {},
        setInterval: callback => {interval = callback; return 2;}, clearInterval: () => {},
        render: state => states.push(state), calculate: () => ({referenceDays: 1})
    });
    return {controller, pending, states, timer: () => timer(), advance: n => {now += n; wall += n;}, offline: () => {online=false;}, jump: n => {wall+=n;}, tick: () => interval()};
}
const FACTS = [{"date": "2027-01-01", "label": "1월 1일", "type": "national"}, {"date": "2027-02-06", "label": "설날(연휴)", "type": "national"}, {"date": "2027-02-07", "label": "설날(연휴)", "type": "national"}, {"date": "2027-02-08", "label": "설날(연휴)", "type": "national"}, {"date": "2027-02-09", "label": "대체공휴일(설날)", "type": "substitute"}, {"date": "2027-03-01", "label": "3·1절", "type": "national"}, {"date": "2027-05-01", "label": "노동절", "type": "national"}, {"date": "2027-05-03", "label": "대체공휴일(노동절)", "type": "substitute"}, {"date": "2027-05-05", "label": "어린이날", "type": "national"}, {"date": "2027-05-13", "label": "부처님 오신 날", "type": "national"}, {"date": "2027-06-06", "label": "현충일", "type": "national"}, {"date": "2027-07-17", "label": "제헌절", "type": "national"}, {"date": "2027-07-19", "label": "대체공휴일(제헌절)", "type": "substitute"}, {"date": "2027-08-15", "label": "광복절", "type": "national"}, {"date": "2027-08-16", "label": "대체공휴일(광복절)", "type": "substitute"}, {"date": "2027-09-14", "label": "추석(연휴)", "type": "national"}, {"date": "2027-09-15", "label": "추석(연휴)", "type": "national"}, {"date": "2027-09-16", "label": "추석(연휴)", "type": "national"}, {"date": "2027-10-03", "label": "개천절", "type": "national"}, {"date": "2027-10-04", "label": "대체공휴일(개천절)", "type": "substitute"}, {"date": "2027-10-09", "label": "한글날", "type": "national"}, {"date": "2027-10-11", "label": "대체공휴일(한글날)", "type": "substitute"}, {"date": "2027-12-25", "label": "기독탄신일", "type": "national"}, {"date": "2027-12-27", "label": "대체공휴일(기독탄신일)", "type": "substitute"}];
function payload(overrides = {}) {
    return {available: true, state: 'current', year: 2027, holidays: FACTS.map(item=>({...item})),
        metadata:{version:'v1',source_url:'https://www.kasa.go.kr/',verified_on:'2026-11-01',next_review:'2026-11-08'},
        server_now:'2026-11-02T12:00:00+09:00', expires_at:'2026-11-02T12:10:00+09:00',lease_ms:600000,...overrides};
}
async function reply(request, data) {request.resolve({ok:true,json:async()=>data}); await new Promise(setImmediate);}
test('opt-in and supported range required; fixed anonymous request', async () => {
    const h=setup(); h.controller.submit(false,'2027-01-01','2027-01-02',false);
    h.controller.submit(true,'2026-01-01','2027-01-02',false); assert.equal(h.pending.length,0);
    h.controller.submit(true,'2027-01-01','2027-01-02',false);
    assert.equal(h.pending[0].url,'/api/calendar/korea/2027');
    assert.equal(h.pending[0].options.credentials,'omit'); assert.equal(h.pending[0].options.referrerPolicy,'no-referrer');
    await reply(h.pending[0],payload()); assert.equal(h.states.at(-1).state,'ready');
});
test('late responses cannot restore invalidated facts',async()=>{
    const h=setup(); h.controller.submit(true,'2027-01-01','2027-01-02',false);
    h.controller.invalidate(); await reply(h.pending[0],payload()); assert.equal(h.states.at(-1).state,'idle');
});
test('round trip consumes lease and expiry clears result',async()=>{
    const h=setup(); h.controller.submit(true,'2027-01-01','2027-01-02',false);
    h.advance(600001); await reply(h.pending[0],payload()); assert.equal(h.states.at(-1).state,'unavailable');
});
test('invalid lease, source and temporal metadata fail closed',async()=>{
    for(const data of [payload({metadata:{...payload().metadata,next_review:'2026-11-09'}}),payload({server_now:'2026-02-30T12:00:00+09:00'}),payload({server_now:'2026-11-02T24:00:00+09:00'}),payload({lease_ms:Infinity}),payload({lease_ms:600001}),payload({expires_at:'2026-11-03T12:10:00+09:00'}),payload({metadata:{...payload().metadata,source_url:'javascript:alert(1)'}}),payload({available:false,holidays:[],lease_ms:0})]) {
        const h=setup(); h.controller.submit(true,'2027-01-01','2027-01-02',false); await reply(h.pending[0],data);
        assert.equal(h.states.at(-1).state,'unavailable');
    }
});
test('timeout aborts without retry',()=>{
    const h=setup(); h.controller.submit(true,'2027-01-01','2027-01-02',false); h.timer();
    assert.equal(h.pending[0].options.signal.aborted,true); assert.equal(h.states.at(-1).state,'unavailable'); assert.equal(h.pending.length,1);
});

test('new request wins even when old request resolves last',async()=>{
    const h=setup(); h.controller.submit(true,'2027-01-01','2027-01-02',false);
    h.controller.submit(true,'2027-02-01','2027-02-02',true);
    await reply(h.pending[1],payload()); const ready=h.states.at(-1);
    await reply(h.pending[0],payload()); assert.equal(h.states.at(-1),ready);
});
test('offline fails before request and clock jump removes displayed facts',async()=>{
    const offline=setup(); offline.offline(); offline.controller.submit(true,'2027-01-01','2027-01-02',false);
    assert.equal(offline.pending.length,0); assert.equal(offline.states.at(-1).state,'unavailable');
    for(const jump of [-60000,60000]) {
        const h=setup(); h.controller.submit(true,'2027-01-01','2027-01-02',false); await reply(h.pending[0],payload());
        h.jump(jump); h.tick(); assert.deepEqual(h.states.at(-1),{state:'expired'});
    }
});
test('displayed lease timer removes facts without auto request',async()=>{
    const h=setup(); h.controller.submit(true,'2027-01-01','2027-01-02',false); await reply(h.pending[0],payload());
    h.timer(); assert.deepEqual(h.states.at(-1),{state:'expired'}); assert.equal(h.pending.length,1);
});

const fs = require('node:fs');
const vm = require('node:vm');
function domFixture() {
    class Element {
        constructor() {this.listeners={};this.children=[];this.dataset={};this.hidden=true;this.value='';this.textContent='';this.checked=false;}
        addEventListener(name, callback) {(this.listeners[name] ||= []).push(callback);}
        emit(name) {(this.listeners[name]||[]).forEach(callback=>callback({preventDefault(){}}));}
        append(...nodes) {this.children.push(...nodes);}
        replaceChildren(...nodes) {this.children=nodes;}
        removeAttribute(name) {delete this[name];}
        focus() {this.focusCalls=(this.focusCalls||0)+1;}
        scrollIntoView() {}
    }
    const ids = {};
    for(const id of ['global-calculator','calculator-config','calculator-error','global-result','result-values','result-note','weekday-result','weekday-values','holiday-mode','holiday-copy','holiday-result','holiday-details','holiday-list','holiday-values','holiday-metadata','holiday-source','holiday-status','holiday-empty','tenure-mode','tenure-result','tenure-values','tenure-config','swap-dates','include-end','result-event','result-title','calculator-inputs','calculator-unavailable']) ids[id]=new Element();
    const ui={result:'Result',units:{day:{other:'{n} days'}},unit_week:{other:'{n} weeks'},duration_separator:' ',exclusive_note:'exclusive',inclusive_note:'inclusive'};
    ids['calculator-config'].textContent=JSON.stringify({kind:'days_between_dates',locale:'ko',ui});
    ids['holiday-copy'].textContent=JSON.stringify({loading:'loading',unavailable:'unavailable',expired:'expired',invalidated:'invalidated',verified:'verified',nextReview:'next',referenceDays:'reference',weekendDays:'weekends',holidayDays:'holidays'});
    ids['tenure-config'].textContent='{}';
    const groups={};
    for(const name of ['start','end']) {
        const legend=new Element();legend.textContent=name;
        for(const part of ['year','month','day']) {const node=ids[`${name}-${part}`]=new Element();node.value=part==='year'?'2027':part==='month'?'1':name==='start'?'1':'2';}
        groups[name]={querySelector: selector=>selector==='legend'?legend:ids[`${name}-${selector.match(/"(.*?)"/)[1]}`]};
    }
    const form=ids['global-calculator'];
    form.querySelector=selector=>{
        if(selector.endsWith(' legend')) return groups[selector.match(/"(.*?)"/)[1]].querySelector('legend');
        return groups[selector.match(/"(.*?)"/)[1]];
    };
    form.querySelectorAll=()=>[];
    const doc=new Element();doc.getElementById=id=>ids[id]||null;doc.createElement=()=>new Element();
    const requests=[]; const win=new Element();
    Object.assign(win,{AgeCalcGlobalRules:require('../static/js/global-calculations.js'),AgeCalcHolidayCount:holiday,
        performance:{now:()=>0},navigator:{onLine:true},fetch:(url,options)=>new Promise(resolve=>requests.push({url,options,resolve})),
        setTimeout:()=>1,clearTimeout(){},setInterval:()=>2,clearInterval(){},matchMedia:()=>({matches:true})});
    vm.runInNewContext(fs.readFileSync('static/js/global-calculator.js','utf8'),{window:win,document:doc,Intl,Date,JSON,Number,String});
    return {ids,doc,win,form,requests};
}
test('DOM event integration invalidates every edit and lifecycle without querying again',async()=>{
    for(const event of ['input','change','reset','swap','visibilitychange','pagehide','pageshow','focus','offline']) {
        const h=domFixture();h.ids['holiday-mode'].checked=true;h.form.emit('submit');
        assert.equal(h.requests.length,1,event);assert.equal(h.ids['global-result'].hidden,false,event);
        if(event==='swap')h.ids['swap-dates'].emit('click');
        else if(['input','change','reset'].includes(event))h.form.emit(event);
        else if(event==='visibilitychange')h.doc.emit(event);
        else h.win.emit(event);
        await reply(h.requests[0],payload());
        assert.equal(h.ids['holiday-details'].hidden,true,event);assert.equal(h.requests.length,1,event);
    }
});
test('async holiday result never steals focus and A remains during server failure',async()=>{
    const h=domFixture();h.ids['holiday-mode'].checked=true;h.form.emit('submit');
    const focus=h.ids['global-result'].focusCalls;
    await reply(h.requests[0],payload());
    assert.equal(h.ids['holiday-details'].hidden,false);
    assert.equal(h.ids['global-result'].focusCalls,focus);
    h.form.emit('submit'); await reply(h.requests[1],{available:false,holidays:[],lease_ms:0});
    assert.equal(h.ids['weekday-result'].hidden,false); assert.equal(h.ids['global-result'].hidden,false);
    assert.equal(h.ids['holiday-details'].hidden,true);
});

test('malformed records fail closed before rendering including duplicate and invalid date',async()=>{
    for(const records of [[],FACTS.slice(0,23),FACTS.slice(0,1),[FACTS[0],...FACTS.slice(0,23)],[{date:'2027-02-30',label:'x',type:'national'},...FACTS.slice(1)],[{date:'2026-01-01',label:'x',type:'national'},...FACTS.slice(1)],[{date:'2027-01-01',label:' ',type:'national'},...FACTS.slice(1)],[{date:'2027-01-01',label:'x',type:'local'},...FACTS.slice(1)]]) {
        const h=setup();h.controller.submit(true,'2027-01-01','2027-01-02',false);
        await reply(h.pending[0],payload({holidays:records})); assert.equal(h.states.at(-1).state,'unavailable');
    }
});

test('default unchecked lifecycle never introduces holiday UI',()=>{
    const h=domFixture();h.form.emit('submit');
    for(const event of ['focus','pagehide','pageshow','offline']) {
        h.win.emit(event); assert.equal(h.ids['holiday-result'].hidden,true,event);
    }
    h.doc.emit('visibilitychange');assert.equal(h.ids['holiday-result'].hidden,true);
    assert.equal(h.requests.length,0);
});

test('invalid and reverse dates never produce a request',()=>{
    for(const [start,end] of [['2027-02-30','2027-03-01'],['2027-01-03','2027-01-01']]) {
        const h=setup();h.controller.submit(true,start,end,false);assert.equal(h.pending.length,0);
    }
});
