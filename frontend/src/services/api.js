import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000/api',
});

// ---- Products ----
export const fetchProducts = (category) =>
  API.get('/products/', { params: category ? { category } : {} }).then(r => r.data);

export const fetchProduct = (id) =>
  API.get(`/products/${id}`).then(r => r.data);

export const createProduct = (data) =>
  API.post('/products/', data).then(r => r.data);

export const updateProduct = (id, data) =>
  API.put(`/products/${id}`, data).then(r => r.data);

export const deleteProduct = (id) =>
  API.delete(`/products/${id}`);

// ---- Inventory ----
export const fetchInventory = () =>
  API.get('/inventory/').then(r => r.data);

export const fetchAlerts = () =>
  API.get('/inventory/alerts').then(r => r.data);

export const updateInventory = (productId, data) =>
  API.put(`/inventory/${productId}`, data).then(r => r.data);

// ---- Orders ----
export const fetchOrders = (params) =>
  API.get('/orders/', { params }).then(r => r.data);

export const fetchOrderStats = () =>
  API.get('/orders/stats').then(r => r.data);

export const createOrder = (data) =>
  API.post('/orders/', data).then(r => r.data);

export const updateOrderStatus = (orderId, status) =>
  API.put(`/orders/${orderId}/status`, { status }).then(r => r.data);

// ---- Scenario Simulation ----
export const runSimulation = (params) =>
  API.post('/simulate-scenario', params).then(r => r.data);

