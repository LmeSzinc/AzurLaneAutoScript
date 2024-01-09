import type {MainEvents} from '@alas/common';
import {onBeforeMount} from 'vue';
/**
 * 在 renderer 监听 main 发过来的 event
 */
const useAppEvent = <T extends keyof MainEvents>(
  eventName: T,
  callback: (e: Event & {data?: MainEvents[T]}) => void,
) => {
  const kitchenEvent = `electron:${eventName}`;
  onBeforeMount(() => {
    window.addEventListener(kitchenEvent, callback);
    return () => {
      window.removeEventListener(kitchenEvent, callback);
    };
  });
};

export default useAppEvent;
