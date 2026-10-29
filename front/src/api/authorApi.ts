import client from './client'
import type { AuthorListResponse, UpdateAuthorRequest } from '../type/authorType'



export function getAuthorList(isBlockedOnly: boolean) {
  return client.get<AuthorListResponse>('/author', { params: { is_blocked_only: isBlockedOnly } })
}


export function updateAuthor(authorId: number, request: UpdateAuthorRequest) {
  return client.patch(`/author/${authorId}`, request)
}
