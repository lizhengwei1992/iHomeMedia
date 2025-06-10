import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000, // 上传大文件可能需要较长时间
})

// 请求拦截器：添加token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 401错误处理
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 媒体相关API
export const mediaApi = {
  // 获取媒体列表
  getList: (params: { page: number; page_size: number; media_type?: string }) => 
    api.get('/media/list', { params }),
  
  // 上传媒体文件
  upload: (formData: FormData, onProgress?: (percentage: number) => void) => 
    api.post('/media/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentage = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percentage)
        }
      },
    }),
    
  // 获取媒体详情
  getDetail: (id: string) => api.get(`/media/${id}`),
  
  // 删除媒体
  delete: (id: string) => api.delete(`/media/${id}`),
  
  // 更新媒体描述
  updateDescription: (id: string, description: string) => {
    const formData = new FormData()
    formData.append('description', description)
    return api.put(`/media/${id}/description`, formData)
  },
}

// 搜索相关API
export const searchApi = {
  // 文本搜索
  searchByText: (params: {
    query: string;
  }) => api.post('/search/text', params),
  
  // 以图搜图
  searchByImage: (file: File) => {
    const formData = new FormData()
    formData.append('image', file)
    
    return api.post('/search/by-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    })
  },
  
  // 基于文件路径的相似搜索（用于查看器中的"找相似"功能）
  searchSimilarByFilePath: (filePath: string) => {
    const formData = new FormData()
    formData.append('file_path', filePath)
    
    return api.post('/search/similar-by-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    })
  },
  
  // 相似内容查找
  findSimilar: (params: {
    media_id: string;
    limit?: number;
    similarity_type?: string;
  }) => api.post('/search/similar', params),
  
  // 获取搜索统计信息
  getStats: () => api.get('/search/stats'),
  
  // 获取速率限制状态
  getRateLimitStatus: () => api.get('/search/rate-limit-status'),
  
  // 数据迁移
  migrateDescriptions: (force: boolean = false) => 
    api.post('/search/migrate-descriptions', {}, { params: { force } }),
}

// 认证相关API
export const authApi = {
  // 登录 - 使用表单格式发送请求，符合FastAPI OAuth2PasswordRequestForm要求
  login: (username: string, password: string) => {
    // 创建表单数据
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    return api.post('/auth/token', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
    
  // 验证token
  verify: () => api.get('/auth/verify'),
}

export default api 