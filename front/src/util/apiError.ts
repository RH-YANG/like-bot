import axios from 'axios'



const DEFAULT_ERROR_MESSAGE = '요청을 처리하지 못했어요. 잠시 후 다시 시도해 주세요.'


// 사용자에게 보여줄 message와 응답 status를 담는다
export class ApiError extends Error {
  status: number | null

  constructor(message: string, status: number | null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}


// 백엔드는 HTTPException의 detail에 사용자용 문구를 담아 보낸다
export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    const message = typeof detail === 'string' ? detail : DEFAULT_ERROR_MESSAGE
    return new ApiError(message, error.response?.status ?? null)
  }
  return new ApiError(DEFAULT_ERROR_MESSAGE, null)
}
