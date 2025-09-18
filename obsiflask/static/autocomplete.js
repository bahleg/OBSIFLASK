const cm = easyMDE.codemirror;
const menu = document.getElementById("autocomplete");
async function fetchSuggestions(context) {
  const resp = await fetch(url_autocomplete, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ context })
  });
  return await resp.json(); // [{text: "...", erase: N}, ...]
}

function showSuggestions(suggestions, x, y, onSelect) {
  menu.innerHTML = "";
  autocompleteIndex = -1;
  autocompleteItems = suggestions;

  suggestions.forEach((s, i) => {
    const item = document.createElement("div");
    item.textContent = s.short;
    item.className = "dropdown-item";
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
  menu.style.display = "none";
  autocompleteIndex = -1;
  autocompleteItems = [];
  document.removeEventListener("keydown", handleAutocompleteKeys);
}

function highlightItem(index) {
  const items = menu.querySelectorAll(".dropdown-item");
  items.forEach((el, i) => el.classList.toggle("active", i === index));
  autocompleteIndex = index;
}

function handleAutocompleteKeys(e) {
  if (menu.style.display === "none") return;

  if (e.key === "ArrowDown") {
    e.preventDefault();
    if (autocompleteIndex < autocompleteItems.length - 1) highlightItem(autocompleteIndex + 1);
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    if (autocompleteIndex > 0) highlightItem(autocompleteIndex - 1);
  } else if (e.key === "Enter") {
    if (autocompleteIndex >= 0) {
      e.preventDefault();
      const s = autocompleteItems[autocompleteIndex];
      insertCompletion(cm, s);
      hideSuggestions();
    }
  } else if (e.key === "Escape") {
    hideSuggestions();
  }
}

function insertCompletion(cm, suggestion) {
  const cursor = cm.getCursor();
  const from = { line: cursor.line, ch: cursor.ch - suggestion.erase };
  cm.replaceRange(suggestion.text, from, cursor);
  cm.focus();
}

async function triggerAutocomplete() {
  const cursor = cm.getCursor();
  let context = cm.getLine(cursor.line).substring(0, cursor.ch);
  for (let i = cursor.line - 1; i >= 0 && context.length < 256; i--) {
    context = cm.getLine(i) + "\n" + context;
  }
  context = context.slice(-256);
  const coords = cm.cursorCoords(cursor, "page");
  const suggestions = await fetchSuggestions(context);
  if (suggestions.length > 0) showSuggestions(suggestions, coords.left, coords.bottom, s => insertCompletion(cm, s));
}

// ========================== События ==========================
cm.on("keydown", async (cmInstance, e) => {
  if (e.key === "Tab") {
    const cursor = cm.getCursor();
    const line = cm.getLine(cursor.line).substring(0, cursor.ch);
      e.preventDefault();
      await triggerAutocomplete();
  }
});

document.getElementById("flo-autocomplete-btn").addEventListener("click", async () => {
  await triggerAutocomplete();
});