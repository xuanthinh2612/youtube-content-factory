import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import HomeView from './views/HomeView.vue'
import ProjectsView from './views/ProjectsView.vue'
import ProjectView from './views/ProjectView.vue'
import OutputsView from './views/OutputsView.vue'
import './styles.css'

const router=createRouter({
  history:createWebHistory(),
  scrollBehavior:()=>({top:0}),
  routes:[
    {path:'/',component:HomeView},
    {path:'/projects',component:ProjectsView},
    {path:'/projects/:id',component:ProjectView},
    {path:'/projects/:id/outputs',component:OutputsView},
  ],
})

createApp(App).use(router).mount('#app')
