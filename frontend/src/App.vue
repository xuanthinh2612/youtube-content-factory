<script setup>
import { onMounted, ref } from 'vue'

const theme=ref('dark')

function applyTheme(value){
  theme.value=value
  document.documentElement.dataset.theme=value
  localStorage.setItem('content-factory-theme',value)
}

function toggleTheme(){
  applyTheme(theme.value==='dark'?'light':'dark')
}

onMounted(()=>{
  const saved=localStorage.getItem('content-factory-theme')
  const systemDark=window.matchMedia?.('(prefers-color-scheme: dark)').matches
  applyTheme(saved || (systemDark?'dark':'light'))
})
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="topbar-inner">
        <RouterLink to="/" class="brand">
          <span class="brand-mark">CF</span>
          <span>Content Factory</span>
        </RouterLink>

        <nav class="topnav" aria-label="Main navigation">
          <RouterLink to="/">Create</RouterLink>
          <RouterLink to="/projects">Projects</RouterLink>
        </nav>

        <button class="icon-button theme-toggle" type="button" @click="toggleTheme"
                :aria-label="theme==='dark'?'Switch to light mode':'Switch to dark mode'">
          <svg v-if="theme==='dark'" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="4"/>
            <path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.66 6.34l1.41-1.41"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" aria-hidden="true">
            <path d="M20.5 14.1A8.5 8.5 0 0 1 9.9 3.5 8.5 8.5 0 1 0 20.5 14.1Z"/>
          </svg>
        </button>
      </div>
    </header>

    <main class="main">
      <RouterView/>
    </main>
  </div>
</template>
