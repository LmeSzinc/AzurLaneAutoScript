import { describe, expect, it } from 'vitest'

import { ansiToHtml } from './ansi'

describe('ansiToHtml', () => {
  it('returns plain text unchanged', () => {
    expect(ansiToHtml('hello world')).toBe('hello world')
  })

  it('escapes HTML before mapping SGR codes', () => {
    expect(ansiToHtml('<a> & "')).toBe('&lt;a&gt; &amp; "')
  })

  it('maps SGR colors to theme-aware spans and resets them', () => {
    expect(ansiToHtml('\x1b[31mred\x1b[0mplain')).toBe('<span style="color:var(--bs-danger)">red</span>plain')
  })

  it('combines multiple styles in one span', () => {
    expect(ansiToHtml('\x1b[1;31mbold red\x1b[0m')).toBe(
      '<span style="font-weight:700;color:var(--bs-danger)">bold red</span>',
    )
  })

  it('closes a pending span at end of input without a reset code', () => {
    expect(ansiToHtml('\x1b[32mgreen')).toBe('<span style="color:var(--bs-success)">green</span>')
  })

  it('drops unsupported codes', () => {
    expect(ansiToHtml('\x1b[99mX\x1b[0m')).toBe('X')
  })
})
