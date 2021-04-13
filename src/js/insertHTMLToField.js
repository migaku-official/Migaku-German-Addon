function insertHTMLToField(newHTML, ordinal) {
  const sel = window.getSelection();
  const field = document.getElementById('f' + ordinal);
  selectAllFieldNodes(field, sel);
  selectText(field, sel);
  setFormat('inserthtml', newHTML.replace(/◱/g, '\n').trim());
}
try {
  insertHTMLToField('%s', '%s');
} catch (e) {
  alert(e);
}
