"use strict";
/* Assay-agnostic qualitative report organizer. No clinical decision rules. */
(function (scope) {
  const RESULTS = new Map([
    ["DETECTED", "Detected"], ["POSITIVE", "Detected"],
    ["NOT DETECTED", "Not detected"], ["NEGATIVE", "Not detected"],
    ["INVALID", "Invalid"], ["INDETERMINATE", "Indeterminate"],
    ["INCONCLUSIVE", "Indeterminate"], ["NOT TESTED", "Not tested"]
  ]);

  function parseCSV(text) {
    if (typeof text !== "string" || text.length > 262144) {
      throw new Error("Provide a CSV document smaller than 256 KiB.");
    }
    const data = text.replace(/^\uFEFF/, "");
    const records = [];
    let row = [], field = "", quoted = false, justClosed = false;
    for (let i = 0; i < data.length; i++) {
      const c = data[i];
      if (quoted) {
        if (c === '"' && data[i + 1] === '"') { field += '"'; i++; }
        else if (c === '"') { quoted = false; justClosed = true; }
        else { field += c; }
      } else if (c === ',') {
        row.push(field); field = ""; justClosed = false;
      } else if (c === '\r' || c === '\n') {
        row.push(field); field = ""; justClosed = false;
        if (row.some(cell => cell.trim() !== "")) records.push(row);
        row = [];
        if (c === '\r' && data[i + 1] === '\n') i++;
      } else if (c === '"') {
        if (field.length || justClosed) throw new Error("Invalid CSV quotation near character " + (i + 1) + ".");
        quoted = true;
      } else {
        if (justClosed && c !== " " && c !== "\t") throw new Error("Unexpected text after a closing quote.");
        if (justClosed && (c === " " || c === "\t")) continue;
        field += c;
      }
    }
    if (quoted) throw new Error("CSV has an unclosed quoted field.");
    row.push(field);
    if (row.some(cell => cell.trim() !== "")) records.push(row);
    if (records.length < 2) throw new Error("Add a header and at least one target row.");
    const header = records.shift().map(s => s.trim().toLowerCase());
    if (header.length !== 2 || !["target", "pathogen"].includes(header[0]) ||
        !["result", "status"].includes(header[1])) {
      throw new Error("CSV header must be target,result (or pathogen,status), with exactly two columns.");
    }
    if (records.length > 100) throw new Error("Maximum 100 target rows per analysis.");
    const seen = new Set();
    return records.map((cells, i) => {
      if (cells.length !== 2) throw new Error("Row " + (i + 2) + " must have two columns.");
      const target = cells[0].trim();
      const raw = cells[1].trim().replace(/[\s_-]+/g, " ").toUpperCase();
      if (!target || target.length > 120) throw new Error("Row " + (i + 2) + " has an invalid target name.");
      const key = target.toLocaleLowerCase();
      if (seen.has(key)) throw new Error("Duplicate target: " + target);
      seen.add(key);
      const result = RESULTS.get(raw);
      if (!result) throw new Error("Unsupported result '" + cells[1].trim() + "' on row " + (i + 2) + ".");
      return {target, result};
    });
  }

  function summarize(rows) {
    if (!Array.isArray(rows) || !rows.length) throw new Error("No results to summarize.");
    const counts = {"Detected":0, "Not detected":0, "Invalid":0, "Indeterminate":0, "Not tested":0};
    for (const row of rows) {
      if (!Object.prototype.hasOwnProperty.call(counts, row.result)) throw new Error("Unrecognized result.");
      counts[row.result]++;
    }
    const review = counts.Invalid + counts.Indeterminate + counts["Not tested"];
    return {
      rows, counts,
      classification: review ? "Incomplete / needs review" : counts.Detected ? "One or more targets detected" : "No listed targets detected",
      caveat: "Result summary only. Target menus, controls, limits of detection, and clinical interpretation depend on the specific assay. A negative panel does not exclude infection."
    };
  }

  scope.viralPanel = Object.freeze({parseCSV, summarize});

  if (typeof document === "undefined") return;
  const byId = id => document.getElementById(id);
  const input = byId("csv");
  const error = byId("error");
  const summary = byId("summary");
  const output = byId("results");
  const csvButton = byId("export-csv");
  const jsonButton = byId("export-json");
  let last = null;

  function addCell(row, tag, value) {
    const cell = document.createElement(tag);
    cell.textContent = value;
    row.appendChild(cell);
  }

  function escapeCSV(value) {
    const s = String(value);
    // Prevent formula execution when a downloaded CSV is opened in a spreadsheet.
    const safe = /^[\s]*[=+@-]/.test(s) ? "'" + s : s;
    return '"' + safe.replace(/"/g, '""') + '"';
  }

  function download(name, text, type) {
    const url = URL.createObjectURL(new Blob([text], {type}));
    const a = document.createElement("a");
    a.href = url; a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function run() {
    last = null;
    csvButton.disabled = true;
    jsonButton.disabled = true;
    output.replaceChildren();
    summary.textContent = "";
    error.textContent = "";
    try {
      last = summarize(parseCSV(input.value));
      byId("total").textContent = String(last.rows.length);
      byId("detected").textContent = String(last.counts.Detected);
      byId("negative").textContent = String(last.counts["Not detected"]);
      byId("needs-review").textContent = String(last.counts.Invalid + last.counts.Indeterminate + last.counts["Not tested"]);
      summary.textContent = last.classification + ". " + last.caveat;
      last.rows.forEach(item => {
        const tr = document.createElement("tr");
        addCell(tr, "td", item.target);
        addCell(tr, "td", item.result);
        output.appendChild(tr);
      });
      byId("result-panel").hidden = false;
      csvButton.disabled = false;
      jsonButton.disabled = false;
    } catch (e) {
      byId("result-panel").hidden = true;
      error.textContent = e.message || "Unable to parse report.";
    }
  }

  byId("analyze").addEventListener("click", run);
  byId("sample").addEventListener("click", () => {
    input.value = "target,result\nSARS-CoV-2,Not detected\nInfluenza A,Detected\nInfluenza B,Not detected\nRSV,Indeterminate\n";
    run();
  });
  byId("upload").addEventListener("change", async event => {
    const file = event.target.files[0];
    if (!file) return;
    if (file.size > 262144) { error.textContent = "File must be smaller than 256 KiB."; return; }
    try { input.value = await file.text(); run(); }
    catch { error.textContent = "Unable to read the selected file."; }
    event.target.value = "";
  });
  csvButton.addEventListener("click", () => {
    if (!last) return;
    const csv = "target,result\n" + last.rows.map(r => escapeCSV(r.target) + "," + escapeCSV(r.result)).join("\n") + "\n";
    download("respiratory-results.csv", csv, "text/csv;charset=utf-8");
  });
  jsonButton.addEventListener("click", () => {
    if (!last) return;
    download("respiratory-results.json", JSON.stringify(last, null, 2), "application/json");
  });
})(globalThis);
