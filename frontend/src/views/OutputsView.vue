<script setup>
import { computed,onMounted,ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../lib/api'

const route=useRoute()
const id=route.params.id
const project=ref(null)
const files=ref([])
const error=ref('')

const finalStems=new Set(['story','script','news_script','suno_prompt','visual_narration'])

const groups=computed(()=>{
  const map=new Map()
  for(const f of files.value){
    const parts=f.split('/')
    if(parts.length!==2)continue
    const match=parts[1].match(/^(.+)\.(md|pdf|docx|json|txt)$/)
    if(!match)continue
    const [,stem,ext]=match
    if(!finalStems.has(stem))continue
    const key=`${parts[0]}:${stem}`
    if(!map.has(key))map.set(key,{language:parts[0],stem,formats:{}})
    map.get(key).formats[ext]=f
  }
  return [...map.values()]
})

const groupedFiles=computed(()=>new Set(
  groups.value.flatMap(g=>Object.values(g.formats))
))
const secondary=computed(()=>files.value.filter(f=>!groupedFiles.value.has(f)))

function label(stem){
  if(stem==='suno_prompt')return 'Suno Master Prompt'
  return stem.replaceAll('_',' ').replace(/\b\w/g,x=>x.toUpperCase())
}

onMounted(async()=>{
  try{
    const [p,f]=await Promise.all([api.project(id),api.files(id)])
    project.value=p
    files.value=f.files
  }catch(e){
    error.value=e.message
  }
})
</script>

<template>
  <section class="page">
    <div class="breadcrumb">
      <RouterLink :to="`/projects/${id}`">Project</RouterLink><span>/</span><span>Outputs</span>
    </div>

    <header class="page-head">
      <h1>{{project?.name || 'Outputs'}}</h1>
      <p>Final content first. Internal checks stay out of the way unless you need them.</p>
    </header>

    <p v-if="error" class="inline-error">{{error}}</p>
    <div v-if="project?.quality?.quality_warnings?.length" class="warning-callout">
      <b>Quality review required</b>
      <span v-for="w in project.quality.quality_warnings" :key="w">{{w}}</span>
    </div>

    <section v-if="project?.request?.niche==='story' && Object.keys(project?.quality?.editor_reviews || {}).length"
             class="surface story-review">
      <header class="story-review-header">
        <div>
          <h2>Editor review of Writer draft</h2>
          <p>One score pass, followed by one full rewrite.</p>
        </div>
      </header>
      <article v-for="(review,language) in project.quality.editor_reviews" :key="language" class="story-review-language">
        <h3>{{language.toUpperCase()}} · {{review.overall_score}}/10 overall</h3>
        <div class="meta-chips">
          <template v-for="(score,dimension) in review" :key="dimension">
            <span v-if="typeof score==='number' && dimension!=='overall_score'"
                  class="meta-chip"><b>{{dimension.replaceAll('_',' ')}}</b>{{score}}/10</span>
          </template>
        </div>
        <p v-if="review.strengths?.length"><b>Strong points:</b> {{review.strengths.join(' · ')}}</p>
        <p v-if="review.issues?.length"><b>Revision points:</b> {{review.issues.join(' · ')}}</p>
      </article>
    </section>

    <section class="surface output-list">
      <div v-if="!groups.length" class="empty-state"><p>Final outputs are not ready yet.</p></div>

      <div v-for="g in groups" :key="`${g.language}:${g.stem}`" class="output-row">
        <div>
          <b>{{g.language.toUpperCase()}} · {{label(g.stem)}}</b>
          <small>{{Object.keys(g.formats).map(x=>x.toUpperCase()).join(' · ')}}</small>
        </div>

        <div class="output-actions">
          <a v-if="g.formats.md"
             :href="`/view/${id}/${g.language}/${g.stem}`"
             target="_blank" rel="noopener">View</a>
          <a v-for="ext in ['pdf','docx','txt','md','json']" :key="ext"
             v-show="g.formats[ext]"
             :href="g.formats[ext] ? `/api/jobs/${id}/download/${g.formats[ext]}` : '#'"
             :download="ext==='md' || ext==='json' ? '' : null">
            {{ext.toUpperCase()}}
          </a>
        </div>
      </div>
    </section>

    <details v-if="secondary.length" class="disclosure artifacts-disclosure">
      <summary>All artifacts · {{secondary.length}}</summary>
      <div class="artifact-list">
        <div v-for="f in secondary" :key="f">
          <span>{{f}}</span>
          <a :href="`/api/jobs/${id}/download/${f}`">Download</a>
        </div>
      </div>
    </details>
  </section>
</template>
