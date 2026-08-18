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

<div class="develop-wrap">
  <AppAside active="Home" onselect={onAsideSelect} />
  <nav class="dev-menu">
    <button class="btn btn-menu" class:btn-menu-active={page === 'HomePage'} onclick={() => (page = 'HomePage')}>
      {t('Gui.MenuDevelop.HomePage')}
    </button>
    <button class="btn btn-menu" class:btn-menu-active={page === 'Update'} onclick={() => (page = 'Update')}>
      {t('Gui.MenuDevelop.Update')}
    </button>
    <button class="btn btn-menu" class:btn-menu-active={page === 'Remote'} onclick={() => (page = 'Remote')}>
      {t('Gui.MenuDevelop.Remote')}
    </button>
    <button class="btn btn-menu" class:btn-menu-active={page === 'Utils'} onclick={() => (page = 'Utils')}>
      {t('Gui.MenuDevelop.Utils')}
    </button>
  </nav>

  <div class="content">
    {#if page === 'HomePage'}
      <p class="center-text">Select your language / 选择语言</p>
      <div class="center-btns">
        {#each LANGS as lang (lang.value)}
          <button
            class="btn btn-sm"
            class:btn-primary={status.language === lang.value}
            class:btn-adaptive={status.language !== lang.value}
            onclick={() => setLanguage(lang.value)}
          >
            {lang.label}
          </button>
        {/each}
      </div>
      <p class="center-text">Change theme / 更改主题</p>
      <div class="center-btns">
        {#each THEMES as theme (theme.value)}
          <button
            class="btn btn-sm"
            class:btn-primary={status.theme === theme.value}
            class:btn-adaptive={status.theme !== theme.value}
            onclick={() => setTheme(theme.value)}
          >
            {theme.label}
          </button>
        {/each}
      </div>
      <p class="center-text">
        Alas is a free open source software.
        <a href="https://github.com/LmeSzinc/AzurLaneAutoScript" target="_blank" rel="noreferrer">
          https://github.com/LmeSzinc/AzurLaneAutoScript
        </a>
      </p>
    {:else if page === 'Update'}
      <div class="d-flex align-items-center gap-2 mb-3">
        {#if updateState === 'checking'}
          <span class="spinner-border spinner-border-sm"></span>
          <span>{t('Gui.Update.UpdateChecking')}</span>
        {:else if updateState === 'available'}
          <span class="text-success">{t('Gui.Update.HaveUpdate')}</span>
          <button class="btn btn-sm btn-success" onclick={runUpdate}>
            {t('Gui.Button.ClickToUpdate')}
          </button>
        {:else if updateState === 'failed'}
          <span class="text-danger">{t('Gui.Update.UpdateFailed')}</span>
          <button class="btn btn-sm btn-info" onclick={checkUpdate}>
            {t('Gui.Button.CheckUpdate')}
          </button>
        {:else}
          <span>{t('Gui.Update.UpToDate')}</span>
          <button class="btn btn-sm btn-info" onclick={checkUpdate}>
            {t('Gui.Button.CheckUpdate')}
          </button>
        {/if}
      </div>

      <table class="table table-sm compare-table">
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
      <table class="table table-sm history-table">
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
      <p class="text-muted">未支持</p>
    {:else}
      <p class="text-muted">未实现</p>
    {/if}
  </div>
</div>

<style>
  .develop-wrap {
    height: 100%;
    display: flex;
    overflow: hidden;
  }
  .dev-menu {
    flex-shrink: 0;
    width: 12rem;
    padding: 1.2rem 0.5rem;
    overflow-y: auto;
  }
  .dev-menu .btn-menu {
    display: block;
    width: 100%;
  }
  .content {
    flex-grow: 1;
    padding: 1rem;
    overflow-y: auto;
  }
  .center-text {
    text-align: center;
    margin: 1rem 0 0.4rem;
  }
  .center-btns {
    display: flex;
    gap: 0.4rem;
    justify-content: center;
    flex-wrap: wrap;
  }
</style>
