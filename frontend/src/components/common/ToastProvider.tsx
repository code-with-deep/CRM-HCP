import { useEffect, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Toaster, toast } from 'sonner'

import type { AppDispatch, RootState } from '@/store'
import { removeToast } from '@/store/slices/uiSlice'

export function ToastProvider() {
  const dispatch = useDispatch<AppDispatch>()
  const toasts = useSelector((state: RootState) => state.ui.toasts)
  const processedIds = useRef(new Set<string>())

  useEffect(() => {
    for (const item of toasts) {
      if (processedIds.current.has(item.id)) continue
      processedIds.current.add(item.id)

      if (item.type === 'success') {
        toast.success(item.message)
      } else if (item.type === 'error') {
        toast.error(item.message)
      } else {
        toast.message(item.message)
      }

      dispatch(removeToast(item.id))
    }
  }, [toasts, dispatch])

  return (
    <Toaster
      position="top-right"
      richColors
      closeButton
      toastOptions={{ duration: 4500 }}
    />
  )
}
