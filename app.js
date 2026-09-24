// app.js — browser-side orchestration for the 1.8.9 -> 26.1.2 texture pack
// converter. This file does NOT contain any of the actual texture-matching
// logic; it just reproduces, in the browser, what convert.sh does on the
// command line: extract both packs, run each build*.py stage in the same
// (non-alphabetical) order against a Pyodide-hosted Python, then zip up
// output_pack and hand back the two result files.
//
// The real logic lives untouched in scripts/build.py ... build13.py and
// scripts/aliases.py, copied verbatim from conversion-source-code.zip.
// pyodide.js itself (which defines the global loadPyodide()) is loaded by
// a <script> tag in index.html — keep that version in sync with any
// change here.

const SCRIPTS_BASE = "scripts/";

const EXPECT_BUNDLED_REFERENCE_PACK = false;

// Exact order from convert.sh's STAGES array. Order is NOT alphabetical —
// see that file's comments for why (build11 predates build12/13 but runs
// after them; build6 does the final strip and must run dead last).
const STAGE_ORDER = [
  { file: "build.py", label: "Matching blocks & items" },
  { file: "build2.py", label: "Matching entities, environment & effects" },
  { file: "build3.py", label: "Rebuilding GUI & HUD sprites" },
  { file: "build4.py", label: "Slicing clock & compass animation frames" },
  { file: "build5.py", label: "Bed icon override & chest glint pass" },
  { file: "build7.py", label: "Placing paintings" },
  { file: "build8.py", label: "Redesigning the Bad Omen bottle" },
  { file: "build9.py", label: "Full texture-tree audit" },
  { file: "build10.py", label: "Fixing pig / cow / mooshroom variants" },
  { file: "build12.py", label: "Chest seams, armor icons & pack icon" },
  { file: "build13.py", label: "Applying your requested removals" },
  { file: "build11.py", label: "Simplifying mob textures" },
  { file: "build6.py", label: "Final cleanup: stripping unmatched textures" },
];

const ALL_SCRIPT_FILES = [
  "_harness_extract.py",
  "aliases.py", 
  ...STAGE_ORDER.map((s) => s.file),
  "_harness_finalize.py"
];
const METHOD_DISPLAY_ORDER = ["exact", "alias", "fuzzy", "reconstructed", "split-crop"];

// ---------------------------------------------------------------------------
// Tiny DOM helpers + state
// ---------------------------------------------------------------------------

const $ = (sel) => document.querySelector(sel);

const el = {
  dropZone: $("#drop-zone"),
  fileInput: $("#file-input"),
  fileName: $("#file-name"),
  secondSlot: $("#second-upload-slot"),
  convertBtn: $("#convert-btn"),
  resetBtn: $("#reset-btn"),
  engineStatus: $("#engine-status"),
  stageArrowFill: $("#stage-arrow-fill"),
  stageLabel: $("#stage-label"),
  log: $("#log"),
  panels: {
    upload: $("#panel-upload"),
    converting: $("#panel-converting"),
    success: $("#panel-success"),
    error: $("#panel-error"),
  },
  summary: $("#summary-stats"),
  downloadPack: $("#download-pack"),
  downloadReport: $("#download-report"),
  errorMessage: $("#error-message"),
};

let pyodide = null;
let engineIsReady = false;
let engineReady = null; // Promise, resolves when pyodide+packages+scripts+reference are all loaded
let engineError = null;
let oldPackFile = null;
let newPackFile = null; // only used when EXPECT_BUNDLED_REFERENCE_PACK is false

function showPanel(name) {
  for (const [key, node] of Object.entries(el.panels)) {
    if (node) node.hidden = key !== name;
  }
}

function log(msg) {
  const line = document.createElement("div");
  line.textContent = msg;
  el.log.appendChild(line);
  el.log.scrollTop = el.log.scrollHeight;
}

function setStageProgress(i, total, label) {
  const pct = Math.round((i / total) * 100);
  el.stageArrowFill.style.width = `${pct}%`;
  el.stageLabel.textContent = `Stage ${Math.min(i + 1, total)} of ${total}: ${label}`;
}

function updateConvertEnabled() {
  const packReady = EXPECT_BUNDLED_REFERENCE_PACK
    ? Boolean(oldPackFile)
    : Boolean(oldPackFile && newPackFile);
  el.convertBtn.disabled = !(packReady && engineIsReady);
}

// ---------------------------------------------------------------------------
// Optional second upload slot (dual-pack mode)
// ---------------------------------------------------------------------------

