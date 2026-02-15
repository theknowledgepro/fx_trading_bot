## Email Alert Setup (Required for Gmail)

To enable email alerts, you must generate a **Gmail App Password**.
Your regular Gmail password will **not** work for SMTP authentication.

### Step-by-Step Instructions

1. Sign in to your Google account.
2. Go to **Manage your Google Account**.
3. Open the **Security** tab.
4. Enable **2-Step Verification** (required).
5. After enabling 2-Step Verification, return to the **Security** page.
6. Click **App passwords**.
7. Generate a new app password with:

   * **App:** Mail
   * **Device:** Windows Computer (or your device type)
8. Google will generate a **16-character password**.

Example:

```
abcd efgh ijkl mnop
```

Remove the spaces when using it in your configuration:

```
abcdefghijklmnop
```

---

### Where to Use It

Enter the generated password when prompted as you run the credentials.py file

⚠️ Do **not** use your regular Gmail password.
⚠️ Do **not** share your app password publicly.

---

If 2-Step Verification is not enabled, the “App passwords” option will not appear.
