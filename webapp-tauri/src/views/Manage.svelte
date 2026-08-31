<script lang="ts">
import { api } from "../api/client";
import { loadI18n, t } from "../api/i18n.svelte";
import { refreshStatus } from "../api/store.svelte";
import AppAside from "../components/AppAside.svelte";
import { push } from "../router.svelte";

interface ConfigFile {
  name: string;
  modified: string;
}

let configs = $state<ConfigFile[]>([]);
let newName = $state("");
let error = $state("");
let fileInput = $state<HTMLInputElement | null>(null);

async function refresh() {
  configs = await api.configs();
}

async function createConfig() {
  error = "";
  const res = await api.newInstance(newName);
  if (!res.ok) {
    error = res.error ?? "Failed";
    return;
  }
  newName = "";
  await refresh();
  await refreshStatus();
}

function pickImportFile() {
  fileInput?.click();
}

async function importFile(event: Event) {
  error = "";
  const input = event.currentTarget as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  const text = await file.text();
  let config: Record<string, unknown>;
  try {
    config = JSON.parse(text);
  } catch {
    error = "Invalid JSON file";
    return;
  }
  const name = file.name.replace(/\.json$/, "");
  await api.importConfig(name, config);
  input.value = "";
  await refresh();
  await refreshStatus();
}

async function exportConfig(name: string) {
  const res = await fetch(`/config/${name}/export`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${name}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

async function renameConfig(name: string) {
  error = "";
  const newName = window.prompt(t("Gui.AppManage.RenamePrompt"), name)?.trim();
  if (!newName || newName === name) return;
  const res = await api.renameInstance(name, newName);
  if (!res.ok) {
    error = res.error ?? "Failed";
    return;
  }
  await refresh();
  await refreshStatus();
}

async function deleteConfig(name: string) {
  error = "";
  if (!window.confirm(t("Gui.AppManage.DeleteConfirm", { name }))) return;
  const res = await api.deleteInstance(name);
  if (!res.ok) {
    error = res.error ?? "Failed";
    return;
  }
  await refresh();
  await refreshStatus();
}

function onAsideSelect(name: string) {
  if (name === "Manage") {
    return;
  }
  if (name === "Home") {
    push("/develop");
    return;
  }
  push("/");
}

$effect(() => {
  void loadI18n();
  void refreshStatus();
  void refresh();
});
</script>

<div class="flex h-full overflow-hidden bg-surface-app">
  <AppAside active="Manage" onselect={onAsideSelect} />
  <div class="grow overflow-y-auto bg-surface-app p-4">
    <h4 class="mt-0 mb-2 text-[1.5rem] font-medium leading-[1.2]">{t('Gui.AppManage.PageTitle')}</h4>
    {#if error}
      <div
        class="relative mb-4 rounded-[var(--alert-radius)] border border-solid px-5 py-3 [border-width:var(--alert-bw)] [font-size:var(--alert-fs,inherit)] [font-weight:var(--alert-fw,inherit)] [border-color:var(--danger-line)] [background:var(--danger-bg)] [color:var(--danger-fg)]"
      >
        {error}
      </div>
    {/if}

    <table class="table max-w-[640px] [&_th]:font-medium">
      <thead>
        <tr>
          <th>{t('Gui.AppManage.Name')}</th>
          <th>{t('Gui.AppManage.Modified')}</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {#each configs as cfg (cfg.name)}
          <tr>
            <td>{cfg.name}</td>
            <td>{cfg.modified}</td>
            <td class="text-end whitespace-nowrap">
              <button
                class="btn-sm border-line-control bg-transparent text-body hover:border-gray-500 hover:bg-gray-800"
                onclick={() => renameConfig(cfg.name)}
              >
                {t('Gui.AppManage.Rename')}
              </button>
              <button
                class="btn-sm border-line-control bg-transparent text-body hover:border-gray-500 hover:bg-gray-800"
                onclick={() => exportConfig(cfg.name)}
              >
                {t('Gui.AppManage.Export')}
              </button>
              <button
                class="btn-sm border-danger bg-transparent text-danger hover:bg-danger"
                onclick={() => deleteConfig(cfg.name)}
              >
                {t('Gui.AppManage.Delete')}
              </button>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>

    <div class="mt-3 flex items-center gap-2">
      <input
        class="block h-auto w-full max-w-[220px] rounded-none border-0 bg-surface-insert px-2 py-1 text-[var(--text-input-sm)] leading-6 [color:var(--input-fg)] focus:bg-surface-hover focus:outline-none"
        placeholder="config name"
        bind:value={newName}
      />
      <button class="btn-sm border-success bg-success text-white hover:bg-success-hover" disabled={!newName} onclick={createConfig}>
        {t('Gui.AppManage.New')}
      </button>
      <button
        class="btn-sm border-line-control bg-transparent text-body hover:border-gray-500 hover:bg-gray-800"
        onclick={pickImportFile}
      >
        {t('Gui.AppManage.Import')}
      </button>
      <input bind:this={fileInput} type="file" accept=".json" style="display: none" onchange={importFile} />
    </div>
  </div>
</div>
