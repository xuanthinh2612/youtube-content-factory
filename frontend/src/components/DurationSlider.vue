<script setup>
const model=defineModel({default:10})
defineProps({max:{type:Number,default:60}})
</script>

<template>
  <div class="duration-control">
    <div class="field-heading">
      <span>Length</span>
      <strong>{{model}} min</strong>
    </div>
    <div class="slider-wrap">
      <input v-model.number="model" type="range" min="1" :max="max" step="1" aria-label="Video length">
    </div>
    <div class="scale duration-scale">
      <span>1 min</span>
      <span>{{max===8?'2':'15'}}</span>
      <span>{{max===8?'4':'30'}}</span>
      <span>{{max===8?'6':'45'}}</span>
      <span>{{max}} min</span>
    </div>
  </div>
</template>
