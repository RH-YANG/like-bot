import type { Platform } from './targetingSetType'


export interface Author {
  id: number
  platform: Platform
  handle: string
  url: string
  displayName: string | null
  isVerified: boolean
  isBlocked: boolean
  memo: string | null
  likedPostCount: number
  lastLikedAt: string | null
  createdAt: string
}


export interface AuthorListResponse {
  authorList: Author[]
}


// memo를 보내지 않으면 기존 메모를 유지한다
export interface UpdateAuthorRequest {
  isBlocked: boolean
  memo?: string | null
}
