<script setup>
import { computed,onMounted,onUnmounted,ref } from 'vue'
import { useRoute,useRouter } from 'vue-router'
import WorkflowGraph from '../components/WorkflowGraph.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { api } from '../lib/api'

const route=useRoute()
const router=useRouter()
const id=route.params.id

const project=ref(null)
const graph=ref({nodes:[],edges:[]})
const events=ref([])
const usage=ref({nodes:{},total_calls:0,total_tokens:0})
const error=ref('')
const connection=ref('connecting')
const deleting=ref(false)
const stopping=ref(false)

let es=null
let timer=null
let refreshTimer=null

const terminal=computed(()=>['completed','failed','cancelled'].includes(project.value?.status))
const lastEventId=computed(()=>events.value.length?Math.max(...events.value.map(e=>Number(e.id)||0)):0)
const currentNode=computed(()=>{
  const stage=project.value?.stage
  return graph.value.nodes?.find(n=>n.id===stage) || null
})
const topUsageNodes=computed(()=>Object.entries(usage.value?.nodes||{}).slice(0,6))

async function refreshSummary(){
  try{
    const [p,g,u]=await Promise.all([api.project(id),api.graph(id),api.usage(id)])
    project.value=p
    graph.value=g
    usage.value=u
    error.value=''
    if(['completed','failed','cancelled'].includes(p.status) && es){
      es.close()
      es=null
      connection.value='closed'
    }
  }catch(e){
    error.value=e.message
  }
}

function scheduleRefresh(){
  clearTimeout(refreshTimer)
  refreshTimer=setTimeout(refreshSummary,200)
}

function appendEvent(event){
  if(events.value.some(x=>x.id===event.id))return
  events.value.push(event)
  if(events.value.length>600)events.value=events.value.slice(-600)
}

function openStream(){
  if(es || terminal.value)return
  connection.value='connecting'
  es=new EventSource(`/api/projects/${id}/events/stream?after=${lastEventId.value}`)
  es.onopen=()=>{connection.value='live'}
  es.onmessage=(ev)=>{
    try{
      appendEvent(JSON.parse(ev.data))
      scheduleRefresh()
    }catch{}
  }
  es.onerror=()=>{
    if(terminal.value){
      es?.close()
      es=null
      connection.value='closed'
    }else{
      connection.value='reconnecting'
    }
  }
}

async function initialLoad(){
  try{
    const [p,g,e,u]=await Promise.all([api.project(id),api.graph(id),api.events(id),api.usage(id)])
    project.value=p
    graph.value=g
    events.value=e.items
    usage.value=u
    error.value=''
    if(!terminal.value)openStream()
    else connection.value='closed'
  }catch(e){
    error.value=e.message
  }
}

async function askDelete(){
  if(!project.value)return
  if(!window.confirm(`Delete "${project.value.name}"? Its generated files, events and database record will be permanently deleted.`))return
  deleting.value=true
  error.value=''
  try{
    es?.close()
    es=null
    await api.deleteProject(id,'Delete')
    router.replace('/projects')
  }catch(e){
    error.value=e.message
  }finally{
    deleting.value=false
  }
}

async function forceStop(){
  if(!window.confirm('Force stop this project now? Current AI requests and pending work will be cancelled.'))return
  stopping.value=true
  error.value=''
  try{
    await api.cancelProject(id)
    es?.close()
    es=null
    connection.value='closed'
    await refreshSummary()
  }catch(e){
    error.value=e.message
  }finally{
    stopping.value=false
  }
}

onMounted(()=>{
  initialLoad()
  timer=setInterval(refreshSummary,6000)
})

onUnmounted(()=>{
  es?.close()
  clearInterval(timer)
  clearTimeout(refreshTimer)
})
</script>

