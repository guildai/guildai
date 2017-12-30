export function fetchRuns(cb) {
  return _fetch('/runs', cb);
}

export function fetchConfig(cb) {
  return _fetch('/config', cb);
}

function _fetch(path, cb) {
  var url = process.env.VIEW_BASE + path;
  fetch(url).then(function (resp) {
    return resp.json();
  }).then(function (json) {
    cb(json);
  });
}
