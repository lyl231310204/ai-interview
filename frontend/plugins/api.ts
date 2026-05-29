import axios from 'axios'

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig()

  const api = axios.create({
    baseURL: config.public.apiBase,
    timeout: 60000,
  })

  // 响应拦截器：统一包装为 { code, message, data }
  api.interceptors.response.use(
    (response) => {
      // 列表接口返回数组时包装成 { items: [...] }，单对象直接透传
      let wrapped = response.data
      if (Array.isArray(response.data)) {
        wrapped = { items: response.data, total: response.data.length }
      }
      response.data = {
        code: 0,
        message: 'success',
        data: wrapped,
      }
      return response
    },
    (error) => {
      const detail = error.response?.data?.detail || error.message || '请求失败'
      return Promise.reject(error)
    },
  )

  return {
    provide: {
      api,
    },
  }
})
