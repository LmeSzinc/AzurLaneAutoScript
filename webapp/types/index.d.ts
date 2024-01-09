declare module '*.json' {
  const jsonValue: any;
  export default jsonValue;
}

declare module '*.mjs' {
  const mjsValue: never;
  export default mjsValue;
}

declare type Recordable<T = any> = Record<string, T>;
