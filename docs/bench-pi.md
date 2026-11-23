# Bench Raspberry Pi: setup guide

This guide covers everything the nilwerk bench needs: a fresh Raspberry Pi 3B+, the ESP32-C3 board, the Nexus 6P phone, and a GitHub Actions self-hosted runner that passes the CI steps.

Commands run on the Pi as user `pi` unless marked otherwise. Never put secrets, provisioning values, or tokens in this file, in commits, or in chat.

---

## 0. Hardware

- **Pi:** Raspberry Pi 3B+ with the official 5 V 3 A power supply. Undervoltage caused USB drops earlier. Check with `vcgencmd get_throttled` (should be `0x0`).
- **Board:** ESP32-C3 SuperMini with a **10 kΩ pull-up from GPIO9 to 3V3**. Without it the chip boots into ROM download mode (`boot:0x5`), and the app never runs.
- **Phone:** Nexus 6P, Android 8.1 (SDK 27), USB debugging on.
- **Cables:** Data cables only, kept short.
- **USB:** Plug the board straight into a Pi port (or a powered hub). Don't share the port with the phone.

## 1. OS and base access

1. Flash **Raspberry Pi OS 64-bit (Trixie)**. A 32-bit OS is rejected by GitHub's runner.
2. Create user `pi`, enable SSH, set the hostname.
3. Passwordless sudo for `pi`:
   ```bash
   echo 'pi ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/pi
   sudo chmod 0440 /etc/sudoers.d/pi
   ```
4. Tailscale for remote access:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```
5. SSH key from the admin machine: `ssh-copy-id pi@<tailscale-ip>`. On macOS, load the key once with `ssh-add --apple-use-keychain ~/.ssh/id_ed25519`.

## 2. Packages

```bash
sudo apt-get update
sudo apt-get install -y adb jq bluez usbutils util-linux curl unzip python3 python3-venv \
  openjdk-17-jdk-headless gh android-sdk-platform-tools
```

- `adb` and `android-sdk-platform-tools`: phone access. Check that `/usr/lib/android-sdk/platform-tools` exists.
- `bluez` (provides `hcitool`): Bluetooth scanning.
- `util-linux` (provides `flock`): one BLE scan at a time.
- `jq`: JSON parsing in the scripts.
- `gh`: artifact download in step 2. Sign in only if you use it by hand (`gh auth login`).

**Node 20** (the runner expects major version 20):

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
node -v   # must print v20.x
```

## 3. Bluetooth for the runner

```bash
sudo systemctl enable --now bluetooth
sudo setcap cap_net_raw,cap_net_admin+eip /usr/bin/hcitool

# Let the runner restart Bluetooth, and nothing else:
echo 'ghrunner ALL=(root) NOPASSWD: /usr/bin/systemctl restart bluetooth' | sudo tee /etc/sudoers.d/ghrunner-bluetooth
sudo chmod 0440 /etc/sudoers.d/ghrunner-bluetooth
sudo visudo -c
```

Check: `sudo -u ghrunner timeout 8 hcitool lescan --duplicates` prints device lines, not `Set scan parameters failed`.

**Do not run `bluetoothctl scan` on the bench.** It can leave the adapter stuck.

## 4. The runner user and its tools

1. Create the runner user and give it the groups it needs:
   ```bash
   sudo useradd -m -s /bin/bash ghrunner
   sudo usermod -aG plugdev,dialout ghrunner
   ```
2. **ESP tools (esptool and NVS):**
   ```bash
   sudo -u ghrunner python3 -m venv /home/ghrunner/esptool-venv
   sudo -u ghrunner /home/ghrunner/esptool-venv/bin/pip install esptool==5.6.0
   sudo -u ghrunner python3 -m venv /home/ghrunner/nvs-venv
   sudo -u ghrunner /home/ghrunner/nvs-venv/bin/pip install esp-idf-nvs-partition-gen==0.3.0
   sudo ln -sf /home/ghrunner/esptool-venv/bin/esptool /usr/local/bin/esptool
   ```
3. **Appium 2.19.0 and the UiAutomator2 driver 3.8.0:**
   ```bash
   sudo npm install -g appium@2.19.0
   sudo -u ghrunner env HOME=/home/ghrunner APPIUM_HOME=/home/ghrunner/.appium \
     bash -c "cd /home/ghrunner && appium driver install uiautomator2@3.8.0"
   ```
   Run the driver install from `/home/ghrunner`. Running it from `pi`'s folder fails with `EACCES`. Don't install the newest driver: it needs a newer Appium than 2.19.
