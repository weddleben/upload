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

async function uploadFile() {
    if (!checkFileSelected()) { return; }

    // let fileExists = await fileAlreadyExistsInDB();
    // if (fileExists) { return; }

    document.getElementById("uploadStatus").style.display = "block";

    let data = new FormData();
    const file = document.getElementById("uploadFile").files[0];
    data.append("file", file)

    const request = new XMLHttpRequest();

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
            // await new Promise(requestAnimationFrame); // allow time for updating content before alert() box
            alert(`${file.name} successfully uploaded!`);
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

async function fileAlreadyExistsInDB() {
    const filename = document.getElementById("uploadFile").files[0].name;
    const data = { "filename": filename };
    let response = await fetch("/upload/checkduplicate", {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        method: "POST",
        body: JSON.stringify(data)
    })

    if (response.ok) {
        return false;
    }
    let responseJSON = await response.json();
    modalAlert(responseJSON.response);
    return true;
}

window.addEventListener("dragover", (e) => { e.preventDefault() })
window.addEventListener("drop", handleFileDrop)

function handleFileDrop(drop) {
    drop.preventDefault();
    let fileDrop = drop.dataTransfer.files[0]; // only allow one file at a time
    let dataTransfer = new DataTransfer();
    dataTransfer.items.add(fileDrop);
    let element = document.getElementById("uploadFile");
    element.files = dataTransfer.files;

}