function buildSecondUploadSlotIfNeeded() {
  if (EXPECT_BUNDLED_REFERENCE_PACK || !el.secondSlot) return;

  el.secondSlot.hidden = false;
  el.secondSlot.innerHTML = `
    <label class="field-label" for="file-input-2">26.1.2 client.jar (or default pack .zip)</label>
    <div class="simple-file-row">
      <input type="file" id="file-input-2" accept=".jar,application/java-archive,.zip,application/zip" />
      <span id="file-name-2" class="file-name"></span>
    </div>
  `;
  const input2 = $("#file-input-2");
  const name2 = $("#file-name-2");
  input2.addEventListener("change", (e) => {
    const f = e.target.files[0];
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".zip") && !f.name.toLowerCase().endsWith(".jar")) {
      log(`"${f.name}" doesn't look like valid input`);
      return;
    }
    newPackFile = f;
    name2.textContent = f.name;
    updateConvertEnabled();
  });
}

// ---------------------------------------------------------------------------
// Engine bootstrap — kicked off immediately on page load, in parallel with
// the user choosing a file, so the wait is (mostly) hidden.
// ---------------------------------------------------------------------------

async function loadPyodideRuntime() {
  el.engineStatus.textContent = "Loading Python runtime…";
  pyodide = await loadPyodide();
  el.engineStatus.textContent = "Loading Pillow & numpy…";
  await pyodide.loadPackage(["Pillow", "numpy"]);
}

async function prepareVirtualFilesystem() {
  await pyodide.runPythonAsync(`
import os, sys
for d in ("/work/scripts", "/work/old_pack", "/work/new_pack"):
    os.makedirs(d, exist_ok=True)
os.chdir("/work")
if "/work/scripts" not in sys.path:
    sys.path.insert(0, "/work/scripts")
`);
}

async function fetchAndWriteScripts() {
  el.engineStatus.textContent = "Loading conversion scripts…";
  for (const file of ALL_SCRIPT_FILES) {
    const res = await fetch(SCRIPTS_BASE + file);
    if (!res.ok) {
      throw new Error(
        `Couldn't load ${SCRIPTS_BASE + file} (HTTP ${res.status}). ` +
          `Make sure the scripts/ folder was deployed alongside index.html.`
      );
    }
    const text = await res.text();
    // Mirrors convert.sh's `sed s|/home/claude/work|$WORKDIR|g` — the
    // scripts hardcode this path internally; we just retarget it.
    const patched = text.replaceAll("/home/claude/work", "/work");
    pyodide.FS.writeFile(`/work/scripts/${file}`, patched);
  }
}

function startEngineBoot() {
  engineReady = (async () => {
    try {
      await loadPyodideRuntime();
      await prepareVirtualFilesystem();
      await fetchAndWriteScripts();
      el.engineStatus.textContent = "Engine ready.";
      el.engineStatus.classList.add("ready");
      engineIsReady = true;
      updateConvertEnabled();
    } catch (err) {
      engineError = err;
      el.engineStatus.textContent = `Couldn't finish loading: ${err.message}`;
      el.engineStatus.classList.add("error");
      throw err;
    }
  })();
  // Don't let a rejected boot promise surface as an unhandled rejection —
  // runConversion() awaits engineReady itself and will surface the error.
  engineReady.catch(() => {});
}

// ---------------------------------------------------------------------------
// Conversion flow
// ---------------------------------------------------------------------------

async function runStage(file) {
  await pyodide.runPythonAsync(`
import runpy
runpy.run_path("/work/scripts/${file}", run_name="__main__")
`);
}

async function runConversion() {
  showPanel("converting");
  el.log.textContent = "";
  setStageProgress(0, STAGE_ORDER.length, "Starting…");

  await engineReady;
  if (engineError) throw engineError;

  log("Resetting work directory…");
  await pyodide.runPythonAsync(`
import shutil, os, glob
if os.path.isdir("/work/output_pack"):
    shutil.rmtree("/work/output_pack")
for f in glob.glob("/work/report_stage*.json") + glob.glob("/work/report_final*.json"):
    os.remove(f)
`);

  log("Reading your 1.8.9 pack…");
  const oldBytes = new Uint8Array(await oldPackFile.arrayBuffer());
  pyodide.FS.writeFile("/work/old_pack.zip", oldBytes);

  if (!EXPECT_BUNDLED_REFERENCE_PACK) {
    log("Reading the 26.1.2 reference pack…");
    const newBytes = new Uint8Array(await newPackFile.arrayBuffer());
    pyodide.FS.writeFile("/work/new_pack.zip", newBytes);
  }

  log("Extracting both packs…");
  await runStage("_harness_extract.py");

  for (let i = 0; i < STAGE_ORDER.length; i++) {
    const stage = STAGE_ORDER[i];
    setStageProgress(i, STAGE_ORDER.length, stage.label);
    log(`Stage ${i + 1}/${STAGE_ORDER.length} — ${stage.file}: ${stage.label}`);
    try {
      await runStage(stage.file);
    } catch (err) {
      const msg = String((err && err.message) || err).split("\n")[0];
      throw new Error(`Stage "${stage.label}" (${stage.file}) failed: ${msg}`);
    }
  }
  setStageProgress(STAGE_ORDER.length, STAGE_ORDER.length, "Packaging…");

  log("Packaging the result…");
  await runStage("_harness_finalize.py");

  const summaryText = pyodide.FS.readFile("/work/summary.json", { encoding: "utf8" });
  return JSON.parse(summaryText);
}

