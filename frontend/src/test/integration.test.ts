import { describe, expect, it } from 'vitest'

import { detectChangedFields } from '@/store/slices/interactionSlice'
import { EMPTY_INTERACTION_DRAFT } from '@/types/interaction.types'
import { canSaveInteraction, mergeInteractionDraft } from '@/utils/chat'

describe('mergeInteractionDraft', () => {
  it('merges only provided fields and preserves unchanged values', () => {
    const current = {
      ...EMPTY_INTERACTION_DRAFT,
      hcp_name: 'Dr Sharma',
      interaction_type: 'Meeting',
      topics_discussed: ['CardioMax'],
    }

    const merged = mergeInteractionDraft(current, {
      hcp_name: 'Dr John',
    })

    expect(merged.hcp_name).toBe('Dr John')
    expect(merged.interaction_type).toBe('Meeting')
    expect(merged.topics_discussed).toEqual(['CardioMax'])
  })
})

describe('detectChangedFields', () => {
  it('detects only modified fields during edit flow', () => {
    const previous = {
      ...EMPTY_INTERACTION_DRAFT,
      hcp_name: 'Dr Sharma',
      interaction_type: 'Meeting',
      topics_discussed: ['CardioMax'],
      sentiment: 'positive' as const,
    }

    const next = {
      ...previous,
      hcp_name: 'Dr John',
    }

    expect(detectChangedFields(previous, next)).toEqual(['hcp_name'])
  })

  it('detects array field updates for materials and samples', () => {
    const previous = {
      ...EMPTY_INTERACTION_DRAFT,
      materials_shared: ['Brochure'],
      samples_distributed: [],
      follow_up_actions: 'Call next week',
    }

    const next = {
      ...previous,
      materials_shared: ['Brochure', 'Clinical study'],
      samples_distributed: ['CardioMax sample pack'],
      follow_up_actions: 'Follow up on Friday',
    }

    expect(detectChangedFields(previous, next)).toEqual([
      'materials_shared',
      'samples_distributed',
      'follow_up_actions',
    ])
  })
})

describe('canSaveInteraction', () => {
  it('requires hcp name and interaction date before saving', () => {
    expect(canSaveInteraction(EMPTY_INTERACTION_DRAFT)).toBe(false)
    expect(
      canSaveInteraction({
        ...EMPTY_INTERACTION_DRAFT,
        hcp_name: 'Dr Sharma',
        interaction_date: '2026-07-09',
      }),
    ).toBe(true)
  })
})
