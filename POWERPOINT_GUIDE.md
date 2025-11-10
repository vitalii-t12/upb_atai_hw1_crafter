# PowerPoint Presentation Guide

## ✅ Successfully Created!

**File:** `crafter_presentation.pptx` (1.3 MB)

**Location:** `/home/vi/remote-dev/uni/upb_atai_hw1_crafter/crafter_presentation.pptx`

---

## 📊 What's Included

### 11 Slides Created:

1. **Title Slide** - Project title, subtitle, your names (placeholder), date
2. **The Crafter Challenge** - Environment specs, challenges, random baseline
3. **Method: Enhanced DQN** - Objective functions, 3 enhancements (Double DQN, Dueling, N-step)
4. **Ablation Study** - Results table with 6 configurations × 3 seeds
5. **Exploration Experiment** - Hypothesis, setup, results (negative finding)
6. **Training Dynamics** - REWARDS PLOT EMBEDDED ✅ (mandatory plot)
7. **Achievement Spectrum** - ACHIEVEMENT PLOT EMBEDDED ✅ (bonus plot)
8. **Training Metrics** - TRAINING METRICS PLOT EMBEDDED ✅ (loss & Q-values)
9. **Emergent Behaviors** - Successful strategies, failure modes, observations
10. **Conclusions** - Achievements, insights, future work
11. **Questions** - Thank you slide with summary

### 🖼️ Plots Embedded:

✅ **Slide 6:** `logdir/enhanced-dqn/plots/rewards.png` (Average episodic reward - MANDATORY)
✅ **Slide 7:** `logdir/enhanced-dqn/plots/achievement_spectrum.png` (Achievement spectrum - BONUS)
✅ **Slide 8:** `logdir/enhanced-dqn/plots/training_metrics.png` (Loss & Q-values)

---

## 🛠️ How to Edit and Convert to PDF

### Option 1: Using PowerPoint (Windows/Mac)

1. **Open the file:**
   ```
   Open crafter_presentation.pptx in PowerPoint
   ```

2. **Edit your info:**
   - Slide 1: Replace `[Your Names Here]` with actual names
   - Slide 11: Add your email and GitHub URL (if available)

3. **Review slides:**
   - Check formatting looks good
   - Verify plots display correctly
   - Adjust text sizes if needed

4. **Export to PDF:**
   - File → Save As → Choose "PDF" format
   - Save as: `surname_name_middlename.pdf`

### Option 2: Using Google Slides (Online)

1. **Upload to Google Drive:**
   - Go to https://drive.google.com
   - Upload `crafter_presentation.pptx`

2. **Open with Google Slides:**
   - Right-click file → Open with → Google Slides

3. **Edit as needed:**
   - Change names and contact info
   - Adjust formatting

4. **Download as PDF:**
   - File → Download → PDF Document (.pdf)
   - Rename to: `surname_name_middlename.pdf`

### Option 3: Using LibreOffice (Linux/Mac/Windows - Free)

