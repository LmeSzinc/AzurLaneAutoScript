<script lang="ts">
import { t } from "../api/i18n.svelte";
import { selectInstance, status } from "../api/store.svelte";

let {
  active = "",
  onselect,
}: {
  active?: string;
  onselect?: (name: string) => void;
} = $props();

/** Icon skeleton shared by all aside entries (mask-image comes per icon).
 *  Longhands only: a `mask:` shorthand resets mask-image to `none`. */
const ICON =
  "mx-auto mb-1.5 block h-8 w-8 bg-icon [mask-position:center] [mask-repeat:no-repeat] [mask-size:contain] " +
  "[-webkit-mask-position:center] [-webkit-mask-repeat:no-repeat] [-webkit-mask-size:contain]";
</script>

<aside
  class="flex flex-shrink-0 flex-col overflow-y-auto bg-surface-side pl-0.5 pr-[0.325rem] pt-4 [z-index:91] [border-right:var(--aside-line)]"
>
  <button
    class="mb-1.5 w-16 flex-col rounded-none border-0 border-l-4 border-solid border-transparent bg-transparent px-0 pt-1.5 pb-3 text-[0.8rem] font-normal [transition:border_.1s_ease-in-out,padding_.1s_ease-in-out] hover:border-l-accent hover:pl-[3px] hover:font-bold hover:text-accent"
    class:border-l-accent={active === 'Home'}
    class:pl-[3px]={active === 'Home'}
    class:font-bold={active === 'Home'}
    class:text-accent={active === 'Home'}
    onclick={() => onselect?.('Home')}
  >
    <span
      class="{ICON} [mask-image:url('/icon/develop.svg')] [-webkit-mask-image:url('/icon/develop.svg')]"
    ></span>
    {t('Gui.Aside.Home')}
  </button>
  {#each status.instances as inst (inst.name)}
    <button
      class="mb-1.5 w-16 flex-col rounded-none border-0 border-l-4 border-solid border-transparent bg-transparent px-0 pt-1.5 pb-3 text-[0.8rem] font-normal [transition:border_.1s_ease-in-out,padding_.1s_ease-in-out] hover:border-l-accent hover:pl-[3px] hover:font-bold hover:text-accent"
      class:border-l-accent={active === inst.name}
      class:pl-[3px]={active === inst.name}
      class:font-bold={active === inst.name}
      class:text-accent={active === inst.name}
      onclick={() => {
        selectInstance(inst.name);
        onselect?.(inst.name);
      }}
    >
      <span class="{ICON} [mask-image:url('/icon/run.svg')] [-webkit-mask-image:url('/icon/run.svg')]"></span>
      {inst.name}
    </button>
  {/each}
  <button
    class="mb-1.5 w-16 flex-col rounded-none border-0 border-l-4 border-solid border-transparent bg-transparent px-0 pt-1.5 pb-3 text-[0.8rem] font-normal [transition:border_.1s_ease-in-out,padding_.1s_ease-in-out] hover:border-l-accent hover:pl-[3px] hover:font-bold hover:text-accent"
    class:border-l-accent={active === 'Manage'}
    class:pl-[3px]={active === 'Manage'}
    class:font-bold={active === 'Manage'}
    class:text-accent={active === 'Manage'}
    onclick={() => onselect?.('Manage')}
  >
    <span
      class="{ICON} [mask-image:url('/icon/setting.svg')] [-webkit-mask-image:url('/icon/setting.svg')]"
    ></span>
    {t('Gui.AddAlas.Manage')}
  </button>
</aside>
