/// <reference types="vite/client" />

/**
 * Describes all existing environment variables and their types.
 * Assists in autocomplete and typechecking
 *
 * @see https://github.com/vitejs/vite/blob/eef51cb37db98a1ad9a541bdd3cd74736ff8488d/packages/vite/types/importMeta.d.ts#L62-L69 Base Interface
 */
interface ImportMetaEnv {

  /**
   * The value of the variable is set in scripts/watch.js and depend on packages/main/vite.config.js
   */
  VITE_DEV_SERVER_URL: undefined | string;
}
