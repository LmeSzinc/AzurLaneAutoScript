import type {ThemeVal} from '/#/config';

export function setupThemeSetting(theme?: ThemeVal) {
  if (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    setTheme('dark');
    return;
  } else if (!theme && !window.matchMedia('(prefers-color-scheme: dark)').matches) {
    setTheme('light');
    return;
  }
  if (theme && theme === 'dark') {
    setTheme('dark');
    window.__electron_preload__ipcRendererSend('electron-theme', 'dark');
  } else {
    setTheme('light');
    window.__electron_preload__ipcRendererSend('electron-theme', 'light');
  }
}

export function setTheme(theme: ThemeVal) {
  if (theme === 'dark') {
    document.documentElement.classList.remove('light');
    document.documentElement.classList.add('dark');
    // Set to dark theme
    document.body.setAttribute('arco-theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark');
    document.documentElement.classList.add('light');
    // Restore the light color theme
    document.body.setAttribute('arco-theme', 'light');
  }
}
