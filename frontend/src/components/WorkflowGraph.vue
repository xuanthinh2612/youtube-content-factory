<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const props=defineProps({graph:{type:Object,required:true}})
const scroller=ref(null)
const zoom=ref(.85)
const isDragging=ref(false)
let drag={active:false,sx:0,sy:0,sl:0,st:0}
const NODE_W=166
const NODE_H=48
const LEVEL_GAP=78
const ROW_GAP=18
const PAD_X=54
const PAD_Y=54
const MIN_ZOOM=.4
const MAX_ZOOM=1.5

const layout=computed(()=>{
  const nodes=props.graph.nodes||[]
  const edges=props.graph.edges||[]
  const ids=new Set(nodes.map(n=>n.id))
  const normal=edges.filter(e=>e.kind==='normal' && ids.has(e.source) && ids.has(e.target))

  const indegree=Object.fromEntries(nodes.map(n=>[n.id,0]))
  const adj=Object.fromEntries(nodes.map(n=>[n.id,[]]))
  for(const e of normal){
    indegree[e.target]=(indegree[e.target]||0)+1
    adj[e.source].push(e.target)
  }

  const queue=nodes.filter(n=>indegree[n.id]===0).map(n=>n.id)
  const level=Object.fromEntries(nodes.map(n=>[n.id,0]))
  const visited=new Set()
  while(queue.length){
    const id=queue.shift()
    visited.add(id)
    for(const next of adj[id]||[]){
      level[next]=Math.max(level[next]||0,(level[id]||0)+1)
      indegree[next]-=1
      if(indegree[next]===0)queue.push(next)
    }
  }

  // Retry/fallback cycles are excluded from topology. Keep unusual nodes stable.
  let fallback=Math.max(0,...Object.values(level))
  for(const n of nodes){
    if(!visited.has(n.id) && !Number.isFinite(level[n.id]))level[n.id]=++fallback
  }

  const columns={}
  for(const n of nodes){
    const l=level[n.id]||0
    ;(columns[l] ||= []).push(n)
  }
  const levels=Object.keys(columns).map(Number).sort((a,b)=>a-b)
  const maxRows=Math.max(1,...levels.map(l=>columns[l].length))
  const maxLevel=Math.max(0,...levels)
  const width=PAD_X*2+(maxLevel+1)*NODE_W+maxLevel*LEVEL_GAP
  const height=Math.max(330,PAD_Y*2+maxRows*NODE_H+(maxRows-1)*ROW_GAP)
  const positions={}

  for(const l of levels){
    const col=columns[l]
    const colHeight=col.length*NODE_H+(col.length-1)*ROW_GAP
    const startY=(height-colHeight)/2
    col.forEach((n,i)=>{
      positions[n.id]={
        x:PAD_X+l*(NODE_W+LEVEL_GAP),
        y:startY+i*(NODE_H+ROW_GAP),
      }
    })
  }

  return {positions,width,height}
})

const zoomLabel=computed(()=>`${Math.round(zoom.value*100)}%`)
const svgStyle=computed(()=>({
  width:`${layout.value.width*zoom.value}px`,
  height:`${layout.value.height*zoom.value}px`,
}))

function setZoom(value){
  zoom.value=Math.min(MAX_ZOOM,Math.max(MIN_ZOOM,Number(value)||1))
}
function zoomIn(){setZoom(zoom.value+.1)}
function zoomOut(){setZoom(zoom.value-.1)}
function resetZoom(){setZoom(1)}
function fitWidth(){
  const el=scroller.value
  if(!el || !layout.value.width)return
  const available=Math.max(320,el.clientWidth-28)
  setZoom(Math.min(1,available/layout.value.width))
  el.scrollTo({left:0,top:0,behavior:'smooth'})
}

function onWheel(e){
  // Zoom on wheel when hovering the workflow canvas.
  // Supports both plain wheel and Ctrl+wheel for discoverability.
  // Keep zoom centered at cursor position for natural feel.
  const el=scroller.value
  if(!el) return
  // Avoid hijacking page scroll when user is not over the graph shell;
  // event is already scoped to scroller via @wheel binding.
  e.preventDefault()
  const rect=el.getBoundingClientRect()
  const cx=e.clientX-rect.left
  const cy=e.clientY-rect.top
  const sx=el.scrollLeft
  const sy=el.scrollTop
  const contentX=(sx+cx)/zoom.value
  const contentY=(sy+cy)/zoom.value
  // Exponential zoom factor feels smoother across devices
  const factor=e.deltaY<0 ? 1.08 : 0.92
  const next=Math.min(MAX_ZOOM,Math.max(MIN_ZOOM,zoom.value*factor))
  if(next===zoom.value) return
  zoom.value=next
  // Adjust scroll so the point under cursor stays fixed
  nextTick(()=>{
    el.scrollLeft=contentX*zoom.value-cx
    el.scrollTop=contentY*zoom.value-cy
  })
}

