<script lang="ts">
  import AppHeader from './components/AppHeader.svelte'
  import Home from './views/Home.svelte'
  import Develop from './views/Develop.svelte'
  import Manage from './views/Manage.svelte'
  import Settings from './views/Settings.svelte'
  import { route } from './router.svelte'
  import { status } from './api/store.svelte'

  const THEMES = ['default', 'dark', 'light', 'minty', 'yeti', 'sketchy']
  let themeLink: HTMLLinkElement | null = null
  let alasLink: HTMLLinkElement | null = null

  function applyTheme(theme: string) {
    const name = THEMES.includes(theme) ? theme : 'default'
    const bsTheme = name === 'light' ? 'default' : name
    const alasTheme = name === 'dark' ? 'dark-alas-shell' : 'light-alas-shell'
    if (themeLink) {
      themeLink.remove()
    }
    if (alasLink) {
      alasLink.remove()
    }
    themeLink = document.createElement('link')
    themeLink.rel = 'stylesheet'
    themeLink.href = `css/${bsTheme}.min.css`
    document.head.appendChild(themeLink)
    alasLink = document.createElement('link')
    alasLink.rel = 'stylesheet'
    alasLink.href = `css/${alasTheme}.css`
    document.head.appendChild(alasLink)
  }

  $effect(() => {
    applyTheme(status.theme)
  })
</script>

<div id="app">
  <AppHeader />
  <main class="app-main">
    {#if route.path === '/settings'}
      <Settings />
    {:else if route.path === '/develop'}
      <Develop />
    {:else if route.path === '/manage'}
      <Manage />
    {:else}
      <Home />
    {/if}
  </main>
</div>

<style>
  :global(html),
  :global(body),
  :global(#app) {
    margin: 0;
    padding: 0;
    height: 100vh;
    overflow: hidden;
    /* Background and text colors follow the active bootstrap theme
       (css/<theme>.min.css loaded dynamically). */
    font-family:
      -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
  }
  .app-main {
    height: calc(100vh - 50px);
  }
  /* Mobile: collapse panels to full width below 768px */
  @media (max-width: 767px) {
    .app-main {
      height: calc(100vh - 50px);
    }
  }
</style>
