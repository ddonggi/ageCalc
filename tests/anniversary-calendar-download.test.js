'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('static/js/anniversary-calendar-download.js', 'utf8');
function harness(birthday = false, supported = true) {
    function element(extra = {}) {
        return Object.assign({ listeners: {}, disabled: true, addEventListener(event, fn) { this.listeners[event] = fn; } }, extra);
    }
    const input = element({value: birthday ? '0229' : '20240229'});
    const month = element({value: '2'}), day = element({value: '29'});
    const form = element();
    const button = element({dataset: {calendarKind: birthday ? 'birthday' : 'hundredth', calendarDate: birthday ? '20280229' : '20240607'}});
    const result = {id: birthday ? 'birthday-dday-result-content' : 'hundred-day-result-content', dataset: {calendarInput: input.value, calendarMonth: '2', calendarDay: '29'}, querySelectorAll() { return [button]; }};
    const status = {textContent: ''};
    const calls = [], downloads = [], revoked = [], timers = [], listeners = {};
    const document = { querySelector() {return result;}, getElementById(id) {return ({'birthday-dday-form':form, 'hundred-day-form':form, 'birthday-dday-input':input, 'hundred-day-date':input, 'birthday-dday-month':month, 'birthday-dday-day':day, 'calendar-download-status':status})[id];}, addEventListener(event, fn) {listeners[event]=fn;}, body: {appendChild(){}}, createElement() {return {click(){downloads.push(this.download);}, remove(){}};} };
    const window = {AnniversaryCalendar: {buildEvent(options) {calls.push(options); return JSON.stringify(options);}}, crypto: supported ? {randomUUID() { return '79107d56-1af9-4ae7-a459-df004c909069'; }} : {}, addEventListener(event, fn){listeners[event]=fn;}, setTimeout(fn){timers.push(fn);} };
    vm.runInNewContext(source,{window,document, Blob,URL:{createObjectURL(){return 'blob:test';},revokeObjectURL(url){revoked.push(url);}}});
    listeners.DOMContentLoaded();
    return {input,month,day,form,button,status,calls,downloads,revoked,timers,listeners};
}
test('confirmed result downloads fixed filename and reuses session UID/stamp',()=>{
    const h=harness(); h.button.listeners.click(); h.button.listeners.click();
    assert.deepEqual(h.downloads,['agecalc-anniversary.ics','agecalc-anniversary.ics']);
    assert.equal(h.calls.length,1);assert.equal(h.calls[0].date,'20240607');assert.match(h.calls[0].dtstamp,/^\d{8}T\d{6}Z$/);
    h.timers.forEach(fn=>fn());assert.deepEqual(h.revoked,['blob:test','blob:test']);
});
test('input event invalidates even after value is restored and forced click',()=>{
    const h=harness(); h.form.listeners.input(); h.button.disabled=false;h.button.listeners.click(); assert.equal(h.downloads.length,0);assert.equal(h.button.disabled,true);
});
test('no-event input mutation cannot export stale result',()=>{
    const h=harness();h.input.value='20240301';h.button.listeners.click();assert.equal(h.downloads.length,0);
});
test('hidden birthday parameter mutation cannot export stale result',()=>{
    const h=harness(true);h.month.value='3';h.button.listeners.click();assert.equal(h.downloads.length,0);
});
test('button data mutation does not replace server-confirmed date',()=>{
    const h=harness();h.button.dataset.calendarDate='20301231';h.button.listeners.click();assert.equal(h.calls[0].date,'20240607');
});
test('initial pageshow leaves confirmed result available',()=>{
    const h=harness();h.listeners.pageshow({persisted:false});assert.equal(h.button.disabled,false);h.button.listeners.click();assert.equal(h.downloads.length,1);
});
test('pagehide and BFCache require recalculation',()=>{
    for(const event of ['pagehide','pageshow']) {const h=harness();h.listeners[event]({persisted:true});h.button.disabled=false;h.button.listeners.click();assert.equal(h.downloads.length,0);}
});
test('secure UUID unavailable keeps controls disabled',()=>{
    const h=harness(false,false);assert.equal(h.button.disabled,true);assert.equal(h.button.listeners.click,undefined);assert.notEqual(h.status.textContent,'');
});
