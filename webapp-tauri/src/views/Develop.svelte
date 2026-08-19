<script lang="ts">
import { api } from "../api/client";
import { loadI18n, t } from "../api/i18n.svelte";
import { refreshStatus, status, titleState } from "../api/store.svelte";
import AppAside from "../components/AppAside.svelte";
import { push } from "../router.svelte";

type SubPage = "HomePage" | "Update" | "Remote" | "Utils";
let page = $state<SubPage>("HomePage");

const SUB_TITLES: Record<SubPage, string> = {
  HomePage: "Gui.MenuDevelop.HomePage",
  Update: "Gui.MenuDevelop.Update",
  Remote: "Gui.MenuDevelop.Remote",
  Utils: "Gui.MenuDevelop.Utils",
};

const LANGS = [
  { label: "简体中文", value: "zh-CN" },
  { label: "繁體中文", value: "zh-TW" },
  { label: "English", value: "en-US" },
  { label: "日本語", value: "ja-JP" },
];
const THEMES = [
  { label: "Light", value: "default" },
  { label: "Dark", value: "dark" },
];

// updater data
let updateState = $state("idle");
let history = $state<{
  local: string[] | null;
  upstream: string[] | null;
  history: string[][];
}>({ local: null, upstream: null, history: [] });

async function refreshUpdate() {
  const [st, hist] = await Promise.all([api.updateStatus(), api.updateHistory()]);
  updateState = st.state;
  history = hist;
}

async function checkUpdate() {
  await api.updateCheck();
  const timer = window.setInterval(async () => {
    const st = await api.updateStatus();
    updateState = st.state;
    if (st.state !== "checking") {
      window.clearInterval(timer);
      await refreshUpdate();
    }
  }, 1500);
}

async function runUpdate() {
  await api.updateRun();
  const timer = window.setInterval(async () => {
    const st = await api.updateStatus();
    updateState = st.state;
    if (st.state !== "updating") {
      window.clearInterval(timer);
      await refreshUpdate();
    }
  }, 2000);
}

async function setLanguage(lang: string) {
  await api.setLanguage(lang);
  status.language = lang;
  // t() is reactive: once the new dictionary is loaded the UI re-renders.
  await loadI18n();
}

async function setTheme(theme: string) {
  await api.setTheme(theme);
  status.theme = theme;
}

/** One class string per state so conditional utilities never conflict. */
function pickButtonClass(active: boolean): string {
  return active
    ? "btn-sm border-primary bg-primary text-white hover:bg-primary-hover"
    : "btn-sm border-line-control bg-transparent text-body hover:border-gray-500 hover:bg-gray-800";
}

function onAsideSelect(name: string) {
  if (name === "Manage") {
    push("/manage");
    return;
  }
  if (name === "Home") {
    page = "HomePage";
    return;
  }
  push("/");
}

$effect(() => {
  titleState.value = t(SUB_TITLES[page]);
});

$effect(() => {
  void loadI18n();
  void refreshStatus();
  void refreshUpdate();
  return () => {
    titleState.value = "";
  };
});
</script>

