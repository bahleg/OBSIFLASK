const togglebtn = document.getElementById("themeToggle");
const body = document.body;

function applyTheme(theme) {
    body.setAttribute("data-bs-theme", theme);
}

let savedTheme = localStorage.getItem("theme");

if (!savedTheme) {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    savedTheme = prefersDark ? "dark" : "light";
}

applyTheme(savedTheme);
if (togglebtn) {
    togglebtn.addEventListener("click", () => {
        const currentTheme = body.getAttribute("data-bs-theme");
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        localStorage.setItem("theme", newTheme);
        applyTheme(newTheme);
    });
}