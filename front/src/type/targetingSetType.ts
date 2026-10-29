export type Platform = 'threads' | 'instagram' | 'x'
export type Language = 'ko' | 'ja' | 'en'


export interface SaveTargetingSetRequest {
  name: string
  platform: Platform
  goalCount: number
  maxScanCount: number
  maxRunMinute: number
  maxPostAgeHour: number | null
  maxLikeCount: number | null
  language: Language
  isVerifiedExcluded: boolean
  authorCooldownDay: number
  searchKeywordList: string[]
  excludeKeywordList: string[]
}


export interface TargetingSet extends SaveTargetingSetRequest {
  id: number
  createdAt: string
  updatedAt: string
}


export interface TargetingSetListResponse {
  targetingSetList: TargetingSet[]
}


export interface SaveTargetingSetResponse {
  targetingSetId: number
}
