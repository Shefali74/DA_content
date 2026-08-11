# VPN Access and Troubleshooting Guide

## Overview
All employees must use the corporate VPN when working remotely or accessing internal systems from outside the office network.

## Setting Up VPN for the First Time
1. Download the GlobalProtect VPN client from the IT Portal at https://itportal.internal/vpn
2. Install the application on your device
3. Launch GlobalProtect and enter the gateway address: vpn.company.internal
4. Authenticate using your corporate credentials (same as email login)
5. Complete the MFA challenge via your authenticator app

## Troubleshooting VPN Connection Issues

### VPN Not Connecting After Windows Update
This is a known issue with Windows Feature Updates. Follow these steps:
1. Open Device Manager and check if the TAP network adapter is present
2. If missing, reinstall the GlobalProtect client
3. Ensure Windows Firewall is not blocking GlobalProtect (check Inbound Rules)
4. Restart the PanGPS service: Open Services > Pan GlobalProtect Service > Restart
5. If issue persists, reset network adapter: `netsh winsock reset` in admin Command Prompt
6. Reboot and try connecting again

### VPN Password Reset
1. Go to https://itportal.internal/vpn/reset
2. Enter your Employee ID
3. Verify via the email OTP sent to your registered email
4. Set new password (minimum 12 characters, must include uppercase, number, and special character)
5. New password takes 15 minutes to propagate across all systems

### Split Tunnel vs Full Tunnel
- Default configuration: Split tunnel (only corporate traffic goes through VPN)
- Full tunnel available for security-sensitive roles (request via IT ticket)
- To check your tunnel mode: GlobalProtect > Settings > Connection tab

## Contact
For urgent VPN issues outside business hours, contact the 24/7 IT Helpdesk at ext. 4357 or helpdesk@company.internal