4. **Appium service:** create `/etc/systemd/system/appium.service`:
   ```ini
   [Unit]
   Description=Appium 2 server for the nilwerk bench (UiAutomator2)
   After=network-online.target
   Wants=network-online.target

   [Service]
   User=ghrunner
   Group=ghrunner
   WorkingDirectory=/home/ghrunner
   Environment=HOME=/home/ghrunner
   Environment=APPIUM_HOME=/home/ghrunner/.appium
   Environment=PATH=/usr/local/bin:/usr/bin:/bin
   Environment=ANDROID_HOME=/usr/lib/android-sdk
   Environment=ANDROID_SDK_ROOT=/usr/lib/android-sdk
   ExecStart=/usr/local/bin/appium --address 127.0.0.1 --port 4723 --log-level warn
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```
   Then:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now appium
   curl -s http://127.0.0.1:4723/status    # "ready": true
   ```
   Without `ANDROID_HOME`, the session fails with "Neither ANDROID_HOME nor ANDROID_SDK_ROOT environment variable was exported".

5. `/home/ghrunner` is `0700`, so `pi` can't read it. Use `sudo -u ghrunner` or `sudo` for anything inside it.

## 5. The GitHub Actions runner

1. In GitHub: **Settings → Actions → Runners → New self-hosted runner** (Linux, ARM64). Copy the registration token.
2. As `ghrunner`, in `/home/ghrunner/actions-runner`, run the configure script with name `plant-bench-pi` and labels `bench` (and `plant-bench-pi`). Use the token from step 1.
3. Install and start it as a service:
   ```bash
   cd /home/ghrunner/actions-runner
   sudo ./svc.sh install ghrunner
   sudo ./svc.sh start
   ```
4. Check it's enabled: `systemctl is-enabled actions.runner.nilwerk-nilwerk-lab.plant-bench-pi.service`.

## 6. Board and phone

**Board**
1. Plug in the board, then find its USB serial and hw_id:
   ```bash
   lsusb | grep 303a
   sudo dmesg | grep -i espressif
   ```
   Example: serial `C8:DA:29:86:F4:70` → hw_id `nw-c8da2986f470`.
2. Provisioning files go in `/var/lib/nilwerk-provision`, owned by `ghrunner`:
   ```bash
   sudo mkdir -p /var/lib/nilwerk-provision
   sudo chown ghrunner:ghrunner /var/lib/nilwerk-provision
   sudo chmod 0700 /var/lib/nilwerk-provision
   # copy <hw_id>.nvs.csv and <hw_id>.label.txt here (the owner provides them; never commit them)
   sudo chown ghrunner:ghrunner /var/lib/nilwerk-provision/*
   sudo chmod 0600 /var/lib/nilwerk-provision/*
   ```
3. Check the board's serial before you flash or provision it.

**Phone**
1. On the Nexus 6P, enable USB debugging. Then, as the runner:
   ```bash
   sudo -u ghrunner adb devices
   ```
   Accept the RSA prompt on the phone. The phone must show `device`, not `unauthorized`.
2. If it stays `unauthorized`: `sudo rm -rf /home/ghrunner/.android` and retry the prompt.
3. Check the Android version: `sudo -u ghrunner adb -s <serial> shell getprop ro.build.version.sdk` returns `27`.

## 7. GitHub repository settings

**Variables** (Settings → Secrets and variables → Actions → Variables):
- `BENCH_BOARD_HW_ID` = the board's hw_id (for example `nw-c8da2986f470`)
- `BENCH_PROVISION_DIR` = `/var/lib/nilwerk-provision`

**Secrets** (Settings → Secrets and variables → Actions → Secrets). The owner provides the values:
- `BENCH_ANDROID_SERIAL`: the phone's serial
- `BENCH_TEST_EMAIL`, `BENCH_TEST_EMAIL_PASSWORD`: the test account
- `BENCH_BOARD_POP`: the board's setup code
- `BENCH_WIFI_SSID`, `BENCH_WIFI_PASSWORD`: Wi-Fi for the board
- `BENCH_CLOUD_CHECK_CONFIG`: JSON `{"url": "https://<project-ref>.supabase.co", "secret_key": "<secret key>"}`

## 8. Health check before the first run

Each line should pass:

```bash
vcgencmd get_throttled                                   # 0x0
node -v                                                  # v20.x
java -version 2>&1 | head -n 1                           # openjdk 17
command -v esptool jq adb flock hcitool appium           # all found
sudo -u ghrunner /home/ghrunner/esptool-venv/bin/esptool version
sudo -u ghrunner adb devices                             # phone shows "device"
curl -s http://127.0.0.1:4723/status                     # "ready": true
sudo -u ghrunner timeout 8 hcitool lescan --duplicates | head -n 3
systemctl is-active bluetooth appium actions.runner.nilwerk-nilwerk-lab.plant-bench-pi.service
```

## 9. Run the bench

Start **Bench (self-hosted)** from GitHub Actions on the branch you're testing. The steps run in order:

1. Download the firmware and APK from this run
2. Check the APK (zip integrity and size)
3. a. Flash the firmware
4. 3. Provision the board (NVS last)
5. c. BLE scan
6. b. Serial stream check
7. 4. Install the APK on the phone
8. d. App launch and Appium session
9. e. Cloud check
10. Bench E2E

## 10. Pitfalls we hit

- **Stuck Bluetooth:** Two scans at once, or a stray `bluetoothctl`, freeze the adapter. Fix: `sudo systemctl restart bluetooth`. CI does this on its own now.
- **Download mode:** A reset over RTS/DTR, or opening the serial port, can put the board into download mode. In the boot log, `boot:0x5` means download mode; `boot:0xd` or `0xf` means a normal boot.
- **Damaged APK:** A truncated file fails with "Failed to parse AndroidManifest.xml". Check with `unzip -tq` and the size (the release APK is about 73 MB). `actions/download-artifact` truncated it on this runner; step 2 now uses `gh run download`.
- **Dev-client APK:** A debug build opens Expo's Dev Launcher, not the app. Bench builds must be the release variant with the JS bundle (on `main`).
- **Activity name:** Appium needs `appium:appActivity` (`.MainActivity`), or the session fails with "Intent does not match any activities".
- **Killing processes:** Don't use `pkill -f ttyACM0`; it matches your own shell. Kill by PID.
- **Serial readers:** Stop any reader on `/dev/ttyACM0` before you flash, or the flash fails with "Serial data stream stopped".
- **Missing secrets:** Steps d and e stop with "not configured". That's intended until the secrets are set.

## 11. Open for the team

- Step d only checks that the app launches. It doesn't log in, pair the board, send Wi-Fi details, or set up sensors. The app team owns that flow.
- The E2E step runs a mock web test. The owner has to decide whether that's the bench E2E.
- The Node 20 warnings come from GitHub running newer action versions on Node 24. They're warnings only.
