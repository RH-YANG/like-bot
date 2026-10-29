import type { Platform } from './targetingSetType'


export type PostStatus = 'candidate' | 'approved' | 'rejected' | 'liked' | 'failed'


export interface Post {
  id: number
  runId: number
  platform: Platform
  postCode: string
  url: string
  content: string | null
  postedAt: string | null
  likeCount: number | null
  searchKeyword: string
  status: PostStatus
  likedAt: string | null
  createdAt: string
  authorId: number
  authorHandle: string
  authorDisplayName: string | null
  isAuthorBlocked: boolean
}


export interface PostListResponse {
  postList: Post[]
}


// 플랫폼별 좋아요 상한과 최근 좋아요 수
export interface LikeUsage {
  platform: Platform
  dailyLikeLimit: number
  hourlyLikeLimit: number
  dailyLikedCount: number
  hourlyLikedCount: number
  minIntervalSec: number
  maxIntervalSec: number
}


export interface LikeUsageListResponse {
  likeUsageList: LikeUsage[]
}
