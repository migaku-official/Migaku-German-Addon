function insertHTML(newHTML) {
  const sel = window.getSelection();
  const field = get_field(sel);
  selectAllFieldNodes(field, sel);
  newHTML = newHTML.replace(/◱/g, '\n').trim();
  setFormat('inserthtml', newHTML);
}
try {
  insertHTML('%s');
} catch (e) {
  alert(e);
}