<div class="flex h-full overflow-hidden bg-surface-app">
  <AppAside active="Home" onselect={onAsideSelect} />
  <nav
    class="w-48 flex-shrink-0 overflow-y-auto bg-surface-panel px-2 pt-[1.2rem] [box-shadow:var(--menu-shadow)] [border-right:var(--menu-line)]"
  >
    <button
      class="mb-2 block w-full rounded-none border-0 border-l-3 border-solid border-transparent bg-transparent px-3 py-[1px] text-left font-normal whitespace-pre-wrap [transition:border_.05s_ease-in-out,padding_.05s_ease-in-out] hover:border-l-accent hover:font-bold hover:text-accent"
      class:border-l-accent={page === 'HomePage'}
      class:font-bold={page === 'HomePage'}
      class:text-accent={page === 'HomePage'}
      onclick={() => (page = 'HomePage')}
    >
      {t('Gui.MenuDevelop.HomePage')}
    </button>
    <button
      class="mb-2 block w-full rounded-none border-0 border-l-3 border-solid border-transparent bg-transparent px-3 py-[1px] text-left font-normal whitespace-pre-wrap [transition:border_.05s_ease-in-out,padding_.05s_ease-in-out] hover:border-l-accent hover:font-bold hover:text-accent"
      class:border-l-accent={page === 'Update'}
      class:font-bold={page === 'Update'}
      class:text-accent={page === 'Update'}
      onclick={() => (page = 'Update')}
    >
      {t('Gui.MenuDevelop.Update')}
    </button>
    <button
      class="mb-2 block w-full rounded-none border-0 border-l-3 border-solid border-transparent bg-transparent px-3 py-[1px] text-left font-normal whitespace-pre-wrap [transition:border_.05s_ease-in-out,padding_.05s_ease-in-out] hover:border-l-accent hover:font-bold hover:text-accent"
      class:border-l-accent={page === 'Remote'}
      class:font-bold={page === 'Remote'}
      class:text-accent={page === 'Remote'}
      onclick={() => (page = 'Remote')}
    >
      {t('Gui.MenuDevelop.Remote')}
    </button>
    <button
      class="mb-2 block w-full rounded-none border-0 border-l-3 border-solid border-transparent bg-transparent px-3 py-[1px] text-left font-normal whitespace-pre-wrap [transition:border_.05s_ease-in-out,padding_.05s_ease-in-out] hover:border-l-accent hover:font-bold hover:text-accent"
      class:border-l-accent={page === 'Utils'}
      class:font-bold={page === 'Utils'}
      class:text-accent={page === 'Utils'}
      onclick={() => (page = 'Utils')}
    >
      {t('Gui.MenuDevelop.Utils')}
    </button>
  </nav>

  <div class="grow overflow-y-auto bg-surface-app p-4">
    {#if page === 'HomePage'}
      <p class="mt-4 mb-1.6 text-center">Select your language / 选择语言</p>
      <div class="flex flex-wrap justify-center gap-1.6">
        {#each LANGS as lang (lang.value)}
          <button class={pickButtonClass(status.language === lang.value)} onclick={() => setLanguage(lang.value)}>
            {lang.label}
          </button>
        {/each}
      </div>
      <p class="mt-4 mb-1.6 text-center">Change theme / 更改主题</p>
      <div class="flex flex-wrap justify-center gap-1.6">
        {#each THEMES as theme (theme.value)}
          <button class={pickButtonClass(status.theme === theme.value)} onclick={() => setTheme(theme.value)}>
            {theme.label}
          </button>
        {/each}
      </div>
      <p class="mt-4 mb-1.6 text-center">
        Joxos fork of Alas — focused on: UnoCSS frontend rewrite, Tauri desktop shell, webui log/scheduler fixes, and dead-code cleanup.
        <a href="https://github.com/Joxos/AzurLaneAutoScript" target="_blank" rel="noreferrer">
          https://github.com/Joxos/AzurLaneAutoScript
        </a>
      </p>
    {:else if page === 'Update'}
      <div class="mb-3 flex items-center gap-2">
        {#if updateState === 'checking'}
          <span
            class="inline-block h-4 w-4 rounded-full border-[0.2em] border-solid border-r-transparent [animation:spinner-border_.75s_linear_infinite]"
          ></span>
          <span>{t('Gui.Update.UpdateChecking')}</span>
        {:else if updateState === 'available'}
          <span class="text-[var(--text-success)]">{t('Gui.Update.HaveUpdate')}</span>
          <button class="btn-sm border-success bg-success text-white hover:bg-success-hover" onclick={runUpdate}>
            {t('Gui.Button.ClickToUpdate')}
          </button>
        {:else if updateState === 'failed'}
          <span class="text-[var(--text-danger)]">{t('Gui.Update.UpdateFailed')}</span>
          <button class="btn-sm border-info bg-info text-white hover:bg-info-hover" onclick={checkUpdate}>
            {t('Gui.Button.CheckUpdate')}
          </button>
        {:else}
          <span>{t('Gui.Update.UpToDate')}</span>
          <button class="btn-sm border-info bg-info text-white hover:bg-info-hover" onclick={checkUpdate}>
            {t('Gui.Button.CheckUpdate')}
          </button>
        {/if}
      </div>

      <table class="table">
        <thead>
          <tr>
            <th></th>
            <th>SHA1</th>
            <th>{t('Gui.Update.Author')}</th>
            <th>{t('Gui.Update.Time')}</th>
            <th>{t('Gui.Update.Message')}</th>
          </tr>
        </thead>
        <tbody>
          {#if history.local}
            <tr>
              <td>{t('Gui.Update.Local')}</td>
              {#each history.local as cell (cell)}
                <td>{cell}</td>
              {/each}
            </tr>
          {/if}
          {#if history.upstream}
            <tr>
              <td>{t('Gui.Update.Upstream')}</td>
              {#each history.upstream as cell (cell)}
                <td>{cell}</td>
              {/each}
            </tr>
          {/if}
        </tbody>
      </table>

      <p class="mb-1">{t('Gui.Update.DetailedHistory')}</p>
      <table class="table">
        <thead>
          <tr>
            <th>SHA1</th>
            <th>{t('Gui.Update.Author')}</th>
            <th>{t('Gui.Update.Time')}</th>
            <th>{t('Gui.Update.Message')}</th>
          </tr>
        </thead>
        <tbody>
          {#each history.history as commit, i (i)}
            <tr>
              {#each commit as cell, j (j)}
                <td>{cell}</td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    {:else if page === 'Remote'}
      <p class="mt-0 mb-4 text-muted">未支持</p>
    {:else}
      <p class="mt-0 mb-4 text-muted">未实现</p>
    {/if}
  </div>
</div>
