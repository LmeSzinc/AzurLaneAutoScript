import type {AlasConfig} from '../../../preload/src/alasConfig';
import type {ComputedRef} from 'vue';
import {computed} from 'vue';

export default function useAlasConfig(): ComputedRef<AlasConfig> {
    return computed(() => window.__electron_preload__getAlasConfig());
}
