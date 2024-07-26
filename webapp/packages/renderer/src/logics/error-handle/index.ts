import type {App} from 'vue';
import useIpcRenderer from '/@/hooks/useIpcRenderer';
import {PAGE_ERROR} from '@common/constant/eventNames';
import type {ErrorLogInfo} from '/#/store';
import {ErrorTypeEnum} from '/#/store';

function addErrorLogInfo(info: Record<any, any>) {
  const {ipcRendererSend} = useIpcRenderer();
  ipcRendererSend(PAGE_ERROR, JSON.stringify(info));
}

/**
 * get comp name
 * @param vm
 */
function formatComponentName(vm: any) {
  if (vm.$root === vm) {
    return {
      name: 'root',
      path: 'root',
    };
  }

  const options = vm.$options as any;
  if (!options) {
    return {
      name: 'anonymous',
      path: 'anonymous',
    };
  }
  const name = options.name || options._componentTag;
  return {
    name: name,
    path: options.__file,
  };
}

export function scriptErrorHandler(
  event: Event | string,
  source?: string,
  lineno?: number,
  colno?: number,
  error?: Error,
) {
  if (event === 'Script error.' && !source) {
    return false;
  }
  const errorInfo: Partial<ErrorLogInfo> = {};
  colno = colno || (window.event && (window.event as any).errorCharacter) || 0;
  errorInfo.message = event as string;
  if (error?.stack) {
    errorInfo.stack = error.stack;
  } else {
    errorInfo.stack = '';
  }
  const name = source ? source.substr(source.lastIndexOf('/') + 1) : 'script';
  addErrorLogInfo({
    type: ErrorTypeEnum.SCRIPT,
    name: name,
    file: source as string,
    detail: 'lineno' + lineno,
    url: window.location.href,
    ...(errorInfo as Pick<ErrorLogInfo, 'message' | 'stack'>),
  });
  return true;
}

/**
 * Handling error stack information
 * @param error
 */
function processStackMsg(error: Error) {
  if (!error.stack) {
    return '';
  }
  let stack = error.stack
    .replace(/\n/gi, '') // Remove line breaks to save the size of the transmitted content
    .replace(/\bat\b/gi, '@') // At in chrome, @ in ff
    .split('@') // Split information with @
    .slice(0, 9) // The maximum stack length (Error.stackTraceLimit = 10), so only take the first 10
    .map(v => v.replace(/^\s*|\s*$/g, '')) // Remove extra spaces
    .join('~') // Manually add separators for later display
    .replace(/\?[^:]+/gi, ''); // Remove redundant parameters of js file links (?x=1 and the like)
  const msg = error.toString();
  if (stack.indexOf(msg) < 0) {
    stack = msg + '@' + stack;
  }
  return stack;
}

function vueErrorHandler(err: Error, vm: any, info: string) {
  const {name, path} = formatComponentName(vm);
  addErrorLogInfo({
    type: ErrorTypeEnum.VUE,
    name,
    file: path,
    message: err.message,
    stack: processStackMsg(err),
    detail: info,
    url: window.location.href,
  });
}

function registerPromiseErrorHandler() {
  window.addEventListener(
    'unhandledrejection',
    function (event) {
      addErrorLogInfo({
        type: ErrorTypeEnum.PROMISE,
        name: 'Promise Error!',
        file: 'none',
        detail: 'promise error!',
        url: window.location.href,
        stack: 'promise error!',
        message: event.reason,
      });
    },
    true,
  );
}

function registerResourceErrorHandler() {
  // Monitoring resource loading error(img,script,css,and jsonp)
  window.addEventListener(
    'error',
    function (e: Event) {
      const target = e.target ? e.target : (e.srcElement as any);
      addErrorLogInfo({
        type: ErrorTypeEnum.RESOURCE,
        name: 'Resource Error!',
        file: (e.target || ({} as any)).currentSrc,
        detail: JSON.stringify({
          tagName: target.localName,
          html: target.outerHTML,
          type: e.type,
        }),
        url: window.location.href,
        stack: 'resource is not found',
        message: (e.target || ({} as any)).localName + ' is load error',
      });
    },
    true,
  );
}

export function setupErrorHandle(app: App) {
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  app.config.errorHandler = vueErrorHandler;

  // script error
  window.onerror = scriptErrorHandler;

  registerPromiseErrorHandler();
  registerResourceErrorHandler();
}
