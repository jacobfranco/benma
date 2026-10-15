// Exact saved-analysis replay; all API calls mocked, private WAVs stay local.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const newest = process.env.BENMA_NEWEST_PHYSICAL === '1';
const fixtures = require(newest ? '../src/__tests__/fixtures/pitchRobustnessPhysical.json' : '../src/__tests__/fixtures/toneClassificationPhysical.json');
const provenance = require(newest ? '../../../docs/research/pronunciation-v2/2026-10-13-natural-acceptance/physical-provenance.json' : '../../../docs/research/pronunciation-v2/2026-10-12-learner-classification/physical-provenance.json');
const { load } = require('../../../benchmark/pronunciation_v2/tone_feedback.cjs');
const { pronunciationChunks, chunkPitch } = load('@/speech/pronunciationChunks');
const { shapeDisplay } = load('@/speech/pitchShapeDisplay');
const { normalizedGeometry } = load('@/components/PitchPlot');
const audioRoot = process.env.BENMA_AUDIO_ROOT || path.resolve(__dirname, '../../../services/api/var/audio');
const output = process.env.BENMA_BROWSER_OUTPUT || '/tmp/benma-classification/browser';
const plotLabel = 'Pitch shape across the selected spoken span; gaps mean missing pitch';
fs.mkdirSync(output, { recursive: true });
(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/chromium', args: [
    '--no-sandbox', '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream',
  ] });
  const review = [];
  try {
    for (const [take, physical] of fixtures.entries()) {
      const meta = provenance.find(p => p.id === physical.id);
      const canonical = fs.readFileSync(path.join(audioRoot, meta.storage_key));
      assert.equal(createHash('sha256').update(canonical).digest('hex'), meta.audio_sha256);
      const chunks = pronunciationChunks(physical.data);
      for (const width of [320, 390, 412]) {
        const context = await browser.newContext({ viewport: { width, height: 844 }, hasTouch: true, isMobile: true });
        const page = await context.newPage(), errors = [], graphs = [], audioCalls = [];
        page.on('pageerror', e => errors.push(String(e)));
        await page.addInitScript(() => localStorage.setItem('benma.auth.session-token', 'offline-classification'));
        await page.route('**/v1/**', async route => {
          const url = new URL(route.request().url()), p = url.pathname;
          const json = data => route.fulfill({ json: data });
          if (p === '/v1/me') return json({ id: 'offline' });
          if (p === '/v1/utterances') return json({ id: physical.utterance_id });
          if (p.endsWith('/perceptions')) return json({ id: physical.perception_run_id, utterance_id: physical.utterance_id,
            transcript: physical.alignment_reference_text, status: 'succeeded' });
          if (p.endsWith('/speech-analysis')) return json(physical);
          if (p.endsWith('/readings')) return json({ syllables: physical.data.syllables });
          if (p.endsWith('/audio')) {
            assert(p.includes(physical.utterance_id)); audioCalls.push(url.search);
            return route.fulfill({ contentType: 'audio/wav', body: canonical });
          }
          return route.fulfill({ status: 404, json: { detail: p } });
        });
        const click = name => page.getByRole('button', { name, exact: true }).click();
        const detail = page.getByTestId('selected-pronunciation-detail');
        const dialog = page.getByRole('dialog');
        const screenshot = name => page.screenshot({ path: `${output}/${take}-${width}-${name}.png`, fullPage: true });
        const play = async text => {
          await click(`Play my recording for ${text}`);
          const pause = page.getByRole('button', { name: `Pause my recording for ${text}`, exact: true });
          await pause.waitFor(); await pause.click();
        };
        await page.goto(process.env.BENMA_WEB_URL || 'http://127.0.0.1:8098');
        await click('Open Practice'); await click('Record'); await page.waitForTimeout(250);
        await click('Stop recording'); await detail.waitFor();
        const grades = take === 0 ? ['Pitch unavailable', newest ? 'Pitch unavailable' : 'Pitch acceptable', 'Pitch unavailable', 'Pitch unavailable']
          : ['Pitch acceptable', newest ? 'Pitch differs' : 'Pitch may be off', 'Pitch acceptable', 'Pitch acceptable'];
        const tones = take === 0 ? ['Tone unclear', newest ? 'Tone unclear' : 'Most like Tone 3', 'Tone unclear']
          : ['Most like Tone 3', 'Most like Tone 4', 'Most like Tone 3'];
        for (const index of [0, 1, 2, 3, 0]) {
          const selected = page.getByTestId(`pronunciation-unit-${index}`), chunk = chunks[index];
          await selected.click();
          assert.equal(await selected.getAttribute('aria-label'), `${chunk.text}, pronunciation chunk, ${grades[index]}`);
          if (index < 3) assert(await detail.getByText(tones[index], { exact: true }).isVisible());
          if (newest && take === 1 && [0, 2].includes(index)) assert(await detail.getByText('Dip is shallow.', { exact: true }).isVisible());
          if (!newest && take === 1 && index === 1) {
            const copy = await detail.innerText();
            assert(copy.includes('may differ') && copy.includes('a tone error is not clear'));
            assert(!copy.includes('Expected low or dipping pitch; yours fell.'));
            assert.equal(await detail.getByLabel('Pitch differs', { exact: true }).count(), 0);
          }
          const plot = detail.getByLabel(plotLabel, { exact: true }), rect = await plot.boundingBox();
          const { layout, domain } = shapeDisplay(chunkPitch(physical.data, chunk).segments, chunk.start, chunk.end);
          const segments = normalizedGeometry(layout, rect.width - 8, 88, domain)
            .map(s => s.map(p => ({ x: p.x + 4, y: p.y + 4 })));
          const expected = segments.flatMap(s => s.slice(1).map((p, i) => [s[i], p]));
          const lines = plot.getByTestId('contour-line');
          assert.equal(await lines.count(), expected.length);
          const actual = await lines.evaluateAll(nodes => nodes.map(n => {
            const style = getComputedStyle(n), transform = new DOMMatrix(style.transform);
            const length = parseFloat(style.width), x = parseFloat(style.left) + length / 2, y = parseFloat(style.top) + 1;
            return [{ x: x - transform.a * length / 2, y: y - transform.b * length / 2 },
              { x: x + transform.a * length / 2, y: y + transform.b * length / 2 }];
          }));
          for (let i = 0; i < expected.length; i++) for (let j = 0; j < 2; j++) for (const axis of ['x', 'y'])
            assert(Math.abs(actual[i][j][axis] - expected[i][j][axis]) < .1);
          assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
          assert.equal(rect.height, 96);
          graphs.push({ text: chunk.text, points: layout.segments.map(s => s.length), lines: expected.length, sourceCoordinatesMatch: true });
          await screenshot(`unit-${index}`);
        }
        await page.getByTestId('pronunciation-unit-3').click(); await play('这个');
        await click('More details'); await dialog.waitFor();
        for (const [index, text] of [[3, '这'], [4, '个']]) {
          await page.getByTestId(`chunk-constituent-${index}`).click();
          const panel = page.getByTestId('selected-constituent-detail');
          assert(await panel.getByLabel(index === 3 && take === 1 ? 'Pitch acceptable' : 'Pitch unavailable', { exact: true }).isVisible());
          if (index === 4) {
            assert.equal(await panel.getByLabel(plotLabel, { exact: true }).count(), take === 0 || newest ? 1 : 0);
            assert(!(await panel.innerText()).includes('Neutral syllable plausibly realized'));
            assert((await panel.innerText()).includes('does not veto'));
          }
          await play(text); await screenshot(`constituent-${index}`);
        }
        await click('Technical details');
        assert((await dialog.innerText()).includes(take === 0 || newest ? 'neutral_unreliable_nonveto' : 'neutral_unmeasured_nonveto'));
        await page.keyboard.press('Escape'); await dialog.waitFor({ state: 'hidden' });
        await click('History'); await click('Open attempt 1');
        await page.getByTestId('pronunciation-unit-3').click();
        assert.equal(await page.getByTestId('pronunciation-unit-3').getAttribute('aria-label'), `这个, pronunciation chunk, ${grades[3]}`);
        await play('这个');
        assert(audioCalls.includes('?canonical=true')); assert.deepEqual(errors, []);
        review.push({ id: physical.id, width, graphs, neutralUnavailableNonVeto: true, canonicalPlayback: true, history: true, errors });
        await context.close();
      }
    }
    fs.writeFileSync(`${output}/review.json`, JSON.stringify(review, null, 2) + '\n');
    console.log(JSON.stringify(review, null, 2));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
