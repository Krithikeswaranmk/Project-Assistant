import axios from 'axios'

const BASE = import.meta.env.VITE_BACKEND_URL

export const api = axios.create({ baseURL: BASE })

export const onboardUser = (data) => api.post('/api/onboard', data)
export const getOnboardStatus = (userId) => api.get(`/api/onboard/status/${userId}`)
export const getProfile = (userId) => api.get(`/api/profile/${userId}`)
export const planSession = (data) => api.post('/api/session/plan', data)
export const updateTask = (sessionId, taskIndex, data) => api.patch(`/api/session/${sessionId}/task/${taskIndex}`, data)
export const submitScoreFeedback = (userId, data) => api.put(`/api/profile/${userId}/score-feedback`, data)
export const completeSession = (sessionId) => api.patch(`/api/session/${sessionId}/complete`)
