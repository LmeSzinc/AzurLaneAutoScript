import type {BrowserWindowOpts} from '@/core/Browser';
import {BrowserWindowsIdentifier} from '@alas/common';

export const index: BrowserWindowOpts = {
  identifier: BrowserWindowsIdentifier.index,
  width: 1280,
  height: 880,
  devTools: false,
};
