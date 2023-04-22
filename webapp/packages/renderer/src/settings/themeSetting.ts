export function setupThemeSetting(theme?: string) {
  if ((theme && theme === 'dark') || window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.classList.add('dark');
    // Set to dark theme
    document.body.setAttribute('arco-theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark');
    // Restore the light color theme
    document.body.removeAttribute('arco-theme');
  }
}
