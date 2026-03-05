const dropArea = document.getElementById('dropArea');
const fileInput = document.getElementById('fileInput');
const uploadStatus = document.getElementById('uploadStatus');
const dashboard = document.getElementById('dashboard');
const previewImage = document.getElementById('previewImage');
const pdfPreviewContainer = document.getElementById('pdfPreviewContainer');
const pdfPreviewFrame = document.getElementById('pdfPreviewFrame');
const statusIndicator = document.getElementById('statusIndicator');
const jsonOutput = document.getElementById('jsonOutput');

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
});
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => {
        dropArea.classList.add('dragover');
    }, false);
});
['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => {
        dropArea.classList.remove('dragover');
    }, false);
});

dropArea.addEventListener('drop', (e) => {
    let dt = e.dataTransfer;
    let files = dt.files;
    handleFiles(files);
});

fileInput.addEventListener('change', function () {
    handleFiles(this.files);
});

function handleFiles(files) {
    if (files.length === 0) return;
    const file = files[0];

    const validTypes = ['image/jpeg', 'image/png', 'application/pdf'];
    if (!validTypes.includes(file.type)) {
        uploadStatus.innerHTML = '<span class="text-danger">Invalid file type. Only JPG, PNG, and PDF allowed.</span>';
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        uploadStatus.innerHTML = '<span class="text-danger">File size exceeds 5MB limit.</span>';
        return;
    }

    uploadStatus.innerHTML = '<span class="text-info">Uploading and extracting data...</span>';

    showPreview(file);
    uploadFile(file);
}

function showPreview(file) {
    dashboard.classList.remove('d-none');

    const reader = new FileReader();
    reader.onload = (e) => {
        if (file.type.startsWith('image/')) {
            previewImage.src = e.target.result;
            previewImage.style.display = 'block';
            pdfPreviewContainer.style.display = 'none';
        } else if (file.type === 'application/pdf') {
            pdfPreviewFrame.src = e.target.result;
            previewImage.style.display = 'none';
            pdfPreviewContainer.style.display = 'block';
        }
    };
    reader.readAsDataURL(file);
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        statusIndicator.style.display = 'block';
        statusIndicator.className = 'alert alert-info shadow-sm';
        statusIndicator.innerText = 'Analyzing invoice ...';
        document.getElementById('jsonFallback').classList.remove('d-none');
        document.getElementById('resultCard').classList.add('d-none');
        jsonOutput.innerText = 'Loading...';

        const response = await fetch('http://127.0.0.1:8000/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || 'Upload failed');
        }

        uploadStatus.innerHTML = '<span class="text-success">Extraction complete!</span>';
        displayResults(result);

    } catch (error) {
        uploadStatus.innerHTML = `<span class="text-danger">Error During Upload</span>`;
        statusIndicator.style.display = 'block';
        statusIndicator.className = 'alert alert-danger shadow-sm';
        statusIndicator.innerText = 'Error processing document.';
        document.getElementById('resultCard').classList.add('d-none');
        document.getElementById('jsonFallback').classList.remove('d-none');
        jsonOutput.innerText = JSON.stringify({ error: error.message }, null, 2);
    }
}

function displayResults(data) {
    statusIndicator.style.display = 'block';

    if (data.status === 'correct') {
        statusIndicator.className = 'alert alert-success shadow-sm';
        statusIndicator.innerHTML = `✅ <strong>Success:</strong> ${data.message}`;
    } else {
        statusIndicator.className = 'alert alert-danger shadow-sm';
        statusIndicator.innerHTML = `❌ <strong>Error:</strong> ${data.message}`;
    }

    if (data.vendor && Array.isArray(data.items)) {
        document.getElementById('resultCard').classList.remove('d-none');
        document.getElementById('jsonFallback').classList.add('d-none');

        document.getElementById('resVendor').textContent = data.vendor;
        document.getElementById('resDate').textContent = data.date || '-';

        const tbody = document.getElementById('resItems');
        tbody.innerHTML = '';

        data.items.forEach(item => {
            const tr = document.createElement('tr');
            const total = (item.quantity * item.unit_price).toFixed(2);
            tr.className = 'border-bottom transition-all';
            tr.innerHTML = `
                <td class="py-3 px-3 fw-medium text-dark">${item.description}</td>
                <td class="py-3 px-3 text-center"><span class="badge bg-secondary rounded-pill shadow-sm px-2 py-1">${item.quantity}</span></td>
                <td class="py-3 px-3 text-end text-muted">$${item.unit_price.toFixed(2)}</td>
                <td class="py-3 px-3 text-end fw-bold text-dark">$${total}</td>
            `;
            tbody.appendChild(tr);
        });

        document.getElementById('resExtractedTotal').textContent = `$${data.extracted_total.toFixed(2)}`;
        document.getElementById('resCalculatedTotal').textContent = `$${data.calculated_total.toFixed(2)}`;

        const calcTotalRow = document.getElementById('calcTotalRow');
        if (data.status === 'correct') {
            calcTotalRow.className = 'table-success text-success transition-all';
        } else {
            calcTotalRow.className = 'table-danger text-danger transition-all';
        }
    } else {
        document.getElementById('resultCard').classList.add('d-none');
        document.getElementById('jsonFallback').classList.remove('d-none');
        jsonOutput.innerText = JSON.stringify(data, null, 2);
    }
}
