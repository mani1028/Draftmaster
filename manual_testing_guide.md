# Manual Testing Guide

This document provides step-by-step instructions for manually testing the application.

## 1. Prerequisites
- Ensure Python and all dependencies in requirements.txt are installed.
- Start the application (usually: `python app.py`).
- Open a web browser and navigate to the application URL (e.g., http://localhost:5000).

## 2. Login Page
- Open the login page.
- Enter valid credentials and verify successful login.
- Enter invalid credentials and verify error message is shown.

## 3. Dashboard
- After login, verify dashboard loads correctly.
- Check that all expected data and UI elements are present.

## 4. Data Export
- Use the export feature (if available) and verify the exported file is correct.

## 5. Error Handling
- Try to access restricted pages without logging in and verify redirection to login.
- Enter invalid data in forms and verify error messages.

## 6. UI Testing
- Check that all buttons, links, and forms work as expected.
- Verify responsiveness and layout in different browsers/devices.

## 7. Logout
- Click logout and verify user is redirected to login page.

---
Add more test cases as needed based on new features or bug fixes.
