import type {BrowserWindowOpts} from '@/core/Browser';
import {BrowserWindowsIdentifier} from '@alas/common';

export const home: BrowserWindowOpts = {
  identifier: BrowserWindowsIdentifier.start,
  width: 1280,
  height: 880,
  devTools: true,
};
