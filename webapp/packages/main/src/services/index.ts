import {ServiceStorage} from '@/core/ServiceStorage';
import type {App} from '@/core/App';
import type {RendererEvents} from '@alas/common';

const baseDecorator =
  (name: string, showLog = true) =>
  (target: any, methodName: string, descriptor: any) => {
    const actions = ServiceStorage.services.get(target.constructor) || [];
    actions.push({
      name,
      methodName,
      showLog,
    });
    ServiceStorage.services.set(target.constructor, actions);
    return descriptor;
  };

/**
 *  service 用的 event 装饰器
 */
export const event = (url: keyof RendererEvents) => baseDecorator(url);

export class ServiceModule {
  constructor(public app: App) {
    this.app = app;
  }
}

export type TServiceModule = typeof ServiceModule;
