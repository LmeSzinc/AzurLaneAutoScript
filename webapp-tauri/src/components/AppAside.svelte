<script lang="ts">
import { t } from "../api/i18n.svelte";
import { status } from "../api/store.svelte";

let {
  active = "",
  onselect,
}: {
  active?: string;
  onselect?: (name: string) => void;
} = $props();
</script>

<aside
  class="[z-index:91] pl-0.5 pr-[0.325rem] pt-4 overflow-y-auto flex-shrink-0 flex flex-col [background:var(--alas-shell-side)] [border-right:var(--alas-aside-border-right)]"
>
  <button class="btn-aside" class:btn-aside-active={active === 'Home'} onclick={() => onselect?.('Home')}>
    <span class="aside-icon [mask-image:url('/icon/develop.svg')] [-webkit-mask-image:url('/icon/develop.svg')]"></span>
    {t('Gui.Aside.Home')}
  </button>
  {#each status.instances as inst (inst.name)}
    <button class="btn-aside" class:btn-aside-active={active === inst.name} onclick={() => onselect?.(inst.name)}>
      <span class="aside-icon [mask-image:url('/icon/run.svg')] [-webkit-mask-image:url('/icon/run.svg')]"></span>
      {inst.name}
    </button>
  {/each}
  <button class="btn-aside" class:btn-aside-active={active === 'Manage'} onclick={() => onselect?.('Manage')}>
    <span class="aside-icon [mask-image:url('/icon/setting.svg')] [-webkit-mask-image:url('/icon/setting.svg')]"></span>
    {t('Gui.AddAlas.Manage')}
  </button>
</aside>
