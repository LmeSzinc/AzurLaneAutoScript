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

// release updater data
type UpdStatus = Awaited<ReturnType<typeof api.updateStatus>>;
let upd = $state<UpdStatus | null>(null);

async function refreshUpdate() {
  try {
    upd = await api.updateStatus();
  } catch {
    // backend offline: keep whatever we had
  }
}

async function refreshReleases() {
  await api.updateRefresh();
  const timer = window.setInterval(async () => {
    const st = await api.updateStatus();
    upd = st;
    if (st.state !== "refreshing") {
      window.clearInterval(timer);
    }
  }, 1500);
}

async function installRelease(tag: string) {
  const res = await api.updateInstall(tag);
  if (!res.ok && res.error && upd) {
    upd = { ...upd, state: "failed", error: res.error };
    return;
  }
  // Poll until the install finishes (or fails); the app restarts on success.
  const timer = window.setInterval(async () => {
    const st = await api.updateStatus();
    upd = st;
    if (!st.installing) {
      window.clearInterval(timer);
    }
  }, 1500);
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
        <span class="text-muted">
          {t('Gui.Update.CurrentVersion')}: {upd?.current ?? '…'}
        </span>
        <span class="text-muted text-[0.8rem]">({upd?.repo ?? ''})</span>
        <button class="btn-sm border-info bg-info text-white hover:bg-info-hover" onclick={refreshReleases}>
          {t('Gui.Update.Refresh')}
        </button>
      </div>

      {#if upd?.state === 'refreshing'}
        <span
          class="inline-block h-4 w-4 rounded-full border-[0.2em] border-solid border-r-transparent [animation:spinner-border_.75s_linear_infinite]"
        ></span>
        <span>{t('Gui.Update.UpdateChecking')}</span>
      {:else if upd?.state === 'failed' && upd.error}
        <p class="text-[var(--text-danger)]">{t('Gui.Update.UpdateFailed')}: {upd.error}</p>
      {/if}

      {#if upd?.installing}
        <div class="panel mb-3 p-2.5">
          <p>
            {t('Gui.Update.Installing')}: {upd.installing.version} — {upd.installing.stage} ({upd.installing.progress}%)
          </p>
          <div class="h-2 w-full overflow-hidden bg-surface-hr">
            <div class="h-full bg-accent" style:width="{upd.installing.progress}%"></div>
          </div>
        </div>
      {/if}

      {#if !upd?.releases?.length}
        <p class="text-muted">{t('Gui.Update.NoReleases')}</p>
      {:else}
        {#each upd.releases as rel (rel.tag)}
          <div class="panel mb-3 p-2.5">
            <div class="flex items-center justify-between gap-2">
              <span class="font-medium">
                {rel.name}
                <span class="text-muted text-[0.8rem]">({rel.tag})</span>
                {#if rel.prerelease}
                  <span class="text-muted text-[0.8rem]"> [pre-release]</span>
                {/if}
              </span>
              <button
                class="btn-sm border-success bg-success text-white hover:bg-success-hover disabled:opacity-50"
                onclick={() => installRelease(rel.tag)}
                disabled={upd?.installing != null}
              >
                {t('Gui.Update.Install')}
              </button>
            </div>
            {#if rel.date}
              <p class="mt-0.5 text-[0.8rem] text-muted">{rel.date}</p>
            {/if}
            {#if rel.body}
              <pre class="mt-1 max-h-40 overflow-y-auto whitespace-pre-wrap text-[0.85rem]">{rel.body}</pre>
            {/if}
          </div>
        {/each}
        <p class="text-muted text-[0.85rem]">{t('Gui.Update.InstallHint')}</p>
      {/if}
    {:else if page === 'Remote'}
      <p class="mt-0 mb-4 text-muted">未支持</p>
    {:else}
      <p class="mt-0 mb-4 text-muted">未实现</p>
    {/if}
  </div>
</div>
