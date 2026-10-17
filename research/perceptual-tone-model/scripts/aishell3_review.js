/* Local-only alignment playback QA. Corpus tone labels are never edited. */
"use strict";
const packet = JSON.parse(document.getElementById("packet").textContent);
const storageKey = `aishell3-playback-${packet.packet_sha256}`;
let answers = {};
const reviewer = document.getElementById("reviewer");
const message = document.getElementById("message");
try {
  const saved = JSON.parse(localStorage.getItem(storageKey) || "null");
  if (saved) { answers = saved.answers || {}; reviewer.value = saved.reviewer || ""; }
} catch { message.textContent = "Local storage unavailable. Export a draft before closing this page."; }
const sections = [...document.querySelectorAll("section[data-id]")];
function persist() {
  try { localStorage.setItem(storageKey, JSON.stringify({ answers, reviewer: reviewer.value })); }
  catch { message.textContent = "Local storage unavailable. Export a draft before closing this page."; }
  document.getElementById("progress").textContent = `${Object.values(answers).filter(a => a.decision && a.heard_context_and_target).length} / ${packet.items.length} decisions recorded`;
}
function render() {
  for (const section of sections) {
    const answer = answers[section.dataset.id] || {};
    section.querySelector("select").value = answer.decision || "";
    section.querySelector("textarea").value = answer.notes || "";
    section.querySelector('input[type="checkbox"]').checked = answer.heard_context_and_target === true;
  }
  persist();
}
for (const section of sections) {
  const save = () => {
    answers[section.dataset.id] = {
      decision: section.querySelector("select").value,
      notes: section.querySelector("textarea").value,
      heard_context_and_target: section.querySelector('input[type="checkbox"]').checked,
      reviewed_at: new Date().toISOString(),
    };
    persist();
  };
  section.querySelector("select").addEventListener("change", save);
  section.querySelector("textarea").addEventListener("input", save);
  section.querySelector('input[type="checkbox"]').addEventListener("change", save);
  for (const button of section.querySelectorAll("button[data-view]")) {
    button.addEventListener("click", async () => {
      document.querySelectorAll("audio").forEach(audio => audio.pause());
      const audio = section.querySelector(`audio[data-view="${button.dataset.view}"]`);
      audio.currentTime = 0;
      try { await audio.play(); }
      catch (error) { message.textContent = `Playback failed: ${error.message}. Try the native audio controls or localhost command.`; }
    });
  }
}
reviewer.addEventListener("input", persist);
function exportReview(requireComplete) {
  const reviews = packet.items.map(item => ({
    ...(answers[item.row.example_id] || {}),
    example_id: item.row.example_id,
    item_sha256: item.item_sha256,
    reviewer: reviewer.value.trim(),
  })).filter(review => review.decision);
  const complete = reviewer.value.trim() && reviews.length === packet.items.length && reviews.every(review =>
    review.heard_context_and_target === true && review.reviewed_at &&
    (review.decision === "PASS" || (review.notes || "").trim()));
  if (requireComplete && !complete) {
    message.textContent = "Enter your name, listen and confirm both clips, choose a decision for every target, and add notes for every non-PASS.";
    return;
  }
  const blob = new Blob([JSON.stringify({schema: packet.schema, packet_sha256: packet.packet_sha256, reviews}, null, 2) + "\n"], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = requireComplete ? "aishell3-playback-decisions.json" : "aishell3-playback-draft.json";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  message.textContent = requireComplete ? "Exported decisions. Ingestion checks hashes and all 26 targets. Any non-PASS blocks training." : "Draft exported; incomplete drafts cannot clear the gate.";
}
document.getElementById("export").addEventListener("click", () => exportReview(true));
document.getElementById("draft").addEventListener("click", () => exportReview(false));
document.getElementById("import").addEventListener("change", async event => {
  try {
    const file = event.target.files[0];
    if (!file) return;
    const data = JSON.parse(await file.text());
    if (data.packet_sha256 !== packet.packet_sha256) throw new Error("This file belongs to a different packet.");
    const expected = new Map(packet.items.map(item => [item.row.example_id, item.item_sha256]));
    const imported = {};
    for (const answer of data.reviews) {
      if (expected.get(answer.example_id) !== answer.item_sha256 || imported[answer.example_id]) throw new Error("Unknown, duplicate or changed target.");
      if (!packet.decisions.includes(answer.decision)) throw new Error("Invalid decision.");
      imported[answer.example_id] = answer;
    }
    answers = imported;
    reviewer.value = data.reviews[0]?.reviewer || "";
    render();
    message.textContent = "Imported. Review and export when complete.";
  } catch (error) { message.textContent = error.message; }
});
render();
