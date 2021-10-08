export function useElectron(): Readonly<ElectronApi> {
  return window.electron;
}
