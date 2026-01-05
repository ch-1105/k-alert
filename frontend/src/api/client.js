import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000, // 10 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;
