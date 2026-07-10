import { toast } from 'sonner'

const MANUAL_EDIT_TITLE = 'Form is AI-controlled'
const MANUAL_EDIT_DESCRIPTION =
  'Please use the AI Assistant chat on the right to update this field. For example: "Change sentiment to positive" or "Shared CardioMax brochure".'

/** Show a polite error when the user tries to edit the left form manually. */
export function notifyManualFormEditBlocked(fieldLabel?: string) {
  toast.error(MANUAL_EDIT_TITLE, {
    description: fieldLabel
      ? `“${fieldLabel}” can’t be edited directly. ${MANUAL_EDIT_DESCRIPTION}`
      : MANUAL_EDIT_DESCRIPTION,
    duration: 5000,
  })
}
