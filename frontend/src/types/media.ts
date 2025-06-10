// 媒体类型（与后端枚举保持一致）
export type MediaType = 'photo' | 'video'

// 媒体项接口
export interface MediaItem {
  id: string
  name: string
  type: MediaType
  url: string
  thumbnail_url?: string // 可能不存在缩略图
  size: number
  upload_date: string // 与后端字段名一致
  width?: number
  height?: number
  duration?: number
  path?: string // 文件路径
  description?: string // 媒体内容说明
  score?: number // 搜索相似度分数
  global_media_id?: string // 32位全局唯一ID
}

// 媒体列表响应接口
export interface MediaListResponse {
  items: MediaItem[]
  total: number
  page: number
  page_size: number // 与后端字段一致
  has_more: boolean
}

// 媒体上传状态
export interface UploadStatus {
  id: string
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}

// 上传结果响应
export interface UploadResult {
  success: boolean
  file_name: string
  file_type: MediaType
  file_size: number
  file_path: string
  message: string
} 