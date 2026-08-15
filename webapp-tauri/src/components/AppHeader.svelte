<script lang="ts">
  import { invoke } from '@tauri-apps/api/core'
  import { status, titleState } from '../api/store.svelte'
  import { t } from '../api/i18n.svelte'
  import { route } from '../router.svelte'

  const isTauri = '__TAURI_INTERNALS__' in window

  const stateText = $derived.by(() => {
    const state = status.instances[0]?.state ?? 0
    if (state === 1) return t('Gui.Status.Running')
    if (state === 3) return t('Gui.Status.Warning')
    if (state === 4) return t('Gui.Status.Updating')
    return t('Gui.Status.Inactive')
  })

  const stateClass = $derived.by(() => {
    const state = status.instances[0]?.state ?? 0
    if (state === 1) return 'header-state-running'
    if (state === 3) return 'header-state-warning'
    if (state === 4) return 'header-state-updating'
    return 'header-state-inactive'
  })

  const pageTitleText = $derived.by(() => {
    if (titleState.value) return titleState.value
    if (route.path === '/settings') {
      const task = route.query.task ?? ''
      return task ? t(`Task.${task}.name`) : ''
    }
    if (route.path === '/develop') return t('Gui.Aside.Home')
    if (route.path === '/manage') return t('Gui.AppManage.PageTitle')
    return t('Gui.MenuAlas.Overview')
  })

  function min() {
    void invoke('window_min')
  }
  function max() {
    void invoke('window_max')
  }
  function close() {
    void invoke('window_close')
  }
</script>

<header class="app-header">
  <img class="header-icon" src="icon/alas.png" alt="Alas" />
  <span class="header-text">Alas</span>
  <span class="header-state {stateClass}">
    <span class="header-state-dot"></span>
    {stateText}
  </span>
  <div class="header-title">
    <span class="header-title-text">{pageTitleText}</span>
  </div>
  {#if isTauri}
    <div class="app-header-controls">
      <button class="header-btn" title="Minimize" onclick={min}>&#x2212;</button>
      <button class="header-btn" title="Maximize" onclick={max}>&#x25A1;</button>
      <button class="header-btn header-btn-close" title="Close" onclick={close}>&#x2715;</button>
    </div>
  {/if}
</header>

<style>
  .app-header {
    display: grid;
    grid-auto-flow: column;
    grid-template-columns: 4.4rem 4rem auto 1fr auto;
    align-items: center;
    height: 50px;
    user-select: none;
    -webkit-app-region: drag;
  }
  .header-icon {
    width: 42px;
    height: 42px;
    margin: 0.25rem auto;
  }
  .header-text {
    font-size: 1.5rem;
    font-weight: bold;
    margin: auto !important;
  }
  .header-state {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.85rem;
    margin: auto;
  }
  .header-state-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #8a939c;
  }
  .header-state-running .header-state-dot {
    background: #4cd07d;
  }
  .header-state-warning .header-state-dot {
    background: #e6a23c;
  }
  .header-state-updating .header-state-dot {
    background: #4c9aff;
  }
  .header-title {
    margin: auto;
  }
  .header-title-text {
    font-size: 1.2rem;
    margin: auto;
    overflow: hidden;
    text-align: center;
    white-space: nowrap;
  }
  .app-header-controls {
    display: flex;
    height: 100%;
    -webkit-app-region: no-drag;
  }
  .header-btn {
    width: 44px;
    height: 100%;
    border: none;
    background: transparent;
    font-size: 12px;
    cursor: pointer;
  }
  .header-btn:hover {
    background: rgba(255, 255, 255, 0.08);
  }
  .header-btn-close:hover {
    background: #c42b1c;
    color: #fff;
  }
</style>
