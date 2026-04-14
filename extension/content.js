const DEFAULT_ENDPOINT = "https://api.commonplace.so/extract";
const ROOT_ID = "commonplace-root";

function normalizeWhitespace(text) {
  return text.replace(/\s+/g, " ").trim();
}

function slugify(value) {
  return (value || "commonplace-session")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "commonplace-session";
}

function looksLikeConversationPage() {
  const href = window.location.href;
  if (window.location.hostname === "claude.ai") {
    return href.includes("/chat/") || href.includes("/share/");
  }
  if (window.location.hostname === "chatgpt.com") {
    return href.includes("/c/") || href.includes("/g/");
  }
  return false;
}

function getExtensionSettings() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(
      {
        commonplaceApiEndpoint: DEFAULT_ENDPOINT,
        commonplaceApiKey: "",
      },
      resolve
    );
  });
}

function findAnchorElement() {
  const textarea = document.querySelector("textarea");
  if (textarea) {
    return textarea.closest("form") || textarea.parentElement;
  }

  const textbox = document.querySelector('[contenteditable="true"], [role="textbox"]');
  if (textbox) {
    return textbox.closest("form") || textbox.parentElement;
  }

  return null;
}

function getVisibleText(element) {
  if (!(element instanceof HTMLElement)) {
    return "";
  }
  return normalizeWhitespace(element.innerText || element.textContent || "");
}

function scrapeChatGPTConversation() {
  const roleNodes = Array.from(document.querySelectorAll("[data-message-author-role]"));
  if (roleNodes.length) {
    return roleNodes
      .map((node) => {
        const role = node.getAttribute("data-message-author-role") === "user" ? "User" : "Assistant";
        const text = getVisibleText(node);
        return text ? `${role}: ${text}` : "";
      })
      .filter(Boolean)
      .join("\n\n");
  }

  const articles = Array.from(document.querySelectorAll("article"));
  return articles
    .map((article) => {
      const text = getVisibleText(article);
      if (!text) {
        return "";
      }
      const label = /you said|you/i.test(text.slice(0, 80)) ? "User" : "Assistant";
      return `${label}: ${text}`;
    })
    .filter(Boolean)
    .join("\n\n");
}

function scrapeClaudeConversation() {
  const messageNodes = Array.from(
    document.querySelectorAll(
      '[data-testid*="message"], [data-testid*="turn"], [data-testid*="assistant"], [data-testid*="user"]'
    )
  );

  if (messageNodes.length) {
    return messageNodes
      .map((node) => {
        const testId = (node.getAttribute("data-testid") || "").toLowerCase();
        const role =
          testId.includes("user") || testId.includes("human")
            ? "User"
            : testId.includes("assistant") || testId.includes("claude")
              ? "Assistant"
              : "";
        const text = getVisibleText(node);
        return role && text ? `${role}: ${text}` : "";
      })
      .filter(Boolean)
      .join("\n\n");
  }

  const articles = Array.from(document.querySelectorAll("article, main section"));
  return articles
    .map((node) => {
      const text = getVisibleText(node);
      if (!text) {
        return "";
      }
      const head = text.slice(0, 120);
      const role = /^(you|human)\b/i.test(head) ? "User" : /^(claude|assistant)\b/i.test(head) ? "Assistant" : "";
      return role ? `${role}: ${text}` : "";
    })
    .filter(Boolean)
    .join("\n\n");
}

function scrapeConversation() {
  if (window.location.hostname === "claude.ai") {
    return scrapeClaudeConversation();
  }
  if (window.location.hostname === "chatgpt.com") {
    return scrapeChatGPTConversation();
  }
  return "";
}

