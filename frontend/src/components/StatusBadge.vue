<script setup>
const props=defineProps({status:{type:String,default:'unknown'}})
const labels={
  queued:'Queued',
  running:'Running',
  completed:'Completed',
  failed:'Failed',
  cancelled:'Cancelled',
}
</script>

<template>
  <span class="status-badge" :class="status">
    <i></i>{{labels[status] || status}}
  </span>
</template>
