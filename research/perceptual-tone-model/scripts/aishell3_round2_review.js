/* Local-only comparison review. Two independent judgments; no release action. */
"use strict";
const packet = JSON.parse(document.getElementById("packet").textContent);
const storageKey = `aishell3-round2-${packet.packet_sha256}`;
const reviewer = document.getElementById("reviewer");
const message = document.getElementById("message");
const sections = [...document.querySelectorAll("section[data-id]")];
let answers = {};
try {
  const saved = JSON.parse(localStorage.getItem(storageKey) || "null");
  if (saved) { answers = saved.answers || {}; reviewer.value = saved.reviewer || ""; }
} catch { message.textContent = "Local storage unavailable. Export a draft before closing."; }
function valid(answer) {
  return packet.decisions.includes(answer.decision) &&
    packet.final_decisions.includes(answer.final_decision) &&
    answer.heard_context_and_target === true && answer.heard_final === true &&
    answer.reviewed_at && ((answer.decision === "PASS" && answer.final_decision === "PASS") ||
      (answer.notes || "").trim());
}
function persist() {
  try { localStorage.setItem(storageKey, JSON.stringify({ answers, reviewer: reviewer.value })); }
  catch { message.textContent = "Local storage unavailable. Export a draft before closing."; }
  document.getElementById("progress").textContent = `${Object.values(answers).filter(valid).length} / ${packet.items.length} complete items`;
}
function render() {
  for (const section of sections) {
    const answer = answers[section.dataset.id] || {};
    for (const select of section.querySelectorAll("select")) select.value = answer[select.dataset.field] || "";
    section.querySelector("textarea").value = answer.notes || "";
    section.querySelector('input[type="checkbox"]').checked = answer.heard_context_and_target === true && answer.heard_final === true;
  }
  persist();
}
for (const section of sections) {
  const save = () => {
    const heard = section.querySelector('input[type="checkbox"]').checked;
    answers[section.dataset.id] = {
      decision: section.querySelector('[data-field="decision"]').value,
      final_decision: section.querySelector('[data-field="final_decision"]').value,
      notes: section.querySelector("textarea").value,
      heard_context_and_target: heard, heard_final: heard, reviewed_at: new Date().toISOString(),
    };
    persist();
  };
  section.querySelectorAll("select,input").forEach(node => node.addEventListener("change", save));
  section.querySelector("textarea").addEventListener("input", save);
  for (const button of section.querySelectorAll("button[data-view]")) {
    button.addEventListener("click", async () => {
      document.querySelectorAll("audio").forEach(audio => audio.pause());
      const audio = section.querySelector(`audio[data-view="${button.dataset.view}"]`);
      audio.currentTime = 0;
      try { await audio.play(); }
      catch (error) { message.textContent = `Playback failed: ${error.message}. Try the native audio controls.`; }
    });
  }
}
reviewer.addEventListener("input", persist);
function exportReview(requireComplete) {
  const reviews = packet.items.map(item => ({
    ...(answers[item.row.example_id] || {}), example_id: item.row.example_id,
    item_sha256: item.item_sha256, reviewer: reviewer.value.trim(),
  })).filter(r => r.decision || r.final_decision);
  if (requireComplete && (!reviewer.value.trim() || reviews.length !== packet.items.length || !reviews.every(valid))) {
    message.textContent = "Enter your name, answer both questions for every item, confirm listening, and add notes when either answer is non-PASS.";
    return;
  }
  const blob = new Blob([JSON.stringify({schema: packet.schema, packet_sha256: packet.packet_sha256, reviews}, null, 2) + "\n"], {type: "application/json"});
  const url = URL.createObjectURL(blob), link = document.createElement("a");
  link.href = url;
  link.download = requireComplete ? "aishell3-round2-decisions.json" : "aishell3-round2-draft.json";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  message.textContent = requireComplete ? "Exported both judgments. Review ingestion does not release data or train a model." : "Draft exported.";
}
document.getElementById("export").addEventListener("click", () => exportReview(true));
document.getElementById("draft").addEventListener("click", () => exportReview(false));
document.getElementById("import").addEventListener("change", async event => {
  try {
    const file = event.target.files[0];
    if (!file) return;
    const data = JSON.parse(await file.text());
    if (data.schema !== packet.schema || data.packet_sha256 !== packet.packet_sha256) throw new Error("This file belongs to a different packet.");
    const expected = new Map(packet.items.map(item => [item.row.example_id, item.item_sha256]));
    const imported = {};
    for (const answer of data.reviews) {
      if (expected.get(answer.example_id) !== answer.item_sha256 || imported[answer.example_id]) throw new Error("Unknown, duplicate or changed target.");
      if ((answer.decision && !packet.decisions.includes(answer.decision)) ||
          (answer.final_decision && !packet.final_decisions.includes(answer.final_decision))) throw new Error("Invalid decision.");
      imported[answer.example_id] = answer;
    }
    answers = imported;
    reviewer.value = data.reviews[0]?.reviewer || "";
    render();
    message.textContent = "Imported. Review and export when complete.";
  } catch (error) { message.textContent = error.message; }
});
render();
