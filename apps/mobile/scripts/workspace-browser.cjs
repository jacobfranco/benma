/* Offline UI acceptance. Requires the ignored saved six-take viewer-data.json.
 * PLAYWRIGHT_MODULE=/path/to/playwright node scripts/workspace-browser.cjs
 * Export the web app and serve it at BENMA_WEB_URL (default localhost:8086).
 * No live API/provider requests; no audio is copied into output artifacts.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '../../..');
const saved = JSON.parse(fs.readFileSync(process.env.BENMA_WORKSPACE_FIXTURE || path.join(root, 'services/api/var/audio-first-feedback/viewer-data.json'))).recordings;
const grouped = saved.find(r => r.id.startsWith('40357072'));
const noTiming = saved.find(r => r.id.startsWith('d47274bc'));
const output = process.env.BENMA_BROWSER_OUTPUT || '/tmp/benma-polish-review';
fs.mkdirSync(output, { recursive: true });
const summary = [];
(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/chromium', args: ['--no-sandbox', '--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] });
  try {
    for (const width of [320, 390, 412]) {
      const context = await browser.newContext({ viewport: { width, height: 844 }, hasTouch: true, isMobile: true });
      const page = await context.newPage(), errors = [], audioCalls = [];
      page.on('pageerror', e => errors.push(String(e)));
      await page.addInitScript(() => {
        localStorage.setItem('benma.auth.session-token', 'offline-workspace-fixture');
        window.__playedAudio = [];
        const originalPlay = HTMLMediaElement.prototype.play;
        HTMLMediaElement.prototype.play = function () { window.__playedAudio.push(this); return originalPlay.call(this); };
      });
      let chosen = grouped, turn = 0;
      let targetText = '我想买五把雨伞';
      const target = () => ({ id: 'target', text: targetText, display_pinyin: targetText === '行' ? 'xíng' : 'wǒ xiǎng mǎi wǔ bǎ yǔ sǎn',
        pinyin_syllables: targetText === '行' ? ['xing2'] : ['wo3', 'xiang3', 'mai3', 'wu3', 'ba3', 'yu3', 'san3'],
        pinyin_alternatives: targetText === '行' ? [['xing2', 'hang2']] : [['wo3'], ['xiang3'], ['mai3'], ['wu3'], ['ba3'], ['yu3'], ['san3']] });
      const attempts = new Map();
      await page.route('**/v1/**', async route => {
        const url = new URL(route.request().url()), p = url.pathname;
        const json = data => route.fulfill({ json: data });
        if (p === '/v1/pronunciation-targets') { targetText = route.request().postDataJSON().text; return json(target()); }
        if (p.endsWith('/reference-speech')) return json({ id: 'ref', status: 'succeeded', audio_url: '/v1/reference-speech/ref/audio', generation_config: {} });
        if (p.endsWith('/pinyin-corrections')) return json({ ...target(), id: 'revision', pinyin_syllables: ['hang2'], display_pinyin: 'háng' });
        if (p === '/v1/pronunciation-attempts') return json({ id: 'attempt' });
        if (p.endsWith('/analyze')) return json({ attempt: { id: 'attempt' }, target: target(), syllables: [] });
        if (p === '/v1/me') return json({ id: 'offline' });
        if (p === '/v1/utterances') { attempts.set(++turn, chosen); return json({ id: `u${turn}` }); }
        if (p.endsWith('/perceptions')) return json({ id: `p${turn}`, utterance_id: `u${turn}`, transcript: chosen.perceived_text, status: 'succeeded' });
        if (p.endsWith('/speech-analysis')) return json({ id: `a${turn}`, utterance_id: `u${turn}`, perception_run_id: `p${turn}`, status: 'succeeded', alignment_reference_text: chosen.perceived_text, data: chosen.data });
        if (p.endsWith('/readings')) return json({ syllables: chosen.data.syllables });
        if (p.endsWith('/audio')) {
          audioCalls.push(url.search);
          const index = Number(p.match(/\/u(\d+)\//)?.[1]);
          return route.fulfill({ contentType: 'audio/wav', body: Buffer.from(attempts.get(index)?.audio_base64 || grouped.audio_base64, 'base64') });
        }
        if (p === '/v1/conversations') return json({ id: 'c' });
        if (p.endsWith('/user-turns/stream')) return route.fulfill({ contentType: 'application/x-ndjson', body: JSON.stringify({ type: 'complete', result: {
          id: `t${turn}`, role: 'user', utterance_id: `u${turn}`, perception_run_id: `p${turn}`, perceived_text: chosen.perceived_text,
          interpretation_decision: 'preserve', resolved_text: chosen.perceived_text,
          assistant_turn: { id: `reply${turn}`, role: 'assistant', assistant_text: '你想买什么颜色的雨伞？' },
        } }) + '\n' });
        return route.fulfill({ status: 404, json: { detail: `Unhandled offline route: ${p}` } });
      });
      const click = name => page.getByRole('button', { name, exact: true }).click();
      const stablePlayback = async (label, pauseLabel = `Pause: ${label}`) => {
        const before = await page.getByRole('button', { name: label, exact: true }).boundingBox();
        await click(label);
        const playing = page.getByRole('button', { name: pauseLabel, exact: true });
        await playing.waitFor();
        assert.deepEqual(await playing.boundingBox(), before);
        await playing.click();
        await page.getByRole('button', { name: label, exact: true }).waitFor();
      };
      const record = async (label = 'New Attempt') => {
        await click(label);
        assert.equal(await page.getByTestId('pronunciation-workspace').count(), 0);
        await page.waitForTimeout(250);
        const analyzed = page.waitForResponse(r => r.url().endsWith('/speech-analysis'));
        await click('Stop recording'); await analyzed;
        await page.getByRole('button', { name: 'New Attempt', exact: true }).waitFor();
        await page.getByTestId('pronunciation-workspace').waitFor();
      };
      await page.goto(process.env.BENMA_WEB_URL || 'http://localhost:8086'); await click('Open Practice');
      await click('Add a target phrase');
      await page.getByLabel('Target phrase', { exact: true }).fill(targetText);
      await click('Prepare target');
      await page.getByRole('button', { name: `Play native reference for ${targetText}`, exact: true }).waitFor();
      assert.equal(await page.getByRole('button', { name: 'Edit reading', exact: true }).count(), 0);
      await record();
      const overview = page.getByTestId('perceived-sentence-overview');
      const labels = await overview.locator('[data-testid^=pronunciation-unit-]').allTextContents();
      assert.deepEqual(labels, ['我', '想', '买', '五', '把', '雨伞']);
      const checkLayout = async () => {
        const box = await overview.boundingBox();
        const items = await overview.locator('[data-testid^=pronunciation-unit-]').evaluateAll(nodes => nodes.map(n => { const r = n.getBoundingClientRect(); return { x: r.x, y: r.y, right: r.right, width: r.width, height: r.height, scroll: n.scrollWidth, client: n.clientWidth }; }));
        for (let i = 0; i < items.length; i++) {
          const r = items[i]; assert(r.width >= 44 && r.height >= 44); assert(r.right <= box.x + box.width + 1); assert(r.scroll <= r.client + 1);
          if (i) assert(r.y > items[i - 1].y || r.x > items[i - 1].x);
        }
        assert(await overview.evaluate(n => n.scrollWidth <= n.clientWidth));
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        return items;
      };
      const short = await checkLayout();
      for (const label of [`Play native reference for ${targetText}`, 'Change target', 'Clear target', 'Play my full recording']) {
        const action = page.getByRole('button', { name: label, exact: true });
        const bounds = await action.boundingBox();
        assert(bounds.width >= 44 && bounds.width <= 48 && bounds.height >= 44);
        assert(bounds.x >= 0 && bounds.x + bounds.width <= width);
        assert(!((await action.textContent()) || '').includes(label));
      }
      await stablePlayback(`Play native reference for ${targetText}`);
      await stablePlayback('Play my full recording');
      assert(await page.getByRole('button', { name: 'History', exact: true }).isVisible());
      const retry = await page.getByRole('button', { name: 'New Attempt', exact: true }).boundingBox();
      assert(retry.y >= 0 && retry.y + retry.height <= 844);
      const primary = await page.getByTestId('selected-pronunciation-detail').boundingBox();
      const more = await page.getByRole('button', { name: 'More details', exact: true }).boundingBox();
      assert(primary.y >= 0 && more.y + more.height < retry.y);
      assert(await overview.getByRole('button', { name: 'Play my full recording', exact: true }).isVisible());
      await page.screenshot({ path: `${output}/${width}-overview.png`, fullPage: true });
      await page.getByTestId('pronunciation-unit-5').click();
      assert.equal(await page.getByTestId('selected-pronunciation-detail').count(), 1);
      await stablePlayback('Play my recording for 雨伞', 'Pause my recording for 雨伞');
      await click('Play my recording for 雨伞');
      await page.waitForTimeout(200);
      assert(audioCalls.includes('?canonical=true'));
      await page.evaluate(() => {
        Object.defineProperty(document, 'hidden', { configurable: true, value: true });
        document.dispatchEvent(new Event('visibilitychange'));
      });
      assert(await page.evaluate(() => window.__playedAudio.every(p => p.paused)));
      await page.evaluate(() => { delete document.hidden; });
      await page.getByTestId('pronunciation-unit-1').click();
      assert.equal(await page.getByRole('button', { name: 'Play my recording for 想', exact: true }).count(), 1);
      await page.getByTestId('pronunciation-workspace').scrollIntoViewIfNeeded();
      await page.screenshot({ path: `${output}/${width}-workspace.png`, fullPage: true });
      await click('More details');
      await page.getByRole('dialog').waitFor();
      await page.waitForTimeout(350);
      await page.screenshot({ path: `${output}/${width}-details-top.png`, fullPage: true });
      for (let i = 0; i < 12; i++) {
        await page.keyboard.press('Tab');
        assert(await page.getByRole('dialog').evaluate(n => n.contains(document.activeElement)));
      }
      assert.equal(await page.getByLabel('Sentence pitch timeline', { exact: true }).count(), 1);
      await page.screenshot({ path: `${output}/${width}-details.png`, fullPage: true });
      await page.keyboard.press('Escape');
      await page.getByRole('dialog').waitFor({ state: 'hidden' });
      chosen = noTiming; await record('New Attempt');
      assert.equal(await page.getByTestId('pronunciation-workspace').count(), 1);
      assert.equal(await page.getByTestId('perceived-sentence-overview').count(), 0);
      assert.equal(await page.getByRole('button', { name: /^Play my recording for/ }).count(), 0);
      await click('Play my full recording');
      await page.screenshot({ path: `${output}/${width}-no-timing.png`, fullPage: true });
      await click('History');
      await page.screenshot({ path: `${output}/${width}-history.png`, fullPage: true });
      await click('Open attempt 1');
      assert.equal(await page.getByTestId('pronunciation-unit-5').count(), 1);
      // A clearly synthetic layout-only long sentence fixture; no acoustic inference.
      const chars = Array.from('我今天下午想去超市买一点东西然后回家和朋友一起吃晚饭');
      chosen = { ...grouped, perceived_text: chars.join(''), data: { ...grouped.data, duration_seconds: chars.length * .4, timing_groups: [],
        syllables: chars.map((characters, index) => ({ ...grouped.data.syllables[0], index, characters, character_start: index, character_end: index + 1,
          start_seconds: index * .4, end_seconds: (index + 1) * .4 })),
      } };
      await record('New Attempt');
      const long = await checkLayout(); assert(long.at(-1).y > long[0].y);
      await page.screenshot({ path: `${output}/${width}-long.png`, fullPage: true });
      await click('Clear target');
      assert.equal(await page.getByTestId('pronunciation-workspace').count(), 0);
      assert.equal(await page.getByRole('button', { name: 'History', exact: true }).count(), 0);
      assert(await page.getByText('Free Practice', { exact: true }).isVisible());
      chosen = grouped; await record();
      await page.screenshot({ path: `${output}/${width}-free.png`, fullPage: true });
      await click('Add a target phrase'); await page.getByLabel('Target phrase', { exact: true }).fill('行');
      await click('Prepare target'); await click('Edit reading');
      assert.deepEqual(await page.getByRole('radio').allTextContents(), ['xing2', 'hang2']);
      await page.getByRole('radio', { name: '行: hang2', exact: true }).click();
      await page.waitForTimeout(350);
      await page.screenshot({ path: `${output}/${width}-reading.png`, fullPage: true });
      await click('Use this reading');
      await page.getByText('háng', { exact: true }).waitFor();
      await click('Change target');
      await page.waitForTimeout(350);
      await page.screenshot({ path: `${output}/${width}-target-dialog.png`, fullPage: true });
      await page.keyboard.press('Escape');
      await page.getByRole('dialog').waitFor({ state: 'hidden' });
      await page.goto(process.env.BENMA_WEB_URL || 'http://localhost:8086'); await click('Open Conversation');
      chosen = grouped;
      await click('Tap to speak'); await page.waitForTimeout(250); await click('Stop recording');
      await page.getByText('你想买什么颜色的雨伞？', { exact: true }).waitFor();
      assert.equal(await page.getByTestId('pronunciation-workspace').count(), 0);
      await page.screenshot({ path: `${output}/${width}-conversation.png`, fullPage: true });
      await click('Explore pronunciation');
      assert.equal(await page.getByTestId('pronunciation-workspace').count(), 1);
      assert.deepEqual(errors, []);
      summary.push({ width, shortRows: new Set(short.map(r => r.y)).size, longRows: new Set(long.map(r => r.y)).size, grouped: true, noTiming: true, history: true, canonicalPlayback: true, targetActions: true, readingSelector: true, clearTarget: true, freshAttempt: true, dialogs: true, primaryFits: true, playbackBoundsStable: true, conversationCollapsed: true, errors });
      await context.close();
    }
    fs.writeFileSync(`${output}/review.json`, JSON.stringify(summary, null, 2));
    console.log(JSON.stringify(summary, null, 2));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
