export function formatRuns(runs) {
  return runs.map(formatRun);
}

function formatRun(run) {
  var formattedAttrs = {
    icon: statusIcon(run.status)
  };
  return Object.assign(formattedAttrs, run);
}

function statusIcon(status) {
  if (status === 'completed') {
    return {
      color: 'green',
      icon: 'check-circle',
      tooltip: 'Completed'
    };
  } else if (status === 'error') {
    return {
      color: 'red',
      icon: 'alert',
      tooltip: 'Failed'
    };
  } else if (status === 'terminated') {
    return {
      color: 'teal lighten-2',
      icon: 'close-circle',
      tooltip: 'Terminated'
    };
  } else if (status === 'running') {
    return {
      color: 'green',
      icon: 'dots-horizontal-circle',
      tooltip: 'Running'
    };
  } else {
    return {
      color: 'grey',
      icon: 'help-circle',
      tooltip: status
    };
  }
}
