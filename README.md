# Leisure Pools Integration

![GitHub release (latest by date)](https://img.shields.io/github/v/release/stijn220/leisure-pools?style=flat-square) [![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

The **Leisure Pools** integration allows you to control your **Leisure Pools** system directly from **Home Assistant**.

## 🚀 Features
- ✅ Control pool lights (turn on and off)
- ✅ Open and close the pool cover

## 📥 Installation

### 🔹 HACS (Home Assistant Community Store)

1. **Add Integration via HACS:**
   - Open **HACS** in Home Assistant.
   - Navigate to the `Integrations` section and search for **"Leisure Pools"**.
   - Click `Download` to install the integration.

2. **Configure the Integration:**
   - After downloading, go to **Settings** → **Devices & Services**.
   - Click `+ Add Integration`.
   - Search for **"Leisure Pools"** and follow the setup instructions.

### 🔹 Manual Installation

1. **Copy Files:**
   - Download the integration and copy the `leisure_pools` folder to:
     ```
     custom_components/leisure_pools
     ```

2. **Restart Home Assistant:**
   - Restart Home Assistant to apply changes.

3. **Add Integration:**
   - Go to **Settings** → **Devices & Services**.
   - Click `+ Add Integration`.
   - Search for **"Leisure Pools"** and follow the setup instructions.

## ⚙️ Configuration

During setup, you will need to provide:

- **API URL:** The IP address or URL of your **Leisure Pools** system (e.g., `http://192.168.178.252`).
- **Username:** Your **Leisure Pools** system username *(default: `admin`)*.
- **Password:** Your **Leisure Pools** system password *(default: `admin`)*.

## 🛠️ Known Issues

- ❌ **Cover state is unknown**
- ❌ **Light state is unknown**
- ❌ **Cover stop button does not work**
