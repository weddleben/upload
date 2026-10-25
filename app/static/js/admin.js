const deleteDialog = document.getElementById("deleteDialog");
const deleteForm = document.getElementById("deleteForm");
const deletePassword = document.getElementById("deletePassword");
const deleteError = document.getElementById("deleteError");
const confirmDelete = document.getElementById("confirmDelete");
const cancelDelete = document.getElementById("cancelDelete");
let selectedDeleteButton = null;
let deleting = false;

document.querySelectorAll(".delete-file").forEach((button) => {
    button.addEventListener("click", () => {
        selectedDeleteButton = button;
        deleteForm.reset();
        deleteError.textContent = "";
        deletePassword.removeAttribute("aria-invalid");
        document.getElementById("deleteFilename").textContent = button.dataset.path;
        deleteDialog.showModal();
        deletePassword.focus();
    });
});

cancelDelete.addEventListener("click", () => deleteDialog.close());
deleteDialog.addEventListener("cancel", (event) => {
    if (deleting) event.preventDefault();
});
deleteDialog.addEventListener("close", () => {
    deleteForm.reset();
    if (selectedDeleteButton?.isConnected) selectedDeleteButton.focus();
    else document.querySelector(".admin header a").focus();
    selectedDeleteButton = null;
});

deleteForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (deleting || !selectedDeleteButton) return;
    const button = selectedDeleteButton;
    const path = button.dataset.path;
    deleting = true;
    confirmDelete.disabled = true;
    cancelDelete.disabled = true;
    deletePassword.disabled = true;
    confirmDelete.textContent = "Deleting…";
    deleteError.textContent = "";
    deletePassword.removeAttribute("aria-invalid");
    try {
        const response = await fetch(button.dataset.url, {
            method: "DELETE",
            body: new URLSearchParams({path, password: deletePassword.value}),
        });
        if (!response.ok) {
            const result = await response.json().catch(() => ({}));
            if (response.status === 401) {
                deletePassword.value = "";
                deletePassword.setAttribute("aria-invalid", "true");
                throw new Error("Incorrect master password. The file was not deleted. Please try again.");
            }
            throw new Error(result.error || "Could not delete the file. Please try again.");
        }
        button.closest("tr").remove();
        const summary = document.getElementById("fileSummary");
        summary.dataset.count = Number(summary.dataset.count) - 1;
        summary.dataset.bytes = Number(summary.dataset.bytes) - Number(button.dataset.size);
        const count = Number(summary.dataset.count);
        summary.textContent = `${count} file${count === 1 ? "" : "s"} · ${Number(summary.dataset.bytes).toLocaleString()} bytes total`;
        document.getElementById("deleteStatus").textContent = `Deleted ${path}.${count === 0 ? " No files uploaded yet." : ""}`;
        deleteDialog.close();
    } catch (error) {
        deleteError.textContent = error.message;
    } finally {
        deleting = false;
        confirmDelete.disabled = false;
        cancelDelete.disabled = false;
        deletePassword.disabled = false;
        confirmDelete.textContent = "Delete file";
        if (deleteDialog.open) deletePassword.focus();
    }
});
