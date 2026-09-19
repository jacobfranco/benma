/* Unpaid integration smoke. Run against tests/web_smoke_app.py, never paid providers.
 * BENMA_PLAYWRIGHT_MODULE may point to an existing @playwright/test install.
 * Export web to /tmp/benma-web-parity-export first. Uses localhost:8081 and API :8000.
 */
const { chromium, expect } = require(process.env.BENMA_PLAYWRIGHT_MODULE || '@playwright/test');
const { createServer } = require('node:http');
const { readFile } = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = process.env.BENMA_WEB_EXPORT || '/tmp/benma-web-parity-export';
const server = createServer(async (req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const file = path.join(root, pathname.includes('.') ? pathname : '/index.html');
  if (!file.startsWith(root + '/')) { res.writeHead(403).end(); return; }
  try {
    const body = await readFile(file);
    res.setHeader('Content-Type', file.endsWith('.js') ? 'application/javascript' : file.endsWith('.png') ? 'image/png' : 'text/html');
    res.end(body);
  } catch { res.writeHead(404).end(); }
});
(async () => {
  await new Promise(resolve => server.listen(8081, '127.0.0.1', resolve));
  const browser = await chromium.launch({ executablePath: process.env.BENMA_CHROMIUM || '/usr/bin/chromium', headless: true,
    args: ['--no-sandbox', '--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream',
      ...(process.env.BENMA_MIC_FIXTURE ? [`--use-file-for-fake-audio-capture=${process.env.BENMA_MIC_FIXTURE}`] : [])] });
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, permissions: ['microphone'] });
    await context.addInitScript(() => {
      window.smoke = { made: [], revoked: [], plays: 0, tracks: [], audios: [], blockNext: false };
      const make = URL.createObjectURL.bind(URL), revoke = URL.revokeObjectURL.bind(URL);
      URL.createObjectURL = blob => { const uri = make(blob); window.smoke.made.push(uri); return uri; };
      URL.revokeObjectURL = uri => { window.smoke.revoked.push(uri); revoke(uri); };
      const play = HTMLMediaElement.prototype.play;
      HTMLMediaElement.prototype.play = function () {
        if (!window.smoke.audios.includes(this)) window.smoke.audios.push(this);
        if (window.smoke.blockNext) { window.smoke.blockNext = false; return Promise.reject(new DOMException('blocked by test policy', 'NotAllowedError')); }
        return play.call(this).then(() => { window.smoke.plays++; });
      };
      const get = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
      navigator.mediaDevices.getUserMedia = async (...args) => { const stream = await get(...args); window.smoke.tracks.push(...stream.getTracks()); return stream; };
    });
    const page = await context.newPage();
    const errors = [], uploads = [], downloads = [], events = [], latencies = [], analysisBodies = [];
    const starts = new Map();
    let lastAnalysisResponseAt = 0;
    let analysisUiFrameUpperBoundMs = 0;
    page.on('request', request => { if (request.url().includes('/v1/')) starts.set(request, performance.now()); });
    page.on('pageerror', error => errors.push(error.message));
    page.on('response', async response => {
      const url = new URL(response.url());
      if (!url.pathname.startsWith('/v1/')) return;
      latencies.push({ path: url.pathname.replace(/[0-9a-f]{8}-[0-9a-f-]{27,}/g, ':id'), ms: performance.now() - starts.get(response.request()) });
      if (url.pathname.endsWith('/speech-analysis')) { lastAnalysisResponseAt = performance.now(); analysisBodies.push(await response.json()); }
      events.push({ path: url.pathname.replace(/[0-9a-f]{8}-[0-9a-f-]{27,}/g, ':id'), status: response.status() });
      if (url.pathname === '/v1/utterances' && response.request().method() === 'POST') {
        const body = await response.json();
        uploads.push({ status: response.status(), ...(response.status() === 201 ? body.original_audio : { validation: body }) });
      }
      if (url.pathname.endsWith('/audio')) downloads.push(url.pathname);
    });
    if (process.env.BENMA_SHAPE_PREVIEW === '1') {
      await page.route('**/speech-analysis', async route => {
        const response = await route.fetch();
        const fixture = await response.json();
        const width = fixture.data.duration_seconds / fixture.data.syllables.length;
        fixture.data.syllables.forEach((syllable, index) => {
          const shape = [[2, 2], [-2, 2], [0, -3, 1], [2, -2]][index % 4];
          syllable.start_seconds = index * width;
          syllable.end_seconds = (index + 1) * width;
          syllable.display_contour = { minimum_semitones: -4, maximum_semitones: 4,
            segments: [shape.map((height, j) => ({ timestamp_seconds: (index + j / (shape.length - 1)) * width, normalized_semitones: height }))] };
          syllable.observed_contour = { classification: `${index % 4 + 1}-like`, confidence: 'moderate', reason: 'synthetic_render_fixture' };
        });
        fixture.data.evidence_status = 'synthetic_replay';
        await route.fulfill({ response, json: fixture });
      });
    }
    await page.goto('http://127.0.0.1:8081/conversation');
    await page.getByRole('button', { name: 'Continue with development account', exact: true }).click();
    await page.getByRole('button', { name: 'Open Conversation', exact: true }).waitFor();
    await page.reload();
    await page.getByRole('button', { name: 'Open Conversation', exact: true }).click();
    await page.reload();
    async function record() {
      await page.getByRole('button', { name: 'Tap to speak', exact: true }).click();
      await page.getByRole('button', { name: 'Stop recording', exact: true }).waitFor();
      await page.waitForTimeout(1400); // Actual MediaRecorder capture interval.
      await page.getByRole('button', { name: 'Stop recording', exact: true }).click();
      await expect.poll(() => uploads.length).toBeGreaterThan(0);
      await page.getByRole('button', { name: 'Tap to speak', exact: true }).waitFor();
    }
    // Hold each branch independently to inspect perception, response, and hydration.
    const gate = (branch, action) => context.request.post(`http://127.0.0.1:8000/__smoke/gates/${branch}/${action}`);
    await gate('analysis', 'hold'); await gate('reply', 'hold');
    await page.getByRole('button', { name: 'Tap to speak', exact: true }).click();
    await page.getByRole('button', { name: 'Stop recording', exact: true }).waitFor();
    await page.waitForTimeout(1400);
    const stoppedAt = performance.now();
    await page.getByRole('button', { name: 'Stop recording', exact: true }).click();
    await page.getByTestId('syllable-0').first().waitFor();
    await page.getByText('Preparing response…', { exact: true }).waitFor();
    const section = page.getByTestId('pronunciation-section');
    const before = await section.boundingBox();
    await page.evaluate(() => { window.pronunciationNode = document.querySelector('[data-testid="pronunciation-section"]'); });
    await gate('reply', 'release');
    await page.getByText('我们一起练习中文。', { exact: true }).waitFor();
    const afterReply = await section.boundingBox();
    await expect(page.getByTestId('syllable-0').first()).toBeVisible();
    const replyBeforeAnalysis = await page.getByText('BENMA', { exact: true }).boundingBox();
    await gate('analysis', 'release');
    await page.getByText('Expected here · acoustic shapes', { exact: true }).waitFor();
    const stopToChartMs = performance.now()-stoppedAt;
    const afterAnalysis = await section.boundingBox();
    const replyAfterAnalysis = await page.getByText('BENMA', { exact: true }).boundingBox();
    const stableNode = await page.evaluate(() => window.pronunciationNode === document.querySelector('[data-testid="pronunciation-section"]'));
    assert(stableNode); assert.equal(before.height, afterReply.height); assert.equal(before.height, afterAnalysis.height);
    assert.equal(replyBeforeAnalysis.y, replyAfterAnalysis.y);
    await expect(page.getByText('你好，今天我们聊聊周末吧。', { exact: true })).toBeVisible();
    for (const reading of ['nǐ', 'hǎo', 'jīn', 'tiān', 'wǒ', 'men', 'liáo', 'zhōu', 'mò', 'ba']) {
      await expect(page.getByText(reading, { exact: true }).first()).toBeAttached();
    }
    await expect(page.getByText('Reading unresolved', { exact: true })).toHaveCount(0);
    await expect(page.getByText('Whole utterance', { exact: true })).toHaveCount(0);
    await page.screenshot({ path: process.env.BENMA_SHAPE_PREVIEW === '1' ? '/tmp/benma-paired-shapes-preview.png' : '/tmp/benma-pronunciation-stable.png', fullPage: true });
    await page.getByRole('button', { name: 'Play response', exact: true }).waitFor();
    await expect.poll(() => page.evaluate(() => window.smoke.plays)).toBeGreaterThan(0);
    let playCount = await page.evaluate(() => window.smoke.plays), count = downloads.length;
    await page.getByRole('button', { name: 'Play response', exact: true }).click();
    await expect.poll(() => page.evaluate(() => window.smoke.plays)).toBeGreaterThan(playCount);
    assert.equal(downloads.length, count, 'response replay redownloaded');
    await page.getByRole('button', { name: '▶ Play mine', exact: true }).click();
    await expect.poll(() => page.evaluate(() => window.smoke.plays)).toBeGreaterThan(playCount + 1);
    await page.getByRole('button', { name: 'Tap to speak', exact: true }).click();
    await page.getByRole('button', { name: 'Stop recording', exact: true }).waitFor();
    assert.equal(await page.evaluate(() => window.smoke.audios.every(audio => audio.paused)), true);
    // Recording must stop learner playback. Then finish the second conversation turn.
    await page.waitForTimeout(1400);
    await page.evaluate(() => { window.smoke.blockNext = true; });
    const secondStoppedAt = performance.now();
    await page.getByRole('button', { name: 'Stop recording', exact: true }).click();
    await expect(page.getByText('我们一起练习中文。', { exact: true })).toHaveCount(2);
    await expect(page.getByRole('button', { name: 'Play response', exact: true })).toHaveCount(2);
    await expect(page.getByText('Expected here · acoustic shapes', { exact: true })).toHaveCount(2);
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    const ungatedStopToChartMs = performance.now()-secondStoppedAt;
    analysisUiFrameUpperBoundMs = performance.now()-lastAnalysisResponseAt;
    await expect(page.getByText('Audio unavailable. Try playing it again.', { exact: true })).toHaveCount(0);
    await expect.poll(() => page.evaluate(() => window.smoke.blockNext)).toBe(false);
    playCount = await page.evaluate(() => window.smoke.plays);
    await page.getByRole('button', { name: 'Play response', exact: true }).last().click();
    await expect.poll(() => page.evaluate(() => window.smoke.plays)).toBeGreaterThan(playCount);
    await page.evaluate(() => document.querySelectorAll('*').forEach(el => { if (el.scrollTop) el.scrollTop = 0; }));
    await page.screenshot({ path: '/tmp/benma-conversation-desktop.png', fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: '/tmp/benma-conversation-narrow.png', fullPage: true });
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goBack();
    await page.getByRole('button', { name: 'Open Practice', exact: true }).click();
    await page.setViewportSize({ width: 390, height: 844 });
    await gate('analysis', 'hold');
    await record();
    await page.getByTestId('syllable-0').first().waitFor();
    const narrowBefore = await page.getByTestId('pronunciation-section').boundingBox();
    await gate('analysis', 'release');
    await page.getByText('Expected here · acoustic shapes', { exact: true }).waitFor();
    const narrowAfter = await page.getByTestId('pronunciation-section').boundingBox();
    assert.equal(narrowBefore.height, narrowAfter.height);
    assert.equal(narrowBefore.y, narrowAfter.y);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.getByRole('button', { name: 'More detail', exact: true }).click();
    await page.getByText('Whole utterance', { exact: true }).waitFor();
    if (process.env.BENMA_MIC_FIXTURE) await expect.poll(() => page.getByLabel('Relative pitch contour', { exact: true }).last().getByTestId('contour-line').count()).toBeGreaterThan(1);
    await page.getByLabel('Relative pitch contour', { exact: true }).last().screenshot({ path: '/tmp/benma-contour-detail.png' });
    await page.screenshot({ path: '/tmp/benma-contour-narrow.png', fullPage: true });
    await page.getByRole('button', { name: 'Less detail', exact: true }).click();
    await page.setViewportSize({ width: 1440, height: 1000 });
    assert.equal(await page.getByRole('button', { name: 'Play response', exact: true }).count(), 0);
    await page.getByRole('button', { name: '▶ Play mine', exact: true }).click();
    await page.getByRole('button', { name: 'Add a target phrase', exact: true }).click();
    await page.getByRole('textbox', { name: 'Target phrase', exact: true }).fill('你好');
    await page.getByRole('button', { name: 'Prepare target', exact: true }).click();
    playCount = await page.evaluate(() => window.smoke.plays);
    await page.getByRole('button', { name: '▶ Native reference', exact: true }).click();
    await expect.poll(() => page.evaluate(() => window.smoke.plays)).toBeGreaterThan(playCount);
    await expect.poll(() => downloads.some(p => p.includes('/reference-speech/'))).toBe(true);
    await record();
    await page.getByText('Experimental pronunciation analysis', { exact: true }).waitFor();
    await expect.poll(() => events.some(e => e.path.endsWith('/analyze') && e.status === 200)).toBe(true);
    await page.screenshot({ path: '/tmp/benma-practice-desktop.png', fullPage: true });
    // Navigate with router back to keep lifecycle cleanup observable in this document.
    await page.goBack();
    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await page.getByRole('button', { name: 'Continue with development account', exact: true }).waitFor();
    const cleanup = await page.evaluate(() => ({ live: window.smoke.made.filter(u => !window.smoke.revoked.includes(u)).length,
      tracks: window.smoke.tracks.filter(t => t.readyState !== 'ended').length,
      stored: localStorage.getItem('benma.auth.session-token') !== null }));
    assert.deepEqual(cleanup, { live: 0, tracks: 0, stored: false });
    await page.reload();
    await page.getByRole('button', { name: 'Continue with development account', exact: true }).waitFor();
    assert.deepEqual(errors, []); assert.equal(uploads.length, 4); assert(uploads.every(u => u.status === 201));
    console.log(JSON.stringify({ chromium: browser.version(), stopToChartMs, ungatedStopToChartMs, analysisUiFrameUpperBoundMs, layout: { before, afterReply, afterAnalysis, replyBeforeAnalysis, replyAfterAnalysis, stableNode, narrowBefore, narrowAfter }, latencies, analysisStages: analysisBodies.map(a => ({ wall: a.latency_ms, ...a.data.timings_ms, pitch: a.data.pitch_latency_ms, alignment: a.data.alignment_latency_ms })), uploads, downloads: downloads.length, events, cleanup, pageErrors: errors }, null, 2));
  } catch (error) { console.error("browser assertion:", error); throw error; } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; }).finally(() => server.close());
