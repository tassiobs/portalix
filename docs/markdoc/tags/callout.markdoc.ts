import { Tag } from '@markdoc/markdoc'

export const callout = {
  render: 'Callout',
  description: 'Display a callout box',
  children: ['paragraph', 'tag', 'list'],
  attributes: {
    type: {
      type: String,
      default: 'note',
      matches: ['note', 'warning', 'error', 'tip'],
    },
    title: { type: String },
  },
}
