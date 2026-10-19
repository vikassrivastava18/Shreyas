import './assets/base.css'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
// import axios from 'axios'
import { createWebHistory, createRouter } from 'vue-router'
import { createApp } from 'vue'

import HomeView from './views/HomeView.vue'
import App from './App.vue'


const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/python',
    name: 'python',
    component: () => import('./views/python/PythonView.vue'),
    children: [
      {
        path: 'topic-summary/:id',
        name: 'topic-summary',
        component: () => import('./views/python/components/SummaryComponent.vue')
      },
      {
        path: 'topics',
        name: 'topics',
        component: () => import('./views/python/components/TopicsComponent.vue')
      },
      {
        path: 'subtopic/:id/code',
        name: 'subtopic-code',
        component: () => import('./views/python/components/CodeComponent.vue')
      },
      {
        path: 'subtopic/:id/summary',
        name: 'subtopic-summary',
        component: () => import('./views/python/components/SubtopicSummary.vue')
      },
      {
        path: 'subtopic/:id/quiz',
        name: 'subtopic-quiz',
        component: () => import('./views/python/components/QuizComponent.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

let app = createApp(App)
            .use(router)

// app.config.globalProperties.$axios = axios
app.mount('#app')