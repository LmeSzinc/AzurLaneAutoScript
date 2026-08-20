<script lang="ts">
import { status } from "./api/store.svelte";
import AppHeader from "./components/AppHeader.svelte";
import { route } from "./router.svelte";
import Develop from "./views/Develop.svelte";
import Home from "./views/Home.svelte";
import Manage from "./views/Manage.svelte";
import Settings from "./views/Settings.svelte";

const THEMES = ["default", "dark", "light", "minty", "yeti", "sketchy"];

// The Tauri shell injects its IPC internals into every page it loads, so
// this doubles as the desktop detector. The desktop window uses the native
// title bar (decorations: true) and therefore skips the custom header;
// the browser version keeps it as the branding/status bar.
const isTauri = "__TAURI_INTERNALS__" in window;

$effect(() => {
  // Single source of truth for theming: the data-theme attribute on <html>
  // selects the token block in src/styles/theme.css. No stylesheet swaps,
  // no FOUC, no cascade-order dependencies.
  document.documentElement.dataset.theme = THEMES.includes(status.theme) ? status.theme : "default";
});
</script>

<div id="app" class="h-full">
  {#if !isTauri}
    <AppHeader />
  {/if}
  <main class={isTauri ? "h-full" : "h-[calc(100vh-50px)]"}>
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
