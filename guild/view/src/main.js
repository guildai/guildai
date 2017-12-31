import Vue from 'vue';

import Vuetify from 'vuetify';
import VueRouter from 'vue-router';
import GuildView from './components';

import 'vuetify/dist/vuetify.css';
import 'mdi/css/materialdesignicons.css';

Vue.use(Vuetify);
Vue.use(VueRouter);
Vue.use(GuildView);

Vue.config.productionTip = false;

const router = new VueRouter({ mode: 'history' });

new Vue({
  el: '#app',
  template: '<guild-view/>',
  router
});
