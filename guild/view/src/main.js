import Vue from 'vue';

import Vuetify from 'vuetify';
import GuildView from './components';

import 'vuetify/dist/vuetify.css';
import 'mdi/css/materialdesignicons.css';

Vue.use(Vuetify);
Vue.use(GuildView);

Vue.config.productionTip = false;

new Vue({
  el: '#app',
  template: '<guild-view/>'
});
