# 🚀 How to Deploy the Cyclistic Power BI Solution on GitHub

This guide explains how to deploy the **Cyclistic Power BI Solution** so it is **publicly accessible from anywhere** (on mobile phones, laptops, executive presentations, or portfolio sites) with **zero software installation required**.

---

## 🌐 Method 1: Deploy Live Web Dashboard via GitHub Pages (Recommended)

We have already configured your repository with a `docs/` folder and an automated GitHub Actions workflow (`.github/workflows/deploy-pages.yml`).

### Step 1: Commit and Push the Files to GitHub
You can push either using **GitHub Desktop** (installed on your system) or via PowerShell:

#### Option A: Using PowerShell (1-Click Command)
Run the following command in PowerShell:
```powershell
& "C:\Users\tamim\AppData\Local\GitHubDesktop\app-3.6.6\resources\app\git\cmd\git.exe" add .
& "C:\Users\tamim\AppData\Local\GitHubDesktop\app-3.6.6\resources\app\git\cmd\git.exe" commit -m "Deploy Enterprise Power BI Solution with live interactive dashboard"
& "C:\Users\tamim\AppData\Local\GitHubDesktop\app-3.6.6\resources\app\git\cmd\git.exe" push origin main
```

#### Option B: Using GitHub Desktop App
1. Open **GitHub Desktop**.
2. You will see all the new files in the left sidebar (`docs/`, `powerbi/`, `.github/`).
3. In the bottom-left summary box, enter: `Deploy Enterprise Power BI Solution`.
4. Click **Commit to main**.
5. Click **Push origin** in the top bar.

---

### Step 2: Enable GitHub Pages in Your Repository Settings
1. Go to your repository on GitHub:
   👉 **`https://github.com/tamim-shadman/cyclistic_data_analysis`**
2. Click on the **⚙️ Settings** tab at the top.
3. In the left sidebar, click **Pages** (under the "Code and automation" section).
4. Under **Build and deployment**:
   - **Source**: Select **Deploy from a branch**.
   - **Branch**: Select `main`.
   - **Folder**: Select `/docs`.
   - Click **Save**.
   *(Alternatively, under Source you can select **GitHub Actions**, and our included workflow will deploy it automatically!)*
5. Wait ~60 seconds. A green banner will appear saying:
   > **"Your site is live at https://tamim-shadman.github.io/cyclistic_data_analysis/"**

Anyone with this URL can now access the full 6-page interactive Power BI dashboard from anywhere in the world!

---

## 📁 Method 2: Deploy to a Separate Dedicated GitHub Repository

If you want a **standalone repository** containing *only* the Power BI assets (without the Python scripts):

1. Go to [github.com/new](https://github.com/new) and create a new public repository (e.g., `cyclistic-powerbi-analytics`).
2. Open PowerShell in a new temporary folder:
   ```powershell
   mkdir C:\Users\tamim\Desktop\cyclistic-powerbi
   cd C:\Users\tamim\Desktop\cyclistic-powerbi
   
   # Copy all files from the powerbi folder and the interactive preview to the root:
   Copy-Item "H:\Projects\cyclistic_data_analysis\powerbi\*" . -Recurse
   Copy-Item "H:\Projects\cyclistic_data_analysis\powerbi\interactive_preview\*" . -Recurse
   
   # Initialize and push to your new repo:
   & "C:\Users\tamim\AppData\Local\GitHubDesktop\app-3.6.6\resources\app\git\cmd\git.exe" init
   & "C:\Users\tamim\AppData\Local\GitHubDesktop\app-3.6.6\resources\app\git\cmd\git.exe" add .
   & "C:\Users\tamim\AppData\Local\GitHubDesktop\app-3.6.6\resources\app\git\cmd\git.exe" commit -m "Initial commit of Cyclistic Power BI Analytics"
   & "C:\Users\tamim\AppData\Local\GitHubDesktop\app-3.6.6\resources\app\git\cmd\git.exe" branch -M main
   & "C:\Users\tamim\AppData\Local\GitHubDesktop\app-3.6.6\resources\app\git\cmd\git.exe" remote add origin https://github.com/tamim-shadman/cyclistic-powerbi-analytics.git
   & "C:\Users\tamim\AppData\Local\GitHubDesktop\app-3.6.6\resources\app\git\cmd\git.exe" push -u origin main
   ```
3. In that new repo's **Settings > Pages**, choose **Deploy from a branch** > `main` > `/(root)`.
4. Your site will be live at:
   `https://tamim-shadman.github.io/cyclistic-powerbi-analytics/`

---

## 📊 Method 3: Official Microsoft Power BI Service ("Publish to Web")

If you build the dashboard in Power BI Desktop and want the native Microsoft report embedded directly:

1. Open **Power BI Desktop**.
2. Click **File > Publish > Publish to Power BI** (requires a free or Pro Power BI account).
3. Select your workspace (e.g., `My Workspace`).
4. Once published, open [app.powerbi.com](https://app.powerbi.com) in your browser.
5. Open your report > Click **File > Embed report > Publish to web (public)**.
6. Copy the generated **iFrame embed code** or **Direct URL**.
7. You can paste the iFrame directly into your GitHub README:
   ```html
   <iframe title="Cyclistic Bike-Share Analytics" width="100%" height="700" src="https://app.powerbi.com/view?r=YOUR_EMBED_URL" frameborder="0" allowFullScreen="true"></iframe>
   ```
