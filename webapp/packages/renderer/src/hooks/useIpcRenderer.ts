import {ref} from 'vue';

const useIpcRenderer = () => {
    return ref(require('electron').ipcRenderer);
};

export default useIpcRenderer;
