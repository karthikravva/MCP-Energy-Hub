# MCP's 1st Birthday Hackathon - Deployment Checklist

## ✅ Pre-Deployment (Complete)

- [x] MCP Server with 8 tools
- [x] Gradio UI with 7 tabs
- [x] Real-time EIA data integration
- [x] 19 data centers seeded
- [x] SQLite database (HF compatible)
- [x] Dockerfile ready
- [x] Track tag: `building-mcp-track-enterprise`

## 🚀 Deployment Steps

### Step 1: Join the Hackathon Organization

1. Go to: https://huggingface.co/MCP-1st-Birthday
2. Click **"Request to join this org"** (top right)
3. Wait for approval (usually quick)

### Step 2: Register for the Hackathon

1. Go to: https://huggingface.co/spaces/MCP-1st-Birthday/gradio-hackathon-registration-winter25
2. Complete the registration form

### Step 3: Create Your Space

1. Go to: https://huggingface.co/new-space?sdk=docker
2. Settings:
   - **Owner**: Select `MCP-1st-Birthday` (the org)
   - **Space name**: `mcp-energy-hub` (or your preferred name)
   - **License**: MIT
   - **SDK**: Docker
   - **Hardware**: CPU Basic (free)
3. Click "Create Space"

### Step 4: Upload Files

**Option A: Git (Recommended)**
```bash
# Clone your new space
git clone https://huggingface.co/spaces/MCP-1st-Birthday/YOUR-SPACE-NAME
cd YOUR-SPACE-NAME

# Copy all files from mcp-energy-hub
# Then push
git add .
git commit -m "Initial commit - MCP Energy Hub"
git push
```

**Option B: Web Upload**
1. Go to your Space's "Files" tab
2. Click "Add file" > "Upload files"
3. Upload these files/folders:
   - `app/` (entire folder)
   - `Dockerfile`
   - `README.md`
   - `gradio_app.py`
   - `mcp_server.py`
   - `startup.py`
   - `seed_datacenters.py`
   - `requirements.txt`
   - `app.py`

### Step 5: Wait for Build

- The Space will automatically build (~3-5 minutes)
- Check the "Logs" tab for progress
- Once complete, you'll see the Gradio UI

### Step 6: Test Your Deployment

1. Open your Space URL
2. Test each tab:
   - Carbon Intensity
   - Find Best Region
   - Real-Time Data
   - AI Impact
   - Data Centers
   - All Regions
   - API & MCP

### Step 7: Record Demo Video (Required)

**Requirements**: 1-5 minutes

**Suggested Script**:
1. (0:00-0:30) Intro: "MCP Energy Hub - carbon-aware AI compute"
2. (0:30-1:30) Show Gradio UI tabs
3. (1:30-2:30) Demo API call with curl
4. (2:30-3:00) Explain real-world impact
5. (3:00-3:30) Close: "Built for MCP's 1st Birthday"

**Upload to**: YouTube, Loom, or embed in README

### Step 8: Post on Social Media (Required)

**Post on Twitter/X or LinkedIn with**:
- Link to your Space
- Tag @AnthropicAI @huggingface
- Use hashtags: #MCP #MCPHackathon

**Template** (see SOCIAL_POST.md):
```
⚡ Introducing MCP Energy Hub - an MCP server for carbon-aware AI compute!

🌱 8 tools for real-time grid intelligence
📊 Live EIA data from 7 US grid regions
🎯 Find the greenest region for your workloads

Built for @AnthropicAI @huggingface MCP's 1st Birthday Hackathon!

Try it: [YOUR_SPACE_URL]

#MCP #AI #Sustainability
```

### Step 9: Update README with Links

After posting, update your Space's README.md:
1. Add demo video link
2. Add social media post link
3. Add your HuggingFace username

## 📝 Required README Elements

Your README must include:
- [x] Track tag in frontmatter: `building-mcp-track-enterprise`
- [ ] Demo video link
- [ ] Social media post link
- [ ] Team member HF usernames (if team)

## 🎯 Judging Criteria

Your project will be evaluated on:
1. **Design/UI-UX** - Polished, intuitive interface ✅
2. **Functionality** - Uses MCP, Gradio properly ✅
3. **Creativity** - Innovative idea ✅
4. **Documentation** - Clear README, demo video
5. **Real-world impact** - Practical usefulness ✅

## 📅 Timeline

- **Hackathon Period**: Nov 14-30, 2025
- **Submission Deadline**: Nov 30, 2025
- **Results**: After judging period

## 🔗 Important Links

- Hackathon Page: https://huggingface.co/MCP-1st-Birthday
- Registration: https://huggingface.co/spaces/MCP-1st-Birthday/gradio-hackathon-registration-winter25
- Discord: Join HF Discord for help

Good luck! 🚀