<template>
  <section v-if="project" class="page project-monitor-page">
    <div class="breadcrumb"><RouterLink to="/projects">Projects</RouterLink><span>/</span><span>{{project.request.niche}}</span></div>

    <header class="project-header">
      <div>
        <h1>{{project.name}}</h1>
        <p>{{project.request.duration_minutes}} min · {{project.request.languages.join(', ').toUpperCase()}}</p>
      </div>
      <div class="header-actions">
        <StatusBadge :status="project.status"/>
        <button v-if="project.status==='queued' || project.status==='running'"
                type="button" class="danger-ghost" :disabled="stopping" @click="forceStop">
          {{stopping?'Stopping…':'Force stop'}}
        </button>
        <RouterLink :to="{path:'/',query:{clone:id}}" class="secondary-button">Clone</RouterLink>
        <RouterLink :to="`/projects/${id}/outputs`" class="secondary-button">Outputs</RouterLink>
        <button type="button" class="danger-ghost" :disabled="deleting" @click="askDelete">
          {{deleting?'Deleting…':'Delete'}}
        </button>
      </div>
    </header>

    <p v-if="error" class="inline-error">{{error}}</p>

    <section class="surface meta-surface">
      <div class="meta-chips">
        <span class="meta-chip"><b>Niche</b>{{project.request.niche}}</span>
        <span class="meta-chip"><b>Languages</b>{{project.request.languages.join(', ').toUpperCase()}}</span>
        <span class="meta-chip"><b>Duration</b>{{project.request.duration_minutes}} min</span>
        <span v-if="project.trend_score!=null" class="meta-chip"><b>Trend</b>{{Math.round(project.trend_score)}}/100</span>
        <span v-if="project.request.sub_niche" class="meta-chip"><b>Sub-niche</b>{{project.request.sub_niche}}</span>
        <span v-if="project.request.style" class="meta-chip"><b>Style</b>{{project.request.style}}</span>
        <span v-if="project.request.tone" class="meta-chip"><b>Tone</b>{{project.request.tone}}</span>
        <span v-if="project.request.audience" class="meta-chip"><b>Audience</b>{{project.request.audience}}</span>
        <span v-if="project.request.aspect_ratio" class="meta-chip"><b>Aspect</b>{{project.request.aspect_ratio}}</span>
        <span v-if="project.request.niche==='music'" class="meta-chip"><b>Music provider</b>{{project.request.music_provider}}</span>
      </div>
      <details class="disclosure meta-disclosure">
        <summary>Prompt / topic</summary>
        <p class="meta-topic">{{project.request.topic}}</p>
        <p v-if="project.request.extra_instructions" class="meta-topic"><b>Extra instructions:</b> {{project.request.extra_instructions}}</p>
      </details>
    </section>

    <section class="run-summary">
      <div class="run-summary-top">
        <div>
          <span class="live-dot" :class="connection"></span>
          <b>{{currentNode?.label || project.stage}}</b>
          <span class="muted">{{connection==='live'?'Live':connection}}</span>
        </div>
        <div class="summary-meta">
          <span>{{project.progress}}%</span>
        </div>
      </div>
      <div class="main-progress"><i :style="{width:project.progress+'%'}"></i></div>
    </section>

    <div v-if="project.error" class="error-callout">
      <b>Project stopped</b>
      <span>{{project.error}}</span>
    </div>
    <div v-else-if="project.status==='cancelled'" class="warning-callout">
      <b>Project force-stopped</b>
      <span>No further agents will run. Partial artifacts, if any, are preserved until you delete the project.</span>
    </div>
    <div v-if="project.quality?.quality_warnings?.length" class="warning-callout">
      <b>Quality review required</b>
      <span v-for="w in project.quality.quality_warnings" :key="w">{{w}}</span>
    </div>

    <section v-if="usage.total_calls" class="surface usage-surface">
      <div class="section-heading"><div><h2>LLM usage</h2><p>{{usage.total_calls}} calls · {{usage.total_tokens.toLocaleString()}} tokens</p></div></div>
      <div class="usage-grid">
        <div v-for="[node,row] in topUsageNodes" :key="node" class="usage-row">
          <b>{{node}}</b><span>{{row.calls}} call{{row.calls===1?'':'s'}}</span><strong>{{row.total_tokens.toLocaleString()}}</strong>
        </div>
      </div>
    </section>

    <div class="monitor-stack">
      <section class="surface workflow-surface">
        <div class="section-heading workflow-heading">
          <div>
            <h2>Workflow</h2>
            <p>Horizontal execution map. Pan the canvas or use zoom controls to inspect large workflows.</p>
          </div>
        </div>
        <WorkflowGraph :graph="graph"/>
      </section>

      <section class="surface live-log">
        <div class="section-heading">
          <div><h2>Live log</h2><p>Latest agent activity.</p></div>
        </div>
        <div class="event-list">
          <div v-for="e in [...events].reverse().slice(0,150)" :key="e.id" class="event-row">
            <span class="event-dot" :class="e.status || e.type"></span>
            <div>
              <div class="event-title">
                <b>{{e.node || e.type}}</b>
                <span>{{new Date(e.ts).toLocaleTimeString()}}</span>
              </div>
              <p v-if="e.message">{{e.message}}</p>
              <small v-if="e.type==='fallback'">{{e.from}} → {{e.to}}</small>
              <small v-if="e.type==='retry'">Round {{e.round}} / {{e.max_rounds}}</small>
            </div>
          </div>
          <div v-if="!events.length" class="empty-state small"><p>Waiting for the first event…</p></div>
        </div>
      </section>
    </div>

  </section>

  <section v-else class="page"><div class="skeleton-line"></div></section>
</template>
