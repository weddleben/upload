function modalAlert(message) {
    const parent = document.getElementById("modalAlert");
    const content = document.getElementById("modalAlertMessage");
    content.innerText = message;
    parent.style.display = "block";
}

function closeModalAlert() {
    const modalElement = document.getElementById("modalAlert");
    modalElement.style.display = "none";
    return;
}

let uploadInProgress = false;

async function uploadFile() {
    if (uploadInProgress) return;
    if (!checkFileSelected()) { return; }

    // let fileExists = await fileAlreadyExistsInDB();
    // if (fileExists) { return; }

    const passwordInput = document.getElementById("uploadPassword");
    if (!passwordInput.value) {
        modalAlert("enter your password first");
        passwordInput.focus();
        return;
    }

    const password = passwordInput.value;
    const file = document.getElementById("uploadFile").files[0];
    const submitButton = document.querySelector('#uploadForm button[type="submit"]');
    uploadInProgress = true;
    submitButton.disabled = true;
    function finishUpload() {
        uploadInProgress = false;
        submitButton.disabled = false;
        document.getElementById("uploadStatus").style.display = "none";
    }
    try {
        const response = await fetch("/upload/check-password", {
            method: "POST",
            body: new URLSearchParams({password}),
        });
        if (!response.ok) {
            if (response.status === 401) {
                passwordInput.value = "";
                passwordInput.focus();
                throw new Error("wrong password — the file was not uploaded");
            }
            throw new Error("Could not verify the password. Please try again or contact the admin.");
        }
    } catch (error) {
        modalAlert(error.message);
        finishUpload();
        return;
    }

    document.getElementById("progress").value = 0;
    document.getElementById("progressPercent").innerText = "0%";
    document.getElementById("uploadStatus").style.display = "block";
    document.getElementById("resultArea").style.display = "none";

    let data = new FormData();
    data.append("file", file);
    data.append("password", password);

    const request = new XMLHttpRequest();
    request.addEventListener("loadend", finishUpload);
    request.addEventListener("error", () => modalAlert("Network error — the upload could not be completed. Please try again."));
    request.addEventListener("abort", () => modalAlert("Upload cancelled."));

    request.upload.addEventListener("progress", function (event) {
        // Get a suitable number for the progress bar. 
        const percent = ((event.loaded / event.total) * 100) - 1;
        const rounded = Math.floor(percent);
        document.getElementById("progress").value = rounded;
        document.getElementById("progressPercent").innerText = rounded + "%"
    })

    request.addEventListener("load", function () {
        if (request.status == 200){
            document.getElementById("progressPercent").innerText = "100%";
            document.getElementById("uploadStatus").style.display = "none";
            const response = JSON.parse(request.responseText);
            document.getElementById("uploadUrl").value = response.url;
            document.getElementById("resultArea").style.display = "block";
        } else if (request.status == 401) {
            modalAlert("wrong password — the upload was rejected");
            passwordInput.value = "";
            passwordInput.focus();
            document.getElementById("uploadStatus").style.display = "none";
        } else if (request.status == 500) {
            modalAlert("server misconfigured: no upload password set. Contact the admin.");
            document.getElementById("uploadStatus").style.display = "none";
        } else {
            alert(`Could not upload ${file.name}! Please try again or contact Mas (it's his fault).`);
            document.getElementById("uploadStatus").style.display = "none";
        }
    })

    const url = "/upload/newfile";
    request.open("PUT", url);
    request.send(data);

}

function checkFileSelected() {
    const file = document.getElementById("uploadFile").files[0];
    if (!file) {
        modalAlert("no file selected");
        return false;
    } else { return true; }
}

function copyUrl() {
    const urlInput = document.getElementById("uploadUrl");
    urlInput.select();
    navigator.clipboard.writeText(urlInput.value);
}

document.getElementById("uploadForm").addEventListener("submit", function (event) {
    event.preventDefault();
    uploadFile();
});

window.addEventListener("dragover", (e) => { e.preventDefault() })
window.addEventListener("drop", handleFileDrop)

document.getElementById("uploadFile").addEventListener("change", function() {
    document.getElementById("resultArea").style.display = "none";
})

function handleFileDrop(drop) {
    drop.preventDefault();
    let fileDrop = drop.dataTransfer.files[0]; // only allow one file at a time
    let dataTransfer = new DataTransfer();
    dataTransfer.items.add(fileDrop);
    let element = document.getElementById("uploadFile");
    element.files = dataTransfer.files;
    document.getElementById("resultArea").style.display = "none";
}
