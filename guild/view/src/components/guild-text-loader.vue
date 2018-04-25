<template>
  <div id="root">
    <div
      id="loading"
      v-if="loading"
      class="elevation-3 pa-3 grey darken-3 white--text">
      <span class="mr-3">Reading file</span>
      <v-progress-circular indeterminate color="white" size="18" />
    </div>
    <slot v-else></slot>
  </div>
</template>

<script>
export default {
  name: 'guild-text-loader',

  props: {
    src: String
  },

  data() {
    return {
      loading: false
    };
  },

  mounted() {
    this.refresh();
  },

  watch: {
    src() {
      this.refresh();
    }
  },

  methods: {
    refresh() {
      this.clear();
      const showLoading = this.scheduleLoading(100);
      this.scheduleFetch(0, showLoading);
    },

    clear() {
      this.$emit('input', '');
    },

    scheduleLoading(timeout) {
      const this_ = this;
      return setTimeout(() => {
        this_.loading = true;
      }, timeout);
    },

    scheduleFetch(timeout, showLoading) {
      const this_ = this;
      setTimeout(() => {
        fetch(this_.src).then(function(resp) {
          return resp.text();
        }).then(function(text) {
          this_.$emit('input', text);
          clearTimeout(showLoading);
          this_.loading = false;
        });
      }, timeout);
    }
  }
};
</script>

<style scoped>
#root {
  display: flex;
  flex-direction: column;
  flex: 1;
  width: 100%;
  justify-content: center;
  align-items: center;
}

#loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
