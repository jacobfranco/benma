/* Offline Chromium regression. Run against Expo web with:
 * PLAYWRIGHT_MODULE=/path/to/playwright node scripts/practice-browser.cjs
 * Every API response is intercepted; this never calls speech providers.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { chromium, devices } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const evidence = JSON.parse(fs.readFileSync(require('node:path').resolve(__dirname, '../../../docs/calibration/2026-09-21/three-known-target-samples.json'), 'utf8'));
const acceptance = require('../src/__tests__/fixtures/learnerAcceptance.json');
const origin = process.env.BENMA_WEB_URL || 'http://localhost:8082';
const output = process.env.BENMA_BROWSER_OUTPUT || '/tmp/benma-practice-browser';
fs.mkdirSync(output, { recursive: true });
function silentWav() {
  const b = Buffer.alloc(3244);
  b.write('RIFF'); b.writeUInt32LE(b.length - 8, 4); b.write('WAVEfmt ', 8);
  b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22);
  b.writeUInt32LE(16000, 24); b.writeUInt32LE(32000, 28); b.writeUInt16LE(2, 32);
  b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(3200, 40);
  return b;
}
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    args: ['--no-sandbox', '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] });
  try {
    for (const mobile of [false, true]) {
      const context = await browser.newContext(mobile ? devices['Pixel 7'] : {});
      const page = await context.newPage();
      const errors = [], calls = [];
      page.on('pageerror', error => errors.push(String(error)));
      await page.addInitScript(() => localStorage.setItem('benma.auth.session-token', 'offline-browser-fixture'));
      let scenario = null;
      let target, upload = 0, attempts = 0, free = 0;
      await page.route('**/v1/**', async route => {
        const request = route.request(), path = new URL(request.url()).pathname;
        calls.push({ path, body: request.method() === 'POST' && !path.endsWith('/utterances') ? request.postDataJSON() : null });
        const json = data => route.fulfill({ json: data });
        if (path === '/v1/pronunciation-targets') {
          target = { id: `target-${request.postDataJSON().text}`, text: request.postDataJSON().text,
            display_pinyin: ({ '妈': 'mā', '麻': 'má', '马': 'mǎ', '骂': 'mà' }[request.postDataJSON().text] || 'ma'),
            pinyin_syllables: [({ '妈': 'ma1', '麻': 'ma2', '马': 'ma3', '骂': 'ma4' }[request.postDataJSON().text] || 'ma5')] };
          return json(target);
        }
        if (path.endsWith('/reference-speech')) return json({ id: 'reference', status: 'succeeded',
          audio_url: '/v1/reference-speech/reference/audio', generation_config: { evidence_status: 'synthetic_replay' } });
        if (path.endsWith('/audio')) return route.fulfill({ contentType: 'audio/wav', body: silentWav() });
        if (path === '/v1/utterances') return json({ id: `utterance-${++upload}` });
        if (path.endsWith('/perceptions')) return json({ id: `perception-${upload}`, utterance_id: `utterance-${upload}`,
          transcript: '妈', status: 'succeeded', normalized_result: { evidence_status: 'synthetic_replay' } });
        if (path === '/v1/pronunciation-attempts') {
          assert.equal(request.postDataJSON().target_id, target.id);
          return json({ id: `attempt-${++attempts}` });
        }
        if (path.endsWith('/analyze')) {
          const row = evidence[target.text === '妈' ? 2 : 1];
          const source = row.before.syllables[0];
          const chosen = scenario;
          return json({ target, attempt: { id: `attempt-${attempts}` },
            assessment: { normalized_result: { evidence_status: 'synthetic_replay' } },
            syllables: [{ syllable_index: 0, characters: target.text, pinyin: target.pinyin_syllables[0],
              lexical_tone: chosen?.tone ?? source.lexical_tone, expected_surface_tone: chosen?.tone ?? source.expected_surface_tone,
              timing: { start_seconds: source.start_seconds, end_seconds: source.end_seconds },
              display_contour: chosen?.display ?? row.simplified_display, observed_contour: chosen?.observed ?? row.after }],
            display_contour: row.full_display,
            overall_evidence: { recording_quality: { status: 'invalid_for_interpretation' } }, recording_audio_url: `/v1/utterances/utterance-${upload}/audio` });
        }
        if (path.endsWith('/speech-analysis')) { free++; return route.fulfill({ status: 503, json: { detail: 'offline fixture' } }); }
        return route.fulfill({ status: 404, json: { detail: 'unhandled offline fixture' } });
      });
      const click = async name => {
        const button = page.getByRole('button', { name, exact: true }).last();
        if (mobile) await button.tap(); else await button.click({ delay: 250 });
      };
      await page.goto(origin);
      await click('Open Practice');
      await page.screenshot({ path: `${output}/${mobile ? 'touch' : 'mouse'}-before.png` });
      if (mobile) await click('Add a target phrase');
      else await page.getByRole('button', { name: 'Add a target phrase', exact: true }).dblclick({ delay: 100 });
      const input = page.getByRole('textbox', { name: 'Target phrase', exact: true });
      await input.waitFor();
      await input.fill('妈');
      await click('Prepare target');
      await page.getByRole('button', { name: '▶ Native reference', exact: true }).waitFor();
      await page.screenshot({ path: `${output}/${mobile ? 'touch' : 'mouse'}-prepared.png` });
      for (let index = 0; index < 3; index++) {
        await click('Tap to speak'); await page.waitForTimeout(300); await click('Stop recording');
        await page.getByText('Experimental pronunciation analysis', { exact: true }).nth(index).waitFor();
        assert.equal(await page.getByText('Recording for target: 妈 mā', { exact: true }).count(), 1);
        await click('▶ Native reference');
        await page.waitForTimeout(250);
        const mine = page.getByRole('button', { name: '▶ Mine', exact: true }).last();
        if (mobile) await mine.tap(); else await mine.click();
        await page.waitForTimeout(250);
        if (index === 0) {
          await page.getByLabel('Expected and mine by syllable', { exact: true }).scrollIntoViewIfNeeded();
          const plot = page.getByLabel('Relative pitch contour', { exact: true }).last();
          const coreLines = await plot.getByTestId('contour-line').count();
          assert(coreLines > 0 && coreLines < evidence[2].simplified_display.segments.flat().length - 1);
          await page.screenshot({ path: `${output}/${mobile ? 'touch' : 'mouse'}-contour.png` });
          await click('More detail');
          await page.getByText('Whole utterance · full contour including onset', { exact: true }).waitFor();
          await page.getByLabel('Relative pitch contour', { exact: true }).nth(1).getByTestId('contour-line').nth(coreLines).waitFor();
          await page.screenshot({ path: `${output}/${mobile ? 'touch' : 'mouse'}-full-evidence.png` });
          await click('Less detail');
        }
      }
      assert.equal(attempts, 3); assert.equal(free, 0);
      await click('Change target');
      await input.waitFor();
      assert.equal(await page.getByRole('button', { name: 'Tap to speak', exact: true }).isDisabled(), true);
      await input.fill('吗');
      await click('Prepare target');
      await page.getByText('Neutral tone has context-dependent pitch. Reference pronunciation is one natural realization, not a fixed expected contour.', { exact: true }).waitFor();
      await click('Tap to speak'); await page.waitForTimeout(300); await click('Stop recording');
      await page.getByText('Neutral tone', { exact: true }).waitFor();
      await page.getByText('Context-dependent', { exact: true }).waitFor();
      await page.getByText('Tone 4-like', { exact: true }).waitFor();
      assert.equal(await page.getByText('Recording for target: 吗 ma', { exact: true }).count(), 1);
      await page.getByLabel('Expected and mine by syllable', { exact: true }).last().scrollIntoViewIfNeeded();
      await page.screenshot({ path: `${output}/${mobile ? 'touch' : 'mouse'}-neutral.png` });
      const shapes = { 1: [0,.1,0,.1,0], 2: [-2,-1,0,1,2], 3: [2,0,-2,0,2], 4: [2,1,0,-1,-2] };
      for (const [name, tone, measured] of [['tone1',1,1],['tone2',2,2],['tone3',3,3],['tone4',4,4],['different',2,4],['unclear',3,0],['neutral',0,2]]) {
        await click('Change target');
        await input.fill(tone === 0 ? '嘛' : ['','妈','麻','马','骂'][tone]);
        await click('Prepare target');
        scenario = { tone, observed: measured ? { ...acceptance.find(r => r.observed.classification === `${measured}-like`).observed } : { classification: 'unclear', reason: 'tracker_instability', confidence: 'low' },
          display: { segments: [shapes[measured || 1].map((v,i) => ({ timestamp_seconds: .5+i*.01, normalized_semitones: v }))] } };
        await click('Tap to speak'); await page.waitForTimeout(300); await click('Stop recording');
        await page.getByText('Experimental pronunciation analysis', { exact: true }).last().waitFor();
        if (name.startsWith('tone')) await page.getByText(`Tone ${tone} ✓`, { exact: true }).waitFor();
        if (name === 'different') await page.getByText('Expected Tone 2. Yours sounded more like Tone 4', { exact: true }).waitFor();
        if (name === 'unclear') await page.getByText('Couldn’t judge this one clearly. Try a steady recording.', { exact: true }).waitFor();
        await page.getByLabel('Expected and mine by syllable', { exact: true }).last().scrollIntoViewIfNeeded();
        await page.screenshot({ path: `${output}/${mobile ? 'touch' : 'mouse'}-${name}.png` });
        await click('More detail');
        await page.getByText('Evidence confidence:', { exact: false }).last().waitFor();
        await page.screenshot({ path: `${output}/${mobile ? 'touch' : 'mouse'}-${name}-detail.png` });
        await click('Less detail');
      }
      await click('Clear target · use free practice');
      await page.getByText('Free practice: speak without a target phrase.', { exact: true }).waitFor();
      await click('Tap to speak'); await page.waitForTimeout(300); await click('Stop recording');
      await page.getByText('Speech analysis unavailable', { exact: false }).waitFor();
      assert.equal(attempts, 11); assert.equal(free, 1); assert.deepEqual(errors, []);
      fs.writeFileSync(`${output}/${mobile ? 'touch' : 'mouse'}-calls.json`, JSON.stringify(calls, null, 2));
      console.log(`${mobile ? 'touch' : 'mouse'}: target input, reference, 11 known-target assessments, reliable-core/full graphs, neutral shape, persistence, free practice PASS`);
      await context.close();
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
