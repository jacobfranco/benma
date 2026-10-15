// Offline visual replay of the saved fragmented physical take at mobile widths.
// Serve an Expo web export via BENMA_WEB_URL. No live API/provider requests.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const physical = require('../../../services/api/tests/fixtures/pitch_measurement_430fcc2e.json');
const { load } = require('../../../benchmark/pronunciation_v2/tone_feedback.cjs');
const { pronunciationChunks, chunkPitch } = load('@/speech/pronunciationChunks');
const { shapeDisplay } = load('@/speech/pitchShapeDisplay');
const { normalizedGeometry } = load('@/components/PitchPlot');
const output = process.env.BENMA_BROWSER_OUTPUT || '/tmp/benma-measurement/browser';
fs.mkdirSync(output, { recursive: true });
(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/chromium', args: [
    '--no-sandbox', '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream',
  ] });
  const review = [], chunks = pronunciationChunks(physical.data);
  try {
    for (const width of [320, 390, 412]) {
      const context = await browser.newContext({ viewport: { width, height: 844 }, hasTouch: true, isMobile: true });
      const page = await context.newPage(), errors = [], graphs = [];
      page.on('pageerror', e => errors.push(String(e)));
      await page.addInitScript(() => localStorage.setItem('benma.auth.session-token', 'offline-measurement-audit'));
      await page.route('**/v1/**', async route => {
        const p = new URL(route.request().url()).pathname;
        const json = data => route.fulfill({ json: data });
        if (p === '/v1/me') return json({ id: 'offline' });
        if (p === '/v1/utterances') return json({ id: physical.utterance_id });
        if (p.endsWith('/perceptions')) return json({ id: 'offline', utterance_id: physical.utterance_id,
          transcript: physical.alignment_reference_text, status: 'succeeded' });
        if (p.endsWith('/speech-analysis')) return json({ ...physical, perception_run_id: 'offline', status: 'succeeded' });
        if (p.endsWith('/readings')) return json({ syllables: physical.data.syllables });
        return route.fulfill({ status: 404, json: { detail: p } });
      });
      const click = name => page.getByRole('button', { name, exact: true }).click();
      await page.goto(process.env.BENMA_WEB_URL || 'http://127.0.0.1:8097');
      await click('Open Practice'); await click('Record'); await page.waitForTimeout(250);
      await click('Stop recording');
      const detail = page.getByTestId('selected-pronunciation-detail'); await detail.waitFor();
      for (const index of [0, 1, 2, 3, 0]) {
        await page.getByTestId(`pronunciation-unit-${index}`).click();
        const plot = detail.getByLabel('Pitch shape across the selected spoken span; gaps mean missing pitch', { exact: true });
        const rect = await plot.boundingBox(), chunk = chunks[index];
        const { layout, domain } = shapeDisplay(chunkPitch(physical.data, chunk).segments, chunk.start, chunk.end);
        // Match React Native Web's onLayout border-box measurement.
        const innerWidth = rect.width;
        const segments = normalizedGeometry(layout, innerWidth - 8, 88, domain)
          .map(s => s.map(p => ({ x: p.x + 4, y: p.y + 4 })));
        const expected = segments.flatMap(s => s.slice(1).map((p, i) => [s[i], p]));
        const lines = plot.getByTestId('contour-line');
        assert.equal(await lines.count(), expected.length, 'Stale, missing or invented line');
        const actual = await lines.evaluateAll(nodes => nodes.map(n => {
          const style = getComputedStyle(n), transform = new DOMMatrix(style.transform);
          const length = parseFloat(style.width), x = parseFloat(style.left) + length / 2, y = parseFloat(style.top) + 1;
          return [{ x: x - transform.a * length / 2, y: y - transform.b * length / 2 },
            { x: x + transform.a * length / 2, y: y + transform.b * length / 2 }];
        }));
        for (let i = 0; i < expected.length; i++) for (let j = 0; j < 2; j++) for (const axis of ['x', 'y'])
          assert(Math.abs(actual[i][j][axis] - expected[i][j][axis]) < .1, `${chunk.text}: rendered ${axis} differs from owned source projection`);
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        assert.equal(rect.height, 96);
        graphs.push({ text: chunk.text, points: layout.segments.map(s => s.length), lines: expected.length, sourceCoordinatesMatch: true });
        await page.screenshot({ path: `${output}/${width}-unit-${index}.png`, fullPage: true });
      }
      assert.deepEqual(errors, []);
      review.push({ width, graphs, errors, overflow: false });
      await context.close();
    }
    fs.writeFileSync(`${output}/review.json`, JSON.stringify(review, null, 2) + '\n');
    console.log(JSON.stringify(review, null, 2));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
