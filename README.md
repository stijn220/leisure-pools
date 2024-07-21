# leisure pools
 
![GitHub release (latest by date)](https://img.shields.io/github/v/release/stijn220/leisure-pools?style=flat-square) [![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

The Leisure Pools integration allows you to control your Leisure Pools system directly from Home Assistant.

## Features
- Control pool lights (turn on and off)

## Installation

### HACS (Home Assistant Community Store)

1. **Add Integration via HACS**:
   - Go to the HACS section in Home Assistant.
   - Go to the `Integrations` page and search for "Leisure Pools".
   - Press the `Download` button to install the integration.

2. **Configure Integration**:
   - After downloading, go to `Settings` -> `Devices & Services` in Home Assistant.
   - Press the `+ Add Integration` button.
   - Search for "Leisure Pools" and follow the config dialog to add your device.

### Manual Installation

1. **Copy Files**:
   - Download and copy the `leisure_pools` folder into your Home Assistant's `custom_components` directory.

2. **Restart Home Assistant**:
   - Restart Home Assistant to load the new integration.

3. **Add Integration**:
   - Go to `Settings` -> `Devices & Services` in Home Assistant.
   - Press the `+ Add Integration` button.
   - Search for "Leisure Pools" and follow the config dialog to add your device.

## Configuration

During setup, you will need to provide the following information:

- **API URL**: The IP address or URL of your Leisure Pools system (e.g., `http://192.168.178.252`).
- **Username**: Your Leisure Pools system username.
- **Password**: Your Leisure Pools system password.