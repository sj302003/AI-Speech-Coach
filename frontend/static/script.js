let mediaRecorder;
let recordedChunks = [];

window.addEventListener("load", async () => {

    await Clerk.load();

    const loginBtn = document.getElementById("loginBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    const email = document.getElementById("userEmail");

    if (!Clerk.user) {

        loginBtn.style.display = "block";
        logoutBtn.style.display = "none";

        loginBtn.onclick = () => Clerk.openSignIn();

    } else {

        loginBtn.style.display = "none";
        logoutBtn.style.display = "block";

        email.innerText = Clerk.user.primaryEmailAddress.emailAddress;

        logoutBtn.onclick = async () => {
            await Clerk.signOut();
            location.reload();
        };

        loadHistory();
    }
});


function showUpload() {
    document.getElementById("uploadSection").style.display = "block";
    document.getElementById("recordSection").style.display = "none";
}

function showRecord() {
    document.getElementById("recordSection").style.display = "block";
    document.getElementById("uploadSection").style.display = "none";

    recordedChunks = [];

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = e => {
                if (e.data.size > 0) recordedChunks.push(e.data);
            };

            mediaRecorder.start();
        });
}

function stopRecording() {
    if (mediaRecorder) mediaRecorder.stop();
}


function submitAudio() {

    const file = document.getElementById("audioUpload").files[0];
    if (!file) return alert("Select file");

    const formData = new FormData();
    formData.append("audio", file);

    analyze(formData);
}

function submitRecordedAudio() {

    const blob = new Blob(recordedChunks, { type: "audio/wav" });

    const formData = new FormData();
    formData.append("audio", blob);

    analyze(formData);
}


async function analyze(formData) {

    if (!Clerk.session) {
        alert("Please login first");
        Clerk.openSignIn();
        return;
    }

    const spinner = document.getElementById("loadingSpinner");

    // 🔥 SHOW spinner
    spinner.style.display = "block";

    try {
        const token = await Clerk.session.getToken();

        const model =
            document.getElementById("modelSelectUpload")?.value ||
            document.getElementById("modelSelectRecord")?.value;

        formData.append("model", model);

        const res = await fetch("/analyze", {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`
            },
            body: formData
        });

        const data = await res.json();

        if (data.error) {
            alert("Error: " + data.error);
            return;
        }

        document.getElementById("transcription").innerText = data.transcription || "";
        document.getElementById("summary").innerText = data.summary || "";
        document.getElementById("sentiment").innerText =
            data.evaluation || data.sentiment || "";

        loadHistory();

    } catch (err) {
        console.error("Analyze error:", err);
        alert("Something went wrong. Check console.");
    } finally {
        // 🔥 HIDE spinner ALWAYS
        spinner.style.display = "none";
    }
}


async function loadHistory() {

    const token = await Clerk.session.getToken();

    const res = await fetch("/api/history", {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });

    const history = await res.json();

    const table = document.getElementById("history");
    table.innerHTML = "";

    history.forEach(item => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${item.created_at}</td>
            <td>${item.audio_name}</td>
            <td>${item.summary}</td>
        `;

        table.appendChild(row);
    });
}