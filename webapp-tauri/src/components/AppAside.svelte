<script lang="ts">
  import { status } from '../api/store.svelte'
  import { t } from '../api/i18n.svelte'

  let {
    active = '',
    onselect,
  }: {
    active?: string
    onselect?: (name: string) => void
  } = $props()

  function stateClass(state: number): string {
    if (state === 1) return 'aside-state-running'
    if (state === 3) return 'aside-state-warning'
    if (state === 4) return 'aside-state-updating'
    return ''
  }
</script>

<aside class="app-aside">
  <button
    class="btn btn-aside"
    class:btn-aside-active={active === 'Home'}
    onclick={() => onselect?.('Home')}
  >
    <span class="aside-icon icon-develop"></span>
    {t('Gui.Aside.Home')}
  </button>
  {#each status.instances as inst (inst.name)}
    <button
      class="btn btn-aside"
      class:btn-aside-active={active === inst.name}
      onclick={() => onselect?.(inst.name)}
    >
      <span class="aside-icon icon-run"></span>
      <span class="aside-state-dot {stateClass(inst.state)}"></span>
      {inst.name}
    </button>
  {/each}
  <button
    class="btn btn-aside"
    class:btn-aside-active={active === 'Manage'}
    onclick={() => onselect?.('Manage')}
  >
    <span class="aside-icon icon-setting"></span>
    {t('Gui.AddAlas.Manage')}
  </button>
</aside>

<style>
  .app-aside {
    z-index: 91;
    padding-left: 0.125rem;
    padding-right: 0.325rem;
    padding-top: 1rem;
    overflow-y: auto;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
  }
  .aside-icon {
    display: block;
    width: 2rem;
    height: 2rem;
    margin: 0 auto 2px;
    background-color: currentColor;
    -webkit-mask: no-repeat center / contain;
    mask: no-repeat center / contain;
  }
  .icon-develop {
    -webkit-mask-image: url('icon/develop.svg');
    mask-image: url('icon/develop.svg');
  }
  .icon-run {
    -webkit-mask-image: url('icon/run.svg');
    mask-image: url('icon/run.svg');
  }
  .icon-setting {
    -webkit-mask-image: url('icon/setting.svg');
    mask-image: url('icon/setting.svg');
  }
  .aside-state-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 3px;
    background: #8a939c;
  }
  .aside-state-running {
    background: #4cd07d;
  }
  .aside-state-warning {
    background: #e6a23c;
  }
  .aside-state-updating {
    background: #4c9aff;
  }
</style>
