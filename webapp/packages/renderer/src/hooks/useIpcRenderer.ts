const useIpcRenderer = () => {
    return {
        ipcRendererSend: window.__electron_preload__ipcRendererSend,
        ipcRendererOn: window.__electron_preload__ipcRendererOn,
    };
};

export default useIpcRenderer;