function downloadFromFS(path, filename, mime) {
  const bytes = pyodide.FS.readFile(path); // Uint8Array
  const blob = new Blob([bytes], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30_000);
}

function renderSummary(summary) {
  el.summary.innerHTML = "";
  const addChip = (label, value) => {
    const d = document.createElement("div");
    d.className = "stat-chip";
    d.innerHTML = `<strong>${value}</strong><span>${label}</span>`;
    el.summary.appendChild(d);
  };

  addChip("matched from your pack", summary.matched_total);
  addChip("kept from 26.1.2", summary.unmatched_total);

  const seen = new Set();
  for (const key of METHOD_DISPLAY_ORDER) {
    if (summary.by_method[key]) {
      addChip(key, summary.by_method[key]);
      seen.add(key);
    }
  }
  // Anything not in the fixed display order still gets shown, so the
  // chips always add up to matched_total.
  const rest = Object.entries(summary.by_method)
    .filter(([k]) => !seen.has(k))
    .sort((a, b) => b[1] - a[1]);
  for (const [key, count] of rest) addChip(key, count);
}

// ---------------------------------------------------------------------------
// Event wiring
// ---------------------------------------------------------------------------

function setOldPackFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".zip") && !file.name.toLowerCase().endsWith(".jar")) {
    log(`"${file.name}" doesn't look like a pack — please pick a proper pack.`);
    return;
  }
  oldPackFile = file;
  el.fileName.textContent = file.name;
  updateConvertEnabled();
}

el.dropZone.addEventListener("click", () => el.fileInput.click());
el.dropZone.addEventListener("keydown", (e) => {
  // The real <input type=file> is visually hidden, which also removes it
  // from the tab order — so Enter/Space on the styled drop zone needs to
  // open the picker itself rather than relying on native input behavior.
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    el.fileInput.click();
  }
});
el.dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  el.dropZone.classList.add("drag-over");
});
el.dropZone.addEventListener("dragleave", () => el.dropZone.classList.remove("drag-over"));
el.dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  el.dropZone.classList.remove("drag-over");
  setOldPackFile(e.dataTransfer.files[0]);
});
el.fileInput.addEventListener("change", (e) => setOldPackFile(e.target.files[0]));

el.convertBtn.addEventListener("click", async () => {
  if (!oldPackFile) return;
  el.convertBtn.disabled = true;
  try {
    const summary = await runConversion();
    renderSummary(summary);
    showPanel("success");
    el.downloadPack.onclick = () =>
      downloadFromFS(
        "/work/1.8.9-legacy-textures-26.1.2.zip",
        "1.8.9-legacy-textures-26.1.2.zip",
        "application/zip"
      );
    el.downloadReport.onclick = () =>
      downloadFromFS("/work/mapping_data.json", "mapping_data.json", "application/json");
  } catch (err) {
    el.errorMessage.textContent = err.message || String(err);
    showPanel("error");
  } finally {
    updateConvertEnabled();
  }
});

function resetToUpload() {
  oldPackFile = null;
  newPackFile = null;
  el.fileInput.value = "";
  el.fileName.textContent = "";
  const name2 = $("#file-name-2");
  const input2 = $("#file-input-2");
  if (name2) name2.textContent = "";
  if (input2) input2.value = "";
  updateConvertEnabled();
  showPanel("upload");
}

el.resetBtn.addEventListener("click", resetToUpload);
$("#reset-btn-error")?.addEventListener("click", resetToUpload);

// Kick things off (WITHOUT auto-loading the heavy Python engine)
buildSecondUploadSlotIfNeeded();
updateConvertEnabled();

let engineBootTriggered = false;

function ensureEngineBooting() {
  if (engineBootTriggered) return;
  engineBootTriggered = true;
  
  // Remove listeners so it only triggers once
  document.removeEventListener('click', ensureEngineBooting);
  document.removeEventListener('touchstart', ensureEngineBooting);
  document.removeEventListener('keydown', ensureEngineBooting);
  
  startEngineBoot();
}

// Start loading on the very first user interaction anywhere on the page
document.addEventListener('click', ensureEngineBooting);
document.addEventListener('touchstart', ensureEngineBooting); // Mobile support
document.addEventListener('keydown', ensureEngineBooting);   // Keyboard/Accessibility support

// SAFEGUARD: If the user's very first action is clicking "Convert", 
// this ensures the engine starts loading before runConversion tries to use it.
const _originalRunConversion = runConversion;
runConversion = async function(...args) {
  ensureEngineBooting();
  return await _originalRunConversion(...args);
};
