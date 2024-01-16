/**
 * 创建日志代理方法
 * @param logLevel 日志级别
 * @param mainLogger 日志对象
 * @return {function}
 */
export const createLogProxy =
  (logLevel: string, mainLogger: any): Function =>
  (fn: Function) =>
  (...args: any) => {
    fn(...args);
    mainLogger[logLevel](...args);
  };