1. **Install LibreOffice** (if not already):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libreoffice

   # Mac (with Homebrew)
   brew install --cask libreoffice
   ```

2. **Convert to PDF:**
   ```bash
   libreoffice --headless --convert-to pdf crafter_presentation.pptx
   # Or
   soffice --headless --convert-to pdf crafter_presentation.pptx
   ```

3. **Rename:**
   ```bash
   mv crafter_presentation.pdf surname_name_middlename.pdf
   ```

### Option 4: Online Converter

1. Go to: https://www.ilovepdf.com/powerpoint_to_pdf
2. Upload `crafter_presentation.pptx`
3. Download PDF
4. Rename to `surname_name_middlename.pdf`

---

## ✏️ Recommended Edits Before Finalizing

### Must Edit:
- [ ] **Slide 1:** Replace `[Your Names Here]` with actual team member names
- [ ] **Slide 11:** Add your email address
- [ ] **Slide 11:** Add GitHub URL if you have one (or remove the line)

### Should Review:
- [ ] **All slides:** Check text is readable on your display/projector
- [ ] **Slide 4, 5:** Verify tables display correctly
- [ ] **Slides 6, 7, 8:** Confirm plots are clear and readable
- [ ] **All formulas:** Ensure mathematical notation is clear

### Optional Enhancements:
- [ ] Add slide numbers (Insert → Slide Number)
- [ ] Adjust color scheme if desired (Design → Themes)
- [ ] Add transitions between slides (Transitions tab)
- [ ] Increase font sizes if presenting on large screen

---

## 📋 Assignment Requirements Checklist

### ✅ All Requirements Met:

| Requirement | Location | Status |
|------------|----------|--------|
| Method description | Slide 3 | ✅ |
| **Objective function (MANDATORY)** | Slide 3 (formulas) | ✅ |
| Enhancements | Slides 3-5 | ✅ |
| **Average episodic reward (MANDATORY)** | Slide 6 (plot) | ✅ |
| Training performance | Slide 6 (plot) | ✅ |
| Evaluation performance | Slide 6 (plot) | ✅ |
| Random baseline comparison | Slides 2, 4, 5, 6 | ✅ |
| **Achievement spectrum (BONUS)** | Slide 7 (plot) | ✅ |
| **2-3 seed average** | All tables (3 seeds) | ✅ |
| Loss evolution | Slide 8 (plot) | ✅ |
| Q-values evolution | Slide 8 (plot) | ✅ |
| **Emergent behaviors** | Slide 9 | ✅ |

---

## 🎨 Slide Design Notes

### Color Scheme:
- **Title color:** Dark blue (RGB: 0, 51, 102)
- **Table headers:** Dark blue background with white text
- **Emphasis:** Red for important negative findings
- **Success indicators:** ⭐ for best configurations, ✅ for achievements

### Font Sizes:
- Slide titles: 32pt (bold)
- Main headings: 18-20pt (bold)
- Body text: 14-16pt
- Table text: 11-12pt
- Captions: 11-12pt (italic)

### Layout:
- Standard slide size: 10" × 7.5" (widescreen)
- Margins: 0.5" on all sides
- Tables: Full width where appropriate
- Images: Scaled to fit well with captions

---

## 🐛 Troubleshooting

### Problem: Plots don't display
**Solution:**
- The plots are embedded, but if they don't show:
- Open in PowerPoint/Google Slides
- Manually insert images: Insert → Pictures
- Use plots from: `logdir/enhanced-dqn/plots/`

### Problem: Formulas look weird
**Solution:**
- The formulas are plain text (not LaTeX)
- They should display correctly in all programs
- If needed, you can replace with equation editor formulas

### Problem: Text is cut off
**Solution:**
- Select the text box
- Drag to make it larger
- Or reduce font size slightly

### Problem: File too large for upload
**Solution:**
- The file is only 1.3 MB, should be fine
- If needed, compress images: File → Compress Pictures

### Problem: Can't edit in Google Slides
**Solution:**
- Make a copy: File → Make a copy
- Or download as PPTX, edit locally, re-upload

---

## 💡 Presentation Tips

### Before Presenting:
1. **Test on presentation computer** - Ensure it opens correctly
2. **Bring backup on USB** - In case of technical issues
3. **Practice timing** - Aim for 10-11 minutes
4. **Prepare for questions** - Review speaker notes (see `presentation_speaker_notes.md`)

### During Presentation:
- **Speak to audience**, not to slides
- **Point at specific results** when discussing them
- **Pause after key findings** (Slides 4, 5, 7)
- **Emphasize the exploration negative result** (Slide 5) - it's your most interesting finding

### Slide Timing Guide:
- Slide 1: 30 seconds
- Slide 2: 1 minute
- Slide 3: 2 minutes
- Slide 4: 1.5 minutes
- Slide 5: 1.5 minutes
- Slide 6: 1.5 minutes
- Slide 7: 1.5 minutes
- Slide 8: 1 minute (can skip if over time)
- Slide 9: 1 minute
- Slide 10: 1 minute
- Slide 11: Q&A

**Total:** ~10-11 minutes

### If Running Over Time:
- **Skip Slide 8** (training metrics) - say "detailed metrics in backup"
- **Shorten Slide 9** (behaviors) - mention 2-3 key points
- **Keep Slides 4, 5, 6, 7** - these are core results

---

## 📦 Files in Your Directory

```
crafter_presentation.pptx          - The PowerPoint file (this is what you need!)
presentation_slides.md             - Original Markdown source
presentation_speaker_notes.md      - Detailed speaker notes for each slide
PRESENTATION_README.md             - Markdown to PDF conversion guide
POWERPOINT_GUIDE.md               - This guide
generate_presentation.py           - Python script that created the PPTX
```

---

## 🚀 Quick Start (TL;DR)

```bash
# 1. Download the file
# Download crafter_presentation.pptx to your local computer

# 2. Open in PowerPoint or Google Slides
# Edit slide 1 and 11 to add your names

# 3. Export to PDF
# File → Save As → PDF
# Name it: surname_name_middlename.pdf

# 4. Review checklist
# Verify all requirements are met (see checklist above)

# 5. Upload to Moodle
# Upload the PDF before deadline (Nov 10, 11:59pm)
```

---

## ✅ Final Checklist

Before submission:
- [ ] Opened `crafter_presentation.pptx` successfully
- [ ] Replaced `[Your Names Here]` with actual names
- [ ] Added contact info on last slide
- [ ] All plots display correctly (Slides 6, 7, 8)
- [ ] All tables are readable (Slides 4, 5)
- [ ] Formulas are clear (Slide 3)
- [ ] Exported to PDF format
- [ ] Named file: `surname_name_middlename.pdf`
- [ ] File size < 10 MB (should be ~2-3 MB)
- [ ] Reviewed assignment requirements checklist above

---

Good luck with your presentation! The slides look professional and include all required elements. 🎯

**Questions?** Review the speaker notes in `presentation_speaker_notes.md` for detailed guidance on what to say for each slide.
