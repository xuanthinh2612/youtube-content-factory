async function request(url,options={}){
  const response=await fetch(url,options)
  let payload=null
  const type=response.headers.get('content-type')||''
  try{
    payload=type.includes('application/json')?await response.json():await response.text()
  }catch{
    payload=null
  }
  if(!response.ok){
    const describe=value=>typeof value==='string'
      ?value
      :value==null?'Invalid value':JSON.stringify(value)
    const validationErrors=Array.isArray(payload?.detail)
      ?payload.detail.map(item=>{
        const field=Array.isArray(item.loc)?item.loc.filter(part=>part!=='body').join('.'):'request'
        return `${field||'request'}: ${describe(item.msg)}`
      })
      :null
    const message=validationErrors?.length
      ?validationErrors.join('; ')
      :typeof payload==='string'
        ?payload
        :typeof payload?.detail==='string'
          ?payload.detail
          :payload?.detail!=null
            ?describe(payload.detail)
            :payload?.message!=null
              ?describe(payload.message)
              :`Request failed (${response.status})`
    throw new Error(message)
  }
  return payload
}

export const api={
  createProject:(payload)=>request('/api/generate',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(payload)
  }),
  projects:()=>request('/api/projects'),
  project:(id)=>request(`/api/projects/${id}`),
  cancelProject:(id)=>request(`/api/projects/${id}/cancel`,{method:'POST'}),
  deleteProject:(id,confirmation)=>request(`/api/projects/${id}?confirm=${encodeURIComponent(confirmation)}`,{method:'DELETE'}),
  deleteProjectsBulk:(projectIds,confirmation)=>request('/api/projects',{
    method:'DELETE',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({project_ids:projectIds,confirm:confirmation})
  }),
  graph:(id)=>request(`/api/projects/${id}/graph`),
  events:(id,after=0)=>request(`/api/projects/${id}/events?after=${after}`),
  files:(id)=>request(`/api/projects/${id}/files`),
  usage:(id)=>request(`/api/projects/${id}/usage`),
}