function showToast(message, tone = "default") {
  const toast = document.createElement("div");
  toast.className = "commonplace-toast";
  toast.dataset.tone = tone;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

function createModal(onSubmit) {
  const overlay = document.createElement("div");
  overlay.className = "commonplace-overlay";
  overlay.innerHTML = `
    <div class="commonplace-modal" role="dialog" aria-modal="true" aria-labelledby="commonplace-modal-title">
      <h2 id="commonplace-modal-title">Save to Commonplace</h2>
      <p>Choose how this conversation should be filed before it is sent to your Commonplace API.</p>
      <div class="commonplace-field">
        <label for="commonplace-session-type">Session type</label>
        <select id="commonplace-session-type">
          <option value="strategy">strategy</option>
          <option value="research">research</option>
        </select>
      </div>
      <div class="commonplace-field">
        <label for="commonplace-title">Optional title</label>
        <input id="commonplace-title" type="text" placeholder="Leave blank to let Commonplace title it" />
      </div>
      <div class="commonplace-actions">
        <button type="button" class="commonplace-secondary" id="commonplace-cancel">Cancel</button>
        <button type="button" class="commonplace-primary" id="commonplace-submit">Save</button>
      </div>
    </div>
  `;

  overlay.querySelector("#commonplace-cancel").addEventListener("click", () => overlay.remove());
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) {
      overlay.remove();
    }
  });
  overlay.querySelector("#commonplace-submit").addEventListener("click", async () => {
    const submitButton = overlay.querySelector("#commonplace-submit");
    submitButton.disabled = true;
    submitButton.textContent = "Saving...";
    const sessionType = overlay.querySelector("#commonplace-session-type").value;
    const title = overlay.querySelector("#commonplace-title").value.trim();
    try {
      await onSubmit({ sessionType, title });
      overlay.remove();
    } catch (error) {
      submitButton.disabled = false;
      submitButton.textContent = "Save";
      showToast(error.message || "Could not save this conversation.", "error");
    }
  });
  document.body.appendChild(overlay);
}

async function downloadMarkdown(markdown, title) {
  const filename = `${new Date().toISOString().slice(0, 10)}-${slugify(title)}`;
  const response = await chrome.runtime.sendMessage({
    type: "commonplace-download",
    markdown,
    filename,
  });
  if (!response?.ok) {
    throw new Error(response?.error || "Download failed.");
  }
}

async function handleSave(button) {
  const settings = await getExtensionSettings();
  if (!settings.commonplaceApiKey) {
    showToast("Set your Commonplace API key in the extension options first.", "error");
    chrome.runtime.openOptionsPage();
    return;
  }

  createModal(async ({ sessionType, title }) => {
    button.disabled = true;
    button.textContent = "Saving to Commonplace...";
    const transcript = scrapeConversation();
    if (!transcript) {
      button.disabled = false;
      button.textContent = "Save to Commonplace";
      throw new Error("Could not find conversation text on this page.");
    }

    const response = await fetch(settings.commonplaceApiEndpoint || DEFAULT_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": settings.commonplaceApiKey,
      },
      body: JSON.stringify({
        transcript,
        session_type: sessionType,
        title,
      }),
    });

    let payload;
    try {
      payload = await response.json();
    } catch (_error) {
      payload = null;
    }

    if (!response.ok) {
      button.disabled = false;
      button.textContent = "Save to Commonplace";
      throw new Error(payload?.detail || "Commonplace API request failed.");
    }

    await downloadMarkdown(payload.markdown, payload.title || title || "commonplace-session");
    button.disabled = false;
    button.textContent = "Save to Commonplace";
    showToast("Saved markdown wiki page.", "success");
  });
}

function ensureButton() {
  if (!looksLikeConversationPage()) {
    return;
  }

  let root = document.getElementById(ROOT_ID);
  if (!root) {
    root = document.createElement("div");
    root.id = ROOT_ID;
  }

  let button = root.querySelector(".commonplace-launcher");
  if (!button) {
    const wrapper = document.createElement("div");
    wrapper.className = "commonplace-anchor";
    button = document.createElement("button");
    button.type = "button";
    button.className = "commonplace-launcher";
    button.textContent = "Save to Commonplace";
    button.addEventListener("click", () => handleSave(button));
    wrapper.appendChild(button);
    root.appendChild(wrapper);
  }

  const anchor = findAnchorElement();
  if (anchor) {
    root.classList.remove("commonplace-fixed");
    anchor.parentElement?.insertBefore(root, anchor.nextSibling);
  } else if (!document.body.contains(root)) {
    root.classList.add("commonplace-fixed");
    document.body.appendChild(root);
  }
}

ensureButton();
new MutationObserver(() => ensureButton()).observe(document.body, {
  childList: true,
  subtree: true,
});
