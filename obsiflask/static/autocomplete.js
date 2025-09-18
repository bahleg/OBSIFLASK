let autocompleteIndex = -1;
let autocompleteItems = [];


  async function triggerAutocomplete(context, editor, coords) {
    const suggestions = await fetchSuggestions(context);
    if (suggestions.length > 0) {
      showSuggestions(suggestions, coords.left, coords.top, s => insertCompletion(editor, s));
    }
  }


function insertCompletion(editor, suggestion) {
  if (editor instanceof HTMLTextAreaElement) {
    let start = editor.selectionStart;
    let end = editor.selectionEnd;
    let before = editor.value.substring(0, start - suggestion.erase);
    let after = editor.value.substring(end);
    editor.value = before + suggestion.text + after;
    let pos = before.length + suggestion.text.length;
    editor.selectionStart = editor.selectionEnd = pos;
    editor.focus();
  } else if (editor && editor.replaceRange) {
    // Codemirror (EasyMDE)
    const cm = editor;
    const cursor = cm.getCursor();
    let from = { line: cursor.line, ch: cursor.ch - suggestion.erase };
    cm.replaceRange(suggestion.text, from, cursor);
  }
}


function showSuggestions(suggestions, x, y, onSelect) {
  const menu = document.getElementById("autocomplete");
  menu.innerHTML = "";
  autocompleteIndex = -1;
  autocompleteItems = suggestions;

  suggestions.forEach((s, i) => {
    const item = document.createElement("div");
    item.textContent = s.text;
    item.className = "item";
    item.onmouseenter = () => highlightItem(i);
    item.onmousedown = e => {
      e.preventDefault();
      onSelect(s);
      hideSuggestions();
    };
    menu.appendChild(item);
  });

  menu.style.left = x + "px";
  menu.style.top = y + "px";
  menu.style.display = "block";

  document.addEventListener("click", hideSuggestions, { once: true });
  document.addEventListener("keydown", handleAutocompleteKeys);
}

function hideSuggestions() {
  const menu = document.getElementById("autocomplete");
  menu.style.display = "none";
  autocompleteIndex = -1;
  autocompleteItems = [];
  document.removeEventListener("keydown", handleAutocompleteKeys);
}

function highlightItem(index) {
  const menu = document.getElementById("autocomplete");
  const items = menu.querySelectorAll(".item");
  items.forEach((el, i) => {
    el.classList.toggle("active", i === index);
  });
  autocompleteIndex = index;
}

function handleAutocompleteKeys(e) {
  const menu = document.getElementById("autocomplete");
  if (menu.style.display === "none") return;

  if (e.key === "ArrowDown") {
    e.preventDefault();
    if (autocompleteIndex < autocompleteItems.length - 1) {
      highlightItem(autocompleteIndex + 1);
    }
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    if (autocompleteIndex > 0) {
      highlightItem(autocompleteIndex - 1);
    }
  } else if (e.key === "Enter") {
    if (autocompleteIndex >= 0) {
      e.preventDefault();
      const s = autocompleteItems[autocompleteIndex];
      const onSelect = menu.querySelectorAll(".item")[autocompleteIndex].onmousedown;
      onSelect({ preventDefault: () => {} });
    }
  } else if (e.key === "Escape") {
    hideSuggestions();
  }
}

function getCaretCoordinates(textarea, position) {
  const div = document.createElement("div");
  const style = window.getComputedStyle(textarea);

  // Скопировать стили, которые влияют на рендер текста
  const properties = [
    "boxSizing","width","height","overflowX","overflowY",
    "borderTopWidth","borderRightWidth","borderBottomWidth","borderLeftWidth",
    "paddingTop","paddingRight","paddingBottom","paddingLeft",
    "fontStyle","fontVariant","fontWeight","fontStretch","fontSize",
    "fontSizeAdjust","lineHeight","fontFamily","textAlign","textTransform",
    "textIndent","textDecoration","letterSpacing","wordSpacing","tabSize","MozTabSize"
  ];
  properties.forEach(prop => {
    div.style[prop] = style[prop];
  });

  div.style.position = "absolute";
  div.style.whiteSpace = "pre-wrap";
  div.style.wordWrap = "break-word";
  div.style.visibility = "hidden";

  // Текст до курсора
  div.textContent = textarea.value.substring(0, position);

  // Каретка
  const span = document.createElement("span");
  span.textContent = textarea.value.substring(position) || "."; 
  div.appendChild(span);

  document.body.appendChild(div);
  const rect = span.getBoundingClientRect();
  const taRect = textarea.getBoundingClientRect();

  // Учитываем скролл внутри textarea
  const coords = {
    left: taRect.left + (rect.left - div.getBoundingClientRect().left) - textarea.scrollLeft,
    top: taRect.top + (rect.top - div.getBoundingClientRect().top) - textarea.scrollTop + parseInt(style.lineHeight || "16", 10)
  };

  document.body.removeChild(div);
  return coords;
}

