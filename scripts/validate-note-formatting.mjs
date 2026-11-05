import assert from "node:assert/strict";
import { evaluate } from "./cdp.mjs";

assert.ok(
  process.env.GHOST_NOTES_DATA_DIR?.startsWith("/tmp/"),
  "Use a disposable test profile",
);
const port = Number(process.env.GHOST_NOTES_TEST_PORT || 9345);
const results = await evaluate(
  port,
  "note.html",
  `(async () => {
  const results = [];
  const check = (condition, name) => { if (!condition) throw Error(name + ': ' + textEl.innerHTML); results.push(name); };
  const pause = () => new Promise(resolve => setTimeout(resolve, 0));
  function selectAll(html = 'Sample text') {
    textEl.innerHTML = html;
    textEl.focus();
    const range = document.createRange();
    range.selectNodeContents(textEl);
    const selection = window.getSelection();
    selection.removeAllRanges(); selection.addRange(range);
  }
  function open() { if (!formatPopover.classList.contains('open')) formatBtn.click(); }
  function action(cmd, value) {
    open();
    const tab = ['bold','italic','underline','strikeThrough','removeFormat'].includes(cmd) ? 'formatTextTab' : ['insertUnorderedList','insertOrderedList','toggleChecklist'].includes(cmd) ? 'formatListsTab' : 'formatParagraphTab';
    document.getElementById(tab).click();
    const button = [...formatPopover.querySelectorAll('[data-cmd]')].find(b => b.dataset.cmd === cmd && (!value || b.dataset.val === value));
    if (!button || button.closest('[hidden]')) throw Error('Unavailable control: ' + cmd);
    button.scrollIntoView({block:'nearest'});
    button.focus(); button.click();
  }
  for (const cmd of ['bold','italic','underline','strikeThrough']) {
    selectAll('alpha beta gamma');
    const range = document.createRange();
    range.setStart(textEl.firstChild,6); range.setEnd(textEl.firstChild,10);
    window.getSelection().removeAllRanges(); window.getSelection().addRange(range);
    await pause(); open();
    window.getSelection().removeAllRanges();
    action(cmd);
    check(window.getSelection().toString() === 'beta' && document.queryCommandState(cmd), cmd + ' preserves selected text across menu focus');
    check(textEl.firstChild.nodeType === Node.TEXT_NODE && textEl.firstChild.textContent === 'alpha ', cmd + ' leaves surrounding text unchanged');
  }
  selectAll('Colored text'); await pause(); open();
  document.getElementById('formatTextTab').click();
  const blue = formatPopover.querySelector('[data-color="#3b82f6"]');
  blue.focus(); blue.click();
  check(document.queryCommandValue('foreColor') === 'rgb(59, 130, 246)', 'Text color');
  formatPopover.querySelector('[data-color="inherit"]').click();
  check(document.queryCommandValue('foreColor') === getComputedStyle(textEl).color, 'Default text color');
  for (const tag of ['H1','H2','H3','DIV','PRE','BLOCKQUOTE']) {
    selectAll(); await pause(); action('formatBlock',tag);
    check(!!textEl.querySelector(tag), 'Paragraph style ' + tag);
  }
  selectAll(); await pause(); action('insertUnorderedList');
  check(!!textEl.querySelector('ul > li'), 'Bulleted list');
  selectAll(); await pause(); action('insertOrderedList');
  check(!!textEl.querySelector('ol > li'), 'Numbered list');
  selectAll(); await pause(); action('toggleChecklist');
  check(!!textEl.querySelector('ul[data-type="checklist"] > li'), 'Checklist on');
  action('toggleChecklist');
  check(!!textEl.querySelector('ul > li') && !textEl.querySelector('[data-type="checklist"]'), 'Checklist off');
  action('toggleChecklist'); action('insertUnorderedList');
  check(!!textEl.querySelector('ul > li') && !textEl.querySelector('[data-type="checklist"]'), 'Checklist converts to bullets');
  action('toggleChecklist'); action('insertOrderedList');
  check(!!textEl.querySelector('ol > li') && !textEl.querySelector('[data-type="checklist"]'), 'Checklist converts to numbered list');
  selectAll('<h1><b><i>Clear me</i></b></h1>'); await pause(); action('removeFormat');
  check(!textEl.querySelector('h1,b,strong,i,em') && textEl.textContent === 'Clear me', 'Clear formatting');
  setFormatPopoverOpen(false); setColorPopoverOpen(true);
  const before = state.monospace; monoBtn.click();
  check(state.monospace !== before && monoBtn.getAttribute('aria-pressed') === String(!before), 'Monospace note control');
  monoBtn.click();
  check(colorPopover.scrollWidth <= colorPopover.clientWidth, 'Appearance has no horizontal overflow');
  if (innerHeight >= 220) check(colorPopover.scrollHeight <= colorPopover.clientHeight, 'Appearance fits without scrolling');
  setColorPopoverOpen(false);
  open();
  for (const tab of formatTabs) {
    selectFormatTab(tab);
    const panel = document.getElementById(tab.getAttribute('aria-controls'));
    check(panel.scrollWidth <= panel.clientWidth, tab.textContent.trim() + ' has no horizontal overflow');
    if (innerHeight >= 220) check(panel.scrollHeight <= panel.clientHeight, tab.textContent.trim() + ' fits without scrolling');
  }
  formatTabs[0].dispatchEvent(new KeyboardEvent('keydown', {key:'ArrowLeft', bubbles:true}));
  check(formatTabs.at(-1).getAttribute('aria-selected') === 'true', 'Left arrow selects previous tab');
  setFormatPopoverOpen(false);
  return results;
})()`,
);
console.log(
  JSON.stringify({ passed: results.length, checks: results }, null, 2),
);
