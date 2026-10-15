// Offline fresh-take and constructed tone feedback review. All API calls mocked.
// Serve a fresh export via BENMA_WEB_URL; BENMA_TONE_AUDIO points to the exact
// private canonical WAV. Screenshots stay in /tmp, never in the repository.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const { inputs } = require('../../../benchmark/pronunciation_v2/tone_feedback_audit.cjs');
const root = path.resolve(__dirname, '../../..');
const fresh = JSON.parse(fs.readFileSync(path.join(root, 'apps/mobile/src/__tests__/fixtures/toneFeedbackPhysical.json')));
const canonical = fs.readFileSync(process.env.BENMA_TONE_AUDIO);
assert.equal(createHash('sha256').update(canonical).digest('hex'), fresh.provenance.audio_sha256);
const cases = inputs().analyses;
for (const [id, scale] of [['weak-mismatch', -1], ['moderate-mismatch', -1.6], ['family-competition', .8]]) {
  const a = JSON.parse(JSON.stringify(cases.find(a => a.id === 'constructed:这个-weak')));
  a.id = `constructed:这个-${id}`;
  const head = a.data.syllables[3];
  for (const segment of a.data.tone_graph.filtered.segments) for (const p of segment)
    if (p.timestamp_seconds >= head.start_seconds && p.timestamp_seconds < head.end_seconds)
      p.normalized_semitones *= scale;
  cases.push(a);
}
const output = process.env.BENMA_BROWSER_OUTPUT || '/tmp/benma-tone-feedback/browser';
fs.mkdirSync(output, { recursive: true });
const plotLabel = 'Pitch shape across the selected spoken span; gaps mean missing pitch';
(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/chromium', args: [
    '--no-sandbox', '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream',
  ] });
  const review = [];
  try {
    for (const width of [320, 390, 412]) {
      const context = await browser.newContext({ viewport: { width, height: 844 }, hasTouch: true, isMobile: true });
      const page = await context.newPage(), errors = [], audioCalls = [];
      page.on('pageerror', e => errors.push(String(e)));
      await page.addInitScript(() => { localStorage.setItem('benma.auth.session-token', 'offline-tone-fixture'); });
      let chosen = fresh, turn = 0;
      const attempts = new Map();
      await page.route('**/v1/**', async route => {
        const url = new URL(route.request().url()), p = url.pathname;
        const json = data => route.fulfill({ json: data });
        if (p === '/v1/me') return json({ id: 'offline' });
        if (p === '/v1/utterances') { attempts.set(++turn, chosen); return json({ id: `u${turn}` }); }
        if (p.endsWith('/perceptions')) return json({ id: `p${turn}`, utterance_id: `u${turn}`, transcript: chosen.alignment_reference_text, status: 'succeeded' });
        if (p.endsWith('/speech-analysis')) return json({ ...chosen, id: `a${turn}`, utterance_id: `u${turn}`, perception_run_id: `p${turn}` });
        if (p.endsWith('/readings')) return json({ syllables: chosen.data.syllables });
        if (p.endsWith('/audio')) {
          const attempt = attempts.get(Number(p.match(/\/u(\d+)\//)?.[1]));
          assert.equal(attempt.id, fresh.id, 'Never attach physical audio to a constructed control');
          audioCalls.push(url.search);
          return route.fulfill({ contentType: 'audio/wav', body: canonical });
        }
        return route.fulfill({ status: 404, json: { detail: p } });
      });
      const click = name => page.getByRole('button', { name, exact: true }).click();
      const select = index => page.getByTestId(`pronunciation-unit-${index}`).click();
      const detail = page.getByTestId('selected-pronunciation-detail');
      const dialog = page.getByRole('dialog');
      const record = async (label = 'New Attempt') => {
        await click(label); await page.waitForTimeout(250);
        const response = page.waitForResponse(r => r.url().endsWith('/speech-analysis'));
        await click('Stop recording'); await response; await detail.waitFor();
      };
      const screenshot = name => page.screenshot({ path: `${output}/${width}-${name}.png`, fullPage: true });
      const layout = async () => {
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        for (const item of await page.getByTestId('perceived-sentence-overview').locator('[data-testid^=pronunciation-unit-]').all()) {
          const r = await item.boundingBox(); assert(r.width >= 44 && r.height >= 48 && r.x + r.width <= width);
        }
        const plot = detail.getByLabel(plotLabel, { exact: true });
        const graph = await plot.count() ? await plot.boundingBox() : null;
        if (graph) { assert(graph.width > 80); assert.equal(graph.height, 96); }
        const footer = await page.getByRole('button', { name: 'New Attempt', exact: true }).boundingBox();
        assert(footer.y >= 0 && footer.y + footer.height <= 844);
        return graph;
      };
      const play = async text => {
        await click(`Play my recording for ${text}`);
        const pause = page.getByRole('button', { name: `Pause my recording for ${text}`, exact: true });
        await pause.waitFor(); await pause.click();
      };
      const close = async () => { await page.keyboard.press('Escape'); await dialog.waitFor({ state: 'hidden' }); };
      await page.goto(process.env.BENMA_WEB_URL || 'http://127.0.0.1:8095'); await click('Open Practice'); await record('Record');
      let graphRect;
      for (const [index, name, copy] of [[0, 'wo', 'Tone unclear'], [1, 'xiang', 'Most like Tone 3'], [2, 'poor-mai', 'Tone unclear']]) {
        await select(index); assert(await detail.getByText(copy, { exact: true }).isVisible());
        assert.equal(await page.getByTestId(`pronunciation-unit-${index}`).getAttribute('aria-label'), `${fresh.data.syllables[index].characters}, pronunciation chunk, ${['Pitch unavailable', 'Pitch acceptable', 'Pitch unavailable'][index]}`);
        const rect = await layout();
        if (graphRect) { assert.equal(rect.x, graphRect.x); assert.equal(rect.width, graphRect.width); }
        graphRect = rect; await screenshot(name);
      }
      await select(0); await play('我'); await click('More details'); await dialog.waitFor();
      assert(await dialog.getByText('Measured shape: Dip and rise', { exact: true }).isVisible());
      assert(await dialog.getByText('Connected-speech realization may vary here.', { exact: true }).isVisible());
      assert.equal(await dialog.getByText('Measurement evidence:', { exact: false }).count(), 0);
      await screenshot('wo-details'); await click('Technical details');
      assert((await dialog.innerText()).includes('Measurement evidence:')); await screenshot('technical-details');
      await click('Raw'); assert((await dialog.innerText()).includes('Raw tracker evidence')); await close();
      const chunk = page.getByTestId('pronunciation-unit-3');
      for (const key of ['Enter', 'Space']) { await select(0); await chunk.focus(); await page.keyboard.press(key); assert.equal(await chunk.getAttribute('aria-pressed'), 'true'); }
      assert.equal(await chunk.getAttribute('aria-label'), '这个, pronunciation chunk, Pitch acceptable');
      assert(await detail.getByText('✓ Pitch acceptable', { exact: true }).isVisible());
      assert(!(await detail.innerText()).includes('Pitch detail is limited.'));
      await layout(); await screenshot('green-this-chunk'); await play('这个');
      await click('More details'); await dialog.waitFor();
      for (const index of [3, 4]) {
        await page.getByTestId(`chunk-constituent-${index}`).click();
        const panel = page.getByTestId('selected-constituent-detail');
        assert.equal(await panel.getByLabel(plotLabel, { exact: true }).count(), index === 3 ? 1 : 0);
        assert((await panel.innerText()).includes(index === 3 ? 'Most like Tone 4' : "Pitch couldn't be measured reliably."));
        if (index === 4) assert(!(await panel.innerText()).includes('Tone unclear'));
        await play(index === 3 ? '这' : '个'); await screenshot(index === 3 ? 'constituent-zhe' : 'neutral-ge');
      }
      for (let i = 0; i < 12; i++) { await page.keyboard.press('Tab'); assert(await dialog.evaluate(n => n.contains(document.activeElement))); }
      await close();
      for (const [id, label, message] of [
        ['mismatch', 'Pitch differs', 'Expected a fall; yours rose.'],
        ['unclear', 'Pitch unavailable', "Pitch couldn't be measured reliably."],
        ['weak', 'Pitch acceptable', 'Fall is a little weak.'],
        ['weak-mismatch', 'Pitch acceptable', 'Rise is a little weak.'],
        ['moderate-mismatch', 'Pitch may be off', 'The pitch may differ from what is expected here, but a tone error is not clear.'],
        ['family-competition', 'Pitch may be off', 'The pitch has more than one plausible interpretation; a tone error is not clear.'],
      ]) {
        chosen = cases.find(a => a.id === `constructed:这个-${id}`); await record(); await select(3);
        assert.equal(await chunk.getAttribute('aria-label'), `这个, pronunciation chunk, ${label}`);
        assert((await detail.innerText()).includes(message), `${id}: missing ${message}`);
        if (id === 'weak-mismatch') {
          assert(!(await detail.innerText()).includes('Pitch may be off'));
          await click('More details'); await dialog.waitFor();
          await page.getByTestId('chunk-constituent-3').click();
          const panel = page.getByTestId('selected-constituent-detail');
          assert((await panel.innerText()).includes('Most like Tone 2'));
          assert((await panel.innerText()).includes('There is not enough evidence of a pitch problem here.'));
          assert(await panel.getByLabel('Pitch acceptable', { exact: true }).isVisible());
          await screenshot('this-weak-mismatch-details'); await close();
        }
        if (label === 'Pitch may be off') assert.equal(await detail.getByLabel('Pitch differs', { exact: true }).count(), 0);
        if (id === 'mismatch') {
          const status = detail.getByLabel('Pitch differs', { exact: true });
          const { pitchGradePresentation } = require('../../../benchmark/pronunciation_v2/tone_feedback.cjs').load('@/speech/learnerPitchGrade');
          assert.equal(pitchGradePresentation.CLEAR_DIFFERENCE.color, 'red');
          assert.equal(await status.evaluate(n => getComputedStyle(n).color), 'rgb(163, 35, 50)');
          assert.equal(await status.evaluate(n => getComputedStyle(n).backgroundColor), 'rgb(252, 236, 239)');
          assert((await status.innerText()).includes('≠'));
        }
        await layout(); await screenshot(`this-${id}`);
      }
      for (const id of ['measured-neutral', 'ambiguous-neutral', 'contradictory-neutral']) {
        chosen = cases.find(a => a.id === `constructed:这个-${id}`); await record(); await select(3);
        assert.equal(await chunk.getAttribute('aria-label'), '这个, pronunciation chunk, Pitch acceptable');
        await click('More details'); await dialog.waitFor();
        await page.getByTestId('chunk-constituent-4').click();
        const panel = page.getByTestId('selected-constituent-detail');
        const unreliable = id === 'contradictory-neutral';
        assert((await panel.innerText()).includes(unreliable ? 'Neutral pitch could not be judged reliably' : 'Neutral syllable plausibly realized in this chunk.'));
        assert(await panel.getByLabel(unreliable ? 'Pitch unavailable' : 'Pitch acceptable', { exact: true }).isVisible());
        assert(!(await panel.innerText()).includes('Tone unclear'));
        await screenshot(id); await close();
      }
      // Resolved standalone T3 context is a separate constructed UI control;
      // the actual chain uses an explicit lexical-family fallback.
      chosen = JSON.parse(JSON.stringify(fresh)); chosen.id = 'constructed:resolved-wo';
      chosen.data.syllables[0].expected_surface_tone = 3; chosen.data.syllables[0].surface_rule = 'constructed_resolved_context';
      // The saved 我 has raw branch flags. An independent clean constructed
      // valley exercises green; changing the expectation cannot erase corruption.
      const syllable = chosen.data.syllables[0], start = syllable.start_seconds, end = syllable.end_seconds;
      chosen.data.tone_graph.raw = chosen.data.tone_graph.raw.filter(p => p.timestamp_seconds < start || p.timestamp_seconds >= end);
      chosen.data.tone_graph.filtered.segments = chosen.data.tone_graph.filtered.segments.map(s =>
        s.filter(p => p.timestamp_seconds < start || p.timestamp_seconds >= end)).filter(s => s.length);
      const n = Math.floor((end - start) / .01) - 1;
      chosen.data.tone_graph.filtered.segments.unshift(Array.from({ length: n }, (_, i) => ({
        timestamp_seconds: start + .01 + i * .01, normalized_semitones: 4 * Math.abs(2 * i / (n - 1) - 1),
      })));

      await record(); await select(0); assert.equal(await page.getByTestId('pronunciation-unit-0').getAttribute('aria-label'), '我, pronunciation chunk, Pitch acceptable');
      assert((await detail.innerText()).includes('Most like Tone 3')); await layout(); await screenshot('resolved-t3-green');
      chosen = cases.find(a => a.id === 'saved:grouped-雨伞'); await record(); await select(5);
      assert((await detail.innerText()).includes('Pitch unavailable')); await layout(); await screenshot('grouped-umbrella');
      await click('More details'); await dialog.waitFor();
      assert.equal(await page.getByTestId('selected-constituent-detail').count(), 0);
      assert((await dialog.innerText()).includes('Separate character timing and playback are unavailable.')); await close();
      await click('History'); await click('Open attempt 1'); await select(3);
      assert.equal(await chunk.getAttribute('aria-label'), '这个, pronunciation chunk, Pitch acceptable');
      await play('这个');
      assert(audioCalls.includes('?canonical=true')); assert.deepEqual(errors, []);
      review.push({ width, graphHeight: 96, graphWidth: graphRect.width, freshToneLabels: true, lexicalFamilyFeedback: true,
        neutralGreen: true, measuredNeutralAccepted: true, redControl: true, grayControl: true,
        weakCompatibleGreen: true, weakMismatchGreen: true, moderateMismatchAmber: true, familyCompetitionAmber: true, resolvedT3Green: true,
        groupedTiming: true, details: true, technical: true, canonicalPlayback: true, keyboard: true,
        focusContainment: true, history: true, overflow: false, errors });
      await context.close();
    }
    fs.writeFileSync(`${output}/review.json`, JSON.stringify(review, null, 2) + '\n');
    console.log(JSON.stringify(review, null, 2));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
