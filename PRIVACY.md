# Linkyard Privacy Policy

*Last updated: 2026-05-20*

## Overview

Linkyard is a self-hosted browser extension. You run the backend on your own server or computer. Google receives no data; the developer (Aryan Mittal) receives no data.

## Data collected by the extension

The extension reads the URL and page title of the active tab when you click **Save**. This information is sent exclusively to the backend URL you configure in the extension's Settings page (default: `http://localhost:8000`).

No data is sent to any third-party service, analytics platform, or the extension developer.

## Data stored locally

The extension stores your configured backend URL in `chrome.storage.sync`. This value is synced across your Chrome profile by Google's standard sync mechanism and is not accessible to the extension developer.

## Data handled by your backend

Because Linkyard is self-hosted, you control all stored bookmarks and embeddings. Refer to your own server's configuration for retention and security policies.

## Permissions

| Permission | Why it's needed |
|---|---|
| `activeTab` | Read the URL and title of the tab you choose to save — only when you click the extension icon. |
| `storage` | Persist your configured backend URL across browser sessions. |
| Host permission for your backend URL | Send the save request to the backend you configure. Requested on demand when you set a non-localhost URL. |

## Contact

For questions, open an issue at the project repository or email mittalaryan99@gmail.com.
