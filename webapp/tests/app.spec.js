const {_electron: electron} = require('playwright');
const {strict: assert} = require('assert');

// Playwright has EXPERIMENTAL electron support.
(async () => {
  const electronApp = await electron.launch({args: ['.']});

  /**
   * App main window state
   * @type {{isVisible: boolean; isDevToolsOpened: boolean; isCrashed: boolean}}
   */
  const windowState = await electronApp.evaluate(({BrowserWindow}) => {
    const mainWindow = BrowserWindow.getAllWindows()[0];

    const getState = () => ({
      isVisible: mainWindow.isVisible(),
      isDevToolsOpened: mainWindow.webContents.isDevToolsOpened(),
      isCrashed: mainWindow.webContents.isCrashed(),
    });

<<<<<<< HEAD
    return new Promise(resolve => {
      if (mainWindow.isVisible()) {
        resolve(getState());
      } else mainWindow.once('ready-to-show', () => setTimeout(() => resolve(getState()), 0));
=======
    return new Promise((resolve) => {
      if (mainWindow.isVisible()) {
        resolve(getState());
      } else
        mainWindow.once('ready-to-show', () => setTimeout(() => resolve(getState()), 0));
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
    });
  });

  // Check main window state
  assert.ok(windowState.isVisible, 'Main window not visible');
  assert.ok(!windowState.isDevToolsOpened, 'DevTools opened');
  assert.ok(!windowState.isCrashed, 'Window crashed');

  /**
   * Rendered Main window web-page
   * @type {Page}
   */
  const page = await electronApp.firstWindow();

<<<<<<< HEAD
  // Check web-page content
  const element = await page.$('#app', {strict: true});
  assert.notStrictEqual(element, null, "Can't find root element");
  assert.notStrictEqual((await element.innerHTML()).trim(), '', 'Window content is empty');

=======

  // Check web-page content
  const element = await page.$('#app', {strict: true});
  assert.notStrictEqual(element, null, 'Can\'t find root element');
  assert.notStrictEqual((await element.innerHTML()).trim(), '', 'Window content is empty');


>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
  // Checking the framework.
  // It is assumed that on the main screen there is a `<button>` that changes its contents after clicking.
  const button = await page.$('button');
  const originalBtnText = await button.textContent();

  await button.click();
  const newBtnText = await button.textContent();

<<<<<<< HEAD
  assert.ok(
    originalBtnText !== newBtnText,
    'The button did not change the contents after clicking',
  );
=======
  assert.ok(originalBtnText !== newBtnText, 'The button did not change the contents after clicking');
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0

  // Check Preload script
  const renderedExposedApi = await page.evaluate(() => globalThis.electron);
  const realVersions = await electronApp.evaluate(() => process.versions);

<<<<<<< HEAD
  assert.notStrictEqual(
    renderedExposedApi,
    undefined,
    'In renderer `globalThis.electron` is undefined',
  );
=======
  assert.notStrictEqual(renderedExposedApi, undefined, 'In renderer `globalThis.electron` is undefined');
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
  assert.strictEqual(renderedExposedApi?.versions?.electron, realVersions.electron);

  // Close app
  await electronApp.close();
})();
