export function fetchData(path, cb) {
  return _fetch(_dataUrl(path), cb);
}

function _dataUrl(base) {
  return base + window.location.search;
}

function _fetch(path, cb) {
  var url = process.env.VIEW_BASE + path;
  fetch(url).then(function(resp) {
    return resp.json();
  }).then(function(json) {
    cb(json);
  });
}
