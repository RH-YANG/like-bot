import { useCallback, useRef, useState } from 'react'
import { ApiError, toApiError } from '../util/apiError'



// 변경 API 공통 훅. 제출 중 중복 호출을 막고 성공 여부를 돌려준다
// 반환: { isSubmitting, error, submit, clearError }
export function useSubmit() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const isSubmittingRef = useRef(false)

  const submit = useCallback(async (action: () => Promise<unknown>): Promise<boolean> => {
    if (isSubmittingRef.current) return false
    isSubmittingRef.current = true
    setIsSubmitting(true)
    setError(null)
    try {
      await action()
      return true
    } catch (caughtError) {
      setError(toApiError(caughtError))
      return false
    } finally {
      isSubmittingRef.current = false
      setIsSubmitting(false)
    }
  }, [])

  const clearError = useCallback(() => setError(null), [])

  return { isSubmitting, error, submit, clearError }
}
