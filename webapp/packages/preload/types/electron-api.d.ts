<<<<<<< HEAD
interface ElectronApi {
  readonly versions: Readonly<NodeJS.ProcessVersions>;
}

declare interface Window {
  electron: Readonly<ElectronApi>;
  electronRequire?: NodeRequire;
=======

interface ElectronApi {
  readonly versions: Readonly<NodeJS.ProcessVersions>
}

declare interface Window {
  electron: Readonly<ElectronApi>
  electronRequire?: NodeRequire
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
}
