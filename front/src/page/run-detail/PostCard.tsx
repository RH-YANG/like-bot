import type { Post } from '../../type/postType'
import { formatDateTime } from '../../util/format'
import s from './PostCard.module.css'



interface PostCardProps {
  post: Post
  isSelected: boolean
  onToggle: () => void
}


// 승인 대기 후보 1개. 카드를 누르면 선택이 바뀐다
function PostCard({ post, isSelected, onToggle }: PostCardProps) {
  return (
    <label className={`${s.card} ${isSelected ? s.selected : ''}`}>
      <div className={s.header}>
        <input type="checkbox" checked={isSelected} onChange={onToggle} />
        <strong>@{post.authorHandle}</strong>
        <span className="muted">
          {formatDateTime(post.postedAt)} · 좋아요 {post.likeCount ?? '?'} · {post.searchKeyword}
        </span>
        <a href={post.url} target="_blank" rel="noreferrer" className={s.link}>
          원본
        </a>
      </div>
      <div className="pre">{post.content}</div>
    </label>
  )
}


export default PostCard
