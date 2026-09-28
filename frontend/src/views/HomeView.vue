<script setup>
import { reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DurationSlider from '../components/DurationSlider.vue'
import { api } from '../lib/api'

const router=useRouter()
const route=useRoute()
const busy=ref(false)
const cloneLoading=ref(false)
const cloneSource=ref(null)
const error=ref('')
let cloneLoadToken=0

function emptyForm(){
  return {
    topic:'',
    niche:'story',
    sub_niche:'',
    languages:['vi'],
    duration_minutes:10,
    style:'',
    tone:'',
    audience:'',
    extra_instructions:'',
    timezone:Intl.DateTimeFormat().resolvedOptions().timeZone || '',
    source_project_id:'',
    aspect_ratio:'16:9',
    music_provider:'generic',
  }
}

const form=reactive(emptyForm())
watch(()=>form.niche,niche=>{
  if(niche==='music' && form.duration_minutes>8)form.duration_minutes=8
})

const languageOptions=[
  ['vi','VI'],['en','EN'],['ja','JA'],['ko','KO'],['zh','ZH'],['es','ES']
]

function toggleLang(code){
  form.languages=form.languages.includes(code)
    ? form.languages.filter(x=>x!==code)
    : [...form.languages,code]
  if(!form.languages.length)form.languages=['vi']
}

function fillFromRequest(request={}){
  const defaults=emptyForm()
  Object.assign(form,{
    topic:typeof request.topic==='string'?request.topic:defaults.topic,
    niche:['story','fact','news','music','visual'].includes(request.niche)?request.niche:defaults.niche,
    sub_niche:typeof request.sub_niche==='string'?request.sub_niche:defaults.sub_niche,
    languages:Array.isArray(request.languages) && request.languages.length?[...request.languages]:defaults.languages,
    duration_minutes:Number.isInteger(request.duration_minutes)
      ?Math.min(request.duration_minutes,request.niche==='music'?8:60):defaults.duration_minutes,
    style:typeof request.style==='string'?request.style:defaults.style,
    tone:typeof request.tone==='string'?request.tone:defaults.tone,
    audience:typeof request.audience==='string'?request.audience:defaults.audience,
    extra_instructions:typeof request.extra_instructions==='string'?request.extra_instructions:defaults.extra_instructions,
    timezone:typeof request.timezone==='string' && request.timezone?request.timezone:defaults.timezone,
    source_project_id:typeof request.source_project_id==='string'?request.source_project_id:defaults.source_project_id,
    aspect_ratio:['16:9','9:16','1:1','4:3','21:9'].includes(request.aspect_ratio)
      ?request.aspect_ratio:defaults.aspect_ratio,
    music_provider:typeof request.music_provider==='string' && request.music_provider
      ?request.music_provider:defaults.music_provider,
  })
}

async function loadClone(rawId){
  const token=++cloneLoadToken
  const id=Array.isArray(rawId)?rawId[0]:rawId
  cloneSource.value=null
  cloneLoading.value=false
  error.value=''
  Object.assign(form,emptyForm())
  if(!id)return
  if(!/^[A-Za-z0-9_-]{1,128}$/.test(id)){
    error.value='Invalid source project ID.'
    return
  }

  cloneLoading.value=true
  try{
    const project=await api.project(id)
    if(token!==cloneLoadToken)return
    fillFromRequest(project.request)
    cloneSource.value={id:project.id,name:project.name}
  }catch(e){
    if(token===cloneLoadToken)error.value=`Could not load project to clone: ${e.message}`
  }finally{
    if(token===cloneLoadToken)cloneLoading.value=false
  }
}

watch(()=>route.query.clone,loadClone,{immediate:true})

async function submit(){
  const topic=form.topic.trim()
  if(topic.length<3){
    error.value='Prompt must contain at least 3 characters.'
    return
  }
  if(topic.length>20000){
    error.value='Prompt must be 20,000 characters or fewer.'
    return
  }

  error.value=''
  busy.value=true
  try{
    const payload={
      topic,
      niche:form.niche,
      sub_niche:form.sub_niche.trim(),
      languages:[...form.languages],
      duration_minutes:form.duration_minutes,
      style:form.style.trim(),
      tone:form.tone.trim(),
      audience:form.audience.trim(),
      extra_instructions:form.extra_instructions.trim(),
      source_project_id:form.source_project_id.trim(),
      aspect_ratio:form.niche==='visual'?form.aspect_ratio:'',
      music_provider:form.niche==='music'?form.music_provider:'generic',
      timezone:form.timezone.trim() || Intl.DateTimeFormat().resolvedOptions().timeZone || '',
    }
    const result=await api.createProject(payload)
    router.push(`/projects/${result.job_id}`)
  }catch(e){
    error.value=e.message
  }finally{
    busy.value=false
  }
}
</script>

<template>
  <section class="page create-page">
    <header class="page-head compact-head">
      <h1>Create a project</h1>
      <p>One prompt. The workflow handles planning, research, writing and quality checks.</p>
    </header>

    <form class="composer" @submit.prevent="submit">
      <textarea v-model="form.topic" class="prompt-input" rows="7"
                placeholder="What do you want to create?"
                aria-label="Main prompt"></textarea>

      <div class="composer-toolbar">
        <div class="segmented" aria-label="Content type">
          <button v-for="n in ['story','fact','news','music','visual']" :key="n"
                  type="button" :class="{active:form.niche===n}" @click="form.niche=n">
            {{n==='music'?'song':n}}
          </button>
        </div>

        <button class="primary compact-primary" type="submit" :disabled="busy || cloneLoading">
          {{cloneLoading?'Loading…':busy?'Creating…':'Generate'}}
        </button>
      </div>
    </form>

    <p v-if="error" class="inline-error">{{error}}</p>
    <div v-if="cloneSource" class="warning-callout clone-callout">
      <b>Cloning inputs from “{{cloneSource.name}}”</b>
      <span>Edit the prompt or any metadata below, then generate to create a separate project. Existing outputs are not copied.</span>
    </div>

    <section class="settings-block">
      <div class="settings-row">
        <DurationSlider v-model="form.duration_minutes" :max="form.niche==='music'?8:60"/>

        <div class="language-control">
          <div class="field-heading"><span>Languages</span><strong>{{form.languages.length}}</strong></div>
          <div class="chip-grid">
            <button v-for="[code,name] in languageOptions" :key="code" type="button"
                    class="chip" :class="{selected:form.languages.includes(code)}"
                    @click="toggleLang(code)">
              {{name}}
            </button>
          </div>
        </div>
      </div>

      <details class="disclosure" :open="!!cloneSource">
        <summary>More options</summary>
        <div class="options-grid">
          <label>Sub-niche<input v-model="form.sub_niche" placeholder="Horror, science, AI…"></label>
          <label>Style<input v-model="form.style" placeholder="Cinematic, documentary…"></label>
          <label>Tone<input v-model="form.tone" placeholder="Dark, calm, analytical…"></label>
          <label>Audience<input v-model="form.audience" placeholder="General audience"></label>
          <label>Timezone<input v-model="form.timezone" placeholder="Asia/Ho_Chi_Minh"></label>
        </div>
        <label>Extra instructions
          <textarea v-model="form.extra_instructions" rows="3" placeholder="Optional constraints or preferences"></textarea>
        </label>
      </details>

      <details v-if="form.niche==='visual'" class="disclosure" open>
        <summary>Content source</summary>
        <label>Aspect ratio
          <select v-model="form.aspect_ratio">
            <option value="16:9">16:9 · Landscape</option>
            <option value="9:16">9:16 · Vertical</option>
            <option value="1:1">1:1 · Square</option>
            <option value="4:3">4:3 · Classic</option>
            <option value="21:9">21:9 · Ultrawide</option>
          </select>
        </label>
        <label>Source project ID
          <input v-model="form.source_project_id" placeholder="Optional: completed Story / Fact / News project ID">
          <small>When provided, Visual uses that project's canonical Blueprint and final narration instead of inventing a parallel visual story.</small>
        </label>
      </details>

      <details v-if="form.niche==='music'" class="disclosure" open>
        <summary>Music generation</summary>
        <label>Target provider
          <select v-model="form.music_provider">
            <option value="generic">Generic music model</option>
            <option value="suno">Suno handoff</option>
          </select>
          <small>The creative package remains provider-neutral; the export can be mapped by an adapter.</small>
        </label>
      </details>

      <p v-if="form.niche==='fact' || form.niche==='news'" class="muted-note">
        Fact and News automatically use the configured model's native web search and traceable citations.
      </p>
    </section>
  </section>
</template>
