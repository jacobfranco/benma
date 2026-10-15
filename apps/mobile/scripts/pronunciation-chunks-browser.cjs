/* Offline chunk acceptance; no live provider/API calls or copied audio artifacts.
 * Serve a fresh web export at BENMA_WEB_URL. Requires the existing private saved
 * six-take viewer and canonical 89cee47e audio (BENMA_CHUNK_AUDIO may override).
 * PLAYWRIGHT_MODULE=/path/to/playwright node scripts/pronunciation-chunks-browser.cjs
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '../../..');
const read = file => JSON.parse(fs.readFileSync(path.join(root, file)));
const cases = read('apps/mobile/src/__tests__/fixtures/pronunciationChunkCases.json');
const physical = read('services/api/tests/fixtures/pitch_projection_89cee47e.json');
const saved = read('services/api/var/audio-first-feedback/viewer-data.json').recordings;
const canonical = fs.readFileSync(process.env.BENMA_CHUNK_AUDIO || path.join(root,
  'services/api/var/audio/4437ecb5-c693-476c-8cc6-4c51cc910742/canonical/89cee47ede594941baf0f4ad758b971a.wav'));
assert.equal(createHash('sha256').update(canonical).digest('hex'), physical.provenance.audio_sha256);
const candidate = text => {
  const value = cases.find(c => c.text === text);
  return { pronunciation_chunk_policy: value.pronunciation_chunk_policy,
    pronunciation_chunk_candidates: value.pronunciation_chunk_candidates };
};
const thisOne = { perceived_text: '我想买这个', data: { ...physical.data, ...candidate('我想买这个') }, audio: canonical };
const umbrella = saved.find(r => r.id.startsWith('40357072'));
const quantity = saved.find(r => r.id.startsWith('8d252264'));
const oneApple = { ...quantity, data: { ...quantity.data, ...candidate('我要一个苹果') } };
const design = text => {
  const fixture = cases.find(c => c.text === text);
  // Linguistic/layout fixture only: these timings do not claim recorded speech.
  return { perceived_text: text, data: { ...physical.data, ...candidate(text),
    duration_seconds: fixture.syllables.length * .4, timing_groups: [], tone_graph: null, measured_pitch: [],
    syllables: fixture.syllables.map((s, i) => ({ ...s, start_seconds: i * .4, end_seconds: (i + 1) * .4 })),
  } };
};
const output = process.env.BENMA_BROWSER_OUTPUT || '/tmp/benma-chunks-review';
fs.mkdirSync(output, { recursive: true });
(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/chromium', args: [
    '--no-sandbox', '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream',
  ] });
  const summary = [];
  try {
    for (const width of [320, 390, 412]) {
      const context = await browser.newContext({ viewport: { width, height: 844 }, hasTouch: true, isMobile: true });
      const page = await context.newPage(), errors = [], audioCalls = [], attempts = new Map();
      page.on('pageerror', e => errors.push(String(e)));
      await page.addInitScript(() => {
        localStorage.setItem('benma.auth.session-token', 'offline-chunk-fixture');
        window.__playedAudio = [];
        const play = HTMLMediaElement.prototype.play;
        HTMLMediaElement.prototype.play = function () { window.__playedAudio.push(this); return play.call(this); };
      });
      let chosen = thisOne, turn = 0, targetText = '我想买这个';
      const target = () => ({ id: 'target', text: targetText, display_pinyin: 'wǒ xiǎng mǎi zhè ge',
        pinyin_syllables: ['wo3', 'xiang3', 'mai3', 'zhe4', 'ge5'],
        pinyin_alternatives: [['wo3'], ['xiang3'], ['mai3'], ['zhe4'], ['ge5']] });
      await page.route('**/v1/**', async route => {
        const url = new URL(route.request().url()), p = url.pathname;
        const json = data => route.fulfill({ json: data });
        if (p === '/v1/me') return json({ id: 'offline' });
        if (p === '/v1/pronunciation-targets') { targetText = route.request().postDataJSON().text; return json(target()); }
        if (p.endsWith('/reference-speech')) return json({ id: 'ref', status: 'succeeded', audio_url: '/v1/reference-speech/ref/audio', generation_config: {} });
        if (p === '/v1/pronunciation-attempts') return json({ id: `attempt${turn}` });
        if (p.endsWith('/analyze')) return json({ attempt: { id: `attempt${turn}` }, target: target(), syllables: [] });
        if (p === '/v1/utterances') { attempts.set(++turn, chosen); return json({ id: `u${turn}` }); }
        if (p.endsWith('/perceptions')) return json({ id: `p${turn}`, utterance_id: `u${turn}`, transcript: chosen.perceived_text, status: 'succeeded' });
        if (p.endsWith('/speech-analysis')) return json({ id: `a${turn}`, utterance_id: `u${turn}`, perception_run_id: `p${turn}`,
          status: 'succeeded', alignment_reference_text: chosen.perceived_text, data: chosen.data });
        if (p.endsWith('/readings')) return json({ syllables: chosen.data.syllables });
        if (p.endsWith('/audio')) {
          audioCalls.push(url.search);
          const recording = attempts.get(Number(p.match(/\/u(\d+)\//)?.[1]));
          assert(recording?.audio || recording?.audio_base64, 'Never invent audio for layout fixtures');
          return route.fulfill({ contentType: 'audio/wav', body: recording.audio || Buffer.from(recording.audio_base64, 'base64') });
        }
        if (p === '/v1/conversations') return json({ id: 'conversation' });
        if (p.endsWith('/user-turns/stream')) return route.fulfill({ contentType: 'application/x-ndjson', body: JSON.stringify({ type: 'complete', result: {
          id: `t${turn}`, role: 'user', utterance_id: `u${turn}`, perception_run_id: `p${turn}`, perceived_text: chosen.perceived_text,
          interpretation_decision: 'preserve', resolved_text: chosen.perceived_text,
          assistant_turn: { id: 'reply', role: 'assistant', assistant_text: '你想买什么？' },
        } }) + '\n' });
        return route.fulfill({ status: 404, json: { detail: p } });
      });
      const click = name => page.getByRole('button', { name, exact: true }).click();
      const record = async (label = 'New Attempt') => {
        await click(label);
        assert.equal(await page.getByTestId('pronunciation-workspace').count(), 0);
        assert(await page.evaluate(() => window.__playedAudio.every(p => p.paused)));
        await page.waitForTimeout(250);
        const analyzed = page.waitForResponse(r => r.url().endsWith('/speech-analysis'));
        await click('Stop recording'); await analyzed;
        await page.getByTestId('pronunciation-workspace').waitFor();
      };
      const labels = () => page.getByTestId('perceived-sentence-overview').locator('[data-testid^=pronunciation-unit-]').evaluateAll(nodes => nodes.map(n => n.getAttribute('aria-label').split(',')[0]));
      const layout = async () => {
        const items = await page.getByTestId('perceived-sentence-overview').locator('[data-testid^=pronunciation-unit-]').evaluateAll(nodes => nodes.map(n => {
          const r = n.getBoundingClientRect(); return { x: r.x, y: r.y, right: r.right, width: r.width, height: r.height, scroll: n.scrollWidth, client: n.clientWidth };
        }));
        for (const [i, r] of items.entries()) {
          assert(r.width >= 44 && r.height >= 48 && r.right <= width && r.scroll <= r.client + 1);
          if (i) assert(r.y > items[i - 1].y || r.x > items[i - 1].x);
        }
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        assert.equal(await page.getByTestId('selected-pronunciation-detail').count(), 1);
        const footer = await page.getByRole('button', { name: 'New Attempt', exact: true }).boundingBox();
        assert(footer.y >= 0 && footer.y + footer.height <= 844);
        return new Set(items.map(r => r.y)).size;
      };
      const play = async text => {
        await click(`Play my recording for ${text}`);
        const pause = page.getByRole('button', { name: `Pause my recording for ${text}`, exact: true });
        await pause.waitFor(); await pause.click();
      };
      await page.goto(process.env.BENMA_WEB_URL || 'http://localhost:8093'); await click('Open Practice');
      await click('Add target'); await page.getByLabel('Target phrase', { exact: true }).fill(targetText); await click('Prepare target');
      await page.getByRole('button', { name: 'Edit target: 我想买这个', exact: true }).waitFor();
      await record('Record');
      assert.deepEqual(await labels(), ['我', '想', '买', '这个']);
      await page.getByTestId('pronunciation-unit-0').click();
      const detail = page.getByTestId('selected-pronunciation-detail');
      const quiet = async () => {
        assert(!/Mostly level|Rising|Falling|Dipping|Gesture unavailable|experimental|Measurement:/i.test(await detail.innerText()));
        const labels = await page.getByTestId('perceived-sentence-overview').locator('button, [role=button]').evaluateAll(nodes => nodes.map(n => n.getAttribute('aria-label')));
        assert(!/Measurement:|Eligible|High confidence/i.test(labels.join(' ')));
        await layout();
      };
      await quiet();
      assert.equal(await detail.getByLabel('Pitch shape across the selected spoken span; gaps mean missing pitch', { exact: true }).count(), 1);
      await play('我');
      await page.screenshot({ path: `${output}/${width}-wo.png`, fullPage: true });
      await click('More details'); await page.getByRole('dialog').waitFor(); await click('Technical details');
      assert(await page.getByText('Observed gesture: Mostly level · experimental', { exact: true }).isVisible());
      assert(await page.getByText('Measurement evidence: sufficient', { exact: true }).isVisible());
      await page.screenshot({ path: `${output}/${width}-wo-details.png`, fullPage: true });
      await click('Raw');
      assert(await page.getByText('Raw tracker evidence · developer detail', { exact: true }).isVisible());
      await page.keyboard.press('Escape'); await page.getByRole('dialog').waitFor({ state: 'hidden' });
      await quiet();
      const chunk = page.getByTestId('pronunciation-unit-3');
      for (const key of ['Enter', 'Space']) {
        await page.getByTestId('pronunciation-unit-0').click(); await chunk.focus(); await page.keyboard.press(key);
        await page.getByRole('button', { name: 'Play my recording for 这个', exact: true }).waitFor();
        assert.equal(await chunk.getAttribute('aria-pressed'), 'true');
      }
      assert.equal(await chunk.getByRole('button').count(), 0);
      assert.equal(await page.getByTestId('pronunciation-unit-4').count(), 0);
      assert(await detail.getByLabel('Pitch unavailable', { exact: true }).isVisible());
      assert.equal(await page.getByText('Pitch was measured for part of this chunk.', { exact: true }).count(), 0);
      assert.equal(await page.getByTestId('selected-pronunciation-detail').getByLabel('Pitch shape across the selected spoken span; gaps mean missing pitch', { exact: true }).count(), 1);
      await quiet();
      const shortRows = await layout();
      await page.screenshot({ path: `${output}/${width}-this-chunk.png`, fullPage: true });
      await play('这个');
      await click('More details'); await page.getByRole('dialog').waitFor(); await page.waitForTimeout(350);
      for (const [text, time, hasPitch] of [['这', '2.34–2.73 s · exact segment', true], ['个', '2.74–3.04 s · exact segment', false]]) {
        await click(`Inspect ${text}, constituent timing unit`);
        const panel = page.getByTestId('selected-constituent-detail');
        assert(!(await panel.innerText()).includes('exact segment'));
        assert(await panel.getByText(hasPitch ? 'Pitch available' : 'Pitch unavailable', { exact: true }).isVisible());
        assert.equal(await panel.getByLabel('Pitch shape across the selected spoken span; gaps mean missing pitch', { exact: true }).count(), hasPitch ? 1 : 0);
        if (!hasPitch) assert(await panel.getByText("Pitch couldn't be measured reliably.", { exact: true }).isVisible());
        await play(text);
        await page.screenshot({ path: `${output}/${width}-constituent-${hasPitch ? 'zhe' : 'ge'}.png`, fullPage: true });
      }
      for (let i = 0; i < 12; i++) { await page.keyboard.press('Tab'); assert(await page.getByRole('dialog').evaluate(n => n.contains(document.activeElement))); }
      await page.keyboard.press('Escape'); await page.getByRole('dialog').waitFor({ state: 'hidden' });
      // Same physical take without chunk metadata: review timed 个 as a singleton.
      chosen = { ...thisOne, data: physical.data }; await record();
      await page.getByTestId('pronunciation-unit-4').click();
      await quiet();
      assert.equal(await detail.getByLabel('Pitch shape across the selected spoken span; gaps mean missing pitch', { exact: true }).count(), 0);
      assert(await detail.getByText("Pitch couldn't be measured reliably.", { exact: true }).isVisible());
      await play('个');
      await page.screenshot({ path: `${output}/${width}-ge-single.png`, fullPage: true });
      chosen = oneApple; await record();
      assert.deepEqual(await labels(), ['我', '要', '一个', '苹', '果']);
      await page.getByTestId('pronunciation-unit-2').click(); await play('一个');
      await page.screenshot({ path: `${output}/${width}-quantity.png`, fullPage: true });
      await click('History'); await click('Open attempt 1');
      assert.deepEqual(await labels(), ['我', '想', '买', '这个']);
      await chunk.click(); await play('这个');
      chosen = design('那个'); await record(); assert.deepEqual(await labels(), ['那个']); await layout();
      chosen = umbrella; await record(); assert.deepEqual(await labels(), ['我', '想', '买', '五', '把', '雨伞']);
      await page.getByTestId('pronunciation-unit-5').click(); await play('雨伞');
      await quiet();
      assert.equal(await detail.getByLabel('Pitch shape across the selected spoken span; gaps mean missing pitch', { exact: true }).count(), 1);
      await page.screenshot({ path: `${output}/${width}-umbrella.png`, fullPage: true });
      chosen = design('我想买这个雨伞和那个雨伞再要一个苹果'); await record();
      assert.deepEqual(await labels(), ['我', '想', '买', '这个', '雨伞', '和', '那个', '雨伞', '再', '要', '一个', '苹', '果']);
      const longRows = await layout(); assert(longRows > 1);
      await page.screenshot({ path: `${output}/${width}-long-chunks.png`, fullPage: true });
      await click('Clear target');
      assert.equal(await page.getByTestId('pronunciation-workspace').count(), 0);
      assert.equal(await page.getByRole('button', { name: 'History', exact: true }).count(), 0);
      chosen = thisOne; await record('Record'); assert.deepEqual(await labels(), ['我', '想', '买', '这个']);
      await chunk.click(); await play('这个'); await layout();
      assert.equal(await page.getByText('Target', { exact: true }).count(), 0);
      await page.screenshot({ path: `${output}/${width}-untargeted.png`, fullPage: true });
      await page.goto(process.env.BENMA_WEB_URL || 'http://localhost:8093'); await click('Open Conversation');
      await click('Tap to speak'); await page.waitForTimeout(250); await click('Stop recording');
      await page.getByText('你想买什么？', { exact: true }).waitFor();
      assert.equal(await page.getByTestId('pronunciation-workspace').count(), 0);
      await click('Explore pronunciation'); assert.deepEqual(await labels(), ['我', '想', '买', '这个']);
      assert(audioCalls.includes('?canonical=true')); assert.deepEqual(errors, []);
      summary.push({ width, shortRows, longRows, keyboard: true, canonicalPlayback: true, partialPitch: true,
        constituents: true, graphFirstWo: true, woDetailsAndRaw: true, unavailableSingleGe: true, quietAccessibility: true, quantity: true, that: true, groupedUmbrella: true, history: true,
        newAttempt: true, clearTarget: true, noTarget: true, conversationCollapsed: true, errors });
      await context.close();
    }
    fs.writeFileSync(`${output}/review.json`, JSON.stringify(summary, null, 2));
    console.log(JSON.stringify(summary, null, 2));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
