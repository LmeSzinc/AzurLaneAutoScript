export function setupThemeSetting(theme?: string) {
  if ((theme && theme === 'dark') || window.matchMedia('(prefers-color-scheme: dark)').matches) {
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