function onMouseDown(e){
  if(e.button!==0) return
  const el=scroller.value
  if(!el) return
  drag.active=true
  drag.sx=e.clientX
  drag.sy=e.clientY
  drag.sl=el.scrollLeft
  drag.st=el.scrollTop
  isDragging.value=true
  el.classList.add('dragging')
  // Prevent text selection while dragging
  e.preventDefault()
}
function onMouseMove(e){
  if(!drag.active) return
  const el=scroller.value
  if(!el) return
  e.preventDefault()
  el.scrollLeft=drag.sl-(e.clientX-drag.sx)
  el.scrollTop=drag.st-(e.clientY-drag.sy)
}
function onMouseUp(){
  if(!drag.active) return
  drag.active=false
  isDragging.value=false
  scroller.value?.classList.remove('dragging')
}
function onWindowMouseMove(e){ if(drag.active) onMouseMove(e) }
function onWindowMouseUp(){ if(drag.active) onMouseUp() }

function edgePath(e,index){
  const a=layout.value.positions[e.source]
  const b=layout.value.positions[e.target]
  if(!a||!b)return ''
  if(e.kind==='normal'){
    const x1=a.x+NODE_W,y1=a.y+NODE_H/2
    const x2=b.x,y2=b.y+NODE_H/2
    const mid=(x1+x2)/2
    return `M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`
  }
  // Retry/fallback routes travel through top/bottom gutters so horizontal
  // execution flow remains readable instead of crossing the main path.
  const top=index%2===0
  const gutterY=top?20:layout.value.height-20
  const x1=a.x+NODE_W/2,y1=a.y+(top?0:NODE_H)
  const x2=b.x+NODE_W/2,y2=b.y+(top?0:NODE_H)
  return `M ${x1} ${y1} C ${x1} ${gutterY}, ${x2} ${gutterY}, ${x2} ${y2}`
}

watch(
  ()=>props.graph.nodes?.map(n=>`${n.id}:${n.status}`).join('|'),
  async()=>{
    await nextTick()
    const running=props.graph.nodes?.find(n=>n.status==='running' || n.status==='retrying')
    const pos=running && layout.value.positions[running.id]
    if(pos && scroller.value){
      scroller.value.scrollTo({
        left:Math.max(0,(pos.x*zoom.value)-scroller.value.clientWidth*.35),
        top:Math.max(0,(pos.y*zoom.value)-scroller.value.clientHeight*.35),
        behavior:'smooth'
      })
    }
  }
)

onMounted(()=>{
  nextTick(()=>fitWidth())
  window.addEventListener('mousemove',onWindowMouseMove)
  window.addEventListener('mouseup',onWindowMouseUp)
})
onUnmounted(()=>{
  window.removeEventListener('mousemove',onWindowMouseMove)
  window.removeEventListener('mouseup',onWindowMouseUp)
})
</script>

<template>
  <div class="graph-shell">
    <div class="graph-toolbar" aria-label="Workflow zoom controls">
      <button type="button" @click="zoomOut" aria-label="Zoom out">−</button>
      <span>{{zoomLabel}}</span>
      <button type="button" @click="zoomIn" aria-label="Zoom in">+</button>
      <button type="button" class="graph-tool-text" @click="fitWidth">Fit</button>
      <button type="button" class="graph-tool-text" @click="resetZoom">100%</button>
      <span class="graph-hint">Lăn chuột để zoom · Giữ chuột trái để kéo</span>
    </div>

    <div ref="scroller" class="graph-scroller" :class="{dragging:isDragging}" @wheel.prevent="onWheel" @mousedown="onMouseDown">
      <svg :viewBox="`0 0 ${layout.width} ${layout.height}`"
           :style="svgStyle"
           class="workflow-svg">
        <defs>
          <marker id="arrow-normal" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
            <path d="M0,0 L8,4 L0,8 z"/>
          </marker>
        </defs>

        <g v-for="(e,i) in graph.edges" :key="`${e.source}-${e.target}-${e.kind}-${i}`"
           :class="['graph-edge',e.kind,e.taken?'taken':'dim']">
          <path :d="edgePath(e,i)" fill="none" marker-end="url(#arrow-normal)"/>
          <title>{{e.label || e.kind}}</title>
        </g>

        <g v-for="n in graph.nodes" :key="n.id"
           :transform="`translate(${layout.positions[n.id]?.x||0},${layout.positions[n.id]?.y||0})`"
           :class="['graph-node',n.group,n.status||'idle']">
          <rect :width="NODE_W" :height="NODE_H" rx="10"/>
          <circle class="node-activity" :cx="NODE_W-13" cy="13" r="3" aria-hidden="true"/>
          <text :x="NODE_W/2" y="20" text-anchor="middle">{{n.label}}</text>
          <text :x="NODE_W/2" y="36" text-anchor="middle" class="node-status">{{n.status}}</text>
          <title>{{n.message || n.label}}</title>
        </g>
      </svg>
    </div>
  </div>
</template>
