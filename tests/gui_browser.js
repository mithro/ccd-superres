// Drives the interactive explorer in a real browser. Run by tests/test_gui.py, or by hand:
//   node tests/gui_browser.js http://127.0.0.1:8765 [folder for screenshots]
const { chromium } = require("playwright");

function check(condition, what) { if (!condition) throw new Error("failed: " + what); }

(async () => {
  const [address, shots] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1360, height: shots ? 2250 : 900 }, deviceScaleFactor: shots ? 1.5 : 1 });
  const problems = [];
  page.on("console", (m) => { if (m.type() === "error") problems.push(m.text()); });
  page.on("pageerror", (e) => problems.push(String(e)));
  const settled = async (id = "status") => {
    await page.waitForTimeout(150);
    await page.waitForFunction((i) => !document.getElementById(i).textContent.startsWith("Working"), id);
  };
  const error = async () => Number(await page.locator("#scores tr:nth-child(2) td:nth-child(2)").innerText());
  const set = async (id, value) => { await page.fill(id, String(value)); await page.dispatchEvent(id, "change"); await settled(); };
  const drawn = (id) => page.evaluate((i) => {
    const c = document.getElementById(i), d = c.getContext("2d").getImageData(0, 0, c.width, c.height).data;
    let n = 0; for (let k = 3; k < d.length; k += 4) if (d[k]) n++; return n;
  }, id);

  await page.goto(address + "/");
  await settled();
  check((await page.textContent("#status")).startsWith("Updated"), "first run");
  const usual = await error();
  check(usual > 0.1 && usual < 0.2, "default error is that of the command line, about 0.154");
  for (const id of ["plot-surface", "plot-readings", "plot-path", "plot-blur"]) check(await drawn(id) > 2000, id + " is drawn");
  check(await page.locator("#setup svg rect").count() > 10, "setup diagram is drawn");
  check((await page.inputValue("#file")).includes('method = "least_squares"'), "approach file text");

  // A wider gap makes it worse; the slider and the number box stay in step.
  await set("#c-optics-gap_nm", 2000);
  check(await error() > usual + 0.03, "wider gap gives a larger error");
  check((await page.innerText("#setup")).includes("gap 2,000 nm"), "diagram shows the new gap");
  check((await page.inputValue("#file")).includes("gap_nm = 2000"), "file text follows the gap");
  await page.locator('[data-key="optics.gap_nm"] input[type=range]').fill("0");
  await page.dispatchEvent('[data-key="optics.gap_nm"] input[type=range]', "input");
  await settled();
  check(await page.inputValue("#c-optics-gap_nm") === "20", "slider drives the number box");
  check(await error() < usual, "smallest gap gives a smaller error");

  // An impossible value is explained and the last good pictures stay.
  await set("#c-optics-gap_nm", -5);
  check((await page.textContent("#status")).includes("at least 0"), "bad value is explained");
  check(await page.locator("#status.bad").count() === 1, "bad value is marked");
  await page.click("#reset"); await settled();
  check(Math.abs(await error() - usual) < 1e-9, "reset returns to the default");

  // Several methods on the same readings, positions unknown, a wandering path.
  for (const m of ["shift_and_add", "two_materials_positions"]) await page.check("#m-" + m);
  await set("#c-scan-wander_px", 1);
  await page.check('input[name=positions][value=unknown]'); await settled();
  const rows = await page.locator("#scores tr").count();
  check(rows === 4, "three methods are scored");
  const table = await page.innerText("#scores");
  check(table.includes("Two known materials, solving positions") && table.includes("Share of 320 nm bars"), "scores table");

  // A method that cannot run on this surface says so, and the others still run.
  await page.selectOption("#scene", "soft_ramps"); await settled();
  check((await page.innerText("#scores")).includes("Did not run"), "method that cannot run is explained");
  await page.selectOption("#scene", "bars"); await settled();

  // Loading an approach file sets the controls; the address keeps the settings across a reload.
  await page.selectOption("#preset", "narrow-opening"); await settled();
  const opening = await page.inputValue("#c-optics-aperture_nm");
  check(Number(opening) < 1120, "approach file sets the pixel opening");
  await page.reload(); await settled();
  check(await page.inputValue("#c-optics-aperture_nm") === opening, "settings survive a reload");
  await page.click("#zooms button:nth-child(5)");
  await page.mouse.move(700, 600);
  if (shots) {
    await page.click("#reset"); await settled();
    for (const m of ["shift_and_add", "two_materials_positions"]) await page.check("#m-" + m);
    await set("#c-scan-wander_px", 1);
    await page.check('input[name=positions][value=unknown]'); await settled();
    await page.screenshot({ path: shots + "/interactive-explorer-1d.png", fullPage: true });
  }

  // Two dimensions: taking the tilt away loses the lines across the scan.
  await page.click("#tab-2d"); await settled("status-2d");
  const across = async () => Number(await page.locator("#groups-2d tr:nth-child(3) td:nth-child(3)").innerText());
  const tilted = await across();
  check(tilted > 0.8, "tilted sensor shows lines across the scan");
  if (shots) await page.screenshot({ path: shots + "/interactive-explorer-2d.png", fullPage: true });
  await page.fill("#c-tilt_deg-2d", "0"); await page.dispatchEvent("#c-tilt_deg-2d", "change"); await settled("status-2d");
  check(await across() < 0.3, "untilted sensor loses them");
  check(await page.evaluate(() => document.getElementById("img-estimate").width) === 512, "reconstruction picture is drawn");

  check(problems.length === 0, "no errors in the browser: " + problems.join("; "));
  await browser.close();
  console.log("ok");
})().catch((problem) => { console.error(String(problem)); process.exit(1); });
