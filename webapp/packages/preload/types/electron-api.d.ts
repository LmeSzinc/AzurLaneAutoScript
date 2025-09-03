
interface ElectronApi {
  readonly versions: Readonly<NodeJS.ProcessVersions>
}

declare interface Window {
  electron: Readonly<ElectronApi>
  electronRequire?: NodeRequire
}
