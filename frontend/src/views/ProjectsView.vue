<script setup>
import { onMounted,onUnmounted,ref,computed } from 'vue'
import StatusBadge from '../components/StatusBadge.vue'
import { api } from '../lib/api'

const projects=ref([])
const queue=ref({})
const error=ref('')
const deletingIds=ref(new Set())
const bulkDeleting=ref(false)
const selectedIds=ref(new Set())
const stoppingIds=ref(new Set())
let timer

const allSelected=computed(()=>projects.value.length>0 && selectedIds.value.size===projects.value.length)
const someSelected=computed(()=>selectedIds.value.size>0)

async function load(){
  try{
    const result=await api.projects()
    projects.value=result.items
    queue.value=result.queue
    error.value=''
    const liveIds=new Set(result.items.map(p=>p.id))
    selectedIds.value=new Set([...selectedIds.value].filter(id=>liveIds.has(id)))
  }catch(e){
    error.value=e.message
  }
}

function isSelected(id){
  return selectedIds.value.has(id)
}

function toggleSelect(id){
  const next=new Set(selectedIds.value)
  if(next.has(id))next.delete(id)
  else next.add(id)
  selectedIds.value=next
}

function toggleSelectAll(){
  selectedIds.value=allSelected.value ? new Set() : new Set(projects.value.map(p=>p.id))
}

async function askDelete(project){
  if(!window.confirm(`Delete "${project.name}"? Its generated files, events and database record will be permanently deleted.`))return
  const next=new Set(deletingIds.value);next.add(project.id);deletingIds.value=next
  error.value=''
  try{
    await api.deleteProject(project.id,'Delete')
    await load()
  }catch(e){
    error.value=e.message
  }finally{
    const after=new Set(deletingIds.value);after.delete(project.id);deletingIds.value=after
  }
}

async function deleteSelected(){
  const ids=[...selectedIds.value]
  if(!ids.length)return
  if(!window.confirm(`Delete ${ids.length} selected project${ids.length===1?'':'s'}? Their generated files, events and database records will be permanently deleted.`))return
  bulkDeleting.value=true
  error.value=''
  try{
    await api.deleteProjectsBulk(ids,'Delete')
    selectedIds.value=new Set()
    await load()
  }catch(e){
    error.value=e.message
  }finally{
    bulkDeleting.value=false
  }
}

async function forceStop(project){
  if(!window.confirm(`Force stop "${project.name}" now?`))return
  stoppingIds.value=new Set([...stoppingIds.value,project.id])
  error.value=''
  try{
    await api.cancelProject(project.id)
    await load()
  }catch(e){
    error.value=e.message
  }finally{
    const next=new Set(stoppingIds.value);next.delete(project.id);stoppingIds.value=next
  }
}

onMounted(()=>{
  load()
  timer=setInterval(load,5000)
})
onUnmounted(()=>clearInterval(timer))
</script>


<template>
  <section class="page">
    <header class="page-head row-between">
      <div>
        <h1>Projects</h1>
        <p>All generated and active projects.</p>
      </div>
      <div class="queue-summary">
        <span><b>{{queue.running_count||0}}</b> running</span>
        <span><b>{{queue.queued_count||0}}</b> queued</span>
        <span>{{queue.max_concurrent||10}} max</span>
      </div>
    </header>

    <p v-if="error" class="inline-error">{{error}}</p>

    <div v-if="projects.length" class="bulk-actions-bar">
      <label class="check-line">
        <input type="checkbox" :checked="allSelected" @change="toggleSelectAll">
        <span>{{someSelected?`${selectedIds.size} selected`:'Select all'}}</span>
      </label>
      <button type="button" class="danger-button" :disabled="!someSelected || bulkDeleting"
              @click="deleteSelected">
        {{bulkDeleting?'Deleting…':'Delete selected'}}
      </button>
    </div>

    <div class="project-list">
      <div class="project-row header">
        <span></span><span>Project</span><span>Type</span><span>Status</span><span>Progress</span><span></span>
      </div>

      <div v-for="p in projects" :key="p.id" class="project-row">
        <span class="select-cell">
          <input type="checkbox" :checked="isSelected(p.id)" @change="toggleSelect(p.id)" :aria-label="`Select ${p.name}`">
        </span>
        <RouterLink :to="`/projects/${p.id}`" class="project-title-cell project-link-cell">
          <b>{{p.name}}</b>
          <small>{{p.request.duration_minutes}} min · {{p.request.languages.join(', ').toUpperCase()}} · {{new Date(p.created_at).toLocaleString()}}</small>
        </RouterLink>
        <span class="muted capitalize">{{p.request.niche}}</span>
        <span><StatusBadge :status="p.status"/></span>
        <span class="progress-cell">
          <span>{{p.progress}}%</span>
          <div class="mini-progress"><i :style="{width:p.progress+'%'}"></i></div>
          <small>{{p.stage}}</small>
        </span>
        <span class="project-actions">
          <RouterLink :to="`/projects/${p.id}`" class="row-action">Open</RouterLink>
          <RouterLink :to="{path:'/',query:{clone:p.id}}" class="row-action">Clone</RouterLink>
          <button v-if="p.status==='queued' || p.status==='running'" type="button"
                  class="row-action danger-link" :disabled="stoppingIds.has(p.id)" @click="forceStop(p)">
            {{stoppingIds.has(p.id)?'Stopping…':'Force stop'}}
          </button>
          <button type="button" class="row-action danger-link" :disabled="deletingIds.has(p.id)" @click="askDelete(p)">
            {{deletingIds.has(p.id)?'Deleting…':'Delete'}}
          </button>
        </span>
      </div>

      <div v-if="!projects.length && !error" class="empty-state">
        <p>No projects yet.</p>
        <RouterLink to="/">Create your first project</RouterLink>
      </div>
    </div>
  </section>
</template>
