import client from './client'
import type { LikeUsageListResponse, PostListResponse, PostStatus } from '../type/postType'



export function getPostList(statusList: PostStatus[]) {
  return client.get<PostListResponse>('/post', { params: { status: statusList } })
}


export function getLikeUsageList() {
  return client.get<LikeUsageListResponse>('/post/like-usage')
}
