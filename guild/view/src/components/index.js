import GuildFilesViewer from './guild-files-viewer.vue';
import GuildMidi from './guild-midi.vue';
import GuildRunFiles from './guild-run-files.vue';
import GuildRunOverview from './guild-run-overview.vue';
import GuildRunStatusIcon from './guild-run-status-icon.vue';
import GuildRunTitlebar from './guild-run-titlebar.vue';
import GuildRunsList from './guild-runs-list.vue';
import GuildText from './guild-text.vue';
import GuildView from './guild-view.vue';
import GuildViewToolbar from './guild-view-toolbar.vue';

GuildView.install = function install(Vue) {
  const component = function(c) {
    Vue.component(c.name, c);
  };
  component(GuildFilesViewer);
  component(GuildMidi);
  component(GuildRunFiles);
  component(GuildRunOverview);
  component(GuildRunStatusIcon);
  component(GuildRunTitlebar);
  component(GuildRunsList);
  component(GuildText);
  component(GuildView);
  component(GuildViewToolbar);
};

export default GuildView;
