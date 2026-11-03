import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import Counter from './Counter.vue'

describe('Counter', () => {
  it('renders the initial count', () => {
    const wrapper = mount(Counter)

    expect(wrapper.get('.count').text()).toBe('Count: 0')
  })

  it('increments the count when the button is clicked', async () => {
    const wrapper = mount(Counter)

    await wrapper.get('button').trigger('click')

    expect(wrapper.get('.count').text()).toBe('Count: 1')
  })
})
