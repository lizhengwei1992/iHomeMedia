import { MediaItem } from '@/types/media'
import MediaGrid from '@/components/media/MediaGrid'
import { InformationCircleIcon } from '@heroicons/react/outline'

interface SearchResult {
  media_id: string;  // 这是32位全局ID
  score: number;
  metadata: {
    global_media_id: string;  // 32位全局ID
  file_path: string;
  file_name: string;
  file_type: string;
  file_size: number;
  upload_time: string;
  description?: string;
    original_url?: string;    // 原始文件URL
    thumbnail_url?: string;   // 缩略图URL
    relative_path?: string;
    file_id?: string;         // 兼容旧的文件ID
    original_name?: string;   // 原始文件名
    width?: number;
    height?: number;
  };
}

interface SearchResultsProps {
  results: SearchResult[];
  isLoading: boolean;
  query: string;
  searchTime?: number;
  totalResults: number;
  onItemClick?: (item: MediaItem) => void;
}

const SearchResults = ({ 
  results, 
  isLoading, 
  query, 
  searchTime, 
  totalResults 
}: SearchResultsProps) => {
  

  
  // 转换搜索结果为MediaItem格式
  const convertToMediaItems = (searchResults: SearchResult[]): MediaItem[] => {
    return searchResults.map(result => {
      // 使用metadata中的数据（新的数据结构）
      const metadata = result.metadata;
      
      // 从metadata中提取数据
      const fileName = metadata.file_name || '未知文件';
      const fileType = metadata.file_type || 'photo';
      const filePath = metadata.relative_path || metadata.file_path || '';
      const fileSize = metadata.file_size || 0;
      const uploadTime = metadata.upload_time || '';
      const description = metadata.description || '';
      
      // 优先使用metadata中的URL，如果没有则构建
      const originalUrl = metadata.original_url || `/media/${filePath}`;
      const thumbnailUrl = metadata.thumbnail_url || 
                          (metadata.thumbnail_url ? metadata.thumbnail_url : `/media/${filePath}`);
      
      // 使用文件名作为ID，确保与媒体查看页面的兼容性
      const mediaId = metadata.file_id || fileName;
      
      return {
        id: mediaId,  // 使用文件名作为ID，保持与媒体查看页面的兼容性
        name: fileName,
        type: fileType.toLowerCase() as 'photo' | 'video',
        path: filePath,
        size: fileSize,
        url: originalUrl,
        thumbnail_url: thumbnailUrl,
        upload_date: uploadTime,
        description: description,
      // 添加搜索特有属性
        score: result.score || 0,
        // 添加额外信息
        width: metadata.width,
        height: metadata.height,
        global_media_id: metadata.global_media_id || result.media_id,
      }
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <span className="ml-3 text-gray-600">搜索中...</span>
      </div>
    )
  }

  if (!results || results.length === 0) {
    return (
      <div className="text-center py-12">
        <InformationCircleIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">没有找到相关内容</h3>
        <p className="mt-1 text-sm text-gray-500">
          尝试使用不同的关键词，或检查拼写是否正确
        </p>
      </div>
    )
  }

  const mediaItems = convertToMediaItems(results)

  return (
    <div className="space-y-4">
      {/* 搜索结果统计 */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <div className="flex items-center">
          <InformationCircleIcon className="h-5 w-5 text-blue-400" />
          <div className="ml-3">
            <p className="text-sm text-blue-800">
              找到 <span className="font-medium">{totalResults}</span> 个与 
              "<span className="font-medium">{query}</span>" 相关的结果
              {searchTime && (
                <span className="text-blue-600">
                  （耗时 {(searchTime * 1000).toFixed(0)}ms）
                </span>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* 搜索结果网格 */}
      <div className="space-y-6">
        <MediaGrid 
          mediaItems={mediaItems} 
          isLoading={false}
          viewMode="grid"
        />
      </div>
    </div>
  )
}

export default SearchResults 