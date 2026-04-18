const DEFAULT_ENDPOINT = "http://localhost:8000/extract";

function setStatus(message, isError = false) {
  const status = document.getElementById("status");
  status.textContent = message;
  status.style.color = isError ? "#b91c1c" : "#166534";
}

function loadSettings() {
  chrome.storage.sync.get(
    {
      commonplaceApiEndpoint: DEFAULT_ENDPOINT,
      commonplaceApiKey: "",
    },
    (items) => {
      document.getElementById("api-endpoint").value = items.commonplaceApiEndpoint || DEFAULT_ENDPOINT;
      document.getElementById("api-key").value = items.commonplaceApiKey || "";
    }
  );
}

document.getElementById("save-settings").addEventListener("click", () => {
  const endpoint = document.getElementById("api-endpoint").value.trim() || DEFAULT_ENDPOINT;
  const apiKey = document.getElementById("api-key").value.trim();

  if (!apiKey) {
    setStatus("API key is required.", true);
    return;
  }

  chrome.storage.sync.set(
    {
      commonplaceApiEndpoint: endpoint,
      commonplaceApiKey: apiKey,
    },
    () => {
      setStatus("Settings saved.");
    }
  );
});

loadSettings();
