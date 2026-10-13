"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const js = fs.readFileSync(path.join(__dirname, "../web/app.js"), "utf8");
const scope = {};
vm.runInNewContext(js, scope);
const {parseCSV, summarize} = scope.viralPanel;

test("analyzes qualitative targets without manufacturing risk levels", () => {
  const rows = parseCSV("target,result\nInfluenza A,Detected\nRSV,Not detected\nSARS-CoV-2,Inconclusive\n");
  const summary = summarize(rows);
  assert.equal(summary.counts.Detected, 1);
  assert.equal(summary.counts["Not detected"], 1);
  assert.equal(summary.counts.Indeterminate, 1);
  assert.equal(summary.classification, "Incomplete / needs review");
});
test("normalizes approved result aliases and handles escaped CSV quotes", () => {
  const rows = parseCSV('\uFEFFtarget,result\r\n"Human ""meta""pneumovirus",Positive\r\nInfluenza B,Negative\r\n');
  assert.equal(rows[0].target, 'Human "meta"pneumovirus');
  assert.equal(rows[0].result, "Detected");
  assert.equal(rows[1].result, "Not detected");
});
test("rejects unknown results, duplicates, malformed headers, and unterminated quotes", () => {
  const fail = data => assert.throws(() => parseCSV(data));
  fail("target,result\nRSV,ambiguous");
  fail("target,result\nRSV,Detected\nrsv,Not detected");
  fail("name,status\nRSV,Detected");
  fail('target,result\n"RSV,Detected');
  fail("target,result\nRSV,Detected,Extra");
});
test("rejects empty input and oversized panels", () => {
  assert.throws(() => parseCSV(""));
  assert.throws(() => parseCSV("target,result\n" + "RSV,Detected\n".repeat(101)));
  assert.throws(() => parseCSV("x".repeat(262145)));
});
test("does not alter target text on import", () => {
  const row = parseCSV('target,result\n"=SUM(1+1)",NOT TESTED')[0];
  assert.equal(row.target, "=SUM(1+1)");
  assert.equal(row.result, "Not tested");
});
