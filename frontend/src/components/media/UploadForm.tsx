import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { mediaApi } from '@/services/api'
import { UploadStatus } from '@/types/media'

interface UploadFormProps {
  onUploadComplete: () => void
}

const UploadForm = ({ onUploadComplete }: UploadFormProps) => {
  const [uploads, setUploads] = useState<UploadStatus[]>([])
  const [isUploading, setIsUploading] = useState(false)
  
  // 处理文件拖放
  const onDrop = useCallback((acceptedFiles: File[]) => {
    // 创建新的上传状态列表
    const newUploads = acceptedFiles.map((file) => ({
      id: `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      file,
      progress: 0,
      status: 'pending' as const,
    }))
    
    setUploads((prev) => [...prev, ...newUploads])
  }, [])
  
  // 使用react-dropzone
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: '.jpg, .jpeg, .png, .heic, .webp, .mp4, .mov, .hevc, .avi'
  })
  
  // 处理上传
  const handleUpload = async () => {
    if (uploads.length === 0 || isUploading) return
    
    setIsUploading(true)
    
    // 过滤出待上传的文件
    const pendingUploads = uploads.filter((u) => u.status === 'pending')
    
    try {
      // 创建FormData，包含所有文件
      const formData = new FormData()
      pendingUploads.forEach(upload => {
        // 使用files[]参数名，与后端匹配
        formData.append('files', upload.file)
        
        // 更新状态为上传中
        setUploads((prev) =>
          prev.map((u) =>
            u.id === upload.id ? { ...u, status: 'uploading', progress: 0 } : u
          )
        )
      })
      
      // 一次性上传所有文件
      const response = await mediaApi.upload(formData, (progress) => {
        // 对所有正在上传的文件更新相同进度
        setUploads((prev) =>
          prev.map((u) =>
            u.status === 'uploading' ? { ...u, progress } : u
          )
        )
      })
      
      // 处理上传结果
      const results = response.data
      
      // 更新每个文件的状态
      for (let i = 0; i < pendingUploads.length; i++) {
        const uploadId = pendingUploads[i].id
        const result = results[i] || { success: false, message: '上传失败' }
        
        setUploads((prev) =>
          prev.map((u) =>
            u.id === uploadId
              ? {
                  ...u,
                  progress: 100,
                  status: result.success ? 'success' : 'error',
                  error: result.success ? undefined : result.message,
                }
              : u
          )
        )
      }
      
      // 通知上传完成
      onUploadComplete()
    } catch (error) {
      // 更新所有正在上传的文件为错误状态
      setUploads((prev) =>
        prev.map((u) =>
          u.status === 'uploading'
            ? {
                ...u,
                status: 'error',
                error: '上传失败，请重试',
              }
            : u
        )
      )
    } finally {
      setIsUploading(false)
    }
  }
  
  // 清除已完成的上传
  const handleClearCompleted = () => {
    setUploads((prev) => prev.filter((u) => u.status !== 'success'))
  }
  
  // 重试失败的上传
  const handleRetry = (id: string) => {
    setUploads((prev) =>
      prev.map((u) => (u.id === id ? { ...u, status: 'pending', progress: 0 } : u))
    )
  }
  
  // 移除上传项
  const handleRemove = (id: string) => {
    setUploads((prev) => prev.filter((u) => u.id !== id))
  }
  
  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <h2 className="text-lg font-medium mb-4">上传媒体文件</h2>
      
      {/* 拖放区域 */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer transition duration-150 ${
          isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400'
        }`}
      >
        <input {...getInputProps()} />
        <svg
          className={`w-12 h-12 mb-4 ${isDragActive ? 'text-primary-500' : 'text-gray-400'}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        
        <p className="text-sm text-center">
          {isDragActive
            ? '放开以添加文件'
            : '拖放文件到此处，或点击选择文件'}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          支持 JPG, PNG, HEIC, WEBP, MP4, MOV, HEVC, AVI (最大500MB)
        </p>
      </div>
      
      {/* 上传列表 */}
      {uploads.length > 0 && (
        <div className="mt-4">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-medium">上传列表</h3>
            <div className="flex space-x-2">
              <button
                onClick={handleUpload}
                disabled={isUploading || !uploads.some(u => u.status === 'pending')}
                className="text-sm bg-primary-600 text-white py-1 px-3 rounded disabled:opacity-50"
              >
                {isUploading ? '上传中...' : '开始上传'}
              </button>
              <button
                onClick={handleClearCompleted}
                disabled={!uploads.some(u => u.status === 'success')}
                className="text-sm bg-gray-200 text-gray-700 py-1 px-3 rounded disabled:opacity-50"
              >
                清除已完成
              </button>
            </div>
          </div>
          
          <div className="max-h-60 overflow-y-auto">
            {uploads.map((upload) => (
              <div
                key={upload.id}
                className="flex items-center justify-between py-2 border-b last:border-b-0"
              >
                <div className="flex items-center flex-1 mr-4 min-w-0">
                  <div className="flex-shrink-0">
                    {upload.status === 'success' && (
                      <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    )}
                    {upload.status === 'error' && (
                      <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    )}
                    {(upload.status === 'pending' || upload.status === 'uploading') && (
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    )}
                  </div>
                  <div className="ml-3 min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {upload.file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {(upload.file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                
                {/* 进度条 */}
                {upload.status === 'uploading' && (
                  <div className="w-24 bg-gray-200 rounded-full h-2.5 mr-4">
                    <div
                      className="bg-primary-600 h-2.5 rounded-full"
                      style={{ width: `${upload.progress}%` }}
                    ></div>
                  </div>
                )}
                
                {/* 操作按钮 */}
                <div className="flex-shrink-0 flex space-x-1">
                  {upload.status === 'error' && (
                    <button
                      onClick={() => handleRetry(upload.id)}
                      className="text-xs text-primary-600 hover:text-primary-900 p-1"
                    >
                      重试
                    </button>
                  )}
                  <button
                    onClick={() => handleRemove(upload.id)}
                    className="text-xs text-gray-500 hover:text-gray-700 p-1"
                    disabled={upload.status === 'uploading'}
                  >
                    移除
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default UploadForm 