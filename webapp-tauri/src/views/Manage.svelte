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

<div class="manage-wrap">
  <AppAside active="Manage" onselect={onAsideSelect} />
  <div class="content">
    <h4>{t('Gui.AppManage.PageTitle')}</h4>
    {#if error}
      <div class="alert alert-danger">{error}</div>
    {/if}

    <table class="table table-sm config-table">
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
            <td class="text-end">
              <button class="btn btn-sm btn-adaptive" onclick={() => exportConfig(cfg.name)}>
                {t('Gui.AppManage.Export')}
              </button>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>

    <div class="d-flex gap-2 mt-3 align-items-center">
      <input
        class="form-control form-control-sm"
        style="max-width: 220px"
        placeholder="config name"
        bind:value={newName}
      />
      <button class="btn btn-sm btn-success" disabled={!newName} onclick={createConfig}>
        {t('Gui.AppManage.New')}
      </button>
      <button class="btn btn-sm btn-adaptive" onclick={pickImportFile}>
        {t('Gui.AppManage.Import')}
      </button>
      <input bind:this={fileInput} type="file" accept=".json" style="display: none" onchange={importFile} />
    </div>
  </div>
</div>

<style>
  .manage-wrap {
    height: 100%;
    display: flex;
    overflow: hidden;
  }
  .content {
    flex-grow: 1;
    padding: 1rem;
    overflow-y: auto;
  }
  .config-table {
    max-width: 640px;
  }
  .config-table th {
    font-weight: 500;
  }
</style>
