document.addEventListener("DOMContentLoaded", () => {
	document.querySelectorAll(".accordion-btn").forEach((btn) => {
		btn.addEventListener("click", () => {
			const content = btn.nextElementSibling;
			content.classList.toggle("open");
			const arrow = btn.querySelector(".arrow");
			arrow.textContent = content.classList.contains("open") ? "⬆" : "⬇";
		});
	});
});
