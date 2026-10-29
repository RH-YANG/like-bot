import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, toApiError } from '../util/apiError'



interface UseApiDataOption {
  pollingMs?: number       // 주면 이 주기로 다시 불러온다
  reloadKey?: unknown      // 값이 바뀌면 다시 불러온다(필터 등)
}


// 조회 API 공통 훅. 반환: { data, isLoading, error, reload, clearError }
export function useApiData<T>(fetcher: () => Promise<T>, option: UseApiDataOption = {}) {
  const { pollingMs, reloadKey } = option
  const [data, setData] = useState<T | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<ApiError | null>(null)
  const fetcherRef = useRef(fetcher)
  const requestIdRef = useRef(0)
  fetcherRef.current = fetcher

  // 필터를 빠르게 바꾸면 늦게 도착한 이전 응답이 최신 결과를 덮어쓰지 않도록 마지막 요청만 반영한다
  const reload = useCallback(async () => {
    const requestId = ++requestIdRef.current
    try {
      const nextData = await fetcherRef.current()
      if (requestId !== requestIdRef.current) return
      setData(nextData)
      setError(null)
    } catch (caughtError) {
      if (requestId !== requestIdRef.current) return
      setError(toApiError(caughtError))
    } finally {
      if (requestId === requestIdRef.current) setIsLoading(false)
    }
  }, [])

  const clearError = useCallback(() => setError(null), [])

  useEffect(() => {
    reload()
    if (!pollingMs) return
    const timer = window.setInterval(reload, pollingMs)
    return () => window.clearInterval(timer)
  }, [reload, pollingMs, reloadKey])

  return { data, isLoading, error, reload, clearError }
}
