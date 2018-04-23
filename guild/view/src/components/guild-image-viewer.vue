<template>
  <div style="height:100%">
    <img ref="img" :src="src" style="max-height:100%; max-width:100%">
  </div>
</template>

<script>
export default {
  name: 'guild-image-viewer',

  props: {
    src: String
  }
};
</script>
