(function () {
  'use strict';

  var COPY_LABEL = '复制';
  var COPIED_LABEL = '已复制';
  var ERROR_LABEL = '复制失败';

  function iconMarkup(kind) {
    if (kind === 'check') {
      return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"></path></svg>';
    }

    return '<svg viewBox="0 0 24 24" aria-hidden="true">' +
      '<rect x="9" y="9" width="11" height="11" rx="2"></rect>' +
      '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>' +
      '</svg>';
  }

  function codeText(pre) {
    var clone = pre.cloneNode(true);
    var lineNumbers = clone.querySelectorAll('.linenos');

    lineNumbers.forEach(function (lineNumber) {
      lineNumber.remove();
    });

    return clone.textContent.replace(/\n$/, '');
  }

  function fallbackCopy(text) {
    var textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.setAttribute('readonly', '');
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();

    var copied = false;
    try {
      copied = document.execCommand('copy');
    } finally {
      textarea.remove();
    }

    return copied ? Promise.resolve() : Promise.reject(new Error('Copy command failed'));
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    return fallbackCopy(text);
  }

  function setButtonState(button, label, icon, stateAttribute) {
    button.innerHTML = iconMarkup(icon);
    button.title = label === COPY_LABEL ? '复制代码' : label;
    button.setAttribute('aria-label', button.title);
    button.removeAttribute('data-copied');
    button.removeAttribute('data-copy-error');

    if (stateAttribute) {
      button.setAttribute(stateAttribute, 'true');
    }
  }

  function addCopyButton(highlight) {
    if (highlight.querySelector('.copy-code-button')) {
      return;
    }

    var pre = highlight.querySelector('pre');
    if (!pre) {
      return;
    }

    var button = document.createElement('button');
    button.className = 'copy-code-button';
    button.type = 'button';
    setButtonState(button, COPY_LABEL, 'copy');
    highlight.classList.add('copy-code-ready');

    button.addEventListener('click', function () {
      var text = codeText(pre);
      copyText(text).then(function () {
        setButtonState(button, COPIED_LABEL, 'check', 'data-copied');
        window.setTimeout(function () {
          setButtonState(button, COPY_LABEL, 'copy');
        }, 1600);
      }).catch(function () {
        setButtonState(button, ERROR_LABEL, 'copy', 'data-copy-error');
        window.setTimeout(function () {
          setButtonState(button, COPY_LABEL, 'copy');
        }, 2000);
      });
    });

    highlight.insertBefore(button, pre);
  }

  function initCopyButtons() {
    document.querySelectorAll('.highlight').forEach(addCopyButton);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCopyButtons);
  } else {
    initCopyButtons();
  }
}());
