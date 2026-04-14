chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "commonplace-download") {
    return;
  }

  const blob = new Blob([message.markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  chrome.downloads.download(
    {
      url,
      filename: `${message.filename}.md`,
      saveAs: true,
    },
    () => {
      const runtimeError = chrome.runtime.lastError;
      if (runtimeError) {
        sendResponse({ ok: false, error: runtimeError.message });
      } else {
        sendResponse({ ok: true });
      }
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
  );

  return true;
});
