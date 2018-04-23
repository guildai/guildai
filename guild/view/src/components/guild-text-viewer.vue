<template>
  <guild-text-loader :src="src" @input="text = $event">
    <textarea readonly class="elevation-3 pa-3 white" >{{ text }}</textarea>
  </guild-text-loader>
</template>

<script>
export default {
  name: 'guild-text-viewer',

  props: {
    src: String
  },

  data() {
    return {
      text: ''
    };
  }
};
</script>

<style scoped>
textarea {
  overflow: auto;
  flex: 1;
  resize: none;
  font-family: monospace;
}

textarea:focus {
  outline: none;
}
</style>
