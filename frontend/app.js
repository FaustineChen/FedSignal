// /api/reports/matches

const matchesButton = document.getElementById("search-matches");
const summaryButton  = document.getElementById("view-summary");
const uploadForm = document.getElementById("upload-form");

function buildCommonParams() {
    const params = new URLSearchParams();

    const keyword = document.getElementById("keyword").value;
    const category = document.getElementById("category").value;
    const documentType = document.getElementById("document-type").value;
    const documentId = document.getElementById("document-id").value;
    const startDate = document.getElementById("start-date").value;
    const endDate = document.getElementById("end-date").value;
    const dateField = document.getElementById("date-field").value;
    const limit = document.getElementById("limit").value;

    if (keyword) params.append("keyword", keyword);
    if (category) params.append("category", category);
    if (documentType) params.append("document_type", documentType);
    if (documentId) params.append("document_id", documentId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (dateField) params.append("date_field", dateField);
    if (limit) params.append("limit", limit);

    return params;
}

async function uploadDocument(formData) {
    const response = await fetch ("/api/documents", {
       method: "POST",
       body: formData
    });

    const data = await response.json();

    return data;
};

async function fetchMatches(){
    const params = buildCommonParams();
    
    const response = await fetch(
        `/api/reports/matches?${params.toString()}`
    );

    // Converts the raw stream into a JS object
    const data = await response.json();

    return data;
};

async function fetchSummary() {
    const params = buildCommonParams();

    // only for summary
    const summaryBy = document.getElementById("summary-by").value;

    if (summaryBy) {
        params.append("summary_by", summaryBy);
    }

    const response = await fetch(
        `/api/reports/summary?${params.toString()}`
    );

    const data = await response.json();

    return data;
}

function renderUploadResult(data) {
    console.log(data);
    
    const results = document.getElementById("upload-result");

    results.textContent = `Document ${data.document_id} uploaded. Job ${data.job_id}: ${data.job_status}`;
}

function renderMatches(data){
    console.log(data);
    
    const results = document.getElementById("results");
    results.innerHTML = "";

    if (data.length === 0) {
        results.textContent = "No matches found.";
        return;
    }

    const keywordInput = document.getElementById("keyword").value;
    const categoryInput = document.getElementById("category").value;

    const summary = document.createElement("p");

    let summaryText = "";

    if (keywordInput) {
        summaryText += `Keyword: ${keywordInput}`;

        // category comes from API result
        if (data[0].category) {
            summaryText += ` | Category: ${data[0].category}`;
        }
    } else if (categoryInput) {
        summaryText += `Category: ${categoryInput}`;
    }

    summaryText += ` | ${data.length} matches`;

    summary.textContent = summaryText;
    results.appendChild(summary);


    const table = document.createElement("table");

    // header
    const headerRow = document.createElement("tr");

    const headers = ["Date", "Document Type", "Title", "Match"];

    for (const header of headers) {
        const th = document.createElement("th");
        th.textContent = header;
        headerRow.appendChild(th);
    }

    table.appendChild(headerRow);

    // data rows
    for (const row of data){
        const tr = document.createElement("tr");

        const values = [
            row.published_date,
            row.document_type,
            row.title,
            row.sentence
        ];

        for (const value of values) {
            const td = document.createElement("td");
            td.textContent = value;
            tr.appendChild(td);
        }

        table.appendChild(tr);
    }

    results.appendChild(table);
};

function renderSummary(data) {
    console.log(data);

    const results = document.getElementById("results");
    results.innerHTML = "";

    const summaryBy = document.getElementById("summary-by").value;

    const table = document.createElement("table");

    // Decide which columns to display
    let columns;

    if (summaryBy === "document") {
        columns = [
            ["Document ID", "document_id"],
            ["Title", "title"],
            ["Published Date", "published_date"],
            ["Count", "occurrence_count"]
        ];
    } else if (summaryBy === "date") {
        columns = [
            ["Date", "report_date"],
            ["Count", "occurrence_count"]
        ];
    } else if (summaryBy === "document_type") {
        columns = [
            ["Document Type", "document_type"],
            ["Count", "occurrence_count"]
        ];
    } else if (summaryBy === "keyword") {
        columns = [
            ["Keyword", "keyword"],
            ["Count", "occurrence_count"]
        ];
    }

    // Create header
    const headerRow = document.createElement("tr");

    for (const [label, key] of columns) {
        const th = document.createElement("th");
        th.textContent = label;
        headerRow.appendChild(th);
    }

    table.appendChild(headerRow);

    // Create data rows
    for (const row of data) {
        const tr = document.createElement("tr");

        for (const [label, key] of columns) {
            const td = document.createElement("td");
            td.textContent = row[key];
            tr.appendChild(td);
        }

        table.appendChild(tr);
    }

    results.appendChild(table);
}

uploadForm.addEventListener("submit", async(event) => {
    event.preventDefault();
    console.log("upload submitted");

    // FormData
    const formData = new FormData(uploadForm);

    // for (const [key, value] of formData.entries()) {
    //     console.log(key, value);
    // }

    const data = await uploadDocument(formData);

    renderUploadResult(data);
});

matchesButton.addEventListener("click", async () => {
    const data = await fetchMatches();
    renderMatches(data);    
});

summaryButton.addEventListener("click", async () => {
    const data = await fetchSummary();
    renderSummary(data);
});

